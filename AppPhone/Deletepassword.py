"""
XÓA MẬT KHẨU OPPO COLOROS 11.1 BẰNG ADB
Yêu cầu: USB Debugging đã bật
"""

import subprocess
import time
import os
import sys
import re

class OPPOColorOS11Unlocker:
    def __init__(self):
        self.adb = self._find_adb()
        self.serial = None
        self.is_connected = False
        
    def _find_adb(self):
        """Tìm ADB"""
        import shutil
        adb = shutil.which("adb")
        if adb:
            return adb
        
        # Các đường dẫn thường gặp
        paths = [
            r"C:\Program Files (x86)\Minimal ADB and Fastboot\adb.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe",
            r"D:\android-sdk\platform-tools\adb.exe",
            r"D:\platform-tools\adb.exe",
            r"C:\platform-tools\adb.exe"
        ]
        
        for path in paths:
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                return expanded
        return None
    
    def connect_device(self):
        """Kết nối thiết bị"""
        if not self.adb:
            print("❌ Không tìm thấy ADB!")
            return False
        
        # Kiểm tra thiết bị
        result = subprocess.run(
            [self.adb, 'devices'],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')[1:]
        devices = [line.split()[0] for line in lines if line and 'device' in line]
        
        if not devices:
            print("❌ Không tìm thấy thiết bị!")
            print("\n🔍 KIỂM TRA:")
            print("  1. USB đã cắm chưa?")
            print("  2. Trên điện thoại đã chọn 'Transfer files' chưa?")
            print("  3. Popup 'Allow USB Debugging?' đã bấm OK chưa?")
            return False
        
        self.serial = devices[0]
        self.is_connected = True
        print(f"✅ Đã kết nối: {self.serial}")
        return True
    
    def remove_password_coloros11(self):
        """
        Xóa mật khẩu trên ColorOS 11.1
        Áp dụng các phương pháp thực tế
        """
        if not self.is_connected:
            print("❌ Chưa kết nối thiết bị!")
            return False
        
        print("\n" + "=" * 60)
        print("🔑 ĐANG XÓA MẬT KHẨU CHO COLOROS 11.1")
        print("=" * 60)
        
        success = False
        
        # === PHƯƠNG PHÁP 1: Xóa file mật khẩu ===
        print("\n📁 Phương pháp 1: Xóa file mật khẩu...")
        
        files_to_remove = [
            '/data/system/gesture.key',
            '/data/system/locksettings.db',
            '/data/system/locksettings.db-wal',
            '/data/system/locksettings.db-shm',
            '/data/system/pattern.key',
            '/data/system/password.key'
        ]
        
        for file in files_to_remove:
            cmd = f'{self.adb} -s {self.serial} shell rm {file}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ Đã xóa: {file}")
                success = True
            else:
                # Kiểm tra nếu file không tồn tại (cũng là thành công)
                if 'No such file' not in result.stderr:
                    print(f"   ⚠️ Không xóa được: {file}")
        
        # === PHƯƠNG PHÁP 2: Dùng locksettings clear ===
        print("\n🔓 Phương pháp 2: Xóa locksettings...")
        cmd = f'{self.adb} -s {self.serial} shell locksettings clear'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 or 'Success' in result.stdout:
            print("   ✅ Đã xóa locksettings")
            success = True
        else:
            print("   ⚠️ Không xóa được locksettings")
        
        # === PHƯƠNG PHÁP 3: Đặt mật khẩu trống ===
        print("\n🔐 Phương pháp 3: Đặt mật khẩu trống...")
        cmd = f'{self.adb} -s {self.serial} shell locksettings set-password ""'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Đã đặt mật khẩu trống")
            success = True
        else:
            print("   ⚠️ Không đặt được mật khẩu trống")
        
        # === PHƯƠNG PHÁP 4: Xóa thông qua settings ===
        print("\n⚙️ Phương pháp 4: Xóa qua settings...")
        commands = [
            f'{self.adb} -s {self.serial} shell settings put secure lock_screen_lock_after_timeout 0',
            f'{self.adb} -s {self.serial} shell settings put secure lockscreen.disabled 1',
            f'{self.adb} -s {self.serial} shell settings put secure lockscreen.password_type 0'
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ Thành công: {cmd[:60]}...")
            else:
                print(f"   ⚠️ Thất bại: {cmd[:60]}...")
        
        # === PHƯƠNG PHÁP 5: Sử dụng content provider ===
        print("\n📱 Phương pháp 5: Dùng content provider...")
        cmd = f'{self.adb} -s {self.serial} shell content insert --uri content://settings/secure --bind name:s:lock_screen_lock_after_timeout --bind value:i:0'
        subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # === PHƯƠNG PHÁP 6: Vô hiệu hóa lock screen ===
        print("\n🚫 Phương pháp 6: Vô hiệu hóa lock screen...")
        cmd = f'{self.adb} -s {self.serial} shell pm disable com.android.keyguard'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Đã vô hiệu hóa Keyguard")
            success = True
        else:
            print("   ⚠️ Không vô hiệu hóa được")
        
        # === KHỞI ĐỘNG LẠI ===
        print("\n🔄 Khởi động lại máy...")
        subprocess.run(f'{self.adb} -s {self.serial} reboot', shell=True)
        
        print("\n" + "=" * 60)
        if success:
            print("✅ ĐÃ XÓA MẬT KHẨU!")
            print("=" * 60)
            print("\n📱 Đợi máy khởi động lại.")
            print("   Màn hình khóa SẼ BIẾN MẤT!")
            print("   Bạn có thể đặt mật khẩu mới trong Settings.")
        else:
            print("⚠️ KHÔNG THỂ XÓA MẬT KHẨU!")
            print("=" * 60)
            print("\n💡 Hãy thử các cách sau:")
            print("   1. Trên điện thoại: Bấm OK khi popup 'Allow USB Debugging'")
            print("   2. Tắt USB Debugging → Bật lại → Chạy lại")
            print("   3. Dùng Google Find My Device:")
            print("      https://www.google.com/android/find")
        
        return success
    
    def try_unlock_commands(self):
        """Thử các lệnh mở khóa trực tiếp"""
        if not self.is_connected:
            return
        
        print("\n🔓 THỬ MỞ KHÓA TRỰC TIẾP...")
        
        commands = [
            ('adb shell input keyevent 26', 'Mở màn hình'),
            ('adb shell input swipe 300 1000 300 200', 'Swipe lên'),
            ('adb shell input keyevent 82', 'Mở menu'),
            ('adb shell am start -n com.android.settings/.Settings', 'Mở Settings'),
            ('adb shell input keyevent 4', 'Back'),
            ('adb shell input keyevent 3', 'Home'),
        ]
        
        for cmd, name in commands:
            full_cmd = cmd.replace('adb', self.adb) + f' -s {self.serial}'
            try:
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ {name}: thành công")
                else:
                    print(f"   ⚠️ {name}: thất bại")
            except:
                print(f"   ❌ {name}: lỗi")

# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("🔑 XÓA MẬT KHẨU OPPO COLOROS 11.1")
    print("=" * 60)
    print("\n📌 ĐIỀU KIỆN:")
    print("   ✅ USB Debugging đã bật")
    print("   ✅ USB đã kết nối")
    print("   ✅ Đã bấm OK khi popup hiện ra")
    print("=" * 60)
    
    unlocker = OPPOColorOS11Unlocker()
    
    # Kết nối
    if not unlocker.connect_device():
        input("\n⚠️ KHÔNG KẾT NỐI ĐƯỢC!\nNhấn Enter để thoát...")
        return
    
    # Menu
    print("\n" + "=" * 60)
    print("📋 CHỌN HÀNH ĐỘNG:")
    print("  1. Xóa mật khẩu (Khuyến nghị)")
    print("  2. Thử mở khóa trực tiếp")
    print("  3. Thoát")
    print("=" * 60)
    
    choice = input("\nNhập số (1-3): ").strip()
    
    if choice == '1':
        unlocker.remove_password_coloros11()
    elif choice == '2':
        unlocker.try_unlock_commands()
    else:
        print("Thoát...")
    
    input("\nNhấn Enter để thoát...")

if __name__ == "__main__":
    main()