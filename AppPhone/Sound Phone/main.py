#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ứng dụng Alarm Controller - Điều khiển chuông báo từ xa qua Telegram
Tích hợp Android Service để chạy ngầm
"""

import os
import sys
import threading
import json
import time
from datetime import datetime, timedelta

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.audio import SoundLoader

# Import các module Android
try:
    from android import mActivity
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast
    HAS_ANDROID = True
except ImportError:
    HAS_ANDROID = False
    Logger.warning("Không thể import android modules - đang chạy trên desktop")

# Import service
try:
    from alarm_service import AlarmService
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False
    Logger.warning("Không thể import alarm_service - service không hoạt động")


class AlarmController(BoxLayout):
    """Layout chính của ứng dụng"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Khởi tạo service
        self.alarm_service = None
        self.is_service_running = False
        
        # Biến trạng thái
        self.alarm_time = None
        self.alarm_active = False
        
        # Khởi tạo UI
        self.init_ui()
        
        # Kiểm tra và xin quyền
        if HAS_ANDROID:
            self.request_permissions()
        
        # Kết nối service
        self.connect_service()
    
    def init_ui(self):
        """Xây dựng giao diện"""
        # Tiêu đề
        title = Label(
            text="⏰ ỨNG DỤNG BÁO THỨC\nChạy ngầm - Phát chuông kể cả khi tắt màn hình",
            font_size='20sp',
            size_hint_y=0.15,
            halign='center'
        )
        self.add_widget(title)
        
        # Khung trạng thái
        status_box = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        self.status_label = Label(
            text="Trạng thái: Đang khởi tạo...",
            font_size='16sp',
            color=(0.5, 0.8, 0.5, 1)
        )
        status_box.add_widget(self.status_label)
        
        self.time_label = Label(
            text="Thời gian hiện tại: " + datetime.now().strftime('%H:%M:%S'),
            font_size='14sp'
        )
        status_box.add_widget(self.time_label)
        self.add_widget(status_box)
        
        # Khung đặt báo thức
        alarm_box = GridLayout(cols=3, size_hint_y=0.15, spacing=5)
        
        self.hour_input = TextInput(
            text='07',
            hint_text='Giờ',
            input_filter='int',
            multiline=False,
            size_hint_x=0.3
        )
        self.minute_input = TextInput(
            text='00',
            hint_text='Phút',
            input_filter='int',
            multiline=False,
            size_hint_x=0.3
        )
        
        self.set_alarm_btn = Button(
            text='Đặt báo thức',
            size_hint_x=0.4,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.set_alarm_btn.bind(on_press=self.set_alarm)
        
        alarm_box.add_widget(Label(text='Giờ:'))
        alarm_box.add_widget(self.hour_input)
        alarm_box.add_widget(Label(text='Phút:'))
        alarm_box.add_widget(self.minute_input)
        alarm_box.add_widget(self.set_alarm_btn)
        self.add_widget(alarm_box)
        
        # Khung nút điều khiển
        control_box = GridLayout(cols=3, size_hint_y=0.2, spacing=5)
        
        self.test_alarm_btn = Button(
            text='🔔 Test chuông',
            background_color=(1, 0.5, 0, 1)
        )
        self.test_alarm_btn.bind(on_press=self.test_alarm)
        
        self.stop_alarm_btn = Button(
            text='⏹ Dừng chuông',
            background_color=(1, 0, 0, 1)
        )
        self.stop_alarm_btn.bind(on_press=self.stop_alarm)
        
        self.start_service_btn = Button(
            text='▶️ Bắt đầu service',
            background_color=(0, 0.8, 0, 1)
        )
        self.start_service_btn.bind(on_press=self.start_service)
        
        control_box.add_widget(self.test_alarm_btn)
        control_box.add_widget(self.stop_alarm_btn)
        control_box.add_widget(self.start_service_btn)
        self.add_widget(control_box)
        
        # Khung log
        log_box = BoxLayout(orientation='vertical', size_hint_y=0.3)
        log_box.add_widget(Label(text='Nhật ký hoạt động:', font_size='14sp', size_hint_y=0.1))
        
        self.log_text = TextInput(
            text='',
            readonly=True,
            multiline=True,
            font_size='12sp'
        )
        log_box.add_widget(self.log_text)
        self.add_widget(log_box)
        
        # Cập nhật thời gian thực
        Clock.schedule_interval(self.update_time, 1)
        
        # Log khởi tạo
        self.add_log("✅ Ứng dụng đã khởi động")
        self.add_log(f"📱 Android: {'Có' if HAS_ANDROID else 'Không'}")
        self.add_log(f"🔧 Service: {'Có' if HAS_SERVICE else 'Không'}")
    
    def request_permissions(self):
        """Xin quyền Android"""
        permissions = [
            Permission.POST_NOTIFICATIONS,
            Permission.FOREGROUND_SERVICE,
            Permission.WAKE_LOCK,
        ]
        
        try:
            request_permissions(permissions)
            self.add_log("✅ Đã xin quyền Android")
        except Exception as e:
            self.add_log(f"⚠️ Lỗi xin quyền: {e}")
    
    def connect_service(self):
        """Kết nối với service nền"""
        if not HAS_SERVICE:
            self.status_label.text = "Trạng thái: Không có service"
            return
        
        try:
            self.alarm_service = AlarmService()
            self.is_service_running = True
            self.status_label.text = "Trạng thái: Đã kết nối service"
            self.add_log("✅ Đã kết nối với AlarmService")
        except Exception as e:
            self.status_label.text = f"Trạng thái: Lỗi service - {str(e)}"
            self.add_log(f"❌ Lỗi kết nối service: {e}")
    
    def set_alarm(self, instance):
        """Đặt báo thức"""
        try:
            hour = int(self.hour_input.text)
            minute = int(self.minute_input.text)
            
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                self.add_log("⚠️ Vui lòng nhập giờ (0-23) và phút (0-59)")
                return
            
            # Lên lịch báo thức
            if HAS_SERVICE and self.alarm_service:
                success = self.alarm_service.schedule_alarm(hour, minute)
                if success:
                    self.alarm_time = f"{hour:02d}:{minute:02d}"
                    self.alarm_active = True
                    self.add_log(f"✅ Đã đặt báo thức lúc {hour:02d}:{minute:02d}")
                    self.status_label.text = f"⏰ Báo thức: {hour:02d}:{minute:02d}"
                else:
                    self.add_log("❌ Không thể đặt báo thức")
            else:
                self.add_log("⚠️ Service chưa sẵn sàng")
                
        except ValueError:
            self.add_log("⚠️ Vui lòng nhập số")
    
    def test_alarm(self, instance):
        """Test phát chuông"""
        self.add_log("🔔 Đang test chuông...")
        
        if HAS_SERVICE and self.alarm_service:
            self.alarm_service.test_alarm()
        else:
            self.play_local_sound()
    
    def stop_alarm(self, instance):
        """Dừng chuông"""
        self.add_log("⏹ Đang dừng chuông...")
        
        if HAS_SERVICE and self.alarm_service:
            self.alarm_service.stop_alarm()
        else:
            # Dừng âm thanh local
            SoundLoader.stop_all()
        
        self.alarm_active = False
        self.status_label.text = "Trạng thái: Đã dừng chuông"
    
    def start_service(self, instance):
        """Khởi chạy service"""
        if not HAS_SERVICE:
            self.add_log("❌ Không có service để khởi chạy")
            return
        
        if HAS_ANDROID:
            try:
                self.alarm_service.start_foreground()
                self.is_service_running = True
                self.status_label.text = "Trạng thái: Service đang chạy"
                self.add_log("✅ Service đã được khởi chạy")
            except Exception as e:
                self.add_log(f"❌ Lỗi khởi chạy service: {e}")
        else:
            self.add_log("⚠️ Chỉ có thể chạy service trên Android")
    
    def play_local_sound(self):
        """Phát âm thanh local (dùng cho desktop)"""
        try:
            sound = SoundLoader.load('alarm_sound.mp3')
            if sound:
                sound.play()
                self.add_log("🔔 Đang phát âm thanh local")
            else:
                self.add_log("⚠️ Không tìm thấy file alarm_sound.mp3")
        except Exception as e:
            self.add_log(f"❌ Lỗi phát âm thanh: {e}")
    
    def update_time(self, dt):
        """Cập nhật thời gian hiện tại"""
        self.time_label.text = "Thời gian hiện tại: " + datetime.now().strftime('%H:%M:%S')
    
    def add_log(self, message):
        """Thêm log vào text box"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.text += log_entry
        # Tự động scroll xuống cuối
        self.log_text.cursor = (0, len(self.log_text.text))


class AlarmApp(App):
    """Ứng dụng chính"""
    
    def build(self):
        """Xây dựng ứng dụng"""
        self.title = 'Alarm Controller'
        return AlarmController()
    
    def on_stop(self):
        """Khi ứng dụng dừng"""
        Logger.info("AlarmApp: Đang dừng ứng dụng...")
        # Dọn dẹp
        SoundLoader.stop_all()


if __name__ == '__main__':
    AlarmApp().run()