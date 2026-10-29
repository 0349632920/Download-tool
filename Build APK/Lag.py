# ==============================================
# FILE: main.py - ỨNG DỤNG ANDROID XEM IP ROUTER
# ==============================================

import socket
import subprocess
import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

# ===== MÀU NỀN =====
Window.clearcolor = (0.1, 0.1, 0.15, 1)

class RouterInfoApp(App):
    def build(self):
        # Layout chính
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Tiêu đề
        title = Label(
            text="📡 THÔNG TIN MẠNG",
            font_size=30,
            color=(0.3, 0.8, 1, 1),
            size_hint_y=None,
            height=60
        )
        layout.add_widget(title)
        
        # Khung hiển thị thông tin
        self.info_label = Label(
            text="🔍 Đang quét mạng...",
            font_size=18,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=400,
            halign='left',
            valign='top'
        )
        self.info_label.bind(size=self.info_label.setter('text_size'))
        layout.add_widget(self.info_label)
        
        # Nút quét lại
        scan_btn = Button(
            text="🔄 QUÉT LẠI MẠNG",
            font_size=20,
            background_color=(0.2, 0.6, 0.9, 1),
            size_hint_y=None,
            height=60
        )
        scan_btn.bind(on_press=self.scan_network)
        layout.add_widget(scan_btn)
        
        # Nút thoát
        exit_btn = Button(
            text="❌ THOÁT",
            font_size=20,
            background_color=(0.8, 0.2, 0.2, 1),
            size_hint_y=None,
            height=50
        )
        exit_btn.bind(on_press=self.exit_app)
        layout.add_widget(exit_btn)
        
        # Chạy quét lần đầu
        self.scan_network(None)
        
        return layout
    
    def scan_network(self, instance):
        """Quét thông tin mạng"""
        info = "📡 THÔNG TIN MẠNG CỦA BẠN\n"
        info += "=" * 40 + "\n\n"
        
        # 1. Lấy IP của máy
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            my_ip = s.getsockname()[0]
            s.close()
            info += f"🖥️ IP máy bạn: {my_ip}\n"
        except:
            info += "❌ Không lấy được IP\n"
        
        # 2. Lấy IP Router (Gateway)
        try:
            # Thử cách 1: dùng ip route (Linux/Android)
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'default via' in line:
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        router_ip = ip_match.group(1)
                        info += f"📡 Router IP: {router_ip}\n"
                        break
        except:
            pass
        
        # 3. Lấy tên WiFi đang kết nối
        try:
            result = subprocess.run(['dumpsys', 'wifi'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'SSID' in line and '=' in line:
                    ssid = line.split('=')[-1].strip()
                    if ssid and ssid != '""':
                        info += f"📶 WiFi: {ssid}\n"
                        break
        except:
            pass
        
        # 4. Lấy thông tin kết nối
        try:
            result = subprocess.run(['dumpsys', 'connectivity'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'InterfaceName:' in line:
                    interface = line.split(':')[-1].strip()
                    info += f"🔗 Interface: {interface}\n"
                    break
        except:
            pass
        
        # 5. Kiểm tra kết nối Internet
        try:
            import urllib.request
            urllib.request.urlopen('http://google.com', timeout=3)
            info += "🌐 Internet: ✅ Đã kết nối\n"
        except:
            info += "🌐 Internet: ❌ Không kết nối\n"
        
        info += "\n" + "=" * 40 + "\n"
        info += "💡 IP Router thường là: 192.168.1.1\n"
        info += "💡 Hoặc 192.168.0.1, 10.0.0.1\n"
        
        self.info_label.text = info
    
    def exit_app(self, instance):
        """Thoát ứng dụng"""
        App.get_running_app().stop()

if __name__ == "__main__":
    RouterInfoApp().run()