# -*- coding: utf-8 -*-
"""
MÃ HÓA CHỮ - v16.0 (Desktop giống Web)
- Giao diện giống hệt web: toggle tab, panel grid, modal, toast
"""

import tkinter as tk
from tkinter import messagebox
import base64, codecs, unicodedata, urllib.parse, html, hashlib, os, json
import zlib, gzip, time, threading

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

try:
    import bcrypt
    BCRYPT_OK = True
except ImportError:
    BCRYPT_OK = False

try:
    from Crypto.Cipher import DES, DES3, Blowfish, ARC4, ChaCha20
    PYCRYPTO_OK = True
except ImportError:
    PYCRYPTO_OK = False

# ============================================================
# MÀU SẮC (giống web)
# ============================================================
C = {
    "bg":           "#0a1428",
    "bg2":          "#0f1e38",
    "bg3":          "#142850",
    "border":       "#1e3a5f",
    "border_glow":  "#2d5fa8",
    "fg":           "#e6f0ff",
    "fg_dim":       "#7a9bc4",
    "blue":         "#2563eb",
    "blue_light":   "#3b82f6",
    "blue_glow":    "#60a5fa",
    "purple":       "#7c3aed",
    "purple_light": "#8b5cf6",
    "cyan":         "#06b6d4",
    "green":        "#10b981",
    "green_light":  "#34d399",
    "red":          "#ef4444",
    "yellow":       "#fbbf24",
    "pink":         "#ec4899",
    "orange":       "#f97316",
}

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{int(max(0, min(255, r))):02x}{int(max(0, min(255, g))):02x}{int(max(0, min(255, b))):02x}"

def lerp_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1+(r2-r1)*t, g1+(g2-g1)*t, b1+(b2-b1)*t)

# ============================================================
# BẢNG MÃ
# ============================================================
MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.',
    '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    ' ': '/'
}
MORSE_REVERSE = {v: k for k, v in MORSE_CODE.items()}

TELEX_MAP = {
    'ă': 'aw', 'â': 'aa', 'ê': 'ee', 'ô': 'oo', 'ơ': 'ow', 'ư': 'uw', 'đ': 'dd',
    'á': 'as', 'à': 'af', 'ả': 'ar', 'ã': 'ax', 'ạ': 'aj',
    'ấ': 'aas', 'ầ': 'aaf', 'ẩ': 'aar', 'ẫ': 'aax', 'ậ': 'aaj',
    'ắ': 'aws', 'ằ': 'awf', 'ẳ': 'awr', 'ẵ': 'awx', 'ặ': 'awj',
    'é': 'es', 'è': 'ef', 'ẻ': 'er', 'ẽ': 'ex', 'ẹ': 'ej',
    'ế': 'ees', 'ề': 'eef', 'ể': 'eer', 'ễ': 'eex', 'ệ': 'eej',
    'í': 'is', 'ì': 'if', 'ỉ': 'ir', 'ĩ': 'ix', 'ị': 'ij',
    'ó': 'os', 'ò': 'of', 'ỏ': 'or', 'õ': 'ox', 'ọ': 'oj',
    'ố': 'oos', 'ồ': 'oof', 'ổ': 'oor', 'ỗ': 'oox', 'ộ': 'ooj',
    'ớ': 'ows', 'ờ': 'owf', 'ở': 'owr', 'ỡ': 'owx', 'ợ': 'owj',
    'ú': 'us', 'ù': 'uf', 'ủ': 'ur', 'ũ': 'ux', 'ụ': 'uj',
    'ứ': 'uws', 'ừ': 'uwf', 'ử': 'uwr', 'ữ': 'uwx', 'ự': 'uwj',
    'ý': 'ys', 'ỳ': 'yf', 'ỷ': 'yr', 'ỹ': 'yx', 'ỵ': 'yj',
    'Ă': 'Aw', 'Â': 'Aa', 'Ê': 'Ee', 'Ô': 'Oo', 'Ơ': 'Ow', 'Ư': 'Uw', 'Đ': 'Dd',
}
TELEX_REVERSE = {v: k for k, v in TELEX_MAP.items()}

VNI_MAP = {
    'ă': 'a8', 'â': 'a6', 'ê': 'e6', 'ô': 'o6', 'ơ': 'o7', 'ư': 'u7', 'đ': 'd9',
    'á': 'a1', 'à': 'a2', 'ả': 'a3', 'ã': 'a4', 'ạ': 'a5',
    'ấ': 'a61', 'ầ': 'a62', 'ẩ': 'a63', 'ẫ': 'a64', 'ậ': 'a65',
    'ắ': 'a81', 'ằ': 'a82', 'ẳ': 'a83', 'ẵ': 'a84', 'ặ': 'a85',
    'é': 'e1', 'è': 'e2', 'ẻ': 'e3', 'ẽ': 'e4', 'ẹ': 'e5',
    'ế': 'e61', 'ề': 'e62', 'ể': 'e63', 'ễ': 'e64', 'ệ': 'e65',
    'í': 'i1', 'ì': 'i2', 'ỉ': 'i3', 'ĩ': 'i4', 'ị': 'i5',
    'ó': 'o1', 'ò': 'o2', 'ỏ': 'o3', 'õ': 'o4', 'ọ': 'o5',
    'ố': 'o61', 'ồ': 'o62', 'ổ': 'o63', 'ỗ': 'o64', 'ộ': 'o65',
    'ớ': 'o71', 'ờ': 'o72', 'ở': 'o73', 'ỡ': 'o74', 'ợ': 'o75',
    'ú': 'u1', 'ù': 'u2', 'ủ': 'u3', 'ũ': 'u4', 'ụ': 'u5',
    'ứ': 'u71', 'ừ': 'u72', 'ử': 'u73', 'ữ': 'u74', 'ự': 'u75',
    'ý': 'y1', 'ỳ': 'y2', 'ỷ': 'y3', 'ỹ': 'y4', 'ỵ': 'y5',
}
VNI_REVERSE = {v: k for k, v in VNI_MAP.items()}

VIQR_MAP = {
    'ă': 'a(', 'â': 'a^', 'ê': 'e^', 'ô': 'o^', 'ơ': 'o+', 'ư': 'u+', 'đ': 'dd',
    'á': "a'", 'à': 'a`', 'ả': 'a?', 'ã': 'a~', 'ạ': 'a.',
    'ấ': "a^'", 'ầ': 'a^`', 'ẩ': 'a^?', 'ẫ': 'a^~', 'ậ': 'a^.',
    'ắ': "a('", 'ằ': 'a(`', 'ẳ': 'a(?', 'ẵ': 'a(~', 'ặ': 'a(.',
    'é': "e'", 'è': 'e`', 'ẻ': 'e?', 'ẽ': 'e~', 'ẹ': 'e.',
    'ế': "e^'", 'ề': 'e^`', 'ể': 'e^?', 'ễ': 'e^~', 'ệ': 'e^.',
    'í': "i'", 'ì': 'i`', 'ỉ': 'i?', 'ĩ': 'i~', 'ị': 'i.',
    'ó': "o'", 'ò': 'o`', 'ỏ': 'o?', 'õ': 'o~', 'ọ': 'o.',
    'ố': "o^'", 'ồ': 'o^`', 'ổ': 'o^?', 'ỗ': 'o^~', 'ộ': 'o^.',
    'ớ': "o+'", 'ờ': 'o+`', 'ở': 'o+?', 'ỡ': 'o+~', 'ợ': 'o+.',
    'ú': "u'", 'ù': 'u`', 'ủ': 'u?', 'ũ': 'u~', 'ụ': 'u.',
    'ứ': "u+'", 'ừ': 'u+`', 'ử': 'u+?', 'ữ': 'u+~', 'ự': 'u+.',
    'ý': "y'", 'ỳ': 'y`', 'ỷ': 'y?', 'ỹ': 'y~', 'ỵ': 'y.',
}
VIQR_REVERSE = {v: k for k, v in VIQR_MAP.items()}

# ============================================================
# HÀM MÃ HÓA
# ============================================================
def strip_viet(t):
    t = t.replace('đ', 'd').replace('Đ', 'D')
    return ''.join(c for c in unicodedata.normalize('NFD', t)
                   if unicodedata.category(c) != 'Mn')

def no_encrypt(t, k): return t
def no_decrypt(t, k): return t

def to_binary(t, k): return " ".join(f"{b:08b}" for b in t.encode("utf-8"))
def from_binary(d, k):
    d = d.replace(" ", "").replace("\n", "")
    if len(d) % 8 != 0: raise ValueError("Độ dài nhị phân phải chia hết cho 8.")
    return bytes(int(d[i:i+8], 2) for i in range(0, len(d), 8)).decode("utf-8")

def to_base64(t, k): return base64.b64encode(t.encode("utf-8")).decode("ascii")
def from_base64(d, k): return base64.b64decode(d.strip().replace("\n","").replace(" ","")).decode("utf-8")
def to_base32(t, k): return base64.b32encode(t.encode("utf-8")).decode("ascii")
def from_base32(d, k): return base64.b32decode(d.strip().replace("\n","").replace(" ","")).decode("utf-8")
def to_base85(t, k): return base64.b85encode(t.encode("utf-8")).decode("ascii")
def from_base85(d, k): return base64.b85decode(d.strip().encode("ascii")).decode("utf-8")
def to_a85(t, k): return base64.a85encode(t.encode("utf-8")).decode("ascii")
def from_a85(d, k): return base64.a85decode(d.strip()).decode("utf-8")
def to_base16(t, k): return base64.b16encode(t.encode("utf-8")).decode("ascii")
def from_base16(d, k): return base64.b16decode(d.strip()).decode("utf-8")
def to_hex(t, k): return " ".join(f"{b:02X}" for b in t.encode("utf-8"))
def from_hex(d, k):
    d = d.replace(" ","").replace("\n","").replace("0x","").replace("0X","")
    return bytes.fromhex(d).decode("utf-8")

def rot13_fn(t, k=None): return codecs.encode(t, 'rot_13')
def rot47(t, k=None):
    out = []
    for c in t:
        o = ord(c)
        if 33 <= o <= 126: out.append(chr(33 + ((o - 33 + 47) % 94)))
        else: out.append(c)
    return ''.join(out)
def atbash(t, k=None):
    out = []
    for c in t:
        if c.isalpha() and ord(c) < 128:
            if c.islower(): out.append(chr(ord('z') - (ord(c) - ord('a'))))
            else: out.append(chr(ord('Z') - (ord(c) - ord('A'))))
        else: out.append(c)
    return ''.join(out)

def caesar_enc(t, k):
    try: shift = int(k) if k else 3
    except ValueError: shift = 3
    out = []
    for c in t:
        if c.isalpha() and ord(c) < 128:
            b = ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c) - b + shift) % 26 + b))
        else: out.append(c)
    return ''.join(out)

def caesar_dec(t, k):
    try: shift = int(k) if k else 3
    except ValueError: shift = 3
    return caesar_enc(t, -shift)

def vigenere_enc(t, k):
    if not k: raise ValueError("Nhập khóa!")
    k = ''.join(c for c in k.upper() if c.isalpha())
    if not k: raise ValueError("Khóa phải có chữ cái!")
    out = []; ki = 0
    for c in t:
        if c.isalpha() and ord(c) < 128:
            shift = ord(k[ki % len(k)]) - ord('A')
            b = ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c) - b + shift) % 26 + b)); ki += 1
        else: out.append(c)
    return ''.join(out)

def vigenere_dec(t, k):
    if not k: raise ValueError("Nhập khóa!")
    k = ''.join(c for c in k.upper() if c.isalpha())
    if not k: raise ValueError("Khóa phải có chữ cái!")
    out = []; ki = 0
    for c in t:
        if c.isalpha() and ord(c) < 128:
            shift = ord(k[ki % len(k)]) - ord('A')
            b = ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c) - b - shift) % 26 + b)); ki += 1
        else: out.append(c)
    return ''.join(out)

def affine_enc(t, k):
    try:
        parts = k.split(",") if k else ["5", "8"]
        a = int(parts[0]) % 26; b = int(parts[1]) % 26 if len(parts) > 1 else 8
    except Exception: a, b = 5, 8
    out = []
    for c in t:
        if c.isalpha() and ord(c) < 128:
            base = ord('A') if c.isupper() else ord('a')
            out.append(chr((a * (ord(c) - base) + b) % 26 + base))
        else: out.append(c)
    return ''.join(out)

def affine_dec(t, k):
    try:
        parts = k.split(",") if k else ["5", "8"]
        a = int(parts[0]) % 26; b = int(parts[1]) % 26 if len(parts) > 1 else 8
    except Exception: a, b = 5, 8
    try: a_inv = pow(a, -1, 26)
    except ValueError: raise ValueError(f"a={a} không hợp lệ!")
    out = []
    for c in t:
        if c.isalpha() and ord(c) < 128:
            base = ord('A') if c.isupper() else ord('a')
            out.append(chr((a_inv * (ord(c) - base - b)) % 26 + base))
        else: out.append(c)
    return ''.join(out)

def rail_fence_enc(t, k):
    try: rails = max(2, int(k) if k else 3)
    except ValueError: rails = 3
    fence = [[] for _ in range(rails)]
    rail = 0; d = 1
    for c in t:
        fence[rail].append(c)
        if rail == 0: d = 1
        elif rail == rails - 1: d = -1
        rail += d
    return ''.join(''.join(r) for r in fence)

def rail_fence_dec(t, k):
    try: rails = max(2, int(k) if k else 3)
    except ValueError: rails = 3
    pattern = []; rail = 0; d = 1
    for _ in t:
        pattern.append(rail)
        if rail == 0: d = 1
        elif rail == rails - 1: d = -1
        rail += d
    counts = [pattern.count(r) for r in range(rails)]
    chunks = []; idx = 0
    for cnt in counts:
        chunks.append(list(t[idx:idx+cnt])); idx += cnt
    out = []; pos = [0] * rails
    for r in pattern:
        out.append(chunks[r][pos[r]]); pos[r] += 1
    return ''.join(out)

def columnar_enc(t, k):
    if not k: raise ValueError("Nhập khóa!")
    key = k.upper(); n = len(key)
    pad = (-len(t)) % n
    t = t + " " * pad
    rows = [t[i:i+n] for i in range(0, len(t), n)]
    order = sorted(range(n), key=lambda i: key[i])
    result = []
    for col in order:
        for row in rows: result.append(row[col])
    return ''.join(result)

def columnar_dec(t, k):
    if not k: raise ValueError("Nhập khóa!")
    key = k.upper(); n = len(key)
    if len(t) % n != 0: raise ValueError("Độ dài không chia hết cho khóa!")
    rows_count = len(t) // n
    order = sorted(range(n), key=lambda i: key[i])
    cols = {}; idx = 0
    for col in order:
        cols[col] = list(t[idx:idx+rows_count]); idx += rows_count
    result = []
    for r in range(rows_count):
        for c in range(n): result.append(cols[c][r])
    return ''.join(result).rstrip()

def to_unicode(t, k): return " ".join(f"U+{ord(c):04X}" for c in t)
def from_unicode(d, k):
    return "".join(chr(int(p.replace("U+","").replace("u+",""), 16))
                   for p in d.replace(","," ").split())
def to_ascii(t, k): return " ".join(str(ord(c)) for c in t)
def from_ascii(d, k): return "".join(chr(int(p)) for p in d.replace(","," ").split())
def to_morse(t, k):
    return " ".join(MORSE_CODE.get(c, '?') for c in strip_viet(t).upper())
def from_morse(d, k):
    return " ".join("".join(MORSE_REVERSE.get(c, '?') for c in w.split())
                    for w in d.strip().split(" / "))
def to_url(t, k): return urllib.parse.quote(t, safe="")
def from_url(d, k): return urllib.parse.unquote(d)
def to_html_fn(t, k): return html.escape(t)
def from_html_fn(d, k): return html.unescape(d)

def _to_syl(t, m): return "".join(m.get(c, c) for c in t)
def _from_syl(t, rm):
    keys = sorted(rm.keys(), key=len, reverse=True)
    out, i = [], 0
    while i < len(t):
        matched = False
        for kk in keys:
            if t[i:i+len(kk)].lower() == kk.lower():
                orig = t[i:i+len(kk)]
                v = rm[kk]
                if orig[0].isupper() and v:
                    v = v.upper() if len(v) == 1 else v[0].upper() + v[1:]
                out.append(v); i += len(kk); matched = True; break
        if not matched: out.append(t[i]); i += 1
    return "".join(out)

def to_telex(t, k): return _to_syl(t, TELEX_MAP)
def from_telex(t, k): return _from_syl(t, TELEX_REVERSE)
def to_vni(t, k): return _to_syl(t, VNI_MAP)
def from_vni(t, k): return _from_syl(t, VNI_REVERSE)
def to_viqr(t, k): return _to_syl(t, VIQR_MAP)
def from_viqr(t, k): return _from_syl(t, VIQR_REVERSE)
def to_no_accent(t, k): return strip_viet(t)
def from_no_accent(d, k): raise ValueError("Không thể giải mã 'không dấu'!")

def hash_md5(t, k): return hashlib.md5(t.encode("utf-8")).hexdigest()
def hash_sha1(t, k): return hashlib.sha1(t.encode("utf-8")).hexdigest()
def hash_sha256(t, k): return hashlib.sha256(t.encode("utf-8")).hexdigest()
def hash_sha512(t, k): return hashlib.sha512(t.encode("utf-8")).hexdigest()
def hash_err(d, k): raise ValueError("Hash một chiều!")

def bcrypt_hash(t, k):
    if not BCRYPT_OK: raise ValueError("Cần bcrypt!")
    return bcrypt.hashpw(t.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def bcrypt_verify(t, k):
    if not BCRYPT_OK: raise ValueError("Cần bcrypt!")
    try:
        return "✅ Đúng" if bcrypt.checkpw(k.encode("utf-8"), t.strip().encode("utf-8")) else "❌ Sai"
    except Exception as e: raise ValueError(f"Hash sai: {e}")

def pbkdf2_hash(t, k):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', t.encode("utf-8"), salt, 100000)
    return base64.b64encode(salt + dk).decode("ascii")
def pbkdf2_err(d, k): raise ValueError("PBKDF2 một chiều!")

def gzip_encode(t, k):
    return base64.b64encode(gzip.compress(t.encode("utf-8"))).decode("ascii")
def gzip_decode(d, k):
    return gzip.decompress(base64.b64decode(d.strip())).decode("utf-8")
def zlib_encode(t, k):
    return base64.b64encode(zlib.compress(t.encode("utf-8"))).decode("ascii")
def zlib_decode(d, k):
    return zlib.decompress(base64.b64decode(d.strip())).decode("utf-8")

def aes_encrypt(text, key):
    if not CRYPTO_OK: raise ValueError("Cần cryptography!")
    if not key: raise ValueError("Nhập khóa!")
    k = hashlib.sha256(key.encode("utf-8")).digest()
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(text.encode("utf-8")) + padder.finalize()
    c = Cipher(algorithms.AES(k), modes.CBC(iv), backend=default_backend()).encryptor()
    return base64.b64encode(iv + c.update(padded) + c.finalize()).decode("ascii")

def aes_decrypt(data, key):
    if not CRYPTO_OK: raise ValueError("Cần cryptography!")
    if not key: raise ValueError("Nhập khóa!")
    k = hashlib.sha256(key.encode("utf-8")).digest()
    raw = base64.b64decode(data.strip())
    iv, ct = raw[:16], raw[16:]
    c = Cipher(algorithms.AES(k), modes.CBC(iv), backend=default_backend()).decryptor()
    padded = c.update(ct) + c.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    try:
        return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")
    except Exception: raise ValueError("Khóa sai!")

def _mk8(key): return hashlib.sha256(key.encode("utf-8")).digest()[:8]
def _mk16(key): return hashlib.sha256(key.encode("utf-8")).digest()[:16]
def _mk24(key): return hashlib.sha256(key.encode("utf-8")).digest()[:24]
def _pad8(d):
    p = 8 - (len(d) % 8); return d + bytes([p]*p)
def _unpad8(d): return d[:-d[-1]]

def des_encrypt(text, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = _mk8(key); iv = os.urandom(8)
    c = DES.new(k, DES.MODE_CBC, iv)
    return base64.b64encode(iv + c.encrypt(_pad8(text.encode("utf-8")))).decode("ascii")
def des_decrypt(data, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = _mk8(key)
    raw = base64.b64decode(data.strip()); iv, ct = raw[:8], raw[8:]
    c = DES.new(k, DES.MODE_CBC, iv)
    return _unpad8(c.decrypt(ct)).decode("utf-8")

def des3_encrypt(text, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = _mk24(key)
    try:
        k = DES3.adjust_key_parity(k); c = DES3.new(k, DES3.MODE_CBC)
    except Exception:
        k = _mk16(key); c = DES3.new(k, DES3.MODE_CBC)
    return base64.b64encode(c.iv + c.encrypt(_pad8(text.encode("utf-8")))).decode("ascii")
def des3_decrypt(data, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = _mk24(key)
    try: k = DES3.adjust_key_parity(k)
    except Exception: k = _mk16(key)
    raw = base64.b64decode(data.strip()); iv, ct = raw[:8], raw[8:]
    c = DES3.new(k, DES3.MODE_CBC, iv)
    return _unpad8(c.decrypt(ct)).decode("utf-8")

def blowfish_encrypt(text, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = _mk16(key); iv = os.urandom(8)
    c = Blowfish.new(k, Blowfish.MODE_CBC, iv)
    return base64.b64encode(iv + c.encrypt(_pad8(text.encode("utf-8")))).decode("ascii")
def blowfish_decrypt(data, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = _mk16(key)
    raw = base64.b64decode(data.strip()); iv, ct = raw[:8], raw[8:]
    c = Blowfish.new(k, Blowfish.MODE_CBC, iv)
    return _unpad8(c.decrypt(ct)).decode("utf-8")

def rc4_encrypt(text, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    return base64.b64encode(ARC4.new(_mk16(key)).encrypt(text.encode("utf-8"))).decode("ascii")
def rc4_decrypt(data, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    return ARC4.new(_mk16(key)).decrypt(base64.b64decode(data.strip())).decode("utf-8")

def chacha_encrypt(text, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = hashlib.sha256(key.encode("utf-8")).digest(); nonce = os.urandom(8)
    c = ChaCha20.new(key=k, nonce=nonce)
    return base64.b64encode(nonce + c.encrypt(text.encode("utf-8"))).decode("ascii")
def chacha_decrypt(data, key):
    if not PYCRYPTO_OK: raise ValueError("Cần pycryptodome!")
    if not key: raise ValueError("Nhập khóa!")
    k = hashlib.sha256(key.encode("utf-8")).digest()
    raw = base64.b64decode(data.strip()); nonce, ct = raw[:8], raw[8:]
    c = ChaCha20.new(key=k, nonce=nonce)
    return c.decrypt(ct).decode("utf-8")

_RSA = {"priv": None, "pub": None}
def rsa_gen():
    if not CRYPTO_OK: raise ValueError("Cần cryptography!")
    p = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    _RSA["priv"] = p; _RSA["pub"] = p.public_key()

def rsa_encrypt(text, key):
    if not CRYPTO_OK: raise ValueError("Cần cryptography!")
    if _RSA["pub"] is None: rsa_gen()
    ct = _RSA["pub"].encrypt(text.encode("utf-8"),
        asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                          algorithm=hashes.SHA256(), label=None))
    return base64.b64encode(ct).decode("ascii")
def rsa_decrypt(data, key):
    if not CRYPTO_OK: raise ValueError("Cần cryptography!")
    if _RSA["priv"] is None: raise ValueError("Chưa có khóa riêng!")
    pt = _RSA["priv"].decrypt(base64.b64decode(data.strip()),
        asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                          algorithm=hashes.SHA256(), label=None))
    return pt.decode("utf-8")

def xor_encrypt(text, key):
    if not key: raise ValueError("Nhập khóa!")
    kb = key.encode("utf-8"); tb = text.encode("utf-8")
    return base64.b64encode(bytes(tb[i] ^ kb[i % len(kb)] for i in range(len(tb)))).decode("ascii")
def xor_decrypt(data, key):
    if not key: raise ValueError("Nhập khóa!")
    kb = key.encode("utf-8"); tb = base64.b64decode(data.strip())
    return bytes(tb[i] ^ kb[i % len(kb)] for i in range(len(tb))).decode("utf-8")

def pwd_encrypt(text, key): return "PWD1:" + aes_encrypt(text, key)
def pwd_decrypt(data, key):
    if not data.startswith("PWD1:"): raise ValueError("Không phải PWD1!")
    return aes_decrypt(data[5:], key)

# ============================================================
# ENCODERS
# ============================================================
ENCODERS = {
    "none":     ("⭕ Không mã hóa",  "Không mã hóa", no_encrypt,    no_decrypt),
    "binary":   ("🔢 Nhị phân",      "Cơ bản",     to_binary,     from_binary),
    "base64":   ("📦 Base64",        "Cơ bản",     to_base64,     from_base64),
    "base32":   ("🗜 Base32",        "Cơ bản",     to_base32,     from_base32),
    "base85":   ("🔷 Base85",        "Cơ bản",     to_base85,     from_base85),
    "a85":      ("🔶 Ascii85",       "Cơ bản",     to_a85,        from_a85),
    "base16":   ("🔡 Base16",        "Cơ bản",     to_base16,     from_base16),
    "hex":      ("#️⃣ Hex",           "Cơ bản",     to_hex,        from_hex),
    "rot13":    ("🔄 ROT13",         "Cổ điển",    rot13_fn,      rot13_fn),
    "rot47":    ("🔃 ROT47",         "Cổ điển",    rot47,         rot47),
    "atbash":   ("🔤 Atbash",        "Cổ điển",    atbash,        atbash),
    "caesar":   ("🏛 Caesar",        "Cổ điển",    caesar_enc,    caesar_dec),
    "vigenere": ("🔐 Vigenère",      "Cổ điển",    vigenere_enc,  vigenere_dec),
    "affine":   ("🎯 Affine",        "Cổ điển",    affine_enc,    affine_dec),
    "railfence":("🚂 Rail Fence",    "Cổ điển",    rail_fence_enc, rail_fence_dec),
    "columnar": ("📊 Columnar",      "Cổ điển",    columnar_enc,  columnar_dec),
    "unicode":  ("🌐 Unicode",       "Ký tự",      to_unicode,    from_unicode),
    "ascii":    ("🔤 ASCII",         "Ký tự",      to_ascii,      from_ascii),
    "morse":    ("📡 Morse",         "Ký tự",      to_morse,      from_morse),
    "url":      ("🔗 URL Encode",    "Web",        to_url,        from_url),
    "html":     ("🌍 HTML Entity",   "Web",        to_html_fn,    from_html_fn),
    "telex":    ("🚫 Không dấu",     "Tiếng Việt", to_telex,      from_telex),
    "vni":      ("🇻🇳 VNI",          "Tiếng Việt", to_vni,        from_vni),
    "viqr":     ("🇻🇳 VIQR",         "Tiếng Việt", to_viqr,       from_viqr),
    "noaccent": ("🚫 Bỏ dấu",        "Tiếng Việt", to_no_accent,  from_no_accent),
    "md5":      ("🔒 MD5",           "Hash",       hash_md5,      hash_err),
    "sha1":     ("🔒 SHA-1",         "Hash",       hash_sha1,     hash_err),
    "sha256":   ("🔒 SHA-256",       "Hash",       hash_sha256,   hash_err),
    "sha512":   ("🔒 SHA-512",       "Hash",       hash_sha512,   hash_err),
    "pbkdf2":   ("🔐 PBKDF2",        "Hash",       pbkdf2_hash,   pbkdf2_err),
    "aes":      ("🔐 AES-256",       "Bảo mật",    aes_encrypt,   aes_decrypt),
    "rsa":      ("🔑 RSA-2048",      "Bảo mật",    rsa_encrypt,   rsa_decrypt),
    "xor":      ("🧮 XOR",           "Bảo mật",    xor_encrypt,   xor_decrypt),
    "pwd":      ("🔐 Mật khẩu",      "Bảo mật",    pwd_encrypt,   pwd_decrypt),
    "gzip":     ("🗜 Gzip + B64",    "Nén",        gzip_encode,   gzip_decode),
    "zlib":     ("🗜 Zlib + B64",    "Nén",        zlib_encode,   zlib_decode),
}
if CRYPTO_OK:
    ENCODERS["bcrypt"] = ("🔒 Bcrypt", "Bảo mật", bcrypt_hash, bcrypt_verify)
if PYCRYPTO_OK:
    ENCODERS["des"] = ("🔐 DES", "Bảo mật", des_encrypt, des_decrypt)
    ENCODERS["des3"] = ("🔐 3DES", "Bảo mật", des3_encrypt, des3_decrypt)
    ENCODERS["blowfish"] = ("🐡 Blowfish", "Bảo mật", blowfish_encrypt, blowfish_decrypt)
    ENCODERS["rc4"] = ("📻 RC4", "Bảo mật", rc4_encrypt, rc4_decrypt)
    ENCODERS["chacha"] = ("🌊 ChaCha20", "Bảo mật", chacha_encrypt, chacha_decrypt)

GROUP_ORDER = ["Không mã hóa", "Cơ bản", "Cổ điển", "Ký tự", "Web",
               "Tiếng Việt", "Hash", "Bảo mật", "Nén"]

GROUP_COLORS = {
    "Không mã hóa": C["fg_dim"],
    "Cơ bản":     C["blue_light"],
    "Cổ điển":    C["purple_light"],
    "Ký tự":      C["cyan"],
    "Web":        C["yellow"],
    "Tiếng Việt": C["pink"],
    "Hash":       C["orange"],
    "Bảo mật":    C["green_light"],
    "Nén":        C["red"],
}

# ============================================================
# WIDGET: NÚT GRADIENT (giống web)
# ============================================================
class GradientButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=200, height=56,
                 c1=None, c2=None, fg="#ffffff",
                 font=("Inter", 13, "bold"), radius=14, icon=""):
        super().__init__(parent, width=width, height=height,
                         bg=C["bg"], highlightthickness=0, bd=0)
        self.command = command
        self.base_w = width; self.base_h = height
        self.c1 = c1 or C["blue"]; self.c2 = c2 or C["purple"]
        self.fg = fg
        self.text = text; self.icon = icon; self.font = font
        self.radius = radius
        self._hover = 0.0; self._target = 0.0; self._press = False
        self._draw()
        self.bind("<Enter>", lambda e: setattr(self, "_target", 1.0))
        self.bind("<Leave>", lambda e: (setattr(self, "_target", 0.0),
                                        setattr(self, "_press", False)))
        self.bind("<Button-1>", lambda e: setattr(self, "_press", True))
        self.bind("<ButtonRelease-1>", self._release)
        self._anim()

    def _release(self, _):
        self._press = False
        if self.command: self.command()

    def _rr(self, x1, y1, x2, y2, r, fill, outline="", w=0):
        r = min(r, (x2-x1)/2, (y2-y1)/2)
        if r < 1: r = 1
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=fill, outline=outline, width=w)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=fill, outline=outline, width=w)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=fill, outline=outline, width=w)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=fill, outline=outline, width=w)
        self.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline=outline, width=w)
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline=outline, width=w)

    def _draw(self):
        self.delete("all")
        w, h, r = self.base_w, self.base_h, self.radius
        # Shadow khi hover
        if self._hover > 0.05:
            for i in range(3, 0, -1):
                a = self._hover * (i / 3) * 0.3
                gc = lerp_color(C["bg"], self.c1, a)
                self._rr(i*2, i*2+3, w-i*2, h-i*2+3, r, gc)
        # Gradient body
        steps = 60
        for i in range(steps):
            t = i / steps
            color = lerp_color(self.c1, self.c2, t)
            if self._hover > 0.05:
                color = lerp_color(color, "#ffffff", self._hover * 0.15)
            if self._press:
                color = lerp_color(color, "#000000", 0.15)
            xa = (w) * i / steps
            xb = (w) * (i + 1) / steps
            if i == 0:
                self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=color, outline="")
                self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=color, outline="")
            if i == steps - 1:
                self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=color, outline="")
                self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=color, outline="")
            xa_c = max(xa, r)
            xb_c = min(xb, w-r)
            if xb_c > xa_c:
                self.create_rectangle(xa_c, 0, xb_c, h, fill=color, outline="")
        # Text
        text = f"{self.icon}  {self.text}" if self.icon else self.text
        self.create_text(w//2, h//2, text=text, fill=self.fg, font=self.font)

    def _anim(self):
        if abs(self._hover - self._target) > 0.01:
            self._hover += (self._target - self._hover) * 0.22
            self._draw()
        self.after(16, self._anim)

# ============================================================
# WIDGET: TOGGLE TAB (giống web)
# ============================================================
class ToggleTabs(tk.Frame):
    def __init__(self, parent, on_change=None):
        super().__init__(parent, bg=C["bg3"], highlightthickness=2,
                         highlightbackground=C["border"])
        self.on_change = on_change
        self.mode = "encode"

        # Padding trong
        inner = tk.Frame(self, bg=C["bg3"])
        inner.pack(padx=4, pady=4)

        self.btn_enc = tk.Button(inner, text="🔒  MÃ HÓA",
                                  font=("Inter", 13, "bold"),
                                  bg=C["blue"], fg="white",
                                  activebackground=C["blue"], activeforeground="white",
                                  relief="flat", bd=0, cursor="hand2",
                                  padx=40, pady=12,
                                  command=lambda: self._set("encode"))
        self.btn_enc.pack(side="left")

        self.btn_dec = tk.Button(inner, text="🔓  GIẢI MÃ",
                                  font=("Inter", 13, "bold"),
                                  bg=C["bg3"], fg=C["fg_dim"],
                                  activebackground=C["bg3"], activeforeground="white",
                                  relief="flat", bd=0, cursor="hand2",
                                  padx=40, pady=12,
                                  command=lambda: self._set("decode"))
        self.btn_dec.pack(side="left")

    def _set(self, mode):
        if mode == self.mode: return
        self.mode = mode
        if mode == "encode":
            self.btn_enc.config(bg=C["blue"], fg="white")
            self.btn_dec.config(bg=C["bg3"], fg=C["fg_dim"])
        else:
            self.btn_dec.config(bg=C["green"], fg="white")
            self.btn_enc.config(bg=C["bg3"], fg=C["fg_dim"])
        if self.on_change: self.on_change(mode)

# ============================================================
# WIDGET: PANEL VĂN BẢN (giống web)
# ============================================================
class TextPanel(tk.Frame):
    def __init__(self, parent, title, placeholder, icon="📄",
                 readonly=False, show_copy=False, accent=None):
        super().__init__(parent, bg=C["bg2"], highlightthickness=2,
                         highlightbackground=C["border"])
        self.readonly = readonly
        self.accent = accent or C["blue_light"]

        # Header
        hdr = tk.Frame(self, bg=C["bg2"])
        hdr.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(hdr, text=icon, font=("Segoe UI Emoji", 16),
                 bg=C["bg2"], fg=self.accent).pack(side="left", padx=(0, 8))
        tk.Label(hdr, text=title, font=("Inter", 12, "bold"),
                 bg=C["bg2"], fg=C["fg"]).pack(side="left")

        if show_copy:
            tk.Button(hdr, text="📋  Sao chép",
                      font=("Inter", 9),
                      bg=C["bg3"], fg=C["fg"],
                      activebackground=C["border"], activeforeground=C["fg"],
                      relief="flat", bd=0, cursor="hand2",
                      padx=12, pady=4,
                      command=self._copy).pack(side="right")
        else:
            self.count_lbl = tk.Label(hdr, text="0",
                                       font=("Inter", 9),
                                       bg=C["bg2"], fg=C["fg_dim"])
            self.count_lbl.pack(side="right")

        # Text box
        tf = tk.Frame(self, bg=C["bg3"], bd=0,
                      highlightthickness=1, highlightbackground=C["border"])
        tf.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.text = tk.Text(tf, height=6, font=("JetBrains Mono", 11),
                            bg=C["bg3"], fg=C["fg"],
                            insertbackground=self.accent,
                            relief="flat", bd=8, wrap="word",
                            highlightthickness=0,
                            selectbackground=C["blue"],
                            selectforeground="white")
        if readonly: self.text.configure(state="disabled")
        self.text.pack(fill="both", expand=True, padx=2, pady=2)

        if not readonly:
            self.text.bind("<KeyRelease>", self._update_count)

    def _update_count(self, _=None):
        t = self.get_text()
        self.count_lbl.config(text=f"{len(t)}")

    def _copy(self):
        t = self.get_text()
        if t:
            self.clipboard_clear(); self.clipboard_append(t)

    def get_text(self):
        if self.readonly: self.text.configure(state="normal")
        t = self.text.get("1.0", tk.END).rstrip("\n")
        if self.readonly: self.text.configure(state="disabled")
        return t

    def set_text(self, value):
        if self.readonly: self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, value)
        if self.readonly: self.text.configure(state="disabled")
        if not self.readonly: self._update_count()

    def clear(self): self.set_text("")

# ============================================================
# WIDGET: ALGO PICKER BOX
# ============================================================
class AlgoBox(tk.Frame):
    def __init__(self, parent, default_key, on_click):
        super().__init__(parent, bg=C["bg2"], highlightthickness=2,
                         highlightbackground=C["border"], cursor="hand2")
        self.value = default_key
        self.on_click = on_click

        inner = tk.Frame(self, bg=C["bg2"])
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        tk.Label(inner, text="🎯", font=("Segoe UI Emoji", 16),
                 bg=C["bg2"], fg=C["cyan"]).pack(side="left", padx=(0, 10))

        lbl_frame = tk.Frame(inner, bg=C["bg2"])
        lbl_frame.pack(side="left", fill="both", expand=True)
        tk.Label(lbl_frame, text="THUẬT TOÁN",
                 font=("Inter", 8, "bold"), bg=C["bg2"], fg=C["fg_dim"],
                 anchor="w").pack(fill="x")
        self.lbl = tk.Label(lbl_frame, text=ENCODERS[default_key][0],
                            font=("Inter", 11, "bold"),
                            bg=C["bg2"], fg=C["fg"], anchor="w")
        self.lbl.pack(fill="x")

        self.arrow = tk.Label(inner, text="▶", font=("Inter", 11),
                              bg=C["bg2"], fg=C["fg_dim"])
        self.arrow.pack(side="right")

        for w in [self, inner, self.lbl] + list(lbl_frame.winfo_children()):
            try:
                w.bind("<Button-1>", lambda e: self.on_click())
                w.bind("<Enter>", self._on_enter)
                w.bind("<Leave>", self._on_leave)
                w.configure(cursor="hand2")
            except Exception: pass

    def _on_enter(self, _):
        self.configure(highlightbackground=C["blue_light"])
        self.arrow.config(fg=C["blue_light"])

    def _on_leave(self, _):
        self.configure(highlightbackground=C["border"])
        self.arrow.config(fg=C["fg_dim"])

    def set_key(self, key):
        self.value = key
        self.lbl.config(text=ENCODERS[key][0])

# ============================================================
# WIDGET: KEY INPUT
# ============================================================
class KeyInput(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg2"], highlightthickness=2,
                         highlightbackground=C["border"])
        self.show = False

        inner = tk.Frame(self, bg=C["bg2"])
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        tk.Label(inner, text="🔑", font=("Segoe UI Emoji", 16),
                 bg=C["bg2"], fg=C["cyan"]).pack(side="left", padx=(0, 10))

        lbl_frame = tk.Frame(inner, bg=C["bg2"])
        lbl_frame.pack(side="left", fill="both", expand=True)
        tk.Label(lbl_frame, text="KHÓA BÍ MẬT",
                 font=("Inter", 8, "bold"), bg=C["bg2"], fg=C["fg_dim"],
                 anchor="w").pack(fill="x")

        self.var = tk.StringVar(value="matkhau123")
        self.entry = tk.Entry(lbl_frame, textvariable=self.var,
                              font=("Inter", 11, "bold"),
                              bg=C["bg2"], fg=C["fg"],
                              insertbackground=C["cyan"],
                              relief="flat", bd=0, show="●",
                              highlightthickness=0)
        self.entry.pack(fill="x")

        self.eye = tk.Button(inner, text="👁", font=("Segoe UI Emoji", 12),
                             bg=C["bg2"], fg=C["fg_dim"],
                             activebackground=C["bg2"],
                             relief="flat", bd=0, cursor="hand2",
                             padx=6, command=self._toggle)
        self.eye.pack(side="right")

    def _toggle(self):
        self.show = not self.show
        self.entry.config(show="" if self.show else "●")
        self.eye.config(text="🙈" if self.show else "👁")

    def get(self): return self.var.get()

# ============================================================
# WIDGET: TOAST
# ============================================================
class Toast:
    def __init__(self, root):
        self.root = root
        self.frame = None
        self.timer = None

    def show(self, msg, is_error=False, duration=2500):
        if self.frame:
            try: self.frame.destroy()
            except: pass
        self.frame = tk.Frame(self.root, bg=C["bg2"],
                              highlightthickness=2,
                              highlightbackground=C["red"] if is_error else C["green"])
        self.frame.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
        tk.Label(self.frame, text=msg, font=("Inter", 10, "bold"),
                 bg=C["bg2"], fg=C["fg"], padx=16, pady=10).pack()
        if self.timer: self.root.after_cancel(self.timer)
        self.timer = self.root.after(duration, self._hide)

    def _hide(self):
        if self.frame:
            try: self.frame.destroy()
            except: pass
            self.frame = None

# ============================================================
# ALGO PICKER MODAL
# ============================================================
class AlgoPickerModal:
    def __init__(self, root):
        self.root = root
        self.frame = None
        self.on_select = None

    def show(self, current, on_select):
        if self.frame: return
        self.on_select = on_select

        self.frame = tk.Frame(self.root, bg=C["bg"])
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.frame.lift()

        # Container (giữa màn hình)
        container = tk.Frame(self.frame, bg=C["bg2"],
                             highlightthickness=2, highlightbackground=C["blue"])
        container.place(relx=0.5, rely=0.5, anchor="center",
                        width=min(900, self.root.winfo_width()-80),
                        height=min(650, self.root.winfo_height()-80))

        # Header
        hdr = tk.Frame(container, bg=C["bg2"])
        hdr.pack(fill="x", padx=24, pady=(20, 10))
        tk.Label(hdr, text="🎯 Chọn thuật toán",
                 font=("Inter", 18, "bold"),
                 bg=C["bg2"], fg=C["fg"]).pack(side="left")
        tk.Button(hdr, text="✕", font=("Inter", 14, "bold"),
                  bg=C["bg3"], fg=C["red"],
                  activebackground=C["red"], activeforeground="white",
                  relief="flat", bd=0, cursor="hand2",
                  width=3, command=self.close).pack(side="right")

        # Search
        search_frame = tk.Frame(container, bg=C["bg3"],
                                 highlightthickness=1, highlightbackground=C["border"])
        search_frame.pack(fill="x", padx=24, pady=(0, 12))
        inner_search = tk.Frame(search_frame, bg=C["bg3"])
        inner_search.pack(fill="x", padx=14, pady=10)
        tk.Label(inner_search, text="🔍", font=("Segoe UI Emoji", 12),
                 bg=C["bg3"], fg=C["cyan"]).pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(inner_search, textvariable=self.search_var,
                                font=("Inter", 11), bg=C["bg3"], fg=C["fg"],
                                insertbackground=C["cyan"], relief="flat", bd=0,
                                highlightthickness=0)
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.focus_set()
        search_entry.bind("<Escape>", lambda e: self.close())
        self.search_var.trace_add("write", lambda *a: self._render())

        # Scroll area
        scroll_outer = tk.Frame(container, bg=C["bg2"])
        scroll_outer.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.canvas = tk.Canvas(scroll_outer, bg=C["bg2"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(scroll_outer, orient="vertical",
                          command=self.canvas.yview,
                          bg=C["bg3"], troughcolor=C["bg2"],
                          activebackground=C["blue"],
                          relief="flat", bd=0, width=12)
        sb.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=sb.set)

        self.content = tk.Frame(self.canvas, bg=C["bg2"])
        self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        def on_config(e):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            try: self.canvas.itemconfig(1, width=self.canvas.winfo_width())
            except: pass
        self.content.bind("<Configure>", on_config)
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(1, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
                              lambda e: self.canvas.yview_scroll(int(-e.delta/120), "units"))

        self.current = current
        self._render()

    def _render(self):
        if not self.content: return
        for w in self.content.winfo_children():
            w.destroy()

        query = (self.search_var.get() if self.search_var else "").lower().strip()

        groups = {}
        for k, (label, group, _, _) in ENCODERS.items():
            if query and query not in label.lower() and query not in k.lower():
                continue
            groups.setdefault(group, []).append((k, label))

        if not groups:
            tk.Label(self.content, text=f"❌ Không tìm thấy: \"{query}\"",
                     font=("Inter", 12, "italic"),
                     bg=C["bg2"], fg=C["fg_dim"]).pack(pady=40)
            return

        for group in GROUP_ORDER:
            if group not in groups: continue
            items = groups[group]
            color = GROUP_COLORS.get(group, C["blue_light"])

            # Group title
            ghdr = tk.Frame(self.content, bg=C["bg2"])
            ghdr.pack(fill="x", pady=(14, 8))
            tk.Frame(ghdr, bg=color, width=4, height=20).pack(side="left", padx=(0, 8))
            tk.Label(ghdr, text=group.upper(),
                     font=("Inter", 11, "bold"),
                     bg=C["bg2"], fg=color).pack(side="left")

            # Grid 3 cột
            grid = tk.Frame(self.content, bg=C["bg2"])
            grid.pack(fill="x")
            for i in range(3):
                grid.grid_columnconfigure(i, weight=1, uniform="g")

            for idx, (key, label) in enumerate(items):
                r = idx // 3; c = idx % 3
                is_current = (key == self.current)

                card = tk.Frame(grid, bg=C["bg3"], cursor="hand2",
                                highlightthickness=2,
                                highlightbackground=color if is_current else C["border"])
                card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

                inner = tk.Frame(card, bg=C["bg3"])
                inner.pack(fill="both", expand=True, padx=12, pady=10)
                tk.Label(inner, text=label, font=("Inter", 10, "bold"),
                         bg=C["bg3"], fg=C["fg"], anchor="w").pack(fill="x")

                if is_current:
                    tk.Label(inner, text="✓ Đang dùng",
                             font=("Inter", 8, "italic"),
                             bg=C["bg3"], fg=color, anchor="w").pack(fill="x")

                def on_enter(e, card=card, inner=inner, color=color):
                    if is_current: return
                    card.configure(bg=C["bg2"], highlightbackground=color)
                    inner.configure(bg=C["bg2"])
                    for w in inner.winfo_children():
                        try: w.configure(bg=C["bg2"])
                        except: pass

                def on_leave(e, card=card, inner=inner):
                    if is_current: return
                    card.configure(bg=C["bg3"], highlightbackground=C["border"])
                    inner.configure(bg=C["bg3"])
                    for w in inner.winfo_children():
                        try: w.configure(bg=C["bg3"])
                        except: pass

                def on_click(e, key=key):
                    self.close()
                    if self.on_select: self.on_select(key)

                for widget in [card, inner] + list(inner.winfo_children()):
                    try:
                        widget.bind("<Enter>", on_enter)
                        widget.bind("<Leave>", on_leave)
                        widget.bind("<Button-1>", on_click)
                        widget.configure(cursor="hand2")
                    except: pass

    def close(self):
        if self.frame:
            try: self.canvas.unbind_all("<MouseWheel>")
            except: pass
            self.frame.destroy()
            self.frame = None
            self.content = None

# ============================================================
# APP
# ============================================================
root = tk.Tk()
root.title("🔐 Mã Hóa Chữ")
root.geometry("1400x900")
root.minsize(1100, 700)
root.configure(bg=C["bg"])

# Scroll tổng thể
outer_canvas = tk.Canvas(root, bg=C["bg"], highlightthickness=0)
outer_canvas.pack(side="left", fill="both", expand=True)

outer_sb = tk.Scrollbar(root, orient="vertical", command=outer_canvas.yview,
                        bg=C["bg3"], troughcolor=C["bg2"],
                        activebackground=C["blue"],
                        relief="flat", bd=0, width=12)
outer_sb.pack(side="right", fill="y")
outer_canvas.configure(yscrollcommand=outer_sb.set)

container = tk.Frame(outer_canvas, bg=C["bg"])
container_window = outer_canvas.create_window((0, 0), window=container, anchor="nw")

def _on_container_config(e):
    outer_canvas.configure(scrollregion=outer_canvas.bbox("all"))
def _on_canvas_config(e):
    outer_canvas.itemconfig(container_window, width=e.width)

container.bind("<Configure>", _on_container_config)
outer_canvas.bind("<Configure>", _on_canvas_config)

def _on_mousewheel(e):
    # Chỉ scroll khi không ở trong Text widget
    try:
        if isinstance(e.widget, tk.Text):
            return
    except: pass
    outer_canvas.yview_scroll(int(-e.delta/120), "units")
root.bind_all("<MouseWheel>", _on_mousewheel)

# State
STATE = {
    "mode": "encode",
    "algo": "base64",
    "input_text": "Xin chào! Đây là một ví dụ về\nmã hóa chữ.",
    "output_text": "",
    "key": "matkhau123",
}

toast = Toast(root)
modal = AlgoPickerModal(root)

# ============================================================
# HANDLERS
# ============================================================
def on_algo_select(key):
    STATE["algo"] = key
    algo_box.set_key(key)

def on_mode_change(mode):
    STATE["mode"] = mode
    run_btn_text = "⚙  MÃ HÓA" if mode == "encode" else "🔓  GIẢI MÃ"
    run_btn.text = "MÃ HÓA" if mode == "encode" else "GIẢI MÃ"
    run_btn.icon = "⚙" if mode == "encode" else "🔓"
    if mode == "encode":
        run_btn.c1 = C["blue"]; run_btn.c2 = C["purple"]
    else:
        run_btn.c1 = C["green"]; run_btn.c2 = C["green_light"]
    run_btn._draw()

def run_process():
    text = panel_in.get_text()
    if not text:
        toast.show("⚠ Chưa nhập văn bản!", is_error=True)
        return

    algo = STATE["algo"]
    if algo not in ENCODERS:
        toast.show(f"❌ Không tìm thấy: {algo}", is_error=True)
        return

    key = key_in.get()
    mode = STATE["mode"]

    try:
        _, _, enc_fn, dec_fn = ENCODERS[algo]
        fn = enc_fn if mode == "encode" else dec_fn
        result = fn(text, key)
        panel_out.set_text(result)
        toast.show(f"✅ {('Mã hóa' if mode=='encode' else 'Giải mã')} thành công!")
    except Exception as e:
        toast.show(f"❌ {e}", is_error=True)

def do_swap():
    c = panel_out.get_text()
    if c:
        panel_in.set_text(c); panel_out.clear()

def do_clear():
    panel_in.clear(); panel_out.clear()

# ============================================================
# BUILD UI
# ============================================================
# ===== HEADER =====
header = tk.Frame(container, bg=C["bg"])
header.pack(fill="x", padx=40, pady=(30, 20))

title_frame = tk.Frame(header, bg=C["bg"])
title_frame.pack()

tk.Label(title_frame, text="🔒", font=("Segoe UI Emoji", 40),
         bg=C["bg"], fg=C["blue_light"]).pack(side="left", padx=(0, 14))
tk.Label(title_frame, text="MÃ HÓA CHỮ",
         font=("Inter", 36, "bold"),
         bg=C["bg"], fg=C["cyan"]).pack(side="left")

tk.Label(header, text=f"Bảo vệ thông tin của bạn • {len(ENCODERS)} thuật toán",
         font=("Inter", 12), bg=C["bg"], fg=C["fg_dim"]).pack(pady=(8, 0))

# ===== TOGGLE TABS =====
toggle_frame = tk.Frame(container, bg=C["bg"])
toggle_frame.pack(pady=(0, 24))
toggle = ToggleTabs(toggle_frame, on_change=on_mode_change)
toggle.pack()

# ===== 2 PANELS =====
panels = tk.Frame(container, bg=C["bg"])
panels.pack(fill="x", padx=40, pady=(0, 20))
panels.grid_columnconfigure(0, weight=1, uniform="panels")
panels.grid_columnconfigure(1, weight=1, uniform="panels")

panel_in = TextPanel(panels, "Văn bản gốc",
                     "Nhập văn bản cần mã hóa...",
                     icon="📄", accent=C["blue_light"])
panel_in.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
panel_in.set_text(STATE["input_text"])

panel_out = TextPanel(panels, "Kết quả",
                      "Kết quả sẽ hiện ở đây...",
                      icon="🔓", readonly=True, show_copy=True,
                      accent=C["purple_light"])
panel_out.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

# ===== CONTROLS =====
controls = tk.Frame(container, bg=C["bg"])
controls.pack(fill="x", padx=40, pady=(0, 12))
controls.grid_columnconfigure(0, weight=2, uniform="c")
controls.grid_columnconfigure(1, weight=3, uniform="c")
controls.grid_columnconfigure(2, weight=2, uniform="c")

algo_box = AlgoBox(controls, STATE["algo"],
                    lambda: modal.show(STATE["algo"], on_algo_select))
algo_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

key_in = KeyInput(controls)
key_in.var.set(STATE["key"])
key_in.grid(row=0, column=1, sticky="nsew", padx=8)

run_btn = GradientButton(controls, "MÃ HÓA", command=run_process,
                          icon="⚙", width=280, height=64,
                          c1=C["blue"], c2=C["purple"])
run_btn.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

# ===== ROW 2 =====
row2 = tk.Frame(container, bg=C["bg"])
row2.pack(fill="x", padx=40, pady=(0, 40))
row2.grid_columnconfigure(0, weight=1, uniform="r2")
row2.grid_columnconfigure(1, weight=1, uniform="r2")

swap_btn = GradientButton(row2, "ĐẢO CHIỀU", command=do_swap,
                           icon="🔁", width=440, height=56,
                           c1=C["cyan"], c2=C["blue_light"])
swap_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))

clear_btn = GradientButton(row2, "XÓA TẤT CẢ", command=do_clear,
                            icon="🗑", width=440, height=56,
                            c1=C["bg3"], c2=C["border"], fg=C["fg"])
clear_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))

# Phím tắt
def on_ctrl_enter(e):
    run_process()
    return "break"
root.bind("<Control-Return>", on_ctrl_enter)

root.mainloop()