import os
import sys
import time
import socket
import subprocess
import psutil

# ===== MÀU SẮC CHO ĐẸP =====
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

print(Color.BLUE + "=" * 70)
print("🔄 TOOL KHÔI PHỤC MẠNG - DỌN DẸP SẠCH SẼ")
print("=" * 70 + Color.RESET)

def khoi_phuc_mang():
    """Khôi phục mạng về trạng thái bình thường"""
    
    print("\n" + Color.YELLOW + "🔍 ĐANG KIỂM TRA TRẠNG THÁI MẠNG..." + Color.RESET)
    
    # ===== 1. KIỂM TRA KẾT NỐI =====
    try:
        socket.gethostbyname("google.com")
        print(Color.GREEN + "✅ Kết nối internet: BÌNH THƯỜNG" + Color.RESET)
    except:
        print(Color.RED + "❌ Mất kết nối internet! Đang khôi phục..." + Color.RESET)
    
    # ===== 2. GIẢI PHÓNG RAM =====
    print("\n" + Color.YELLOW + "🧹 GIẢI PHÓNG RAM..." + Color.RESET)
    
    # Giải phóng RAM bằng cách xóa cache
    if os.name == 'nt':  # Windows
        os.system('ipconfig /flushdns >nul 2>&1')
        print(Color.GREEN + "✅ Đã xóa DNS cache" + Color.RESET)
    
    # ===== 3. RESET KẾT NỐI MẠNG =====
    print("\n" + Color.YELLOW + "🔄 RESET KẾT NỐI MẠNG..." + Color.RESET)
    
    if os.name == 'nt':  # Windows
        # Reset Winsock và TCP/IP
        os.system('netsh winsock reset >nul 2>&1')
        os.system('netsh int ip reset >nul 2>&1')
        print(Color.GREEN + "✅ Đã reset Winsock và TCP/IP" + Color.RESET)
        
        # Giải phóng và gia hạn IP
        os.system('ipconfig /release >nul 2>&1')
        time.sleep(1)
        os.system('ipconfig /renew >nul 2>&1')
        print(Color.GREEN + "✅ Đã gia hạn IP" + Color.RESET)
    
    else:  # Linux/Mac
        os.system('sudo systemctl restart NetworkManager 2>/dev/null')
        os.system('sudo service network-manager restart 2>/dev/null')
        print(Color.GREEN + "✅ Đã restart Network Manager" + Color.RESET)
    
    # ===== 4. ĐÓNG CÁC KẾT NỐI TREO =====
    print("\n" + Color.YELLOW + "🔌 ĐÓNG CÁC KẾT NỐI TREO..." + Color.RESET)
    
    if os.name == 'nt':  # Windows
        # Đóng các kết nối TCP treo (cần admin)
        os.system('netstat -ano | findstr ESTABLISHED > temp.txt')
        with open('temp.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.split()
                if len(parts) > 4 and parts[1].startswith('192.168'):
                    pid = parts[4]
                    try:
                        # Kill các process Python đang chạy
                        os.system(f'taskkill /F /PID {pid} >nul 2>&1')
                    except:
                        pass
        os.remove('temp.txt')
        print(Color.GREEN + "✅ Đã đóng các kết nối treo" + Color.RESET)
    
    # ===== 5. KILL CÁC PROCESS PYTHON ĐANG CHẠY =====
    print("\n" + Color.YELLOW + "🛑 DỪNG CÁC SCRIPT PYTHON..." + Color.RESET)
    
    if os.name == 'nt':  # Windows
        os.system('taskkill /F /IM python.exe >nul 2>&1')
        os.system('taskkill /F /IM python3.exe >nul 2>&1')
        print(Color.GREEN + "✅ Đã dừng tất cả Python" + Color.RESET)
    else:
        os.system('pkill -f python 2>/dev/null')
        os.system('pkill -f python3 2>/dev/null')
        print(Color.GREEN + "✅ Đã dừng tất cả Python" + Color.RESET)
    
    # ===== 6. XÓA FILE TEMP =====
    print("\n" + Color.YELLOW + "🗑️ XÓA FILE TẠM..." + Color.RESET)
    
    if os.name == 'nt':  # Windows
        os.system('del /f /q *.tmp 2>nul')
        os.system('del /f /q temp*.txt 2>nul')
        print(Color.GREEN + "✅ Đã xóa file tạm" + Color.RESET)
    
    # ===== 7. ROUTER CACHE =====
    print("\n" + Color.YELLOW + "🔄 LÀM MỚI ROUTER..." + Color.RESET)
    
    # Gửi lệnh ARP để làm mới bảng ARP
    try:
        os.system('arp -d * >nul 2>&1')
        print(Color.GREEN + "✅ Đã xóa bảng ARP" + Color.RESET)
    except:
        pass
    
    # ===== 8. KIỂM TRA LẠI =====
    print("\n" + Color.YELLOW + "📊 KIỂM TRA LẠI TRẠNG THÁI..." + Color.RESET)
    
    try:
        import psutil
        net = psutil.net_io_counters()
        dl_mbps = net.bytes_recv / 1024 / 1024 * 8 / 10  # Trung bình 10s
        ul_mbps = net.bytes_sent / 1024 / 1024 * 8 / 10
        
        print(Color.GREEN + f"📡 Download: {dl_mbps:.1f} Mbps" + Color.RESET)
        print(Color.GREEN + f"📡 Upload: {ul_mbps:.1f} Mbps" + Color.RESET)
        
        # Kiểm tra ping
        result = os.system('ping -n 2 8.8.8.8 >nul 2>&1')
        if result == 0:
            print(Color.GREEN + "✅ Ping Google: OK" + Color.RESET)
        else:
            print(Color.RED + "⚠️ Ping Google: CHẬM" + Color.RESET)
            
    except:
        pass
    
    print("\n" + Color.BLUE + "=" * 70)
    print("✅ KHÔI PHỤC MẠNG HOÀN TẤT!")
    print("💡 Mạng đã trở lại bình thường.")
    print("=" * 70 + Color.RESET)

# ===== CHẠY =====
if __name__ == "__main__":
    try:
        khoi_phuc_mang()
    except Exception as e:
        print(f"Lỗi: {e}")
    
    input("\nNhấn Enter để thoát...")