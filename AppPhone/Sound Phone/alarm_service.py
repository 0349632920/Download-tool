#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Alarm Service - Chạy ngầm trên Android
Phát chuông báo kể cả khi ứng dụng đã đóng
"""

import time
import threading
from datetime import datetime, timedelta
import os

from kivy.logger import Logger
from kivy.core.audio import SoundLoader

# Import Android modules
try:
    from android import mActivity
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast
    HAS_ANDROID = True
except ImportError:
    HAS_ANDROID = False
    Logger.warning("Không import được Android modules - đang chạy desktop")

class AlarmService:
    """Service quản lý chuông báo trên Android"""
    
    def __init__(self):
        self.is_running = False
        self.is_alarm_playing = False
        self.alarm_thread = None
        self.wakelock = None
        
        # Khởi tạo Android components
        if HAS_ANDROID:
            self.init_android_components()
        
        Logger.info("AlarmService: Khởi tạo thành công")
    
    def init_android_components(self):
        """Khởi tạo các thành phần Android"""
        try:
            # Context
            self.context = mActivity.getApplicationContext()
            
            # MediaPlayer
            self.MediaPlayer = autoclass('android.media.MediaPlayer')
            self.player = self.MediaPlayer()
            
            # Notification Manager
            self.NotificationManager = autoclass('android.app.NotificationManager')
            self.NotificationChannel = autoclass('android.app.NotificationChannel')
            self.NotificationBuilder = autoclass('android.app.Notification$Builder')
            
            # AlarmManager
            self.AlarmManager = autoclass('android.app.AlarmManager')
            self.PendingIntent = autoclass('android.app.PendingIntent')
            self.Intent = autoclass('android.content.Intent')
            
            # PowerManager (WakeLock)
            self.PowerManager = autoclass('android.os.PowerManager')
            
            # System
            self.System = autoclass('java.lang.System')
            
            # Build version
            self.Build = autoclass('android.os.Build$VERSION')
            
            Logger.info("AlarmService: Đã khởi tạo Android components")
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi khởi tạo Android - {e}")
    
    def start_foreground(self):
        """Chạy service ở chế độ foreground"""
        if not HAS_ANDROID:
            Logger.warning("AlarmService: Không thể chạy foreground trên desktop")
            return
        
        try:
            # Tạo notification
            notification = self.create_notification(
                "⏰ Alarm Service",
                "Đang chạy nền, sẵn sàng phát chuông báo"
            )
            
            # Lấy service object
            PythonService = autoclass('org.kivy.android.PythonService')
            service = PythonService.mService
            
            # Chạy foreground
            service.startForeground(1, notification)
            self.is_running = True
            
            Logger.info("AlarmService: Đã chạy foreground service")
            
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi foreground - {e}")
    
    def create_notification(self, title, message):
        """Tạo notification cho foreground service"""
        if not HAS_ANDROID:
            return None
        
        try:
            # Tạo channel (Android 8+)
            if self.Build.SDK_INT >= 26:
                channel_id = "alarm_channel"
                channel_name = "Alarm Service"
                importance = self.NotificationManager.IMPORTANCE_HIGH
                
                channel = self.NotificationChannel(channel_id, channel_name, importance)
                notification_manager = self.context.getSystemService(
                    self.context.NOTIFICATION_SERVICE
                )
                notification_manager.createNotificationChannel(channel)
            else:
                channel_id = ""
            
            # Tạo notification
            builder = self.NotificationBuilder(self.context, channel_id)
            builder.setContentTitle(title)
            builder.setContentText(message)
            builder.setSmallIcon(self.context.getApplicationInfo().icon)
            builder.setOngoing(True)
            builder.setPriority(self.NotificationBuilder.PRIORITY_HIGH)
            
            return builder.build()
            
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi tạo notification - {e}")
            return None
    
    def acquire_wakelock(self):
        """Giữ CPU không ngủ"""
        if not HAS_ANDROID:
            return
        
        try:
            power_manager = self.context.getSystemService(self.context.POWER_SERVICE)
            self.wakelock = power_manager.newWakeLock(
                self.PowerManager.PARTIAL_WAKE_LOCK,
                'AlarmWakeLock'
            )
            self.wakelock.acquire(60000)  # 1 phút
            Logger.info("AlarmService: Đã acquire Wakelock")
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi acquire wakelock - {e}")
    
    def release_wakelock(self):
        """Giải phóng Wakelock"""
        if self.wakelock:
            try:
                self.wakelock.release()
                self.wakelock = None
                Logger.info("AlarmService: Đã release Wakelock")
            except Exception as e:
                Logger.error(f"AlarmService: Lỗi release wakelock - {e}")
    
    def schedule_alarm(self, hour, minute):
        """Lên lịch báo thức với AlarmManager"""
        if not HAS_ANDROID:
            Logger.warning("AlarmService: Không thể schedule trên desktop")
            return False
        
        try:
            # Tạo Intent để khởi động service
            PythonService = autoclass('org.kivy.android.PythonService')
            service_class = PythonService.mService.getClass()
            
            intent = self.Intent(self.context, service_class)
            intent.setAction("START_ALARM")
            
            # Tạo PendingIntent
            pi = self.PendingIntent.getService(
                self.context,
                0,
                intent,
                self.PendingIntent.FLAG_UPDATE_CURRENT
            )
            
            # Đặt thời gian
            Calendar = autoclass('java.util.Calendar')
            calendar = Calendar.getInstance()
            calendar.set(Calendar.HOUR_OF_DAY, hour)
            calendar.set(Calendar.MINUTE, minute)
            calendar.set(Calendar.SECOND, 0)
            
            now = self.System.currentTimeMillis()
            alarm_time = calendar.getTimeInMillis()
            
            # Nếu thời gian đã qua, đặt cho ngày mai
            if alarm_time <= now:
                calendar.add(Calendar.DAY_OF_MONTH, 1)
                alarm_time = calendar.getTimeInMillis()
            
            # Đặt báo thức
            alarm_manager = self.context.getSystemService(self.context.ALARM_SERVICE)
            alarm_manager.setExact(
                self.AlarmManager.RTC_WAKEUP,
                alarm_time,
                pi
            )
            
            Logger.info(f"AlarmService: Đã đặt báo thức lúc {hour:02d}:{minute:02d}")
            return True
            
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi schedule alarm - {e}")
            return False
    
    def test_alarm(self):
        """Test phát chuông"""
        self.play_alarm_sound()
    
    def play_alarm_sound(self):
        """Phát chuông báo"""
        if self.is_alarm_playing:
            return
        
        self.is_alarm_playing = True
        self.acquire_wakelock()
        
        # Chạy trong thread riêng
        self.alarm_thread = threading.Thread(target=self._play_sound_thread)
        self.alarm_thread.start()
    
    def _play_sound_thread(self):
        """Thread phát âm thanh"""
        try:
            Logger.info("AlarmService: Bắt đầu phát chuông")
            
            # Phương pháp 1: Dùng MediaPlayer (Android)
            if HAS_ANDROID:
                self._play_android_sound()
            else:
                # Phương pháp 2: Dùng Kivy SoundLoader (Desktop)
                self._play_desktop_sound()
            
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi phát chuông - {e}")
        finally:
            self.is_alarm_playing = False
            self.release_wakelock()
    
    def _play_android_sound(self):
        """Phát âm thanh trên Android"""
        try:
            # Đường dẫn file âm thanh
            sound_path = os.path.join(os.getcwd(), 'alarm_sound.mp3')
            
            if os.path.exists(sound_path):
                # Dùng MediaPlayer
                self.player = self.MediaPlayer()
                self.player.setDataSource(sound_path)
                self.player.prepare()
                self.player.start()
                self.player.setLooping(True)
                
                # Chạy trong 30 giây hoặc đến khi dừng
                time.sleep(30)
                self.player.stop()
                self.player.release()
            else:
                Logger.warning("AlarmService: Không tìm thấy file âm thanh")
                # Dùng âm thanh mặc định của Android
                self._play_default_sound()
                
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi phát âm thanh Android - {e}")
            self._play_default_sound()
    
    def _play_default_sound(self):
        """Phát âm thanh mặc định của Android"""
        try:
            # Lấy RingtoneManager để phát nhạc chuông mặc định
            RingtoneManager = autoclass('android.media.RingtoneManager')
            uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            
            self.player = self.MediaPlayer()
            self.player.setDataSource(self.context, uri)
            self.player.prepare()
            self.player.start()
            self.player.setLooping(True)
            
            time.sleep(30)
            self.player.stop()
            self.player.release()
            
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi phát nhạc chuông mặc định - {e}")
    
    def _play_desktop_sound(self):
        """Phát âm thanh trên desktop (dùng SoundLoader)"""
        try:
            sound = SoundLoader.load('alarm_sound.mp3')
            if sound:
                sound.play()
                time.sleep(10)
                sound.stop()
            else:
                Logger.warning("AlarmService: Không tìm thấy file âm thanh trên desktop")
        except Exception as e:
            Logger.error(f"AlarmService: Lỗi phát âm thanh desktop - {e}")
    
    def stop_alarm(self):
        """Dừng chuông báo"""
        self.is_alarm_playing = False
        
        # Dừng MediaPlayer
        if HAS_ANDROID and hasattr(self, 'player'):
            try:
                self.player.stop()
                self.player.release()
                Logger.info("AlarmService: Đã dừng MediaPlayer")
            except:
                pass
        
        # Dừng SoundLoader
        SoundLoader.stop_all()
        
        self.release_wakelock()
        Logger.info("AlarmService: Đã dừng chuông")
    
    def stop_service(self):
        """Dừng service"""
        self.is_running = False
        self.stop_alarm()
        Logger.info("AlarmService: Đã dừng service")


# Hàm khởi chạy service từ buildozer
def start_service():
    """Hàm được gọi từ buildozer để khởi chạy service"""
    service = AlarmService()
    service.start_foreground()
    
    # Giữ service chạy
    while True:
        time.sleep(10)