# -*- coding: utf-8 -*-
"""
Shared utilities, instances, and decorators for OrgChat-AI Blueprints.
Avoids circular imports by keeping Flask factory components separate.
"""
import os
import sys
import io
import time
import json
import logging
import ipaddress
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse
from flask import request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pywebpush import webpush, WebPushException
from concurrent.futures import ThreadPoolExecutor

import database

logger = logging.getLogger("OrgChatAI")

# ─── Version ─────────────────────────────────────────────────
VERSION = "1.10.0-STABLE"

# ─── App Start Time ──────────────────────────────────────────
_APP_START_TIME = time.time()

# ─── Allowed File Extensions ─────────────────────────────────
ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".md", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".docx", ".xlsx"}

# ─── Thread Pools for Push Notifications ─────────────────────
_executor = ThreadPoolExecutor(max_workers=10)

# ─── SocketIO & Limiter instances (initialized via init_app in factory) ──
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading', max_http_payload_size=10*1024*1024)
_limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

# ─── Online Users Registry ───────────────────────────────────
online_users_registry = {}  # sid -> username

# ─── OAuth2 States & LINE Linking Tokens ─────────────────────
PENDING_LINE_LINKS = {}
_OAUTH_STATES = {}

def _store_oauth_state(state: str, data: dict):
    data["expires"] = time.time() + 600  # 10 minutes
    _OAUTH_STATES[state] = data
    # Clean expired
    now = time.time()
    for k in list(_OAUTH_STATES.keys()):
        if _OAUTH_STATES[k]["expires"] < now:
            _OAUTH_STATES.pop(k, None)

def _pop_oauth_state(state: str) -> dict | None:
    entry = _OAUTH_STATES.pop(state, None)
    if entry and entry["expires"] > time.time():
        return entry
    return None

# ─── OAuth2 Availability ─────────────────────────────────────
try:
    from oauth2_service import oauth2_service
    OAUTH2_AVAILABLE = True
except ImportError:
    OAUTH2_AVAILABLE = False
    oauth2_service = None
    print("⚠️ oauth2_service not available — per-user Google login disabled")

try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    id_token = None
    google_requests = None

# ─── VAPID Keys for Push Notifications ───────────────────────
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "BNW7f7p3Ush_rg9vjIXxz1KTthTsiy3rz17oaygTy1-l4bTQJKpLeYEj4v3jYQkggo1VLa7w7sNb6mWDaIVH5eU")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "iVj1ybjnV5yP34d1BZ9ydP6Ad_m_24FC6AhYkc2On04")
VAPID_CLAIMS = {"sub": "mailto:" + os.environ.get("VAPID_CONTACT_EMAIL", "admin@openchat.sbs")}


# ═══════════════════════════════════════════════════════════════
# Push Notifications
# ═══════════════════════════════════════════════════════════════

def send_push_notification(username, title, message, url='/', tag=None):
    """Send a real-time push notification to a user's device via VAPID."""
    subscriptions = database.get_push_subscriptions(username)
    if not subscriptions:
        return

    payload_data = {
        "title": title,
        "body": message,
        "url": url
    }
    if tag:
        payload_data["tag"] = tag
        
    payload = json.dumps(payload_data)

    for sub_json in subscriptions:
        try:
            subscription_info = json.loads(sub_json)
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS.copy()
            )
        except WebPushException as ex:
            print(f"WebPush error for {username}: {ex}")
            if ex.response is not None and ex.response.status_code in [404, 410]:
                database.remove_push_subscription(username, sub_json)
        except Exception as e:
            print(f"General Push error for {username}: {e}")

def batch_send_push_notification(usernames, title, message, url='/'):
    """Send push notifications to multiple users in parallel."""
    if not usernames:
        return
    for uname in usernames:
        _executor.submit(send_push_notification, uname, title, message, url)


# ═══════════════════════════════════════════════════════════════
# Decorators
# ═══════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อนใช้งาน"}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อนใช้งาน"}), 401
        
        user = session.get("user")
        settings = database.get_user_setting(user)
        if settings.get("role") != "admin":
            return jsonify({"ok": False, "error": "เฉพาะผู้ดูแลระบบเท่านั้นที่มีสิทธิ์เข้าถึงส่วนนี้"}), 403
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        if not user:
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        sa_users = set(filter(None, os.environ.get("SUPERADMIN_USERS", "Admin").split(",")))
        if user not in sa_users:
            return jsonify({"ok": False, "error": "Super admin only"}), 403
        return f(*args, **kwargs)
    return decorated_function

def safe_thread_target(target_fn):
    """Decorator to ensure thread-local Google context is cleared at the end of a background thread execution."""
    @wraps(target_fn)
    def wrapper(*args, **kwargs):
        try:
            return target_fn(*args, **kwargs)
        finally:
            try:
                from google_drive_service import google_manager
                google_manager.clear_context()
            except Exception:
                pass
    return wrapper


# ═══════════════════════════════════════════════════════════════
# Session / Org Helpers
# ═══════════════════════════════════════════════════════════════

def _set_session_org(username: str):
    """Resolve and store the correct org for a user after login."""
    orgs = database.get_user_orgs(username)
    if orgs:
        # Prioritize org where user is admin
        admin_orgs = [o for o in orgs if o.get("role") == "admin"]
        if admin_orgs:
            session["org_id"] = admin_orgs[0]["id"]
            session["org_role"] = admin_orgs[0]["role"]
        else:
            session["org_id"] = orgs[0]["id"]
            session["org_role"] = orgs[0]["role"]
    else:
        # ไม่มี org → สร้าง personal org ให้อัตโนมัติ
        try:
            personal_org_name = f"personal_{username}"
            org_id, _ = database.create_organization(personal_org_name, username)
        except Exception:
            orgs_retry = database.get_user_orgs(username)
            org_id = orgs_retry[0]["id"] if orgs_retry else 1
        session["org_id"] = org_id
        session["org_role"] = "admin"

def get_current_org_id() -> int:
    """Return the org_id for the current request session."""
    username = session.get("user")
    if username:
        org_id = session.get("org_id")
        if org_id:
            try:
                conn = database._get_conn()
                exists = conn.execute(
                    "SELECT 1 FROM organization_members WHERE username=? AND organization_id=?",
                    (username, org_id)
                ).fetchone()
                conn.close()
                if not exists:
                    _set_session_org(username)
            except Exception:
                pass
        else:
            _set_session_org(username)
    return session.get("org_id", 1)


# ═══════════════════════════════════════════════════════════════
# Knowledge Base Authorization Helpers
# ═══════════════════════════════════════════════════════════════

def can_edit_knowledge_base():
    user = session.get("user")
    if not user: return False
    settings = database.get_user_setting(user)
    if settings.get("role") == "admin":
        return True
    return bool(settings.get("can_edit_kb", False))

def can_view_knowledge_base():
    user = session.get("user")
    if not user: return False
    settings = database.get_user_setting(user)
    if settings.get("role") == "admin":
        return True
    return bool(settings.get("can_view_kb", False))

def can_delete_knowledge_base():
    user = session.get("user")
    if not user: return False
    settings = database.get_user_setting(user)
    if settings.get("role") == "admin":
        return True
    return bool(settings.get("can_delete_kb", False))

def is_admin():
    user = session.get("user")
    if not user: return False
    settings = database.get_user_setting(user)
    return settings.get("role") == "admin"

def get_rag_filter(username, org_id=1):
    """Constructs a ChromaDB filter to restrict AI search based on category permissions and org."""
    if not username:
        return None

    user_settings = database.get_user_setting(username)
    if user_settings.get("role") == "admin":
        return {"$or": [{"organization_id": org_id}, {"organization_id": {"$eq": None}}]}

    cats = database.get_categories(username)
    allowed_ids = []
    for c in cats:
        if c.get('id') is not None:
            allowed_ids.append(c['id'])
            allowed_ids.append(str(c['id']))

    org_clause = {"$or": [{"organization_id": org_id}, {"organization_id": {"$eq": None}}]}
    unassigned_filters = [{"category_id": ""}]

    if not allowed_ids:
        return {"$and": [org_clause, {"$or": unassigned_filters}]}

    res = {
        "$and": [
            org_clause,
            {"$or": [{"category_id": {"$in": allowed_ids}}, *unassigned_filters]}
        ]
    }
    print(f"🛡️ [AUTH] RAG filter for {username} org={org_id}: {len(allowed_ids)//2} allowed categories.")
    return res


# ═══════════════════════════════════════════════════════════════
# Gemini API Key Helpers
# ═══════════════════════════════════════════════════════════════

def _get_gemini_api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY", "").strip() or None

def _configure_gemini(api_key: str):
    pass  # google-genai ใหม่สร้าง client ต่อ session — ไม่มี configure() แบบ global


# ═══════════════════════════════════════════════════════════════
# File Validation
# ═══════════════════════════════════════════════════════════════

def validate_uploaded_file(file_stream, filename) -> tuple[bool, str]:
    """Validates an uploaded file strictly based on extension, content inspection, and null-byte."""
    if not filename:
        return False, "ไม่พบชื่อไฟล์"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"ไม่รองรับนามสกุลไฟล์ {ext}"
    try:
        header = file_stream.read(2048)
        file_stream.seek(0)
    except Exception as e:
        return False, f"ไม่สามารถอ่านข้อมูลโครงสร้างไฟล์ได้: {e}"
    if ext in ['.txt', '.csv', '.md']:
        if b'\x00' in header:
            return False, "โครงสร้างไฟล์ขัดแย้งกับข้อความธรรมดา (พบโค้ดไบนารีแฝงในไฟล์)"
    if ext == '.pdf' and not header.startswith(b'%PDF'):
        return False, "โครงสร้างไฟล์ PDF ไม่ถูกต้อง (ลายเซ็นต์ไฟล์ไม่ถูกต้อง)"
    if ext == '.png' and not header.startswith(b'\x89PNG\r\n\x1a\n'):
        return False, "โครงสร้างไฟล์ PNG ไม่ถูกต้อง"
    if ext in ['.jpg', '.jpeg'] and not header.startswith(b'\xff\xd8\xff'):
        return False, "โครงสร้างไฟล์ JPEG/JPG ไม่ถูกต้อง"
    return True, ""


# ═══════════════════════════════════════════════════════════════
# URL Safety (SSRF Prevention)
# ═══════════════════════════════════════════════════════════════

def _is_safe_url(url: str) -> bool:
    """Block SSRF: only allow public http/https URLs."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        blocked_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
        if host in blocked_hosts:
            return False
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            pass  # hostname, not IP — OK
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# Weather Cache & Context
# ═══════════════════════════════════════════════════════════════

_weather_cache = {"data": "กำลังเตรียมข้อมูลสภาพอากาศ...", "timestamp": 0}

def update_weather_background():
    """Fetch Bangkok weather in background to prevent blocking chat."""
    global _weather_cache
    import requests
    
    WMO_CODES = {
        0: "ท้องฟ้าแจ่มใส", 1: "ท้องฟ้าโปร่ง", 2: "มีเมฆบางส่วน", 3: "เมฆมาก",
        45: "หมอกลง", 48: "หมอกน้ำค้างแข็ง",
        51: "ฝนปรอยๆ", 53: "ฝนปรอยๆ", 55: "ฝนปรอยๆ หนาแน่น",
        61: "ฝนตกเล็กน้อย", 63: "ฝนตกปานกลาง", 65: "ฝนตกหนัก",
        80: "ฝนซู่เล็กน้อย", 81: "ฝนซู่ปานกลาง", 82: "ฝนซู่รุนแรง",
        95: "พายุฝนฟ้าคะนอง",
    }
    
    try:
        w_url = "https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.51&current=temperature_2m,weather_code&timezone=Asia%2FBangkok"
        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=13.75&longitude=100.51&current=pm2_5&timezone=Asia%2FBangkok"
        
        w_res = requests.get(w_url, timeout=10).json()
        aq_res = requests.get(aq_url, timeout=10).json()
        
        cur = w_res.get("current", {})
        temp = round(cur.get("temperature_2m", 0))
        cond = WMO_CODES.get(cur.get("weather_code", 0), "แจ่มใส")
        pm25 = aq_res.get("current", {}).get("pm2_5", 0)
        
        _weather_cache["data"] = f"ขณะนี้ในกรุงเทพฯ: {cond}, อุณหภูมิ {temp}°C, PM2.5: {pm25} µg/m³"
        _weather_cache["timestamp"] = time.time()
        print("🌤️ Background Weather Synced", flush=True)
    except Exception as e:
        print(f"⚠️ Background Weather Error: {e}", flush=True)

def get_weather_context():
    return _weather_cache["data"]


# ═══════════════════════════════════════════════════════════════
# Thai Holidays 2026
# ═══════════════════════════════════════════════════════════════

THAI_HOLIDAYS_2026 = {
    "2026-01-01": "วันขึ้นปีใหม่",
    "2026-02-11": "วันมาฆบูชา",
    "2026-04-06": "วันจักรี",
    "2026-04-13": "วันสงกรานต์",
    "2026-04-14": "วันสงกรานต์",
    "2026-04-15": "วันสงกรานต์",
    "2026-05-01": "วันแรงงานแห่งชาติ",
    "2026-05-04": "วันฉัตรมงคล",
    "2026-05-11": "วันพืชมงคล",
    "2026-05-20": "วันวิสาขบูชา",
    "2026-06-03": "วันเฉลิมพระชนมพรรษาพระราชินี",
    "2026-07-18": "วันอาสาฬหบูชา",
    "2026-07-19": "วันเข้าพรรษา",
    "2026-07-28": "วันเฉลิมพระชนมพรรษา ร.10",
    "2026-08-12": "วันแม่แห่งชาติ",
    "2026-10-13": "วันนวมินทรมหาราช",
    "2026-10-23": "วันปิยมหาราช",
    "2026-12-05": "วันคล้ายวันเฉลิมพระชนมพรรษา ร.9 / วันพ่อแห่งชาติ",
    "2026-12-10": "วันรัฐธรรมนูญ",
    "2026-12-31": "วันสิ้นปี"
}

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════
# Legacy Users (loaded from env)
# ═══════════════════════════════════════════════════════════════

def _load_legacy_users() -> dict:
    result = {}
    for key, val in os.environ.items():
        if key.startswith("LEGACY_USER_") and val:
            result[key[len("LEGACY_USER_"):].lower()] = val
    return result

USERS = _load_legacy_users()
