import os
import sys
import subprocess
import json
import base64
import time
import shutil
import ctypes
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ============ QUẢN LÝ QUYỀN ============
class PermissionManager:
    """Quản lý quyền truy cập trên Windows"""
    
    @staticmethod
    def is_admin():
        """Kiểm tra quyền Administrator"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    @staticmethod
    def request_admin():
        """Yêu cầu quyền Administrator"""
        if not PermissionManager.is_admin():
            print("\n🔑 ĐANG YÊU CẦU QUYỀN ADMINISTRATOR...")
            print("   ⚠️ Windows sẽ hiện hộp thoại UAC")
            print("   ✅ Nhấn 'Yes' / 'Có' để tiếp tục\n")
            
            try:
                script = os.path.abspath(sys.argv[0])
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{script}"', None, 1
                )
                sys.exit()
            except Exception as e:
                print(f"❌ Không thể xin quyền Admin: {e}")
                return False
        return True
    
    @staticmethod
    def check_adb_connection():
        """Kiểm tra kết nối ADB"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "unauthorized" in result.stdout.lower():
                return False, "unauthorized", "Chưa được cấp quyền USB Debugging"
            
            if "device" in result.stdout and "offline" not in result.stdout:
                return True, "connected", "Đã kết nối"
            
            return False, "no_device", "Không tìm thấy thiết bị"
        except Exception as e:
            return False, "error", str(e)
    
    @staticmethod
    def request_usb_debugging():
        """Yêu cầu quyền USB Debugging trên Android"""
        print("\n📱 ĐANG YÊU CẦU QUYỀN USB DEBUGGING...")
        print("   ⚠️ TRÊN ĐIỆN THOẠI SẼ HIỆN POPUP")
        print("   📱 'Cho phép gỡ lỗi USB?'")
        print("   ✅ Nhấn 'Cho phép' / 'OK' để tiếp tục")
        print("   ⏳ Đợi 5 giây...\n")
        
        subprocess.run(['adb', 'kill-server'], capture_output=True)
        time.sleep(1)
        subprocess.run(['adb', 'start-server'], capture_output=True)
        time.sleep(1)
        subprocess.run(['adb', 'devices'], capture_output=True)
        time.sleep(2)
        
        for i in range(5):
            print(f"   ⏳ Đang chờ... {i+1}/5")
            status, code, msg = PermissionManager.check_adb_connection()
            if status:
                print("   ✅ ĐÃ ĐƯỢC CẤP QUYỀN USB DEBUGGING!")
                return True
            time.sleep(1)
        
        print("   ❌ Vẫn chưa được cấp quyền!")
        return False

# ============ QUẢN LÝ ẨN/KHÓA APP ============
class AppLocker:
    """Quản lý ẩn và khóa ứng dụng"""
    
    def __init__(self, adb_manager):
        self.adb = adb_manager
        self.hidden_apps = {}
        self.locked_apps = {}
        self.app_passwords = {}
        self.app_pins = {}
        self.lock_methods = {}
        self.data_file = "app_security.json"
        self.load_data()
    
    def load_data(self):
        """Tải dữ liệu từ file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.hidden_apps = data.get('hidden_apps', {})
                    self.locked_apps = data.get('locked_apps', {})
                    self.app_passwords = data.get('app_passwords', {})
                    self.app_pins = data.get('app_pins', {})
                    self.lock_methods = data.get('lock_methods', {})
                print(f"✅ Đã tải dữ liệu: {len(self.hidden_apps)} app ẩn, {len(self.locked_apps)} app khóa")
            except:
                print("⚠️ Không thể tải dữ liệu")
    
    def save_data(self):
        """Lưu dữ liệu vào file"""
        try:
            data = {
                'hidden_apps': self.hidden_apps,
                'locked_apps': self.locked_apps,
                'app_passwords': self.app_passwords,
                'app_pins': self.app_pins,
                'lock_methods': self.lock_methods,
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Lưu thất bại: {e}")
            return False
    
    # ========== ẨN ỨNG DỤNG ==========
    
    def hide_app(self, package_name):
        """ẨN ứng dụng - Không tìm thấy trên điện thoại"""
        if package_name in self.hidden_apps:
            return False, "Ứng dụng đã được ẩn!"
        
        # Thử các phương thức ẩn
        methods = [
            (f'pm hide {package_name}', 'pm hide'),
            (f'pm disable-user {package_name}', 'pm disable-user'),
            (f'pm disable --user 0 {package_name}', 'pm disable --user 0')
        ]
        
        for cmd, method_name in methods:
            stdout, stderr, code = self.adb.run_adb_shell(cmd)
            if code == 0 and ('disabled' in stdout.lower() or 'hidden' in stdout.lower()):
                self.hidden_apps[package_name] = {
                    'hidden_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'method': method_name
                }
                self.save_data()
                return True, f"✅ Đã ẨN ứng dụng {package_name} - Không tìm thấy trên điện thoại! (Phương thức: {method_name})"
        
        return False, "❌ Không thể ẩn ứng dụng. Có thể là ứng dụng hệ thống hoặc được bảo vệ!"
    
    def unhide_app(self, package_name):
        """HIỆN lại ứng dụng đã ẩn"""
        if package_name not in self.hidden_apps:
            return False, "Ứng dụng chưa được ẩn!"
        
        # Thử các phương thức hiện
        methods = [
            (f'pm unhide {package_name}', 'pm unhide'),
            (f'pm enable {package_name}', 'pm enable'),
            (f'pm enable --user 0 {package_name}', 'pm enable --user 0')
        ]
        
        for cmd, method_name in methods:
            stdout, stderr, code = self.adb.run_adb_shell(cmd)
            if code == 0:
                del self.hidden_apps[package_name]
                self.save_data()
                return True, f"✅ Đã HIỆN lại ứng dụng {package_name} (Phương thức: {method_name})"
        
        return False, "❌ Không thể hiện ứng dụng!"
    
    def is_hidden(self, package_name):
        """Kiểm tra ứng dụng có đang ẩn không"""
        return package_name in self.hidden_apps
    
    def get_hidden_apps(self):
        """Lấy danh sách ứng dụng đã ẩn"""
        return list(self.hidden_apps.keys())
    
    def unhide_all(self):
        """Hiện tất cả ứng dụng đã ẩn"""
        apps = list(self.hidden_apps.keys())
        success_count = 0
        
        for app in apps:
            success, msg = self.unhide_app(app)
            if success:
                success_count += 1
        
        return True, f"✅ Đã hiện lại {success_count}/{len(apps)} ứng dụng"
    
    # ========== KHÓA ỨNG DỤNG ==========
    
    def lock_app_with_password(self, package_name, password):
        """KHÓA ứng dụng bằng mật khẩu"""
        if package_name in self.locked_apps:
            return False, "Ứng dụng đã được khóa!"
        
        hashed = hashlib.sha256(password.encode()).hexdigest()
        stdout, stderr, code = self.adb.run_adb_shell(f'pm disable --user 0 {package_name}')
        
        if code == 0:
            self.locked_apps[package_name] = {
                'type': 'password',
                'hash': hashed,
                'locked_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.app_passwords[package_name] = hashed
            self.lock_methods[package_name] = 'password'
            self.save_data()
            return True, f"✅ Đã KHÓA ứng dụng {package_name} bằng mật khẩu"
        else:
            return False, f"❌ Khóa thất bại: {stderr}"
    
    def lock_app_with_pin(self, package_name, pin):
        """KHÓA ứng dụng bằng PIN"""
        if package_name in self.locked_apps:
            return False, "Ứng dụng đã được khóa!"
        
        if len(pin) < 4 or not pin.isdigit():
            return False, "PIN phải có ít nhất 4 chữ số!"
        
        hashed = hashlib.sha256(pin.encode()).hexdigest()
        stdout, stderr, code = self.adb.run_adb_shell(f'pm disable --user 0 {package_name}')
        
        if code == 0:
            self.locked_apps[package_name] = {
                'type': 'pin',
                'hash': hashed,
                'locked_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.app_pins[package_name] = hashed
            self.lock_methods[package_name] = 'pin'
            self.save_data()
            return True, f"✅ Đã KHÓA ứng dụng {package_name} bằng PIN"
        else:
            return False, f"❌ Khóa thất bại: {stderr}"
    
    def unlock_app(self, package_name, credential):
        """MỞ KHÓA ứng dụng"""
        if package_name not in self.locked_apps:
            return False, "Ứng dụng chưa được khóa!"
        
        lock_type = self.lock_methods.get(package_name)
        hashed = hashlib.sha256(credential.encode()).hexdigest()
        
        if lock_type == 'password':
            if hashed != self.app_passwords.get(package_name):
                return False, "❌ Sai mật khẩu!"
        elif lock_type == 'pin':
            if hashed != self.app_pins.get(package_name):
                return False, "❌ Sai PIN!"
        else:
            return False, "❌ Phương thức khóa không hỗ trợ!"
        
        stdout, stderr, code = self.adb.run_adb_shell(f'pm enable --user 0 {package_name}')
        if code == 0:
            del self.locked_apps[package_name]
            if package_name in self.app_passwords:
                del self.app_passwords[package_name]
            if package_name in self.app_pins:
                del self.app_pins[package_name]
            if package_name in self.lock_methods:
                del self.lock_methods[package_name]
            self.save_data()
            return True, f"✅ Đã MỞ KHÓA ứng dụng {package_name}"
        else:
            return False, f"❌ Mở khóa thất bại: {stderr}"
    
    def is_locked(self, package_name):
        """Kiểm tra ứng dụng có đang khóa không"""
        return package_name in self.locked_apps
    
    def get_locked_apps(self):
        """Lấy danh sách ứng dụng đã khóa"""
        return list(self.locked_apps.keys())
    
    def get_lock_method(self, package_name):
        """Lấy phương thức khóa"""
        return self.lock_methods.get(package_name, None)
    
    def get_lock_info(self, package_name):
        """Lấy thông tin khóa"""
        if package_name in self.locked_apps:
            return self.locked_apps[package_name]
        return None
    
    def unlock_all(self):
        """Mở khóa tất cả ứng dụng"""
        apps = list(self.locked_apps.keys())
        success_count = 0
        
        for app in apps:
            stdout, stderr, code = self.adb.run_adb_shell(f'pm enable --user 0 {app}')
            if code == 0:
                if app in self.locked_apps:
                    del self.locked_apps[app]
                if app in self.app_passwords:
                    del self.app_passwords[app]
                if app in self.app_pins:
                    del self.app_pins[app]
                if app in self.lock_methods:
                    del self.lock_methods[app]
                success_count += 1
        
        self.save_data()
        return True, f"✅ Đã mở khóa {success_count}/{len(apps)} ứng dụng"
    
    def force_unlock(self, package_name):
        """Mở khóa cưỡng bức (bỏ qua mật khẩu)"""
        if package_name in self.locked_apps:
            stdout, stderr, code = self.adb.run_adb_shell(f'pm enable --user 0 {package_name}')
            if code == 0:
                del self.locked_apps[package_name]
                if package_name in self.app_passwords:
                    del self.app_passwords[package_name]
                if package_name in self.app_pins:
                    del self.app_pins[package_name]
                if package_name in self.lock_methods:
                    del self.lock_methods[package_name]
                self.save_data()
                return True, f"✅ Đã mở khóa cưỡng bức {package_name}"
            else:
                return False, f"❌ Mở khóa thất bại: {stderr}"
        return False, "❌ Ứng dụng chưa được khóa"

# ============ LỚP QUẢN LÝ ADB ============
class ADBManager:
    def __init__(self):
        self.adb_path = self.find_adb()
        self.connected = False
        self.device_id = None
        self.encryption_key = None
        self.cipher = None
        self.current_path = '/sdcard/'
        self.default_pin = "676767"
        
        self.auto_request_permissions()
        self.app_locker = AppLocker(self)
    
    def find_adb(self):
        """Tìm đường dẫn adb.exe"""
        common_paths = [
            r"D:\Troll Hiệp\AppPhone\adb.exe",
            r"C:\adb\adb.exe",
            r"C:\platform-tools\adb.exe",
            r"C:\Program Files\Android\platform-tools\adb.exe",
            r"C:\Users\{}\AppData\Local\Android\Sdk\platform-tools\adb.exe".format(os.getlogin())
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        try:
            result = subprocess.run(['where', 'adb'], capture_output=True, text=True)
            if result.returncode == 0:
                return 'adb'
        except:
            pass
        
        return None
    
    def auto_request_permissions(self):
        """Tự động xin quyền"""
        print("\n" + "="*60)
        print("   🔐 TỰ ĐỘNG XIN QUYỀN TRUY CẬP")
        print("="*60)
        
        if not self.adb_path:
            print("❌ Không tìm thấy ADB!")
            print("\n📥 Tải Platform Tools:")
            print("   https://developer.android.com/studio/releases/platform-tools")
            return
        
        print(f"✅ Tìm thấy ADB tại: {self.adb_path}")
        
        if not PermissionManager.is_admin():
            print("\n⚠️ Cần quyền Administrator")
            choice = input("👉 Có muốn cấp quyền Admin không? (y/n): ").strip().lower()
            if choice == 'y':
                PermissionManager.request_admin()
            else:
                print("⚠️ Một số chức năng có thể không hoạt động!")
        
        print("\n📱 KIỂM TRA QUYỀN USB DEBUGGING...")
        status, code, msg = PermissionManager.check_adb_connection()
        
        if not status:
            if code == "unauthorized":
                print(f"⚠️ {msg}")
                choice = input("👉 Có muốn gửi yêu cầu quyền không? (y/n): ").strip().lower()
                if choice == 'y':
                    PermissionManager.request_usb_debugging()
            else:
                print(f"❌ {msg}")
                print("\n💡 HƯỚNG DẪN KẾT NỐI:")
                print("   1️⃣ Bật USB Debugging trên điện thoại:")
                print("      - Cài đặt → Giới thiệu về điện thoại")
                print("      - Bấm 'Số bản dựng' 7 lần")
                print("      - Cài đặt → Tùy chọn nhà phát triển")
                print("      - Bật 'Gỡ lỗi USB'")
                print("   2️⃣ Cắm cáp USB vào máy tính")
                print("   3️⃣ Cho phép popup trên điện thoại")
        else:
            print(f"✅ {msg}")
    
    def run_adb(self, command):
        """Chạy lệnh ADB - KHÔNG ĐỆ QUY"""
        if not self.adb_path:
            return "", "ADB not found", 1
        
        if isinstance(command, str):
            cmd = [self.adb_path] + command.split()
        else:
            cmd = [self.adb_path] + command
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=30)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", 1
        except Exception as e:
            return "", str(e), 1
    
    def run_adb_shell(self, command):
        """Chạy lệnh adb shell - KHÔNG ĐỆ QUY"""
        if not self.adb_path:
            return "", "ADB not found", 1
        
        if isinstance(command, str):
            cmd = [self.adb_path, 'shell'] + command.split()
        else:
            cmd = [self.adb_path, 'shell'] + command
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=30)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", 1
        except Exception as e:
            return "", str(e), 1
    
    def connect(self):
        """Kết nối với thiết bị"""
        if not self.adb_path:
            print("❌ Không tìm thấy ADB!")
            return False
        
        stdout, stderr, code = self.run_adb('devices')
        
        if code != 0:
            print(f"❌ Lỗi ADB: {stderr}")
            return False
        
        lines = stdout.strip().split('\n')
        for line in lines[1:]:
            if line.strip() and 'device' in line and 'offline' not in line:
                self.device_id = line.split()[0]
                self.connected = True
                print(f"✅ Đã kết nối với: {self.device_id}")
                return True
        
        print("❌ Không tìm thấy thiết bị nào!")
        return False
    
    # ========== QUẢN LÝ ỨNG DỤNG ==========
    
    def get_all_apps(self):
        """Lấy danh sách tất cả ứng dụng"""
        stdout, stderr, code = self.run_adb_shell('pm list packages')
        if code == 0:
            apps = [line.replace('package:', '').strip() for line in stdout.split('\n') if line]
            return apps
        return []
    
    def get_system_apps(self):
        """Lấy danh sách ứng dụng hệ thống"""
        stdout, stderr, code = self.run_adb_shell('pm list packages -s')
        if code == 0:
            apps = [line.replace('package:', '').strip() for line in stdout.split('\n') if line]
            return apps
        return []
    
    def get_third_party_apps(self):
        """Lấy danh sách ứng dụng bên thứ 3"""
        stdout, stderr, code = self.run_adb_shell('pm list packages -3')
        if code == 0:
            apps = [line.replace('package:', '').strip() for line in stdout.split('\n') if line]
            return apps
        return []
    
    def get_app_info(self, package_name):
        """Lấy thông tin chi tiết ứng dụng"""
        stdout, stderr, code = self.run_adb_shell(f'dumpsys package {package_name}')
        if code == 0:
            return stdout
        return f"Không tìm thấy: {package_name}"
    
    def get_app_version(self, package_name):
        """Lấy phiên bản ứng dụng"""
        stdout, stderr, code = self.run_adb_shell(f'dumpsys package {package_name} | grep versionName')
        if code == 0:
            lines = stdout.split('\n')
            for line in lines:
                if 'versionName' in line:
                    return line.split('=')[-1].strip()
        return "Không xác định"
    
    def install_app(self, apk_path):
        """Cài đặt ứng dụng từ file APK"""
        if not os.path.exists(apk_path):
            return False, "File APK không tồn tại"
        
        stdout, stderr, code = self.run_adb(f'install "{apk_path}"')
        return code == 0, stdout if stdout else stderr
    
    def uninstall_app(self, package_name):
        """Gỡ cài đặt ứng dụng"""
        stdout, stderr, code = self.run_adb(f'uninstall {package_name}')
        return code == 0, stdout if stdout else stderr
    
    def start_app(self, package_name):
        """Mở ứng dụng - Tự động kiểm tra khóa"""
        if self.app_locker.is_locked(package_name):
            print(f"🔒 Ứng dụng {package_name} đã bị khóa!")
            return False
        
        stdout, stderr, code = self.run_adb_shell(f'monkey -p {package_name} 1')
        return code == 0
    
    def stop_app(self, package_name):
        """Dừng ứng dụng"""
        stdout, stderr, code = self.run_adb_shell(f'am force-stop {package_name}')
        return code == 0
    
    def backup_app(self, package_name, backup_path):
        """Sao lưu APK"""
        stdout, stderr, code = self.run_adb_shell(f'pm path {package_name}')
        if code == 0 and stdout:
            apk_path = stdout.replace('package:', '').strip()
            return self.download_file(apk_path, backup_path)
        return False, "Không tìm thấy APK"
    
    # ========== QUẢN LÝ FILE ==========
    
    def list_files(self, path=None):
        """Liệt kê file trong thư mục"""
        if path is None:
            path = self.current_path
        
        stdout, stderr, code = self.run_adb_shell(f'ls -la {path}')
        if code == 0:
            return stdout
        return f"❌ Lỗi: {stderr}"
    
    def upload_file(self, local_path, remote_path):
        """Upload file từ PC lên điện thoại"""
        if not os.path.exists(local_path):
            return False, "File không tồn tại trên PC"
        
        stdout, stderr, code = self.run_adb(f'push "{local_path}" "{remote_path}"')
        return code == 0, stdout if stdout else stderr
    
    def download_file(self, remote_path, local_path):
        """Download file từ điện thoại về PC"""
        stdout, stderr, code = self.run_adb(f'pull "{remote_path}" "{local_path}"')
        return code == 0, stdout if stdout else stderr
    
    def delete_file(self, path):
        """Xóa file trên điện thoại"""
        stdout, stderr, code = self.run_adb_shell(f'rm {path}')
        return code == 0, stdout if stdout else stderr
    
    def delete_folder(self, path):
        """Xóa thư mục trên điện thoại"""
        stdout, stderr, code = self.run_adb_shell(f'rm -rf {path}')
        return code == 0, stdout if stdout else stderr
    
    def create_folder(self, path):
        """Tạo thư mục mới"""
        stdout, stderr, code = self.run_adb_shell(f'mkdir -p {path}')
        return code == 0, stdout if stdout else stderr
    
    # ========== MÃ HÓA ==========
    
    def set_encryption_key(self, password):
        """Tạo khóa mã hóa từ mật khẩu"""
        password_bytes = password.encode()
        salt = b'android_secure_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        self.encryption_key = key
        self.cipher = Fernet(key)
        return True
    
    def encrypt_file(self, file_path, output_path=None):
        """Mã hóa file"""
        if not self.cipher:
            return False, "Chưa thiết lập khóa mã hóa!"
        
        if not os.path.exists(file_path):
            return False, "File không tồn tại"
        
        if not output_path:
            output_path = file_path + '.encrypted'
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            encrypted_data = self.cipher.encrypt(data)
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    def decrypt_file(self, encrypted_path, output_path=None):
        """Giải mã file"""
        if not self.cipher:
            return False, "Chưa thiết lập khóa mã hóa!"
        
        if not os.path.exists(encrypted_path):
            return False, "File không tồn tại"
        
        if not output_path:
            output_path = encrypted_path.replace('.encrypted', '.decrypted')
        
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    def encrypt_app(self, package_name, output_path=None):
        """Mã hóa ứng dụng (APK)"""
        if not output_path:
            output_path = f"{package_name}_encrypted.enc"
        
        stdout, stderr, code = self.run_adb_shell(f'pm path {package_name}')
        if code != 0 or not stdout:
            return False, "Không tìm thấy APK"
        
        apk_path = stdout.replace('package:', '').strip()
        temp_apk = f"temp_{package_name}_{int(time.time())}.apk"
        success, msg = self.download_file(apk_path, temp_apk)
        
        if not success:
            return False, f"Tải APK thất bại: {msg}"
        
        success, encrypted_path = self.encrypt_file(temp_apk, output_path)
        
        if os.path.exists(temp_apk):
            os.remove(temp_apk)
        
        return success, encrypted_path if success else encrypted_path
    
    # ========== MỞ KHÓA MÀN HÌNH ==========
    
    def unlock_screen_default_pin(self):
        """Mở khóa điện thoại bằng PIN 676767"""
        print("🔑 Đang mở khóa bằng PIN: 676767")
        for digit in self.default_pin:
            self.run_adb_shell(f'input keyevent KEYCODE_{digit}')
            time.sleep(0.3)
        self.run_adb_shell('input keyevent KEYCODE_ENTER')
        time.sleep(1)
        return True
    
    def lock_screen(self):
        """Khóa màn hình"""
        self.run_adb_shell('input keyevent KEYCODE_POWER')
        return True

# ============ MENU ============
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("\n" + "="*60)
    print(f"   {title}")
    print("="*60)

def show_hide_menu(adb):
    """Menu ẩn/hiện ứng dụng"""
    while True:
        clear_screen()
        print_header("👻 ẨN/HIỆN ỨNG DỤNG")
        
        hidden_apps = adb.app_locker.get_hidden_apps()
        print(f"  📱 Ứng dụng đã ẩn: {len(hidden_apps)}")
        if hidden_apps:
            print("  📋 Danh sách:")
            for app in hidden_apps:
                print(f"     - {app}")
        print("="*60)
        print("  1. 👻 ẨN ứng dụng (không tìm thấy trên điện thoại)")
        print("  2. 👀 HIỆN lại ứng dụng đã ẩn")
        print("  3. 👀 HIỆN TẤT CẢ ứng dụng đã ẩn")
        print("  4. 📋 Xem danh sách ứng dụng đã ẩn")
        print("  0. 🔙 Quay lại")
        print("="*60)
        
        choice = input("👉 Chọn: ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            print("\n📱 CHỌN ỨNG DỤNG CẦN ẨN:")
            print("-"*60)
            apps = adb.get_third_party_apps()
            if not apps:
                print("❌ Không có ứng dụng bên thứ 3 nào!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            for i, app in enumerate(apps, 1):
                hidden = "👻" if adb.app_locker.is_hidden(app) else " "
                locked = "🔒" if adb.app_locker.is_locked(app) else " "
                print(f"  {i:3}. {hidden}{locked} {app}")
            
            print("\n" + "-"*60)
            app_choice = input("👉 Nhập số thứ tự hoặc tên gói: ").strip()
            
            if app_choice.isdigit():
                idx = int(app_choice) - 1
                if 0 <= idx < len(apps):
                    package = apps[idx]
                else:
                    print("❌ Số thứ tự không hợp lệ!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
            else:
                package = app_choice
            
            if package:
                if adb.app_locker.is_hidden(package):
                    print(f"⚠️ Ứng dụng {package} đã được ẩn!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
                
                if adb.app_locker.is_locked(package):
                    print(f"⚠️ Ứng dụng {package} đang bị khóa!")
                    print("💡 Vui lòng mở khóa trước khi ẩn")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
                
                confirm = input(f"⚠️ ẨN ứng dụng {package}? (y/n): ").strip().lower()
                if confirm == 'y':
                    success, msg = adb.app_locker.hide_app(package)
                    print(msg)
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '2':
            hidden_apps = adb.app_locker.get_hidden_apps()
            if not hidden_apps:
                print("✅ Không có ứng dụng nào đang bị ẩn!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            print("\n👀 CHỌN ỨNG DỤNG CẦN HIỆN:")
            print("-"*60)
            for i, app in enumerate(hidden_apps, 1):
                print(f"  {i:3}. {app}")
            
            print("\n" + "-"*60)
            app_choice = input("👉 Nhập số thứ tự hoặc tên gói: ").strip()
            
            if app_choice.isdigit():
                idx = int(app_choice) - 1
                if 0 <= idx < len(hidden_apps):
                    package = hidden_apps[idx]
                else:
                    print("❌ Số thứ tự không hợp lệ!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
            else:
                package = app_choice
            
            if package:
                success, msg = adb.app_locker.unhide_app(package)
                print(msg)
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '3':
            hidden_apps = adb.app_locker.get_hidden_apps()
            if not hidden_apps:
                print("✅ Không có ứng dụng nào đang bị ẩn!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            confirm = input("⚠️ Hiện TẤT CẢ ứng dụng đã ẩn? (y/n): ").strip().lower()
            if confirm == 'y':
                success, msg = adb.app_locker.unhide_all()
                print(msg)
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '4':
            hidden_apps = adb.app_locker.get_hidden_apps()
            if hidden_apps:
                print("\n👻 DANH SÁCH ỨNG DỤNG ĐÃ ẨN:")
                print("-"*60)
                for i, app in enumerate(hidden_apps, 1):
                    info = adb.app_locker.hidden_apps.get(app, {})
                    hidden_time = info.get('hidden_at', 'Không rõ')
                    method = info.get('method', 'Không rõ')
                    print(f"  {i:3}. {app}")
                    print(f"       Phương thức: {method}")
                    print(f"       Thời gian ẩn: {hidden_time}")
            else:
                print("✅ Không có ứng dụng nào bị ẩn")
            input("\nNhấn Enter để tiếp tục...")
        
        else:
            print("⚠️ Lựa chọn không hợp lệ!")
            input("\nNhấn Enter để tiếp tục...")

def show_lock_menu(adb):
    """Menu khóa ứng dụng"""
    while True:
        clear_screen()
        print_header("🔒 KHÓA ỨNG DỤNG")
        
        locked_apps = adb.app_locker.get_locked_apps()
        print(f"  📱 Ứng dụng đã khóa: {len(locked_apps)}")
        if locked_apps:
            print("  📋 Danh sách:")
            for app in locked_apps:
                method = adb.app_locker.get_lock_method(app)
                method_name = "Mật khẩu" if method == "password" else "PIN"
                print(f"     - {app} ({method_name})")
        print("="*60)
        print("  1. 🔒 Khóa bằng MẬT KHẨU")
        print("  2. 🔒 Khóa bằng PIN")
        print("  3. 🔓 Mở khóa")
        print("  4. 🔓 Mở khóa CƯỠNG BỨC")
        print("  5. 🔓 Mở khóa TẤT CẢ")
        print("  6. 📋 Xem danh sách khóa")
        print("  0. 🔙 Quay lại")
        print("="*60)
        
        choice = input("👉 Chọn: ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            print("\n📱 CHỌN ỨNG DỤNG CẦN KHÓA:")
            print("-"*60)
            apps = adb.get_third_party_apps()
            if not apps:
                print("❌ Không có ứng dụng bên thứ 3 nào!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            for i, app in enumerate(apps, 1):
                hidden = "👻" if adb.app_locker.is_hidden(app) else " "
                locked = "🔒" if adb.app_locker.is_locked(app) else " "
                print(f"  {i:3}. {hidden}{locked} {app}")
            
            print("\n" + "-"*60)
            app_choice = input("👉 Nhập số thứ tự hoặc tên gói: ").strip()
            
            if app_choice.isdigit():
                idx = int(app_choice) - 1
                if 0 <= idx < len(apps):
                    package = apps[idx]
                else:
                    print("❌ Số thứ tự không hợp lệ!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
            else:
                package = app_choice
            
            if package:
                if adb.app_locker.is_locked(package):
                    print(f"⚠️ Ứng dụng {package} đã được khóa!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
                
                password = input("🔑 Nhập mật khẩu: ").strip()
                if password:
                    confirm = input("🔑 Nhập lại mật khẩu: ").strip()
                    if password == confirm:
                        success, msg = adb.app_locker.lock_app_with_password(package, password)
                        print(msg)
                    else:
                        print("❌ Mật khẩu không khớp!")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '2':
            print("\n📱 CHỌN ỨNG DỤNG CẦN KHÓA:")
            print("-"*60)
            apps = adb.get_third_party_apps()
            if not apps:
                print("❌ Không có ứng dụng bên thứ 3 nào!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            for i, app in enumerate(apps, 1):
                hidden = "👻" if adb.app_locker.is_hidden(app) else " "
                locked = "🔒" if adb.app_locker.is_locked(app) else " "
                print(f"  {i:3}. {hidden}{locked} {app}")
            
            print("\n" + "-"*60)
            app_choice = input("👉 Nhập số thứ tự hoặc tên gói: ").strip()
            
            if app_choice.isdigit():
                idx = int(app_choice) - 1
                if 0 <= idx < len(apps):
                    package = apps[idx]
                else:
                    print("❌ Số thứ tự không hợp lệ!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
            else:
                package = app_choice
            
            if package:
                if adb.app_locker.is_locked(package):
                    print(f"⚠️ Ứng dụng {package} đã được khóa!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
                
                pin = input("🔑 Nhập PIN (4-6 chữ số): ").strip()
                if pin and pin.isdigit() and len(pin) >= 4:
                    confirm = input("🔑 Nhập lại PIN: ").strip()
                    if pin == confirm:
                        success, msg = adb.app_locker.lock_app_with_pin(package, pin)
                        print(msg)
                    else:
                        print("❌ PIN không khớp!")
                else:
                    print("❌ PIN phải có ít nhất 4 chữ số!")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '3':
            locked_apps = adb.app_locker.get_locked_apps()
            if not locked_apps:
                print("✅ Không có ứng dụng nào đang bị khóa!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            print("\n🔓 CHỌN ỨNG DỤNG CẦN MỞ KHÓA:")
            print("-"*60)
            for i, app in enumerate(locked_apps, 1):
                method = adb.app_locker.get_lock_method(app)
                method_name = "Mật khẩu" if method == "password" else "PIN"
                print(f"  {i:3}. {app} ({method_name})")
            
            print("\n" + "-"*60)
            app_choice = input("👉 Nhập số thứ tự hoặc tên gói: ").strip()
            
            if app_choice.isdigit():
                idx = int(app_choice) - 1
                if 0 <= idx < len(locked_apps):
                    package = locked_apps[idx]
                else:
                    print("❌ Số thứ tự không hợp lệ!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
            else:
                package = app_choice
            
            if package and package in locked_apps:
                credential = input("🔑 Nhập mật khẩu/PIN: ").strip()
                if credential:
                    success, msg = adb.app_locker.unlock_app(package, credential)
                    print(msg)
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '4':
            locked_apps = adb.app_locker.get_locked_apps()
            if not locked_apps:
                print("✅ Không có ứng dụng nào đang bị khóa!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            print("\n🔓 CHỌN ỨNG DỤNG CẦN MỞ KHÓA CƯỠNG BỨC:")
            print("-"*60)
            for i, app in enumerate(locked_apps, 1):
                print(f"  {i:3}. {app}")
            
            print("\n" + "-"*60)
            app_choice = input("👉 Nhập số thứ tự hoặc tên gói: ").strip()
            
            if app_choice.isdigit():
                idx = int(app_choice) - 1
                if 0 <= idx < len(locked_apps):
                    package = locked_apps[idx]
                else:
                    print("❌ Số thứ tự không hợp lệ!")
                    input("\nNhấn Enter để tiếp tục...")
                    continue
            else:
                package = app_choice
            
            if package:
                confirm = input(f"⚠️ Mở khóa cưỡng bức {package}? (y/n): ").strip().lower()
                if confirm == 'y':
                    success, msg = adb.app_locker.force_unlock(package)
                    print(msg)
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '5':
            locked_apps = adb.app_locker.get_locked_apps()
            if not locked_apps:
                print("✅ Không có ứng dụng nào đang bị khóa!")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            confirm = input("⚠️ Mở khóa TẤT CẢ ứng dụng? (y/n): ").strip().lower()
            if confirm == 'y':
                success, msg = adb.app_locker.unlock_all()
                print(msg)
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '6':
            locked_apps = adb.app_locker.get_locked_apps()
            if locked_apps:
                print("\n🔒 DANH SÁCH ỨNG DỤNG ĐÃ KHÓA:")
                print("-"*60)
                for i, app in enumerate(locked_apps, 1):
                    method = adb.app_locker.get_lock_method(app)
                    method_name = "Mật khẩu" if method == "password" else "PIN"
                    info = adb.app_locker.get_lock_info(app)
                    locked_time = info.get('locked_at', 'Không rõ') if info else 'Không rõ'
                    print(f"  {i:3}. {app}")
                    print(f"       Phương thức: {method_name}")
                    print(f"       Thời gian khóa: {locked_time}")
            else:
                print("✅ Không có ứng dụng nào bị khóa")
            input("\nNhấn Enter để tiếp tục...")
        
        else:
            print("⚠️ Lựa chọn không hợp lệ!")
            input("\nNhấn Enter để tiếp tục...")

def show_apps_menu(adb):
    """Menu quản lý ứng dụng"""
    while True:
        clear_screen()
        print_header("📱 QUẢN LÝ ỨNG DỤNG")
        print("  1. 📋 Xem tất cả ứng dụng")
        print("  2. 📋 Xem ứng dụng hệ thống")
        print("  3. 📋 Xem ứng dụng bên thứ 3")
        print("  4. 🔍 Xem thông tin ứng dụng")
        print("  5. 📦 Cài đặt APK")
        print("  6. 🗑️ Gỡ cài đặt ứng dụng")
        print("  7. 🚀 Mở ứng dụng")
        print("  8. 🛑 Dừng ứng dụng")
        print("  9. 💾 Sao lưu APK")
        print(" 10. 🔐 Mã hóa APK")
        print(" 11. 🔓 Giải mã APK")
        print(" 12. 👻 ẨN/HIỆN ứng dụng")
        print(" 13. 🔒 KHÓA/MỞ KHÓA ứng dụng")
        print("  0. 🔙 Quay lại")
        print("="*60)
        
        choice = input("👉 Chọn: ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            apps = adb.get_all_apps()
            print(f"\n📋 Tổng: {len(apps)} ứng dụng")
            for i, app in enumerate(apps, 1):
                hidden = "👻" if adb.app_locker.is_hidden(app) else " "
                locked = "🔒" if adb.app_locker.is_locked(app) else " "
                print(f"  {i:3}. {hidden}{locked} {app}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '2':
            apps = adb.get_system_apps()
            print(f"\n📋 Tổng: {len(apps)} ứng dụng hệ thống")
            for i, app in enumerate(apps, 1):
                print(f"  {i:3}. {app}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '3':
            apps = adb.get_third_party_apps()
            print(f"\n📋 Tổng: {len(apps)} ứng dụng bên thứ 3")
            for i, app in enumerate(apps, 1):
                hidden = "👻" if adb.app_locker.is_hidden(app) else " "
                locked = "🔒" if adb.app_locker.is_locked(app) else " "
                print(f"  {i:3}. {hidden}{locked} {app}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '4':
            package = input("📦 Nhập tên gói: ").strip()
            if package:
                print(f"\n🔍 THÔNG TIN {package}:")
                print("-"*60)
                version = adb.get_app_version(package)
                print(f"  Phiên bản: {version}")
                hidden = "Có" if adb.app_locker.is_hidden(package) else "Không"
                locked = "Có" if adb.app_locker.is_locked(package) else "Không"
                print(f"  Đã ẩn: {hidden}")
                print(f"  Đã khóa: {locked}")
                print("\n" + adb.get_app_info(package))
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '5':
            apk_path = input("📂 Đường dẫn file APK: ").strip()
            if apk_path and os.path.exists(apk_path):
                print("📦 Đang cài đặt...")
                success, msg = adb.install_app(apk_path)
                if success:
                    print(f"✅ {msg}")
                else:
                    print(f"❌ {msg}")
            else:
                print("❌ File không tồn tại!")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '6':
            package = input("📦 Nhập tên gói cần gỡ: ").strip()
            if package:
                confirm = input(f"⚠️ Gỡ {package}? (y/n): ").strip().lower()
                if confirm == 'y':
                    success, msg = adb.uninstall_app(package)
                    if success:
                        print(f"✅ {msg}")
                    else:
                        print(f"❌ {msg}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '7':
            package = input("📦 Nhập tên gói cần mở: ").strip()
            if package:
                if adb.start_app(package):
                    print("✅ Đã mở ứng dụng")
                else:
                    print("❌ Mở thất bại")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '8':
            package = input("📦 Nhập tên gói cần dừng: ").strip()
            if package:
                if adb.stop_app(package):
                    print("✅ Đã dừng ứng dụng")
                else:
                    print("❌ Dừng thất bại")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '9':
            package = input("📦 Nhập tên gói cần sao lưu: ").strip()
            if package:
                save_path = input("💾 Đường dẫn lưu APK: ").strip()
                if save_path:
                    print("💾 Đang sao lưu...")
                    success, msg = adb.backup_app(package, save_path)
                    if success:
                        print(f"✅ Đã lưu tại: {save_path}")
                    else:
                        print(f"❌ {msg}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '10':
            package = input("📦 Nhập tên gói cần mã hóa: ").strip()
            if package:
                save_path = input("💾 Đường dẫn lưu file mã hóa: ").strip()
                if save_path:
                    password = input("🔑 Nhập mật khẩu: ").strip()
                    if password:
                        adb.set_encryption_key(password)
                        print("🔐 Đang mã hóa APK...")
                        success, msg = adb.encrypt_app(package, save_path)
                        if success:
                            print(f"✅ Mã hóa thành công: {msg}")
                        else:
                            print(f"❌ {msg}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '11':
            enc_path = input("📂 Đường dẫn file mã hóa: ").strip()
            if enc_path and os.path.exists(enc_path):
                save_path = input("💾 Đường dẫn lưu APK: ").strip()
                if save_path:
                    password = input("🔑 Nhập mật khẩu: ").strip()
                    if password:
                        adb.set_encryption_key(password)
                        print("🔓 Đang giải mã...")
                        success, msg = adb.decrypt_file(enc_path, save_path)
                        if success:
                            print(f"✅ Giải mã thành công: {msg}")
                        else:
                            print(f"❌ {msg}")
            else:
                print("❌ File không tồn tại!")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '12':
            show_hide_menu(adb)
        
        elif choice == '13':
            show_lock_menu(adb)
        
        else:
            print("⚠️ Lựa chọn không hợp lệ!")
            input("\nNhấn Enter để tiếp tục...")

def show_file_menu(adb):
    """Menu quản lý file"""
    current_path = '/sdcard/'
    
    while True:
        clear_screen()
        print_header("📂 QUẢN LÝ FILE")
        print(f"  📍 Đường dẫn: {current_path}")
        print("-"*60)
        print("  1. 📂 Xem danh sách file")
        print("  2. 📤 Upload file lên điện thoại")
        print("  3. 📥 Download file về PC")
        print("  4. 🗑️ Xóa file/thư mục")
        print("  5. 📁 Tạo thư mục")
        print("  6. 📂 Đổi thư mục")
        print("  0. 🔙 Quay lại")
        print("="*60)
        
        choice = input("👉 Chọn: ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            print(f"\n📂 DANH SÁCH FILE trong {current_path}:")
            print("-"*60)
            print(adb.list_files(current_path))
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '2':
            local = input("📤 Đường dẫn file trên PC: ").strip()
            remote = input("📥 Đường dẫn đích: ").strip()
            if local and remote:
                success, msg = adb.upload_file(local, remote)
                print(f"{'✅' if success else '❌'} {msg}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '3':
            remote = input("📤 Đường dẫn file trên điện thoại: ").strip()
            local = input("📥 Đường dẫn lưu trên PC: ").strip()
            if remote and local:
                success, msg = adb.download_file(remote, local)
                print(f"{'✅' if success else '❌'} {msg}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '4':
            path = input("🗑️ Đường dẫn cần xóa: ").strip()
            if path:
                confirm = input(f"⚠️ Xóa {path}? (y/n): ").strip().lower()
                if confirm == 'y':
                    if path.endswith('/') or path.endswith('\\'):
                        success, msg = adb.delete_folder(path)
                    else:
                        success, msg = adb.delete_file(path)
                    print(f"{'✅' if success else '❌'} {msg}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '5':
            path = input("📁 Đường dẫn thư mục mới: ").strip()
            if path:
                success, msg = adb.create_folder(path)
                print(f"{'✅' if success else '❌'} {msg}")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '6':
            new_path = input("📁 Đường dẫn mới: ").strip()
            if new_path:
                current_path = new_path
                print(f"✅ Đã chuyển đến: {current_path}")
            input("\nNhấn Enter để tiếp tục...")
        
        else:
            print("⚠️ Lựa chọn không hợp lệ!")
            input("\nNhấn Enter để tiếp tục...")

def show_encryption_menu(adb):
    """Menu mã hóa file trên PC"""
    while True:
        clear_screen()
        print_header("🔐 MÃ HÓA FILE TRÊN PC")
        print("  1. 🔐 Mã hóa file")
        print("  2. 🔓 Giải mã file")
        print("  0. 🔙 Quay lại")
        print("="*60)
        
        choice = input("👉 Chọn: ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            file_path = input("📂 Đường dẫn file cần mã hóa: ").strip()
            if file_path and os.path.exists(file_path):
                password = input("🔑 Nhập mật khẩu: ").strip()
                if password:
                    adb.set_encryption_key(password)
                    save_path = input("💾 Đường dẫn lưu (Enter để tự động): ").strip()
                    save_path = save_path if save_path else None
                    success, result = adb.encrypt_file(file_path, save_path)
                    print(f"{'✅' if success else '❌'} {result}")
            else:
                print("❌ File không tồn tại!")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '2':
            enc_path = input("📂 Đường dẫn file mã hóa: ").strip()
            if enc_path and os.path.exists(enc_path):
                password = input("🔑 Nhập mật khẩu: ").strip()
                if password:
                    adb.set_encryption_key(password)
                    save_path = input("💾 Đường dẫn lưu (Enter để tự động): ").strip()
                    save_path = save_path if save_path else None
                    success, result = adb.decrypt_file(enc_path, save_path)
                    print(f"{'✅' if success else '❌'} {result}")
            else:
                print("❌ File không tồn tại!")
            input("\nNhấn Enter để tiếp tục...")
        
        else:
            print("⚠️ Lựa chọn không hợp lệ!")
            input("\nNhấn Enter để tiếp tục...")

def show_system_info(adb):
    """Hiển thị thông tin hệ thống"""
    clear_screen()
    print_header("📊 THÔNG TIN HỆ THỐNG")
    
    info = {
        'Model': 'ro.product.model',
        'Manufacturer': 'ro.product.manufacturer',
        'Android Version': 'ro.build.version.release',
        'SDK Version': 'ro.build.version.sdk',
        'CPU ABI': 'ro.product.cpu.abi',
        'Serial': 'ro.serialno'
    }
    
    for name, prop in info.items():
        stdout, stderr, code = adb.run_adb_shell(f'getprop {prop}')
        if code == 0:
            print(f"  {name}: {stdout}")
    
    print("\n🔋 THÔNG TIN PIN:")
    stdout, stderr, code = adb.run_adb_shell('dumpsys battery')
    if code == 0:
        lines = stdout.split('\n')
        for line in lines:
            if 'level' in line or 'status' in line or 'health' in line:
                print(f"  {line.strip()}")
    
    print("\n💾 THÔNG TIN BỘ NHỚ:")
    stdout, stderr, code = adb.run_adb_shell('df -h')
    if code == 0:
        lines = stdout.split('\n')
        for line in lines:
            if '/data' in line or '/storage' in line or '/sdcard' in line:
                print(f"  {line}")
    
    input("\nNhấn Enter để tiếp tục...")

# ============ MAIN ============
def main():
    """Menu chính"""
    # Cài đặt thư viện
    try:
        import cryptography
    except ImportError:
        print("📦 Đang cài đặt thư viện cryptography...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'cryptography'], capture_output=True)
        print("✅ Đã cài đặt xong!")
    
    # Khởi tạo
    adb = ADBManager()
    
    print("\n" + "="*60)
    print("   📱 ANDROID SECURITY MANAGER")
    print("="*60)
    
    # Kết nối
    if not adb.connect():
        print("\n❌ Không thể kết nối với điện thoại!")
        print("\n💡 Hãy thử:")
        print("   - Cắm lại cáp USB")
        print("   - Mở khóa điện thoại")
        print("   - Tắt/bật lại USB Debugging")
        print("   - Khởi động lại ADB: adb kill-server && adb start-server")
        input("\nNhấn Enter để thoát...")
        return
    
    # Menu chính
    while True:
        clear_screen()
        print_header("📱 ANDROID SECURITY MANAGER")
        print(f"  🔌 Thiết bị: {adb.device_id}")
        print(f"  📂 Đường dẫn: {adb.current_path}")
        hidden_count = len(adb.app_locker.get_hidden_apps())
        locked_count = len(adb.app_locker.get_locked_apps())
        print(f"  👻 Ẩn: {hidden_count} | 🔒 Khóa: {locked_count}")
        print("="*60)
        print("  1. 🔓 Mở khóa điện thoại (PIN 676767)")
        print("  2. 📱 Quản lý ứng dụng")
        print("  3. 📂 Quản lý file")
        print("  4. 🔐 Mã hóa/giải mã file (PC)")
        print("  5. 📊 Thông tin hệ thống")
        print("  0. 🚪 Thoát")
        print("="*60)
        
        choice = input("👉 Chọn chức năng: ").strip()
        
        if choice == '0':
            print("\n👋 Tạm biệt!")
            break
        
        elif choice == '1':
            print("\n🔑 Đang mở khóa điện thoại...")
            adb.unlock_screen_default_pin()
            print("✅ Đã mở khóa!")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '2':
            show_apps_menu(adb)
        
        elif choice == '3':
            show_file_menu(adb)
        
        elif choice == '4':
            show_encryption_menu(adb)
        
        elif choice == '5':
            show_system_info(adb)
        
        else:
            print("⚠️ Lựa chọn không hợp lệ!")
            input("\nNhấn Enter để tiếp tục...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        input("\nNhấn Enter để thoát...")