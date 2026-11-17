# -*- coding: utf-8 -*-
"""
webrtc_ice.py — รายการ ICE server (STUN/TURN) สำหรับระบบโทรเสียง/วิดีโอ

ทำไมต้องมี: โทรข้ามเครือข่าย (เช่น มือถือ 4G ↔ Wi-Fi ออฟฟิศ) ต้องใช้ TURN relay ถ้าไม่มี การเชื่อมต่อจะล้มเหลวบ่อย
เดิมโค้ดฝัง TURN สาธารณะฟรี (openrelay.metered.ca / รหัสผ่านสาธารณะ) ซึ่งไม่เสถียรและจำกัดโควตา → โทรจริงไม่ติด

ตั้งค่าได้ 4 แบบ (เลือกอย่างใดอย่างหนึ่ง ตามลำดับความสำคัญ) ใน .env:
  1) Cloudflare Realtime TURN (ฟรี 1TB/เดือน — ใช้ Cloudflare อยู่แล้ว):
       CLOUDFLARE_TURN_KEY_ID=...   CLOUDFLARE_TURN_API_TOKEN=...
  2) Metered.ca (มีแพ็กเกจฟรี):
       METERED_APP_NAME=ชื่อแอป      METERED_API_KEY=...
  3) coturn ของตัวเอง แบบรหัสชั่วคราว:
       TURN_URLS=turn:turn.example.com:3478,turns:turn.example.com:5349   TURN_SECRET=static-auth-secret
  4) TURN ทั่วไป รหัสตายตัว:
       TURN_URLS=turn:host:3478   TURN_USERNAME=...   TURN_CREDENTIAL=...

ถ้าไม่ตั้งอะไรเลย → ใช้ STUN + TURN สาธารณะเป็นทางสำรอง (turn_configured=False) และหน้าเว็บจะบอกผู้ใช้เมื่อเชื่อมต่อไม่ได้
"""
import base64
import hashlib
import hmac
import logging
import os
import threading
import time

logger = logging.getLogger("OrgChatAI")

STUN_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"},
    {"urls": "stun:stun2.l.google.com:19302"},
]

# ทางสำรองสุดท้ายเมื่อไม่ได้ตั้ง TURN ของตัวเอง (สาธารณะ ไม่รับประกันว่าใช้ได้)
PUBLIC_FALLBACK_TURN = [
    {"urls": "turn:openrelay.metered.ca:80", "username": "openrelayproject", "credential": "openrelayproject"},
    {"urls": "turn:openrelay.metered.ca:443", "username": "openrelayproject", "credential": "openrelayproject"},
    {"urls": "turn:openrelay.metered.ca:443?transport=tcp", "username": "openrelayproject", "credential": "openrelayproject"},
]

_CACHE = {"t": 0.0, "value": None}
_LOCK = threading.Lock()
CACHE_SECONDS = 1800          # ขอรหัสใหม่ทุก 30 นาที (รหัสที่ออกมีอายุ 24 ชม.)
CRED_TTL_SECONDS = 86400


def _normalize(servers):
    """รับรูปแบบที่ผู้ให้บริการต่างๆ ส่งมา (list หรือ dict เดียว) → list ของ {urls, username?, credential?}"""
    if not servers:
        return []
    if isinstance(servers, dict):
        servers = [servers]
    out = []
    for s in servers:
        if not isinstance(s, dict) or not s.get("urls"):
            continue
        item = {"urls": s["urls"]}
        if s.get("username"):
            item["username"] = s["username"]
        if s.get("credential"):
            item["credential"] = s["credential"]
        out.append(item)
    return out


def _cloudflare():
    key_id, token = os.getenv("CLOUDFLARE_TURN_KEY_ID", "").strip(), os.getenv("CLOUDFLARE_TURN_API_TOKEN", "").strip()
    if not (key_id and token):
        return None
    import requests
    r = requests.post(
        f"https://rtc.live.cloudflare.com/v1/turn/keys/{key_id}/credentials/generate-ice-servers",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"ttl": CRED_TTL_SECONDS}, timeout=6)
    r.raise_for_status()
    data = r.json()
    servers = _normalize(data.get("iceServers"))
    # Cloudflare ส่ง STUN รวมมาด้วย (urls ขึ้นต้น stun:) — เก็บเฉพาะ TURN ส่วน STUN เรามีของเราเอง
    return [s for s in servers if any(str(u).startswith(("turn:", "turns:")) for u in (s["urls"] if isinstance(s["urls"], list) else [s["urls"]]))]


def _metered():
    app, key = os.getenv("METERED_APP_NAME", "").strip(), os.getenv("METERED_API_KEY", "").strip()
    if not (app and key):
        return None
    import requests
    r = requests.get(f"https://{app}.metered.live/api/v1/turn/credentials", params={"apiKey": key}, timeout=6)
    r.raise_for_status()
    return _normalize(r.json())


def _coturn_secret(username="orgchat"):
    urls, secret = os.getenv("TURN_URLS", "").strip(), os.getenv("TURN_SECRET", "").strip()
    if not (urls and secret):
        return None
    expiry = int(time.time()) + CRED_TTL_SECONDS
    user = f"{expiry}:{username}"
    cred = base64.b64encode(hmac.new(secret.encode(), user.encode(), hashlib.sha1).digest()).decode()
    return [{"urls": [u.strip() for u in urls.split(",") if u.strip()], "username": user, "credential": cred}]


def _static_turn():
    urls = os.getenv("TURN_URLS", "").strip()
    u, c = os.getenv("TURN_USERNAME", "").strip(), os.getenv("TURN_CREDENTIAL", "").strip()
    if not (urls and u and c):
        return None
    return [{"urls": [x.strip() for x in urls.split(",") if x.strip()], "username": u, "credential": c}]


def get_ice_config(force=False) -> dict:
    """{'iceServers': [...], 'turn_configured': bool, 'source': str}"""
    now = time.time()
    with _LOCK:
        if not force and _CACHE["value"] and now - _CACHE["t"] < CACHE_SECONDS:
            return _CACHE["value"]
    turn, source = None, "none"
    for name, fn in (("cloudflare", _cloudflare), ("metered", _metered), ("coturn-secret", _coturn_secret), ("static", _static_turn)):
        try:
            got = fn()
        except Exception as e:  # ผู้ให้บริการล่ม/คีย์ผิด → ลองแบบถัดไป ไม่ทำให้การโทรทั้งระบบพัง
            logger.warning(f"[webrtc] TURN provider '{name}' failed: {e}")
            continue
        if got:
            turn, source = got, name
            break
    if turn:
        value = {"iceServers": STUN_SERVERS + turn, "turn_configured": True, "source": source}
        ttl_ok = True
    else:
        value = {"iceServers": STUN_SERVERS + PUBLIC_FALLBACK_TURN, "turn_configured": False, "source": "public-fallback"}
        ttl_ok = False
    with _LOCK:
        # ถ้าไม่ได้ตั้งค่า เก็บแคชสั้นๆ (1 นาที) เผื่อเพิ่งแก้ .env; ถ้าตั้งค่าแล้วเก็บเต็มเวลา
        _CACHE["value"], _CACHE["t"] = value, now if ttl_ok else now - CACHE_SECONDS + 60
    return value
