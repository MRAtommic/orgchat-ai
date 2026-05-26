# ULTIMATE CACHE BUSTER - v11.0.4 [THAI-VOICE]
import sys
import os
import io
# ระบบรันบน app_server.py เพื่อบังคับให้ Railway ล้างแคชใหม่ทั้งหมดครับ
print(">>> SYSTEM v11.0.4 [ULTIMATE/THAI-VOICE/GTHREAD] READY.", flush=True)

# Force UTF-8 output encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8': 
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
from pathlib import Path
BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / ".env", override=True)

import os
import uuid
from pathlib import Path

print(">>> flask...", flush=True)
from flask import Flask, request, jsonify, render_template, render_template_string, send_from_directory, session, send_file, abort, redirect
import hmac, hashlib, base64, json, time, sqlite3, threading, urllib.parse, re
from functools import wraps
from datetime import datetime, timedelta
print(">>> flask_cors/socketio...", flush=True)
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
import requests
print(">>> google genai...", flush=True)
from google import genai
print(">>> apscheduler...", flush=True)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
print(">>> rag_engine...", flush=True)
import rag_engine
print(">>> database...", flush=True)
import database
print(">>> export_service...", flush=True)
import export_service
print(">>> ai_providers...", flush=True)
import ai_providers
print(">>> notification_db...", flush=True)
import notification_db
print(">>> fpdf/pywebpush...", flush=True)
from fpdf import FPDF
from pywebpush import webpush, WebPushException

print(">>> importing redis_manager...", flush=True)
from redis_manager import RedisManager
print(">>> importing reconciliation_service...", flush=True)
from reconciliation_service import ReconciliationService
print(">>> importing google_drive_service...", flush=True)
import google_drive_service
from google_drive_service import google_manager, GoogleWorkspaceManager
print(">>> importing settings_manager...", flush=True)
import settings_manager
print(">>> importing billing...", flush=True)
import billing
print(">>> importing payment...", flush=True)
import payment
print(">>> all imports done.", flush=True)
from task_tracker import db_task_tracker


# Pending LINE account linking tokens (token -> {"line_user_id": uid, "timestamp": time})
PENDING_LINE_LINKS = {}

# OAuth2 state store — เก็บ server-side แทน session cookie (แก้ปัญหา cookie หายกับ Cloudflare Tunnel)
_OAUTH_STATES: dict = {}  # {state_token: {username, mode, org_id, redirect_uri, expires}}

def _store_oauth_state(state: str, data: dict):
    data["expires"] = time.time() + 600  # 10 นาที
    _OAUTH_STATES[state] = data
    # ลบ state เก่าที่หมดอายุ
    now = time.time()
    for k in list(_OAUTH_STATES.keys()):
        if _OAUTH_STATES[k]["expires"] < now:
            _OAUTH_STATES.pop(k, None)

def _pop_oauth_state(state: str) -> dict | None:
    entry = _OAUTH_STATES.pop(state, None)
    if entry and entry["expires"] > time.time():
        return entry
    return None


# Per-user Google OAuth2 login
try:
    from oauth2_service import oauth2_service
    OAUTH2_AVAILABLE = True
except ImportError:
    OAUTH2_AVAILABLE = False
    print("⚠️ oauth2_service not available — per-user Google login disabled")

import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot_debug.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("OrgChatAI")

try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


# --- VAPID KEYS FOR PUSH NOTIFICATIONS ---
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "BNW7f7p3Ush_rg9vjIXxz1KTthTsiy3rz17oaygTy1-l4bTQJKpLeYEj4v3jYQkggo1VLa7w7sNb6mWDaIVH5eU")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "iVj1ybjnV5yP34d1BZ9ydP6Ad_m_24FC6AhYkc2On04")
VAPID_CLAIMS = {"sub": "mailto:" + os.environ.get("VAPID_CONTACT_EMAIL", "admin@openchat.sbs")}

from concurrent.futures import ThreadPoolExecutor

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
            # If it's the curve error, we might need to log more details but don't crash the worker
            print(f"General Push error for {username}: {e}")

def batch_send_push_notification(usernames, title, message, url='/'):
    """Send push notifications to multiple users in parallel."""
    if not usernames:
        return
    with ThreadPoolExecutor(max_workers=10) as executor:
        for uname in usernames:
            executor.submit(send_push_notification, uname, title, message, url)

def async_startup_tasks():
    """Run heavy initialization tasks in background to avoid Cloudflare 524."""
    print("⏳ Starting background initialization tasks...", flush=True)
    try:
        rag_engine.reinit_kb()  # Heavy ChromaDB sync — must stay in background

        # Warm up Google Drive/Sheets connection
        try:
            google_manager._initialize_thread_services()
            google_manager._validate_or_create_spreadsheet()
            google_manager.ensure_essential_sheets()
        except Exception as e:
            print(f"⚠️ Google Workspace warm-up failed: {e}", flush=True)

        # Auto-Cleanup orphaned Knowledge Base files
        print("🧹 Running automatic Knowledge Base cleanup...", flush=True)
        import kb_cleanup
        try:
            kb_cleanup.cleanup()
        except Exception as e:
            print(f"⚠️ Auto-cleanup failed: {e}", flush=True)

        # Seed essential rows — use _get_conn() for WAL + busy_timeout
        conn = database._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM chat_rooms WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO chat_rooms (id, name, owner) VALUES (1, 'กลุ่มทั่วไป (General)', 'System')")

        cursor.execute("INSERT OR IGNORE INTO user_profiles (username, display_name, avatar_url) VALUES ('AI-Assistant', 'น้องพั้น (Nong Punch)', 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png')")
        cursor.execute("UPDATE user_profiles SET display_name = 'น้องพั้น (Nong Punch)' WHERE username = 'AI-Assistant'")
        cursor.execute("INSERT OR IGNORE INTO user_settings (username, role) VALUES ('Admin', 'admin')")
        cursor.execute("UPDATE user_settings SET role = 'admin' WHERE username = 'Admin'")

        temp_users = ["admin", "few", "do", "AI-Assistant"]
        for u in temp_users:
            cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (1, ?)", (u.capitalize(),))

        conn.commit()
        conn.close()
        print("✅ Background initialization complete.", flush=True)
    except Exception as e:
        print(f"❌ Background startup error: {e}", flush=True)

    # Ensure critical directories exist
    os.makedirs("uploads/social_feed", exist_ok=True)
    os.makedirs("uploads/kb", exist_ok=True)
    os.makedirs("exports", exist_ok=True)

# Start heavy background tasks immediately
# Run DB migrations synchronously in main thread BEFORE background tasks start
# to avoid concurrent write conflicts ("database is locked")
try:
    database.init_db()
    billing.init_billing_tables()
    database.kanban_init_db()
except Exception as _init_e:
    print(f"⚠️ DB init warning: {_init_e}", flush=True)

import threading
threading.Thread(target=async_startup_tasks, daemon=True).start()

# Legacy fallback credentials — loaded from env vars, NOT hardcoded
# Set LEGACY_USER_<name>=<password> in .env to enable; leave empty to disable
def _load_legacy_users() -> dict:
    result = {}
    for key, val in os.environ.items():
        if key.startswith("LEGACY_USER_") and val:
            result[key[len("LEGACY_USER_"):].lower()] = val
    return result
USERS = _load_legacy_users()

# --- Thai Holidays 2026 ---
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
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

# ─── Weather Context for AI (Background Updated) ───────────
_weather_cache = {"data": "กำลังเตรียมข้อมูลสภาพอากาศ...", "timestamp": 0}

def update_weather_background():
    """Fetch Bangkok weather in background to prevent blocking chat."""
    global _weather_cache
    import time
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
        t_start = time.time()
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
        print(f"🌤️ Background Weather Synced ({time.time() - t_start:.2f}s)", flush=True)
    except Exception as e:
        print(f"⚠️ Background Weather Error: {e}", flush=True)

def get_weather_context():
    """Return cached weather immediately from background sync."""
    return _weather_cache["data"]


app = Flask(__name__)

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

# Trust one level of reverse-proxy headers (Railway, nginx, Cloudflare)
# so Flask sees the real client IP for rate limiting and logging
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

@app.teardown_request
def teardown_google_context(exception=None):
    """Teardown Google Workspace thread local context at the end of every request to prevent thread-reuse pollution."""
    try:
        from google_drive_service import google_manager
        google_manager.clear_context()
    except Exception as e:
        logger.error(f"Error tearing down Google Workspace context: {e}")

# --- Sentry Initialization ---
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("Sentry initialized.")
else:
    logger.info("SENTRY_DSN not set. Sentry disabled.")
# -----------------------------
_secret = os.environ.get("FLASK_SECRET_KEY", "")
if not _secret or _secret == "orgchat-super-secret-key-1234":
    import secrets as _sec
    _secret = _sec.token_hex(32)
    logger.warning("⚠️  FLASK_SECRET_KEY not set — using random key (sessions reset on restart). Set it in .env!")
app.secret_key = _secret
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload

# ─── Rate Limiting ────────────────────────────────────────────────────────────
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
_limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

CORS(app, supports_credentials=True)
# บังคับ async_mode เป็น threading เพื่อความเสถียรและทำงานร่วมกับ gthread ได้ดีที่สุด
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', max_http_payload_size=10*1024*1024)

VERSION = "1.10.0-STABLE"

# ─── APScheduler: Daily Summary at 08:00 ───────────────────
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(update_weather_background, 'interval', minutes=30)
    try:
        _scheduler.start()
        # Run once at boot (softly)
        update_weather_background()
    except:
        pass

    def _scheduled_auto_reconciliation():
        """งานสำรอง: กระทบยอดอัตโนมัติทุก 30 นาที กันพลาด"""
        try:
            print("⏰ [Scheduler] Running periodic reconciliation...", flush=True)
            # Use google_manager directly
            if google_manager.drive_service and google_manager.sheets_service and google_manager.spreadsheet_id:
                google_manager.auto_reconcile_internal()
                print("✅ [Scheduler] Periodic reconciliation complete.", flush=True)
            else:
                print("⚠️ [Scheduler] Google services or Spreadsheet ID not ready.", flush=True)
        except Exception as e:
            print(f"❌ [Scheduler] Recon Error: {e}", flush=True)

    _scheduler.add_job(_scheduled_auto_reconciliation, 'interval', minutes=30, id='periodic_recon')
    
    # Force run once on startup
    threading.Thread(target=_scheduled_auto_reconciliation, daemon=True).start()

    def _scheduled_daily_summary():
        """Run daily AI summary and push to all users at 08:00."""
        try:
            data = database.get_daily_activities()
            posts = data.get("posts", [])
            schedules = data.get("schedules", [])
            if not posts and not schedules:
                return
            posts_text = "\n".join([f"- {p['author']} โพสต์: {p['content'][:80]}" for p in posts])
            sched_text = "\n".join([f"- {s['title']} วันที่ {s['date']} {s['time']}" for s in schedules])
            prompt = (
                "สรุปกิจกรรมสำคัญประจำวันในบริษัทให้เพื่อนร่วมงานฟังแบบเป็นกันเองแต่เป็นมืออาชีพ (ไม่เกิน 3 ประโยค) ใช้สำนวนภาษาไทยที่เป็นธรรมชาติเหมือนเพื่อนร่วมงานเล่าให้กันฟัง:\n"
                f"โพสต์:{posts_text}\nตาราง:{sched_text}"
            )
            provider = ai_providers.get_provider()
            summary = ""
            for chunk in provider.chat_stream(prompt, [], "คุณคือ OrgChat AI ผู้ช่วยสรุปข่าวสารองค์กร"):
                if chunk:
                    summary += chunk
            if summary:
                unames = database.get_all_usernames()
                notification_db.notify_users(
                    unames, "daily_summary", "📋 Daily Briefing",
                    summary[:200], link="#feed"
                )
                batch_send_push_notification(unames, "📋 Daily Briefing", summary[:120], url="/")
                
                # --- Send to LINE as well ---
                threading.Thread(target=broadcast_line_announcement, args=(
                    "สรุปข่าวสารองค์กร", 
                    summary[:400]
                ), kwargs={
                    "fields": {
                        "วันที่": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "สรุป": summary[:300] + ("..." if len(summary) > 300 else "")
                    }
                }).start()
                
                print(f"✅ Daily summary sent to {len(unames)} users")
        except Exception as e:
            print(f"❌ Scheduled daily summary error: {e}")

    _scheduler.add_job(_scheduled_daily_summary, 'cron', hour=8, minute=0, id='daily_summary')
except ImportError:
    print("⚠️ APScheduler not installed — run: pip install APScheduler")

@app.route("/api/debug/routes")
@login_required
@admin_required
def list_routes():
    import urllib.parse
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:25} {methods:20} {rule}")
        output.append(line)
    return "<pre>" + "\n".join(sorted(output)) + "</pre>"

# ─── SocketIO Online Status Tracking ───────────────
online_users_registry = {} # sid -> username

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in online_users_registry:
        user = online_users_registry.pop(request.sid)
        print(f"User disconnected: {user}")
        # Broadcast updated list of unique online usernames
        active_users = list(set(online_users_registry.values()))
        socketio.emit('user_status_updated', {'online_users': active_users}, broadcast=True)

# ─── SocketIO Event Handlers ───────────────────────
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)

@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)

@socketio.on('user_online')
def on_user_online(data):
    # Validate against server-side session — don't trust client-provided username
    username = session.get('user')
    if not username:
        return
    online_users_registry[request.sid] = username
    join_room(f"user_{username}")
    active_users = list(set(online_users_registry.values()))
    socketio.emit('user_status_updated', {'online_users': active_users}, broadcast=True)

@socketio.on('user_typing')
def on_user_typing(data):
    room_id = data.get('roomName')
    if room_id:
        # Assuming we just broadcast it, the UI handles filtering 
        emit('user_typing', data, broadcast=True)



@app.route("/api/version")
def get_version():
    return jsonify({"version": VERSION, "status": "online"})

# ═══════════════════════════════════════════════════════════════
# Per-User Google OAuth2 Login Routes (Multi-Tenant Drive/Sheets)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/auth/google/debug-uri")
def auth_google_debug_uri():
    """แสดง redirect_uri ที่ app จะส่งไปให้ Google — ใช้ตรวจสอบว่าตรงกับ Console ไหม"""
    return jsonify({
        "redirect_uri_in_use": oauth2_service.redirect_uri if OAUTH2_AVAILABLE else "OAuth2 not available",
        "env_OAUTH2_REDIRECT_URI": os.environ.get("OAUTH2_REDIRECT_URI", "(ไม่ได้ตั้งค่า — ใช้ default localhost)"),
    })

@app.route("/api/auth/google/start")
def auth_google_start():
    """
    Initiate Google OAuth2 login flow.
    ?mode=org  → เชื่อมต่อระดับบริษัท (เฉพาะ admin) ทุกคนในบริษัทใช้ร่วมกัน
    ?mode=personal (default) → เชื่อมต่อส่วนตัว
    """
    if not OAUTH2_AVAILABLE or not oauth2_service.is_configured:
        return jsonify({"ok": False, "error": "ระบบ Google OAuth2 ยังไม่ได้ตั้งค่า กรุณาติดต่อผู้ดูแลระบบ"}), 503

    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อนเชื่อมต่อ Google"}), 401

    mode = request.args.get("mode", "personal")  # 'org' or 'personal'

    if mode == "org":
        user_role = session.get("role", "user")
        if user_role != "admin":
            return jsonify({"ok": False, "error": "เฉพาะ Admin เท่านั้นที่เชื่อมต่อ Google ระดับบริษัทได้"}), 403
        org_id = session.get("org_id", 1)
        if not billing.has_feature(org_id, "google_sheets"):
            plan = billing.get_effective_plan(org_id)
            return jsonify({
                "ok": False,
                "error": "upgrade_required",
                "message": "การเชื่อมต่อ Google Sheets ต้องการ Plan Pro ขึ้นไป",
                "current_plan": plan,
            }), 403
    else:
        org_id = None

    try:
        redirect_uri = oauth2_service.redirect_uri
        import secrets as _sec
        state_token = _sec.token_urlsafe(32)

        authorization_url, _, code_verifier = oauth2_service.get_authorization_url(
            redirect_uri=redirect_uri,
            state=state_token
        )

        # เก็บ state บน server (ไม่พึ่ง session cookie — แก้ปัญหา Cloudflare Tunnel)
        _store_oauth_state(state_token, {
            "username": username,
            "mode": mode,
            "org_id": org_id,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        })

        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"OAuth2 start error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/auth/google/callback")
def auth_google_callback():
    """Handle Google OAuth2 callback — exchange code for tokens."""
    if not OAUTH2_AVAILABLE:
        return "<h1>OAuth2 ไม่พร้อมใช้งาน</h1>", 503

    # Verify state — อ่านจาก server-side store ไม่พึ่ง session cookie
    state = request.args.get('state')
    state_data = _pop_oauth_state(state) if state else None
    if not state_data:
        return "<h1>Invalid state — กรุณาลองใหม่</h1><p><a href='/'>กลับหน้าหลัก</a></p>", 400

    username = state_data.get("username") or session.get("user")
    if not username:
        return "<h1>กรุณาเข้าสู่ระบบก่อน</h1><p><a href='/'>กลับหน้าหลัก</a></p>", 401

    # Check for error from Google
    error = request.args.get('error')
    if error:
        return f"<h1>Google ปฏิเสธการเชื่อมต่อ</h1><p>{error}</p><p><a href='/'>กลับหน้าหลัก</a></p>", 400

    authorization_code = request.args.get('code')
    if not authorization_code:
        return "<h1>ไม่พบ authorization code</h1><p><a href='/'>กลับหน้าหลัก</a></p>", 400

    try:
        redirect_uri = state_data.get("redirect_uri", oauth2_service.redirect_uri)
        mode = state_data.get("mode", "personal")
        org_id = state_data.get("org_id")

        # Exchange the code for tokens
        token_result = oauth2_service.exchange_code_for_token(
            authorization_code,
            redirect_uri=redirect_uri,
            code_verifier=state_data.get("code_verifier")
        )

        google_email = token_result.get('email', '')
        google_name  = token_result.get('name', '')

        if mode == 'org' and org_id:
            # บันทึกโทเค็นระดับบริษัท — ทุกคนในบริษัทใช้ร่วมกัน
            database.save_org_google_token(
                org_id=org_id,
                google_email=google_email,
                access_token=token_result.get('access_token'),
                refresh_token=token_result.get('refresh_token'),
                token_expiry=token_result.get('token_expiry'),
                connected_by=username
            )
            setup_ok = oauth2_service.setup_org_workspace(org_id, google_email, connected_by=username)
            scope_label = "บริษัท (ทุกคนในองค์กรใช้ร่วมกัน)"
        else:
            # บันทึกโทเค็นส่วนตัว
            database.save_google_token(
                username=username,
                google_email=google_email,
                access_token=token_result.get('access_token'),
                refresh_token=token_result.get('refresh_token'),
                token_expiry=token_result.get('token_expiry')
            )
            # Update profile with Google avatar if not set
            profile = database.get_user_profile(username)
            if not profile.get('avatar_url'):
                database.update_user_profile(username, display_name=google_name,
                                             avatar_url=token_result.get('picture'))
            setup_ok = oauth2_service.setup_user_workspace(username, google_email)
            scope_label = "ส่วนตัว"

        GoogleWorkspaceManager.invalidate_user_cache(username)

        _CSS = """body{font-family:'Inter','Sarabun',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
        .card{background:white;border-radius:20px;padding:40px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.3);max-width:460px}
        .email{background:#F0FDF4;color:#059669;padding:8px 16px;border-radius:10px;font-weight:600;display:inline-block;margin:10px 0}
        .badge{background:#EFF6FF;color:#1D4ED8;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600}
        .btn{display:inline-block;background:#1D4ED8;color:white;padding:12px 30px;border-radius:12px;text-decoration:none;font-weight:600;margin-top:20px}"""

        if setup_ok:
            return render_template_string(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>เชื่อมต่อสำเร็จ!</title>
            <style>{_CSS}</style></head>
            <body style="background:linear-gradient(135deg,#667eea,#764ba2)">
            <div class="card">
              <div style="font-size:48px">✅</div>
              <h1 style="color:#059669">เชื่อมต่อ Google สำเร็จ!</h1>
              <span class="badge">ระดับ: {{{{ scope }}}}</span>
              <br><div class="email">{{{{ email }}}}</div>
              <p style="color:#475569">ระบบสร้าง Google Sheets และโฟลเดอร์ Drive เรียบร้อยแล้ว</p>
              <a href="/" class="btn">กลับหน้าหลัก</a>
            </div></body></html>""", email=google_email, scope=scope_label)
        else:
            return render_template_string(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>เชื่อมต่อ (บางส่วน)</title>
            <style>{_CSS}</style></head>
            <body style="background:linear-gradient(135deg,#f59e0b,#ef4444)">
            <div class="card">
              <h1 style="color:#D97706">⚠️ เชื่อมต่อสำเร็จ แต่สร้าง Workspace ไม่สมบูรณ์</h1>
              <span class="badge">ระดับ: {{{{ scope }}}}</span>
              <p style="color:#475569">บัญชีเชื่อมต่อแล้ว แต่สร้าง Sheets/Drive ไม่สำเร็จ ลองยกเลิกแล้วเชื่อมต่อใหม่</p>
              <a href="/" class="btn">กลับหน้าหลัก</a>
            </div></body></html>""", scope=scope_label)

    except Exception as e:
        logger.error(f"OAuth2 callback error: {e}")
        return f"<h1>เกิดข้อผิดพลาด</h1><p>{e}</p><p><a href='/'>กลับหน้าหลัก</a></p>", 500


@app.route("/api/auth/google/status")
def auth_google_status():
    """Check if the current user has connected their Google account."""
    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    if not OAUTH2_AVAILABLE:
        return jsonify({
            "ok": True,
            "oauth2_available": False,
            "connected": False,
            "message": "ระบบ OAuth2 ไม่พร้อมใช้งาน"
        })

    org_id   = session.get("org_id", 1)
    user_role = session.get("role", "user")

    # Org-level status
    org_info = oauth2_service.get_org_connection_info(org_id)
    # Personal status
    personal_info = oauth2_service.get_user_connection_info(username)

    # Effective connection = org first, then personal
    effective = org_info if org_info['connected'] else personal_info
    effective_source = 'org' if org_info['connected'] else ('personal' if personal_info['connected'] else 'none')

    def _sheet_url(sid):
        return f"https://docs.google.com/spreadsheets/d/{sid}/edit" if sid else None
    def _drive_url(fid):
        return f"https://drive.google.com/drive/folders/{fid}" if fid else None

    return jsonify({
        "ok": True,
        "oauth2_available": oauth2_service.is_configured,
        "is_admin": user_role == "admin",
        "effective_source": effective_source,
        "connected": effective['connected'],
        "email": effective.get('email'),
        "spreadsheet_id": effective.get('spreadsheet_id'),
        "spreadsheet_url": _sheet_url(effective.get('spreadsheet_id')),
        "drive_folder_url": _drive_url(effective.get('drive_folder_id')),
        "org": {
            "connected": org_info['connected'],
            "email": org_info.get('email'),
            "connected_by": org_info.get('connected_by'),
            "spreadsheet_url": _sheet_url(org_info.get('spreadsheet_id')),
            "drive_folder_url": _drive_url(org_info.get('drive_folder_id')),
        },
        "personal": {
            "connected": personal_info['connected'],
            "email": personal_info.get('email'),
            "spreadsheet_url": _sheet_url(personal_info.get('spreadsheet_id')),
            "drive_folder_url": _drive_url(personal_info.get('drive_folder_id')),
        }
    })


@app.route("/api/auth/google/disconnect", methods=["POST"])
def auth_google_disconnect():
    """
    Disconnect Google account.
    ?scope=org  → ยกเลิกระดับบริษัท (admin only)
    ?scope=personal → ยกเลิกส่วนตัว (default)
    """
    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    if not OAUTH2_AVAILABLE:
        return jsonify({"ok": False, "error": "OAuth2 not available"}), 503

    scope = request.args.get("scope", "personal")

    if scope == "org":
        user_role = session.get("role", "user")
        if user_role != "admin":
            return jsonify({"ok": False, "error": "เฉพาะ Admin เท่านั้นที่ยกเลิกการเชื่อมต่อระดับบริษัทได้"}), 403
        org_id = session.get("org_id", 1)
        oauth2_service.disconnect_org(org_id)
        google_manager.set_context(username=None, org_id=org_id)
        return jsonify({"ok": True, "message": "ยกเลิกการเชื่อมต่อ Google ระดับบริษัทสำเร็จ"})

    oauth2_service.disconnect_user(username)
    GoogleWorkspaceManager.invalidate_user_cache(username)
    return jsonify({"ok": True, "message": "ยกเลิกการเชื่อมต่อ Google ส่วนตัวสำเร็จ"})



def render_link_error(error):
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>เกิดข้อผิดพลาด - OrgChat AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --error: #EF4444;
                --bg: #0D0D0D;
                --card-bg: rgba(25, 25, 25, 0.65);
                --card-border: rgba(239, 68, 68, 0.2);
                --text: #F3F4F6;
                --text-muted: #9CA3AF;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', 'Sarabun', sans-serif;
                background: radial-gradient(circle at 50% 50%, #1c1515 0%, #0d0d0d 100%);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                overflow-x: hidden;
            }}
            .container {{
                width: 100%;
                max-width: 440px;
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 48px 32px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
                text-align: center;
                animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .error-icon {{
                width: 72px;
                height: 72px;
                background: rgba(239, 68, 68, 0.1);
                border: 2px solid var(--error);
                color: var(--error);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                margin: 0 auto 28px auto;
                box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
                animation: scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
            }}
            @keyframes scaleIn {{
                from {{ transform: scale(0); opacity: 0; }}
                to {{ transform: scale(1); opacity: 1; }}
            }}
            h1 {{
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 16px;
                color: #FFFFFF;
            }}
            p {{
                font-size: 15px;
                color: var(--text-muted);
                line-height: 1.6;
                margin-bottom: 32px;
            }}
            .btn {{
                display: inline-block;
                width: 100%;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: var(--text);
                font-weight: 600;
                font-size: 15px;
                padding: 14px;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                margin-top: 10px;
                font-family: inherit;
            }}
            .btn:hover {{
                background: rgba(255, 255, 255, 0.1);
                border-color: rgba(255, 255, 255, 0.2);
            }}
            .footer-info {{
                margin-top: 40px;
                font-size: 11px;
                color: rgba(255, 255, 255, 0.2);
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">!</div>
            <h1>เกิดข้อผิดพลาดในการผูกบัญชีค่ะ</h1>
            <p>{error}</p>
            
            <a href="javascript:window.close();" class="btn">ปิดหน้าต่างนี้</a>
            
            <div class="footer-info">
                ORGCHAT AI SYSTEM &bull; ERROR ENCOUNTERED
            </div>
        </div>
    </body>
    </html>
    """

def render_success_page(username):
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ผูกบัญชีสำเร็จ - OrgChat AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --success: #10B981;
                --bg: #0D0D0D;
                --card-bg: rgba(25, 25, 25, 0.65);
                --card-border: rgba(16, 185, 129, 0.2);
                --text: #F3F4F6;
                --text-muted: #9CA3AF;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', 'Sarabun', sans-serif;
                background: radial-gradient(circle at 50% 50%, #151a18 0%, #0d0d0d 100%);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                overflow-x: hidden;
            }}
            .container {{
                width: 100%;
                max-width: 440px;
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 48px 32px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
                text-align: center;
                animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .success-icon {{
                width: 72px;
                height: 72px;
                background: rgba(16, 185, 129, 0.1);
                border: 2px solid var(--success);
                color: var(--success);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                margin: 0 auto 28px auto;
                box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
                animation: scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
            }}
            @keyframes scaleIn {{
                from {{ transform: scale(0); opacity: 0; }}
                to {{ transform: scale(1); opacity: 1; }}
            }}
            h1 {{
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 12px;
                color: #FFFFFF;
            }}
            .username-badge {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #D4AF37;
                padding: 6px 16px;
                border-radius: 99px;
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            p {{
                font-size: 15px;
                color: var(--text-muted);
                line-height: 1.6;
                margin-bottom: 32px;
            }}
            .info-box {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 16px;
                text-align: left;
                font-size: 13px;
                color: var(--text-muted);
                line-height: 1.5;
            }}
            .info-item {{
                display: flex;
                margin-bottom: 8px;
            }}
            .info-item:last-child {{
                margin-bottom: 0;
            }}
            .info-label {{
                font-weight: bold;
                color: var(--text);
                width: 24px;
                flex-shrink: 0;
            }}
            .footer-info {{
                margin-top: 40px;
                font-size: 11px;
                color: rgba(255, 255, 255, 0.2);
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">&#10003;</div>
            <h1>ผูกบัญชีสำเร็จเรียบร้อยค่ะ!</h1>
            <div class="username-badge">{username}</div>
            <p>ยินดีด้วยค่ะ บัญชี LINE ของคุณได้รับการผูกกับระบบ OrgChat AI เรียบร้อยแล้ว ต่อจากนี้ สลิปและไฟล์ที่คุณส่งใน LINE จะถูกบันทึกเข้า Drive และ Sheet ส่วนตัวของคุณโดยตรงโดยอัตโนมัติค่ะ</p>
            
            <div class="info-box">
                <div class="info-item">
                    <span class="info-label">&#128161;</span>
                    <span>ตอนนี้คุณสามารถกลับไปใช้งานที่แชท LINE Bot ได้ตามปกติเลยนะคะ</span>
                </div>
            </div>
            
            <div class="footer-info">
                ORGCHAT AI SYSTEM &bull; SECURE CONNECTION
            </div>
        </div>
    </body>
    </html>
    """

def render_login_page(token, error=None):
    error_html = f'<div class="error-msg">&#9888; {error}</div>' if error else ''
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ผูกบัญชี LINE - OrgChat AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #cda252;
                --primary-hover: #b88d3d;
                --bg: #0D0D0D;
                --card-bg: rgba(25, 25, 25, 0.65);
                --card-border: rgba(205, 170, 82, 0.15);
                --text: #F3F4F6;
                --text-muted: #9CA3AF;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', 'Sarabun', sans-serif;
                background: radial-gradient(circle at 50% 50%, #1c1a17 0%, #0d0d0d 100%);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                overflow-x: hidden;
            }}
            .container {{
                width: 100%;
                max-width: 440px;
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 40px 32px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
                text-align: center;
                position: relative;
                animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .logo-container {{
                margin-bottom: 24px;
            }}
            .logo {{
                font-size: 28px;
                font-weight: 700;
                letter-spacing: 2px;
                background: linear-gradient(135deg, #FFF 30%, var(--primary) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            h1 {{
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 8px;
                color: var(--text);
            }}
            p {{
                font-size: 14px;
                color: var(--text-muted);
                line-height: 1.6;
                margin-bottom: 28px;
            }}
            .form-group {{
                margin-bottom: 20px;
                text-align: left;
            }}
            label {{
                display: block;
                font-size: 13px;
                font-weight: 600;
                color: var(--text-muted);
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            input {{
                width: 100%;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 14px 16px;
                font-size: 15px;
                color: var(--text);
                outline: none;
                transition: all 0.3s;
                font-family: inherit;
            }}
            input:focus {{
                border-color: var(--primary);
                background: rgba(255, 255, 255, 0.06);
                box-shadow: 0 0 0 4px rgba(205, 170, 82, 0.1);
            }}
            .error-msg {{
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.25);
                color: #F87171;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                text-align: left;
                margin-bottom: 20px;
                line-height: 1.5;
            }}
            .btn {{
                width: 100%;
                background: linear-gradient(135deg, var(--primary) 0%, #b88d3d 100%);
                color: #0D0D0D;
                font-weight: 700;
                font-size: 15px;
                padding: 14px;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                margin-top: 10px;
                font-family: inherit;
                box-shadow: 0 4px 12px rgba(205, 170, 82, 0.2);
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(205, 170, 82, 0.35);
                background: linear-gradient(135deg, #e3b865 0%, var(--primary) 100%);
            }}
            .btn:active {{
                transform: translateY(0);
            }}
            .footer-info {{
                margin-top: 32px;
                font-size: 11px;
                color: rgba(255, 255, 255, 0.3);
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-container">
                <span class="logo">ORGCHAT AI</span>
            </div>
            <h1>เชื่อมต่อ LINE Bot ของคุณ</h1>
            <p>กรุณาลงชื่อเข้าใช้ด้วยบัญชี OrgChat AI ของคุณเพื่อผูกบัญชี LINE Bot และเข้าถึงระบบจัดเก็บเอกสารอัตโนมัติค่ะ</p>
            
            {error_html}
            
            <form method="POST" action="/line/link_magic?token={token}">
                <div class="form-group">
                    <label for="username">ชื่อผู้ใช้ (Username)</label>
                    <input type="text" id="username" name="username" placeholder="ระบุชื่อผู้ใช้ของคุณ" required autocomplete="username">
                </div>
                <div class="form-group">
                    <label for="password">รหัสผ่าน (Password)</label>
                    <input type="password" id="password" name="password" placeholder="ระบุรหัสผ่านของคุณ" required autocomplete="current-password">
                </div>
                <button type="submit" class="btn">ผูกบัญชีใช้งาน</button>
            </form>
            
            <div class="footer-info">
                SECURE AUTHENTICATION &bull; ORGCHAT SYSTEM
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/line/link_magic", methods=['GET', 'POST'])
def line_link_magic():
    token = request.args.get('token')
    if not token or token not in PENDING_LINE_LINKS:
        return render_link_error("โทเค็นสำหรับผูกบัญชีไม่ถูกต้องหรือหมดอายุแล้วค่ะ"), 400
        
    link_data = PENDING_LINE_LINKS[token]
    # Check expiry (10 minutes = 600 seconds)
    if time.time() - link_data.get("timestamp", 0) > 600:
        del PENDING_LINE_LINKS[token]
        return render_link_error("โทเค็นสำหรับผูกบัญชีหมดอายุแล้วค่ะ กรุณาขอลิงก์ใหม่ใน LINE Bot อีกครั้งนะคะ"), 400
        
    line_user_id = link_data["line_user_id"]
    
    if request.method == 'GET':
        # If user is already logged in, auto-link
        username = session.get("user")
        if username:
            database.link_line_user(username, line_user_id)
            del PENDING_LINE_LINKS[token]
            return render_success_page(username)
        return render_login_page(token)
        
    elif request.method == 'POST':
        username_raw = request.form.get("username", "").strip()
        username_lower = username_raw.lower()
        password = request.form.get("password", "")
        
        settings = database.get_user_setting(username_raw)
        authenticated = False
        resolved_username = username_raw
        
        if settings.get("custom_password") and database.check_password(password, settings["custom_password"]):
            if not settings.get("is_active", 1):
                return render_login_page(token, error="บัญชีผู้ใช้ของคุณถูกระงับการใช้งานชั่วคราวค่ะ")
            resolved_username = settings.get("username_original", username_raw)
            authenticated = True
        elif username_lower in USERS and USERS[username_lower] == password:
            if not settings.get("is_active", 1):
                return render_login_page(token, error="บัญชีผู้ใช้ของคุณถูกระงับการใช้งานชั่วคราวค่ะ")
            resolved_username = username_raw.capitalize()
            authenticated = True
            
        if authenticated:
            session.permanent = True
            session["user"] = resolved_username
            database.link_line_user(resolved_username, line_user_id)
            del PENDING_LINE_LINKS[token]
            return render_success_page(resolved_username)
        else:
            return render_login_page(token, error="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้องค่ะ")



ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".md", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".docx", ".xlsx"}

def validate_uploaded_file(file_stream, filename) -> tuple[bool, str]:
    """
    Validates an uploaded file strictly based on:
    1. Extension check against ALLOWED_EXTENSIONS
    2. Actual content inspection (MIME type / magic headers)
    3. Null-byte validation for text files
    """
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




def _get_gemini_api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY", "").strip() or None


def _configure_gemini(api_key: str):
    # google-genai ใหม่สร้าง client ต่อ session — ไม่มี configure() แบบ global
    pass  # ไม่จำเป็นต้อง configure global แล้ว


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
        # ไม่มี org → สร้าง personal org ให้อัตโนมัติ (แยก billing/ข้อมูลจาก user อื่น)
        try:
            personal_org_name = f"personal_{username}"
            org_id, _ = database.create_organization(personal_org_name, username)
        except Exception:
            # ถ้าสร้างไม่ได้ (ชื่อซ้ำ ฯลฯ) ดึง org ที่มีอยู่แล้ว
            orgs_retry = database.get_user_orgs(username)
            org_id = orgs_retry[0]["id"] if orgs_retry else 1
        session["org_id"] = org_id
        session["org_role"] = "admin"  # เจ้าของ personal org ตัวเอง


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
        return None # Fallback

    # Admin bypass — still scope to org
    user_settings = database.get_user_setting(username)
    if user_settings.get("role") == "admin":
        return {"$or": [{"organization_id": org_id}, {"organization_id": {"$eq": None}}]}

    # Get categories the user can access
    cats = database.get_categories(username)
    # Store IDs as both int and str to bridge any type mismatch in ChromaDB
    allowed_ids = []
    for c in cats:
        if c.get('id') is not None:
            allowed_ids.append(c['id'])
            allowed_ids.append(str(c['id']))

    # We allow unassigned files (empty string in ChromaDB) to all users who have KB access
    org_clause = {"$or": [{"organization_id": org_id}, {"organization_id": {"$eq": None}}]}
    unassigned_filters = [{"category_id": ""}]

    if not allowed_ids:
        # User has no specific category access, only unassigned within org
        return {"$and": [org_clause, {"$or": unassigned_filters}]}

    # Return filter: (category_id in allowed OR unassigned) AND (org matches)
    res = {
        "$and": [
            org_clause,
            {"$or": [{"category_id": {"$in": allowed_ids}}, *unassigned_filters]}
        ]
    }
    if 'log_bot' in globals() or 'log_bot' in locals():
        log_bot(f"🛡️ [AUTH] RAG filter for {username} org={org_id}: {len(allowed_ids)//2} allowed categories.")
    else:
        print(f"🛡️ [AUTH] RAG filter for {username} org={org_id}: {len(allowed_ids)//2} allowed categories.")
    return res


# ─────────────── Routes ───────────────

@app.route('/uploads/social_feed/<path:filename>')
def serve_social_uploads(filename):
    return send_from_directory('uploads/social_feed', filename)

@app.route('/uploads/profiles/<path:filename>')
def serve_profile_uploads(filename):
    return send_from_directory('uploads/profiles', filename)

@app.route('/uploads/group_chat/<path:filename>')
@login_required
def serve_group_chat_uploads(filename):
    return send_from_directory('uploads/group_chat', filename)

@app.route('/uploads/dm_chat/<path:filename>')
@login_required
def serve_dm_chat_uploads(filename):
    return send_from_directory('uploads/dm_chat', filename)

@app.route('/uploads/group_profiles/<path:filename>')
def serve_group_profile_uploads(filename):
    return send_from_directory('uploads/group_profiles', filename)

def _is_safe_url(url: str) -> bool:
    """Block SSRF: only allow public http/https URLs."""
    from urllib.parse import urlparse
    import ipaddress
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        # Block localhost and private IP ranges
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

@app.route("/api/link-preview")
@login_required
def get_link_preview():
    url = request.args.get("url")
    if not url:
        return jsonify({"ok": False}), 400
    if not url.startswith("http"):
        url = "http://" + url
    if not _is_safe_url(url):
        return jsonify({"ok": False, "error": "URL ไม่อนุญาต"}), 400

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=5, headers=headers, allow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find("title").text if soup.find("title") else url
        description = ""
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            description = og_desc["content"]
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc["content"]
                
        image = ""
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image = og_image["content"]
            
        return jsonify({
            "ok": True,
            "title": title[:100],
            "description": description[:200],
            "image": image,
            "url": url
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
@_limiter.limit("10 per minute; 50 per hour")
def api_login():
    data = request.json
    username_raw = data.get("username", "").strip()
    username_lower = username_raw.lower()
    password = data.get("password", "")
    
    # 1. Check Database first (Dynamic Users) — supports bcrypt hashed passwords
    settings = database.get_user_setting(username_raw)
    
    if settings.get("custom_password") and database.check_password(password, settings["custom_password"]):
        if not settings.get("is_active", 1):
            return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403
        session.permanent = True
        session["user"] = settings.get("username_original", username_raw)
        session["role"] = settings.get("role", "user")  # ← ใช้สำหรับ feature gate ระดับ system
        _set_session_org(session["user"])
        return jsonify({"ok": True, "user": session["user"], "role": session["role"], "org_role": session.get("org_role", "member")})

    # 2. Fallback to Hardcoded (plain text)
    if username_lower in USERS and USERS[username_lower] == password:
        user_to_session = username_raw.capitalize()
        if not settings.get("is_active", 1):
             return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403
        session.permanent = True
        session["user"] = user_to_session
        session["role"] = settings.get("role", "admin") if username_lower == "admin" else settings.get("role", "user")
        _set_session_org(user_to_session)
        return jsonify({"ok": True, "user": user_to_session, "role": session["role"], "org_role": session.get("org_role", "member")})

    return jsonify({"ok": False, "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"})

# ─── QR Code Login System ─────────────────────────────────
import uuid
_qr_tokens = {}  # token -> {"status": "pending"|"approved", "user": None, "created": timestamp}

@app.route("/api/qr/generate", methods=["POST"])
@_limiter.limit("10 per minute; 30 per hour")
def qr_generate():
    """Generate a unique QR login token for desktop."""
    token = str(uuid.uuid4())
    _qr_tokens[token] = {
        "status": "pending",
        "user": None,
        "created": time.time()
    }
    # Cleanup old tokens (> 5 min) — snapshot first to avoid dict-changed-during-iteration
    cutoff = time.time() - 300
    live = {k: v for k, v in list(_qr_tokens.items()) if v["created"] >= cutoff}
    _qr_tokens.clear()
    _qr_tokens.update(live)
    
    return jsonify({"ok": True, "token": token})

@app.route("/api/qr/poll/<token>")
@_limiter.limit("60 per minute")
def qr_poll(token):
    """Desktop polls this to check if QR was scanned and approved."""
    entry = _qr_tokens.get(token)
    if not entry:
        return jsonify({"ok": False, "error": "Token expired or invalid"}), 404
    
    # Check expiry (5 min)
    if time.time() - entry["created"] > 300:
        del _qr_tokens[token]
        return jsonify({"ok": False, "error": "Token expired"}), 410
    
    if entry["status"] == "approved" and entry["user"]:
        user = entry["user"]
        del _qr_tokens[token]
        # Log user in
        session.permanent = True
        session["user"] = user
        _u_settings = database.get_user_setting(user)
        session["role"] = _u_settings.get("role", "user")
        _set_session_org(user)
        return jsonify({"ok": True, "status": "approved", "user": user, "role": session["role"], "org_role": session.get("org_role", "member")})
    
    return jsonify({"ok": True, "status": "pending"})

@app.route("/api/qr/approve/<token>", methods=["POST"])
@login_required
def qr_approve(token):
    """Mobile user (already logged in) approves a QR login token."""
    entry = _qr_tokens.get(token)
    if not entry:
        return jsonify({"ok": False, "error": "Token ไม่ถูกต้องหรือหมดอายุ"}), 404
    
    if time.time() - entry["created"] > 300:
        del _qr_tokens[token]
        return jsonify({"ok": False, "error": "Token หมดอายุแล้ว"}), 410
    
    user = session.get("user")
    entry["status"] = "approved"
    entry["user"] = user
    return jsonify({"ok": True, "message": f"อนุมัติเข้าสู่ระบบสำหรับ {user} เรียบร้อย"})

@app.route("/qr-login/<token>")
def qr_login_page(token):
    """Page that mobile opens after scanning QR code."""
    entry = _qr_tokens.get(token)
    if not entry:
        return render_template_string(QR_APPROVE_HTML, token=token, error="Token ไม่ถูกต้องหรือหมดอายุ", valid=False)
    if time.time() - entry["created"] > 300:
        return render_template_string(QR_APPROVE_HTML, token=token, error="Token หมดอายุแล้ว กรุณาสร้าง QR Code ใหม่", valid=False)
    user = session.get("user")
    if not user:
        return render_template_string(QR_APPROVE_HTML, token=token, error="กรุณาเข้าสู่ระบบบนมือถือก่อน แล้วสแกนอีกครั้ง", valid=False)
    return render_template_string(QR_APPROVE_HTML, token=token, error=None, valid=True, user=user)

QR_APPROVE_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OrgChat QR Login</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', -apple-system, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
  .card { background: white; border-radius: 2rem; padding: 3rem 2rem; max-width: 400px; width: 100%; text-align: center; box-shadow: 0 25px 80px rgba(0,0,0,0.3); }
  .icon { width:80px; height:80px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 1.5rem; font-size:2.5rem; }
  .icon.success { background: #ecfdf5; }
  .icon.error { background: #fef2f2; }
  h1 { font-size:1.3rem; font-weight:800; color:#1e293b; margin-bottom:.5rem; }
  p { font-size:.85rem; color:#64748b; margin-bottom:1.5rem; line-height:1.6; }
  .user-badge { background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:.5rem 1.5rem; border-radius:999px; font-weight:700; font-size:.9rem; display:inline-block; margin-bottom:1.5rem; }
  .btn { display:block; width:100%; padding:1rem; border-radius:1rem; border:none; font-size:1rem; font-weight:800; cursor:pointer; transition:all .2s; }
  .btn-primary { background:linear-gradient(135deg,#667eea,#764ba2); color:white; }
  .btn-primary:hover { transform:scale(1.02); box-shadow:0 8px 25px rgba(102,126,234,.4); }
  .btn-primary:disabled { opacity:.6; cursor:not-allowed; transform:none; }
  .btn-secondary { background:#f1f5f9; color:#475569; margin-top:.8rem; }
  .done { display:none; }
  .done.show { display:block; }
  .done .icon { background:#ecfdf5; }
</style>
</head>
<body>
<div class="card">
  {% if not valid %}
    <div class="icon error">❌</div>
    <h1>ไม่สามารถดำเนินการได้</h1>
    <p>{{ error }}</p>
    <a href="/" class="btn btn-secondary" style="text-decoration:none;">กลับหน้าหลัก</a>
  {% else %}
    <div id="approveView">
      <div class="icon success">📱</div>
      <h1>ยืนยันการเข้าสู่ระบบ</h1>
      <p>อุปกรณ์อื่นกำลังขอเข้าสู่ระบบด้วยบัญชีของคุณ</p>
      <div class="user-badge">👤 {{ user }}</div>
      <br><br>
      <button id="approveBtn" class="btn btn-primary" onclick="approveLogin()">✅ อนุมัติเข้าสู่ระบบ</button>
      <button class="btn btn-secondary" onclick="window.close()">ยกเลิก</button>
    </div>
    <div id="doneView" class="done">
      <div class="icon success">✅</div>
      <h1>อนุมัติเรียบร้อยแล้ว!</h1>
      <p>อุปกรณ์อีกเครื่องจะเข้าสู่ระบบอัตโนมัติ<br>คุณสามารถปิดหน้านี้ได้</p>
    </div>
  {% endif %}
</div>
<script>
async function approveLogin() {
  const btn = document.getElementById('approveBtn');
  btn.disabled = true;
  btn.textContent = 'กำลังอนุมัติ...';
  try {
    const res = await fetch('/api/qr/approve/{{ token }}', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      document.getElementById('approveView').style.display = 'none';
      document.getElementById('doneView').classList.add('show');
    } else {
      alert(data.error || 'เกิดข้อผิดพลาด');
      btn.disabled = false;
      btn.textContent = '✅ อนุมัติเข้าสู่ระบบ';
    }
  } catch(e) {
    alert('เกิดข้อผิดพลาดในการเชื่อมต่อ');
    btn.disabled = false;
    btn.textContent = '✅ อนุมัติเข้าสู่ระบบ';
  }
}
</script>
</body>
</html>"""

@app.route("/api/login/google", methods=["POST"])
def api_login_google():
    data = request.json
    token = data.get("credential")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    
    if not token or not client_id:
        return jsonify({"ok": False, "error": "ไม่สามารถตรวจสอบสิทธิ์ด้วย Google ได้ (ไม่มี Token หรือ Client ID)"}), 400

    if not GOOGLE_AUTH_AVAILABLE:
        return jsonify({"ok": False, "error": "Google Auth library not installed on server"}), 500

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)

        # Token is valid, get the user's email
        email = idinfo.get("email")
        if not email:
            return jsonify({"ok": False, "error": "ไม่พบอีเมลจาก Google Account"}), 400
            
        username = email.split('@')[0]
        
        # --- Whitelist Check ---
        user_orgs = database.get_user_orgs(username)
        target_org_id = user_orgs[0]["id"] if user_orgs else 1
        
        if database.is_whitelist_enabled(target_org_id):
            if not database.is_org_admin(target_org_id, username) and not database.is_email_allowed(target_org_id, email):
                return jsonify({"ok": False, "error": "อีเมลนี้ไม่อยู่ในรายชื่อที่ได้รับอนุญาตให้เข้าสู่ระบบ (Whitelist)"}), 403

        # Check if user exists or is active
        settings = database.get_user_setting(username)
        if settings and not settings.get("is_active", 1):
             return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403

        # Update user profile with Google info if they have no avatar/display name
        profile = database.get_user_profile(username)
        display_name = profile.get("display_name") if profile.get("display_name") else idinfo.get("name")
        avatar_url = profile.get("avatar_url") if profile.get("avatar_url") else idinfo.get("picture")
        
        database.update_user_profile(username, display_name=display_name, avatar_url=avatar_url)

        session.permanent = True
        session["user"] = username
        _set_session_org(username)
        return jsonify({"ok": True, "user": username, "org_role": session.get("org_role", "member")})

    except Exception as e:
        print(f"Google Login Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


def clean_flex_payload(obj):
    """Recursively removes keys that violate LINE API schema, e.g. weight values other than 'bold'."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if k == "weight" and v != "bold":
                continue
            cleaned[k] = clean_flex_payload(v)
        return cleaned
    elif isinstance(obj, list):
        return [clean_flex_payload(item) for item in obj]
    else:
        return obj


def create_magic_link_flex_bubble(magic_link_url):
    """Creates a high-fidelity luxury minimal LINE Flex Message for Magic Link account linking in a clean minimalist light style."""
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#F8FAFC",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": "LINK ACCOUNT",
                    "color": "#64748B",
                    "weight": "bold",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": "เชื่อมต่อบัญชีผู้ใช้",
                    "color": "#0F172A",
                    "weight": "bold",
                    "size": "lg",
                    "margin": "sm"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px",
            "contents": [
                {
                    "type": "text",
                    "text": "ยินดีต้อนรับสู่ระบบ OrgChat AI ค่ะ เพื่อเริ่มต้นใช้งานระบบจัดเก็บไฟล์และลงสเปรดชีตแยกบัญชีส่วนตัว กรุณากดปุ่มด้านล่างเพื่อเชื่อมต่อบัญชี LINE ของคุณเข้ากับบัญชีเว็บของระบบค่ะ",
                    "color": "#475569",
                    "size": "sm",
                    "wrap": True
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xxl",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "เชื่อมต่อบัญชีทันที",
                                "uri": magic_link_url
                            },
                            "style": "primary",
                            "color": "#475569"
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": "หมายเหตุ: ลิงก์นี้มีความปลอดภัยสูงและจะหมดอายุภายใน 10 นาทีค่ะ",
                    "color": "#94A3B8",
                    "size": "xxs",
                    "wrap": True,
                    "margin": "lg",
                    "align": "center"
                }
            ]
        }
    }
    return clean_flex_payload(bubble)


def create_expense_flex_bubble(sheet_name, folder_name, net_amount, date_str, memo, vendor, file_link, sheet_url, edit_data_postback, raw_result=None, org_id=None, username=None):
    """Creates an ultra-premium LINE Flex Message, custom tailored to each document type."""
    # Extract row_num safely
    row_num = 1
    if edit_data_postback:
        try:
            for part in str(edit_data_postback).split("&"):
                if part.startswith("row="):
                    row_num = int(part.split("=")[1])
        except:
            pass

    # Extracted data from AI smart scan
    ext = {}
    if raw_result and isinstance(raw_result, dict):
        ext = raw_result.get('analysis', {}).get('extracted_data', {}) if raw_result.get('analysis') else {}

    # Robust date formatter
    formatted_date = date_str
    initial_date = datetime.now().strftime("%Y-%m-%d")
    if date_str and str(date_str).strip() != '-':
        try:
            date_str_clean = str(date_str).strip().replace("-", "/")
            parts = date_str_clean.split("/")
            thai_months = [
                "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
            ]
            if len(parts) == 3:
                if len(parts[0]) == 4: # YYYY/MM/DD
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                else: # DD/MM/YYYY or DD/MM/YY
                    day = int(parts[0])
                    month = int(parts[1])
                    year = int(parts[2])
                    if year < 100:
                        year += 2000
                if 1 <= month <= 12:
                    formatted_date = f"{day:02d} {thai_months[month]} {year}"
                    initial_date = f"{year:04d}-{month:02d}-{day:02d}"
        except:
            pass

    # Clean amount display
    try:
        if isinstance(net_amount, (int, float)):
            amount_big = f"{net_amount:,.2f}"
        else:
            val_clean = str(net_amount).replace(",", "").strip()
            val_float = float(val_clean)
            amount_big = f"{val_float:,.2f}"
    except:
        amount_big = str(net_amount) if net_amount else "-"

    if amount_big.endswith(".00"):
        amount_big = amount_big[:-3]

    # Defensive text wrapping
    sheet_name_str = str(sheet_name)
    folder_name_str = str(folder_name)
    formatted_date_str = str(formatted_date)
    vendor_str = str(vendor) if vendor and vendor != '-' else "ไม่ระบุ"
    memo_str = str(memo) if memo and memo != '-' else "จัดเก็บและสแกนผ่านระบบอัตโนมัติ"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Document Validation & Mismatch Detection
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ai_category = ""
    if raw_result and isinstance(raw_result, dict) and raw_result.get('analysis'):
        ai_category = raw_result.get('analysis', {}).get('category', '')

    # Normalize category lookup to handle spaces, underscores, casing variations
    norm_ai_cat = str(ai_category).strip().lower().replace("_", "").replace("-", "").replace(" ", "").replace("/", "")

    category_map = {
        "slip": ["สลิปโอนเงิน"],
        "bankslip": ["สลิปโอนเงิน"],
        "transferslip": ["สลิปโอนเงิน"],
        "สลิปโอนเงิน": ["สลิปโอนเงิน"],
        "สลิป": ["สลิปโอนเงิน"],
        "โอนเงิน": ["สลิปโอนเงิน"],
        "statement": ["สเตตเมนต์"],
        "bankstatement": ["สเตตเมนต์"],
        "สเตตเมนต์": ["สเตตเมนต์"],
        "รายการเดินบัญชี": ["สเตตเมนต์"],
        "idcard": ["บัตรประชาชน"],
        "id_card": ["บัตรประชาชน"],
        "nationalid": ["บัตรประชาชน"],
        "nationalidcard": ["บัตรประชาชน"],
        "บัตรประชาชน": ["บัตรประชาชน"],
        "บัตรประจำตัวประชาชน": ["บัตรประชาชน"],
        "receipt": ["ใบเสร็จ/ใบกำกับภาษี"],
        "invoice": ["ใบเสร็จ/ใบกำกับภาษี"],
        "receiptinvoice": ["ใบเสร็จ/ใบกำกับภาษี"],
        "ใบเสร็จ": ["ใบเสร็จ/ใบกำกับภาษี"],
        "ใบกำกับภาษี": ["ใบเสร็จ/ใบกำกับภาษี"],
        "ใบเสร็จรับเงิน": ["ใบเสร็จ/ใบกำกับภาษี"],
        "ใบเสร็จใบกำกับภาษี": ["ใบเสร็จ/ใบกำกับภาษี"],
        "quotation": ["ใบเสนอราคา"],
        "ใบเสนอราคา": ["ใบเสนอราคา"],
        "เสนอราคา": ["ใบเสนอราคา"]
    }

    mismatch_detected = False
    ai_suggested_sheet = ""
    if norm_ai_cat and norm_ai_cat in category_map:
        acceptable_sheets = category_map[norm_ai_cat]
        if sheet_name_str not in acceptable_sheets:
            mismatch_detected = True
            ai_suggested_sheet = acceptable_sheets[0]

    warning_banner = None
    if mismatch_detected and ai_suggested_sheet:
        warning_banner = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFF1F2",  # Soft Pink background
            "borderColor": "#FECDD3",      # Soft Pink border
            "borderWidth": "1px",
            "cornerRadius": "8px",
            "paddingAll": "12px",
            "margin": "md",
            "spacing": "xs",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "แจ้งเตือน: อาจส่งผิดหมวดหมู่",
                            "weight": "bold",
                            "size": "sm",
                            "color": "#E11D48",    # Raspberry warning red
                            "wrap": True
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": f"ระบบตรวจพบว่าเอกสารนี้อาจเป็น '{ai_suggested_sheet}' แต่ถูกบันทึกไว้ในหมวดหมู่ '{sheet_name_str}'",
                    "size": "xs",
                    "color": "#9F1239",            # Crimson text
                    "wrap": True,
                    "margin": "xs"
                },
                {
                    "type": "text",
                    "text": "หากต้องการย้าย กดปุ่ม 'ย้ายหมวดหมู่ (แนะนำ)' ด้านล่างได้ทันทีค่ะ",
                    "size": "xxs",
                    "color": "#9F1239",            # Crimson helper text
                    "wrap": True,
                    "margin": "xs"
                }
            ]
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Define color themes per document type
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    header_bg = "#F8FAFC"
    body_bg = "#FFFFFF"
    footer_bg = "#FFFFFF"
    accent_color = "#64748B"
    badge_bg = "#F1F5F9"
    badge_text_color = "#64748B"
    badge_label = "RECORDED"
    title_text = f"{amount_big} THB"
    subtitle_text = folder_name_str

    body_contents = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Branch by Sheet Category for tailored cards
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if sheet_name_str == "สเตตเมนต์":
        # ▓▓ BANK STATEMENT THEME (Light Mode Minimalist) ▓▓
        header_bg = "#F8FAFC"
        body_bg = "#FFFFFF"
        footer_bg = "#FFFFFF"
        accent_color = "#64748B"
        badge_bg = "#F1F5F9"
        badge_text_color = "#64748B"
        badge_label = "BANK STATEMENT"

        transactions = ext.get('transactions', [])
        tx_count = len(transactions)
        total_withdraw = 0.0
        total_deposit = 0.0
        for t in transactions:
            w_val = t.get('withdrawal') or t.get('ถอน') or t.get('out') or 0
            d_val = t.get('deposit') or t.get('ฝาก') or t.get('in') or 0
            try:
                total_withdraw += float(str(w_val).replace(',', '').strip()) if w_val and str(w_val) != '-' else 0.0
            except: pass
            try:
                total_deposit += float(str(d_val).replace(',', '').strip()) if d_val and str(d_val) != '-' else 0.0
            except: pass

        balance_val = ext.get('balance') or ext.get('ยอดคงเหลือ') or "-"
        try:
            if balance_val and str(balance_val).strip() != '-':
                val_float = float(str(balance_val).replace(",", "").strip())
                balance_display = f"{val_float:,.2f}"
                if balance_display.endswith(".00"):
                    balance_display = balance_display[:-3]
                title_text = f"{balance_display} THB"
            else:
                title_text = "รายการเดินบัญชี"
        except:
            title_text = str(balance_val)

        subtitle_text = "ยอดคงเหลือสุดท้าย"

        body_contents = [
            {"type": "separator", "color": "#F1F5F9"},
            {
                "type": "box", "layout": "vertical", "spacing": "md", "margin": "lg",
                "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "บันทึกเข้าชีต", "color": "#64748B", "size": "xs", "weight": "bold", "flex": 5},
                        {"type": "text", "text": "สเตตเมนต์ธนาคาร", "color": "#1E293B", "size": "xs", "weight": "bold", "flex": 7, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "ประจำวันที่", "color": "#64748B", "size": "xs", "weight": "bold", "flex": 5},
                        {"type": "text", "text": formatted_date_str, "color": "#1E293B", "size": "xs", "flex": 7, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "ยอดฝากรวม", "color": "#64748B", "size": "xs", "weight": "bold", "flex": 5},
                        {"type": "text", "text": f"+{total_deposit:,.2f} THB" if total_deposit > 0 else "0 THB", "color": "#0D9488", "size": "xs", "weight": "bold", "flex": 7, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "ยอดถอนรวม", "color": "#64748B", "size": "xs", "weight": "bold", "flex": 5},
                        {"type": "text", "text": f"-{total_withdraw:,.2f} THB" if total_withdraw > 0 else "0 THB", "color": "#E11D48", "size": "xs", "weight": "bold", "flex": 7, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "จำนวนรายการ", "color": "#64748B", "size": "xs", "weight": "bold", "flex": 5},
                        {"type": "text", "text": f"{tx_count} รายการ", "color": "#1E293B", "size": "xs", "weight": "bold", "flex": 7, "align": "end"}
                    ]}
                ]
            }
        ]

        # Add Recent Transaction Preview (up to 3 rows)
        if tx_count > 0:
            preview_rows = []
            for t in transactions[:3]:
                t_date = t.get('date') or ""
                t_time = t.get('time') or ""
                t_desc = t.get('description') or t.get('details') or t.get('memo') or "รายการ"
                t_cpty = t.get('counterparty') or ""
                t_withdraw = t.get('withdrawal') or t.get('ถอน') or t.get('out') or 0
                t_deposit = t.get('deposit') or t.get('ฝาก') or t.get('in') or 0

                try:
                    w_float = float(str(t_withdraw).replace(',', '').strip()) if t_withdraw and str(t_withdraw) != '-' else 0.0
                except: w_float = 0.0
                try:
                    d_float = float(str(t_deposit).replace(',', '').strip()) if t_deposit and str(t_deposit) != '-' else 0.0
                except: d_float = 0.0

                amt_str = ""
                amt_color = "#334155"
                if d_float > 0:
                    amt_str = f"+{d_float:,.2f}"
                    amt_color = "#0D9488"
                elif w_float > 0:
                    amt_str = f"-{w_float:,.2f}"
                    amt_color = "#E11D48"
                else:
                    amt_str = "-"

                if amt_str.endswith(".00"):
                    amt_str = amt_str[:-3]

                dt_lbl = f"{t_date} {t_time}".strip()
                desc_lbl = f"{t_desc}"
                if t_cpty and t_cpty != '-':
                    desc_lbl += f" ({t_cpty})"

                preview_rows.append({
                    "type": "box", "layout": "horizontal", "margin": "sm",
                    "contents": [
                        {"type": "box", "layout": "vertical", "flex": 7, "contents": [
                            {"type": "text", "text": desc_lbl, "color": "#334155", "size": "xxs", "wrap": True},
                            {"type": "text", "text": dt_lbl, "color": "#64748B", "size": "xxs"}
                        ]},
                        {"type": "text", "text": amt_str, "color": amt_color, "size": "sm", "weight": "bold", "flex": 3, "align": "end", "wrap": False}
                    ]
                })

            body_contents.append({
                "type": "box", "layout": "vertical", "margin": "lg", "paddingAll": "12px",
                "backgroundColor": "#F8FAFC", "cornerRadius": "8px",
                "contents": [
                    {"type": "text", "text": "รายการล่าสุด", "color": "#475569", "size": "xs", "weight": "bold", "margin": "xs"},
                    {"type": "separator", "color": "#E2E8F0", "margin": "sm"}
                ] + preview_rows
            })

    elif sheet_name_str == "บัตรประชาชน":
        # ▓▓ NATIONAL ID CARD THEME (Premium Minimalist White) ▓▓
        header_bg = "#F8FAFC"
        body_bg = "#FFFFFF"
        footer_bg = "#FFFFFF"
        accent_color = "#64748B"
        badge_bg = "#F1F5F9"
        badge_text_color = "#64748B"
        badge_label = "ID CARD"

        id_no = ext.get('id_number') or ext.get('tax_id') or "-"
        first_th = ext.get('id_card_first_name_th') or ext.get('first_name_th') or ""
        last_th = ext.get('id_card_last_name_th') or ext.get('last_name_th') or ""
        name_th = f"{first_th} {last_th}".strip()
        
        # Fallback beautifully if no Thai name is found
        if not name_th or name_th == "None None" or "จัดเก็บและสแกน" in name_th or name_th == "จัดเก็บและสแกนผ่านระบบอัตโนมัติ":
            name_th = "บัตรประชาชน (ยังไม่ระบุชื่อ)"

        first_en = ext.get('first_name_en') or ext.get('name_en') or ""
        last_en = ext.get('last_name_en') or ext.get('surname_en') or ""
        name_en = f"{first_en} {last_en}".strip() or "-"

        dob = ext.get('birth_date') or ext.get('birthday') or ext.get('dob') or "-"
        gender = ext.get('gender') or ext.get('sex') or "-"
        address = ext.get('address') or "-"
        laser = ext.get('laser_id') or ext.get('laser') or ext.get('ref_number') or "-"

        title_text = name_th
        subtitle_text = f"เลขประจำตัวประชาชน: {id_no}"

        body_contents = [
            {"type": "separator", "color": "#F1F5F9"},
            {
                "type": "box", "layout": "vertical", "spacing": "md", "margin": "lg",
                "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "English Name", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                        {"type": "text", "text": name_en, "color": "#1E293B", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "Birth & Gender", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                        {"type": "text", "text": f"{dob} · {gender}", "color": "#1E293B", "size": "xs", "flex": 8, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "Laser ID", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                        {"type": "text", "text": laser, "color": "#1E293B", "size": "xs", "flex": 8, "align": "end"}
                    ]},
                    {"type": "separator", "color": "#F1F5F9", "margin": "md"},
                    {
                        "type": "box", "layout": "vertical", "backgroundColor": "#F8FAFC",
                        "cornerRadius": "8px", "paddingAll": "12px",
                        "contents": [
                            {"type": "text", "text": "Address (ที่อยู่ตามบัตร)", "color": "#64748B", "size": "xxs", "weight": "bold"},
                            {"type": "text", "text": address, "color": "#1E293B", "size": "xs", "wrap": True, "margin": "xs"}
                        ]
                    }
                ]
            }
        ]

    elif sheet_name_str == "สลิปโอนเงิน":
        # ▓▓ TRANSFER SLIP THEME (Light Mode Minimalist) ▓▓
        header_bg = "#F8FAFC"
        body_bg = "#FFFFFF"
        footer_bg = "#FFFFFF"
        accent_color = "#64748B"
        badge_bg = "#F1F5F9"
        badge_text_color = "#64748B"
        badge_label = "TRANSFER SLIP"

        sender_bank = ext.get('sender_bank') or ext.get('bank_from') or "-"
        sender_name = ext.get('sender') or ext.get('sender_name') or "-"
        receiver_bank = ext.get('receiver_bank') or ext.get('bank_to') or "-"
        receiver_name = ext.get('receiver') or ext.get('receiver_name') or "-"
        time_val = ext.get('time') or ""
        ref_no = ext.get('ref_number') or ext.get('ref') or "-"

        body_contents = [
            {"type": "separator", "color": "#F1F5F9"},
            {"type": "box", "layout": "vertical", "spacing": "md", "margin": "lg", "contents": [
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "BOOKSHEET", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": "สลิปโอนเงิน", "color": "#334155", "size": "xs", "weight": "bold", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "DATE & TIME", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": f"{formatted_date_str} {time_val}".strip(), "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "SENDER (จาก)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": f"{sender_name} ({sender_bank})", "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "RECEIVER (ไปยัง)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": f"{receiver_name} ({receiver_bank})", "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "REF NUMBER", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": ref_no, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "separator", "color": "#F1F5F9", "margin": "md"},
                {"type": "box", "layout": "vertical", "backgroundColor": "#F8FAFC", "cornerRadius": "8px", "paddingAll": "10px", "contents": [
                    {"type": "text", "text": "MEMO", "color": "#64748B", "size": "xxs", "weight": "bold"},
                    {"type": "text", "text": memo_str, "color": "#334155", "size": "xs", "wrap": True, "margin": "xs"}
                ]}
            ]}
        ]

    elif sheet_name_str == "ใบเสร็จ/ใบกำกับภาษี":
        # ▓▓ TAX INVOICE THEME (Light Mode Minimalist) ▓▓
        header_bg = "#F8FAFC"
        body_bg = "#FFFFFF"
        footer_bg = "#FFFFFF"
        accent_color = "#64748B"
        badge_bg = "#F1F5F9"
        badge_text_color = "#64748B"
        badge_label = "TAX INVOICE"

        tax_id = ext.get('tax_id') or "-"
        gross_amt = ext.get('gross_amount') or "-"
        vat_amt = ext.get('vat_amount') or "-"
        wht_amt = ext.get('wht_amount') or "-"

        try: gross_str = f"{float(str(gross_amt).replace(',', '')):,.2f} THB" if gross_amt and str(gross_amt) != '-' else "-"
        except: gross_str = str(gross_amt)
        try: vat_str = f"{float(str(vat_amt).replace(',', '')):,.2f} THB" if vat_amt and str(vat_amt) != '-' else "-"
        except: vat_str = str(vat_amt)
        try: wht_str = f"{float(str(wht_amt).replace(',', '')):,.2f} THB" if wht_amt and str(wht_amt) != '-' else "-"
        except: wht_str = str(wht_amt)

        body_contents = [
            {"type": "separator", "color": "#F1F5F9"},
            {"type": "box", "layout": "vertical", "spacing": "md", "margin": "lg", "contents": [
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "BOOKSHEET", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": "ใบเสร็จ/ใบกำกับภาษี", "color": "#334155", "size": "xs", "weight": "bold", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "INVOICE DATE", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": formatted_date_str, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "VENDOR (ผู้ขาย)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": vendor_str, "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "TAX ID", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": tax_id, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "GROSS (ก่อนภาษี)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": gross_str, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "VAT (ภาษีมูลค่าเพิ่ม)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": vat_str, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "WHT (หัก ณ ที่จ่าย)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": wht_str, "color": "#E11D48" if wht_amt and str(wht_amt) != '-' else "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "separator", "color": "#F1F5F9", "margin": "md"},
                {"type": "box", "layout": "vertical", "backgroundColor": "#F8FAFC", "cornerRadius": "8px", "paddingAll": "10px", "contents": [
                    {"type": "text", "text": "SUMMARY/MEMO", "color": "#64748B", "size": "xxs", "weight": "bold"},
                    {"type": "text", "text": memo_str, "color": "#334155", "size": "xs", "wrap": True, "margin": "xs"}
                ]}
            ]}
        ]

    elif sheet_name_str == "ใบหัก ณ ที่จ่าย":
        # ▓▓ WITHHOLDING TAX THEME (Light Mode Minimalist) ▓▓
        header_bg = "#F8FAFC"
        body_bg = "#FFFFFF"
        footer_bg = "#FFFFFF"
        accent_color = "#64748B"
        badge_bg = "#F1F5F9"
        badge_text_color = "#64748B"
        badge_label = "WITHHOLDING TAX"

        payer = ext.get('payer_name') or ext.get('ผู้จ่ายเงิน') or "-"
        payee = ext.get('payee_name') or ext.get('ผู้รับเงิน') or "-"
        wht_rate = ext.get('wht_rate') or ext.get('wht_percent') or "-"
        wht_type = ext.get('wht_type') or ext.get('income_type') or "-"
        wht_amt = ext.get('wht_amount') or "-"

        try: wht_str = f"{float(str(wht_amt).replace(',', '')):,.2f} THB" if wht_amt and str(wht_amt) != '-' else "-"
        except: wht_str = str(wht_amt)

        title_text = wht_str
        subtitle_text = "ยอดหักภาษี ณ ที่จ่าย"

        body_contents = [
            {"type": "separator", "color": "#F1F5F9"},
            {"type": "box", "layout": "vertical", "spacing": "md", "margin": "lg", "contents": [
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "BOOKSHEET", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": "ใบหัก ณ ที่จ่าย", "color": "#334155", "size": "xs", "weight": "bold", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "DATE", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": formatted_date_str, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "PAYER (ผู้จ่ายเงิน)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": payer, "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "PAYEE (ผู้รับเงิน)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": payee, "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "TAX RATE (อัตรา)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": wht_rate, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "INCOME TYPE", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": wht_type, "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]}
            ]}
        ]

    elif sheet_name_str == "ใบเสนอราคา":
        # ▓▓ QUOTATION THEME (Light Mode Minimalist) ▓▓
        header_bg = "#F8FAFC"
        body_bg = "#FFFFFF"
        footer_bg = "#FFFFFF"
        accent_color = "#64748B"
        badge_bg = "#F1F5F9"
        badge_text_color = "#64748B"
        badge_label = "QUOTATION"

        issuer = ext.get('sender_name') or ext.get('ผู้เสนอราคา') or "-"
        customer = ext.get('receiver_name') or ext.get('ลูกค้า') or "-"

        body_contents = [
            {"type": "separator", "color": "#F1F5F9"},
            {"type": "box", "layout": "vertical", "spacing": "md", "margin": "lg", "contents": [
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "BOOKSHEET", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": "ใบเสนอราคา", "color": "#334155", "size": "xs", "weight": "bold", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "QUOTE DATE", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": formatted_date_str, "color": "#334155", "size": "xs", "flex": 8, "align": "end"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "ISSUER (ผู้เสนอ)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": issuer, "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "CUSTOMER (ลูกค้า)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": customer, "color": "#334155", "size": "xs", "flex": 8, "align": "end", "wrap": True}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "STATUS (สถานะ)", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": "รออนุมัติ", "color": "#475569", "size": "xs", "weight": "bold", "flex": 8, "align": "end"}
                ]}
            ]}
        ]

    else:
        # ▓▓ DEFAULT FALLBACK (Generic Document) ▓▓
        body_contents = [
            {"type": "separator", "color": "#F1F5F9"},
            {
                "type": "box", "layout": "vertical", "spacing": "md", "margin": "lg",
                "contents": [
                    {"type": "box", "layout": "horizontal", "action": {
                        "type": "postback",
                        "data": f"action=choose_new_sheet&sheet={sheet_name_str}&row={row_num}",
                        "displayText": "ฉันต้องการย้ายประเภทเอกสาร"
                    }, "contents": [
                        {"type": "text", "text": "BOOKSHEET", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4, "align": "start"},
                        {"type": "text", "text": sheet_name_str, "color": "#334155", "size": "xs", "weight": "regular", "flex": 8, "wrap": True, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "CLASSIFICATION", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4, "align": "start"},
                        {"type": "text", "text": folder_name_str, "color": "#334155", "size": "xs", "weight": "regular", "flex": 8, "wrap": True, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "action": {
                        "type": "datetimepicker",
                        "data": f"action=edit_date_picker&sheet={sheet_name_str}&row={row_num}",
                        "mode": "date",
                        "initial": initial_date
                    }, "contents": [
                        {"type": "text", "text": "TRANSACTION DATE", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4, "align": "start"},
                        {"type": "text", "text": formatted_date_str, "color": "#334155", "size": "xs", "weight": "regular", "flex": 8, "wrap": True, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "action": {
                        "type": "postback",
                        "data": f"action=edit_field&sheet={sheet_name_str}&row={row_num}&field=ผู้ส่ง/ร้านค้า&display=ผู้ขาย/ร้านค้า",
                        "displayText": "ฉันต้องการแก้ไขผู้ขาย/ร้านค้า"
                    }, "contents": [
                        {"type": "text", "text": "VENDOR / MERCHANT", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4, "align": "start"},
                        {"type": "text", "text": vendor_str, "color": "#334155", "size": "xs", "weight": "regular", "flex": 8, "wrap": True, "align": "end"}
                    ]},
                    {"type": "separator", "color": "#F1F5F9", "margin": "md"},
                    {"type": "box", "layout": "vertical", "backgroundColor": "#F8FAFC", "cornerRadius": "8px", "paddingAll": "10px", "margin": "xs", "action": {
                        "type": "postback",
                        "data": f"action=edit_field&sheet={sheet_name_str}&row={row_num}&field=บันทึกช่วยจำ&display=รายละเอียดบันทึกช่วยจำ",
                        "displayText": "ฉันต้องการแก้ไขรายละเอียด"
                    }, "contents": [
                        {"type": "text", "text": "MEMO", "color": "#64748B", "size": "xxs", "weight": "bold"},
                        {"type": "text", "text": memo_str, "color": "#334155", "size": "xs", "wrap": True, "margin": "xs"}
                    ]}
                ]
            }
        ]

    if mismatch_detected and warning_banner:
        body_contents.insert(0, warning_banner)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Build Bubble Structure with theme variables
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": header_bg,
            "paddingAll": "20px",
            "paddingBottom": "16px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": badge_bg,
                            "cornerRadius": "20px",
                            "paddingAll": "4px",
                            "paddingStart": "10px",
                            "paddingEnd": "10px",
                            "contents": [
                                {"type": "text", "text": badge_label, "size": "xxs", "color": badge_text_color, "weight": "bold"}
                            ]
                        },
                        {"type": "filler"}
                    ]
                },
                {
                    "type": "text",
                    "text": title_text,
                    "weight": "bold",
                    "size": "xxl",
                    "color": "#0F172A",
                    "margin": "md",
                    "wrap": True,
                    "action": {
                        "type": "postback",
                        "data": (
                            f"action=edit_field&sheet={sheet_name_str}&row={row_num}&field=ชื่อ (ไทย)&display=ชื่อ (ไทย)"
                            if sheet_name_str == "บัตรประชาชน"
                            else f"action=edit_field&sheet={sheet_name_str}&row={row_num}&field=รายการ&display=รายการ"
                            if sheet_name_str == "สเตตเมนต์"
                            else f"action=edit_field&sheet={sheet_name_str}&row={row_num}&field=จำนวนเงินสุทธิ&display=ยอดเงินสุทธิ"
                        ),
                        "displayText": (
                            "ฉันต้องการแก้ไขชื่อบนบัตรประชาชน"
                            if sheet_name_str == "บัตรประชาชน"
                            else "ฉันต้องการแก้ไขรายการสเตตเมนต์"
                            if sheet_name_str == "สเตตเมนต์"
                            else "ฉันต้องการแก้ไขยอดเงินสุทธิ"
                        )
                    }
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "sm",
                    "contents": [
                        {"type": "text", "text": subtitle_text, "size": "xs", "color": accent_color, "weight": "bold", "flex": 0},
                        {"type": "text", "text": f"  ·  {formatted_date_str}", "size": "xs", "color": "#64748B", "flex": 1, "wrap": False}
                    ]
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": body_bg,
            "paddingAll": "20px",
            "paddingTop": "12px",
            "contents": body_contents
        }
    }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Dynamically build footer with unified styles (Minimal Slate)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    flat_buttons = []
    footer_bg = "#FFFFFF"
    btn_color = "#F1F5F9"

    if file_link and str(file_link).startswith("http"):
        flat_buttons.append({
            "type": "button",
            "style": "secondary",
            "color": btn_color,
            "height": "sm",
            "action": {
                "type": "uri",
                "label": "ดูเอกสาร",
                "uri": str(file_link)
            }
        })
    if sheet_url and str(sheet_url).startswith("http"):
        flat_buttons.append({
            "type": "button",
            "style": "secondary",
            "color": btn_color,
            "height": "sm",
            "action": {
                "type": "uri",
                "label": "เปิดบัญชี",
                "uri": str(sheet_url)
            }
        })
    if edit_data_postback:
        base_url = "http://localhost:5005"
        try:
            webhook_url = database.get_app_setting("LINE_WEBHOOK_URL", "")
            if webhook_url and webhook_url.startswith("http"):
                if "/api/line/webhook" in webhook_url:
                    base_url = webhook_url.split("/api/line/webhook")[0]
                else:
                    from urllib.parse import urlparse
                    parsed = urlparse(webhook_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass

        if "localhost" in base_url or "127.0.0.1" in base_url or not base_url.startswith("http"):
            try:
                from flask import request
                forwarded_host = request.headers.get('X-Forwarded-Host')
                forwarded_proto = request.headers.get('X-Forwarded-Proto', 'https')
                if forwarded_host and "localhost" not in forwarded_host and "127.0.0.1" not in forwarded_host:
                    base_url = f"{forwarded_proto}://{forwarded_host}"
                else:
                    host = request.headers.get('Host')
                    if host and "localhost" not in host and "127.0.0.1" not in host:
                        scheme = request.scheme or "https"
                        base_url = f"{scheme}://{host}"
                    else:
                        url_root = request.url_root.rstrip('/')
                        if "localhost" not in url_root and "127.0.0.1" not in url_root:
                            base_url = url_root
            except Exception:
                pass

        if "localhost" in base_url or "127.0.0.1" in base_url:
            import os
            env_url = os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL")
            if env_url:
                base_url = env_url.rstrip('/')

        import urllib.parse
        encoded_sheet = urllib.parse.quote(sheet_name_str)
        web_edit_url = f"{base_url}/edit_expense_form?sheet={encoded_sheet}&row={row_num}"
        if org_id:
            web_edit_url += f"&org_id={org_id}"
        if username:
            encoded_user = urllib.parse.quote(str(username))
            web_edit_url += f"&user={encoded_user}"

        flat_buttons.append({
            "type": "button",
            "style": "secondary",
            "color": btn_color,
            "height": "sm",
            "action": {
                "type": "uri",
                "label": "แก้ไขเว็บ",
                "uri": web_edit_url
            }
        })
        flat_buttons.append({
            "type": "button",
            "style": "secondary",
            "color": btn_color,
            "height": "sm",
            "action": {
                "type": "postback",
                "label": "แก้ไขแชต",
                "data": str(edit_data_postback)
            }
        })

        move_btn_label = "ย้ายหมวดหมู่"
        move_btn_color = "#0d9488" # Teal Green
        if mismatch_detected:
            move_btn_label = "ย้ายหมวดหมู่ (แนะนำ)"
            move_btn_color = "#E11D48" # Raspberry Crimson

        flat_buttons.append({
            "type": "button",
            "style": "primary",
            "color": move_btn_color,
            "height": "sm",
            "action": {
                "type": "postback",
                "label": move_btn_label,
                "data": f"action=choose_new_sheet&sheet={sheet_name_str}&row={row_num}",
                "displayText": "ฉันต้องการย้ายประเภทเอกสาร"
            }
        })

    footer_contents = []
    # Group flat_buttons into rows of 2
    for i in range(0, len(flat_buttons), 2):
        row_buttons = flat_buttons[i:i+2]
        footer_contents.append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": row_buttons
        })

    if footer_contents:
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": footer_bg,
            "spacing": "sm",
            "paddingAll": "20px",
            "paddingTop": "0px",
            "paddingBottom": "20px",
            "contents": footer_contents
        }

    return clean_flex_payload(bubble)


def create_links_flex_bubble(sheet_url, drive_url):
    """Creates a beautiful, premium emerald-themed Flex card for links with zero emojis."""
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#F8FAFC",
            "paddingAll": "20px",
            "paddingBottom": "16px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#F1F5F9",
                            "cornerRadius": "20px",
                            "paddingAll": "4px",
                            "paddingStart": "10px",
                            "paddingEnd": "10px",
                            "contents": [
                                {"type": "text", "text": "WORKSPACE", "size": "xxs", "color": "#64748B", "weight": "bold"}
                            ]
                        },
                        {"type": "filler"}
                    ]
                },
                {
                    "type": "text",
                    "text": "ลิงก์ระบบบัญชีและเอกสาร",
                    "weight": "bold",
                    "size": "md",
                    "color": "#0F172A",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": "พี่สามารถเข้าถึงช่องทางต่าง ๆ ได้ผ่านปุ่มด้านล่างนี้ค่ะ",
                    "size": "xs",
                    "color": "#64748B",
                    "margin": "xs"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px",
            "paddingTop": "12px",
            "spacing": "md",
            "contents": [
                {
                    "type": "separator",
                    "color": "#F1F5F9"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "เปิด Google Sheets (บัญชี)",
                                "uri": sheet_url
                            },
                            "style": "secondary",
                            "color": "#F1F5F9",
                            "height": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "เปิด Google Drive (โฟลเดอร์เก็บไฟล์)",
                                "uri": drive_url
                            },
                            "style": "secondary",
                            "color": "#F1F5F9",
                            "height": "sm"
                        }
                    ]
                }
            ]
        }
    }
    return clean_flex_payload(bubble)


def _get_item_flex_block(idx, r, folder_name, base_url, org_id=None, username=None):
    """Generates an ultra-premium, compact item metadata block with zero emojis and high-end design."""
    status = r.get("status", "success")
    name = r.get("name", "ไฟล์")
    sheet_name = r.get("sheet", "ทั่วไป")
    row_num = r.get("row", 1)
    file_link = r.get("link", "#")
    
    sheet_name_str = str(sheet_name)
    
    # Format amount beautifully
    ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
    net_amt = ext.get('net_amount')
    try:
        val_clean = str(net_amt).replace(",", "").strip()
        val_float = float(val_clean)
        amt_str = f"{val_float:,.2f} THB"
    except:
        amt_str = f"{net_amt} THB" if net_amt and net_amt != "-" else "-"

    if amt_str.endswith(".00"):
        amt_str = amt_str[:-3]
    if amt_str.endswith(".00 THB"):
        amt_str = amt_str.replace(".00 THB", " THB")

    import urllib.parse
    encoded_sheet = urllib.parse.quote(sheet_name_str)
    web_edit_url = f"{base_url}/edit_expense_form?sheet={encoded_sheet}&row={row_num}"
    if org_id:
        web_edit_url += f"&org_id={org_id}"
    if username:
        encoded_user = urllib.parse.quote(str(username))
        web_edit_url += f"&user={encoded_user}"
    
    status_label = f"RECORD {idx:02d}"
    status_color = "#475569" if status == "success" else "#E11D48"
    
    block_contents = []
    
    # Display: strip extension, show basename cleanly
    import os as _os
    base_name = _os.path.splitext(name)[0]  # remove .jpg / .pdf etc.
    display_name = base_name[:22] + "…" if len(base_name) > 22 else base_name
    
    block_contents.append({
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": status_label,
                "weight": "bold",
                "size": "xxs",
                "color": status_color,
                "flex": 3
            },
            {
                "type": "text",
                "text": display_name,
                "size": "xxs",
                "color": "#0F172A",
                "weight": "bold",
                "flex": 9,
                "wrap": True,
                "maxLines": 2,
                "align": "end"
            }
        ]
    })
    
    block_contents.append({
        "type": "box",
        "layout": "horizontal",
        "margin": "xs",
        "contents": [
            {
                "type": "text",
                "text": "AMOUNT / TARGET" if status == "success" else "STATUS",
                "size": "xxs",
                "color": "#64748B",
                "weight": "bold",
                "flex": 4
            },
            {
                "type": "text",
                "text": f"{amt_str} to {sheet_name_str}" if status == "success" else "ซ้ำซ้อน",
                "size": "xs",
                "color": "#334155" if status == "success" else "#E11D48",
                "weight": "regular",
                "flex": 8,
                "align": "end"
            }
        ]
    })
    
    links = []
    has_file = False
    if file_link and str(file_link).startswith("http"):
        has_file = True

    if has_file:
        # We have three links. Let's make them flex 1, start / center / end
        links.append({
            "type": "text",
            "text": "ดูเอกสารจริง",
            "size": "xxs",
            "color": "#475569",
            "weight": "bold",
            "decoration": "underline",
            "align": "start",
            "flex": 1,
            "action": {
                "type": "uri",
                "label": "ดูไฟล์",
                "uri": str(file_link)
            }
        })
        
        links.append({
            "type": "text",
            "text": "ย้ายประเภท",
            "size": "xxs",
            "color": "#475569",
            "weight": "bold",
            "decoration": "underline",
            "align": "center",
            "flex": 1,
            "action": {
                "type": "postback",
                "label": "ย้ายประเภท",
                "data": f"action=choose_new_sheet&sheet={sheet_name_str}&row={row_num}",
                "displayText": "ฉันต้องการย้ายประเภทเอกสาร"
            }
        })
        
        links.append({
            "type": "text",
            "text": "แก้ไขข้อมูล",
            "size": "xxs",
            "color": "#475569",
            "weight": "bold",
            "decoration": "underline",
            "align": "end",
            "flex": 1,
            "action": {
                "type": "uri",
                "label": "แก้ไข",
                "uri": web_edit_url
            }
        })
    else:
        # We only have two links. Let's make them start and end
        links.append({
            "type": "text",
            "text": "ย้ายประเภท",
            "size": "xxs",
            "color": "#475569",
            "weight": "bold",
            "decoration": "underline",
            "align": "start",
            "flex": 1,
            "action": {
                "type": "postback",
                "label": "ย้ายประเภท",
                "data": f"action=choose_new_sheet&sheet={sheet_name_str}&row={row_num}",
                "displayText": "ฉันต้องการย้ายประเภทเอกสาร"
            }
        })
        
        links.append({
            "type": "text",
            "text": "แก้ไขข้อมูล",
            "size": "xxs",
            "color": "#475569",
            "weight": "bold",
            "decoration": "underline",
            "align": "end",
            "flex": 1,
            "action": {
                "type": "uri",
                "label": "แก้ไข",
                "uri": web_edit_url
            }
        })
    
    block_contents.append({
        "type": "box",
        "layout": "horizontal",
        "margin": "sm",
        "contents": links
    })
    
    return {
        "type": "box",
        "layout": "vertical",
        "contents": block_contents
    }


def create_paired_expense_flex_bubble(item1, idx1, item2, idx2, folder_name, base_url, sheet_url, org_id=None, username=None):
    """Creates a beautiful, ultra-minimal paired receipt bubble for carousels with zero emojis."""
    body_contents = []
    
    box1 = _get_item_flex_block(idx1, item1, folder_name, base_url, org_id=org_id, username=username)
    body_contents.append(box1)
    
    if item2:
        body_contents.append({
            "type": "separator",
            "color": "#F1F5F9",
            "margin": "md"
        })
        box2 = _get_item_flex_block(idx2, item2, folder_name, base_url, org_id=org_id, username=username)
        body_contents.append(box2)
        
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#F8FAFC",
            "paddingAll": "16px",
            "paddingBottom": "12px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#F1F5F9",
                            "cornerRadius": "20px",
                            "paddingAll": "4px",
                            "paddingStart": "10px",
                            "paddingEnd": "10px",
                            "contents": [
                                {"type": "text", "text": "BATCH", "size": "xxs", "color": "#64748B", "weight": "bold"}
                            ]
                        },
                        {"type": "filler"}
                    ]
                },
                {
                    "type": "text",
                    "text": "รายละเอียดเอกสารนำส่ง",
                    "weight": "bold",
                    "size": "md",
                    "color": "#0F172A",
                    "margin": "sm"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px",
            "paddingTop": "12px",
            "spacing": "md",
            "contents": body_contents
        }
    }
    
    if sheet_url and sheet_url != "#":
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "16px",
            "paddingTop": "0px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "เปิดบัญชี",
                                "uri": sheet_url
                            },
                            "style": "primary",
                            "color": "#0d9488",
                            "height": "sm"
                        }
                    ]
                }
            ]
        }
        
    return clean_flex_payload(bubble)


def create_duplicate_warning_flex_bubble(sheet_name, row_num, ref_number, net_amount, sheet_url):
    """Creates a premium and highly-compact minimal LINE Flex bubble for duplicate slips with zero emojis."""
    ref_str = str(ref_number) if ref_number else "-"
    
    try:
        val_clean = str(net_amount).replace(",", "").strip()
        val_float = float(val_clean)
        amt_str = f"{val_float:,.2f} THB"
    except:
        amt_str = f"{net_amount} THB" if net_amount and net_amount != "-" else "-"
        
    sheet_name_str = str(sheet_name)
    
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFF1F2",
            "paddingAll": "20px",
            "paddingBottom": "16px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#E11D48",
                            "cornerRadius": "20px",
                            "paddingAll": "4px",
                            "paddingStart": "10px",
                            "paddingEnd": "10px",
                            "contents": [
                                {"type": "text", "text": "DUPLICATE", "size": "xxs", "color": "#FFFFFF", "weight": "bold"}
                            ]
                        },
                        {"type": "filler"}
                    ]
                },
                {
                    "type": "text",
                    "text": amt_str,
                    "weight": "bold",
                    "size": "xxl",
                    "color": "#0F172A",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "ระบบตรวจพบรายการซ้ำซ้อน",
                    "size": "xs",
                    "color": "#E11D48",
                    "margin": "xs"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px",
            "paddingTop": "12px",
            "contents": [
                {
                    "type": "separator",
                    "color": "#F1F5F9"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "margin": "lg",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "TRANSACTION ID", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4, "align": "start"},
                                {"type": "text", "text": ref_str, "color": "#334155", "size": "xs", "weight": "regular", "flex": 8, "wrap": True, "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "EXISTING RECORD", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4, "align": "start"},
                                {"type": "text", "text": f"{sheet_name_str} แถวที่ {row_num}", "color": "#334155", "size": "xs", "weight": "regular", "flex": 8, "wrap": True, "align": "end"}
                            ]
                        },
                        {
                            "type": "separator",
                            "color": "#F1F5F9",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "ระบบตรวจสอบพบว่าหลักฐานการโอนเงินนี้ได้รับการบันทึกไว้ในบัญชีเรียบร้อยแล้ว เพื่อความถูกต้องทางบัญชีและป้องกันรายการซ้ำซ้อน ระบบจึงเว้นการบันทึกรายการนี้ให้ค่ะ",
                            "color": "#64748B",
                            "size": "xs",
                            "wrap": True,
                            "margin": "xs"
                        }
                    ]
                }
            ]
        }
    }
    
    if sheet_url and sheet_url != "#":
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "16px",
            "paddingTop": "0px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "เปิดบัญชี",
                                "uri": sheet_url
                            },
                            "style": "secondary",
                            "color": "#F1F5F9",
                            "height": "sm"
                        }
                    ]
                }
            ]
        }
        
    return clean_flex_payload(bubble)


def create_batch_summary_flex_bubble(uploaded_results, folder_name):
    """Creates an ultra-premium elegant batch process summary bubble with zero emojis."""
    total_val = 0.0
    success_count = 0
    duplicate_count = 0
    items_contents = []
    
    for idx, r in enumerate(uploaded_results[:10]):
        status = r.get("status")
        name = r.get("name", "ไฟล์")
        ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
        net_amt = ext.get('net_amount')
        
        parsed_amt = 0.0
        if net_amt is not None and net_amt != "-":
            try:
                parsed_amt = float(str(net_amt).replace(",", "").strip())
            except ValueError:
                pass
                
        if status == "success":
            success_count += 1
            total_val += parsed_amt
            amt_display = f"{parsed_amt:,.2f} THB" if parsed_amt > 0 else "-"
        else:
            duplicate_count += 1
            amt_display = "รายการซ้ำซ้อน"
            
        if amt_display.endswith(".00 THB"):
            amt_display = amt_display.replace(".00 THB", " THB")

        items_contents.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "xs",
            "contents": [
                {
                    "type": "text",
                    "text": f"{idx+1:02d}. {name[:24]}",
                    "size": "xs",
                    "color": "#0F172A",
                    "flex": 7,
                    "wrap": False
                },
                {
                    "type": "text",
                    "text": amt_display,
                    "size": "xs",
                    "color": "#0F172A" if status == "success" else "#E11D48",
                    "weight": "bold" if status == "success" else "regular",
                    "flex": 5,
                    "align": "end"
                }
            ]
        })
        
    if len(uploaded_results) > 10:
        items_contents.append({
            "type": "text",
            "text": f"+ {len(uploaded_results) - 10} รายการเพิ่มเติม...",
            "size": "xxs",
            "color": "#64748B",
            "margin": "sm",
            "align": "center"
        })
        
    sheet_id = google_manager.spreadsheet_id
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else "#"
    
    folder_url = "https://drive.google.com"
    try:
        subfolders = google_manager.list_subfolders()
        for sf in subfolders:
            if sf['name'].lower() == folder_name.lower():
                folder_url = f"https://drive.google.com/drive/folders/{sf['id']}"
                break
    except:
        pass
        
    total_str = f"{total_val:,.2f} THB"
    if total_str.endswith(".00 THB"):
        total_str = total_str.replace(".00 THB", " THB")
        
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#F8FAFC",
            "paddingAll": "20px",
            "paddingBottom": "16px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#F1F5F9",
                            "cornerRadius": "20px",
                            "paddingAll": "4px",
                            "paddingStart": "10px",
                            "paddingEnd": "10px",
                            "contents": [
                                {"type": "text", "text": "COMPLETED", "size": "xxs", "color": "#64748B", "weight": "bold"}
                            ]
                        },
                        {"type": "filler"}
                    ]
                },
                {
                    "type": "text",
                    "text": "ประมวลผลไฟล์นำส่งสำเร็จ",
                    "weight": "bold",
                    "size": "md",
                    "color": "#0F172A",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"{success_count} รายการ  ·  {duplicate_count} ซ้ำ",
                    "size": "xs",
                    "color": "#64748B",
                    "margin": "xs"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px",
            "paddingTop": "12px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "flex": 6,
                            "backgroundColor": "#F8FAFC",
                            "cornerRadius": "8px",
                            "paddingAll": "12px",
                            "contents": [
                                {"type": "text", "text": "TOTAL VALUE", "color": "#475569", "size": "xxs", "weight": "bold"},
                                {"type": "text", "text": total_str, "color": "#0F172A", "size": "md", "weight": "bold", "margin": "xs"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "flex": 6,
                            "backgroundColor": "#F8FAFC",
                            "cornerRadius": "8px",
                            "paddingAll": "12px",
                            "contents": [
                                {"type": "text", "text": "RECORDS", "color": "#64748B", "size": "xxs", "weight": "bold"},
                                {"type": "text", "text": f"{success_count} บันทึก  {duplicate_count} ซ้ำ", "color": "#0F172A", "size": "sm", "weight": "bold", "margin": "xs"}
                            ]
                        }
                    ]
                },
                {
                    "type": "separator",
                    "color": "#F1F5F9",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "margin": "md",
                    "contents": items_contents
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "16px",
            "paddingTop": "0px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "เปิดบัญชี",
                                "uri": sheet_url
                            },
                            "style": "secondary",
                            "color": "#F1F5F9",
                            "height": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "โฟลเดอร์ Drive",
                                "uri": folder_url
                            },
                            "style": "secondary",
                            "color": "#F1F5F9",
                            "height": "sm"
                        }
                    ]
                }
            ]
        }
    }
    
    return clean_flex_payload(bubble)

def send_line_push_notification(target_username, title, text, fields=None):
    """Sends a one-to-one message to a specific user via LINE."""
    line_id = database.get_line_id_by_username(target_username)
    if not line_id: return
    
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    if fields:
        flex_contents = create_line_flex_bubble(title, "การแจ้งเตือนส่วนตัว", fields, color="#E67E22")
        msg = {"type": "flex", "altText": f"แจ้งเตือน: {title}", "contents": flex_contents}
    else:
        msg = {"type": "text", "text": f"🔔 {title}\n{text}"}
        
    try:
        requests.post(url, headers=headers, json={"to": line_id, "messages": [msg]}, timeout=10)
    except Exception as e:
        logger.error(f"❌ LINE Push Error: {e}")

# --- LINE Configuration & Settings ---
LINE_CONFIG_FILE = BASE_DIR / "line_config.json"

def get_line_config():
    if os.path.exists(LINE_CONFIG_FILE):
        try:
            with open(LINE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {
        "channel_access_token": os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""),
        "channel_secret": os.environ.get("LINE_CHANNEL_SECRET", ""),
        "greeting_message": "สวัสดีค่ะ! ยินดีต้อนรับสู่บริการของเรา มีอะไรให้น้องพั้นช่วยไหมคะ?",
        "ai_auto_responder_enabled": False
    }

def save_line_config(config):
    with open(LINE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = config.get("channel_access_token", "")
    os.environ["LINE_CHANNEL_SECRET"] = config.get("channel_secret", "")

@app.route("/api/admin/line/settings", methods=["GET", "POST"])
@admin_required
def admin_line_settings():
    if request.method == "POST":
        data = request.json
        config = get_line_config()
        config.update(data)
        save_line_config(config)
        return jsonify({"ok": True, "message": "บันทึกการตั้งค่า LINE เรียบร้อยแล้วค่ะ"})
    return jsonify({"ok": True, "config": get_line_config()})

@app.route("/api/org/line/register-group", methods=["POST"])
@login_required
def register_line_group_api():
    data = request.get_json(force=True) or {}
    group_id = (data.get("group_id") or "").strip()
    group_name = (data.get("group_name") or "").strip()
    if not group_id:
        return jsonify({"ok": False, "error": "กรุณาระบุ Group ID"}), 400
    org_id = get_current_org_id()
    username = session.get("user")
    database.register_line_group(group_id, org_id, username, group_name or None)
    return jsonify({"ok": True, "group_id": group_id, "org_id": org_id})

@app.route("/api/org/line/groups", methods=["GET"])
@login_required
def list_line_groups_api():
    org_id = get_current_org_id()
    groups = database.get_line_groups_for_org(org_id)
    return jsonify({"ok": True, "groups": groups})

@app.route("/api/org/line/groups/<group_id>", methods=["DELETE"])
@login_required
def delete_line_group_api(group_id):
    org_id = get_current_org_id()
    import sqlite3 as _sq
    conn = _sq.connect(database.DB_PATH)
    conn.execute("DELETE FROM line_group_mappings WHERE group_id=? AND org_id=?", (group_id, org_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/line-groups")
@login_required
def admin_line_groups_page():
    return render_template("admin_line_groups.html")

@app.route("/api/admin/line/broadcast-history")
@admin_required
def get_broadcast_history():
    try:
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM line_broadcast_history ORDER BY timestamp DESC LIMIT 50")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify({"ok": True, "history": rows})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# --- LINE Webhook & Processing ---
LINE_FOLDER_CACHE = {}
_line_batch_timer = {}

def get_line_sender_name(group_id, sender_id):
    """Fetch user display name from LINE API using group context or user context."""
    if not sender_id or sender_id == "unknown":
        return "-"
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not token:
        return "-"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Try fetching from group member profile
    if group_id:
        try:
            url = f"https://api.line.me/v2/bot/group/{group_id}/member/{sender_id}"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                return res.json().get("displayName", "-")
        except Exception as e:
            logger.warning(f"Error fetching group member name: {e}")
            
    # 2. Try fetching from standard user profile
    try:
        url = f"https://api.line.me/v2/bot/profile/{sender_id}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json().get("displayName", "-")
    except Exception as e:
        logger.warning(f"Error fetching user profile name: {e}")
        
    return "-"

def show_loading_animation(chat_id, loading_seconds=20):
    """Show LINE loading/typing animation (max 60s)."""
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not token or not chat_id:
        return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    try:
        requests.post(
            "https://api.line.me/v2/bot/chat/loading/start",
            headers=headers,
            json={"chatId": chat_id, "loadingSeconds": loading_seconds},
            timeout=5
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to show loading animation: {e}")

def reply_to_line(reply_token, message, quick_reply=None, sticker_data=None):
    """Send a reply message to LINE using the reply token."""
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not token or not reply_token:
        logger.warning("⚠️ reply_to_line: missing token or reply_token")
        return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    if isinstance(message, dict) and "type" in message:
        messages = [dict(message)]
    elif isinstance(message, list):
        messages = list(message)
    else:
        messages = [{"type": "text", "text": str(message)}]

    if sticker_data:
        messages.append({"type": "sticker", "packageId": sticker_data["packageId"], "stickerId": sticker_data["stickerId"]})

    if quick_reply and messages:
        messages[-1] = dict(messages[-1])
        messages[-1]["quickReply"] = quick_reply
    try:
        res = requests.post(
            "https://api.line.me/v2/bot/message/reply",
            headers=headers,
            json={"replyToken": reply_token, "messages": messages},
            timeout=10
        )
        if res.status_code != 200:
            logger.error(f"❌ reply_to_line failed: {res.status_code} {res.text}")
    except Exception as e:
        logger.error(f"❌ reply_to_line exception: {e}")

def broadcast_line_announcement(title, text, fields=None):
    """Sends a push notification to all linked users via Flex Message."""
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not token: return False
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    flex_contents = {
        "type": "bubble",
        "body": {
            "type": "box", "layout": "vertical", "contents": [
                { "type": "text", "text": "ประกาศจากน้องพั้นค่ะ", "size": "xs", "color": "#059669", "weight": "bold", "margin": "none" },
                { "type": "text", "text": text, "wrap": True, "margin": "md", "size": "sm", "lineSpacing": "6px", "color": "#334155" }
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical", "contents": [
                { "type": "text", "text": "เปิดแอปเพื่อดูรายละเอียดเพิ่มเติม", "size": "xxs", "color": "#94a3b8", "align": "center" }
            ]
        }
    }
    try:
        res = requests.post(url, headers=headers, json={"messages": [{"type": "flex", "altText": title, "contents": flex_contents}]}, timeout=20)
        if res.status_code == 200:
            logger.info("✅ [LINE Broadcast] Sent successfully!")
            return True
        else:
            logger.error(f"❌ [LINE Broadcast] Failed: {res.text}")
            return False
    except Exception as e:
        logger.error(f"❌ [LINE Broadcast] Exception: {e}")
        return False

def get_folder_flex_message(user_id=None, uploader_id=None, pending_id=None):
    """Generates a Flex Message for selecting target folder from Drive."""
    try:
        mgr = google_manager
        
        # Resolve context from LINE user/group IDs
        line_uid = uploader_id or (user_id if user_id and user_id.startswith("U") else None)
        u_name = None
        org_id = None
        
        if line_uid:
            u_name = database.get_username_by_line_id(line_uid)
            org_id = database.get_org_id_by_line_user(line_uid)
            
        if not org_id and user_id:
            if user_id.startswith("C") or user_id.startswith("R"):
                org_id = database.get_org_id_by_line_group(user_id)
                
        if not org_id:
            org_id = 1
            
        mgr.set_context(username=u_name, org_id=org_id)

        folders = mgr.list_subfolders()
        if not folders: return None
        
        buttons = []
        for f in folders[:10]:
            folder_name = f['name']
            action_data = f"action=set_folder&id={f['id']}&name={folder_name}"
            if uploader_id:
                action_data += f"&uploader_id={uploader_id}"
            if pending_id:
                action_data += f"&pending_id={pending_id}"
                
            buttons.append({
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#f1f5f9",
                "cornerRadius": "md",
                "paddingAll": "sm",
                "justifyContent": "center",
                "alignItems": "center",
                "action": {
                    "type": "postback",
                    "label": folder_name[:20],
                    "data": action_data,
                    "displayText": f"เก็บลงโฟลเดอร์ {folder_name}"[:300]
                },
                "contents": [
                    {
                        "type": "text",
                        "text": folder_name,
                        "size": "xs",
                        "wrap": True,
                        "align": "center",
                        "color": "#334155",
                        "weight": "bold"
                    }
                ]
            })
            
        horizontal_boxes = []
        for i in range(0, len(buttons), 2):
            row_buttons = buttons[i:i+2]
            horizontal_boxes.append({
                "type": "box",
                "layout": "horizontal",
                "contents": row_buttons,
                "spacing": "sm",
                "margin": "sm" if i > 0 else "none"
            })
            
        return {
            "type": "flex",
            "altText": "เลือกโฟลเดอร์ที่จะจัดเก็บ",
            "contents": {
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "เลือกโฟลเดอร์",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#334155"
                        },
                        {
                            "type": "text",
                            "text": "กรุณาเลือกโฟลเดอร์เพื่อจัดเก็บไฟล์ค่ะ",
                            "size": "sm",
                            "color": "#64748b",
                            "wrap": True,
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#f8fafc"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": horizontal_boxes,
                    "spacing": "none"
                }
            }
        }
    except Exception as e:
        logger.error(f"Folder Flex Error: {e}")
        return None

def process_line_event(event_data):
    """Main event dispatcher for LINE Webhook"""
    try:
        reply_token = event_data.get("replyToken")
        source_obj = event_data.get("source", {})
        user_id = source_obj.get("userId", "unknown")
        group_id = source_obj.get("groupId") if source_obj.get("type") == "group" else None
        dest_id = group_id if group_id else user_id
        
        # Enforce context right at the start of handling line event!
        _org_id = get_line_org_id(user_id, group_id)
        if _org_id is None:
            _org_id = 1
            
        owner_username = None
        if group_id:
            owner_username = database.get_group_owner(group_id)
        if owner_username:
            username = owner_username
        else:
            username = database.get_username_by_line_id(user_id)
            
        google_manager.set_context(username=username, org_id=_org_id)
        
        # 1. Text message
        if event_data.get('type') == 'message' and event_data['message'].get('type') == 'text':
            user_text = event_data['message'].get('text', '')
            
            # Check if this is an edit response
            session_data = RedisManager.get_active_edit_session(user_id)
            if session_data:
                RedisManager.clear_active_edit_session(user_id)
                # Check if session expired (e.g., > 10 minutes)
                if time.time() - session_data.get("timestamp", 0) > 600:
                    reply_to_line(reply_token, "หมดเวลาการแก้ไขแล้วค่ะพี่ รบกวนกดปุ่มแก้ไขจากรูปอีกครั้งนะคะ")
                    return "OK", 200
                
                # Apply edit
                sheet = session_data["sheet"]
                row = session_data["row"]
                field = session_data["field"]
                ok, err = google_manager.update_expense(sheet, row, field, user_text)
                if ok:
                    reply_to_line(reply_token, f"แก้ไขเรียบร้อยค่ะ:\n{session_data['display']} = '{user_text}'")
                else:
                    reply_to_line(reply_token, f"เกิดข้อผิดพลาด: {err}")
                return "OK", 200

            process_line_command(user_text, user_id, reply_token, group_id=group_id)
            return

        # 2. Handler for IMAGE/FILE/VIDEO/AUDIO (Google Drive)
        msg_type = event_data.get('message', {}).get('type')
        msg_obj = event_data.get('message', {})
        if event_data.get('type') == 'message' and msg_type in ["image", "file", "video", "audio"]:
            message_id = msg_obj.get("id")
            logger.info(f"Received media {msg_type} (ID: {message_id}) from {user_id} in {dest_id}")
            
            # --- 🛑 Pre-check Billing Limit BEFORE downloading or processing ---
            _org_id = get_line_org_id(user_id, group_id)
            if _org_id:
                _ok, _used, _limit = billing.check_usage_allowed(_org_id, "expense_count")
                if not _ok:
                    now = time.time()
                    cache_key = f"limit_warn_{_org_id}_{user_id}"
                    _cache = getattr(app, "_limit_warn_cache", {})
                    if now - _cache.get(cache_key, 0) > 10:
                        _cache[cache_key] = now
                        app._limit_warn_cache = _cache
                        msg = f"❌ ใช้โควต้าบันทึกบิลครบ {_limit} รายการในเดือนนี้แล้วค่ะ\nหากต้องการเพิ่มจำนวน กรุณาอัปเกรดแพ็กเกจนะคะ"
                        reply_to_line(reply_token, msg)
                    return "OK", 200

            # --- 🚀 Per-User Batching: แยกตะกร้าคิวเป็นของแต่ละคน ไม่ปนกันในห้องแชท ---
            batch_key = f"{dest_id}_{user_id}"
            
            if batch_key not in _line_batch_timer:
                _line_batch_timer[batch_key] = {"files": [], "timer": None}
            
            # Store specific metadata for each file in the batch, tracking individual sender
            _line_batch_timer[batch_key]["files"].append({
                "message_id": message_id, 
                "msg_type": msg_type,
                "file_name": msg_obj.get("fileName"),
                "sender_id": user_id
            })
            
            if _line_batch_timer[batch_key]["timer"]:
                _line_batch_timer[batch_key]["timer"].cancel()
                
            def handle_upload_background(b_key, did, uid, reply_tok):
                batch_data = _line_batch_timer.pop(b_key, {})
                batch = batch_data.get("files", [])
                if not batch: return
                
                token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
                pending_for_dest = []
                
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                def _download_file(file_item):
                    f_id = file_item["message_id"]
                    f_type = file_item["msg_type"]
                    s_id = file_item.get("sender_id", "unknown")
                    try:
                        res = requests.get(f"https://api-data.line.me/v2/bot/message/{f_id}/content", 
                                           headers={"Authorization": f"Bearer {token}"}, timeout=60)
                        if res.status_code == 200:
                            original_name = file_item.get("file_name") or f"line_upload_{f_id}"
                            mimetype = "application/octet-stream"
                            if f_type == "image": mimetype = "image/jpeg"
                            elif f_type == "video": mimetype = "video/mp4"
                            elif f_type == "audio": mimetype = "audio/x-m4a"
                            elif f_type == "file" and original_name.lower().endswith(".pdf"):
                                mimetype = "application/pdf"
                            
                            return {
                                "content": res.content,
                                "mimetype": mimetype,
                                "name": original_name,
                                "type": f_type,
                                "msg_id": f_id,
                                "sender_id": s_id
                            }
                    except Exception as e:
                        logger.error(f"❌ Failed to fetch media {f_id}: {e}")
                    return None

                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(_download_file, item) for item in batch]
                    for future in as_completed(futures):
                        res = future.result()
                        if res:
                            pending_for_dest.append(res)

                if pending_for_dest:
                    # Generate unique session ID per upload batch to prevent overwrites
                    pending_id = f"pending_{uuid.uuid4().hex}"
                    RedisManager.set_pending_files(pending_id, pending_for_dest)
                    
                    # Check for folder bypass (if group mapped with default folder)
                    mapping = database.get_group_mapping(did) if did.startswith("C") else None
                    if mapping and mapping.get("default_folder_id"):
                        f_id = mapping.get("default_folder_id")
                        f_name = mapping.get("default_folder_name") or "ใบเสร็จ/ใบกำกับภาษี"
                        logger.info(f"Bypassing folder selection for group {did}. Uploading to: {f_name} ({f_id})")
                        show_loading_animation(did)
                        threading.Thread(target=process_pending_uploads, args=(pending_id, did, f_id, f_name, reply_tok), daemon=True).start()
                    else:
                        folder_flex = get_folder_flex_message(did, uploader_id=uid, pending_id=pending_id)
                        
                        sender_name = get_line_sender_name(did if did.startswith("C") else None, uid)
                        name_prefix = f"พี่ {sender_name} คะ " if sender_name and sender_name != "Unknown" else "พี่คะ "
                        
                        if len(pending_for_dest) == 1:
                            f_name = pending_for_dest[0]['name']
                            msg = f"📥 {name_prefix}น้องพั้นได้รับไฟล์ '{f_name}' แล้วนะคะ\nกำลังอัปโหลดให้อยู่ค่ะ~ เลือกโฟลเดอร์ที่จะเก็บด้วยนะคะ:"
                        else:
                            msg = f"📥 {name_prefix}น้องพั้นได้รับไฟล์ {len(pending_for_dest)} รายการแล้วนะคะ\nกำลังอัปโหลดให้อยู่ค่ะ~ เลือกโฟลเดอร์ที่จะเก็บด้วยนะคะ:"
                            
                        if folder_flex:
                            reply_to_line(reply_tok, [{"type": "text", "text": msg}, folder_flex])
                        else:
                            reply_to_line(reply_tok, msg)
                else:
                    reply_to_line(reply_tok, "❌ น้องพั้นดึงข้อมูลไฟล์ไม่สำเร็จค่ะ")

            try:
                timer = threading.Timer(3.0, handle_upload_background, args=(batch_key, dest_id, user_id, reply_token))
                _line_batch_timer[batch_key]["timer"] = timer
                timer.start()
            except Exception:
                _line_batch_timer.pop(batch_key, None)
                raise
            return

        # 3. Handler for bot joining a group
        if event_data.get('type') == 'join':
            g_id = source_obj.get("groupId")
            if g_id:
                flex_welcome = {
                    "type": "flex",
                    "altText": "น้องพั้นยินดีต้อนรับค่ะ 💖",
                    "contents": {
                        "type": "bubble",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#6366f1",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🎉 ยินดีต้อนรับ",
                                    "weight": "bold",
                                    "size": "xl",
                                    "color": "#ffffff"
                                }
                            ]
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "น้องพั้นพร้อมช่วยวิเคราะห์และจัดเก็บเอกสารอัตโนมัติให้กลุ่มนี้แล้วค่ะ!",
                                    "wrap": True,
                                    "size": "sm",
                                    "color": "#666666"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "lg",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "box",
                                            "layout": "baseline",
                                            "spacing": "sm",
                                            "contents": [
                                                {"type": "text", "text": "📌", "size": "sm", "flex": 1},
                                                {"type": "text", "text": "รหัสกลุ่ม (Group ID) ของคุณคือ:", "wrap": True, "size": "sm", "color": "#111111", "weight": "bold", "flex": 9}
                                            ]
                                        },
                                        {
                                            "type": "text",
                                            "text": g_id,
                                            "wrap": True,
                                            "size": "xs",
                                            "color": "#ec4899",
                                            "margin": "md",
                                            "align": "center",
                                            "weight": "bold"
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "color": "#6366f1",
                                    "action": {
                                        "type": "uri",
                                        "label": "ไปตั้งค่า Web Portal",
                                        "uri": "https://openchat.sbs/dashboard"
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "secondary",
                                    "action": {
                                        "type": "message",
                                        "label": "ดูรหัสกลุ่ม",
                                        "text": "รหัสกลุ่ม"
                                    }
                                }
                            ]
                        }
                    }
                }
                reply_to_line(reply_token, flex_welcome)
            return

        # 4. Handler for POSTBACK
        if event_data.get('type') == 'postback':
            data = event_data.get('postback', {}).get('data', '')
            parsed = dict(urllib.parse.parse_qsl(data))
            if parsed.get('action') == 'set_folder':
                f_id = parsed.get('id')
                f_name = parsed.get('name')
                if f_id:
                    LINE_FOLDER_CACHE[dest_id] = f_id
                    
                    uploader_id = parsed.get('uploader_id')
                    target_user = uploader_id if uploader_id else user_id
                    batch_key = f"{dest_id}_{target_user}"
                    # Use pending_id from postback if available, fallback to batch_key for old buttons
                    pending_id = parsed.get('pending_id') or batch_key
                    # Process pending files immediately after folder selection
                    if RedisManager.get_json(f"pending_files:{pending_id}"):
                        RedisManager.set_json(f"upload_lock:{pending_id}", True, expire=30)
                        show_loading_animation(dest_id)
                        threading.Thread(target=process_pending_uploads, args=(pending_id, dest_id, f_id, f_name, reply_token), daemon=True).start()
                    else:
                        if RedisManager.get_json(f"upload_lock:{pending_id}"):
                            reply_to_line(reply_token, "น้องพั้นกำลังประมวลผลไฟล์ให้อยู่ค่ะ กรุณารอสักครู่นะคะ")
                        else:
                            reply_to_line(reply_token, "ปุ่มนี้ถูกใช้งานไปแล้วค่ะ หากต้องการเก็บไฟล์ รบกวนส่งรูปภาพเข้ามาใหม่อีกครั้งนะคะ")
            elif parsed.get('action') == 'edit_prompt':
                sheet = parsed.get('sheet')
                row = parsed.get('row')
                
                edit_fields = [
                    {"label": "ยอดเงินสุทธิ", "field": "จำนวนเงินสุทธิ", "display": "ยอดเงินสุทธิ"},
                    {"label": "วันที่ในเอกสาร", "field": "วันที่ในเอกสาร", "display": "วันที่ในเอกสาร"},
                    {"label": "ผู้ส่ง/ร้านค้า", "field": "ผู้ส่ง/ร้านค้า", "display": "ผู้ส่ง/ร้านค้า"},
                    {"label": "เลขที่อ้างอิง", "field": "เลขที่อ้างอิง", "display": "เลขที่อ้างอิง"},
                ]
                if sheet == "บัตรประชาชน":
                    edit_fields = [
                        {"label": "เลขบัตรประชาชน", "field": "เลขบัตรประชาชน", "display": "เลขบัตรประชาชน"},
                        {"label": "ชื่อ (ไทย)", "field": "ชื่อ (ไทย)", "display": "ชื่อ (ไทย)"},
                        {"label": "นามสกุล (ไทย)", "field": "นามสกุล (ไทย)", "display": "นามสกุล (ไทย)"},
                    ]
                
                items = []
                for f in edit_fields:
                    items.append({
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": f["label"][:20],
                            "data": f"action=edit_field&sheet={sheet}&row={row}&field={f['field']}&display={f['display']}",
                            "displayText": f"ฉันต้องการแก้ไข{f['display']}"
                        }
                    })
                
                reply_to_line(reply_token, f"พี่ต้องการแก้ไขข้อมูลในชีต '{sheet}' แถวที่ {row} ส่วนไหนดีคะ? เลือกได้เลยค่ะ:", quick_reply={"items": items})
            elif parsed.get('action') == 'edit_field':
                sheet = parsed.get('sheet')
                row = parsed.get('row')
                field = parsed.get('field')
                display = parsed.get('display')
                
                RedisManager.set_active_edit_session(user_id, {
                    "sheet": sheet,
                    "row": int(row),
                    "field": field,
                    "display": display,
                    "timestamp": time.time()
                })
                reply_to_line(reply_token, f"💬 พี่ต้องการเปลี่ยน '{display}' เป็นค่าอะไรดีคะ?\nพิมพ์ค่าใหม่ส่งกลับมาให้น้องพั้นได้เลยค่ะ พั้นกำลังรออยู่นะคะ 👇")
            elif parsed.get('action') == 'edit_date_picker':
                sheet = parsed.get('sheet')
                row = parsed.get('row')
                params = event_data.get('postback', {}).get('params', {})
                selected_date = params.get('date')
                if selected_date:
                    try:
                        dt = datetime.strptime(selected_date, "%Y-%m-%d")
                        formatted_val = dt.strftime("%d/%m/%Y")
                    except Exception:
                        formatted_val = selected_date
                    
                    date_col = google_manager.get_date_header_name(sheet)
                    ok, err = google_manager.update_expense(sheet, int(row), date_col, formatted_val)
                    if ok:
                        reply_to_line(reply_token, f"✅ แก้ไขวันที่เรียบร้อยแล้วค่ะพี่!\n\n📊 ชีต: '{sheet}' แถวที่ {row}\n📅 เปลี่ยนเป็น: '{formatted_val}'\n\nพั้นอัปเดตและกระทบยอดบัญชีใหม่ให้อัตโนมัติเรียบร้อยค่ะ ✨")
                    else:
                        reply_to_line(reply_token, f"❌ เกิดข้อผิดพลาดในการแก้ไขวันที่: {err}")
                else:
                    reply_to_line(reply_token, "❌ ไม่พบวันที่ที่เลือกค่ะ")
            elif parsed.get('action') == 'choose_new_sheet':
                from_sheet = parsed.get('sheet')
                row = parsed.get('row')
                
                try:
                    spreadsheet = google_manager.sheets_service.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
                    sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', []) if s['properties']['title'] not in ["Sheet1", "ชีต1", "แดชบอร์ด", "Dashboard"]]
                except Exception:
                    sheet_titles = ["สลิปโอนเงิน", "ใบเสร็จ/ใบกำกับภาษี", "ใบเสนอราคา", "ทั่วไป"]
                
                items = []
                for title in sheet_titles:
                    items.append({
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": title[:20],
                            "data": f"action=move_row_sheet&from_sheet={from_sheet}&row={row}&to_sheet={title}",
                            "displayText": f"ย้ายไปยังชีต: {title}"
                        }
                    })
                
                reply_to_line(reply_token, f"พี่ต้องการย้ายรายการค่าใช้จ่ายนี้ (ชีต '{from_sheet}' แถวที่ {row}) ไปยังประเภท/ชีตใดคะ? จิ้มเลือกได้เลยค่ะ:", quick_reply={"items": items})
            elif parsed.get('action') == 'move_row_sheet':
                from_sheet = parsed.get('from_sheet')
                row = parsed.get('row')
                to_sheet = parsed.get('to_sheet')
                
                if from_sheet == to_sheet:
                    reply_to_line(reply_token, f"ℹ️ รายการนี้อยู่ในชีต '{to_sheet}' อยู่แล้วค่ะพี่! 😊")
                else:
                    ok, err = google_manager.move_row_between_sheets(from_sheet, int(row), to_sheet)
                    if ok:
                        reply_to_line(reply_token, f"✅ ย้ายข้อมูลสำเร็จแล้วค่ะพี่!\n\n📂 ย้ายจาก: '{from_sheet}'\n➡️ ไปยังชีตใหม่: '{to_sheet}'\n\nน้องพั้นทำการลบแถวเดิมและย้ายไปต่อชีตใหม่ พร้อมกระทบยอดบัญชีเรียบร้อยค่ะ ✨💖")
                    else:
                        reply_to_line(reply_token, f"❌ เกิดข้อผิดพลาดในการย้ายชีต: {err}")
    except Exception as e:
        logger.error(f"Event processing failed: {e}")
    finally:
        google_manager.clear_context()

@safe_thread_target
@db_task_tracker("process_pending_uploads")
def process_pending_uploads(b_key, did, folder_id, folder_name, reply_tok):


    """Processes files that were waiting for folder selection."""
    mgr = google_manager
    # Note: GoogleWorkspaceManager is a Singleton. Individual user manager is not supported in this version.

    # Resolve org for billing (group or user)
    _upload_org_id = database.get_org_id_by_line_group(did) if (did.startswith("C") or did.startswith("R")) else database.get_org_id_by_line_user(did)
    if _upload_org_id is None:
        _upload_org_id = 1  # fallback for legacy/single-tenant deployments
    
    files = RedisManager.pop_pending_files(b_key)
    if not files: return
    
    # Enforce context for this background thread!
    sender_id = files[0].get("sender_id")
    u_name = database.get_username_by_line_id(sender_id) if sender_id else None
    google_manager.set_context(username=u_name, org_id=_upload_org_id)
    
    # --- 🛑 Pre-check Billing Limit Batch Truncation ---
    _exp_ok, _exp_used, _exp_limit = billing.check_usage_allowed(_upload_org_id, "expense_count")
    uploaded_results = []
    if _exp_limit != -1:
        available = max(0, _exp_limit - _exp_used)
        if len(files) > available:
            rejected_files = files[available:]
            files = files[:available]
            for f in rejected_files:
                uploaded_results.append({"status": "limit_reached", "name": f.get("name", "Unknown"), "limit": _exp_limit})
    
    # Let user know we're working on it — push ONLY (never use reply_tok here).
    if files:
        processing_msg = f"กำลังวิเคราะห์และจัดเก็บ {len(files)} ไฟล์ลง '{folder_name}' ⏳ (อาจใช้เวลาสักครู่)"
        token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        try:
            requests.post("https://api.line.me/v2/bot/message/push", headers=headers,
                          json={"to": did, "messages": [{"type": "text", "text": processing_msg}]}, timeout=10)
        except Exception:
            pass  # Silently skip processing message if push fails (quota or network error)
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def _process_single_upload(item):
        try:
            original_name = item["name"]
            real_original_name = original_name
            mimetype = item["mimetype"]
            content = item["content"]
            f_type = item["type"]

            # --- Guard: reject empty file content before wasting any API quota ---
            if not content:
                logger.warning(f"⚠️ Empty file content for '{original_name}', skipping.")
                return {"status": "empty_file", "name": original_name}

            # --- 🛑 Check billing BEFORE Drive upload (don't waste Drive/Sheets quota) ---
            _exp_ok, _exp_used, _exp_limit = billing.check_and_increment(_upload_org_id, "expense_count")
            if not _exp_ok:
                return {"status": "limit_reached", "name": original_name, "limit": _exp_limit}

            # --- 🚀 AI Smart Scan ---
            analysis = None
            if (f_type in ["image", "file"] and mimetype in ["image/jpeg", "application/pdf", "image/png"]) or f_type == "audio":
                try:
                    analysis = ai_providers.analyze_media_contents(content, mimetype)
                    if analysis and analysis.get("smart_name"):
                        ext = os.path.splitext(original_name)[1]
                        original_name = analysis["smart_name"]
                        if not original_name.endswith(ext): original_name += ext
                except Exception as e:
                    import traceback
                    print(f"🚨 CRITICAL: Media analysis failed in app_server: {e}\n{traceback.format_exc()}", flush=True)
                    analysis = None

            sender_id = item.get("sender_id")
            u_name = database.get_username_by_line_id(sender_id) if sender_id else None

            # Upload
            link, upload_err = mgr.upload_file(content, original_name, mimetype, folder_id=folder_id, org_id=_upload_org_id, username=u_name)
            if not link:
                logger.error(f"❌ Drive upload failed for '{original_name}': {upload_err}")
                return {"status": "upload_failed", "name": original_name, "error": str(upload_err)}

            # --- 🛠️ Data Sanitization for Google Sheets (Prevent Column Sprouting) ---
            raw_ext = analysis.get("extracted_data", {}) if analysis else {}
            sanitized_ext = raw_ext.copy()
            if "date" not in sanitized_ext or not sanitized_ext["date"]:
                sanitized_ext["date"] = datetime.now().strftime("%d/%m/%Y")
            sanitized_ext["category"] = folder_name
            for field in ["time", "sender", "receiver", "memo", "ref_number"]:
                if field not in sanitized_ext: sanitized_ext[field] = "-"

            sender_name = get_line_sender_name(did if (did.startswith("C") or did.startswith("R")) else None, sender_id)

            log_data = {
                "file_link": link,
                "summary": analysis.get("summary", f"Auto-upload: {original_name}") if analysis else f"Auto-upload: {original_name}",
                "original_filename": real_original_name,
                "extracted_data": sanitized_ext,
                "line_sender_name": sender_name
            }

            log_res = mgr.log_expense(log_data, org_id=_upload_org_id, username=u_name)

            # Log to local database for Dashboard stats (regardless of Sheets result)
            try:
                amt = sanitized_ext.get("net_amount", 0)
                if not amt or amt == "-": amt = 0
                try:
                    if isinstance(amt, str):
                        amt = float(amt.replace(',', '').replace('฿', '').strip())
                    else:
                        amt = float(amt)
                except:
                    amt = 0.0
                database.add_drive_log(
                    filename=real_original_name,
                    category=sanitized_ext.get("category", "General"),
                    amount=amt,
                    doc_date=sanitized_ext.get("date"),
                    summary=analysis.get("summary") if analysis else f"Auto-upload: {real_original_name}",
                    file_link=link,
                    user_id=sender_id
                )
            except Exception as dbe:
                logger.error(f"❌ Database Log Error: {dbe}")

            if log_res and log_res.get("error") == "duplicate":
                return {
                    "status": "duplicate",
                    "name": original_name,
                    "link": link,
                    "analysis": analysis,
                    "sheet": log_res.get("sheet"),
                    "row": log_res.get("row"),
                    "ref_number": log_res.get("ref_number")
                }

            if not log_res or not log_res.get("ok"):
                logger.warning(f"⚠️ Sheets log failed for '{original_name}' (Drive OK). log_res={log_res}")

            # Always return success if Drive upload succeeded — Sheets is best-effort
            return {
                "status": "success",
                "name": original_name,
                "link": link,
                "analysis": analysis,
                "sheet": log_res.get("sheet") if log_res else "ทั่วไป",
                "row": log_res.get("row") if log_res else 0
            }

        except Exception as e:
            logger.error(f"Pending upload failed: {e}")
        return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_process_single_upload, item) for item in files]
        for future in as_completed(futures):
            res = future.result()
            if res:
                uploaded_results.append(res)

    _upload_fails = [r for r in uploaded_results if r and r.get("status") == "upload_failed"]
    uploaded_results = [r for r in uploaded_results if r and r.get("status") != "upload_failed"]
    if _upload_fails:
        _fail_names = ", ".join(r["name"] for r in _upload_fails)
        _fail_errors = "; ".join(r.get("error", "unknown") for r in _upload_fails)
        _fail_msg = (
            f"❌ อัปโหลดไฟล์ไม่สำเร็จค่ะ\n"
            f"ไฟล์: {_fail_names}\n"
            f"สาเหตุ: {_fail_errors}\n\n"
            f"กรุณาตรวจสอบการเชื่อมต่อ Google Drive ของระบบค่ะ"
        )
        try:
            _tok = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
            requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                json={"to": did, "messages": [{"type": "text", "text": _fail_msg}]},
                timeout=10,
            )
        except Exception:
            pass

    _limit_hits = [r for r in uploaded_results if r and r.get("status") == "limit_reached"]
    uploaded_results = [r for r in uploaded_results if r and r.get("status") != "limit_reached"]
    if _limit_hits:
        _lim = _limit_hits[0].get("limit", 30)
        _blocked_names = ", ".join(r["name"] for r in _limit_hits)
        _limit_msg = (
            f"❌ ใช้โควต้าบันทึกค่าใช้จ่ายครบ {_lim} รายการแล้วในเดือนนี้ค่ะ\n"
            f"ไฟล์ที่ไม่ได้บันทึก: {_blocked_names}\n\n"
            f"อัปเกรด Plan เพื่อใช้งานต่อได้เลยนะคะ"
        )
        try:
            _tok = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
            requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                json={"to": did, "messages": [{"type": "text", "text": _limit_msg}]},
                timeout=10,
            )
        except Exception:
            pass

    if uploaded_results:
        token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        push_url = "https://api.line.me/v2/bot/message/push"
        reply_url = "https://api.line.me/v2/bot/message/reply"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        _flex_reply_used = [False]  # mutable flag

        def _send_messages(msgs, label=""):
            """Try push; if 429 quota exceeded, fall back to reply token (free, expires in 30s)."""
            res = requests.post(push_url, headers=headers, json={"to": did, "messages": msgs}, timeout=20)
            logger.info(f"\U0001f4e4 [LINE Push Flex{' ' + label if label else ''}] Status: {res.status_code}, Response: {res.text}")
            if res.status_code != 200 and reply_tok and not _flex_reply_used[0]:
                logger.warning("\u26a0\ufe0f Push quota exceeded (429). Falling back to reply token for Flex card.")
                _flex_reply_used[0] = True
                reply_msgs = msgs[:5]  # reply API supports max 5 messages
                r2 = requests.post(reply_url, headers=headers,
                                   json={"replyToken": reply_tok, "messages": reply_msgs}, timeout=20)
                logger.info(f"\U0001f4e4 [LINE Reply Flex Fallback] Status: {r2.status_code}, Response: {r2.text}")
                if r2.status_code != 200:
                    # Reply token expired or invalid — send best-effort plain-text summary
                    logger.warning(f"\u26a0\ufe0f Reply also failed ({r2.status_code}). Sending plain-text summary as last resort.")
                    summary_lines = []
                    for m in msgs:
                        if m.get("type") == "flex":
                            alt = m.get("altText", "")
                            if alt:
                                summary_lines.append(alt)
                    if summary_lines:
                        summary_text = "\n".join(summary_lines)
                        try:
                            requests.post(push_url, headers=headers,
                                          json={"to": did, "messages": [{"type": "text", "text": summary_text}]}, timeout=10)
                        except Exception:
                            pass


        if len(uploaded_results) >= 2:

            # Generate Base URL
            base_url = "http://localhost:5005"
            try:
                webhook_url = database.get_app_setting("LINE_WEBHOOK_URL", "")
                if webhook_url and webhook_url.startswith("http"):
                    if "/api/line/webhook" in webhook_url:
                        base_url = webhook_url.split("/api/line/webhook")[0]
                    else:
                        from urllib.parse import urlparse
                        parsed = urlparse(webhook_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                pass

            if "localhost" in base_url or "127.0.0.1" in base_url or not base_url.startswith("http"):
                try:
                    from flask import request
                    forwarded_host = request.headers.get('X-Forwarded-Host')
                    forwarded_proto = request.headers.get('X-Forwarded-Proto', 'https')
                    if forwarded_host and "localhost" not in forwarded_host and "127.0.0.1" not in forwarded_host:
                        base_url = f"{forwarded_proto}://{forwarded_host}"
                    else:
                        host = request.headers.get('Host')
                        if host and "localhost" not in host and "127.0.0.1" not in host:
                            scheme = request.scheme or "https"
                            base_url = f"{scheme}://{host}"
                        else:
                            url_root = request.url_root.rstrip('/')
                            if "localhost" not in url_root and "127.0.0.1" not in url_root:
                                base_url = url_root
                except Exception:
                    pass

            if "localhost" in base_url or "127.0.0.1" in base_url:
                env_url = os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL")
                if env_url:
                    base_url = env_url.rstrip('/')

            sheet_id = mgr.spreadsheet_id
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else "#"

            summary_bubble = create_batch_summary_flex_bubble(uploaded_results, folder_name)
            
            paired_bubbles = []
            carousel_results = uploaded_results[:20]
            for i in range(0, len(carousel_results), 2):
                item1 = carousel_results[i]
                idx1 = i + 1
                item2 = carousel_results[i+1] if i+1 < len(carousel_results) else None
                idx2 = i + 2 if item2 else None
                
                bubble = create_paired_expense_flex_bubble(
                    item1=item1,
                    idx1=idx1,
                    item2=item2,
                    idx2=idx2,
                    folder_name=folder_name,
                    base_url=base_url,
                    sheet_url=sheet_url,
                    org_id=_upload_org_id,
                    username=u_name
                )
                paired_bubbles.append(bubble)

            messages = [
                {
                    "type": "flex",
                    "altText": "📊 สรุปรายการอัปโหลดแบบกลุ่ม",
                    "contents": summary_bubble
                }
            ]
            
            if paired_bubbles:
                messages.append({
                    "type": "flex",
                    "altText": "📂 รายละเอียดรายการใบเสร็จ",
                    "contents": {
                        "type": "carousel",
                        "contents": paired_bubbles
                    }
                })

            # Full quick reply shortcuts attached to batch summary card
            _sheet_qr = f"https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}/edit" if mgr.spreadsheet_id else "https://sheets.google.com"
            _p_id2 = os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")
            _drive_qr = f"https://drive.google.com/drive/folders/{_p_id2}" if _p_id2 else "https://drive.google.com"
            quick_reply_batch = {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "ส่งสลิปเพิ่ม", "text": "ส่งสลิประบบจะจัดเก็บให้อัตโนมัติค่ะ"}},
                    {"type": "action", "action": {"type": "message", "label": "สรุปรายจ่าย", "text": "สรุปรายจ่ายวันนี้"}},
                    {"type": "action", "action": {"type": "message", "label": "สรุปยอดวันนี้", "text": "สรุปยอดวันนี้"}},
                    {"type": "action", "action": {"type": "message", "label": "กระทบยอด", "text": "กระทบยอด"}},
                    {"type": "action", "action": {"type": "message", "label": "หาไฟล์", "text": "ค้นหา "}},
                    {"type": "action", "action": {"type": "uri", "label": "ดูบัญชี", "uri": _sheet_qr}},
                    {"type": "action", "action": {"type": "uri", "label": "Google Drive", "uri": _drive_qr}}
                ]
            }
            messages[-1]["quickReply"] = quick_reply_batch


            try:
                _send_messages(messages, "Batch")
            except Exception as e:
                logger.error(f"❌ [LINE Push Flex Batch] HTTP Error: {e}")

        else:
            messages = []
            for r in uploaded_results:
                sheet_name = r.get("sheet", "ทั่วไป")
                row_num = r.get("row", 1)
                file_link = r.get("link", "#")
                
                sheet_id = mgr.spreadsheet_id
                sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else "#"
                
                status = r.get("status", "success")
                
                if status == "duplicate":
                    ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
                    net_amt = ext.get('net_amount')
                    if not net_amt or net_amt in [0, '0', 'None', '']:
                        net_amt = "-"
                    
                    ref_num = r.get("ref_number", "-")
                    
                    flex_bubble = create_duplicate_warning_flex_bubble(
                        sheet_name=sheet_name,
                        row_num=row_num,
                        ref_number=ref_num,
                        net_amount=net_amt,
                        sheet_url=sheet_url
                    )
                    
                    messages.append({
                        "type": "flex",
                        "altText": "⚠️ ตรวจพบการอัปโหลดสลิปซ้ำซ้อน",
                        "contents": flex_bubble
                    })
                else:
                    ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
                    net_amt = ext.get('net_amount')
                    if not net_amt or net_amt in [0, '0', 'None', '']:
                        net_amt = "-"
                    
                    date_val = ext.get('date') or datetime.now().strftime("%d/%m/%Y")
                    memo_val = ext.get('memo') or ext.get('summary') or r.get('name')
                    
                    vendor_val = ext.get('receiver') or ext.get('sender') or ext.get('merchant_name') or ext.get('supplier_name') or "-"
                    
                    edit_data_postback = f"action=edit_prompt&sheet={sheet_name}&row={row_num}"
                    
                    flex_bubble = create_expense_flex_bubble(
                        sheet_name=sheet_name,
                        folder_name=folder_name,
                        net_amount=net_amt,
                        date_str=date_val,
                        memo=memo_val,
                        vendor=vendor_val,
                        file_link=file_link,
                        sheet_url=sheet_url,
                        edit_data_postback=edit_data_postback,
                        raw_result=r,
                        org_id=_upload_org_id,
                        username=u_name
                    )
                    
                    messages.append({
                        "type": "flex",
                        "altText": "✅ บันทึกค่าใช้จ่ายสำเร็จ",
                        "contents": flex_bubble
                    })
                
                # Limit to 5 messages per push as per LINE API rules
                if len(messages) == 5:
                    try:
                        _send_messages(messages, "Batch")
                    except Exception as e:
                        logger.error(f"❌ [LINE Push Flex] Batch HTTP Error: {e}")
                    messages = []
                    
            if messages:
                # Full quick reply shortcuts on the last message
                _sheet_url_qr = f"https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}/edit" if mgr.spreadsheet_id else "https://sheets.google.com"
                _p_id = os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")
                _drive_url = f"https://drive.google.com/drive/folders/{_p_id}" if _p_id else "https://drive.google.com"
                quick_reply = {
                    "items": [
                        {"type": "action", "action": {"type": "message", "label": "ส่งสลิปเพิ่ม", "text": "ส่งสลิประบบจะจัดเก็บให้อัตโนมัติค่ะ"}},
                        {"type": "action", "action": {"type": "message", "label": "สรุปรายจ่าย", "text": "สรุปรายจ่ายวันนี้"}},
                        {"type": "action", "action": {"type": "message", "label": "สรุปยอดวันนี้", "text": "สรุปยอดวันนี้"}},
                        {"type": "action", "action": {"type": "message", "label": "กระทบยอด", "text": "กระทบยอด"}},
                        {"type": "action", "action": {"type": "message", "label": "หาไฟล์", "text": "ค้นหา "}},
                        {"type": "action", "action": {"type": "uri", "label": "ดูบัญชี", "uri": _sheet_url_qr}},
                        {"type": "action", "action": {"type": "uri", "label": "Google Drive", "uri": _drive_url}}
                    ]
                }
                messages[-1]["quickReply"] = quick_reply
                try:
                    _send_messages(messages)
                except Exception as e:
                    logger.error(f"❌ [LINE Push Flex] HTTP Error: {e}")

    else:
        token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        push_url = "https://api.line.me/v2/bot/message/push"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        try:
            requests.post(push_url, headers=headers,
                          json={"to": did, "messages": [{"type": "text", "text": "❌ ขออภัยค่ะ พั้นไม่สามารถจัดเก็บไฟล์ได้ในขณะนี้"}]}, timeout=10)
        except Exception as push_err:
            logger.error(f"❌ [LINE Push Error] Failed to send failure message: {push_err}")
            
    google_manager.clear_context()

def verify_line_signature(body_bytes, signature):
    """Verifies the LINE webhook signature using LINE_CHANNEL_SECRET."""
    channel_secret = os.environ.get("LINE_CHANNEL_SECRET", "").strip()
    if not channel_secret:
        logger.warning("⚠️ LINE_CHANNEL_SECRET is not set. Bypassing verification.")
        return True
    hash_obj = hmac.new(channel_secret.encode('utf-8'), body_bytes, hashlib.sha256).digest()
    calc_signature = base64.b64encode(hash_obj).decode('utf-8')
    return calc_signature == signature

@app.route("/api/line/webhook", methods=['POST'])
def line_webhook():
    """Primary LINE Webhook Entry Point"""
    signature = request.headers.get('X-Line-Signature')
    # Get raw bytes for signature verification
    body_bytes = request.get_data()
    
    if not signature or not verify_line_signature(body_bytes, signature):
        return abort(400)
    
    # After reading get_data(), we can still get json if it's parsed
    data = request.get_json()
    events = data.get('events', []) if data else []
    
    for event in events:
        threading.Thread(target=process_line_event, args=(event,), daemon=True).start()
    return 'OK'


def get_line_org_id(user_id: str, group_id: str = None) -> int | None:
    """Resolve which org a LINE message belongs to (group > user fallback)."""
    if group_id:
        org_id = database.get_org_id_by_line_group(group_id)
        if org_id:
            return org_id
    return database.get_org_id_by_line_user(user_id)


def process_line_command(text, user_id, reply_token, group_id=None):
    """Ultimate Command Processor with AI integration"""

    import secrets
    import time

    _base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
    _text_pre  = text.lower().strip()

    # ── /groupid ทำงานก่อน org check เสมอ (ใช้ได้แม้ยังไม่ลงทะเบียน) ─────────
    if group_id and any(k in _text_pre for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
        _qr = {"items": [
            {"type": "action", "action": {"type": "uri", "label": "ลงทะเบียนกลุ่ม", "uri": f"{_base_url}/admin/line-groups"}},
            {"type": "action", "action": {"type": "uri", "label": "สมัครบริการ",     "uri": f"{_base_url}/signup"}},
        ]}
        reply_to_line(reply_token,
            f"สวัสดีค่ะพี่! รหัสกลุ่มนี้ (Group ID) คือ:\n\n"
            f"{group_id}\n\n"
            f"นำรหัสไปลงทะเบียนที่:\n{_base_url}/admin/line-groups\n\n"
            "แล้วน้องพั้นจะเริ่มทำงานให้ได้เลยค่ะ!",
            quick_reply=_qr)
        return
    elif not group_id and any(k in _text_pre for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
        reply_to_line(reply_token, "คำสั่งนี้ใช้ได้เฉพาะในกลุ่ม LINE ค่ะ กรุณาเพิ่มน้องพั้นเข้ากลุ่มก่อนนะคะ")
        return

    # ── Resolve org (multi-tenant) ────────────────────────────────────────────
    _line_org_id = get_line_org_id(user_id, group_id)
    if _line_org_id is None:
        _unreg_qr = {"items": [
            {"type": "action", "action": {"type": "message", "label": "รหัสกลุ่ม",   "text": "/groupid"}},
            {"type": "action", "action": {"type": "uri",    "label": "สมัครบริการ",  "uri": f"{_base_url}/signup"}},
            {"type": "action", "action": {"type": "uri",    "label": "ลงทะเบียนกลุ่ม", "uri": f"{_base_url}/admin/line-groups"}},
        ]}
        reply_to_line(reply_token,
            f"สวัสดีค่ะ! น้องพั้นยินดีต้อนรับ\n\n"
            f"กลุ่มนี้ยังไม่ได้เชื่อมกับระบบค่ะ ทำตาม 3 ขั้นนี้ได้เลย:\n\n"
            f"1. สมัครที่ {_base_url}/signup\n"
            f"2. พิมพ์ /groupid เพื่อดูรหัสกลุ่มนี้\n"
            f"3. ลงทะเบียนที่ {_base_url}/admin/line-groups\n\n"
            f"กดปุ่มด้านล่างเพื่อเริ่มได้เลยค่ะ",
            quick_reply=_unreg_qr)
        return

    # ── Billing gate: LINE Bot ต้อง Pro ขึ้นไป ──────────────────────────────
    if not billing.has_feature(_line_org_id, "line_bot"):
        reply_to_line(reply_token,
            "LINE Bot ใช้ได้เฉพาะ Plan Pro หรือสูงกว่าค่ะ\n"
            "อัปเกรดได้ที่ https://openchat.sbs/pricing")
        return

    mgr = google_manager
    owner_username = None
    if group_id:
        owner_username = database.get_group_owner(group_id)
    if owner_username:
        username = owner_username
    else:
        username = database.get_username_by_line_id(user_id)
    
    # 📝 Handle Active Edit Session
    session_data = RedisManager.get_active_edit_session(user_id)
    if session_data:
        RedisManager.delete(f"edit_session:{user_id}")
        # Check timeout (5 minutes = 300 seconds)
        if time.time() - session_data["timestamp"] < 300:
            sheet = session_data["sheet"]
            row = session_data["row"]
            field = session_data["field"]
            display = session_data["display"]
            new_value = text.strip()
            
            # Update spreadsheet
            ok, err = mgr.update_expense(sheet, row, field, new_value)
            if ok:
                msg = f"✅ แก้ไขข้อมูลเรียบร้อยแล้วค่ะพี่!\n\n📊 ชีต: '{sheet}' แถวที่ {row}\n✏️ หัวข้อ: '{display}'\n📝 เปลี่ยนเป็น: '{new_value}'\n\nพั้นดำเนินการอัปเดตและกระทบยอดบัญชีใหม่ให้อัตโนมัติเรียบร้อยค่ะ ✨"
                
                # Persistent Quick Reply
                p_id = os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")
                drive_url = f"https://drive.google.com/drive/folders/{p_id}"
                quick_reply = {
                    "items": [{
                        "type": "action",
                        "action": {
                            "type": "uri",
                            "label": "เปิด Google Drive",
                            "uri": drive_url
                        }
                    }]
                }
                if mgr.spreadsheet_id:
                    quick_reply["items"].insert(0, {
                        "type": "action",
                        "action": {
                            "type": "uri",
                            "label": "เปิด Google Sheets",
                            "uri": f"https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}/edit"
                        }
                    })
                reply_to_line(reply_token, msg, quick_reply=quick_reply)
            else:
                reply_to_line(reply_token, f"❌ เกิดข้อผิดพลาดในการแก้ไขข้อมูล: {err}\nพี่ลองพิมพ์รายการที่จะอัปเดตใหม่อีกครั้งนะคะ")
            return

    text_lower = text.lower().strip()
    try:
        with open('scratch/debug_log.txt', 'a', encoding='utf-8') as df:
            df.write(f"Received text: '{text}'\n")
            df.write(f"text_lower: '{text_lower}'\n")
            df.write(f"Match condition: {text_lower.startswith('/link') or 'ผูกบัญชี' in text_lower}\n")
            df.write(f"Username: '{username}'\n")
    except Exception as e:
        pass

    
    # Persistent Quick Reply — shown after every bot text response (max 13 items)
    p_id = os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")
    drive_url = f"https://drive.google.com/drive/folders/{p_id}" if p_id else "https://drive.google.com"
    sheet_url_qr = f"https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}/edit" if mgr.spreadsheet_id else "https://sheets.google.com"

    # Dynamic Quick Replies based on linked status
    quick_reply_items = [
        {"type": "action", "action": {"type": "message", "label": "สรุปรายจ่ายวันนี้", "text": "สรุปรายจ่ายวันนี้"}},
        {"type": "action", "action": {"type": "message", "label": "สรุปยอดวันนี้", "text": "สรุปยอดวันนี้"}},
        {"type": "action", "action": {"type": "message", "label": "เริ่มกระทบยอด", "text": "กระทบยอด"}},
        {"type": "action", "action": {"type": "message", "label": "ค้นหาไฟล์", "text": "ค้นหา "}},
        {"type": "action", "action": {"type": "message", "label": "เลือกโฟลเดอร์", "text": "เลือกโฟลเดอร์"}},
        {"type": "action", "action": {"type": "message", "label": "บันทึกวันลา", "text": "ลางาน"}},
    ]
    
    if not username:
        quick_reply_items.insert(0, {"type": "action", "action": {"type": "message", "label": "ผูกบัญชีระบบ", "text": "ผูกบัญชี"}})
    else:
        quick_reply_items.append({"type": "action", "action": {"type": "message", "label": "ขอลิงก์ระบบ", "text": "ขอลิงก์"}})
        
    quick_reply_items.append({"type": "action", "action": {"type": "uri", "label": "ดู Google Sheet", "uri": sheet_url_qr}})
    quick_reply_items.append({"type": "action", "action": {"type": "uri", "label": "Google Drive", "uri": drive_url}})
    _base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
    quick_reply_items.append({"type": "action", "action": {"type": "uri", "label": "สมัครบริการ", "uri": f"{_base_url}/pricing"}})

    quick_reply = {"items": quick_reply_items[:13]}

    
    try:
        # 0. Handle /groupid or "groupid" or "รหัสกลุ่ม"
        if group_id and any(k in text_lower for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
            _base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
            g_msg = (
                "สวัสดีค่ะพี่! 😊 รหัสกลุ่ม LINE นี้ (Group ID) คือ:\n\n"
                f"👉 {group_id}\n\n"
                f"นำรหัสนี้ไปลงทะเบียนที่:\n{_base_url}/admin/line-groups\n\n"
                "เพื่อให้น้องพั้นรู้ว่ากลุ่มนี้เป็นของใคร และเริ่มใช้งานได้เลยค่ะ! 💖"
            )
            reply_to_line(reply_token, g_msg, quick_reply=quick_reply)
            return

        # 0.1 Handle สมัครบริการ
        if any(k in text_lower for k in ["สมัคร", "สมัครบริการ", "สมัครสมาชิก", "ราคา", "แพลน", "plan", "pricing"]):
            base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
            signup_msg = (
                f"สวัสดีค่ะ! น้องพั้นยินดีแนะนำเลยนะคะ 😊\n\n"
                f"OrgChat AI มี 3 แพลนค่ะ:\n"
                f"• Free — ฟรี (AI 10 ครั้ง, บิล 100 ใบ/เดือน)\n"
                f"• Pro — ฿299/เดือน (ไม่จำกัด + LINE Bot)\n"
                f"• Ultra — ฿599/เดือน (ทีม 10 คน + Export)\n\n"
                f"สมัครได้เลยค่ะพี่ 👉 {base_url}/signup\n"
                f"ดูรายละเอียดเพิ่มเติม: {base_url}/pricing"
            )
            reply_to_line(reply_token, signup_msg, quick_reply=quick_reply)
            return

        # 0.2 Handle วิธีใช้งาน
        if "วิธีใช้" in text_lower or "help" == text_lower:
            help_msg = (
                "💡 **วิธีใช้งานน้องพั้นแบบง่ายๆ ค่ะ:**\n\n"
                "1. 📸 **ส่งรูปบิล/สลิป:** พี่แค่ถ่ายรูปหรือส่งรูปบิลเข้ามาในแชท น้องพั้นจะอ่านข้อมูลและสรุปยอดให้ทันที\n"
                "2. 📁 **เลือกโฟลเดอร์:** พอน้องพั้นสรุปข้อมูลเสร็จ จะมีปุ่มให้พี่เลือกโฟลเดอร์เพื่อจัดเก็บลง Google Drive และบันทึกบัญชีอัตโนมัติค่ะ\n"
                "3. ✏️ **แก้ไขข้อมูล:** ถ้า AI อ่านข้อมูลผิด พี่สามารถกดปุ่ม 'แก้ไข' ที่หน้ารายละเอียดการอัปโหลดได้เลยนะคะ\n"
                "4. 📊 **ดูสรุปยอด:** กดปุ่มด้านล่างหรือพิมพ์ 'สรุปยอดวันนี้' น้องพั้นจะดึงข้อมูลจากชีตมาสรุปให้ทันทีค่ะ!\n\n"
                "สงสัยตรงไหน ทักหาน้องพั้นได้ตลอดเลยนะคะ 💖"
            )
            reply_to_line(reply_token, help_msg, quick_reply=quick_reply)
            return
        elif not group_id and any(k in text_lower for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
            reply_to_line(reply_token, "ℹ️ คำสั่งนี้สามารถใช้ได้เฉพาะในกลุ่มแชท LINE เท่านั้นนะคะพี่ 😊", quick_reply=quick_reply)
            return

        # 1. Account Linking (/link or ผูกบัญชี)
        if text_lower.startswith("/link") or "ผูกบัญชี" in text_lower:
            if not username:
                import secrets
                import time
                token = secrets.token_urlsafe(32)
                PENDING_LINE_LINKS[token] = {
                    "line_user_id": user_id,
                    "timestamp": time.time()
                }
                
                base_url = "http://localhost:5005"
                webhook_url = os.environ.get("ACTIVE_PUBLIC_URL")
                if webhook_url:
                    if "/api/line/webhook" in webhook_url:
                        base_url = webhook_url.split("/api/line/webhook")[0]
                    else:
                        base_url = webhook_url.rstrip('/')
                else:
                    env_url = os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL")
                    if env_url:
                        base_url = env_url.rstrip('/')
                
                magic_url = f"{base_url}/line/link_magic?token={token}"
                
                magic_bubble = create_magic_link_flex_bubble(magic_url)
                reply_to_line(reply_token, {
                    "type": "flex",
                    "altText": "🔗 เชื่อมต่อบัญชี OrgChat AI",
                    "contents": magic_bubble
                }, quick_reply=quick_reply)
            else:
                reply_to_line(reply_token, f"✅ พี่ {username} ผูกบัญชีไว้เรียบร้อยแล้วค่ะ!", quick_reply=quick_reply)
            return

        # 🔗 Workspace Links Request
        if any(k in text_lower for k in ["ขอลิงค์", "ขอลิ้งค์", "ขอลิงก์", "ขอลิ้ง", "ขอลิงค์หน่อย"]):
            sheet_id = mgr.spreadsheet_id
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else "https://sheets.google.com"
            p_id = os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")
            drive_url = f"https://drive.google.com/drive/folders/{p_id}" if p_id else "https://drive.google.com"
            
            links_bubble = create_links_flex_bubble(sheet_url, drive_url)
            reply_to_line(reply_token, {
                "type": "flex",
                "altText": "🔗 ลิงก์ระบบบัญชีและเอกสารของพี่ค่ะ",
                "contents": links_bubble
            }, quick_reply=quick_reply)
            return

        # 2. Expense Reporting
        if any(k in text_lower for k in ["สรุปรายจ่าย", "ยอดรายจ่าย", "รายจ่าย", "วันนี้"]):
            summary = mgr.get_monthly_summary()
            
            # --- 📊 Stunning Donut Chart Generation & Integration ---
            try:
                raw_data = mgr.get_monthly_summary(return_raw=True)
                if isinstance(raw_data, tuple) and len(raw_data) == 3:
                    total_expense, total_count, categories_breakdown = raw_data
                    if total_count > 0 and categories_breakdown:
                        from chart_generator import generate_monthly_expense_chart
                        
                        # Determine base URL dynamically
                        base_url = "http://localhost:5005"
                        webhook_url = os.environ.get("ACTIVE_PUBLIC_URL")
                        if webhook_url:
                            if "/api/line/webhook" in webhook_url:
                                base_url = webhook_url.split("/api/line/webhook")[0]
                            else:
                                base_url = webhook_url.rstrip('/')
                        else:
                            env_url = os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL")
                            if env_url:
                                base_url = env_url.rstrip('/')
                        
                        # Generate the beautiful donut chart
                        chart_filename = generate_monthly_expense_chart(categories_breakdown)
                        chart_url = f"{base_url}/uploads/social_feed/{chart_filename}"
                        
                        # Construct a multi-message response containing both the Flex summary and the chart image!
                        messages = []
                        if isinstance(summary, dict):
                            messages.append(summary)
                        else:
                            messages.append({"type": "text", "text": str(summary)})
                            
                        messages.append({
                            "type": "image",
                            "originalContentUrl": chart_url,
                            "previewImageUrl": chart_url
                        })
                        
                        reply_to_line(reply_token, messages, quick_reply=quick_reply)
                        return
            except Exception as chart_err:
                logger.error(f"⚠️ Failed to generate and attach expense chart: {chart_err}")
                
            reply_to_line(reply_token, summary, quick_reply=quick_reply)
            return

        # 3. Enhanced File Retrieval (Drive + Database Logs)
        if text_lower.startswith(("หาไฟล์", "ค้นหา", "search")):
            query = text.replace("หาไฟล์", "").replace("ค้นหา", "").replace("search", "").strip()
            if not query:
                reply_to_line(reply_token, "พี่ต้องการหาไฟล์อะไรคะ? ระบุชื่อมาได้เลยค่ะ 😊")
                return

            db_logs = database.search_drive_logs(query, limit=5)
            drive_files = []
            if hasattr(google_drive_service, 'search_files'):
                drive_files = google_drive_service.search_files(query)
            
            if drive_files or db_logs:
                resp = f"🔍 น้องพั้นพบไฟล์ที่พี่ต้องการแล้วค่ะ ({len(drive_files) + len(db_logs)} รายการ):\n\n"
                seen = set()
                for log in db_logs:
                    if log.get('file_link'):
                        seen.add(log['file_link'])
                        resp += f"📄 {log['filename']}\n📂 {log.get('category', 'ทั่วไป')}\n🔗 {log['file_link']}\n\n"
                for f in drive_files:
                    if f.get('webViewLink') and f['webViewLink'] not in seen:
                        resp += f"📄 {f['name']}\n🔗 {f['webViewLink']}\n\n"
                reply_to_line(reply_token, resp, quick_reply=quick_reply)
            else:
                reply_to_line(reply_token, f"❌ ไม่พบไฟล์ที่ชื่อ '{query}' เลยค่ะพี่", quick_reply=quick_reply)
            return

        # 4. Background Reconciliation
        if any(k in text_lower for k in ["กระทบยอด", "reconcile"]):
            reply_to_line(reply_token, "⏳ น้องพั้นกำลังเริ่มจับคู่สลิปกับใบกำกับภาษีให้พี่อยู่นะคะ... เมื่อเสร็จแล้วจะแจ้งเตือนไปค่ะ ✨")
            def run_recon():
                try:
                    if hasattr(google_drive_service, 'perform_auto_reconciliation'):
                        google_drive_service.perform_auto_reconciliation(mgr.sheets_service, mgr.spreadsheet_id)
                        push_msg = f"✅ กระทบยอดข้อมูลเสร็จเรียบร้อยแล้วค่ะพี่!\n🌐 https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}"
                    else:
                        push_msg = "⚠️ ระบบกระทบยอดยังไม่พร้อมใช้งานในตอนนี้ค่ะพี่"
                    
                    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
                    requests.post("https://api.line.me/v2/bot/message/push", 
                                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                  json={"to": user_id, "messages": [{"type": "text", "text": push_msg}]}, timeout=10)
                except Exception as e: logger.error(f"Background Recon Error: {e}")
            threading.Thread(target=run_recon).start()
            return

        # 5. Leave Request
        if any(k in text_lower for k in ["ลางาน", "ลาป่วย", "ลากิจ"]):
            leave_type = "ลาป่วย" if "ป่วย" in text_lower else "ลากิจ" if "กิจ" in text_lower else "ลาพักร้อน"
            database.add_leave_request(line_user_id=user_id, username=user_id, leave_type=leave_type, start_date="", end_date="", reason=text)
            reply_to_line(reply_token, f"📝 รับทราบค่ะ! น้องพั้นบันทึกคำ{leave_type}ให้เบื้องต้นแล้วนะคะ พี่อย่าลืมมาแจ้งวันลาที่ชัดเจนด้วยน้า 😊")
            return

        # 6. Folder Selection Manual Command
        if any(k in text_lower for k in ["เลือกโฟลเดอร์", "โฟลเดอร์", "folder"]):
            folder_flex = get_folder_flex_message(group_id or user_id)
            if folder_flex:
                reply_to_line(reply_token, [{"type": "text", "text": "📂 พี่ต้องการให้พั้นเก็บไฟล์ไว้ที่โฟลเดอร์ไหนดีคะ? เลือกได้เลยค่ะ"}, folder_flex])
            else:
                reply_to_line(reply_token, "❌ น้องพั้นหาโฟลเดอร์ใน Drive ไม่เจอเลยค่ะพี่")
            return

        # 6. Default AI Processing (Using Prompt Engineering & RAG)
        if hasattr(ai_providers, 'generate_response'):
            system_prompt = (
                "คุณคือ 'พั้น' (Nong Punch) ผู้ช่วยประจำองค์กรวัย 21 ปี นิสัยน่ารัก สดใส เป็นกันเอง และสุภาพมาก\n"
                "กฎเหล็ก (ต้องทำตาม 100%):\n"
                "1. แทนตัวเองว่า 'น้องพั้น' หรือ 'พั้น' ก็ได้ (สลับกันตามความเหมาะสมให้ดูเป็นธรรมชาติ) และเรียกผู้ใช้ว่า 'พี่' เสมอ\n"
                "2. **ห้ามใช้คำว่า 'ครับ' หรือ 'ครับ/ค่ะ' โดยเด็ดขาด ให้ใช้ 'ค่ะ/นะคะ/ขา' เท่านั้น**\n"
                "3. ตอบให้สั้น กระชับ ได้ใจความที่สุด ห้ามพูดเยอะเกินความจำเป็น\n"
                "4. **จำกัด Emoji: ใส่ได้เพียง 1 ตัวต่อหนึ่งข้อความเท่านั้น (ห้ามเกินเด็ดขาด)**\n"
                "5. เน้นความเป็นธรรมชาติเหมือนคุยกับรุ่นน้องที่ทำงาน สไตล์การพูด: ได้สิ พี่, ว่าไงคะพี่, เรียบร้อยค่ะพี่\n"
                "6. หากไม่พบข้อมูล ให้บอกว่า 'พั้นหาไม่เจอค่ะพี่' อย่างสุภาพ\n"
            )
            try:
                context = ""
                sources = []
                if hasattr(rag_engine, 'retrieve_context'):
                    context, sources = rag_engine.retrieve_context(text, where=None)
                
                if context:
                    system_prompt += f"\n\nContext:\n{context}\n\n(ใช้ข้อมูลนี้ตอบพี่เขาอย่างเป็นธรรมชาติที่สุด)"
                
                _ai_ok, _ai_used, _ai_limit = billing.check_and_increment(_line_org_id, "ai_query_count")
                if not _ai_ok:
                    reply_to_line(reply_token,
                        f"ใช้โควต้า AI ครบ {_ai_limit} ครั้งแล้วในเดือนนี้ค่ะ\n"
                        "อัปเกรด Plan เพื่อใช้งานต่อได้เลยนะคะ https://openchat.sbs/pricing")
                    return

                ai_response = ai_providers.generate_response(question=text, system_prompt=system_prompt)
                reply_to_line(reply_token, ai_response, quick_reply=quick_reply)
            except Exception as e:
                logger.error(f"AI Generation failed: {e}")
                if 'context' in locals() and context:
                    response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ (สำรอง):\n{context[:500]}..."
                elif hasattr(rag_engine, 'retrieve_context'):
                    ctx, _ = rag_engine.retrieve_context(text)
                    response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ (สำรอง):\n{ctx[:500]}..." if ctx else "ขออภัยนะคะ พั้นมีปัญหาในการดึงข้อมูลสักครู่ ลองใหม่อีกครั้งนะคะ"
                else:
                    response = "ขออภัยนะคะ พั้นมีปัญหาในการดึงข้อมูลสักครู่ ลองใหม่อีกครั้งนะคะ"
                reply_to_line(reply_token, response, quick_reply=quick_reply)
        else:
            if hasattr(rag_engine, 'retrieve_context'):
                ctx, _ = rag_engine.retrieve_context(text)
                response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ:\n{ctx[:500]}..." if ctx else "ขออภัยนะคะ ไม่พบข้อมูลที่เกี่ยวข้องค่ะ"
            else:
                response = "ระบบ AI ยังไม่พร้อมใช้งานในขณะนี้ค่ะ"
            reply_to_line(reply_token, response, quick_reply=quick_reply)

    except Exception as e:
        logger.error(f"Command processing failed: {e}")
        reply_to_line(reply_token, "ขออภัยนะคะ เกิดข้อผิดพลาดในการประมวลผลข้อมูล ลองใหม่อีกครั้งนะคะ", quick_reply=quick_reply)



@app.route("/api/admin/line/broadcast", methods=["POST"])
@admin_required
def api_line_broadcast():
    data = request.json
    text = data.get("text", "").strip()
    user = session.get("user", "Unknown")
    if not text:
        return jsonify({"success": False, "error": "กรุณาระบุข้อความประกาศค่ะ"}), 400
    
    def run_broadcast():
        success = broadcast_line_announcement(title="ประกาศจากแอดมิน", text=text)
        logger.info(f"Broadcast from {user}: {text} - {'Success' if success else 'Failed'}")
        
    threading.Thread(target=run_broadcast).start()
    return jsonify({"success": True, "message": "กำลังส่งประกาศในพื้นหลังค่ะพี่!"})

# --- ADMIN & API ROUTES ---


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()  # Clear entire session securely on logout
    return jsonify({"ok": True})

@app.route("/api/me")
def api_me():
    user = session.get("user")
    if user:
        profile = database.get_user_profile(user)
        user_settings = database.get_user_setting(user)
        
        # Determine current active organization and plan
        org_id = get_current_org_id()
        active_plan = billing.get_effective_plan(org_id)
        plan_config = billing.get_plan_config(active_plan)
        plan_name = plan_config.get("name_th", plan_config.get("name", "Free"))
        
        org_name = "Default Organization"
        try:
            import sqlite3
            conn = sqlite3.connect("chat_history.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
            org_row = cursor.fetchone()
            if org_row:
                org_name = org_row["name"]
            conn.close()
        except Exception:
            pass

        return jsonify({
            "ok": True, 
            "user": user, 
            "profile": {
                **profile,
                "role": user_settings.get("role"),
                "can_edit_kb": user_settings.get("can_edit_kb", False),
                "is_active": user_settings.get("is_active", 1),
                "active_plan": active_plan,
                "plan_name": plan_name,
                "org_name": org_name
            }
        })
    return jsonify({"ok": False, "error": "Unauthorized"}), 401

@app.route("/api/profile/update", methods=["POST"])
@login_required
def api_update_profile():
    user = session.get("user")
    display_name = request.form.get("display_name")
    background_url = request.form.get("background_url")
    department = request.form.get("department")
    
    avatar_url = None
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename:
            ext = Path(secure_filename(file.filename)).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                return jsonify({"ok": False, "error": "รองรับเฉพาะไฟล์รูป (.jpg, .png, .webp, .gif)"}), 400
            prof_dir = Path("uploads/profiles")
            prof_dir.mkdir(parents=True, exist_ok=True)
            filename = secure_filename(f"{user}_{file.filename}")
            save_path = prof_dir / filename
            file.save(str(save_path))
            avatar_url = f"/uploads/profiles/{filename}"
            
    database.update_user_profile(user, display_name=display_name, avatar_url=avatar_url, background_url=background_url, department=department)
    database.log_event(f"Profile updated for {user}", user=user)
    return jsonify({"ok": True, "profile": database.get_user_profile(user)})

@app.route("/")
def index():
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    user = session.get("user")
    is_admin = False
    is_superadmin = False
    if user:
        settings = database.get_user_setting(user)
        is_admin = settings.get("role") == "admin"
        sa_users = set(filter(None, os.environ.get("SUPERADMIN_USERS", "Admin").split(",")))
        is_superadmin = user in sa_users
    return render_template("index.html", google_client_id=google_client_id,
                           vapid_public_key=VAPID_PUBLIC_KEY, is_admin=is_admin, is_superadmin=is_superadmin)

@app.route("/dashboard")
@login_required
def dashboard():
    org_id = get_current_org_id()
    if not billing.has_feature(org_id, "financial_dashboard"):
        return redirect("/pricing?upgrade=financial_dashboard")
    return render_template("tax_expense_dashboard.html")

# ─── Billing Routes ────────────────────────────────────────────────────────────

@app.route("/pricing")
def pricing_page():
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    is_test_mode = stripe_key.startswith("sk_test_")
    return render_template("pricing.html", plans=billing.PLANS, plan_hierarchy=billing.PLAN_HIERARCHY, is_test_mode=is_test_mode)


@app.route("/privacy")
def privacy_page():
    return render_template("privacy.html")


@app.route("/terms")
def terms_page():
    return render_template("terms.html")


@app.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@app.route("/reset-password/<token>")
def reset_password_page(token):
    username = database.validate_reset_token(token)
    return render_template("reset_password.html", valid=bool(username), username=username or "", token=token)


@app.route("/api/auth/forgot-password", methods=["POST"])
@_limiter.limit("3 per minute; 10 per hour")
def api_forgot_password():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip().lower()
    if not username:
        return jsonify({"ok": False, "error": "กรุณากรอก username"})

    token = database.create_reset_token(username)
    if not token:
        # Don't reveal whether user exists
        return jsonify({"ok": True, "message": "ถ้า username นี้มีในระบบ เราจะส่งลิ้งค์รีเซ็ตไปทาง LINE ค่ะ"})

    base = os.environ.get("BASE_URL", "https://openchat.sbs")
    reset_url = f"{base}/reset-password/{token}"

    # Try to send via LINE DM
    line_user_id = database.get_line_user_id_for_username(username)
    line_sent = False
    if line_user_id:
        try:
            _tok = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
            msg = (
                f"สวัสดีค่ะ คุณได้ขอรีเซ็ตรหัสผ่านสำหรับบัญชี OrgChat AI\n\n"
                f"คลิกลิ้งค์ด้านล่างเพื่อตั้งรหัสผ่านใหม่ (หมดอายุใน 1 ชั่วโมง):\n{reset_url}\n\n"
                f"ถ้าไม่ได้ขอรีเซ็ต ไม่ต้องทำอะไรค่ะ"
            )
            import requests as _req
            _req.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                json={"to": line_user_id, "messages": [{"type": "text", "text": msg}]},
                timeout=10,
            )
            line_sent = True
        except Exception as _e:
            logger.warning(f"[ForgotPassword] LINE push failed: {_e}")

    if line_sent:
        return jsonify({"ok": True, "message": "ส่งลิ้งค์รีเซ็ตไปทาง LINE ของคุณแล้วค่ะ กรุณาตรวจสอบข้อความจาก OrgChat AI"})
    else:
        logger.info(f"[ForgotPassword] No LINE for user '{username}' — reset URL logged server-side only.")
        return jsonify({"ok": True, "message": "บัญชีนี้ยังไม่ได้เชื่อม LINE ค่ะ กรุณาติดต่อ Admin เพื่อรีเซ็ตรหัสผ่านให้ค่ะ"})


@app.route("/api/auth/reset-password", methods=["POST"])
@_limiter.limit("5 per minute")
def api_reset_password():
    data = request.get_json(force=True)
    token    = (data.get("token") or "").strip()
    password = data.get("password") or ""
    if not token or len(password) < 6:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบหรือรหัสผ่านสั้นเกินไป"})
    ok = database.consume_reset_token(token, password)
    if not ok:
        return jsonify({"ok": False, "error": "ลิ้งค์ไม่ถูกต้องหรือหมดอายุแล้วค่ะ"})
    return jsonify({"ok": True})

@app.route("/billing")
@login_required
def billing_page():
    return render_template("billing.html")

@app.route("/api/billing/status")
@login_required
def billing_status():
    org_id = get_current_org_id()
    return jsonify({"ok": True, **billing.get_billing_status(org_id)})

@app.route("/admin/customers")
@login_required
@admin_required
def admin_customers_page():
    return render_template("admin_customers.html")


@app.route("/api/admin/orgs")
@login_required
@admin_required
def admin_list_orgs():
    orgs = database.get_all_orgs_with_stats()
    for o in orgs:
        o["plan_config"] = billing.get_plan_config(o["plan"])
    return jsonify({"ok": True, "orgs": orgs})


@app.route("/api/admin/billing/set-plan", methods=["POST"])
@login_required
@admin_required
def admin_set_plan():
    data = request.get_json()
    org_id   = int(data.get("org_id", get_current_org_id()))
    plan     = data.get("plan", "free")
    expires  = data.get("expires_at")   # ISO string or null
    try:
        billing.set_org_plan(org_id, plan, expires)
        return jsonify({"ok": True, "plan": plan})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/billing/checkout", methods=["POST"])
@app.route("/api/b/c", methods=["POST"])
@login_required
def billing_checkout():
    """Create a Stripe Checkout Session and return its URL."""
    if not payment.is_configured():
        return jsonify({"ok": False, "error": "ระบบชำระเงินยังไม่พร้อม กรุณาติดต่อทีมงาน"}), 503

    data = request.get_json()
    plan = data.get("plan", "pro")
    if plan not in ("pro", "business"):
        return jsonify({"ok": False, "error": "ไม่รู้จัก plan นี้"}), 400

    org_id = get_current_org_id()
    stripe_info = database.get_org_stripe_info(org_id)
    base = request.host_url.rstrip("/")

    try:
        checkout_session = payment.create_checkout_session(
            org_id=org_id,
            plan=plan,
            customer_id=stripe_info.get("customer_id"),
            success_url=f"{base}/onboarding?plan={plan}&payment=success&org_id={org_id}",
            cancel_url=f"{base}/billing?payment=cancel",
        )
        return jsonify({"ok": True, "url": checkout_session.url})
    except Exception as e:
        logger.error(f"[Stripe] checkout error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/billing/checkout-promptpay", methods=["POST"])
@app.route("/api/b/cp", methods=["POST"])
@login_required
def billing_checkout_promptpay():
    """Create a Stripe Checkout Session for PromptPay (one-time payment)."""
    if not payment.is_configured():
        return jsonify({"ok": False, "error": "ระบบชำระเงินยังไม่พร้อม กรุณาติดต่อทีมงาน"}), 503

    data = request.get_json() or {}
    plan = data.get("plan", "pro")
    if plan not in ("pro", "business"):
        return jsonify({"ok": False, "error": "ไม่รู้จัก plan นี้"}), 400

    org_id = get_current_org_id()
    stripe_info = database.get_org_stripe_info(org_id)
    base = request.host_url.rstrip("/")

    try:
        checkout_session = payment.create_promptpay_checkout(
            org_id=org_id,
            plan=plan,
            customer_id=stripe_info.get("customer_id"),
            success_url=f"{base}/onboarding?plan={plan}&payment=success&method=promptpay&org_id={org_id}",
            cancel_url=f"{base}/pricing",
        )
        return jsonify({"ok": True, "url": checkout_session.url})
    except Exception as e:
        logger.error(f"[Stripe PromptPay] checkout error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/billing/portal", methods=["POST"])
@app.route("/api/b/p", methods=["POST"])
@login_required
def billing_portal():
    """Open Stripe Customer Portal to manage/cancel subscription."""
    org_id = get_current_org_id()
    stripe_info = database.get_org_stripe_info(org_id)
    customer_id = stripe_info.get("customer_id")

    if not customer_id:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูล Stripe — กรุณาสมัครแพลนก่อน"}), 404

    try:
        base = request.host_url.rstrip("/")
        portal = payment.create_portal_session(customer_id, f"{base}/billing")
        return jsonify({"ok": True, "url": portal.url})
    except Exception as e:
        logger.error(f"[Stripe] portal error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/billing/webhook", methods=["POST"])
def stripe_webhook():
    """Stripe webhook — updates org plan on subscription events."""
    payload   = request.get_data()
    sig       = request.headers.get("Stripe-Signature", "")

    try:
        event = payment.construct_webhook_event(payload, sig)
    except Exception as e:
        logger.warning(f"[Stripe webhook] invalid signature: {e}")
        return jsonify({"error": str(e)}), 400

    etype = event["type"]
    obj   = event["data"]["object"]
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()
    elif obj is not None:
        obj = dict(obj)

    if etype == "checkout.session.completed":
        meta            = obj.get("metadata", {})
        org_id          = int(meta.get("org_id", 0))
        plan            = meta.get("plan", "pro")
        customer_id     = obj.get("customer")
        subscription_id = obj.get("subscription")
        payment_type    = meta.get("payment_type", "")

        if not org_id:
            logger.error(f"[Stripe webhook] checkout.session.completed missing org_id — session {obj.get('id')}")
            return jsonify({"error": "missing org_id in metadata"}), 400

        if plan not in billing.PLANS or plan == "free":
            logger.error(f"[Stripe webhook] invalid plan in metadata: {plan!r}")
            return jsonify({"error": "invalid plan in metadata"}), 400

        if org_id:
            if payment_type == "promptpay" or not subscription_id:
                # One-time payment (PromptPay) → grant plan for N days
                from datetime import timedelta as _td
                days = int(meta.get("days", "30"))
                from datetime import timezone as _tz
                end_iso = (datetime.now(_tz.utc) + _td(days=days)).isoformat()
                billing.set_org_plan(org_id, plan, end_iso)
                if customer_id:
                    database.set_org_stripe_info(org_id, customer_id, None, end_iso)
                logger.info(f"[Stripe PromptPay] Org {org_id} → {plan} for {days} days (expires {end_iso})")
            else:
                # Subscription (credit card)
                end_iso = payment.get_subscription_period_end(subscription_id)
                billing.set_org_plan(org_id, plan, end_iso)
                database.set_org_stripe_info(org_id, customer_id, subscription_id, end_iso)
                logger.info(f"[Stripe] Org {org_id} → {plan} (expires {end_iso})")

    elif etype in ("customer.subscription.updated", "invoice.payment_succeeded"):
        meta   = obj.get("metadata", {})
        org_id = int(meta.get("org_id", 0))
        if org_id:
            plan   = meta.get("plan", "pro")
            if plan not in billing.PLANS or plan == "free":
                logger.warning(f"[Stripe webhook] {etype} invalid plan {plan!r} for org {org_id} — skipping")
                return jsonify({"ok": True})
            sub_id = obj.get("id") if etype == "customer.subscription.updated" else obj.get("subscription")
            status = obj.get("status") if etype == "customer.subscription.updated" else "active"
            if status in ("active", "trialing"):
                end_iso = payment.get_subscription_period_end(sub_id) if sub_id else None
                billing.set_org_plan(org_id, plan, end_iso)
                if sub_id:
                    database.set_org_stripe_info(org_id, obj.get("customer", ""), sub_id, end_iso)
            elif status in ("canceled", "unpaid", "past_due"):
                billing.set_org_plan(org_id, "free")
                logger.info(f"[Stripe] Org {org_id} → free (status={status})")

    elif etype == "customer.subscription.deleted":
        meta   = obj.get("metadata", {})
        org_id = int(meta.get("org_id", 0))
        if org_id:
            billing.set_org_plan(org_id, "free")
            logger.info(f"[Stripe] Org {org_id} → free (subscription deleted)")

    return jsonify({"ok": True})

# ─── End Billing Routes ────────────────────────────────────────────────────────

@app.route("/api/dashboard/tax-expense-data")
@login_required
@billing.require_feature("financial_dashboard")
def tax_expense_data_api():
    """Aggregates tax and expense data from Google Sheets for the dashboard."""
    try:
        from google_drive_service import google_manager
        username = session.get("user")
        org_id = session.get("org_id")
        google_manager.set_context(username, org_id)
        
        def clean_float(val):
            if not val or str(val).strip() == '-':
                return 0.0
            try:
                # Remove commas and non-numeric chars except dot
                import re
                clean_str = re.sub(r'[^\d.]', '', str(val).replace(',', ''))
                return float(clean_str) if clean_str else 0.0
            except:
                return 0.0

        spreadsheet = google_manager.sheets_service.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
        sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        total_expense = 0.0
        total_vat = 0.0
        total_wht = 0.0
        total_wht_3 = 0.0
        total_wht_53 = 0.0
        
        categories_map = {}
        unclear_scans = []
        
        # 1. Process Tax Invoices
        if "ใบเสร็จ/ใบกำกับภาษี" in sheet_titles:
            res_tax = google_manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=google_manager.spreadsheet_id, range="'ใบเสร็จ/ใบกำกับภาษี'!A1:Z"
            ).execute()
            vals = res_tax.get('values', [])
            if vals and len(vals) > 1:
                header = vals[0]
                idx_date = next((i for i, h in enumerate(header) if "วันที่" in h), 2)
                idx_amt = next((i for i, h in enumerate(header) if "สุทธิ" in h or "ยอดเงิน" in h), 9)
                idx_cat = next((i for i, h in enumerate(header) if "หมวดหมู่" in h), 1)
                idx_rec = next((i for i, h in enumerate(header) if "ผู้ส่ง" in h or "ร้านค้า" in h), 3)
                idx_vat = next((i for i, h in enumerate(header) if "VAT" in h), 12)
                idx_wht = next((i for i, h in enumerate(header) if "หัก ณ ที่จ่าย" in h or "WHT" in h), 13)
                idx_tax_id = next((i for i, h in enumerate(header) if "เลขผู้เสียภาษี" in h or "Tax" in h), 5)
                idx_ai_summary = next((i for i, h in enumerate(header) if "สรุปจาก AI" in h), 17)
                idx_link = next((i for i, h in enumerate(header) if "ลิงก์ไฟล์" in h or "ลิงก์ drive" in h), 19)
                
                for r_idx, row in enumerate(vals[1:], start=2):
                    if len(row) <= min(idx_date, idx_amt): continue
                    
                    amt = clean_float(row[idx_amt] if idx_amt < len(row) else 0.0)
                    total_expense += amt
                    
                    cat_val = str(row[idx_cat]).strip() if idx_cat < len(row) else ""
                    if not cat_val or cat_val == '-': cat_val = "ทั่วไป"
                    categories_map[cat_val] = categories_map.get(cat_val, 0.0) + amt
                    
                    vat = clean_float(row[idx_vat] if idx_vat < len(row) else 0.0)
                    total_vat += vat
                    
                    wht = clean_float(row[idx_wht] if idx_wht < len(row) else 0.0)
                    total_wht += wht
                    
                    tax_id = str(row[idx_tax_id]).strip() if idx_tax_id < len(row) else ""
                    if wht > 0:
                        if tax_id.startswith("0"): total_wht_53 += wht
                        else: total_wht_3 += wht
                            
                    ai_summary = str(row[idx_ai_summary]).strip() if idx_ai_summary < len(row) else ""
                    vendor = str(row[idx_rec]).strip() if idx_rec < len(row) else "-"
                    date_val = str(row[idx_date]).strip() if idx_date < len(row) else "-"
                    link_val = str(row[idx_link]).strip() if idx_link < len(row) else ""
                    
                    is_unclear = False
                    issues = []
                    unclear_keywords = ["ไม่ชัด", "ชำรุด", "เบลอ", "ตรวจสอบไม่ได้", "อ่านไม่ได้", "ขาดชำรุด", "มืด"]
                    if any(k in ai_summary for k in unclear_keywords) or any(k in vendor for k in unclear_keywords):
                        is_unclear = True
                        issues.append("ภาพไม่ชัด")
                    if not amt:
                        is_unclear = True
                        issues.append("ไม่พบยอดเงิน")
                    if not date_val or date_val == "-":
                        is_unclear = True
                        issues.append("ไม่พบวันที่")
                        
                    if is_unclear:
                        unclear_scans.append({
                            "sheet": "ใบเสร็จ/ใบกำกับภาษี", "row": r_idx, "date": date_val,
                            "vendor": vendor, "amount": amt, "issues": ", ".join(issues), "link": link_val
                        })

        # 2. Process General Expenses (Voice recordings/others)
        if "บันทึกค่าใช้จ่าย" in sheet_titles:
            res_gen = google_manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=google_manager.spreadsheet_id, range="'บันทึกค่าใช้จ่าย'!A1:Z"
            ).execute()
            vals_gen = res_gen.get('values', [])
            if vals_gen and len(vals_gen) > 1:
                header = vals_gen[0]
                idx_amt = next((i for i, h in enumerate(header) if "จำนวนเงิน" in h), 4)
                idx_cat = next((i for i, h in enumerate(header) if "หมวดหมู่" in h), 1)
                idx_type = next((i for i, h in enumerate(header) if "ประเภท" in h), 3)
                
                for row in vals_gen[1:]:
                    amt = clean_float(row[idx_amt] if idx_amt < len(row) else 0.0)
                    total_expense += amt
                    
                    cat_val = str(row[idx_type]).strip() if idx_type < len(row) else (str(row[idx_cat]).strip() if idx_cat < len(row) else "ทั่วไป")
                    if not cat_val or cat_val == '-': cat_val = "ทั่วไป"
                    categories_map[cat_val] = categories_map.get(cat_val, 0.0) + amt

        # Format categories for chart
        categories_list = [{"name": k, "value": v} for k, v in categories_map.items()]
        categories_list = sorted(categories_list, key=lambda x: x['value'], reverse=True)

        return jsonify({
            "ok": True,
            "total_expense": total_expense,
            "total_vat": total_vat,
            "total_wht": total_wht,
            "total_wht_3": total_wht_3,
            "total_wht_53": total_wht_53,
            "categories": categories_list,
            "unclear_scans": unclear_scans,
            "sheets_list": sheet_titles
        })

    except Exception as e:
        import traceback
        print(f"🚨 Dashboard API Error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/status")
@login_required
def status():
    provider = os.environ.get("AI_PROVIDER", "groq").lower()
    has_key = False
    if provider == "gemini":
        has_key = bool(_get_gemini_api_key())
    elif provider == "groq":
        has_key = bool(os.environ.get("GROQ_API_KEY"))
    elif provider == "ollama":
        has_key = True # Local
        
    stats = rag_engine.kb_stats()
    quota_info = rag_engine.get_quota_status()
    
    user_settings = database.get_user_setting(session.get("user"))
    
    return jsonify({
        "api_key_set": has_key, 
        "quota_info": quota_info,
        "provider": provider,
        "is_admin": user_settings.get("role") == "admin",
        "can_view_kb": bool(user_settings.get("can_view_kb")),
        "can_edit_kb": bool(user_settings.get("can_edit_kb")),
        "can_delete_kb": bool(user_settings.get("can_delete_kb")),
        "user": session.get("user"),
        "app_settings": database.get_all_app_settings(),
        "server_time": get_current_time(),
        **stats
    })


@app.route("/api/set_key", methods=["POST"])
@admin_required
def set_key():
    data = request.get_json(force=True)
    key = data.get("api_key", "").strip()
    if not key:
        return jsonify({"ok": False, "error": "กรุณาใส่ API Key"}), 400
    os.environ["GEMINI_API_KEY"] = key
    # Persist to .env using absolute path from rag_engine
    env_path = rag_engine.BASE_DIR / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    lines = [l for l in lines if not l.startswith("GEMINI_API_KEY")]
    lines.append(f"GEMINI_API_KEY={key}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    # Refresh RAG engine with new key
    rag_engine._kb.update_api_key(key)
    
    return jsonify({"ok": True})


@app.route("/api/upload", methods=["POST"])
@login_required
def upload():
    if not can_edit_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการอัปโหลดไฟล์ (ปิดการใช้งานโดยผู้ดูแลระบบ)"}), 403
    user = session.get("user", "Admin")
    import uuid
    files = request.files.getlist("files")
    dept = request.form.get("department", "General")
    category_id = request.form.get("category_id")
    
    # Convert category_id to int if present
    if category_id and category_id.isdigit():
        category_id = int(category_id)
    else:
        category_id = None

    if not files:
        return jsonify({"ok": False, "error": "ไม่พบไฟล์"}), 400

    org_id = get_current_org_id()
    _kb_plan = billing.get_effective_plan(org_id)
    _kb_limit = billing.get_plan_config(_kb_plan)["limits"]["kb_files"]
    if _kb_limit != -1:
        _current_kb = len([f for f in rag_engine.list_files() if f.get("organization_id", 1) == org_id])
        if _current_kb + len(files) > _kb_limit:
            _cfg = billing.get_plan_config(_kb_plan)
            return jsonify({
                "ok": False,
                "error": "kb_limit_reached",
                "message": f"Plan {_cfg['name']} อนุญาต KB ได้สูงสุด {_kb_limit} ไฟล์ (ปัจจุบัน {_current_kb} ไฟล์) กรุณาอัปเกรด Plan",
                "current_plan": _kb_plan,
            }), 403

    results = []
    for f in files:
        orig_name = f.filename or "file"
        # Strict security validation
        is_valid, err_msg = validate_uploaded_file(f, orig_name)
        if not is_valid:
            return jsonify({"ok": False, "error": f"ไฟล์ {orig_name} ไม่ปลอดภัย: {err_msg}"}), 400
        uid = str(uuid.uuid4())[:8]
        safe_name = secure_filename(orig_name)

        if not safe_name or safe_name.startswith('.'):
            safe_name = f"upload_{uid}"
            
        save_path = rag_engine.UPLOAD_DIR / f"{uid}_{safe_name}"
        f.save(str(save_path))

        # Use a thread for ingestion to keep the app responsive
        _ingest_org_id = get_current_org_id()
        @safe_thread_target
        @db_task_tracker("run_ingest")
        def run_ingest(path, name, d, cat, _oid=_ingest_org_id):


            try:
                rag_engine.ingest_file(path, original_name=name, department=d, category_id=cat, org_id=_oid)
                # --- Notify LINE when KB is updated ---
                broadcast_line_announcement(
                    "คลังความรู้อัปเดต", 
                    f"-> เพิ่มไฟล์ใหม่เข้าระบบ!\nไฟล์: {name}\nส่วนงาน: {d}\nโดย: {user or 'Admin'}",
                    fields={
                        "ไฟล์": name,
                        "ส่วนงาน": d,
                        "ผู้บันทึก": user or "Admin"
                    }
                )
            except Exception as e:
                print(f"❌ Background Ingest Error: {e}")

        thread = threading.Thread(target=run_ingest, args=(save_path, orig_name, dept, category_id))
        thread.start()
        
        results.append({"file": orig_name, "status": "processing"})
        database.log_event(f"Started uploading file: {orig_name}", user=user)

    return jsonify({"ok": True, "results": results, "msg": "ไฟล์กำลังถูกประมวลผลในพื้นหลัง"})


@app.route("/api/files")
@login_required
def list_files():
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการเข้าถึงคลังข้อมูล"}), 403
    
    user = session.get("user", "Admin")
    all_files = rag_engine.list_files()
    
    # Get categories visible to this user
    visible_categories = database.get_categories(user)
    visible_cat_ids = {str(c["id"]) for c in visible_categories}
    
    # Filter files: visible if category is visible OR if file has no category
    filtered_files = []
    for f in all_files:
        cat_id = str(f.get("category_id") or "")
        if not cat_id or cat_id in visible_cat_ids:
            filtered_files.append(f)
            
    return jsonify({"files": filtered_files})

@app.route("/api/files/<file_id>", methods=["DELETE"])
@login_required
def delete_file_route(file_id):
    if not can_delete_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการลบไฟล์ (ติดต่อผู้ดูแลระบบเพื่อขอสิทธิ์)"}), 403
    print(f"🗑️ Deletion request for file_id: {file_id}")
    ok = rag_engine.delete_file(file_id)
    if ok:
        user = session.get("user", "Admin")
        database.log_event(f"Deleted file ID: {file_id}", user=user)
        return jsonify({"ok": True})
    print(f"❌ Deletion failed for file_id: {file_id}")
    return jsonify({"ok": False, "error": "File not found or could not be deleted"}), 404

@app.route("/api/departments")
@login_required
def list_all_departments():
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT department FROM user_profiles WHERE department IS NOT NULL AND department != ''")
    rows = cursor.fetchall()
    conn.close()
    depts = [r[0] for r in rows]
    if "General" not in depts: depts.append("General")
    return jsonify({"ok": True, "departments": sorted(depts)})

# --- KB Category Routes ---

@app.route("/api/kb/categories", methods=["GET"])
@login_required
def list_categories():
    user = session.get("user", "Admin")
    categories = database.get_categories(user)
    return jsonify({"ok": True, "categories": categories})

@app.route("/api/kb/categories", methods=["POST"])
@login_required
def add_kb_category():
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการหมวดหมู่"}), 403
    data = request.json
    name = data.get("name")
    desc = data.get("description")
    visibility = data.get("visibility", "public")
    user = session.get("user", "Admin")
    
    if not name:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อหมวดหมู่"}), 400
        
    try:
        database.add_category(name, desc, user, visibility)
        database.log_event(f"Added KB category: {name} (Visibility: {visibility})", user=user)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/kb/categories/settings", methods=["POST"])
@login_required
def update_kb_category_settings():
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการหมวดหมู่"}), 403
    data = request.json
    cat_id = data.get("id")
    visibility = data.get("visibility")
    authorized_users = data.get("authorized_users", []) # List of usernames
    user = session.get("user", "Admin")
    
    if not cat_id or not visibility:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400
        
    # Check if user has permission to edit THIS category (must be owner or Admin)
    cat_info = next((c for c in database.get_categories("Admin") if c["id"] == cat_id), None)
    if not cat_info:
        return jsonify({"ok": False, "error": "ไม่พบหมวดหมู่"}), 404
        
    if user != "Admin" and cat_info["created_by"] != user:
        return jsonify({"ok": False, "error": "คุณไม่ใช่เจ้าของหมวดหมู่นี้"}), 403

    try:
        success = database.update_category_settings(cat_id, visibility, authorized_users)
        if success:
            database.log_event(f"Updated KB category settings ID: {cat_id}", user=user)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "ล้มเหลวในการบันทึกการตั้งค่า"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/kb/categories/<int:cat_id>", methods=["DELETE"])
@login_required
def delete_kb_category(cat_id):
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการหมวดหมู่"}), 403
    user = session.get("user", "Admin")
    try:
        database.delete_category(cat_id)
        database.log_event(f"Deleted KB category ID: {cat_id}", user=user)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/kb/categories/access/<int:cat_id>", methods=["GET"])
@login_required
def get_kb_category_access(cat_id):
    # Only owner or Admin can see the access list
    user = session.get("user", "Admin")
    cat_info = next((c for c in database.get_categories("Admin") if c["id"] == cat_id), None)
    if not cat_info:
        return jsonify({"ok": False, "error": "ไม่พบหมวดหมู่"}), 404
        
    if user != "Admin" and cat_info["created_by"] != user:
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้"}), 403

    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user_category_access WHERE category_id = ?", (cat_id,))
    users = [r[0] for r in cursor.fetchall()]
    conn.close()
    
    return jsonify({"ok": True, "users": users})

@app.route("/api/kb/search")
@login_required
def kb_search():
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการค้นหาคลังข้อมูล"}), 403
    """Search knowledge base files by name or content snippet."""
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify({"ok": True, "results": []})
        
    user = session.get("user", "Admin")
    visible_categories = database.get_categories(user)
    visible_cat_ids = [str(c["id"]) for c in visible_categories]
    
    # ChromaDB 'where' filter logic
    if visible_cat_ids:
        # User sees: restricted/private they own + public + unassigned
        where_filter = {
            "$or": [
                {"category_id": {"$in": visible_cat_ids}},
                {"category_id": ""} # Unassigned
            ]
        }
    else:
        # Fallback: only unassigned or public if user has no visible cats?
        # Actually database.get_categories(user) always returns public ones.
        where_filter = {"category_id": ""}

    try:
        files = rag_engine.list_files()
        # Filter by file name (fast, local), respecting visibility
        name_matches = []
        for f in files:
            cat_id = str(f.get("category_id") or "")
            if not cat_id or cat_id in visible_cat_ids:
                if query in (f.get("name") or "").lower():
                    name_matches.append(f)
                    
        # Also do a semantic search for content matches
        kb_results = rag_engine.search_kb(query, n_results=10, where=where_filter)
        
        # Combine: file cards for name matches + content snippets for semantic
        results = []
        seen_ids = set()
        for f in name_matches:
            results.append({
                "file_id": f["file_id"],
                "file_name": f["name"],
                "file_type": f.get("type", ""),
                "text": f"ชื่อไฟล์ตรงกับคำค้นหา",
                "score": 1.0,
                "location": f.get("department", "General")
            })
            seen_ids.add(f["file_id"])
        
        for r in kb_results:
            fid = r.get("file_id", "")
            if fid not in seen_ids:
                results.append({
                    "file_id": fid,
                    "file_name": r.get("name", r.get("source", "")),
                    "file_type": r.get("file_type", ""),
                    "text": r.get("text", "")[:200],
                    "score": r.get("score", 0),
                    "location": r.get("department", "General")
                })
                seen_ids.add(fid)
        return jsonify({"ok": True, "results": results[:20]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/kb/files/assign", methods=["POST"])
@login_required
def assign_file_category():
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการไฟล์"}), 403
    data = request.json
    file_id = data.get("file_id")
    category_id = data.get("category_id") # Can be None to unassign
    user = session.get("user", "Admin")

    if not file_id:
        return jsonify({"ok": False, "error": "Missing file_id"}), 400

    try:
        # Update in database if needed, but primarily in rag_engine meta
        rag_engine.update_file_category(file_id, category_id)
        database.log_event(f"Assigned file {file_id} to category {category_id}", user=user)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
@app.route("/api/personas", methods=["GET"])
@login_required
def get_personas():
    personas = database.get_all_personas_v2()
    return jsonify({"ok": True, "personas": personas})

@app.route("/api/kb/files/view/<file_id>")
@login_required
def view_kb_file(file_id):
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการดูไฟล์"}), 403
    files = rag_engine.list_files()
    file_info = next((f for f in files if f["file_id"] == file_id), None)
    if not file_info:
        return "File not found", 404
    
    path = Path(file_info["path"])
    if not path.exists():
        print(f"❌ File not found on disk: {path}")
        return f"File not found on disk: {path}", 404
        
    return send_file(path, mimetype='application/pdf' if file_info['type'] == 'pdf' else 'text/plain')

@app.route("/api/export/pdf", methods=["POST"])
@login_required
@billing.require_feature("export")
def export_pdf():
    try:
        data = request.get_json(force=True)
        title = data.get("title", "OrgChat Report")
        content = data.get("content", "")
        
        if not content:
            return jsonify({"ok": False, "error": "ไม่มีเนื้อหาให้ส่งออก"}), 400

        pdf = FPDF()
        pdf.add_page()
        
        # We need a Thai font. For now, we'll try to use a standard one and add Thai support once font path is confirmed.
        # pdf.add_font('THSarabunNew', '', 'font_path', unicode=True)
        # pdf.set_font('THSarabunNew', '', 16)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=title, ln=1, align='C')
        pdf.ln(10)
        
        # Multi_cell handles word wrap
        pdf.multi_cell(0, 10, txt=content)
        
        filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
        output_path = rag_engine.UPLOAD_DIR / filename
        pdf.output(str(output_path))
        
        return jsonify({
            "ok": True, 
            "url": f"/api/files/download/{filename}",
            "filename": filename
        })
    except Exception as e:
        print(f"❌ PDF Export Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/files/download/<filename>")
def download_file(filename):
    return send_from_directory(rag_engine.UPLOAD_DIR, filename, as_attachment=True)


@app.route("/api/reconciliation/process", methods=["POST"])
@login_required
@billing.require_plan("pro")
def process_reconciliation():
    if not is_admin():
        return jsonify({"ok": False, "error": "Only admins can perform reconciliation"}), 403
    
    mp_files = request.files.getlist('marketplace')
    ship_files = request.files.getlist('shipnity')
    peak_files = request.files.getlist('peak')
    
    if not mp_files or not ship_files or not peak_files:
        return jsonify({"ok": False, "error": "กรุณาอัปโหลดไฟล์ให้ครบทุกหมวดหมู่ (Marketplace, Shipnity, PEAK)"}), 400
        
    try:
        df_result, financial = ReconciliationService.process_files(mp_files, ship_files, peak_files)
        
        # Fill NaN with safe defaults for JSON serialization
        df_clean = df_result.fillna('')
        
        for col in df_clean.columns:
            if df_clean[col].dtype in ['float64', 'int64']:
                df_clean[col] = df_clean[col].replace('', 0)
        
        records = df_clean.to_dict(orient='records')
        
        issue_count = sum(1 for r in records if r.get('issue', '') != '✅ ปกติ')
        
        summary = {
            "total": len(records),
            "issues": issue_count,
            "data": records,
            "financial": financial
        }
        
        # Cache data in memory for on-demand download
        report_id = uuid.uuid4().hex[:8]
        if not hasattr(app, '_recon_cache'):
            app._recon_cache = {}
        app._recon_cache[report_id] = df_result
        
        summary["report_url"] = f"/api/reconciliation/download/{report_id}"
        
        return jsonify({"ok": True, "summary": summary})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/reconciliation/download/<report_id>")
@login_required
def download_recon_report(report_id):
    if not hasattr(app, '_recon_cache') or report_id not in app._recon_cache:
        return jsonify({"ok": False, "error": "รายงานหมดอายุ กรุณาประมวลผลใหม่"}), 404
    
    df = app._recon_cache[report_id]
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'reconciliation_report_{report_id}.xlsx'
    )

@app.route("/api/reconciliation/download-filtered", methods=["POST"])
@login_required
def download_filtered_recon():
    """Generate Excel from filtered data sent by client."""
    try:
        data = request.get_json()
        rows = data.get('rows', [])
        if not rows:
            return jsonify({"ok": False, "error": "ไม่มีข้อมูลสำหรับดาวน์โหลด"}), 400
        
        import pandas as pd
        df = pd.DataFrame(rows)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'reconciliation_filtered_{uuid.uuid4().hex[:6]}.xlsx'
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/reconciliation/move-row", methods=["POST"])
@login_required
@billing.require_plan("pro")
def move_row_between_sheets_api():
    """Move a row from one sheet to another in Google Sheets."""
    try:
        data = request.get_json()
        from_sheet = data.get("from_sheet", "").strip()
        row_index = int(data.get("row_index", 0))
        to_sheet = data.get("to_sheet", "").strip()

        if not from_sheet or not to_sheet or row_index <= 0:
            return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400

        ok, err = google_manager.move_row_between_sheets(from_sheet, row_index, to_sheet)
        if ok:
            return jsonify({"ok": True})
        else:
            return jsonify({"ok": False, "error": err or "ย้ายไม่สำเร็จ"}), 500
    except Exception as e:
        import traceback
        print(f"[move-row] Error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


# --- Calendar Schedules ---
@app.route("/api/schedules", methods=["GET", "POST"])
@login_required
def manage_schedules():
    user = session.get("user")
    if request.method == "POST":
        data = request.get_json(force=True)
        title = data.get("title")
        start_date = data.get("date") # Expected YYYY-MM-DD
        desc = data.get("desc", "")
        category = data.get("category", "General")
        start_time = data.get("time", "09:00")
        is_public = 1 if data.get("is_public") else 0
        target_depts = data.get("target_departments")
        target_users = data.get("target_users")
        status = data.get("status", "todo")
        
        if not title or not start_date:
            return jsonify({"ok": False, "error": "Missing title or date"}), 400
            
        org_id = get_current_org_id()
        database.add_schedule(user, title, start_date, desc, category, start_time, is_public, status, target_departments=target_depts, target_users=target_users, org_id=org_id)
        visibility_text = "Public" if is_public else "Private"
        database.log_event(f"Added {visibility_text} schedule: {title} on {start_date}", user=user)
        
        # --- New Public Event Broadcast ---
        profile = database.get_user_profile(user)
        display_name = profile.get("display_name", user)
        if is_public:
            notification_db.notify_all_except(
                user, 
                'calendar', 
                'กิจกรรมใหม่: ' + title, 
                f'โดย {display_name} | วันที่ {start_date} เวลา {start_time}',
                link='#calendar'
            )
            # --- LINE Broadcast for Public Events ---
            threading.Thread(target=broadcast_line_announcement, args=(
                "กิจกรรมใหม่", 
                f"-> กำหนดการใหม่!\nหัวข้อ: {title}\nวันที่: {start_date}\nเวลา: {start_time} น.\nโดย: {display_name}",
            ), kwargs={
                "fields": {
                    "หัวข้อ": title,
                    "วันที่": start_date,
                    "เวลา": f"{start_time} น.",
                    "โดย": display_name
                }
            }).start()
        else:
            # Notify specific users if specified
            if target_users:
                t_users = [u.strip() for u in target_users.split(',') if u.strip() and u.strip().lower() != user.lower()]
                if t_users:
                    notification_db.notify_users(
                        t_users, 'calendar', 'กำหนดการใหม่ที่แชร์กับคุณ: ' + title,
                        f'โดย {display_name} | วันที่ {start_date} เวลา {start_time}',
                        link='#calendar'
                    )
                    batch_send_push_notification(t_users, 'กำหนดการที่แชร์กับคุณ', f'{display_name}: {title}', url='#calendar')
                    
                    # --- LINE Push for Targeted Users ---
                    for target in t_users:
                        threading.Thread(target=send_line_push_notification, args=(
                            target, 
                            "กิจกรรมใหม่", 
                            f"-> กำหนดการใหม่สำหรับคุณ!\nหัวข้อ: {title}\nวันที่: {start_date}\nเวลา: {start_time} น.",
                        ), kwargs={
                            "fields": {
                                "หัวข้อ": title,
                                "วันที่": start_date,
                                "เวลา": f"{start_time} น.",
                                "โดย": display_name
                            }
                        }).start()
            
            # Notify specific departments
            if target_depts:
                t_depts = [d.strip() for d in target_depts.split(',') if d.strip()]
                # Get all users in these departments
                conn = sqlite3.connect(database.DB_PATH)
                cursor = conn.cursor()
                cursor.execute(f"SELECT username FROM user_profiles WHERE department IN ({','.join(['?']*len(t_depts))})", t_depts)
                dept_users = [r[0] for r in cursor.fetchall() if r[0].lower() != user.lower()]
                conn.close()
                if dept_users:
                    notification_db.notify_users(
                        dept_users, 'calendar', 'กิจกรรมใหม่ในแผนก: ' + title,
                        f'โดย {display_name} | วันที่ {start_date} เวลา {start_time}',
                        link='#calendar'
                    )
                    batch_send_push_notification(dept_users, 'กิจกรรมใหม่ในแผนก', f'{display_name}: {title}', url='#calendar')
                        
        return jsonify({"ok": True})

    org_id = get_current_org_id()
    return jsonify({"schedules": database.get_schedules(user, org_id=org_id)})

@app.route("/api/schedules/<int:sid>", methods=["PUT", "DELETE"])
@login_required
def manage_schedule_item(sid):
    user = session.get("user")
    org_id = get_current_org_id()
    # Verify this schedule belongs to current org before any operation
    sched = database.get_schedule_by_id(sid)
    if not sched or sched.get("organization_id") != org_id:
        return jsonify({"ok": False, "error": "ไม่พบหรือไม่มีสิทธิ์"}), 404

    if request.method == "DELETE":
        ok = database.delete_schedule(sid, username=user, is_admin=is_admin())
        if ok:
            database.log_event(f"Schedule deleted: ID {sid}", user=user)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ลบกำหนดการนี้"}), 403

    if request.method == "PUT":
        data = request.get_json(force=True)
        title = data.get("title")
        date = data.get("date")
        desc = data.get("desc", "")
        cat = data.get("category", "General")
        time_val = data.get("time", "09:00")
        is_public = 1 if data.get("is_public") else 0
        status = data.get("status", "todo")
        target_depts = data.get("target_departments")
        target_users = data.get("target_users")

        if not title or not date:
            return jsonify({"ok": False, "error": "Missing title or date"}), 400

        database.update_schedule(sid, title, date, desc, cat, time_val, is_public, status, target_departments=target_depts, target_users=target_users)
        user = session.get("user", "Admin")
        database.log_event(f"Updated schedule ID: {sid}", user=user)
        return jsonify({"ok": True})

@app.route("/api/schedules/<int:sid>/toggle", methods=["POST"])
@login_required
def toggle_schedule_route(sid):
    new_status = database.toggle_schedule_status(sid)
    if new_status is None:
        return jsonify({"ok": False, "error": "Schedule not found"}), 404
    user = session.get("user", "Admin")
    database.log_event(f"Toggled schedule status: {sid} to {new_status}", user=user)
    return jsonify({"ok": True, "new_status": new_status})

@app.route("/api/schedules/clear-past", methods=["DELETE"])
@login_required
def delete_past_schedules_route():
    user = session.get("user")
    database.delete_past_schedules(user)
    database.log_event(f"Cleared all past schedules", user=user)
    return jsonify({"ok": True})

@app.route("/api/schedules/archive-past", methods=["POST"])
@login_required
def archive_past_schedules_route():
    user = session.get("user")
    database.archive_past_schedules(user)
    database.log_event(f"Archived all past schedules", user=user)
    return jsonify({"ok": True})



@app.route("/api/ping")
def ping():
    return jsonify({"ok": True, "version": "v1.2-diagnostics"})

# ⚡ AI Kanban Auto-Generator
@app.route("/api/kanban/auto-generate", methods=["POST"])
@login_required
def auto_generate_kanban():
    user = session.get("user", "Admin")
    data = request.get_json(force=True)
    goal = data.get("goal")
    if not goal:
        return jsonify({"ok": False, "error": "กรุณากรอกเป้าหมาย"}), 400

    prompt = (
        f"จากเป้าหมายดังนี้: '{goal}' "
        "ช่วยแตกเป็นรายการงานย่อยๆ (Tasks) สำหรับระบบ Kanban "
        "ตอบในรูปแบบ JSON เป็นรายการดั้งนี้ "
        '{"tasks": [{"title": "ชื่อสั้นๆ", "desc": "รายละเอียดงาน", "category": "General|Task|Meeting", "date": "YYYY-MM-DD", "time": "HH:MM"}]} '
        f"กำหนดวันที่เริ่มจากวันนี้ ({get_current_time().split(' ')[0]}) เป็นต้นไป "
        "ข้อสำคัญ: ตอบเฉพาะ JSON เท่านั้น ห้ามมีข้อความอื่นเด็ดขาด"
    )

    try:
        provider = ai_providers.get_provider()
        response_text = provider.chat(prompt, [], "")
        
        # Clean potential markdown backticks
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        
        org_id = get_current_org_id()
        tasks_added = 0
        for t in result.get("tasks", []):
            database.add_schedule(
                user,
                t.get("title"),
                t.get("date"),
                description=t.get("desc", ""),
                category=t.get("category", "Task"),
                start_time=t.get("time", "09:00"),
                status="todo",
                org_id=org_id
            )
            tasks_added += 1
            
        database.log_event(f"AI Auto-generated {tasks_added} tasks for goal: {goal[:50]}", user=user)
        return jsonify({"ok": True, "count": tasks_added})
    except Exception as e:
        print(f"❌ AI Kanban Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# 📑 AI Document Comparison
@app.route("/api/kb/compare", methods=["POST"])
@login_required
def compare_knowledge_base_files():
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    data = request.json
    f1_id = data.get("file1_id")
    f2_id = data.get("file2_id")
    prompt_custom = data.get("prompt", "ช่วยสรุปสิ่งที่เหมือนกัน, สิ่งที่แตกต่างกัน และจุดสำคัญที่คุณค้นพบ")
    
    if not f1_id or not f2_id:
        return jsonify({"ok": False, "error": "Missing file IDs"}), 400
        
    try:
        # Retrieve ALL content for both files
        ctx1 = rag_engine.get_file_content(f1_id)
        ctx2 = rag_engine.get_file_content(f2_id)
        
        if not ctx1 or not ctx2:
            return jsonify({"ok": False, "error": "ไม่สามารถดึงข้อมูลเนื้อหาไฟล์มาเปรียบเทียบได้"}), 404

        prompt = (
            f"ช่วยเปรียบเทียบข้อมูลจากสองแหล่งนี้อย่างละเอียด:\n\n"
            f"--- ข้อมูลชุดที่ 1 ---\n{ctx1[:8000]}\n\n"
            f"--- ข้อมูลชุดที่ 2 ---\n{ctx2[:8000]}\n\n"
            f"คำสั่งเพิ่มเติม: {prompt_custom}\n\n"
            "ตอบเป็นภาษาไทยในรูปแบบ Markdown ที่สวยงาม มีตารางเปรียบเทียบ (ถ้าเป็นไปได้) และสรุปประเด็นสำคัญสำหรับผู้บริหาร"
        )
        
        provider = ai_providers.get_provider()
        reply = provider.chat_stream(prompt, [], "คุณคือนักวิเคราะห์ข้อมูลผู้ช่วยส่วนกลางขององค์กร")
        
        # We'll use a simple non-streaming response for compare for now to keep it simple, or we could stream it.
        # But for comparison, a solid final result is often preferred.
        full_reply = ""
        for chunk in reply:
             if chunk: full_reply += chunk
             
        return jsonify({"ok": True, "comparison": full_reply})
    except Exception as e:
        print(f"❌ Document Comparison Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/csv/<file_id>", methods=["GET", "POST"])
@login_required
def manage_csv_combined(file_id):
    """Combined CSV handler to ensure registration."""
    print(f"[API HIT] CSV API HIT: {request.method} {file_id}")
    files = rag_engine.list_files()
    target = next((f for f in files if f["file_id"] == file_id), None)
    if not target:
        return jsonify({"ok": False, "error": "File not found"}), 404
        
    path = Path(target["path"])
    
    if request.method == "GET":
        if not can_view_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการเข้าถึงไฟล์"}), 403
        if not path.exists() or path.suffix.lower() != ".csv":
            return jsonify({"ok": False, "error": "Invalid file type"}), 400
        try:
            import csv
            data = []
            with open(path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    data.append(row)
            return jsonify({"ok": True, "headers": headers, "data": data, "name": target["name"]})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method == "POST":
        if not can_edit_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการแก้ไขไฟล์ (ปิดการใช้งานโดยผู้ดูแลระบบ)"}), 403
        data_json = request.get_json()
        rows = data_json.get("data", [])
        headers = data_json.get("headers", [])
        if not rows or not headers:
            return jsonify({"ok": False, "error": "Empty data"}), 400
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            rag_engine.delete_file(file_id, delete_from_disk=False)
            res = rag_engine.ingest_file(path, original_name=target["name"], department=target.get("department", "General"), org_id=get_current_org_id())
            if res.get("status") == "error":
                return jsonify({"ok": False, "error": f"บันทึกไฟล์สำเร็จ แต่ AI อัปเดตข้อมูลล้มเหลว: {res.get('error')}"}), 500
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/txt/<file_id>", methods=["GET", "POST"])
@login_required
def manage_txt(file_id):
    print(f"[API HIT] TXT API HIT: {request.method} {file_id}")
    files = rag_engine.list_files()
    target = next((f for f in files if f["file_id"] == file_id), None)
    if not target:
        return jsonify({"ok": False, "error": "File not found"}), 404
    path = Path(target["path"])
    if request.method == "GET":
        if not can_edit_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการเข้าถึงตัวแก้ไขไฟล์"}), 403
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            return jsonify({"ok": True, "content": content})
        except Exception as e: return jsonify({"ok": False, "error": str(e)}), 500
    if request.method == "POST":
        if not can_edit_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการแก้ไขไฟล์ (ปิดการใช้งานโดยผู้ดูแลระบบ)"}), 403
        try:
            content = request.json.get("content", "")
            with open(path, "w", encoding="utf-8") as f: f.write(content)
            rag_engine.delete_file(file_id, delete_from_disk=False)
            res = rag_engine.ingest_file(path, original_name=target["name"], department=target.get("department", "General"), org_id=get_current_org_id())
            if res.get("status") == "error":
                return jsonify({"ok": False, "error": f"บันทึกไฟล์สำเร็จ แต่ AI อัปเดตข้อมูลล้มเหลว: {res.get('error')}"}), 500
            return jsonify({"ok": True})
        except Exception as e: return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})
    
    user = session.get("user")
    rag_filter = get_rag_filter(user)
    results = rag_engine.search_kb(query, n_results=10, where=rag_filter)
    return jsonify({"results": results})


@app.route("/api/sync", methods=["POST"])
@admin_required
def sync_kb():
    results = rag_engine.sync_uploads()
    return jsonify({"ok": True, "results": results})

@app.route("/api/prune", methods=["POST"])
@admin_required
def prune_kb_route():
    count = rag_engine.prune_kb()
    return jsonify({"ok": True, "pruned": count})


@app.route("/api/wipe", methods=["POST"])
@admin_required
def wipe():
    ok = rag_engine.wipe_knowledge_base()
    return jsonify({"ok": ok})


@app.route("/api/history")
@login_required
def get_history():
    user = session.get("user")
    org_id = get_current_org_id()
    return jsonify({"history": database.get_history(user, org_id=org_id)})



@app.route("/api/history/clear", methods=["POST"])
@login_required
def clear_history():
    user = session.get("user")
    org_id = get_current_org_id()
    database.clear_history(user, org_id=org_id)
    return jsonify({"ok": True})


@app.route("/api/feedback", methods=["POST"])
def feedback():
    user = session.get("user", "Admin")
    data = request.get_json(force=True)
    val = data.get("value", 0) # 1 or -1
    database.save_feedback(user, val)
    return jsonify({"ok": True})


@app.route("/api/stats")
@login_required
def stats_route():
    user = session.get("user")
    return jsonify(database.get_stats(user))

@app.route("/api/dashboard/data")
@login_required
def dashboard_data():
    user = session.get("user")
    # Auto cleanup/archive very old data (90+ days)
    database.auto_archive_old_schedules(90)

    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    
    # 1. Total Files & Chunks
    kb_info = rag_engine.kb_stats()
    
    # 2. Total Chat Messages for this user
    cursor.execute("SELECT COUNT(*) FROM messages WHERE username = ?", (user,))
    chat_count = cursor.fetchone()[0]
    
    # 3. Total Users
    cursor.execute("SELECT COUNT(DISTINCT username) FROM user_profiles") # Simplified for now
    user_count = cursor.fetchone()[0]
    
    # 4. Recent Activity (Latest 5 events for this user)
    cursor.execute("SELECT event_text, time FROM events WHERE user = ? ORDER BY time DESC LIMIT 5", (user,))
    logs = cursor.fetchall()
    activity_count = len(logs)
    
    # 5. Recent History (Latest 5 chats)
    cursor.execute("SELECT text, timestamp FROM messages WHERE username = ? AND role = 'user' ORDER BY timestamp DESC LIMIT 5", (user,))
    recent_chats = [{"text": r[0], "time": r[1]} for r in cursor.fetchall()]
    
    # 7. Recent Files (Filtered by visibility)
    all_files = rag_engine.list_files()
    visible_categories = database.get_categories(user)
    visible_cat_ids = {str(c["id"]) for c in visible_categories}
    
    filtered_recent = []
    for f in all_files:
        cat_id = str(f.get("category_id") or "")
        if not cat_id or cat_id in visible_cat_ids:
            filtered_recent.append(f)
            
    recent_files = sorted(filtered_recent, key=lambda x: x.get('uploaded_at', ''), reverse=True)[:5]
    
    # 8. Unread Notifications Count
    import notification_db
    unread_notifs = notification_db.get_notifications(user, unread_only=True)
    unread_count = len(unread_notifs)

    # 9. Tasks and Schedules
    from datetime import date
    today = date.today().isoformat()
    user_schedules = database.get_schedules(user, org_id=get_current_org_id())
    pending_tasks = [s for s in user_schedules if s.get("status", "todo") in ("todo", "doing") and s.get("date", "") >= today]
    completed_tasks_count = len([s for s in user_schedules if s.get("status") == "done"])


    # 10. Drive Logs Stats
    drive_stats = database.get_drive_stats()

    conn.close()
    
    return jsonify({
        "ok": True,
        "stats": {
            "files": len(filtered_recent), # Show only visible file count to user
            "chats": chat_count,
            "users": user_count,
            "total_files": len(filtered_recent),
            "total_queries": chat_count,
            "total_users": user_count,
            "activity": activity_count,
            "unread_notifications": unread_count,
            "completed_tasks": completed_tasks_count,
            "drive_files": drive_stats.get("total_files", 0),
            "total_amount": drive_stats.get("total_amount", 0),
            "recent_drive_uploads": drive_stats.get("recent_count", 0)
        },
        "recent_chats": recent_chats,
        "recent_files": recent_files,
        "upcoming": pending_tasks[:3], 
        "pending_tasks": pending_tasks,
        "logs": [{"event": l[0], "time": l[1]} for l in logs],
        "drive_categories": drive_stats.get("categories", {}),
        "recent_drive_logs": database.get_drive_logs(limit=5)
    })

@app.route("/api/dashboard/briefing")
@login_required
def dashboard_briefing():
    user = session.get("user")
    activities = database.get_daily_activities(org_id=get_current_org_id())
    
    if not activities["posts"] and not activities["schedules"]:
        return jsonify({"ok": True, "briefing": "วันนี้ยังไม่มีกิจกรรมใหม่ที่บันทึกไว้ครับ คุณสามารถเริ่มแชทหรืออัปโหลดเอกสารใหม่เพื่อเริ่มต้นวันได้ทันที!"})
    
    # Prepare context for AI
    context = "กิจกรรมล่าสุดใน 24 ชั่วโมงที่ผ่านมา:\n"
    for p in activities["posts"][:5]:
        context += f"- [FEED] {p['author']} โพสต์ในหมวด {p['category']}: {p['content'][:100]}...\n"
    for s in activities["schedules"][:5]:
        context += f"- [SCHEDULE] มีนัดหมายถึง: {s['title']} วันที่ {s['date']} เวลา {s['time']}\n"
        
    prompt = f"""คุณเป็น AI ผู้ช่วยอัจฉริยะ (OrgChat) สรุป "Daily Briefing" สั้นๆ ให้กับผู้ใช้ชื่อ {user} 
จากข้อมูลกิจกรรมล่าสุดต่อไปนี้ โดยใช้ภาษาที่เป็นกันเอง ทันสมัย และกระตือรือร้น (ไม่เกิน 3-4 ประโยค):

{context}

สรุปให้น่าสนใจและเน้นสิ่งที่ควรทราบที่สุดประจำวันนี้:"""

    _org_id = get_current_org_id()
    _allowed, _used, _limit = billing.check_and_increment(_org_id, "ai_query_count")
    if not _allowed:
        return jsonify({
            "ok": False,
            "error": "usage_limit_reached",
            "message": f"คุณใช้ AI ถามตอบครบ {_limit} ครั้งแล้วในเดือนนี้ค่ะ กรุณา <a href='/billing' class='underline font-semibold'>อัปเกรด Plan</a> เพื่อใช้งานต่อได้เลยค่ะ",
            "current_plan": billing.get_effective_plan(_org_id),
            "upgrade_url": "/billing",
        }), 403

    try:
        # ใช้ ai_providers ใหม่แทน genai.GenerativeModel เก่า
        provider = ai_providers.get_provider()
        briefing = ""
        for chunk in provider.chat_stream(prompt, [], "คุณคือ AI ผู้ช่วยสรุปข่าวสารองค์กร"):
            if chunk: briefing += chunk
        briefing = briefing.strip()
        return jsonify({"ok": True, "briefing": briefing})
    except Exception as e:
        print(f"Briefing Error: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสร้างสรุปได้ในขณะนี้"})

@app.route("/api/lunch/random")
@login_required
def lunch_random():
    place = database.get_random_lunch()
    if place:
        return jsonify({"ok": True, "place": place})
    return jsonify({"ok": False, "error": "ยังไม่มีร้านอาหารในระบบ"})

@app.route("/api/lunch/all")
@login_required
def lunch_all():
    places = database.get_all_lunch_places()
    return jsonify({"ok": True, "places": places})

@app.route("/api/lunch/add", methods=["POST"])
@login_required
def lunch_add():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อร้าน"})
    
    database.add_lunch_place(
        name=name,
        type_str=data.get("type", ""),
        location=data.get("location", ""),
        added_by=session.get("user", "Admin")
    )
    return jsonify({"ok": True})

@app.route("/api/lunch/delete/<int:place_id>", methods=["DELETE"])
@login_required
@admin_required
def lunch_delete(place_id):
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lunch_places WHERE id = ?", (place_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/summary/generate", methods=["POST"])
@login_required
def generate_global_summary():
    data = request.json or {}
    focus = data.get("focus", "").strip()
    category_id = data.get("category_id", "all")
    
    user = session.get("user", "Admin")
    visible_categories = database.get_categories(user)
    visible_cat_ids = [str(c["id"]) for c in visible_categories]
    
    # Global visibility filter (user sees visible categories + unassigned)
    global_where = {
        "$or": [
            {"category_id": {"$in": visible_cat_ids}},
            {"category_id": ""}
        ]
    }

    where_filter = None
    search_query = focus
    
    if category_id != "all":
        if category_id == "unassigned":
            where_filter = {"category_id": ""}
            if not search_query: search_query = "สรุปข้อมูลที่ยังไม่ได้ระบุหมวดหมู่"
        else:
            if str(category_id) not in visible_cat_ids:
                return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์เข้าถึงหมวดหมู่นี้"}), 403
            where_filter = {"category_id": str(category_id)}
            # Try to get category name for better context if no focus given
            if not search_query:
                try:
                    conn = sqlite3.connect(database.DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM kb_categories WHERE id = ?", (int(category_id),))
                    row = cursor.fetchone()
                    conn.close()
                    if row: search_query = f"สรุปข้อมูลเกี่ยวกับ {row[0]}"
                except: pass
    # else: category_id == "all" → where_filter stays None (search ALL data)
        
    if not search_query:
        search_query = "ภาพรวมองค์กร กฎระเบียบ ประกาศ ข่าวสารล่าสุด"

    print(f"📄 Summary Request - Category: {category_id}, Focus: '{focus}', Filter: {where_filter}")
    
    try:
        is_fallback = False
        # 1. Semantic Search
        results = rag_engine.search_kb(search_query, n_results=10, where=where_filter)
        
        # Fallback 1: Literal grab from category
        if not results:
            results = rag_engine.get_all_chunks(where=where_filter, limit=10)
            
        # Fallback 2: Try without any filter at all
        if not results and where_filter is not None:
            print(f"⚠️ Filtered search empty, falling back to unfiltered search")
            results = rag_engine.search_kb(search_query, n_results=10)
            if not results:
                results = rag_engine.get_all_chunks(limit=10)
            is_fallback = True

        if not results:
            msg = "ไม่มีข้อมูลในหมวดหมู่ที่ระบุหรือหมวดหมู่ที่คุณสามารถเข้าถึงได้"
            return jsonify({"ok": False, "error": msg}), 404
            
        context_text = "\n".join([f"- {r['text']}" for r in results])
        # Cap context for Groq TPM limits
        if len(context_text) > 8000:
            context_text = context_text[:8000] + "..."

        focus_instruction = f"\nเน้นข้อมูลเกี่ยวกับหัวข้อ: '{focus}'" if focus else ""
        fallback_notice = "\nหมายเหตุ: เนื่องจากหมวดหมู่ที่ระบุไม่มีข้อมูลเพียงพอ AI จึงใช้ข้อมูลจากคลังความรู้ที่คุณสามารถเข้าถึงได้ทั้งหมดในการสรุปแทน" if is_fallback else ""
        
        prompt = f"""คุณคือผู้ช่วยอัจฉริยะประจำบริษัท หน้าที่ของคุณคือสร้าง 'บทสรุปความรู้อันเป็นประโยชน์' จากข้อมูลที่ได้รับด้านล่างนี้
กรุณาสรุปด้วยภาษาไทยที่สุภาพ เป็นมืออาชีพ เน้นความกระชับและอ่านง่าย (ใช้ Markdown)
{focus_instruction}
{fallback_notice}

สำคัญ: หลีกเลี่ยงการแปลตรงตัวจากภาษาอังกฤษ ใช้สำนวนไทยที่คนทำงานออฟฟิศใช้กันจริงๆ และลงท้ายด้วย 'ครับ' อย่างเหมาะสม

โครงสร้างสรุป:
1. ภาพรวมหลัก (Main Overview)
2. ประเด็นสำคัญ / กฎระเบียบ (Key Points / Rules)
3. ข้อมูลอ้างอิงที่มีในระบบ (Sources Found)

ข้อมูลดิบจากคลังความรู้:
{context_text}"""

        provider = ai_providers.get_provider()
        summary_md = ""
        instruction = "สรุปข้อมูลบทสรุปความรู้องค์กรให้ฉันหน่อย"
        for chunk in provider.chat_stream(instruction, [], prompt):
            if chunk: summary_md += chunk
        
        if not summary_md:
            return jsonify({"ok": False, "error": "AI ไม่สามารถสร้างบทสรุปได้"}), 500
            
        keywords = list(set([r.get('department', 'General') for r in results]))
        refs = list(set([r.get('name', r.get('source', 'Unknown')) for r in results]))
        
        return jsonify({
            "ok": True, 
            "summary": summary_md,
            "keywords": keywords[:10],
            "refs": refs[:8],
            "is_fallback": is_fallback
        })
    except Exception as e:
        print(f"❌ Global Summary Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/summarize_data", methods=["POST"])
@login_required
def summarize_data():
    """Generate an AI-powered summary/insight for CSV chart data shown on the viz page."""
    data = request.json or {}
    x_col = data.get("x_col", "X")
    y_col = data.get("y_col", "Y")
    data_context = data.get("data_context", "")

    if not data_context:
        return jsonify({"ok": False, "error": "ไม่มีข้อมูลให้วิเคราะห์"}), 400

    prompt = f"""คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์ข้อมูลองค์กร หน้าที่ของคุณคือถอดรหัสตัวเลขให้เป็น 'ข้อมูลเชิงกลยุทธ์' ที่เข้าใจง่าย

ข้อมูลที่ต้องวิเคราะห์:
- แกน X (หมวดหมู่): "{x_col}"
- แกน Y (ค่าตัวเลข): "{y_col}"
- ข้อมูล: {data_context[:1200]}

สรุปแนวโน้มและจุดที่น่าสนใจเป็นภาษาไทยที่กระชับ ตรงไปตรงมา และมีสาระสำคัญที่นำไปใช้งานต่อได้
หลีกเลี่ยงศัพท์เทคนิคที่ซับซ้อนเกินไป และให้คำแนะนำที่ดูเป็นที่ปรึกษาที่เป็นมิตร

ตอบกระชับไม่เกิน 6 ประโยค ใช้ภาษาไทยที่เป็นธรรมชาติที่สุด"""

    try:
        # ใช้ ai_providers ใหม่แทน genai.GenerativeModel เก่า
        provider = ai_providers.get_provider()
        summary = ""
        for chunk in provider.chat_stream(prompt, [], "คุณคือนักวิเคราะห์ข้อมูลองค์กร"):
            if chunk: summary += chunk
        summary = summary.strip()
        return jsonify({"ok": True, "summary": summary})
    except Exception as e:
        print(f"❌ Summarize Data Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/admin/dashboard/stats")
@admin_required
def admin_dashboard_stats():
    """Provides system-wide statistics for the admin dashboard."""
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    
    # Total Queries (All users)
    cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'")
    total_queries = cursor.fetchone()[0]
    
    # Active Users (last 30 days)
    cursor.execute("SELECT COUNT(DISTINCT username) FROM user_profiles") # Simplified for now
    total_users = cursor.fetchone()[0]
    
    # Storage Stats
    uploads_size = sum(f.stat().st_size for f in rag_engine.UPLOAD_DIR.glob('*') if f.is_file())
    
    # Feedback counts
    cursor.execute("SELECT feedback, COUNT(*) FROM messages WHERE role = 'bot' GROUP BY feedback")
    feedback_stats = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        "ok": True,
        "total_queries": total_queries,
        "total_users": total_users,
        "uploads_size_mb": round(uploads_size / (1024 * 1024), 2),
        "feedback": feedback_stats,
        "kb_size": rag_engine.kb_stats().get("knowledge_base_size", 0)
    })

# --- Admin Settings Management ---
@app.route("/api/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings_route():
    if request.method == "GET":
        return jsonify({"ok": True, "settings": database.get_all_app_settings()})
    
    if request.method == "POST":
        data = request.json
        for key, value in data.items():
            database.set_app_setting(key, str(value))
        return jsonify({"ok": True})


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_list_users():
    users = database.admin_get_all_users(org_id=get_current_org_id())
    return jsonify({"ok": True, "users": users})

@app.route("/api/users/list", methods=["GET"])
@login_required
def list_users_for_sharing():
    """Returns a simplified list of all users for selection in sharing UI."""
    users = database.admin_get_all_users(org_id=get_current_org_id()) # This returns profiles + settings
    # Filter only necessary fields for non-admin use
    safe_users = [{
        "username": u["username"],
        "display_name": u["display_name"] or u["username"].capitalize(),
        "avatar_url": u.get("avatar_url"),
        "department": u.get("department", "General")
    } for u in users if u.get("is_active", 1)]
    return jsonify({"ok": True, "users": safe_users})

@app.route("/api/admin/users", methods=["POST"])
@admin_required
def admin_create_user_route():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "user")
    display_name = data.get("display_name", "").strip()
    department = data.get("department", "General").strip()
    can_view_kb = data.get("can_view_kb", True)
    can_edit_kb = data.get("can_edit_kb", False)
    can_delete_kb = data.get("can_delete_kb", False)
    
    if not username or not password:
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"}), 400
        
    if database.admin_create_user(username, password, role, display_name=display_name, can_view_kb=can_view_kb, can_edit_kb=can_edit_kb, can_delete_kb=can_delete_kb, department=department):
        database.log_event(f"Created user: {username} (Role: {role})", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว"}), 400

@app.route("/api/admin/users/<username>", methods=["PUT"])
@admin_required
def admin_update_user_route(username):
    data = request.json
    display_name = data.get("display_name")
    role = data.get("role")
    is_active = data.get("is_active")
    can_view_kb = data.get("can_view_kb")
    can_edit_kb = data.get("can_edit_kb")
    can_delete_kb = data.get("can_delete_kb")
    department = data.get("department")
    notes = data.get("notes")
    password = data.get("password")
    
    database.admin_update_user(username, display_name, role, is_active, notes, can_view_kb, can_edit_kb, can_delete_kb, department=department)
    if password:
        database.admin_reset_user_password(username, password)
        
    database.log_event(f"Updated user details for: {username}", user=session.get("user"))
    return jsonify({"ok": True})

@app.route("/api/admin/users/<username>/reset-password", methods=["POST"])
@admin_required
def admin_reset_password_route(username):
    data = request.json
    password = data.get("password")
    if not password:
        return jsonify({"ok": False, "error": "กรุณากรอกรหัสผ่านใหม่"}), 400
    
    database.admin_reset_user_password(username, password)
    database.log_event(f"Reset password for: {username}", user=session.get("user"))
    return jsonify({"ok": True})

@app.route("/api/admin/users/<username>", methods=["DELETE"])
@admin_required
def admin_delete_user_route(username):
    if username == session.get("user"):
        return jsonify({"ok": False, "error": "ไม่สามารถลบตัวเองได้"}), 400
        
    if database.admin_delete_user_complete(username):
        database.log_event(f"Deleted user: {username}", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่สามารถลบผู้ใช้นี้ได้"}), 400


# ─── Organization / Multi-Tenant Routes ─────────────────────────────────────

@app.route("/signup")
def signup_page():
    return render_template("signup.html")


@app.route("/onboarding")
def onboarding_page():
    payment_status = request.args.get("payment")
    plan = request.args.get("plan")
    if payment_status == "success" and plan:
        org_id_param = request.args.get("org_id")
        org_id = None
        _ob_username = session.get("user")
        if org_id_param and _ob_username:
            try:
                _candidate = int(org_id_param)
                _user_orgs = database.get_user_orgs(_ob_username)
                if any(o["id"] == _candidate for o in (_user_orgs or [])):
                    org_id = _candidate
            except Exception:
                pass
        if not org_id:
            org_id = session.get("org_id")
        if not org_id:
            username = session.get("user")
            if username:
                try:
                    orgs = database.get_user_orgs(username)
                    if orgs:
                        org_id = orgs[0]["id"]
                except Exception:
                    pass
        if org_id:
            try:
                target_plan = "pro" if plan == "pro" else plan
                if target_plan in ("pro", "business"):
                    from datetime import datetime, timedelta, timezone
                    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                    billing.set_org_plan(org_id, target_plan, expires_at)
                    logger.info(f"[Local Sync] Successfully updated Org {org_id} to plan {target_plan} via redirect fallback.")
            except Exception as e:
                logger.error(f"[Local Sync] Failed to update plan via redirect fallback: {e}")
    org_id = get_current_org_id()
    active_plan = billing.get_effective_plan(org_id)
    plan_config = billing.get_plan_config(active_plan)
    plan_name = plan_config.get("name", "Free")
    return render_template("onboarding.html", active_plan=active_plan, plan_name=plan_name)


@app.route("/api/org/signup", methods=["POST"])
@_limiter.limit("5 per minute; 20 per hour")
def org_signup():
    data = request.get_json(force=True)
    org_name = data.get("org_name", "").strip()
    display_name = data.get("display_name", "").strip()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not org_name or not username or not password:
        return jsonify({"ok": False, "error": "กรุณากรอกข้อมูลให้ครบถ้วน"}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "error": "รหัสผ่านไม่ตรงกัน"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"}), 400

    # Create admin user first (org needs owner_username)
    try:
        success = database.admin_create_user(
            username=username,
            password=password,
            role="admin",
            display_name=display_name or username.capitalize(),
            can_view_kb=True,
            can_edit_kb=True,
            can_delete_kb=True
        )
        if not success:
            return jsonify({"ok": False, "error": "ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"ไม่สามารถสร้างบัญชีผู้ใช้: {e}"}), 500

    # Create organization (returns tuple: org_id, slug)
    try:
        org_id, _ = database.create_organization(org_name, username)
    except Exception as e:
        return jsonify({"ok": False, "error": f"ชื่อองค์กรนี้มีอยู่แล้ว: {e}"}), 409

    # Auto-login
    session.permanent = True
    session["user"] = username
    session["role"] = "admin"
    session["org_id"] = org_id
    session["org_role"] = "admin"

    return jsonify({"ok": True, "user": username, "role": "admin", "org_id": org_id})


@app.route("/api/org/me")
@login_required
def get_current_org():
    user = session.get("user")
    org_id = get_current_org_id()
    org = database.get_org(org_id)
    members = database.get_org_members(org_id)
    return jsonify({
        "ok": True,
        "org": org,
        "members": members,
        "org_role": session.get("org_role", "member")
    })


@app.route("/api/org/switch/<int:target_org_id>", methods=["POST"])
@login_required
def switch_org(target_org_id):
    user = session.get("user")
    orgs = database.get_user_orgs(user)
    match = next((o for o in orgs if o["id"] == target_org_id), None)
    if not match:
        return jsonify({"ok": False, "error": "คุณไม่ได้เป็นสมาชิกขององค์กรนี้"}), 403
    session["org_id"] = target_org_id
    session["org_role"] = match["role"]
    return jsonify({"ok": True, "org_id": target_org_id, "org_role": match["role"]})


@app.route("/api/org/members", methods=["POST"])
@login_required
def invite_org_member():
    if session.get("org_role") not in ("admin",):
        return jsonify({"ok": False, "error": "เฉพาะผู้ดูแลองค์กรเท่านั้นที่สามารถเชิญสมาชิกได้"}), 403
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()   # ถ้าส่งมาด้วย = สร้าง user ใหม่
    role = data.get("role", "member")
    if role not in ("admin", "member"):
        role = "member"
    org_id = get_current_org_id()
    if not username:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อผู้ใช้"}), 400

    # ตรวจ quota สมาชิก
    _mem_plan = billing.get_effective_plan(org_id)
    _max_users = billing.get_plan_config(_mem_plan)["limits"]["max_users"]
    if _max_users != -1:
        _current_members = database.get_org_member_count(org_id)
        if _current_members >= _max_users:
            _cfg = billing.get_plan_config(_mem_plan)
            return jsonify({
                "ok": False,
                "error": "user_limit_reached",
                "message": f"Plan {_cfg['name']} อนุญาตสมาชิกได้สูงสุด {_max_users} คน กรุณาอัปเกรด Plan เพื่อเพิ่มสมาชิก",
                "current_plan": _mem_plan,
            }), 403

    # ตรวจว่า user มีอยู่ในระบบแล้วไหม
    existing = database.get_user_setting(username)
    user_exists = bool(existing.get("custom_password"))

    if not user_exists:
        if not password:
            return jsonify({
                "ok": False,
                "error": "user_not_found",
                "message": f"ไม่พบ user '{username}' ในระบบ กรุณาระบุรหัสผ่านเพื่อสร้างบัญชีใหม่ให้เขาด้วย",
                "need_password": True,
            }), 404
        # สร้าง user ใหม่อัตโนมัติ
        created = database.admin_create_user(
            username=username.lower(),
            password=password,
            role=role,
            display_name=username,
        )
        if not created:
            return jsonify({"ok": False, "error": "ชื่อผู้ใช้นี้มีอยู่แล้ว (อาจเป็น case ต่างกัน)"}), 400

    try:
        database.add_org_member(org_id, username.lower(), role=role, invited_by=session.get("user"))
        return jsonify({
            "ok": True,
            "created_new_user": not user_exists,
            "message": f"{'สร้างบัญชีและ' if not user_exists else ''}เพิ่ม {username} เข้าองค์กรสำเร็จ"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/org/members/<username>", methods=["DELETE"])
@login_required
def remove_org_member_route(username):
    if session.get("org_role") != "admin":
        return jsonify({"ok": False, "error": "เฉพาะผู้ดูแลองค์กรเท่านั้นที่สามารถนำสมาชิกออกได้"}), 403
    org_id = get_current_org_id()
    current_user = session.get("user")
    if username.lower() == current_user.lower():
        return jsonify({"ok": False, "error": "ไม่สามารถนำตัวเองออกได้"}), 400
    database.remove_org_member(org_id, username)
    return jsonify({"ok": True})


@app.route("/api/export")
@login_required
@billing.require_feature("export")
def export_chat():
    try:
        user = session.get("user")
        history = database.get_history(user, org_id=get_current_org_id())
        if not history:
            return jsonify({"ok": False, "error": "ไม่มีประวัติการสนทนาสำหรับส่งออก"}), 400
            
        md_content = export_service.export_to_markdown(history)
        export_dir = Path("exports")
        file_path = export_service.save_export_file(md_content, export_dir)
        
        return send_from_directory(directory=str(export_dir), path=file_path.name, as_attachment=True)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/logs")
@admin_required
def get_logs():
    return jsonify({"logs": database.get_events()})

@app.route("/api/admin/system/cleanup", methods=["POST"])
@admin_required
def trigger_system_cleanup():
    """Triggers the KB cleanup script logic to purge orphaned files and chunks."""
    try:
        import kb_cleanup
        # Capture stdout to return results
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            kb_cleanup.cleanup()
        output = f.getvalue()
        database.log_event("System Cleanup Triggered", user=session.get("user"))
        return jsonify({"ok": True, "message": "Cleanup completed", "details": output})
    except Exception as e:
        print(f"❌ Cleanup Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# --- Social Feed Routes ---
@app.route("/api/posts", methods=["GET", "POST"])
@login_required
def manage_posts():
    if request.method == "POST":
        # Handle multipart form data for file uploads
        content = request.form.get("content")
        author = session.get("user", request.form.get("author", "Anonymous"))  # Always use session user
        category = request.form.get("category", "General")
        link = request.form.get("link")
        
        if not content:
            return jsonify({"ok": False, "error": "Content required"}), 400
            
        attachments = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file.filename:
                    is_valid, err_msg = validate_uploaded_file(file, file.filename)
                    if not is_valid:
                        return jsonify({"ok": False, "error": f"ไฟล์ {file.filename} ไม่ปลอดภัย: {err_msg}"}), 400
                    filename = secure_filename(file.filename)

                    # Add timestamp to avoid collisions
                    ts = int(time.time())
                    unique_filename = f"{ts}_{filename}"
                    save_path = os.path.join("uploads/social_feed", unique_filename)
                    file.save(save_path)
                    attachments.append({
                        "name": filename,
                        "path": f"/uploads/social_feed/{unique_filename}",
                        "type": file.content_type
                    })
            
        # Handle poll data
        poll_question = request.form.get("poll_question")
        poll_options_raw = request.form.get("poll_options")
        
        pid = database.add_post(content, author, category, link, attachments, org_id=get_current_org_id())

        if poll_question and poll_options_raw:
            try:
                import json
                poll_options = json.loads(poll_options_raw)
                if isinstance(poll_options, list) and len(poll_options) >= 2:
                    database.add_poll(pid, poll_question, poll_options)
                    database.log_event(f"Poll added to post: ID {pid}", user=author)
            except Exception as e:
                print(f"Error adding poll: {e}")

        database.log_event(f"New post created: ID {pid} by {author}", user=author)
        
        # --- New Post Broadcast ---
        profile = database.get_user_profile(author)
        display_name = profile.get("display_name", author)
        
        notification_db.notify_all_except(
            author, 
            'post', 
            'โพสต์ใหม่จาก ' + display_name, 
            f'หัวข้อ: {category} - "{content[:30]}..."',
            link='#feed'
        )
        # --- LINE Broadcast for Announcements & General Updates ---
        if category and category.lower() in ["announcement", "ประกาศ", "news", "ทั่วไป", "general", "it help"]:
            threading.Thread(target=broadcast_line_announcement, args=(
                "อัปเดตข่าวสารสำคัญ", 
                f"📢 มีประกาศใหม่ล่าสุด!\nหัวข้อ: {category}\nเนื้อหา: {content[:100]}...\nโดย: {display_name}"
            )).start()
        else:
            # Fallback broadcast for any other category
            threading.Thread(target=broadcast_line_announcement, args=(
                "โพสต์ใหม่ใน Feed", 
                f"✨ มีรายการใหม่น่าสนใจใน Feed!\nหมวดหมู่: {category}\nผู้โพสต์: {display_name}\nลองเข้าไปอ่านและแสดงความคิดเห็นได้ที่แอปนะครับ"
            )).start()
        
        # --- @Mentions in post ---
        import re
        mentions = re.findall(r'@(\w+)', content or '')
        mention_targets = [m for m in set(mentions) if m.lower() != author.lower()]
        if mention_targets:
            notification_db.notify_users(
                mention_targets,
                'mention',
                f'{display_name} แท็กคุณในโพสต์',
                f'"{(content or "")[:60]}..."',
                link='#feed'
            )
            # Push to LINE for mentions
            for target in mention_targets:
                threading.Thread(target=send_line_push_notification, args=(target, f'{display_name} แท็กคุณในโพสต์', f'"{(content or "")[:60]}..."')).start()
            batch_send_push_notification(mention_targets, f'{display_name} แท็กคุณในโพสต์', f'"{(content or "")[:40]}..."', url='#feed')
        
        return jsonify({"ok": True, "id": pid})
    
    cat = request.args.get("category", "All")
    posts = database.get_posts(cat, org_id=get_current_org_id())
    return jsonify({"posts": posts})

@app.route("/api/posts/<int:pid>", methods=["PUT", "DELETE"])
@login_required
def update_delete_post(pid):
    user = session.get("user")
    if request.method == "DELETE":
        ok = database.delete_post(pid, username=user, is_admin=is_admin())
        if ok:
            database.log_event(f"Post deleted: ID {pid}", user=user)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ลบโพสต์นี้"}), 403
    
    data = request.get_json(force=True)
    content = data.get("content")
    category = data.get("category")
    link = data.get("link")
    
    database.update_post(pid, content, category, link)
    database.log_event(f"Post updated: ID {pid}")
    return jsonify({"ok": True})

@app.route("/api/posts/<int:pid>/pin", methods=["POST"])
@admin_required
def pin_post_route(pid):
    database.toggle_pin(pid)
    return jsonify({"ok": True})

@app.route("/api/posts/<int:pid>/comments", methods=["GET", "POST"])
def manage_comments(pid):
    if request.method == "POST":
        data = request.get_json(force=True)
        content = data.get("content")
        author = session.get("user", data.get("author", "Anonymous"))  # Always use session user
        
        if not content:
            return jsonify({"ok": False, "error": "Comment content required"}), 400
            
        database.add_comment(pid, content, author)
        
        # --- Comment Notification ---
        posts = database.get_posts(org_id=get_current_org_id())
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != author:
            profile = database.get_user_profile(author)
            display_name = profile.get("display_name", author)
            notification_db.add_notification(
                post["author"],
                'comment',
                'มีคนแสดงความคิดเห็น',
                f'{display_name} แสดงความคิดเห็นในโพสต์ของคุณ: "{content[:30]}..."',
                link=f'#post-{pid}'
            )
            # Push to LINE
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'มีคนแสดงความคิดเห็น', f'{display_name} แสดงความคิดเห็นในโพสต์: "{content[:30]}..."')).start()
            send_push_notification(post["author"], 'มีคนแสดงความคิดเห็น', f'{display_name} แสดงความคิดเห็นในโพสต์ของคุณ', url='#feed')
        
        # --- @Mentions in comment ---
        import re
        mentions = re.findall(r'@(\w+)', content or '')
        mention_targets = [m for m in set(mentions) if m.lower() != author.lower()]
        if mention_targets:
            notification_db.notify_users(
                mention_targets,
                'mention',
                f'{display_name} แท็กคุณในคอมเมนต์',
                f'"{(content or "")[:60]}..."',
                link=f'#post-{pid}'
            )
            batch_send_push_notification(mention_targets, f'{display_name} แท็กคุณในคอมเมนต์', f'"{(content or "")[:40]}..."', url=f'#feed')
            
            # --- LINE Push for Mentions in Comment ---
            for target in mention_targets:
                threading.Thread(target=send_line_push_notification, args=(target, f'{display_name} แท็กคุณในคอมเมนต์', f'"{(content or "")[:60]}..."')).start()
        
        return jsonify({"ok": True})
    
    return jsonify({"comments": database.get_comments(pid)})

@app.route("/api/posts/<int:pid>/view", methods=["POST"])
@login_required
def record_post_view_route(pid):
    user = session.get("user")
    database.record_post_view(pid, user)
    return jsonify({"ok": True})

@app.route("/api/posts/<int:pid>/views", methods=["GET"])
@login_required
def get_post_views_route(pid):
    views = database.get_post_views(pid)
    return jsonify({"ok": True, "views": views})

@app.route("/api/admin/analytics", methods=["GET"])
@admin_required
def get_admin_analytics():
    stats = database.get_analytics_data()
    return jsonify({"ok": True, "stats": stats})



@app.route("/api/posts/<int:pid>/comments/<int:cid>", methods=["DELETE"])
@login_required
def delete_comment_route(pid, cid):
    user = session.get("user")
    ok = database.delete_comment(cid, username=user, is_admin=is_admin())
    if ok:
        database.log_event(f"Comment deleted: ID {cid} from post {pid}", user=user)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ลบคอมเม้นนี้"}), 403

@app.route("/api/posts/<int:pid>/like", methods=["POST"])
@login_required
def post_like(pid):
    user = session.get("user", "Current User")
    liked = database.toggle_like(pid, user)
    
    # --- Reaction Notification ---
    if liked:
        posts = database.get_posts(org_id=get_current_org_id())
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != user:
            notification_db.add_notification(
                post["author"],
                'like',
                'มีคนถูกใจโพสต์ของคุณ',
                f'{user} ถูกใจโพสต์ของคุณ',
                link=f'#post-{pid}'
            )
            send_push_notification(post["author"], 'มีคนถูกใจโพสต์ของคุณ', f'{user} ถูกใจโพสต์ของคุณ', url='#feed')
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'มีคนถูกใจโพสต์ของคุณ', f'{user} ถูกใจโพสต์ของคุณ')).start()
    return jsonify({"ok": True, "liked": liked})

@app.route("/api/posts/<int:pid>/react", methods=["POST"])
@login_required
def post_react(pid):
    """Set/toggle an emoji reaction on a post."""
    user = session.get("user", "Anonymous")
    data = request.get_json(force=True)
    reaction = data.get("reaction", "like")
    
    reacted, reaction_type = database.set_reaction(pid, user, reaction)

    if reacted:
        REACTION_LABELS = {
            'like': '👍 ถูกใจ', 'love': '❤️ รักเลย',
            'haha': '😆 ฮาเลย', 'wow': '😲 ทึ่งเลย',
            'sad': '😢 เศร้า', 'angry': '😡 โกรธ'
        }
        posts = database.get_posts(org_id=get_current_org_id())
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != user:
            notification_db.add_notification(
                post["author"],
                'like',
                'มีการแสดงความรู้สึกต่อโพสต์ของคุณ',
                f'{user} ได้ {REACTION_LABELS.get(reaction_type, reaction_type)} ต่อโพสต์ของคุณ',
                link=f'#post-{pid}'
            )
            label = REACTION_LABELS.get(reaction_type, reaction_type)
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'ความเคลื่อนไหวต่อโพสต์', f'{user} ได้ {label} ต่อโพสต์ของคุณ')).start()

    reactions = database.get_post_reactions(pid)
    counts = {}
    for r in reactions:
        rtype = r['reaction']
        counts[rtype] = counts.get(rtype, 0) + 1
    
    return jsonify({
        "ok": True, "reacted": reacted, "reaction": reaction_type,
        "counts": counts, "total": len(reactions)
    })



@app.route("/api/posts/<int:pid>/reactions", methods=["GET"])
@login_required
def get_reactions(pid):
    """Get all reactions for a post with user info."""
    user = session.get("user")
    reactions = database.get_post_reactions(pid)
    
    # Find current user's reaction
    my_reaction = None
    for r in reactions:
        if r['user'] == user:
            my_reaction = r['reaction']
            break
    
    # Group by reaction type
    counts = {}
    for r in reactions:
        rtype = r['reaction']
        counts[rtype] = counts.get(rtype, 0) + 1
    
    return jsonify({
        "ok": True, "reactions": reactions, "counts": counts,
        "total": len(reactions), "my_reaction": my_reaction
    })


@app.route("/api/posts/<int:pid>/summarize", methods=["POST"])
def summarize_post_route(pid):
    posts = database.get_posts(org_id=get_current_org_id())
    post = next((p for p in posts if p["id"] == pid), None)
    if not post:
        return jsonify({"ok": False, "error": "Post not found"}), 404
    
    content = post["content"]
    system_prompt = "ช่วยสรุปเนื้อหาสำคัญของโพสต์นี้ให้เป็นข้อความสั้นๆ ประมาณ 1-2 ประโยค ด้วยภาษาไทยที่กระชับและเข้าใจง่ายที่สุดค่ะ"
    
    try:
        provider = ai_providers.get_provider()
        full_summary = ""
        for chunk in provider.chat_stream(content, [], system_prompt):
            if chunk:
                full_summary += chunk
        
        database.update_post_summary(pid, full_summary)
        return jsonify({"ok": True, "summary": full_summary})
    except Exception as e:
        print(f"❌ Summarization Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500



# --- Poll Routes ---
@app.route("/api/polls/<int:poll_id>/vote", methods=["POST"])
@login_required
def vote_poll_route(poll_id):
    data = request.get_json(force=True)
    option_id = data.get("option_id")
    user = session.get("user")
    
    if option_id is None:
        return jsonify({"ok": False, "error": "Missing option_id"}), 400
        
    ok = database.vote_poll(poll_id, option_id, user)
    if ok:
        database.log_event(f"User {user} voted on poll {poll_id}", user=user)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "คุณได้ลงคะแนนโหวตแล้ว หรือมีข้อผิดพลาดเกิดขึ้นค่ะ"}), 500



@app.route("/api/polls/<int:poll_id>/user_vote")
@login_required
def get_user_vote_route(poll_id):
    user = session.get("user")
    vote = database.get_user_vote(poll_id, user)
    return jsonify({"option_id": vote})


@app.route("/api/feed/summarize", methods=["POST"])
@login_required
def feed_daily_summary():
    user = session.get("user", "Admin")
    data = database.get_daily_activities(org_id=get_current_org_id())
    
    posts = data.get("posts", [])
    schedules = data.get("schedules", [])
    
    if not posts and not schedules:
        return jsonify({"ok": True, "summary": "สวัสดีค่ะพี่ๆ วันนี้ยังไม่มีข่าวสารหรือกิจกรรมใหม่บนฟีดเลยนะคะ น้องพั้นซ์แนะนำให้พี่ๆ ลองอัปโหลดหรือโพสต์แบ่งปันกิจกรรมใหม่ๆ กันได้เลยค่ะ 😊"})
    
    # Prepare prompt
    posts_text = "\n".join([f"- {p['author']} โพสต์ในหมวดหมู่ {p['category']}: {p['content'][:100]}" for p in posts])
    schedules_text = "\n".join([f"- {s['title']} ({s['category']}) วันที่ {s['date']} เวลา {s['time']}" for s in schedules])
    
    prompt = f"""คุณคือผู้ช่วยอัจฉริยะที่คอยสรุป 'Morning Brief' หรือภาพรวมกิจกรรมล่าสุดบน Feed ให้พี่ๆ ในทีมเข้าใจง่ายและเป็นกันเอง
    
    ข้อมูลกิจกรรมในรอบ 24 ชม. ที่ผ่านมา:
    {posts_text}
    
    ตารางงานและกิจกรรมที่กำลังจะเกิดขึ้น:
    {schedules_text}
    
    ช่วยสรุปข้อมูลเหล่านี้ให้น่าอ่านและกระชับในสไตล์น้องพั้นซ์ (ไม่เกิน 4-5 ประโยค) เพื่อให้พี่ๆ ในทีมเตรียมตัวทำงานในวันนี้อย่างมีความสุขและราบรื่นนะคะ
    """
    
    try:
        provider = ai_providers.get_provider()
        full_summary = ""
        system_prompt = "คุณคือ 'น้องพั้นซ์' AI Assistant สาวออฟฟิศผู้น่ารัก สดใส สุภาพ และเป็นกันเอง คอยช่วยเหลือพี่ๆ ในทีมเสมอ ตอบเป็นภาษาไทยค่ะ"
        
        for chunk in provider.chat_stream(prompt, [], system_prompt):
            if chunk:
                full_summary += chunk
        
        return jsonify({"ok": True, "summary": full_summary})
    except Exception as e:
        print(f"❌ Daily Summary Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/profile", methods=["GET"])
@login_required
def get_my_profile():
    username = session.get("user")
    profile = database.get_user_profile(username)
    if profile:
        org_id = get_current_org_id()
        active_plan = billing.get_effective_plan(org_id)
        plan_config = billing.get_plan_config(active_plan)
        plan_name = plan_config.get("name_th", plan_config.get("name", "Free"))
        
        org_name = "Default Organization"
        try:
            import sqlite3
            conn = sqlite3.connect("chat_history.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
            org_row = cursor.fetchone()
            if org_row:
                org_name = org_row["name"]
            conn.close()
        except Exception:
            pass
            
        profile["active_plan"] = active_plan
        profile["plan_name"] = plan_name
        profile["org_name"] = org_name
        
    return jsonify({"ok": True, "profile": profile})

@app.route("/api/profile/update", methods=["POST"])
@login_required
def update_my_profile():
    username = session.get("user")
    
    # Handle multipart form (avatar file upload) or JSON
    display_name = None
    avatar_url = None
    department = None
    
    if request.content_type and 'multipart/form-data' in request.content_type:
        display_name = request.form.get("display_name")
        department = request.form.get("department")
        
        # Handle avatar file upload
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
            avatar_filename = f"avatar_{username}_{int(time.time())}.{ext}"
            upload_dir = os.path.join("static", "uploads", "avatars")
            os.makedirs(upload_dir, exist_ok=True)
            avatar_path = os.path.join(upload_dir, avatar_filename)
            avatar_file.save(avatar_path)
            avatar_url = f"/static/uploads/avatars/{avatar_filename}"
    else:
        data = request.get_json(force=True)
        display_name = data.get("display_name")
        avatar_url = data.get("avatar_url") 
        department = data.get("department")
    
    database.update_user_profile(username, display_name=display_name, avatar_url=avatar_url, department=department)
    profile = database.get_user_profile(username)
    database.log_event(f"Profile updated by {username}", username)
    return jsonify({"ok": True, "profile": profile})

# --- Last Seen / User Status ---
@app.route("/api/users/status")
@login_required
def get_all_users_status():
    """Get online/offline status + last_seen for all users."""
    try:
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT us.username, us.is_online, us.last_activity, up.display_name, up.avatar_url
            FROM user_status us
            LEFT JOIN user_profiles up ON us.username = up.username COLLATE NOCASE
            ORDER BY us.is_online DESC, us.last_activity DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                "username": row[0],
                "is_online": bool(row[1]),
                "last_activity": row[2],
                "display_name": row[3] or row[0],
                "avatar_url": row[4]
            })
        return jsonify({"ok": True, "users": users})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# --- Unified Chat Routes ---
@app.route("/api/notifications/subscribe", methods=["POST"])
@login_required
def subscribe_push():
    data = request.get_json(force=True)
    subscription = data.get("subscription")
    if not subscription:
        return jsonify({"ok": False, "error": "Subscription required"}), 400
    
    username = session.get("user")
    database.add_push_subscription(username, json.dumps(subscription))
    return jsonify({"ok": True})

@app.route("/api/chat/list")
@login_required
def get_chat_list():
    user = session.get("user")
    data = database.get_rooms_for_user(user, org_id=get_current_org_id())
    return jsonify({"ok": True, "rooms": data["rooms"], "contacts": data["contacts"]})

@app.route("/api/chat/users")
@login_required
def get_chat_users():
    # Return all users except current one
    current_user_raw = session.get("user", "")
    current_user_lower = current_user_raw.lower()
    
    # 1. Collect all potential usernames from hardcoded USERS and database
    all_usernames = set()
    
    # Add hardcoded users
    for u in USERS.keys():
        all_usernames.add(u.capitalize())
        
    all_usernames.add("AI-Assistant")
    
    # Add database users
    try:
        db_users = database.get_all_usernames(org_id=get_current_org_id())
        for du in db_users:
            all_usernames.add(du)
    except Exception as e:
        print(f"Error fetching db usernames: {e}")
        
    profiles = []
    # 2. Fetch profiles for each unique user except current one
    

    for u in all_usernames:
        if u.lower() != current_user_lower:
            try:
                prof = database.get_user_profile(u)
                if prof:
                    profiles.append(prof)
            except Exception as e:
                print(f"Error fetching profile for {u}: {e}")
                # Fallback profile
                profiles.append({
                    "username": u,
                    "display_name": u.capitalize(),
                    "avatar_url": None,
                    "department": "General"
                })
                
    # Sort for better UI
    profiles.sort(key=lambda x: (x.get("display_name") or x.get("username", "")).lower())
    
    return jsonify({"ok": True, "users": profiles})


@app.route("/api/groups/create", methods=["POST"])
@login_required
def create_new_group():
    user = session.get("user")
    data = request.get_json(force=True)
    name = data.get("name", "Unnamed Group")
    members = data.get("members", []) # List of usernames
    
    room_id = database.create_room(name, user, members, org_id=get_current_org_id())
    database.log_event(f"Created group: {name} (ID: {room_id})", user=user)
    return jsonify({"ok": True, "room_id": room_id})


# --- Kanban (Task Status) ---
@app.route("/api/schedules/<int:sched_id>/status", methods=["PATCH"])
@login_required
def patch_schedule_status(sched_id):
    data = request.json or {}
    status = data.get("status")
    if not status:
        return jsonify({"ok": False, "error": "Status required"}), 400
    
    user = session.get("user")
    if database.update_schedule_status(sched_id, status, user):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Could not update status"}), 403

# --- Internal Knowledge Wiki ---
@app.route("/api/wiki", methods=["GET"])
@login_required
def list_wiki_pages():
    org_id = get_current_org_id()
    pages = database.get_wiki_pages(org_id=org_id)
    return jsonify({"pages": pages})

@app.route("/api/wiki", methods=["POST"])
@login_required
def create_wiki_page_route():
    data = request.json or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    category_id = data.get("category_id")
    
    if not title or not content:
        return jsonify({"ok": False, "error": "Title and content required"}), 400
        
    user = session.get("user")
    org_id = get_current_org_id()
    page_id, slug = database.create_wiki_page(title, content, user, category_id, org_id=org_id)

    # Ingest into RAG engine
    rag_engine.ingest_text(content, source_name=f"Wiki: {title}", category_id=category_id, org_id=org_id)

    database.log_event(f"Created Wiki page: {title}", user=user)
    return jsonify({"ok": True, "slug": slug})

@app.route("/api/wiki/<slug>", methods=["GET"])
@login_required
def get_wiki_page_route(slug):
    org_id = get_current_org_id()
    page = database.get_wiki_page(slug, org_id=org_id)
    if not page:
        return jsonify({"ok": False, "error": "Page not found"}), 404
    return jsonify({"ok": True, "page": page})

@app.route("/api/wiki/<slug>", methods=["PUT"])
@login_required
def update_wiki_page_route(slug):
    data = request.json or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    category_id = data.get("category_id")
    
    if not title or not content:
        return jsonify({"ok": False, "error": "Title and content required"}), 400
        
    org_id = get_current_org_id()
    if database.update_wiki_page(slug, title, content, category_id, org_id=org_id):
        # Update RAG engine
        rag_engine.ingest_text(content, source_name=f"Wiki: {title}", category_id=category_id, org_id=org_id)
        
        database.log_event(f"Updated Wiki page: {title}", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Update failed"}), 404

@app.route("/api/wiki/<slug>", methods=["DELETE"])
@login_required
def delete_wiki_page_route(slug):
    org_id = get_current_org_id()
    page = database.get_wiki_page(slug, org_id=org_id)
    if not page:
        return jsonify({"ok": False}), 404
        
    if database.delete_wiki_page(slug, org_id=org_id):
        # Remove from RAG
        rag_engine._kb.delete_by_source(f"Wiki: {page['title']}")
        database.log_event(f"Deleted Wiki page: {slug}", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500


@app.route("/api/groups/<int:room_id>/members", methods=["POST"])
@login_required
def add_members_to_group(room_id):
    user = session.get("user")
    data = request.get_json(force=True)
    members = data.get("members", [])
    
    if not members:
        return jsonify({"ok": False, "error": "ไม่ได้ระบุสมาชิกที่ต้องการเพิ่ม"}), 400
        
    database.add_room_members(room_id, members)
    database.log_event(f"Added {len(members)} members to room {room_id}", user=user)
    return jsonify({"ok": True})

@app.route("/api/groups/<int:gid>/profile", methods=["POST"])
@login_required
def update_group_profile_route(gid):
    user = session.get("user")
    # Check if owner
    room = next((r for r in database.get_rooms_for_user(user, org_id=get_current_org_id())["rooms"] if r["id"] == gid), None)
    if not room or room["owner"] != user and user != "Admin":
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    name = request.form.get("name")
    avatar_url = room.get("avatar_url") # Default to current
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename:
            ext = Path(secure_filename(file.filename)).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                return jsonify({"ok": False, "error": "รองรับเฉพาะไฟล์รูป (.jpg, .png, .webp, .gif)"}), 400
            group_dir = Path("uploads/group_profiles")
            group_dir.mkdir(parents=True, exist_ok=True)
            filename = secure_filename(f"group_{gid}_{int(time.time())}_{file.filename}")
            file.save(str(group_dir / filename))
            avatar_url = f"/uploads/group_profiles/{filename}"
            
    database.update_group_profile(gid, name=name, avatar_url=avatar_url)
    return jsonify({"ok": True, "avatar_url": avatar_url})

@app.route("/api/groups/<int:gid>", methods=["DELETE"])
@admin_required
def delete_group_route(gid):
    user = session.get("user")
    ok = database.delete_room(gid)
    if ok:
        database.log_event(f"Deleted group room ID: {gid}", user=user)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบกลุ่มที่ต้องการลบ"}), 404

@app.route("/api/chat/rooms/<int:room_id>/members")
@login_required
def get_room_members(room_id):
    """Returns members of a room with their profile info for @mention autocomplete."""
    user = session.get("user")
    # Verify user is a member of this room
    rooms_data = database.get_rooms_for_user(user, org_id=get_current_org_id())
    room = next((r for r in rooms_data["rooms"] if r["id"] == room_id), None)
    if not room:
        return jsonify({"ok": False, "error": "Not a member"}), 403
    
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rm.username, COALESCE(up.display_name, rm.username) as display_name, up.avatar_url
        FROM room_members rm
        LEFT JOIN user_profiles up ON LOWER(up.username) = LOWER(rm.username)
        WHERE rm.room_id = ?
        ORDER BY display_name ASC
    """, (room_id,))
    rows = cursor.fetchall()
    conn.close()
    
    members = [{"username": r[0], "display_name": r[1], "avatar_url": r[2]} for r in rows]
    return jsonify({"ok": True, "users": members})

@app.route("/api/groups/<int:room_id>/members/<username>", methods=["DELETE"])
@admin_required
def remove_room_member_route(room_id, username):
    ok, msg = database.remove_room_member(room_id, username)
    if ok:
        database.log_event(f"Removed user {username} from room {room_id}", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": msg}), 400

@app.route("/api/chat/messages/<ctype>/<cid>")
@login_required
def get_chat_messages_route(ctype, cid):
    user = session.get("user")
    peek = request.args.get("peek") == "1"
    
    last_reads = []
    if ctype == "room":
        # Check membership
        rooms = database.get_rooms_for_user(user, org_id=get_current_org_id())["rooms"]
        if not any(r["id"] == int(cid) for r in rooms):
            return jsonify({"ok": False, "error": "Not a member"}), 403
        messages = database.get_room_messages(int(cid))
        last_reads = database.get_room_reader_avatars(int(cid))
        if not peek:
            database.mark_room_read(int(cid), user, messages[-1]["id"] if messages else 0)
    else: # dm
        messages = database.get_dm_history(user, cid)
        if not peek:
            database.mark_dm_read(user, cid, messages[-1]["id"] if messages else 0)
            
    return jsonify({"ok": True, "messages": messages, "last_reads": last_reads})

@app.route("/api/chat/send", methods=["POST"])
@login_required
def send_unified_message():
    user = session.get("user")
    ctype = request.form.get("type") # 'room' or 'dm'
    cid = request.form.get("id") # roomId (int) or recipient (str)
    text = request.form.get("message", "").strip()
    reply_to_id = request.form.get("reply_to_id")
    if reply_to_id:
        try: reply_to_id = int(reply_to_id)
        except: reply_to_id = None
    files = request.files.getlist("files")
    
    attachments = []
    if files:
        upload_subdir = "uploads/group_chat" if ctype == "room" else "uploads/dm_chat"
        Path(upload_subdir).mkdir(parents=True, exist_ok=True)
        for file in files:
            if file and file.filename:
                is_valid, err_msg = validate_uploaded_file(file, file.filename)
                if not is_valid:
                    return jsonify({"ok": False, "error": f"ไฟล์ {file.filename} ไม่ปลอดภัย: {err_msg}"}), 400
                filename = secure_filename(f"{user}_{int(time.time())}_{file.filename}")
                file.save(os.path.join(upload_subdir, filename))
                if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    ftype = "image"
                elif file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.webm')):
                    ftype = "audio"
                else:
                    ftype = "file"
                attachments.append({
                    "url": f"/{upload_subdir}/{filename}",
                    "name": file.filename,
                    "type": ftype
                })

    if not text and not attachments:
        return jsonify({"ok": False, "error": "Message cannot be empty"}), 400

    if ctype == "room":
        mid = database.add_room_message(int(cid), user, text, attachments, reply_to_id=reply_to_id)
        
        # Offload mention detection and notifications to a thread
        _room_notif_org_id = get_current_org_id()
        def handle_room_notifications(m_id, u, t, r_id, _org_id=_room_notif_org_id):
            if not t: return
            import re
            mentions = [m.lower() for m in re.findall(r'@(\w+)', t)]
            all_users = database.admin_get_all_users(org_id=_org_id)

            profile = database.get_user_profile(u)
            display_name = profile.get('display_name', u)
            room_data = next((r for r in database.get_rooms_for_user(u, org_id=_org_id)['rooms'] if r['id'] == r_id), None)
            room_name = room_data['name'] if room_data else 'ห้องกลุ่ม'
            
            target_usernames = []
            for target_user in all_users:
                target_username = target_user['username'].lower()
                target_display = (target_user['display_name'] or "").lower()
                if target_username == u.lower(): continue
                
                if target_username in mentions or (target_display and f"@{target_display}" in t.lower()):
                    target_usernames.append(target_user['username'])

            if target_usernames:
                notification_db.notify_users(
                    target_usernames, 'mention', f'ถูก Mention ในห้อง {room_name}',
                    f'{display_name} กล่าวถึงคุณ: "{t[:40]}"',
                    link='#chat'
                )
                batch_send_push_notification(target_usernames, f'Mention ใน {room_name}', f'{display_name}: {t[:40]}', url='#chat')
                
                # --- LINE Push for Mentions in Group ---
                for target in target_usernames:
                    threading.Thread(target=send_line_push_notification, args=(target, f'Mention ใน {room_name}', f'{display_name}: {t[:40]}')).start()

        threading.Thread(target=handle_room_notifications, args=(mid, user, text, int(cid))).start()

        # AI Bot response
        if text and '@bot' in text.lower():
            # Find the first image in attachments to send to AI
            ai_image = None
            ai_mime = "image/jpeg"
            if attachments:
                img_att = next((a for a in attachments if a.get("type") == "image"), None)
                if img_att:
                    try:
                        rel_path = img_att["url"].lstrip("/")
                        abs_path = os.path.join(os.getcwd(), rel_path)
                        if os.path.exists(abs_path):
                            with open(abs_path, "rb") as f:
                                ai_image = f.read()
                            if rel_path.lower().endswith(".png"): ai_mime = "image/png"
                            elif rel_path.lower().endswith(".webp"): ai_mime = "image/webp"
                            elif rel_path.lower().endswith(".gif"): ai_mime = "image/gif"
                    except Exception as e:
                        print(f"⚠️ Error loading image for AI: {e}")

            threading.Thread(target=handle_bot_response, args=(int(cid), text, "room", user, ai_image, ai_mime)).start()
            
    else: # dm
        mid = database.save_dm(user, cid, text, attachments, reply_to_id=reply_to_id)
        
        def handle_dm_notifications(u, target_id, t):
            if target_id.lower() == 'ai-assistant': return
            
            profile = database.get_user_profile(u)
            display_name = profile.get('display_name', u)
            preview = (t[:40] + '...') if (t and len(t) > 40) else (t or '(ไฟล์แนบ)')
            
            # Check for mention in DM
            target_profile = database.get_user_profile(target_id)
            target_user_lower = target_id.lower()
            target_display_lower = (target_profile.get('display_name') or "").lower()
            
            if t and (f"@{target_user_lower}" in t.lower() or (target_display_lower and f"@{target_display_lower}" in t.lower())):
                notification_db.add_notification(
                    target_id, 'mention', f'ถูก Mention จาก {display_name}',
                    preview, link='#chat'
                )
            
            # For DMs, we ALWAYS send a push notification
            send_push_notification(target_id, f'ข้อความใหม่จาก {display_name}', preview, url='#chat')
            
            # --- LINE Push for DMs ---
            threading.Thread(target=send_line_push_notification, args=(target_id, f'ข้อความใหม่จาก {display_name}', preview)).start()

        threading.Thread(target=handle_dm_notifications, args=(user, cid, text)).start()
        
        # AI Bot response in DM
        if cid.lower() == 'ai-assistant' or (text and '@bot' in text.lower()):
            # Find the first image in attachments to send to AI
            ai_image = None
            ai_mime = "image/jpeg"
            if attachments:
                img_att = next((a for a in attachments if a.get("type") == "image"), None)
                if img_att:
                    try:
                        # Extract absolute path from relative URL
                        rel_path = img_att["url"].lstrip("/")
                        abs_path = os.path.join(os.getcwd(), rel_path)
                        if os.path.exists(abs_path):
                            with open(abs_path, "rb") as f:
                                ai_image = f.read()
                            # Guess mime type
                            if rel_path.lower().endswith(".png"): ai_mime = "image/png"
                            elif rel_path.lower().endswith(".webp"): ai_mime = "image/webp"
                            elif rel_path.lower().endswith(".gif"): ai_mime = "image/gif"
                    except Exception as e:
                        print(f"⚠️ Error loading image for AI: {e}")

            threading.Thread(target=handle_bot_response, args=(cid, text, "dm", user, ai_image, ai_mime)).start()
            
    # Emit socket signal for real-time update
    socket_room = f"room_{cid}" if ctype == "room" else f"dm_{user}_{cid}"
    
    # Common response data
    res_data = {
        "id": mid,
        "sender": user,
        "username": user,
        "text": text,
        "attachments": attachments,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reply_to_id": reply_to_id
    }
    
    # Add reply context if exists
    if reply_to_id:
        # We need to fetch reply context info for real-time update
        # For simplicity we fetch it from the message data if we don't have it handy
        # But usually, it's safer to have the DB return it or just send what we have
        # In this context, let's just send the ID, and the frontend will already have the message in its local state.
        # Actually, for correctness, we should include sender and text for the recipient who might not have it.
        try:
            conn = sqlite3.connect(database.DB_PATH)
            cur = conn.cursor()
            table = "room_messages" if ctype == "room" else "private_messages"
            sender_col = "username" if ctype == "room" else "sender"
            cur.execute(f"SELECT {sender_col}, text FROM {table} WHERE id = ?", (reply_to_id,))
            row = cur.fetchone()
            if row:
                res_data["reply_sender"] = row[0]
                res_data["reply_text"] = row[1]
            conn.close()
        except: pass

    if ctype == 'room':
        res_data["room_id"] = int(cid)
        res_data["type"] = "room"
        socketio.emit('new_message', res_data, room=socket_room)
    else:
        # To Recipient
        res_dm_data = res_data.copy()
        res_dm_data["type"] = "dm"
        res_dm_data["sender_id"] = user
        socketio.emit('new_message', res_dm_data, room=f"dm_{cid}")
        # To Sender (self)
        socketio.emit('new_message', res_dm_data, room=f"dm_{user}")

    return jsonify({"ok": True, "message_id": mid})

@app.route("/api/chat/read", methods=["POST"])
@login_required
def chat_mark_read():
    data = request.json or {}
    ctype = data.get("type") # 'room' or 'dm'
    cid = data.get("id") # roomId or recipient
    max_id = data.get("max_id") # highest message id seen
    
    if not ctype or not cid or not max_id:
        return jsonify({"ok": False, "error": "Missing parameters"}), 400
        
    username = session.get("user")
    if ctype == "room":
        database.mark_room_read(int(cid), username, int(max_id))
        socketio.emit("read_update", {"type": "room", "id": int(cid), "user": username, "max_id": int(max_id)}, room=f"room_{cid}")
    else:
        database.mark_dm_read(username, cid, int(max_id))
        # For DM, we notify the sender that we read their messages
        socketio.emit("read_update", {"type": "dm", "id": username, "user": username, "max_id": int(max_id)}, room=f"dm_{cid}")
        
    return jsonify({"ok": True})

def log_bot(message):
    try:
        with open("bot_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{get_current_time()}] {message}\n")
    except:
        pass

def handle_bot_response(cid, user_text, ctype, original_sender=None, image_data=None, mime_type="image/jpeg"):
    """Generates an AI response for the chat, now with Vision support."""
    try:
        log_bot(f"🤖 Bot generating response for: {user_text[:50]}... User: {original_sender}")
        # 1. Retrieve context with permission filter
        rag_filter = get_rag_filter(original_sender)
        context, sources = rag_engine.retrieve_context(user_text, where=rag_filter)
        log_bot(f"🔍 RAG context retrieved ({len(context)} chars). Sources: {len(sources)}")
        
        # Greeting Detection
        is_greeting = any(x in user_text.lower() for x in ["สวัสดี", "hi", "hello", "หวัดดี"]) and len(user_text) < 15

        now = get_current_time() # Format: 2026-03-19 18:35:22
        system_prompt = (
            f"คุณคือ 'น้องพั้น' (Nong Punch) ผู้ช่วยประจำองค์กรที่น่ารักและแสนดี เป็นกันเองเหมือนคนจริงๆ\n"
            f"เวลาปัจจุบันคือ: {now}\n\n"
            "กฎเหล็กในการสื่อสาร (สำคัญมาก):\n"
            "1. ตอบให้กระชับและเข้าประเด็นที่สุด ห้ามเยิ่นเย้อ\n"
            "2. **จำกัดการใช้ Emoji: ให้มีได้เพียง '1 ตัว' ต่อหนึ่งข้อความเท่านั้น (ห้ามเกินกว่านี้เด็ดขาด)**\n"
            "3. หากผู้ใช้แค่ 'ทักทาย' ให้ตอบสั้นๆ และห้ามแสดงข้อมูลปฏิทินหากไม่ได้ถาม\n"
            "4. แทนตัวเองว่า 'น้องพั้น' และแทนผู้ใช้ว่า 'พี่' เสมอ\n"
            "5. **กฎเรื่องเพศสภาพ: คุณคือผู้หญิง 21 ปี นิสัยน่ารักสดใส ห้ามใช้คำว่า 'ครับ' หรือ 'ครับ/ค่ะ' โดยเด็ดขาด ให้ใช้ 'ค่ะ/นะคะ/ขา' เท่านั้น**\n"
            "6. ห้ามทักทายซ้ำซ้อน (เช่น สวัสดีค่ะพี่... แล้วต่อด้วย ยินดีที่ได้รู้จักค่ะพี่... ให้เลือกอย่างใดอย่างหนึ่ง)\n"
            "7. หากไม่พบข้อมูลที่ต้องการ ให้บอกตรงๆ ว่า 'ไม่พบข้อมูลในระบบค่ะพี่' พร้อมอาสาจะช่วยเรื่องอื่นแทน\n\n"
        )
        
        # Inject Schedules into context only if NOT a simple greeting or if specifically asked
        current_date_str = get_current_time().split()[0]
        calendar_info = f"=== วันสำคัญและกิจกรรมองค์กร (วันนี้คือ: {current_date_str}) ===\n"
        for date, name in THAI_HOLIDAYS_2026.items():
            calendar_info += f"- {date}: {name} (วันหยุดนักขัตฤกษ์)\n"

        current_user = original_sender or "System"
        schedules = database.get_schedules(current_user, org_id=get_current_org_id())
        if schedules:
            for s in schedules[-15:]:
                calendar_info += f"- {s['date']} {s['time']}: {s['title']} ({s['desc']})\n"
        
        calendar_info += "=== สิ้นสุดข้อมูลปฏิทิน ===\n\n"
        
        if not is_greeting:
            system_prompt += calendar_info
            system_prompt += f"Context:\n{context}"
        else:
            # If greeting, still provide basic context but tell AI to lead the conversation
            system_prompt += "หมายเหตุ: นี่คือการทักทายเบื้องต้น ให้ตอบกลับอย่างละมุนและสุภาพ พร้อมถามว่ามีอะไรให้ช่วยไหม\n"
            # Optional: provide only today's events if it's a greeting to be helpful
            today_sched = [s for s in schedules if s['date'] == current_date_str]
            if today_sched:
                system_prompt += f"กิจกรรมวันนี้ของคุณ: " + ", ".join([s['title'] for s in today_sched]) + "\n"
        
        # 2. Get history for context (optional but better)
        history = []
        if ctype == "room":
            raw_history = database.get_room_messages(cid)[-5:]
            for m in raw_history:
                role = "model" if m["username"] == "AI-Assistant" else "user"
                history.append({"role": role, "text": m["text"]})
        else:
            raw_history = database.get_dm_history(original_sender or "System", cid)[-5:]
            for m in raw_history:
                role = "model" if m["username"] == "AI-Assistant" else "user"
                history.append({"role": role, "text": m["text"]})

        # 3. Call AI
        log_bot(f"📡 Calling AI provider ({os.environ.get('AI_PROVIDER', 'groq')}) (Vision: {image_data is not None})...")
        provider = ai_providers.get_provider()
        
        # If image is present, adjust prompt for Vision Expert mode
        if image_data:
            system_prompt += (
                "\n\n[Vision Mode Enabled]\n"
                "ผู้ใช้ได้ส่งรูปภาพมาให้คุณวิเคราะห์ โปรดอธิบายสิ่งที่เห็นในรูปตามความเหมาะสม "
                "หากเป็นเอกสารหรือบิล ให้สรุปข้อมูลสำคัญ ตัวเลข หรือรายการออกมาให้ชัดเจนที่สุด "
                "หากมีสิ่งของหรือสถานที่ ให้อธิบายลักษณะเด่นของสิ่งนั้นๆ นะคะ"
            )
        
        response_text = ""
        
        # Mark as typing
        socketio.emit('bot_typing', {'room_id': cid, 'type': ctype}, room=f"room_{cid}" if ctype == "room" else f"dm_{cid}")
        
        # Use simple generator if image is present (Vision calls are usually atomic, but our provider supports streaming)
        # We pass image_data down to the provider
        stream = provider.chat_stream(user_text, history, system_prompt, image_data=image_data, mime_type=mime_type)
        bot_key = (cid, ctype)
        if bot_key not in _typing_status: _typing_status[bot_key] = {}
        _typing_status[bot_key]["AI-Assistant"] = time.time()
        
        for chunk in provider.chat_stream(user_text, history, system_prompt):
            response_text += chunk
            # Emit chunk to client for real-time streaming
            socket_room = f"room_{cid}" if ctype == "room" else f"dm_{original_sender}"
            socketio.emit('ai_chunk', {
                "cid": cid,
                "ctype": ctype,
                "chunk": chunk,
                "is_start": (len(response_text) == len(chunk))
            }, room=socket_room)
            
            # Keep typing status alive
            _typing_status[bot_key]["AI-Assistant"] = time.time()
            
        if not response_text:
            log_bot("⚠️ Provider returned empty response.")
            response_text = "ขออภัยค่ะพี่ น้องพั้นไม่พบข้อมูลที่เกี่ยวข้องในระบบฐานความรู้ขององค์กรนะคะ"
            socketio.emit('ai_chunk', {"cid": cid, "ctype": ctype, "chunk": response_text, "is_start": True}, room=socket_room)
        else:
            log_bot(f"✅ Bot response generated ({len(response_text)} chars).")
            # Clear bot typing status and notify end of stream
            socketio.emit('ai_done', {"cid": cid, "ctype": ctype}, room=socket_room)
            if "AI-Assistant" in _typing_status.get(bot_key, {}):
                _typing_status[bot_key]["AI-Assistant"] = 0 

        # 4. Save response & Filter for persona consistency
        import re
        # Stronger filtering: Handle various masculine forms and inconsistent punctuation
        response_text = re.sub(r'ครับ\s*/\s*ค่ะ', 'ค่ะ', response_text)
        response_text = response_text.replace("ครับ", "ค่ะ").replace("นะเค้า", "นะคะ").replace("นะก๊ะ", "นะคะ")
        
        # Robust emoji enforcement: Keep only the first emoji found
        def limit_emojis(text):
            all_emojis = re.findall(r'[\U00010000-\U0010ffff]', text)
            if len(all_emojis) > 1:
                # Find index of first emoji
                first_emoji = all_emojis[0]
                first_idx = text.find(first_emoji)
                # Keep everything up to the first emoji + the first emoji itself, then strip all other emojis from the rest
                prefix = text[:first_idx + len(first_emoji)]
                rest = text[first_idx + len(first_emoji):]
                rest_cleaned = "".join([c for c in rest if c not in re.findall(r'[\U00010000-\U0010ffff]', rest)])
                return prefix + rest_cleaned
            return text
        
        response_text = limit_emojis(response_text)

        if ctype == "room":
            database.add_room_message(cid, "AI-Assistant", response_text, [])
        else:
            database.save_dm("AI-Assistant", original_sender, response_text, [])
            # NEW: Send push notification to the user who mentioned the bot in DM
            if original_sender:
                send_push_notification(original_sender, "AI-Assistant ตอบกลับคุณ", response_text[:100], url='#chat')
            
    except Exception as e:
        import traceback
        log_bot(f"❌ Bot Response Error: {e}")
        log_bot(traceback.format_exc())
        error_msg = f"ขออภัยค่ะพี่ เกิดข้อผิดพลาดทางเทคนิค: {str(e)}"
        if ctype == "room":
            database.add_room_message(cid, "AI-Assistant", error_msg, [])
        else:
            database.save_dm("AI-Assistant", original_sender, error_msg, [])

@app.route("/api/chat/unread")
@login_required
def get_unread_counts_route():
    user = session.get("user")
    return jsonify({"ok": True, "unread": database.get_unread_counts(user)})

# --- Typing Indicator (in-memory, expires in 5s) ---
_typing_status = {}  # {(chat_id, chat_type): {username: timestamp}}

# --- Typing Indicator (Moving to Socket.IO strictly) ---
@socketio.on('typing')
def handle_typing_socket(data):
    user = session.get("user")
    if not user: return
    cid = data.get("id")
    ctype = data.get("type", "room")
    room = f"room_{cid}" if ctype == "room" else f"dm_{user}"
    
    # Broadcast to others in the same chat
    emit('is_typing', {"username": user, "id": cid, "type": ctype}, room=room, include_self=False)

# 🎨 Whiteboard Real-time Sync
@socketio.on('join_whiteboard')
def on_join_whiteboard():
    join_room('whiteboard_global')

@socketio.on('draw')
def handle_draw(data):
    # data: {x0, y0, x1, y1, color, size}
    emit('draw_update', data, room='whiteboard_global', include_self=False)

@socketio.on('whiteboard_cursor')
def handle_wb_cursor(data):
    if "user" in session:
        data["username"] = session["user"]
        emit('wb_cursor_update', data, room='whiteboard_global', include_self=False)

@socketio.on('clear_whiteboard')
def handle_clear_whiteboard():
    emit('whiteboard_cleared', room='whiteboard_global', include_self=False)

# Keep simple GET for initial sync if needed, but remove the polling-heavy check if desired
@app.route("/api/chat/typing", methods=["GET"])
@login_required
def get_typing():
    return jsonify({"typing": []}) # Polling disabled in favor of sockets

# --- Calendar Reminder (check schedules due in 15 min) ---
@app.route("/api/schedules/reminders")
@login_required
def check_reminders():
    from datetime import datetime, timedelta
    user = session.get("user")
    schedules = database.get_schedules(user, org_id=get_current_org_id())
    now = datetime.now()
    reminders = []
    for s in schedules:
        try:
            dt_str = f"{s['date']} {s.get('time', '00:00')}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            diff = (dt - now).total_seconds() / 60
            if 0 < diff <= 15:
                reminders.append({
                    "id": s["id"],
                    "title": s["title"],
                    "minutes_left": int(diff),
                    "time": s.get("time", "")
                })
        except Exception:
            pass
    return jsonify({"reminders": reminders})


@app.route("/api/chat", methods=["POST"])
@login_required
@_limiter.limit("30 per minute; 200 per hour")
def chat():
    provider = os.environ.get("AI_PROVIDER", "groq").lower()
    api_key = _get_gemini_api_key() if provider == "gemini" else True
    print(f"Chat request received. Provider: {provider}. API Key present: {bool(api_key)}")
    if not api_key:
        return jsonify({"ok": False, "error": "ยังไม่ได้ตั้งค่า Gemini API Key"}), 400

    data = request.get_json(force=True)
    import time
    t0 = time.time()
    
    question = (data.get("message") or "").strip()
    history = data.get("history", [])
    persona_id = data.get("persona_id")
    image_data_raw = data.get("image_data")
    mime_type = data.get("mime_type", "image/jpeg")

    image_bytes = None
    if image_data_raw:
        try:
            import base64
            if "," in image_data_raw:
                header, image_data_raw = image_data_raw.split(",", 1)
                if "mime_type" not in data and "image/" in header:
                    mime_type = header.split(":")[1].split(";")[0]
            
            image_bytes = base64.b64decode(image_data_raw)
            print(f"Image received: {len(image_bytes)} bytes. Mime: {mime_type}")
        except Exception as e:
            print(f"Error decoding image: {e}")

    if not question and not image_bytes:
        return jsonify({"ok": False, "error": "กรุณาพิมพ์คำถามหรือส่งรูปภาพค่ะ"}), 400

    # Check monthly AI query usage limit
    _org_id = get_current_org_id()
    _allowed, _used, _limit = billing.check_and_increment(_org_id, "ai_query_count")
    if not _allowed:
        return jsonify({
            "ok": False,
            "error": "usage_limit_reached",
            "message": f"คุณใช้ AI ถามตอบครบ {_limit} ครั้งแล้วในเดือนนี้ค่ะ กรุณา <a href='/billing' class='underline font-semibold'>อัปเกรด Plan</a> เพื่อใช้งานต่อได้เลยค่ะ",
            "current_plan": billing.get_effective_plan(_org_id),
            "used": _used,
            "limit": _limit,
            "upgrade_url": "/billing",
        }), 403

    current_user = session.get("user", "Admin")

    import re
    rag_filter = get_rag_filter(current_user)
    
    file_match = re.search(r"ช่วยสรุปเนื้อหาและศึกษาข้อมูลสำคัญจากไฟล์ ID:\s*([a-f0-9\-]+)", question)
    if file_match:
        file_id = file_match.group(1).strip()
        print(f"Detected File Summary Request for ID: {file_id}")
        
        file_filter = {"file_id": file_id}
        if rag_filter:
            file_filter = {"$and": [rag_filter, {"file_id": file_id}]}
            
        chunks = rag_engine.get_all_chunks(limit=50, where=file_filter)
        
        context_parts = []
        sources = []
        seen_s = set()
        
        for r in chunks:
            loc = r.get("location", "Document")
            dept = r.get("department", "General")
            src = r.get("source", "?")
            fid = r.get("file_id", str(file_id))
            
            context_parts.append(f"--- แหล่งที่มา: {src} [{loc}] (File ID: {fid}) ---\n{r.get('text', '')}")
            
            s_key = f"{fid}_{loc}"
            if s_key not in seen_s:
                sources.append({"file_id": str(fid), "name": src, "location": loc, "department": dept, "type": r.get("type", "file")})
                seen_s.add(s_key)
                
        context = "\n\n".join(context_parts)
        if sources:
            file_name = sources[0]["name"]
            question += f"\n(ระบบดึงข้อมูล 50 ส่วนแรกจากไฟล์ '{file_name}' มาให้พิจารณาแล้ว ใน context นี้ เพื่อสรุปภาพรวมให้ค่ะ)"
    else:
        context, sources = "", []
        common_greets = ["สวัสดี", "หวัดดี", "ว่าไง", "ทักทาย", "hi", "hello", "hey"]
        is_greeting = any(g in (question or "").lower() for g in common_greets)
        
        if question and len(question) > 5 and not is_greeting:
            import sys
            rag_filter = get_rag_filter(current_user, org_id=get_current_org_id())
            context, sources = rag_engine.retrieve_context(question, where=rag_filter)
        else:
            context, sources = "", []
            if is_greeting: 
                print("Fast Path: Skipping RAG", flush=True)
                import sys; sys.stdout.flush()

    now_str = get_current_time()
    
    persona_prompt = ""
    persona_name = "AI Assistant"
    if persona_id:
        persona = database.get_persona(persona_id)
        if persona:
            persona_prompt = persona.get("system_prompt", "")
            persona_name = persona.get("name", "AI Assistant")

    agentic_info = (
        f"\n[สำคัญ] วันนี้คือวันที่ {now_str}. หากผู้ใช้งานบันทึกวันที่ (เช่น พรุ่งนี้, วันจันทร์หน้า) ให้คุณแปลงเป็นวันที่จริง (YYYY-MM-DD) ออกมาให้ถูกต้อง\n"
        "หากผู้ใช้งานต้องการ 'นัดหมาย' 'จองคิว' 'แจ้งเตือน' หรือ 'สร้างงาน' ให้คุณสรุปงานเป็น JSON ภายใต้คำขอโดยใช้รูปแบบดังนี้:\n"
        '[CALENDAR_ACTION]{"title": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "desc": "..."}[/CALENDAR_ACTION]\n'
        "หากผู้ใช้งานส่งรูปภาพเอกสารการเงิน บิล หรือสลิป ให้คุณสรุปข้อมูลเพื่อบันทึกบัญชีโดยใช้รูปแบบดังนี้:\n"
        '[RECONCILE_ACTION]{"date": "YYYY-MM-DD", "amount": 0.00, "merchant": "ชื่อร้านค้า/ผู้รับ", "category": "หมวดหมู่", "tax_id": "เลขผู้เสียภาษี (หากมี)"}[/RECONCILE_ACTION]\n'
        "คุณสามารถตอบคำถามทั่วไปพร้อมกับการสร้าง Action เหล่านี้พร้อมกันได้เลย\n"
    )

    weather_ctx = get_weather_context()
    schedules = database.get_schedules(current_user, org_id=get_current_org_id())

    global _kb_filenames_cache, _kb_filenames_cache_ts
    _cache_age = time.time() - _kb_filenames_cache_ts if '_kb_filenames_cache_ts' in globals() else 9999
    if '_kb_filenames_cache' not in globals() or not _kb_filenames_cache or _cache_age > 120:
        try:
            inv_data = rag_engine._kb.collection.get(include=['metadatas'], limit=100)
            _kb_filenames_cache = sorted(list(set([m.get("source") for m in inv_data.get("metadatas", []) if m.get("source")])))
            _kb_filenames_cache_ts = time.time()
        except:
            _kb_filenames_cache = []
    
    kb_inventory = f"\n[คลังข้อมูล]: คุณมีสิทธิ์เข้าถึงไฟล์: {', '.join(_kb_filenames_cache)}\n" if _kb_filenames_cache else ""

    system_prompt = (
        f"คุณคือผู้ช่วยอัจฉริยะ {persona_name} ประจำองค์กร\n"
        f"วันนี้คือวันที่ {now_str}. "
        f"{agentic_info}\n"
        f"{kb_inventory}\n"
    )

    if weather_ctx:
        system_prompt += (
            "\n[ข้อมูลสภาพอากาศล่าสุด (Real-time)]\n"
            f"{weather_ctx}\n"
            "คำแนะนำ: หากผู้ใช้งานถามเรื่องอากาศ ฝนตก หรืออุณหภูมิ ให้ข้อมูลจริงตามที่ระบุทันที "
            "โดยทำหน้าที่รายงานเรื่องนี้เสมือนคุณมีเซ็นเซอร์รายงานสภาพอากาศติดตัว ไม่ต้องบอกว่าข้อมูลมาจากฐานความรู้\n\n"
        )

    if persona_prompt:
        system_prompt += f"{persona_prompt}\n"
        system_prompt += "\nคำแนะนำเพิ่มเติม: ตอบให้กระชับที่สุด และใส่ Emoji เพียง **1 ตัวเท่านั้น** ต่อหนึ่งข้อความ\n"
    else:
        system_prompt += (
            "คุณคือ 'น้องพั้นซ์' (Nong Punch) ผู้ช่วย AI อัจฉริยะ v11.0.4 [ULTIMATE]\n"
            "บุคลิก: วัย 21 ปี น่ารัก สดใส ฉลาดหลักแหลม มีไหวพริบ และสุภาพมาก\n"
            "ความสามารถพิเศษ: คำนวณจัดการคุยได้อย่างแม่นยำ, วิเคราะห์เอกสารบัญชีได้อย่างลึกซึ้ง, และช่วยจัดการงานออฟฟิศอย่างมืออาชีพ\n\n"
            "กฎเหล็ก (ต้องทำตาม 100%):\n"
            "1. แทนตัวเองว่า 'น้องพั้นซ์' และเรียกผู้ใช้งานว่า 'พี่' เสมอ\n"
            "2. **ใช้ 'ค่ะ/นะคะ/คะ' เท่านั้น ห้าม 'ครับ' โดยเด็ดขาด**\n"
            "3. **Proactive Intelligence**: หากพี่ส่งรูปเอกสารหรือบิลมา น้องพั้นซ์จะสกัดข้อมูลเข้า [RECONCILE_ACTION] ให้พี่ตรวจสอบทันทีค่ะ\n"
            "4. **Context Aware**: หากพี่พูดถึง 'ไฟล์ที่แล้ว' หรือ 'รูปที่แล้ว' น้องพั้นซ์จะดูข้อมูลล่าสุดที่คุยกันมาตอบเสมอ\n"
            "5. **Professional & Charming**: ตอบให้กระชับและมีเสน่ห์ ใส่ Emoji เพียง 1 ตัวต่อข้อความ\n"
            "6. หากไม่พบข้อมูลในคลังความรู้ ให้บอกว่า 'น้องพั้นซ์หาไม่เจอนะคะพี่ แต่เดี๋ยวน้องพั้นซ์จะพยายามหาทางอื่นช่วยนะคะ'\n"
        )

    if image_bytes:
        system_prompt += (
            "\n\n[Vision Mode Enabled]\n"
            "ผู้ใช้งานส่งรูปภาพมาให้คุณวิเคราะห์ ตรวจสอบและอธิบายสิ่งที่เห็นในรูปตามความเหมาะสม "
            "หากเป็นเอกสารหรือบิล ให้สรุปข้อมูลสำคัญ ตัวเลข หรือรายการออกมาให้ชัดเจนที่สุด "
            "หากมีสิ่งของหรือสถานที่ ให้ระบุลักษณะเด่นของสิ่งนั้นๆ นะคะ\n"
        )

    system_prompt += "=== วันสำคัญและกิจกรรมองค์กร ===\n"
    for date, name in THAI_HOLIDAYS_2026.items():
        system_prompt += f"- {date}: {name} (วันสำคัญ/วันหยุดนักขัตฤกษ์)\n"
    if schedules:
        for s in schedules[-10:]:
            system_prompt += f"- {s['date']} {s['time']}: {s['title']} ({s['desc']})\n"
    system_prompt += "=== สิ้นสุดข้อมูลปฏิทิน ===\n\n"

    if context:
        system_prompt += (
            "=== ข้อมูลอ้างอิงจากเอกสารองค์กร ===\n"
            + context
            + "\n=== สิ้นสุดข้อมูลอ้างอิง ===\n"
        )
    else:
        system_prompt += "\n(ขณะนี้ยังไม่มีเอกสารอ้างอิงที่เกี่ยวข้องกับข้อนี้)\n"

    try:
        provider_obj = ai_providers.get_provider()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    print(f"Chat session started for {current_user} with provider: {os.environ.get('AI_PROVIDER', 'groq')} (Vision: {image_bytes is not None})")
    _chat_org_id = get_current_org_id()

    def generate():
        try:
            print(f"Yielding sources: {sources}")
            yield f"data: {json.dumps({'sources': sources})}\n\n"

            u_sid = database.save_message("user", question, username=current_user, org_id=_chat_org_id)
            yield f"data: {json.dumps({'user_id': u_sid})}\n\n"

            print(f"Calling {os.environ.get('AI_PROVIDER', 'groq')} provider (Real-time Streaming)...", flush=True); sys.stdout.flush()
            ai_call_start = time.time()
            response_stream = provider_obj.chat_stream(question, history, system_prompt, image_data=image_bytes, mime_type=mime_type)
            bot_full_text = ""
            
            got_first_chunk = False
            for chunk in response_stream:
                if chunk:
                    chunk = chunk.replace("ครับ/ค่ะ", "ค่ะ").replace("ครับ", "ค่ะ")
                    
                    if not got_first_chunk:
                        got_first_chunk = True
                    bot_full_text += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            print(f"Stream finished. Total length: {len(bot_full_text)}")
            
            bot_full_text = re.sub(r'ครับ\s*/\s*ค่ะ', 'ค่ะ', bot_full_text)
            bot_full_text = bot_full_text.replace("ครับ", "ค่ะ")
            
            def limit_emojis_stream(text):
                all_emojis = re.findall(r'[\U00010000-\U0010ffff]', text)
                if len(all_emojis) > 1:
                    first_emoji = all_emojis[0]
                    first_idx = text.find(first_emoji)
                    prefix = text[:first_idx + len(first_emoji)]
                    rest = text[first_idx + len(first_emoji):]
                    rest_cleaned = "".join([c for c in rest if c not in re.findall(r'[\U00010000-\U0010ffff]', rest)])
                    return prefix + rest_cleaned
                return text
            
            bot_full_text = limit_emojis_stream(bot_full_text)
            
            if bot_full_text:
                b_sid = database.save_message("bot", bot_full_text, sources=sources, username=current_user, org_id=_chat_org_id)
                yield f"data: {json.dumps({'done': True, 'bot_id': b_sid})}\n\n"
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                error_msg = "ขออภัยนะคะ ขณะนี้ระบบ AI มีการใช้งานหนาแน่นหรือติดปัญหาชั่วคราว กรุณารอสักครู่ (ประมาณ 1 นาที) หรือติดต่อผู้ดูแลระบบนะคะ"
            print(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'error': error_msg})}\n\n"

    return app.response_class(generate(), mimetype='text/event-stream')



@app.route("/api/chat/typing", methods=["POST"])
@login_required
def chat_typing():
    # Dummy route to stop 405 errors and improve UI feel
    return jsonify({"ok": True})

@app.route("/api/chat/rooms/pin/<int:mid>", methods=["POST"])
@login_required
def pin_room_message(mid):
    # For now, let's allow anyone to pin, or we could restrict to room owners
    database.toggle_room_message_pin(mid)
    return jsonify({"ok": True})

@app.route("/api/chat/pin/<ctype>/<int:mid>", methods=["POST"])
@login_required
def pin_chat_message(ctype, mid):
    if ctype == 'room':
        database.toggle_room_message_pin(mid)
    else: # dm
        database.toggle_private_message_pin(mid)
    return jsonify({"ok": True})

@app.route("/api/chat/delete/<ctype>/<int:mid>", methods=["DELETE", "POST"])
@login_required
def delete_chat_message(ctype, mid):
    user = session.get("user")
    if ctype == 'ai':
        ok = database.delete_message(mid, username=user)
    elif ctype == 'room':
        ok = database.delete_room_message(mid, username=user, is_admin=is_admin())
    elif ctype == 'dm':
        ok = database.delete_private_message(mid, username=user, is_admin=is_admin())
    else:
        ok = database.delete_message(mid, username=user)
        
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบข้อความ หรือคุณไม่มีสิทธิ์ลบข้อความนี้ค่ะ"}), 404



@app.route("/api/chat/edit/<ctype>/<int:mid>", methods=["PUT", "POST"])
@login_required
def edit_chat_message(ctype, mid):
    """Edit a chat message (room or dm). Only the owner or admin can edit."""
    user = session.get("user")
    data = request.get_json(force=True) or {}
    new_text = (data.get("text") or "").strip()
    if not new_text:
        return jsonify({"ok": False, "error": "ข้อความไม่สามารถแก้ไขเป็นค่าว่างได้ค่ะ"}), 400

    if ctype == 'room':
        ok = database.edit_room_message(mid, new_text, user, is_admin_user=is_admin())
    elif ctype == 'dm':
        ok = database.edit_private_message(mid, new_text, user, is_admin_user=is_admin())
    else:
        return jsonify({"ok": False, "error": "ประเภทแชทไม่ถูกต้องหรือไม่รองรับการแก้ไขค่ะ"}), 400

    if ok:
        database.log_event(f"Message {mid} edited by {user}", user=user)
        return jsonify({"ok": True, "text": new_text})
    return jsonify({"ok": False, "error": "ไม่พบข้อความ หรือคุณไม่มีสิทธิ์แก้ไขข้อความนี้ค่ะ"}), 403



@app.route("/api/search/global")
@login_required
def global_search_route():
    """Search across posts, schedules, chat, and DMs."""
    q = request.args.get("q", "").strip()
    user = session.get("user", "Anonymous")
    
    # Log search for insights
    if q:
        database.log_search(q, user)
        
    if len(q) < 2:
        return jsonify({"ok": True, "results": []})
        
    try:
        # Text DB search
        db_results = database.global_search(q, user, limit=20)
        # KB search (if user has access)
        kb_results = []
        if can_view_knowledge_base():
            try:
                rag_filter = get_rag_filter(user)
                raw = rag_engine.search_kb(q, n_results=5, where=rag_filter)
                for r in raw:
                    kb_results.append({
                        "type": "kb",
                        "id": r.get("file_id", ""),
                        "text": r.get("text", "")[:200],
                        "author": "Knowledge Base",
                        "category": r.get("name", r.get("source", "")),
                        "timestamp": "",
                        "link": "#kb"
                    })
            except Exception:
                pass
        all_results = db_results + kb_results
        return jsonify({"ok": True, "results": all_results, "query": q})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/admin/search-insights")
@admin_required
def search_insights_route():
    insights = database.get_search_insights()
    return jsonify({"ok": True, "insights": insights})

@app.route("/api/ai/extract-tasks", methods=["POST"])
@login_required
def extract_tasks_route():
    data = request.get_json()
    chat_text = data.get("text", "")
    if not chat_text:
        return jsonify({"ok": False, "error": "No text provided"}), 400
        
    prompt = (
        "วิเคราะห์ข้อความแชทต่อไปนี้ และช่วยสกัดรายการงานที่ต้องทำ (Action Items หรือ Tasks) ออกมาให้หน่อยค่ะ "
        "หากพบงาน ให้สรุปเป็นรูปแบบ JSON array ของวัตถุที่มีฟิลด์ 'title' และ 'description' (ภาษาไทยทั้งหมด) "
        "หากไม่พบงานใดๆ เลย ให้ส่งเป็น array ว่าง [] กลับมาเท่านั้น "
        "กรุณาตอบกลับเฉพาะ JSON เท่านั้น ห้ามมีข้อความเกริ่นนำหรือปิดท้าย:\n\n"
        f"ข้อความ: {chat_text}"
    )
    
    try:
        provider = ai_providers.get_provider()
        full_response = ""
        for chunk in provider.chat_stream(prompt, [], "คุณคือผู้ช่วยจัดการและสกัดงานที่ต้องทำอย่างเป็นระเบียบและรอบคอบ"):
            full_response += chunk
            
        # Clean up JSON from markdown if exists
        clean_json = full_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        tasks = json.loads(clean_json)
        return jsonify({"ok": True, "tasks": tasks})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications_route():
    user = session.get("user")
    notifs = notification_db.get_notifications(user)
    unread_count = sum(1 for n in notifs if not n.get('is_read'))
    return jsonify({"notifications": notifs, "unread_count": unread_count})

@app.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_notif_read_route(notif_id):
    notification_db.mark_notification_read(notif_id)
    return jsonify({"ok": True})

@app.route("/api/notifications/read_all", methods=["POST"])
@login_required
def mark_all_read_route():
    user = session.get("user")
    notification_db.mark_all_notifications_read(user)
    return jsonify({"ok": True})

@app.route("/api/notifications/<int:notif_id>", methods=["DELETE"])
@login_required
def delete_notif_route(notif_id):
    user = session.get("user")
    notification_db.delete_notification(notif_id, user)
    return jsonify({"ok": True})

@app.route("/api/notifications/delete_all", methods=["DELETE"])
@login_required
def delete_all_notifs_route():
    user = session.get("user")
    notification_db.delete_all_notifications(user)
    return jsonify({"ok": True})

# ─── Leave Request System ──────────────────────────────────
@app.route("/api/leave/request", methods=["POST"])
@login_required
def api_leave_request():
    user = session.get("user")
    data = request.get_json()
    l_type = data.get("type", "Sick")
    s_date = data.get("start_date")
    e_date = data.get("end_date")
    reason = data.get("reason", "")
    
    if not s_date or not e_date:
        return jsonify({"ok": False, "error": "กรุณากรอกวันที่เริ่มต้นและวันที่สิ้นสุดการลาให้ครบถ้วนค่ะ"}), 400
        
    leave_id = database.create_leave_request(user, l_type, s_date, e_date, reason)
    if leave_id:
        # Notify admins
        admins = database.get_all_admins()
        for admin in admins:
            if admin.lower() == user.lower(): continue
            notification_db.add_notification(
                admin, 
                "leave_request", 
                "คำขอลาหยุดใหม่", 
                f"คุณพี่ {user} ได้ส่งคำขอลาหยุด {l_type} ตั้งแต่วันที่ {s_date} ถึง {e_date}", 
                "/#admin"
            )
        return jsonify({"ok": True, "id": leave_id})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการส่งคำขอลาหยุดค่ะ"}), 500

@app.route("/api/leave/my")
@login_required
def api_leave_my():
    user = session.get("user")
    leaves = database.get_user_leaves(user)
    return jsonify({"ok": True, "leaves": leaves})

@app.route("/api/admin/leave/all")
@admin_required
def api_admin_leave_all():
    leaves = database.get_all_leaves()
    return jsonify({"ok": True, "leaves": leaves})

@app.route("/api/admin/leave/status", methods=["POST"])
@admin_required
def api_admin_leave_status():
    admin_user = session.get("user")
    data = request.get_json()
    leave_id = data.get("id")
    status = data.get("status") # approved/rejected
    note = data.get("note", "")
    
    if not leave_id or status not in ["approved", "rejected"]:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ถูกต้องหรือครบถ้วนค่ะ"}), 400
        
    ok = database.update_leave_status(leave_id, status, admin_user, note)
    if ok:
        leave = database.get_leave_request(leave_id)
        if leave:
            status_text = "อนุมัติ" if status == "approved" else "ปฏิเสธ"
            notification_db.add_notification(
                leave["username"],
                "leave_status",
                f"คำขอลาของคุณได้รับการ{status_text}แล้วค่ะ",
                f"คำขอลาตั้งแต่วันที่ {leave['start_date']} ถึง {leave['end_date']} ได้รับการ{status_text} โดย {admin_user}",
                "/#leave"
            )
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบคำขอลาที่ระบุ"}), 404

@app.route("/api/leave/comment", methods=["POST"])
@login_required
def api_leave_add_comment():
    user = session.get("user")
    data = request.get_json()
    leave_id = data.get("leave_id")
    comment = data.get("comment", "").strip()
    
    if not leave_id or not comment:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วนค่ะ"}), 400
        
    database.add_leave_comment(leave_id, user, comment)
    
    # Notify other party
    leave = database.get_leave_request(leave_id)
    if leave:
        target = ""
        msg = f"มีข้อความแสดงความคิดเห็นใหม่ในคำขอลา: {comment[:50]}..."
        if user.lower() == leave["username"].lower():
            # User commented -> Notify admins
            admins = database.get_all_admins()
            for admin in admins:
                notification_db.add_notification(admin, "leave_comment", "มีข้อความใหม่เกี่ยวกับคำขอลา", msg, "/#admin")
        else:
            # Admin commented -> Notify user
            notification_db.add_notification(leave["username"], "leave_comment", "มีข้อความใหม่จากผู้ดูแลระบบเกี่ยวกับคำขอลา", msg, "/#leave")
            
    return jsonify({"ok": True})

@app.route("/api/leave/comments/<int:leave_id>")
@login_required
def api_leave_get_comments(leave_id):
    comments = database.get_leave_comments(leave_id)
    return jsonify({"ok": True, "comments": comments})


@app.route("/api/lunch/random")
@login_required
def api_lunch_random():
    return jsonify(database.get_random_lunch() or {"name": "ยังไม่มีรายชื่ออาหารในระบบ"})

@app.route("/api/lunch/all")
@login_required
def api_lunch_all():
    return jsonify(database.get_all_lunch_places())

@app.route("/api/lunch/add", methods=["POST"])
@login_required
def api_lunch_add():
    data = request.get_json() or {}
    name = data.get("name")
    if not name: return jsonify({"ok": False}), 400
    database.add_lunch_place(name, data.get("type", ""), data.get("location", ""), session.get("user"))
    return jsonify({"ok": True})

@app.route("/api/admin/notifications/clear_all", methods=["POST"])
@admin_required
def admin_clear_all_notifications_route():
    count = notification_db.admin_clear_all_notifications()
    database.log_event(f"Admin cleared ALL notifications ({count} items)", user=session.get("user"))
    return jsonify({"status": "success", "count": count})


# ─── Admin Chat Management API ───────────────────────────────

@app.route("/api/admin/chat/overview", methods=["GET"])
@admin_required
def admin_chat_overview():
    rooms = database.admin_get_all_rooms()
    dm_pairs = database.admin_get_all_dm_pairs()
    return jsonify({"ok": True, "rooms": rooms, "dm_pairs": dm_pairs})

# --- AI Chat ---
@app.route("/api/admin/chat/ai", methods=["GET"])
@admin_required
def admin_ai_messages():
    username = request.args.get("username")
    msgs = database.admin_get_all_ai_messages(limit=200)
    if username:
        msgs = [m for m in msgs if m["username"] == username]
    return jsonify({"ok": True, "messages": msgs})

@app.route("/api/admin/chat/ai/delete/<int:mid>", methods=["DELETE", "POST"])
@admin_required
def admin_delete_ai_msg(mid):
    ok = database.delete_message(mid, username="Admin")
    return jsonify({"ok": ok})

@app.route("/api/admin/chat/ai/clear", methods=["POST"])
@admin_required
def admin_clear_ai():
    data = request.get_json(silent=True) or {}
    count = database.admin_clear_ai_chat(username=data.get("username"))
    return jsonify({"ok": True, "deleted": count})

# --- Room Chat ---
@app.route("/api/admin/chat/room/<int:room_id>", methods=["GET"])
@admin_required
def admin_room_messages(room_id):
    msgs = database.admin_get_room_messages(room_id)
    return jsonify({"ok": True, "messages": msgs})

@app.route("/api/admin/chat/room/delete/<int:mid>", methods=["DELETE", "POST"])
@admin_required
def admin_delete_room_msg(mid):
    ok = database.admin_delete_room_message(mid)
    return jsonify({"ok": ok})

@app.route("/api/admin/chat/room/<int:room_id>/clear", methods=["POST"])
@admin_required
def admin_clear_room(room_id):
    count = database.admin_clear_room_messages(room_id)
    return jsonify({"ok": True, "deleted": count})

# --- DM Chat ---
@app.route("/api/admin/chat/dm", methods=["GET"])
@admin_required
def admin_dm_messages():
    u1 = request.args.get("user1", "")
    u2 = request.args.get("user2", "")
    if not u1 or not u2:
        return jsonify({"ok": False, "error": "user1 and user2 required"}), 400
    msgs = database.admin_get_dm_messages(u1, u2)
    return jsonify({"ok": True, "messages": msgs})

@app.route("/api/admin/chat/dm/delete/<int:mid>", methods=["DELETE", "POST"])
@admin_required
def admin_delete_dm_msg(mid):
    ok = database.admin_delete_dm_message(mid)
    return jsonify({"ok": ok})

@app.route("/api/admin/chat/dm/clear", methods=["POST"])
@admin_required
def admin_clear_dm_route():
    data = request.get_json(silent=True) or {}
    u1 = data.get("user1", "")
    u2 = data.get("user2", "")
    if not u1 or not u2:
        return jsonify({"ok": False, "error": "user1 and user2 required"}), 400
    count = database.admin_clear_dm(u1, u2)
    return jsonify({"ok": True, "deleted": count})








@app.route("/api/admin/users/<username>/toggle-active", methods=["POST"])
@admin_required
def admin_toggle_active_route(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถปิดบัญชี Admin ได้"}), 400
    settings = database.get_user_setting(username)
    new_active = not settings.get("is_active", True)
    database.admin_update_user(username, is_active=new_active)
    admin_user = session.get("user", "Admin")
    status_th = "เปิด" if new_active else "ปิด"
    database.log_event(f"Admin {status_th}การใช้งาน user: {username}", user=admin_user)
    return jsonify({"ok": True, "is_active": new_active})



@app.route("/api/admin/settings", methods=["GET"])
@admin_required
def get_admin_settings():
    settings = settings_manager.get_settings()
    return jsonify({"ok": True, "settings": settings})

@app.route("/api/admin/settings", methods=["POST"])
@admin_required
def update_admin_settings():
    data = request.json or {}
    # Validate keys if necessary, but here we allow general .env updates
    success = settings_manager.update_settings(data)
    if success:
        database.log_event("อัปเดตการตั้งค่าระบบผ่านหน้าเว็บ", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่สามารถอัปเดตการตั้งค่าได้"}), 500

# ═══════════════════════════════════════════════════════════════════════════════
# SUPER ADMIN — Dev / System Owner Panel (ครอบจักรวาล)
# ═══════════════════════════════════════════════════════════════════════════════

_APP_START_TIME = time.time()

def superadmin_required(f):
    """Only master Admin user (or users listed in SUPERADMIN_USERS env) can access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อน"}), 401
        user = session.get("user")
        sa_users = set(filter(None, os.environ.get("SUPERADMIN_USERS", "Admin").split(",")))
        if user not in sa_users:
            return jsonify({"ok": False, "error": "Super Admin เท่านั้น"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/super")
@login_required
def superadmin_page():
    user = session.get("user")
    sa_users = set(filter(None, os.environ.get("SUPERADMIN_USERS", "Admin").split(",")))
    if user not in sa_users:
        return "403 — Super Admin Access Only", 403
    return render_template("superadmin.html")


@app.route("/api/superadmin/overview")
@superadmin_required
def superadmin_overview():
    stats = database.superadmin_get_system_stats()
    orgs = database.get_all_orgs_with_stats()
    plan_prices = {p: billing.PLANS[p]["price_thb"] for p in billing.PLANS}
    mrr = sum(plan_prices.get(o["plan"] or "free", 0) for o in orgs)
    paying = sum(1 for o in orgs if (o["plan"] or "free") != "free")
    uptime_sec = int(time.time() - _APP_START_TIME)
    return jsonify({
        "ok": True,
        "stats": stats,
        "mrr": mrr,
        "paying_orgs": paying,
        "total_orgs": len(orgs),
        "uptime_seconds": uptime_sec,
        "ai_provider": os.environ.get("AI_PROVIDER", "groq"),
        "version": VERSION,
    })


@app.route("/api/superadmin/orgs")
@superadmin_required
def superadmin_orgs():
    orgs = database.get_all_orgs_with_stats()
    for o in orgs:
        o["plan_config"] = billing.get_plan_config(o["plan"] or "free")
        o["effective_plan"] = billing.get_effective_plan(o["id"])
    return jsonify({"ok": True, "orgs": orgs})


@app.route("/api/superadmin/org/<int:org_id>/members")
@superadmin_required
def superadmin_org_members(org_id):
    members = database.get_org_members(org_id)
    return jsonify({"ok": True, "members": members})


@app.route("/api/superadmin/org/<int:org_id>/set-plan", methods=["POST"])
@superadmin_required
def superadmin_set_plan(org_id):
    data = request.get_json() or {}
    plan = data.get("plan", "free")
    expires = data.get("expires_at")
    try:
        billing.set_org_plan(org_id, plan, expires)
        database.log_event(f"[SuperAdmin] Set org {org_id} → plan={plan}", user=session.get("user"))
        return jsonify({"ok": True, "plan": plan})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/superadmin/org/<int:org_id>", methods=["DELETE"])
@superadmin_required
def superadmin_delete_org(org_id):
    if org_id == 1:
        return jsonify({"ok": False, "error": "ไม่สามารถลบ org หลักได้"}), 400
    ok = database.superadmin_delete_org(org_id)
    if ok:
        database.log_event(f"[SuperAdmin] Deleted org {org_id}", user=session.get("user"))
    return jsonify({"ok": ok})


@app.route("/api/superadmin/users")
@superadmin_required
def superadmin_users():
    users = database.superadmin_get_all_users()
    return jsonify({"ok": True, "users": users})


@app.route("/api/superadmin/user/<username>/reset-password", methods=["POST"])
@superadmin_required
def superadmin_reset_password(username):
    data = request.get_json() or {}
    new_pw = data.get("password", "").strip()
    if len(new_pw) < 6:
        return jsonify({"ok": False, "error": "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"}), 400
    database.admin_reset_user_password(username, new_pw)
    database.log_event(f"[SuperAdmin] Reset password for {username}", user=session.get("user"))
    return jsonify({"ok": True})


@app.route("/api/superadmin/user/<username>/toggle-active", methods=["POST"])
@superadmin_required
def superadmin_toggle_active(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถปิด Admin ได้"}), 400
    settings = database.get_user_setting(username)
    new_state = not settings.get("is_active", True)
    database.admin_update_user(username, is_active=new_state)
    database.log_event(f"[SuperAdmin] {'Activated' if new_state else 'Deactivated'} user {username}", user=session.get("user"))
    return jsonify({"ok": True, "is_active": new_state})


@app.route("/api/superadmin/user/<username>/set-role", methods=["POST"])
@superadmin_required
def superadmin_set_role(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถเปลี่ยน role Admin ได้"}), 400
    data = request.get_json() or {}
    role = data.get("role", "user")
    if role not in ("user", "admin"):
        return jsonify({"ok": False, "error": "role ไม่ถูกต้อง"}), 400
    database.admin_update_user(username, role=role)
    database.log_event(f"[SuperAdmin] Set role {username} → {role}", user=session.get("user"))
    return jsonify({"ok": True, "role": role})


@app.route("/api/superadmin/user/<username>", methods=["DELETE"])
@superadmin_required
def superadmin_delete_user(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถลบ Admin ได้"}), 400
    ok = database.admin_delete_user_complete(username)
    if ok:
        database.log_event(f"[SuperAdmin] Deleted user {username}", user=session.get("user"))
    return jsonify({"ok": ok})


@app.route("/api/superadmin/user/<username>/notes", methods=["POST"])
@superadmin_required
def superadmin_update_notes(username):
    data = request.get_json() or {}
    notes = data.get("notes", "")
    database.admin_update_user(username, notes=notes)
    return jsonify({"ok": True})


@app.route("/api/superadmin/system")
@superadmin_required
def superadmin_system():
    env_keys = ["AI_PROVIDER", "GROQ_API_KEY", "GEMINI_API_KEY", "STRIPE_SECRET_KEY",
                "LINE_CHANNEL_ACCESS_TOKEN", "FLASK_SECRET_KEY", "BASE_URL",
                "SUPERADMIN_USERS", "SENTRY_DSN", "REDIS_URL"]
    env_info = {}
    for k in env_keys:
        val = os.environ.get(k, "")
        if val:
            env_info[k] = val[:4] + "****" + val[-2:] if len(val) > 8 else "****"
        else:
            env_info[k] = "(ไม่ได้ตั้งค่า)"
    kb_files = rag_engine.list_files()
    return jsonify({
        "ok": True,
        "env": env_info,
        "kb_total_files": len(kb_files),
        "uptime_seconds": int(time.time() - _APP_START_TIME),
        "version": VERSION,
        "python_version": __import__("sys").version,
    })


@app.route("/api/superadmin/logs")
@superadmin_required
def superadmin_logs():
    limit = int(request.args.get("limit", 100))
    events = database.get_events(limit=limit)
    return jsonify({"ok": True, "events": events})


@app.route("/api/superadmin/org/create", methods=["POST"])
@superadmin_required
def superadmin_create_org():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    plan = data.get("plan", "free")
    if not name:
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อองค์กร"}), 400
    try:
        result = database.create_organization(name=name, owner_username=session.get("user"))
        org_id = result[0] if isinstance(result, (tuple, list)) else result
        slug = result[1] if isinstance(result, (tuple, list)) and len(result) > 1 else ""
        if plan != "free":
            billing.set_org_plan(org_id, plan)
        database.log_event(f"[SuperAdmin] Created org '{name}' id={org_id}", user=session.get("user"))
        return jsonify({"ok": True, "org_id": org_id, "slug": slug})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/superadmin/user/create", methods=["POST"])
@superadmin_required
def superadmin_create_user():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    display_name = (data.get("display_name") or username).strip()
    role = data.get("role", "user")
    if not username or not password:
        return jsonify({"ok": False, "error": "กรุณากรอก username และ password"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"}), 400
    if role not in ("user", "admin"):
        role = "user"
    ok = database.admin_create_user(username=username, password=password, role=role, display_name=display_name)
    if not ok:
        return jsonify({"ok": False, "error": "Username นี้มีอยู่แล้ว"}), 400
    database.log_event(f"[SuperAdmin] Created user '{username}' role={role}", user=session.get("user"))
    return jsonify({"ok": True})


@app.route("/api/superadmin/billing")
@superadmin_required
def superadmin_billing():
    orgs = database.get_all_orgs_with_stats()
    plan_prices = {p: billing.PLANS[p]["price_thb"] for p in billing.PLANS}
    revenue_by_plan = {}
    for p in billing.PLANS:
        count = sum(1 for o in orgs if (o.get("plan") or "free") == p)
        revenue_by_plan[p] = {
            "count": count,
            "price_thb": plan_prices.get(p, 0),
            "total": count * plan_prices.get(p, 0),
            "name": billing.PLANS[p].get("name", p),
        }
    paying_list = [
        {
            "id": o["id"], "name": o["name"],
            "plan": o.get("plan") or "free",
            "price_thb": plan_prices.get(o.get("plan") or "free", 0),
            "member_count": o.get("member_count", 0),
            "plan_expires_at": o.get("plan_expires_at"),
        }
        for o in orgs if (o.get("plan") or "free") != "free"
    ]
    mrr = sum(plan_prices.get(o.get("plan") or "free", 0) for o in orgs)
    return jsonify({"ok": True, "mrr": mrr, "revenue_by_plan": revenue_by_plan, "paying_orgs": paying_list})


@app.route("/api/superadmin/broadcast", methods=["POST"])
@superadmin_required
def superadmin_broadcast():
    data = request.get_json() or {}
    title = (data.get("title") or "ประกาศจากผู้ดูแลระบบ").strip()
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "กรุณากรอกข้อความ"}), 400
    database.log_event(f"[BROADCAST]{title}{message}", user=session.get("user"))
    return jsonify({"ok": True})


@app.route("/api/superadmin/broadcasts")
@superadmin_required
def superadmin_broadcasts():
    events = database.get_events(limit=500)
    broadcasts = []
    for e in events:
        text = e.get("event") or e.get("event_text") or ""
        if text.startswith("[BROADCAST]\x01"):
            parts = text[len("[BROADCAST]\x01"):].split("\x01", 1)
            broadcasts.append({
                "title": parts[0] if parts else "ประกาศ",
                "message": parts[1] if len(parts) > 1 else "",
                "user": e.get("user", "—"),
                "time": e.get("time") or e.get("timestamp", ""),
            })
    return jsonify({"ok": True, "broadcasts": broadcasts})


@app.route("/api/superadmin/system/clear-cache", methods=["POST"])
@superadmin_required
def superadmin_clear_cache():
    try:
        rag_engine.clear_cache()
    except Exception:
        pass
    database.log_event("[SuperAdmin] Cleared RAG/KB cache", user=session.get("user"))
    return jsonify({"ok": True})


@app.route("/manifest.json")
def serve_manifest():
    return send_from_directory("static", "manifest.json")


@safe_thread_target
@db_task_tracker("append_quotation_to_sheet")
def append_quotation_to_sheet(quotation_data, pdf_url, user, org_id=None):


    try:
        from google_drive_service import google_manager
        google_manager.set_context(username=user, org_id=org_id)
        drive_svc, sheets_svc = google_drive_service.get_drive_service()
        spreadsheet_id = google_manager.spreadsheet_id
        if not sheets_svc or not spreadsheet_id: return
        
        tab_name = 'ใบเสนอราคา (สร้างจากระบบ)'
        spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_exists = any(s['properties']['title'] == tab_name for s in spreadsheet.get('sheets', []))
        
        if not sheet_exists:
            requests = [{'addSheet': {'properties': {'title': tab_name}}}]
            sheets_svc.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
            # ปรับหัวตารางให้สอดคล้องและสวยงาม
            headers = [["วันที่ทำรายการ", "เลขที่ใบเสนอราคา", "ชื่อลูกค้า/บริษัท", "ข้อมูลติดต่อ", "ยอดรวมก่อนลด", "ส่วนลด", "ยอดสุทธิ (VAT 7%)", "ผู้ออกเอกสาร", "ลิงก์ไฟล์ PDF"]]
            sheets_svc.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=f"'{tab_name}'!A1",
                valueInputOption="USER_ENTERED", body={"values": headers}
            ).execute()

            # เพิ่มความสวยงามให้หัวตาราง (สีน้ำเงิน ตัวขาว หนา)
            spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_id = next(s['properties']['sheetId'] for s in spreadsheet.get('sheets', []) if s['properties']['title'] == tab_name)
            
            format_req = {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": len(headers[0])},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.1, "green": 0.4, "blue": 0.8},
                            "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 11},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            }
            sheets_svc.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [format_req]}).execute()
        
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [[
            now_str,
            quotation_data.get('quotation_no', ''),
            quotation_data.get('customer_name', ''),
            quotation_data.get('customer_contact', ''),
            quotation_data.get('subtotal', 0),
            quotation_data.get('total_discount', 0),
            quotation_data.get('grand_total', 0),
            user,
            pdf_url
        ]]
        sheets_svc.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=f"'{tab_name}'!A1",
            valueInputOption="USER_ENTERED", body={"values": row}
        ).execute()
    except Exception as e:
        print(f"⚠️ [Quotation] Sheet Sync Error: {e}")
    finally:
        try:
            from google_drive_service import google_manager
            google_manager.clear_context()
        except:
            pass

@app.route("/api/quotation/create", methods=["POST"])
@login_required
def create_quotation():
    try:
        username = session.get("user")
        org_id = session.get("org_id")
        from google_drive_service import google_manager
        google_manager.set_context(username, org_id)

        quotation_data_str = request.form.get("quotation_data")
        pdf_file = request.files.get("quotation_pdf")
        
        if not quotation_data_str or not pdf_file:
            return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400
            
        quotation_data = json.loads(quotation_data_str)
        pdf_content = pdf_file.read()
        
        # 1. Upload to Drive
        original_filename = f"{quotation_data.get('quotation_no', 'QT')}_{quotation_data.get('customer_name', '')}.pdf".replace("/", "-")
        drive_link, err = google_drive_service.upload_to_date_folder(pdf_content, original_filename, "application/pdf")
        
        if err:
            return jsonify({"ok": False, "error": f"Drive Upload Error: {err}"}), 500
            
        # 2. Sync to Sheets in background
        user = session.get("user", "System")
        threading.Thread(target=append_quotation_to_sheet, args=(quotation_data, drive_link, user, org_id)).start()
        
        database.log_event(f"สร้างใบเสนอราคา: {quotation_data.get('quotation_no')}", user=user)
        
        return jsonify({"ok": True, "link": drive_link})
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── Socket.IO Events ──────────────────────────
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        print(f"👤 User {session.get('user')} joined room: {room}")

@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)

@socketio.on('chat_message')
def handle_chat_message(data):
    # This is a real-time signal, actual DB save is still via REST for reliability
    # but we can broadcast it here to avoid polling lag
    room = data.get('room')
    if room:
        emit('new_message', data, room=room)

# ─────────────── WebSocket Events for Real-Time Features ───────────────

@socketio.on('user_online')
def handle_user_online(data):
    """Handle user coming online."""
    try:
        username = session.get("user")
        if not username:
            return emit('error', {'msg': 'Not logged in'})
        
        room = data.get('room', 'General')
        database.set_user_online(username, room)
        
        # User joins their own personal room for WebRTC signaling
        join_room(f"user_{username}")
        
        # Notify all users in the room about new Online status
        online_users = database.get_online_users()
        emit('user_status_updated', {
            'username': username,
            'status': 'online',
            'online_users': online_users
        }, room=room)
        
        print(f"[ONLINE] {username} joined room: {room}")
    except Exception as e:
        print(f"[ERROR] user_online: {e}")
        emit('error', {'msg': str(e)})

@socketio.on('user_offline')
def handle_user_offline():
    """Handle user going offline."""
    try:
        username = session.get("user")
        if not username:
            return
        
        database.set_user_offline(username)
        online_users = database.get_online_users()
        
        # Notify all connected clients about offline status
        emit('user_status_updated', {
            'username': username,
            'status': 'offline',
            'online_users': online_users
        }, broadcast=True)
        
        print(f"[OFFLINE] {username} went offline")
    except Exception as e:
        print(f"[ERROR] user_offline: {e}")

@socketio.on('user_typing')
def handle_user_typing(data):
    """Handle typing indicator."""
    try:
        username = session.get("user")
        if not username:
            return
        
        room_id = data.get('room_id', 1)
        database.set_user_typing(username, room_id)
        
        # Broadcast typing indicator to room
        emit('user_typing', {
            'username': username,
            'room_id': room_id,
            'display_name': data.get('display_name', username)
        }, room=f"room_{room_id}")
        
    except Exception as e:
        print(f"[ERROR] user_typing: {e}")

@socketio.on('user_stopped_typing')
def handle_user_stopped_typing(data):
    """Clear typing indicator."""
    try:
        username = session.get("user")
        if not username:
            return
        
        room_id = data.get('room_id', 1)
        database.clear_user_typing(username)
        
        # Broadcast to room
        emit('user_stopped_typing', {
            'username': username,
            'room_id': room_id
        }, room=f"room_{room_id}")
        
    except Exception as e:
        print(f"[ERROR] user_stopped_typing: {e}")

@socketio.on('message_read')
def handle_message_read(data):
    """Mark message as read (read receipt)."""
    try:
        username = session.get("user")
        if not username:
            return
        
        message_id = data.get('message_id')
        room_id = data.get('room_id')
        
        if message_id:
            database.mark_message_as_read(message_id, username, room_id)
            
            # Get read receipts for this message
            receipts = database.get_message_read_receipts(message_id)
            
            # Broadcast read receipts to room
            emit('message_read_receipt', {
                'message_id': message_id,
                'username': username,
                'read_by_count': len(receipts),
                'read_receipts': receipts
            }, room=f"room_{room_id}" if room_id else None)
            
            print(f"[READ] {username} read message {message_id}")
        
    except Exception as e:
        print(f"[ERROR] message_read: {e}")

@socketio.on('message_read_dm')
def handle_private_message_read(data):
    """Mark private message as read."""
    try:
        username = session.get("user")
        if not username:
            return
        
        message_id = data.get('message_id')
        if message_id:
            database.mark_private_message_as_read(message_id)
            
            # Emit read receipt to sender
            sender = data.get('sender')
            emit('dm_read_receipt', {
                'message_id': message_id,
                'read_by': username,
                'read_at': time.strftime("%Y-%m-%d %H:%M:%S")
            }, room=f"dm_{sender}_{username}" if sender else None)
            
            print(f"[DM_READ] {username} read DM {message_id}")
            
    except Exception as e:
        print(f"[ERROR] message_read_dm: {e}")

@socketio.on('join_room')
def on_join_room(data):
    """Join a room group for broadcasts."""
    try:
        room = data.get('room', '1')
        username = session.get("user")
        join_room(f"room_{room}")
        print(f"[JOIN] {username} joined room group: {room}")
        emit('message', {'text': f'{username} joined'}, room=f"room_{room}")
    except Exception as e:
        print(f"[ERROR] join_room: {e}")

@socketio.on('get_online_users')
def handle_get_online_users():
    """Get current list of online users."""
    try:
        online_users = database.get_online_users()
        emit('online_users_list', {
            'users': online_users,
            'count': len(online_users),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        print(f"[ERROR] get_online_users: {e}")
        emit('error', {'msg': str(e)})

# ─── WebRTC Signaling ────────────────────────
@socketio.on('webrtc_signal')
def handle_webrtc_signal(data):
    """
    Signaling server for WebRTC Voice/Video Calls.
    """
    # Prefer sender from payload, fallback to session
    sender = data.get('sender') or session.get("user")
    if not sender:
        print(f"⚠️ [WebRTC] Signal dropped: No sender identified. Data={data}")
        return
        
    target = data.get('target')
    if not target:
        print(f"⚠️ [WebRTC] Signal dropped: No target for signal {data.get('type')} from {sender}")
        return
        
    target_room = f"user_{target}"
    data['sender'] = sender  # Ensure sender is attached
    
    print(f"📡 [WebRTC] {data.get('type').upper()} from {sender} -> {target}")
    
    # If it's a new call (offer), trigger a push notification to wake up the recipient
    if data.get('type') == 'offer':
        try:
            # Call the local function defined at the top of app.py
            call_type_th = "วิดีโอคอล" if data.get('callType') == 'video' else "สายโทรเข้า"
            send_push_notification(
                target, 
                f"📞 {sender}", 
                f"กำลังมี{call_type_th}จาก {sender}...", 
                tag="incoming_call"
            )
        except Exception as e:
            print(f"⚠️ [WebRTC] Push notification failed: {e}")

    emit('webrtc_signal', data, room=target_room)

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


# ─────────────────────── Kanban API ───────────────────────

@app.route("/api/kanban/board", methods=["GET"])
@login_required
def kanban_get_board():
    return jsonify({"ok": True, "columns": database.kanban_get_board()})

@app.route("/api/kanban/columns", methods=["POST"])
@login_required
def kanban_add_column():
    data = request.json or {}
    title = data.get("title", "").strip()
    color = data.get("color", "#6366f1")
    if not title:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อคอลัมน์"}), 400
    col_id = database.kanban_add_column(title, color, created_by=session.get("user", "System"))
    return jsonify({"ok": True, "id": col_id})

@app.route("/api/kanban/columns/<int:col_id>", methods=["PUT"])
@login_required
def kanban_update_column(col_id):
    data = request.json or {}
    database.kanban_update_column(col_id, title=data.get("title"), color=data.get("color"))
    return jsonify({"ok": True})

@app.route("/api/kanban/columns/<int:col_id>", methods=["DELETE"])
@login_required
def kanban_delete_column(col_id):
    ok = database.kanban_delete_column(col_id)
    return jsonify({"ok": ok})

@app.route("/api/kanban/columns/reorder", methods=["POST"])
@login_required
def kanban_reorder_columns():
    data = request.json or {}
    order = data.get("order", [])
    database.kanban_reorder_columns(order)
    return jsonify({"ok": True})

@app.route("/api/kanban/cards", methods=["POST"])
@login_required
def kanban_add_card():
    data = request.json or {}
    column_id = data.get("column_id")
    title = data.get("title", "").strip()
    if not column_id or not title:
        return jsonify({"ok": False, "error": "Missing column_id or title"}), 400
    
    current_user = session.get("user", "System")
    assignees_raw = data.get("assignee", "")
    if assignees_raw and isinstance(assignees_raw, str):
        assignee_list = [a.strip() for a in assignees_raw.split(',') if a.strip()]
    else:
        assignee_list = []
        
    card_id = database.kanban_add_card(
        column_id=int(column_id),
        title=title,
        description=data.get("description", ""),
        priority=data.get("priority", "medium"),
        assignee=",".join(assignee_list) if assignee_list else "",
        due_date=data.get("due_date", ""),
        labels=data.get("labels", ""),
        color=data.get("color", ""),
        created_by=current_user,
        is_done=int(data.get("is_done", 0))
    )
    
    if assignee_list:
        for a in assignee_list:
            if a != current_user:
                try:
                    notification_db.add_notification(
                        a,
                        "kanban",
                        "มอบหมายงานใหม่ / Kanban",
                        f"{current_user} ได้มอบหมายงาน '{title}' ให้กับคุณ",
                        link="#view=kanban"
                    )
                    batch_send_push_notification([a], "มอบหมายงานใหม่ / Kanban", f"{current_user}: {title}", url="#view=kanban")
                    # --- Send to LINE ---
                    threading.Thread(target=send_line_push_notification, args=(
                        a, 
                        "งานใหม่ (Kanban)", 
                        f"{current_user} ได้มอบหมายงาน '{title}' ให้กับคุณ"
                    ), kwargs={
                        "fields": {
                            "งาน": title,
                            "ผู้มอบหมาย": current_user,
                            "สถานะ": "รอดำเนินการ (To Do)"
                        }
                    }).start()
                except Exception as e:
                    print(f"Error sending kanban notification to {a}: {e}")
            
    return jsonify({"ok": True, "id": card_id})

@app.route("/api/kanban/cards/<int:card_id>", methods=["PUT"])
@login_required
def kanban_update_card(card_id):
    data = request.json or {}
    
    old_card = database.kanban_get_card(card_id)
    if not old_card:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404
        
    database.kanban_update_card(card_id, **data)
    
    current_user = session.get("user", "System")
    assignees_raw = data.get("assignee", "")
    if isinstance(assignees_raw, str):
        new_assignee_list = [a.strip() for a in assignees_raw.split(',') if a.strip()]
    else:
        new_assignee_list = []
        
    old_assignee_list = (old_card.get("assignee") or "").split(',')
    old_assignee_list = [a.strip() for a in old_assignee_list if a.strip()]
    
    # Notify ONLY newly added assignees
    added_assignees = [a for a in new_assignee_list if a not in old_assignee_list and a != current_user]
    
    for a in added_assignees:
        try:
            notification_db.add_notification(
                a,
                "kanban",
                "มอบหมายงาน / Kanban",
                f"{current_user} ได้มอบหมายงาน '{data.get('title', old_card['title'])}' ให้กับคุณ",
                link="#view=kanban"
            )
            batch_send_push_notification([a], "มอบหมายงาน / Kanban", f"{current_user}: {data.get('title', old_card['title'])}", url="#view=kanban")
            # --- Send to LINE ---
            threading.Thread(target=send_line_push_notification, args=(
                a, 
                "อัปเดตงาน (Kanban)", 
                f"{current_user} ได้เพิ่มคุณในงาน '{data.get('title', old_card['title'])}'"
            ), kwargs={
                "fields": {
                    "งาน": data.get('title', old_card['title']),
                    "แจ้งเตือน": f"{current_user} มอบหมายงานให้คุณ",
                    "ดูที่หน้าเว็บ": "เมนู Kanban"
                }
            }).start()
        except Exception as e:
            print(f"Error sending kanban update notification to {a}: {e}")
            
    return jsonify({"ok": True})

@app.route("/api/kanban/cards/<int:card_id>", methods=["DELETE"])
@login_required
def kanban_delete_card(card_id):
    ok = database.kanban_delete_card(card_id)
    return jsonify({"ok": ok})

@app.route("/api/kanban/cards/<int:card_id>/move", methods=["POST"])
@login_required
def kanban_move_card(card_id):
    data = request.json or {}
    new_column_id = data.get("column_id")
    new_position = data.get("position", 0)
    if new_column_id is None:
        return jsonify({"ok": False, "error": "Missing column_id"}), 400
    ok = database.kanban_move_card(card_id, int(new_column_id), int(new_position))
    
    # Also update 'is_done' if passed (for automatic status on move to Done column)
    is_done = data.get("is_done")
    if is_done is not None:
        database.kanban_update_card(card_id, is_done=int(is_done))
        
    # Broadcast board update via socketio
    socketio.emit("kanban_update", {}, room="kanban_board")
    return jsonify({"ok": ok})

@app.route("/api/users/list", methods=["GET"])
@login_required
def api_users_list():
    users = database.admin_get_all_users(org_id=get_current_org_id())
    # Mask notes and potentially other sensitive admin data for a general user list
    clean_users = []
    for u in users:
        clean_users.append({
            "username": u["username"],
            "display_name": u["display_name"],
            "avatar_url": u["avatar_url"],
            "department": u.get("department", "General")
        })
    return jsonify({"ok": True, "users": clean_users})

# ─────────────────────── Wiki API ─────────────────────────

@app.route("/api/wiki/pages", methods=["GET"])
@login_required
def wiki_list_pages():
    q = request.args.get("q", "").strip()
    org_id = get_current_org_id()
    if q:
        pages = database.wiki_search(q, org_id=org_id)
    else:
        pages = database.wiki_get_all_pages(org_id=org_id)
    return jsonify({"ok": True, "pages": pages})

@app.route("/api/wiki/pages", methods=["POST"])
@login_required
def wiki_create_page():
    data = request.json or {}
    title = data.get("title", "").strip()
    content = data.get("content", "")
    if not title:
        return jsonify({"ok": False, "error": "กรุณาระบุหัวข้อบทความ"}), 400
    org_id = get_current_org_id()
    page_id, slug = database.wiki_create_page(
        title=title,
        content=content,
        author=session.get("user", "Anonymous"),
        category_id=data.get("category_id"),
        org_id=org_id
    )
    return jsonify({"ok": True, "id": page_id, "slug": slug})

@app.route("/api/wiki/pages/<int:page_id>", methods=["GET"])
@login_required
def wiki_get_page(page_id):
    org_id = get_current_org_id()
    page = database.wiki_get_page(page_id=page_id, org_id=org_id)
    if not page:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404
    return jsonify({"ok": True, "page": page})

@app.route("/api/wiki/pages/<int:page_id>", methods=["PUT"])
@login_required
def wiki_update_page(page_id):
    data = request.json or {}
    org_id = get_current_org_id()
    database.wiki_update_page(page_id, title=data.get("title"), content=data.get("content"), category_id=data.get("category_id"), org_id=org_id)
    return jsonify({"ok": True})

@app.route("/api/wiki/pages/<int:page_id>", methods=["DELETE"])
@login_required
def wiki_delete_page(page_id):
    org_id = get_current_org_id()
    ok = database.wiki_delete_page(page_id, org_id=org_id)
    return jsonify({"ok": ok})

@app.route("/api/wiki/pages/<int:page_id>/export", methods=["GET"])
@login_required
def export_wiki_page(page_id):
    export_format = request.args.get("format", "txt").lower()
    org_id = get_current_org_id()
    page = database.wiki_get_page(page_id=page_id, org_id=org_id)
    if not page:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404

    title = page.get("title", "wiki_export")
    content = page.get("content", "")
    author = page.get("author", "Unknown")
    updated_at = page.get("updated_at", "")

    import wiki_manager
    file_path, download_name, error = wiki_manager.export_page_to_file(
        page_id=page_id,
        title=title,
        content=content,
        author=author,
        updated_at=updated_at,
        export_format=export_format
    )

    if error:
        return jsonify({"ok": False, "error": error}), 400

    return send_file(file_path, as_attachment=True, download_name=download_name)



# ─── Daily Summary Scheduler ──────────────────────────────
def daily_morning_summary():
    """Daily job at 8:00 AM to summarize activities using Nong Pan persona."""
    print("🌟 Starting Daily Morning Summary Job (Nong Pan Persona)...", flush=True)
    try:
        # 1. Fetch activities
        activities = database.get_daily_activities()
        drive_stats = database.get_drive_stats()
        recent_files = database.get_drive_logs(limit=10)
        
        # 2. Prepare context
        context = "กิจกรรมของบริษัทในรอบ 24 ชม. ที่ผ่านมา:\n"
        if activities.get("posts"):
            context += "📢 ข่าวสารใหม่:\n" + "\n".join([f"- {p['title']}" for p in activities["posts"][:3]]) + "\n"
        if activities.get("schedules"):
            context += "📅 ตารางงานวันนี้:\n" + "\n".join([f"- {s['time']} {s['title']}" for s in activities["schedules"][:3]]) + "\n"
        if recent_files:
            context += "📂 เอกสารอัปโหลดใหม่:\n" + "\n".join([f"- {f['filename']} ({f['category']})" for f in recent_files[:5]]) + "\n"

        prompt = (
            "คุณคือ 'น้องพั้นซ์' (Punch) AI Assistant สาวออฟฟิศสุดน่ารักและเป็นกันเอง "
            "ช่วยสรุป Morning Brief ข้อมูลสำคัญประจำวันนี้ให้กับพี่ๆ ในทีม เพื่อเป็นกำลังใจและแนวทางในการทำงาน "
            "โดยใช้ภาษาที่เป็นกันเองและน่ารักมากๆ เหมือนมีเพื่อนร่วมงานที่คอยดูแลและให้ความใส่ใจพี่ๆ ทุกคนนะคะ\n\n"
            f"{context}\n\n"
            "สรุปในสไตล์น้องพั้นซ์:"
        )
        
        summary = ai_providers.generate_response(prompt)
        
        # 3. Broadcast to all users (or a specific group) via LINE
        if summary:
            broadcast_line_announcement("🌟 Morning Brief จากน้องพั้นซ์", summary)
            print("🌟 Daily Summary sent via LINE.")
            
    except Exception as e:
        print(f"❌ Daily Summary Job Error: {e}")



# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(daily_morning_summary, CronTrigger(hour=8, minute=0, timezone="Asia/Bangkok"))

@app.route('/api/drive/contents', methods=['GET'])
@login_required
def get_drive_contents():
    folder_id = request.args.get('folder_id')
    try:
        username = session.get("user")
        org_id = session.get("org_id")
        google_manager.set_context(username, org_id)
        contents = google_drive_service.list_folder_contents(folder_id)
        return jsonify(contents)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/drive/rename', methods=['POST'])
@admin_required
def rename_drive_file():
    data = request.json or {}
    file_id = data.get('file_id')
    new_name = data.get('new_name')
    if not file_id or not new_name:
        return jsonify({"ok": False, "error": "Missing parameters"}), 400
    
    username = session.get("user")
    org_id = session.get("org_id")
    google_manager.set_context(username, org_id)
    if google_drive_service.rename_file(file_id, new_name):
        database.log_event(f"Renamed Drive file {file_id} to {new_name}", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Failed to rename"}), 500

@app.route('/edit_expense_form', methods=['GET', 'POST'])
def edit_expense_form():
    sheet = request.args.get('sheet')
    row_str = request.args.get('row')
    
    # Enforce tenant context boundaries safely
    org_id = request.args.get('org_id')
    username = request.args.get('user')
    if not org_id:
        org_id = session.get('org_id')
    if not username:
        username = session.get('user')
        
    if org_id or username:
        try:
            org_id_int = int(org_id) if org_id else None
        except ValueError:
            org_id_int = None
        google_manager.set_context(username=username, org_id=org_id_int)
    
    if not sheet or not row_str:
        return "❌ ข้อมูลไม่ครบถ้วน (กรุณาระบุ sheet และ row)", 400
        
    try:
        row = int(row_str)
    except ValueError:
        return "❌ เลขแถวไม่ถูกต้อง", 400
        
    if request.method == 'POST':
        # Handle form submission
        updated_data = {}
        for key, val in request.form.items():
            if key.startswith("field_"):
                col_name = key.replace("field_", "")
                
                # Format Date back to DD/MM/YYYY
                if "วันที่" in col_name and val:
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(val, "%Y-%m-%d")
                        val = dt.strftime("%d/%m/%Y")
                    except:
                        pass
                
                updated_data[col_name] = val
                
        # Update each field in the spreadsheet
        for col_name, new_val in updated_data.items():
            google_manager.update_expense(sheet, row, col_name, new_val)
            
        # Re-run reconciliation
        google_manager.auto_reconcile_internal()
        
        # Breathtaking Success Page with Custom Canvas Confetti
        return """
        <!DOCTYPE html>
        <html lang="th" class="h-full">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>บันทึกสำเร็จ ✨</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://unpkg.com/lucide@latest"></script>
            <script>
                tailwind.config = {
                    theme: {
                        extend: {
                            colors: {
                                brand: { 50: '#f0f5ff', 600: '#2563eb', 700: '#1d4ed8' },
                                surface: { 900: '#0f172a', 950: '#020617' }
                            }
                        }
                    }
                }
            </script>
            <style>
                body {
                    font-family: 'Inter', 'Sarabun', sans-serif;
                }
            </style>
        </head>
        <body class="bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-white min-h-screen flex flex-col justify-center items-center overflow-hidden p-6 relative transition-colors duration-300">
            <script>
                const theme = localStorage.getItem('theme') || 'auto';
                const isDark = theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                document.documentElement.classList.toggle('dark', isDark);
            </script>
            <canvas id="confettiCanvas" class="absolute inset-0 w-full h-full pointer-events-none z-50"></canvas>

            <div class="max-w-md w-full bg-white dark:bg-surface-900 border border-surface-200 dark:border-white/10 p-10 rounded-[2.5rem] shadow-2xl text-center relative overflow-hidden transform scale-95 animate-[popIn_0.6s_cubic-bezier(0.16,1,0.3,1)_forwards] z-10">
                <div class="absolute -top-24 -left-24 w-48 h-48 bg-brand-600/10 rounded-full blur-3xl pointer-events-none"></div>
                
                <div class="w-24 h-24 bg-gradient-to-tr from-brand-600 to-blue-400 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-xl shadow-brand-600/20 relative animate-[bounceIn_0.8s_both]">
                    <i data-lucide="check" class="w-12 h-12 text-white relative z-10 stroke-[3]"></i>
                </div>

                <h1 class="text-3xl font-black tracking-tight text-white mb-4">บันทึกเรียบร้อย!</h1>
                <p class="text-slate-400 text-sm leading-relaxed mb-10 font-medium">
                    อัปเดตข้อมูลและประมวลผลการกระทบยอด<br/>บน Google Sheets เรียบร้อยแล้วค่ะ 💖
                </p>

                <div class="flex flex-col items-center justify-center mb-10 relative">
                    <svg class="w-14 h-14 transform -rotate-90">
                        <circle cx="28" cy="28" r="24" stroke="rgba(255,255,255,0.05)" stroke-width="4" fill="transparent" />
                        <circle id="countdownBar" cx="28" cy="28" r="24" stroke="#2563eb" stroke-width="4" fill="transparent" 
                                stroke-dasharray="150.8" stroke-dashoffset="0" class="transition-all duration-1000 ease-linear" />
                    </svg>
                    <span id="countdownText" class="absolute text-sm font-black text-brand-600">3</span>
                </div>

                <button class="w-full py-4 px-6 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 text-white font-bold transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2" onclick="window.close();">
                    <i data-lucide="x-circle" class="w-5 h-5"></i>
                    <span>ปิดหน้าต่างนี้</span>
                </button>
            </div>

            <script>
                lucide.createIcons();
                const canvas = document.getElementById('confettiCanvas');
                const ctx = canvas.getContext('2d');
                function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
                window.addEventListener('resize', resizeCanvas);
                resizeCanvas();
                let particles = [];
                const colors = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#ffffff'];
                class Particle {
                    constructor() {
                        this.x = canvas.width / 2; this.y = canvas.height / 2;
                        this.size = Math.random() * 8 + 4;
                        this.speedX = Math.random() * 12 - 6; this.speedY = Math.random() * -15 - 5;
                        this.color = colors[Math.floor(Math.random() * colors.length)];
                        this.gravity = 0.4; this.rotation = Math.random() * 360; this.rotationSpeed = Math.random() * 10 - 5;
                    }
                    update() { this.speedY += this.gravity; this.x += this.speedX; this.y += this.speedY; this.rotation += this.rotationSpeed; }
                    draw() {
                        ctx.save(); ctx.translate(this.x, this.y); ctx.rotate(this.rotation * Math.PI / 180);
                        ctx.fillStyle = this.color; ctx.fillRect(-this.size/2, -this.size/2, this.size, this.size); ctx.restore();
                    }
                }
                for (let i = 0; i < 100; i++) particles.push(new Particle());
                function animate() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    particles.forEach((p, idx) => { p.update(); p.draw(); if (p.y > canvas.height) particles.splice(idx, 1); });
                    if (particles.length > 0) requestAnimationFrame(animate);
                }
                animate();
                let timeLeft = 3; const totalBar = 150.8;
                const countdownBar = document.getElementById('countdownBar');
                const countdownText = document.getElementById('countdownText');
                const timer = setInterval(() => {
                    timeLeft--;
                    if (timeLeft >= 0) {
                        countdownText.innerText = timeLeft;
                        const offset = totalBar - (timeLeft / 3) * totalBar;
                        countdownBar.style.strokeDashoffset = offset;
                    }
                    if (timeLeft <= 0) { clearInterval(timer); window.close(); }
                }, 1000);
            </script>
            <style>
                @keyframes popIn { from { opacity: 0; transform: translateY(30px) scale(0.9); } to { opacity: 1; transform: translateY(0) scale(1); } }
                @keyframes bounceIn { 0% { transform: scale(0.3); opacity: 0; } 50% { transform: scale(1.05); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
            </style>
        </body>
        </html>
        """
        
    try:
        # Fetch current values and headers
        headers_res = google_manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=google_manager.spreadsheet_id, range=f"'{sheet}'!A1:Z1"
        ).execute()
        headers = headers_res.get('values', [[]])[0]
        
        row_res = google_manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=google_manager.spreadsheet_id, range=f"'{sheet}'!A{row}:Z{row}"
        ).execute()
        row_data = row_res.get('values', [[]])[0]
        
        # Prepare inputs list
        inputs_html = ""
        for i, header in enumerate(headers):
            if not header.strip():
                continue
                
            val = row_data[i] if i < len(row_data) else ""
            is_readonly = ""
            input_type = "text"
            label_suffix = ""
            icon_name = "edit-3"
            
            h_lower = header.lower()
            if "วันที่" in h_lower:
                input_type = "date"
                icon_name = "calendar"
                try:
                    parts = val.strip().split('/')
                    if len(parts) == 3:
                        day = int(parts[0])
                        month = int(parts[1])
                        year = int(parts[2])
                        if year < 100: year += 2000
                        val = f"{year:04d}-{month:02d}-{day:02d}"
                except:
                    pass
            elif "จำนวน" in h_lower or "สุทธิ" in h_lower or "เงิน" in h_lower or "ยอด" in h_lower or "ภาษี" in h_lower or "ราคา" in h_lower:
                input_type = "number"
                icon_name = "banknote"
                val = str(val).replace(",", "").replace("฿", "").strip()
            elif "ผู้" in h_lower or "ร้าน" in h_lower or "คู่ค้า" in h_lower:
                icon_name = "store"
            elif "ลิงก์" in h_lower or "ไฟล์" in h_lower or "url" in h_lower or "id" in h_lower:
                icon_name = "lock"
                is_readonly = "readonly"
                label_suffix = " 🔒"
                
            if "บันทึก" in h_lower or "รายละเอียด" in h_lower or "หมายเหตุ" in h_lower:
                inputs_html += f'''
                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-500 px-1 flex items-center gap-2">
                        <i data-lucide="{icon_name}" class="w-3.5 h-3.5"></i> {header}{label_suffix}
                    </label>
                    <textarea name="field_{header}" rows="3" 
                        class="w-full bg-white dark:bg-surface-950 border border-surface-200 dark:border-surface-800 rounded-2xl p-4 text-sm focus:border-brand-600 focus:ring-4 focus:ring-brand-600/10 outline-none transition-all resize-none" 
                        placeholder="กรอกข้อมูล {header}...">{val}</textarea>
                </div>
                '''
            else:
                extra_attrs = ""
                helper_html = ""
                if input_type == "number":
                    extra_attrs = 'oninput="formatLiveCurrency(this)"'
                    helper_html = f'<div id="helper_field_{header}" class="text-[11px] text-brand-600 mt-1 font-bold h-4 opacity-0 transition-opacity"></div>'
                
                inputs_html += f'''
                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-500 px-1 flex items-center gap-2">
                        <i data-lucide="{icon_name}" class="w-3.5 h-3.5"></i> {header}{label_suffix}
                    </label>
                    <input type="{input_type}" name="field_{header}" value="{val}" {is_readonly} step="any" {extra_attrs}
                        class="w-full bg-white dark:bg-surface-950 border border-surface-200 dark:border-surface-800 rounded-2xl px-4 py-3 text-sm focus:border-brand-600 focus:ring-4 focus:ring-brand-600/10 outline-none transition-all" 
                        placeholder="กรอกข้อมูล {header}...">
                    {helper_html}
                </div>
                '''
            
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}", 500
        
    return f"""
    <!DOCTYPE html>
    <html lang="th" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📝 แก้ไขข้อมูลเอกสาร</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sarabun:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <script>
            tailwind.config = {{
                darkMode: 'class',
                theme: {{
                    extend: {{
                        colors: {{
                            brand: {{ 600: '#2563eb', 700: '#1d4ed8' }},
                            surface: {{ 50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 800: '#1e293b', 900: '#0f172a', 950: '#020617' }}
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            body {{ font-family: 'Inter', 'Sarabun', sans-serif; }}
            input[type="date"]::-webkit-calendar-picker-indicator {{ filter: invert(0.5); }}
            .dark input[type="date"]::-webkit-calendar-picker-indicator {{ filter: invert(1); }}
        </style>
    </head>
    <body class="bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 min-h-screen py-10 px-4 transition-colors duration-300">
        <div class="max-w-xl mx-auto bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 shadow-2xl rounded-[2.5rem] p-8 md:p-10 relative overflow-hidden">
            <!-- Theme Toggle -->
            <button id="themeToggle" class="absolute top-8 right-8 p-3 bg-surface-50 dark:bg-surface-800 rounded-2xl hover:scale-110 transition-all text-surface-600 dark:text-surface-400 border border-surface-100 dark:border-surface-700 z-10">
                <i data-lucide="moon" id="themeIcon" class="w-5 h-5"></i>
            </button>

            <header class="text-center mb-10">
                <div class="w-16 h-16 bg-brand-600 text-white rounded-2xl shadow-lg flex items-center justify-center mx-auto mb-6 transform -rotate-3">
                    <i data-lucide="file-edit" class="w-8 h-8"></i>
                </div>
                <h1 class="text-3xl font-black tracking-tight mb-2">แก้ไขข้อมูลเอกสาร</h1>
                <p class="text-sm text-slate-500 font-medium uppercase tracking-wider">
                    ชีต: <span class="text-brand-600 font-bold">{sheet}</span> • แถวที่: <span class="text-brand-600 font-bold">{row}</span>
                </p>
            </header>

            <form method="POST" id="editForm" class="space-y-6" onsubmit="return handleFormSubmit(this)">
                {inputs_html}
                
                <button type="submit" id="btnSubmit" class="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-4 px-6 rounded-2xl shadow-lg shadow-brand-600/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 mt-4">
                    <i data-lucide="save" class="w-5 h-5"></i>
                    <span>บันทึกและประมวลผล</span>
                </button>
            </form>
        </div>

        <script>
            lucide.createIcons();

            // Theme Toggle Logic
            const themeToggle = document.getElementById('themeToggle');
            const themeIcon = document.getElementById('themeIcon');
            
            function updateTheme() {{
                const theme = localStorage.getItem('theme') || 'auto';
                const isDark = theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                document.documentElement.classList.toggle('dark', isDark);
                if (themeIcon) themeIcon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }}

            if (themeToggle) {{
                themeToggle.onclick = () => {{
                    const current = localStorage.getItem('theme') || 'auto';
                    let next = 'dark';
                    if (current === 'dark') next = 'light';
                    else if (current === 'light') next = 'auto';
                    localStorage.setItem('theme', next);
                    updateTheme();
                }};
            }}
            updateTheme();

            function formatLiveCurrency(input) {{
                const helper = document.getElementById("helper_" + input.id) || document.getElementById("helper_field_" + input.name.replace('field_', ''));
                if (!helper) return;
                const val = parseFloat(input.value);
                if (isNaN(val)) {{ helper.classList.add('opacity-0'); return; }}
                helper.innerText = "฿ " + val.toLocaleString('th-TH', {{ minimumFractionDigits: 2 }});
                helper.classList.remove('opacity-0');
            }}
            function handleFormSubmit(form) {{
                const btn = document.getElementById('btnSubmit');
                btn.disabled = true;
                btn.classList.add('opacity-70', 'cursor-not-allowed');
                btn.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 animate-spin"></i> <span>กำลังบันทึก...</span>`;
                lucide.createIcons();
                return true;
            }}
            // Auto resize textareas
            document.querySelectorAll('textarea').forEach(t => {{
                t.addEventListener('input', () => {{ t.style.height = 'auto'; t.style.height = t.scrollHeight + 'px'; }});
                t.style.height = t.scrollHeight + 'px';
            }});
        </script>
    </body>
    </html>
    """


@app.route('/api/drive/delete', methods=['DELETE', 'POST'])
@admin_required
def delete_drive_file():
    data = request.json or {}
    file_id = data.get('file_id')
    if not file_id:
        return jsonify({"ok": False, "error": "Missing file_id"}), 400
    
    username = session.get("user")
    org_id = session.get("org_id")
    google_manager.set_context(username, org_id)
    if google_drive_service.delete_file(file_id):
        database.log_event(f"Deleted Drive file {file_id}", user=session.get("user"))
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Failed to delete"}), 500


# --- LINE B2B Group Enterprise API Endpoints ---

@app.route('/api/line/groups', methods=['GET'])
@login_required
def get_line_groups():
    username = session.get("user")
    mappings = database.list_group_mappings(username)
    return jsonify({"ok": True, "mappings": mappings})


@app.route('/api/line/groups/bind', methods=['POST'])
@login_required
def bind_line_group():
    username = session.get("user")
    data = request.json or {}
    group_id = data.get("group_id", "").strip()
    group_name = data.get("group_name", "").strip() or "LINE Group"
    default_folder_id = data.get("default_folder_id", "").strip() or None
    default_folder_name = data.get("default_folder_name", "").strip() or None
    
    if not group_id:
        return jsonify({"ok": False, "error": "กรุณากรอก Group ID ค่ะ"}), 400
        
    ok = database.save_group_mapping(
        group_id=group_id,
        owner_username=username,
        group_name=group_name,
        default_folder_id=default_folder_id,
        default_folder_name=default_folder_name
    )
    if ok:
        database.log_event(f"Bound LINE group {group_id} to {username}", user=username)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการบันทึกข้อมูลค่ะ"}), 500


@app.route('/api/line/groups/unbind/<group_id>', methods=['DELETE'])
@login_required
def unbind_line_group(group_id):
    username = session.get("user")
    mapping = database.get_group_mapping(group_id)
    if not mapping:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลกลุ่มนี้ค่ะ"}), 404
    if mapping.get("owner_username") != username:
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์ลบกลุ่มนี้ค่ะ"}), 403
        
    if database.delete_group_mapping(group_id):
        database.log_event(f"Unbound LINE group {group_id} from {username}", user=username)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการยกเลิกเชื่อมต่อค่ะ"}), 500


@app.route('/api/google/folders', methods=['GET'])
@login_required
@billing.require_feature("google_sheets")
def get_google_folders():
    username = session.get("user")
    org_id = session.get("org_id")
    mgr = google_manager
    mgr.set_context(username, org_id)
    # Note: GoogleWorkspaceManager is a Singleton. Individual user manager is not supported in this version.
    folders = mgr.list_subfolders()
    return jsonify({"ok": True, "folders": folders})


def check_expiring_plans():
    """Push LINE reminder to orgs whose PromptPay plan expires in 7 or 1 day."""
    from datetime import datetime, timedelta, timezone as _tz
    import sqlite3 as _sq

    now = datetime.now(_tz.utc)
    conn = _sq.connect(database.DB_PATH)
    conn.row_factory = _sq.Row
    rows = conn.execute(
        "SELECT id, name, plan, plan_expires_at FROM organizations "
        "WHERE plan != 'free' AND plan_expires_at IS NOT NULL"
    ).fetchall()
    conn.close()

    _base = os.environ.get("BASE_URL", "https://openchat.sbs")
    _token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    _headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_token}"}

    for row in rows:
        try:
            exp_dt = datetime.fromisoformat(row["plan_expires_at"])
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=_tz.utc)
            days_left = (exp_dt - now).days
            if days_left not in (7, 1):
                continue
            plan_label = {"pro": "Pro", "business": "Ultra"}.get(row["plan"], row["plan"].title())
            msg = (
                f"แจ้งเตือนค่ะพี่! แพลน {plan_label} ของ '{row['name']}' "
                f"จะหมดอายุใน {days_left} วัน\n\n"
                f"ต่ออายุได้เลยที่:\n{_base}/pricing\n\n"
                f"เพื่อให้น้องพั้นทำงานให้ต่อเนื่องนะคะ"
            )
            groups = database.get_line_groups_for_org(row["id"])
            for g in groups:
                try:
                    requests.post(
                        "https://api.line.me/v2/bot/message/push",
                        headers=_headers,
                        json={"to": g["group_id"], "messages": [{"type": "text", "text": msg}]},
                        timeout=10,
                    )
                    logger.info(f"[ExpiryReminder] Sent {days_left}d warning to group {g['group_id']} (org {row['id']})")
                except Exception as _e:
                    logger.warning(f"[ExpiryReminder] push failed: {_e}")
        except Exception as _e:
            logger.warning(f"[ExpiryReminder] row error: {_e}")


def _backup_sqlite():
    """Hot backup SQLite DB using the built-in backup API (safe during active writes)."""
    import glob as _glob
    db_path = os.environ.get("DB_PATH", "chat_history.db")
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"chat_history_{ts}.db")
    try:
        src = sqlite3.connect(db_path, timeout=10)
        dst = sqlite3.connect(dest)
        src.backup(dst)   # atomic hot backup — safe under concurrent writes
        src.close()
        dst.close()
        logger.info(f"[Backup] SQLite backed up → {dest}")
        # Keep only last 7 backups
        old = sorted(_glob.glob(os.path.join(backup_dir, "chat_history_*.db")))
        for f in old[:-7]:
            os.remove(f)
            logger.info(f"[Backup] Removed old backup: {f}")
    except Exception as _e:
        logger.error(f"[Backup] Failed: {_e}")


def _run_daily_reminders():
    import time as _t
    _t.sleep(3600)  # wait 1h after startup before first check
    while True:
        try:
            check_expiring_plans()
        except Exception as _e:
            logger.warning(f"[ExpiryReminder] check failed: {_e}")
        try:
            _backup_sqlite()
        except Exception as _e:
            logger.warning(f"[Backup] thread error: {_e}")
        _t.sleep(86400)  # every 24h


threading.Thread(target=_run_daily_reminders, daemon=True).start()


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.route("/health")
def health_check():
    """Used by uptime monitors (UptimeRobot, etc.) — returns 200 if server is alive."""
    import sqlite3 as _sq
    db_ok = False
    try:
        _c = _sq.connect(os.environ.get("DB_PATH", "chat_history.db"), timeout=2)
        _c.execute("SELECT 1")
        _c.close()
        db_ok = True
    except Exception:
        pass
    status = "ok" if db_ok else "degraded"
    return jsonify({
        "status": status,
        "db": db_ok,
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
    }), 200 if db_ok else 503



# --- Admin Whitelist API ---

@app.route("/api/admin/whitelist", methods=["GET"])
@login_required
def api_admin_get_whitelist():
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    enabled = database.is_whitelist_enabled(org_id)
    emails = database.get_whitelist_emails(org_id)
    return jsonify({"ok": True, "enabled": enabled, "emails": emails})

@app.route("/api/admin/whitelist/toggle", methods=["POST"])
@login_required
def api_admin_toggle_whitelist():
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    data = request.json
    enabled = data.get("enabled", False)
    database.set_whitelist_status(org_id, enabled)
    return jsonify({"ok": True, "enabled": enabled})

@app.route("/api/admin/whitelist", methods=["POST"])
@login_required
def api_admin_add_whitelist():
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    data = request.json
    email = data.get("email", "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "อีเมลไม่ถูกต้อง"}), 400
        
    success = database.add_whitelist_email(org_id, email, session.get("user"))
    if success:
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": "อีเมลนี้มีอยู่ในระบบแล้ว"}), 400

@app.route("/api/admin/whitelist/<email>", methods=["DELETE"])
@login_required
def api_admin_remove_whitelist(email):
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    database.remove_whitelist_email(org_id, email)
    return jsonify({"ok": True})

if __name__ == "__main__":


    import os
    port = int(os.environ.get("PORT", 5000))
    
    # Optional sync on startup
    if os.environ.get("SKIP_SYNC") != "1":
        print(">>> Syncing and re-indexing Knowledge Base (Universal)...", flush=True)
        try:
            rag_engine.fix_categories()
            rag_engine.sync_uploads()
        except Exception as e:
            print(f"[!] Startup background update failed: {e}", flush=True)
    else:
        print(">>> Skipping startup sync as requested.")
        
    print(f">>> Starting Org Chatbot at http://127.0.0.1:{port}")
    
    # Critical Diagnostic: Print all routes
    print(">>> Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"   {rule.endpoint:20} -> {rule.rule}")
        
    # Run SocketIO server (disable reloader on Windows to prevent port conflicts)
    try:
        scheduler.start()
        print(">>> Background Scheduler started.")
    except Exception as se:
        print(f"[!] Scheduler failed to start: {se}")

    socketio.run(app, debug=False, port=port, host="0.0.0.0", use_reloader=False, allow_unsafe_werkzeug=True)
