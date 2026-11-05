# ULTIMATE CACHE BUSTER - v11.0.4 [THAI-VOICE]
import sys
import os
import io

# Force UTF-8 encoding for stdout/stderr to support emojis on Windows terminals
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from pathlib import Path
BASE_DIR = Path(__file__).parent.absolute()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dns_patch import apply_dns_patch_if_needed
apply_dns_patch_if_needed()

# Force UTF-8 output encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8': 
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
from pathlib import Path
BASE_DIR = Path(__file__).parent.absolute()
_orig_db_path = os.environ.get("DB_PATH")
load_dotenv(BASE_DIR / ".env", override=True, encoding="utf-8")
if _orig_db_path:
    os.environ["DB_PATH"] = _orig_db_path

import uuid
import time
import sqlite3
import threading
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from google import genai
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import rag_engine
import database
import export_service
import ai_providers
import notification_db
import billing
import payment
import google_drive_service
from google_drive_service import google_manager, GoogleWorkspaceManager
import settings_manager
from redis_manager import RedisManager
from reconciliation_service import ReconciliationService
from task_tracker import db_task_tracker
from knowledge_harvester import KnowledgeHarvester

# ─── Logging ─────────────────────────────────────────────────
from logging.handlers import RotatingFileHandler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            "bot_debug.log", encoding="utf-8",
            maxBytes=5 * 1024 * 1024,  # 5 MB ต่อไฟล์
            backupCount=3              # เก็บย้อนหลัง 3 ไฟล์ = สูงสุด 20 MB
        )
    ]
)
logger = logging.getLogger("OrgChatAI")

# Mute repetitive background noise from scheduler
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

# Filter out repetitive heartbeat / polling endpoint logs from werkzeug
class PollingLogFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if any(endpoint in msg for endpoint in ["/api/chat/unread", "/api/notifications"]):
            return False
        return True

logging.getLogger("werkzeug").addFilter(PollingLogFilter())

# ─── Sentry Initialization ───────────────────────────────────
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )
    logger.info("Sentry initialized.")
else:
    from routes.shared import is_production as _is_prod
    if _is_prod():
        logger.warning("⚠️  SENTRY_DSN ไม่ได้ตั้งค่าใน production — error จะไม่ถูกส่งไปแจ้งเตือน")
    else:
        logger.info("SENTRY_DSN not set. Sentry disabled.")


# ═══════════════════════════════════════════════════════════════
# Background Startup Tasks
# ═══════════════════════════════════════════════════════════════

def cleanup_old_exports():
    """Delete exported files older than 1 hour from static/downloads."""
    import time
    from pathlib import Path
    downloads_dir = Path("static/downloads")
    if not downloads_dir.exists():
        return
    now = time.time()
    count = 0
    for f in downloads_dir.glob("*"):
        if f.is_file() and (now - f.stat().st_mtime) > 3600:
            try:
                f.unlink()
                count += 1
            except Exception:
                pass
    if count > 0:
        print(f">>> Cleaned up {count} old export files from static/downloads", flush=True)

def async_startup_tasks():
    """Run heavy initialization tasks in background to avoid Cloudflare 524."""
    print(">>> Starting background initialization tasks...", flush=True)
    try:
        cleanup_old_exports()
        rag_engine.reinit_kb()  # Heavy ChromaDB sync — must stay in background

        # Warm up Google Drive/Sheets connection
        try:
            google_manager._initialize_thread_services()
            google_manager._validate_or_create_spreadsheet()
            google_manager.ensure_essential_sheets()
        except Exception as e:
            print(f">>> Google Workspace warm-up failed: {e}", flush=True)

        # Auto-Cleanup orphaned Knowledge Base files
        print(">>> Running automatic Knowledge Base cleanup...", flush=True)
        import kb_cleanup
        try:
            kb_cleanup.cleanup()
        except Exception as e:
            print(f">>> Auto-cleanup failed: {e}", flush=True)

        # Seed essential rows — use _get_conn() for WAL + busy_timeout
        conn = database._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM chat_rooms WHERE id = 1")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO chat_rooms (id, name, owner, organization_id) VALUES (1, 'กลุ่มทั่วไป (General)', 'System', 1)")

            cursor.execute("INSERT OR IGNORE INTO user_profiles (username, display_name, avatar_url) VALUES ('AI-Assistant', 'น้องพั้น (Nong Punch)', 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png')")
            cursor.execute("UPDATE user_profiles SET display_name = 'น้องพั้น (Nong Punch)' WHERE username = 'AI-Assistant'")
            cursor.execute("INSERT OR IGNORE INTO user_settings (username, role) VALUES ('Admin', 'admin')")
            cursor.execute("UPDATE user_settings SET role = 'admin' WHERE username = 'Admin'")

            # Add default users that belong to Org 1 into Room 1 (strict capitalization)
            cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (1, 'admin')")
            cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (1, 'AI-Assistant')")

            conn.commit()
        finally:
            conn.close()
        print(">>> Background initialization complete.", flush=True)
    except Exception as e:
        print(f">>> Background startup error: {e}", flush=True)

    # Ensure critical directories exist (Railway Volume หรือ local)
    _data_root = os.environ.get("DATA_DIR", ".")
    for _sub in [
        "uploads/social_feed", "uploads/kb", "uploads/meetings",
        "uploads/receipts_backup", "uploads/profiles", "uploads/group_profiles",
        "uploads/group_chat", "uploads/dm_chat", "uploads/voice",
        "exports", "backups", "static/uploads/logos", "static/uploads/signatures"
    ]:
        os.makedirs(os.path.join(_data_root, _sub), exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# DB Init (synchronous — before background tasks)
# ═══════════════════════════════════════════════════════════════

try:
    database.init_db()
    billing.init_billing_tables()
    database.kanban_init_db()
except Exception as _init_e:
    print(f">>> DB init warning: {_init_e}", flush=True)

if payment.is_configured() and payment.is_test_mode():
    logger.warning("=" * 60)
    logger.warning("⚠️  STRIPE TEST MODE — ระบบชำระเงินยังไม่ LIVE")
    logger.warning("   เปลี่ยน STRIPE_SECRET_KEY เป็น sk_live_... ก่อน go-live")
    logger.warning("=" * 60)

def schedule_reminder_background_worker():
    """Background worker that checks upcoming calendar schedules every 60 seconds and sends 15-minute LINE reminders."""
    import time
    from datetime import datetime
    reminded_events = set()
    
    while True:
        try:
            time.sleep(60)
            now = datetime.now()
            conn = database._get_conn()
            try:
                cursor = conn.cursor()
                today_str = now.strftime("%Y-%m-%d")
                cursor.execute("SELECT id, username, title, start_date, start_time, is_public, description, category, organization_id FROM schedules WHERE start_date >= ?", (today_str,))
                rows = cursor.fetchall()
                for row in rows:
                    sid, username, title, date_str, time_str, is_pub, desc, cat, org_id = row
                    if sid in reminded_events:
                        continue
                    try:
                        time_val = time_str if time_str else "09:00"
                        dt_str = f"{date_str} {time_val}"
                        event_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                        diff_minutes = (event_dt - now).total_seconds() / 60.0
                        
                        if 0 <= diff_minutes <= 15:
                            reminded_events.add(sid)
                            from routes.chat import broadcast_line_announcement, send_line_push_notification, push_to_org_line_groups
                            fields_data = {
                                "หัวข้อ": title,
                                "กำหนดเวลา": f"{date_str} @ {time_val} น.",
                                "เริ่มต้นในอีก": f"ประมาณ {max(1, int(diff_minutes))} นาที",
                                "หมวดหมู่": cat or "ทั่วไป",
                                "รายละเอียด": desc if desc else "-"
                            }
                            if is_pub:
                                broadcast_line_announcement(
                                    "⏰ เตือนความจำ: กำหนดการสาธารณะใกล้ถึงเวลา!",
                                    f"📌 กำหนดการสาธารณะ '{title}' จะเริ่มต้นในอีกประมาณ {max(1, int(diff_minutes))} นาที",
                                    fields=fields_data,
                                    org_id=org_id or 1
                                )
                            else:
                                send_line_push_notification(
                                    username,
                                    "⏰ เตือนความจำ: กำหนดการใกล้ถึงเวลา!",
                                    f"📌 กำหนดการของคุณ '{title}' จะเริ่มต้นในอีกประมาณ {max(1, int(diff_minutes))} นาที",
                                    fields=fields_data
                                )
                    except Exception:
                        pass
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"[Reminder Worker Error] {e}")

threading.Thread(target=async_startup_tasks, daemon=True).start()
threading.Thread(target=schedule_reminder_background_worker, daemon=True).start()


# ═══════════════════════════════════════════════════════════════
# App Factory
# ═══════════════════════════════════════════════════════════════

def create_app():
    """Flask Application Factory — creates, configures, and returns the app."""
    app = Flask(__name__)

    # ─── Secret Key & Cookie Security (P0-2 & P0-3) ───────────
    from routes.shared import is_production
    _secret = (os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY", "")).strip()
    _insecure_defaults = {"orgchat-super-secret-key-1234", "orgchat-default-secret-change-me", "dev-secret-change-in-prod"}
    
    if is_production():
        if not _secret or _secret in _insecure_defaults:
            raise RuntimeError(
                "CRITICAL SECURITY ERROR (P0-2): FLASK_SECRET_KEY (or SECRET_KEY) must be set to a strong random value in production!"
            )
    else:
        if not _secret or _secret in _insecure_defaults:
            import secrets as _sec
            _secret = _sec.token_hex(32)
            logger.warning(">>> FLASK_SECRET_KEY not set - using random key (sessions reset on restart). Set it in .env!")
            
    app.secret_key = _secret
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # P0-3: Default SESSION_COOKIE_SECURE=True in production, can override via env
    _cookie_secure_env = os.environ.get("SESSION_COOKIE_SECURE", "").strip().lower()
    if _cookie_secure_env == "true":
        app.config['SESSION_COOKIE_SECURE'] = True
    elif _cookie_secure_env == "false":
        app.config['SESSION_COOKIE_SECURE'] = False
    else:
        # ค่าเริ่มต้น: เปิด Secure เมื่อเป็น production หรือเมื่อ BASE_URL เป็น https (เช่นรันหลัง Cloudflare Tunnel)
        # เดิมผูกกับ APP_ENV=production อย่างเดียว ทำให้เว็บ HTTPS จริงส่ง session cookie ไม่มีแฟล็ก Secure
        # การเข้าผ่าน http://localhost ยังใช้ได้ เพราะเบราว์เซอร์ยอมรับ cookie Secure บน localhost
        app.config['SESSION_COOKIE_SECURE'] = is_production() or os.environ.get("BASE_URL", "").strip().lower().startswith("https://")

    # ─── Proxy Fix ───────────────────────────────────────────
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ─── CORS ────────────────────────────────────────────────
    # ใช้ origin เดียวกับ SocketIO (BASE_URL) — ป้องกัน wildcard + credentials
    from routes.shared import _cors_origins
    if _cors_origins == "*":
        CORS(app, supports_credentials=True)
        logger.warning("⚠️  CORS: BASE_URL ไม่ได้ตั้งค่า — ใช้ wildcard origin (ไม่ปลอดภัยสำหรับ production)")
    else:
        CORS(app, supports_credentials=True, origins=_cors_origins, vary_header=True)
        logger.info(f">>> CORS origins: {_cors_origins}")

    # ─── Init SocketIO & Limiter with app ────────────────────
    from routes.shared import socketio, _limiter, update_weather_background, batch_send_push_notification
    socketio.init_app(app)
    _limiter.init_app(app)

    # ─── Teardown: Google Context ────────────────────────────
    @app.teardown_request
    def teardown_google_context(exception=None):
        try:
            google_manager.clear_context()
        except Exception as e:
            logger.error(f"Error tearing down Google Workspace context: {e}")

    @app.after_request
    def add_header(r):
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        return r

    # ─── Register Blueprints ─────────────────────────────────
    from routes import ALL_BLUEPRINTS
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)
        logger.info(f">>> Registered Blueprint: {bp.name}")

    # ─── Security Headers ────────────────────────────────────
    @app.after_request
    def _add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers["Server"] = "OrgChat-Shield"
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")

        # 🛡️ Content-Security-Policy — restrict resource origins
        csp_parts = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com https://accounts.google.com https://apis.google.com https://js.stripe.com https://cdn.socket.io https://static.cloudflareinsights.com https://api.qrserver.com",
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.googleapis.com https://unpkg.com https://accounts.google.com",
            "img-src 'self' data: blob: https: http:",
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com data:",
            "connect-src 'self' https://api.open-meteo.com https://air-quality-api.open-meteo.com https://*.open-meteo.com https://api.openweathermap.org https://generativelanguage.googleapis.com https://api.groq.com https://api.openai.com https://accounts.google.com https://js.stripe.com https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://api.qrserver.com https://static.cloudflareinsights.com https://cdn.socket.io wss: ws:",
            "frame-src 'self' https://accounts.google.com https://js.stripe.com https://drive.google.com https://docs.google.com",
            "object-src 'none'",
            "base-uri 'self'",
        ]
        response.headers.setdefault("Content-Security-Policy", "; ".join(csp_parts))

        # 🛡️ Permissions-Policy — restrict browser features from third-party contexts
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(self), microphone=(self), geolocation=(), payment=(self), usb=()"
        )

        # HSTS เปิดเฉพาะเมื่อ BASE_URL เป็น https
        base = os.environ.get("BASE_URL", "")
        if base.startswith("https://"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.route("/api/csrf-token", methods=["GET"])
    def get_csrf_token_endpoint():
        from routes.shared import get_or_create_csrf_token
        return jsonify({"ok": True, "csrf_token": get_or_create_csrf_token()})

    # ─── Real-Time WAF Threat Patterns ──────────────────────
    import re as _waf_re
    _WAF_SQLI_PATTERN = _waf_re.compile(
        r"(?i)(\bUNION\s+(?:ALL\s+)?SELECT\b|\bSELECT\s+.+\s+FROM\b|\bDROP\s+TABLE\b|\bWAITFOR\s+DELAY\b|\bBENCHMARK\s*\(|\bSLEEP\s*\(\s*\d+\s*\)|'\s*OR\s*['\"\d]\s*=\s*['\"\d]|\bINFORMATION_SCHEMA\b)",
        _waf_re.IGNORECASE
    )
    _WAF_TRAVERSAL_PATTERN = _waf_re.compile(
        r"(?:\.\.[/\\]|\.\.%2f|\.\.%5c|%2e%2e|/etc/passwd|/etc/shadow|c:\\windows|win\.ini|boot\.ini)",
        _waf_re.IGNORECASE
    )
    _WAF_XSS_RCE_PATTERN = _waf_re.compile(
        r"(?i)(<\s*script[^>]*>|javascript\s*:|data\s*:\s*text/html|<\s*iframe[^>]*>|<\s*object[^>]*>|<\s*embed[^>]*>|onload\s*=\s*|onerror\s*=\s*)",
        _waf_re.IGNORECASE
    )

    def _inspect_waf_threats(req) -> str | None:
        """Inspects request path, query string and request body for common cyber attack payloads."""
        # 1. Inspect Path
        if _WAF_TRAVERSAL_PATTERN.search(req.path):
            return "Path Traversal / LFI Attack in URL Path"

        # 2. Inspect Query Parameters
        for k, v in req.args.items():
            if _WAF_SQLI_PATTERN.search(v) or _WAF_SQLI_PATTERN.search(k):
                return "SQL Injection Attack in URL Parameters"
            if _WAF_TRAVERSAL_PATTERN.search(v):
                return "Path Traversal Attack in URL Parameters"
            if _WAF_XSS_RCE_PATTERN.search(v):
                return "Cross-Site Scripting (XSS) in URL Parameters"

        # 3. Inspect Body for mutating requests (exempt chat message payloads which have AI Guardrails)
        if req.method in ("POST", "PUT", "PATCH") and not req.path.startswith("/api/chat") and not req.path.startswith("/line/"):
            try:
                if req.is_json:
                    raw_body = req.get_data(as_text=True)
                    if raw_body and len(raw_body) < 65536:
                        if _WAF_SQLI_PATTERN.search(raw_body):
                            return "SQL Injection Attack in Request Body"
                        if _WAF_TRAVERSAL_PATTERN.search(raw_body):
                            return "Path Traversal Attack in Request Body"
                        if _WAF_XSS_RCE_PATTERN.search(raw_body):
                            return "XSS Script Payload in Request Body"
            except Exception:
                pass

        return None

    def _get_ua_fingerprint(req):
        """U0-1: Stable User-Agent family & OS fingerprint.
        Resistant to minor browser version updates or navigation/fetch variance,
        while strictly detecting device/OS or browser cross-hijacking.
        """
        ua = req.user_agent
        platform = (ua.platform or "").lower()
        browser = (ua.browser or "").lower()
        version = ua.version or ""
        major = version.split('.')[0] if version else ""
        if platform or browser:
            return f"{platform}:{browser}:{major}"
        raw = (req.headers.get('User-Agent') or '').lower()
        p = 'win' if 'windows' in raw else ('mac' if 'macintosh' in raw or 'mac os' in raw else ('android' if 'android' in raw else ('ios' if 'iphone' in raw or 'ipad' in raw else 'other')))
        b = 'chrome' if 'chrome' in raw or 'crios' in raw else ('firefox' if 'firefox' in raw else ('safari' if 'safari' in raw else ('edge' if 'edg' in raw else 'other')))
        return f"{p}:{b}"

    # ─── Idle Session Timeout (2 hours) & CSRF Middleware ────
    _IDLE_SECONDS = 2 * 60 * 60  # 2 ชั่วโมง

    _ORG_CHECK_INTERVAL = 5 * 60  # re-validate org membership ทุก 5 นาที

    @app.before_request
    def _refresh_session_or_expire():
        from flask import session, request as _req
        import time as _time
        # ข้ามสำหรับ static files และ uploads
        if _req.path.startswith('/static') or _req.path.startswith('/uploads'):
            return

        # 🛑 1. Automated IP Blacklist Enforcement
        client_ip = _req.remote_addr or "unknown"
        is_blocked, block_reason = database.is_ip_blacklisted(client_ip)
        if is_blocked:
            from flask import jsonify as _json_ip
            logger.warning(f"🛑 Blocked Request from Blacklisted IP={client_ip} path={_req.path} reason={block_reason}")
            return _json_ip({"ok": False, "error": "ip_blocked", "message": f"IP ของท่านถูกระงับการเข้าถึงชั่วคราว ({block_reason})"}), 403

        # 🚨 2. Real-Time WAF Threat Inspection (Auto-Jail on malicious payloads)
        waf_threat = _inspect_waf_threats(_req)
        if waf_threat:
            from flask import jsonify as _json_waf
            logger.critical(f"🚨 [WAF AUTO-JAIL] Intercepted {waf_threat} from IP={client_ip} path={_req.path}")
            database.block_ip(client_ip, reason=f"WAF: {waf_threat}", duration_minutes=120)
            try:
                database.log_audit_event("System", "WAF_ATTACK_BLOCKED", f"Blocked {waf_threat} on {_req.path}", client_ip, 1)
            except Exception:
                pass
            return _json_waf({"ok": False, "error": "waf_blocked", "message": f"คำขอถูกปฏิเสธเนื่องจากตรวจพบคำสั่งที่มีความเสี่ยงต่อความปลอดภัย ({waf_threat})"}), 403

        # 🛡️ 3. Anti-CSRF Token Enforcement for mutating methods
        if _req.method in ("POST", "PUT", "DELETE", "PATCH"):
            csrf_exempt = (
                _req.path.startswith('/line/webhook') or 
                _req.path.startswith('/stripe/webhook') or
                _req.path.startswith('/api/csrf-token') or
                _req.path.startswith('/api/login') or
                _req.path.startswith('/api/qr/') or
                _req.path.startswith('/api/auth/google/') or
                _req.path.startswith('/api/auth/forgot-password') or
                _req.path.startswith('/api/auth/verify-reset-otp') or
                _req.path.startswith('/api/auth/reset-password') or
                _req.path.startswith('/api/org/signup') or
                _req.path.startswith('/api/org/create-for-user') or
                _req.path.startswith('/api/org/join-via-invite') or
                _req.path.startswith('/api/org/join-by-token') or
                _req.path.startswith('/api/superadmin/')
            )

            if not csrf_exempt and 'user' in session:
                from routes.shared import validate_csrf_token
                csrf_header = _req.headers.get("X-CSRF-Token")
                if not csrf_header or not validate_csrf_token(csrf_header):
                    from flask import jsonify as _json_csrf
                    logger.warning(f"🛡️ CSRF Blocked: Invalid or missing token from IP={_req.remote_addr} path={_req.path}")
                    return _json_csrf({"ok": False, "error": "csrf_invalid", "message": "คำขอไม่ถูกต้องหรือ CSRF token หมดอายุ กรุณารีเฟรชหน้าเว็บ"}), 403
        if 'user' not in session:
            return

        # 🛡️ 4. Session Hijacking Prevention (User-Agent Family Fingerprint)
        ua_fingerprint = _get_ua_fingerprint(_req)
        stored_ua = session.get('_ua_hash')
        if stored_ua is None:
            session['_ua_hash'] = ua_fingerprint
        elif stored_ua != ua_fingerprint:
            logger.warning(
                f"🛡️ Session Hijacking Blocked: UA mismatch for user={session.get('user')} "
                f"IP={_req.remote_addr} (stored='{stored_ua}', current='{ua_fingerprint}')"
            )
            session.clear()
            if _req.path.startswith('/api/') or _req.path.startswith('/line/') or _req.is_json:
                from flask import jsonify as _json_hijack
                return _json_hijack({
                    "ok": False,
                    "error": "session_hijack_detected",
                    "message": "ตรวจพบการเข้าสู่ระบบจากอุปกรณ์หรือเบราว์เซอร์อื่น กรุณาเข้าสู่ระบบใหม่เพื่อความปลอดภัย"
                }), 401
            from flask import redirect as _redir_hijack
            return _redir_hijack('/?session_invalid=1')

        now = _time.time()

        # 🔐 5. Multi-Device Session Invalidation (Session Versioning - throttled every 30s)
        current_username = session.get('user')
        if current_username:
            last_ver_check = session.get('_last_ver_check', 0)
            if now - last_ver_check > 30:
                session['_last_ver_check'] = now
                try:
                    db_session_ver = database.get_user_session_version(current_username)
                    sess_ver = session.get('session_version')
                    if sess_ver is not None and sess_ver != db_session_ver:
                        logger.warning(f"🔐 [Session Revoked] User {current_username} session version mismatch (sess={sess_ver}, db={db_session_ver}) — revoking session")
                        session.clear()
                        if _req.path.startswith('/api/') or _req.path.startswith('/line/') or _req.is_json:
                            from flask import jsonify as _json_revoked
                            return _json_revoked({"ok": False, "error": "session_revoked", "message": "รหัสผ่านหรือสิทธิ์ของคุณมีการเปลี่ยนแปลง กรุณาเข้าสู่ระบบใหม่"}), 401
                        from flask import redirect as _redir_revoked
                        return _redir_revoked('/?session_revoked=1')
                    elif sess_ver is None:
                        session['session_version'] = db_session_ver
                except Exception as _sve:
                    logger.debug(f"Session version check bypass: {_sve}")
        # ⏱️ เวลาหมดอายุเซสชันตามนโยบายองค์กร (cache ใน session 60 วินาที)
        _lim = session.get('_idle_lim')
        if not _lim or now - _lim[0] > 60:
            try:
                from db import org_security as _osec
                _lim = [now, _osec.idle_seconds_for_user(session.get('user'), _IDLE_SECONDS)]
            except Exception:
                _lim = [now, _IDLE_SECONDS]
            session['_idle_lim'] = _lim
        last = session.get('_last_active', now)
        if now - last > _lim[1]:
            session.clear()
            # API / webhook → return 401 JSON; page request → redirect to login
            if _req.path.startswith('/api/') or _req.path.startswith('/line/') or _req.is_json:
                from flask import jsonify as _json
                return _json({"ok": False, "error": "session_expired", "message": "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่"}), 401
            from flask import redirect as _redir
            return _redir('/?session_expired=1')
        session['_last_active'] = now

        # 🛡️ นโยบายองค์กรบังคับ 2FA: ผู้ใช้ที่ยังไม่เปิดต้องตั้งค่าก่อนจึงใช้งาน API อื่นได้
        if _req.path.startswith('/api/') and not any(_req.path.startswith(p) for p in (
                '/api/2fa/', '/api/logout', '/api/csrf-token', '/api/me', '/api/org/me', '/api/org/security/my-status', '/api/login', '/api/qr/')):
            _need = session.get('_2fa_need')
            if not _need or now - _need[0] > 60:
                try:
                    from db import org_security as _osec2
                    _need = [now, bool(_osec2.needs_2fa_setup(session.get('user')))]
                except Exception:
                    _need = [now, False]
                session['_2fa_need'] = _need
            if _need[1]:
                from flask import jsonify as _json_2fa
                return _json_2fa({"ok": False, "error": "2fa_setup_required",
                                 "message": "องค์กรของคุณบังคับให้เปิดการยืนยันตัวตนสองชั้น (2FA) กรุณาตั้งค่าก่อนใช้งานต่อ"}), 403

        # Re-validate user is_active + org membership ทุก 5 นาที
        org_id  = session.get('org_id')
        username = session.get('user')
        if username:
            last_check = session.get('_org_check_at', 0)
            if now - last_check > _ORG_CHECK_INTERVAL:
                session['_org_check_at'] = now

                # ตรวจ is_active — ถ้า admin deactivate user ระหว่าง session → logout ทันที
                try:
                    _us = database.get_user_setting(username)
                    if _us and not _us.get('is_active', 1):
                        session.clear()
                        if _req.path.startswith('/api/') or _req.path.startswith('/line/') or _req.is_json:
                            from flask import jsonify as _json2
                            return _json2({"ok": False, "error": "account_deactivated",
                                          "message": "บัญชีของคุณถูกระงับ กรุณาติดต่อผู้ดูแลระบบ"}), 403
                        from flask import redirect as _redir2
                        return _redir2('/?account_deactivated=1')
                except Exception:
                    pass

                # ตรวจ org membership
                if org_id and not database.is_org_member_active(org_id, username):
                    session.pop('org_id', None)
                    session.pop('org_role', None)
                    session.pop('_org_check_at', None)

        # Enforce thread-local Google context for the active user request
        active_user = session.get('user')
        active_org = session.get('org_id')
        if active_user and active_org:
            try:
                google_manager.set_context(username=active_user, org_id=active_org)
            except Exception as context_err:
                logger.error(f"Failed to auto-set Google context in request hook: {context_err}")

    # ─── Global Error Handlers ───────────────────────────────
    ERROR_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ขออภัย ระบบขัดข้องชั่วคราว</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Sarabun:wght@400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com/3.4.16"></script>
    <style>
        body { font-family: 'Inter', 'Sarabun', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white rounded-3xl p-8 shadow-xl border border-slate-100 text-center">
        <div class="w-16 h-16 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
        </div>
        <h2 class="text-2xl font-bold mb-3 text-slate-900">ขออภัย ระบบขัดข้องชั่วคราว</h2>
        <p class="text-slate-500 text-sm mb-6 leading-relaxed">
            {{ error_message }}
        </p>
        <div class="flex flex-col gap-2">
            <a href="/" class="w-full py-2.5 px-4 text-white rounded-xl font-semibold text-sm transition-all shadow-lg text-center bg-blue-600 hover:bg-blue-700">
                กลับสู่หน้าหลัก
            </a>
            <button onclick="window.location.reload()" class="w-full py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold text-sm transition-all text-center">
                ลองใหม่อีกครั้ง
            </button>
        </div>
    </div>
</body>
</html>"""

    @app.errorhandler(429)
    def ratelimit_handler(e):
        from flask import render_template_string
        msg = "คุณทำรายการถี่เกินไป กรุณารอสักครู่ (ประมาณ 1 นาที) แล้วลองใหม่อีกครั้งค่ะ"
        if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "ok": False,
                "error": "rate_limit_exceeded",
                "message": msg
            }), 429
        return render_template_string(ERROR_TEMPLATE, error_message=msg), 429

    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template_string
        logger.exception("Global 500 Error Handler caught exception:")
        msg = "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง หรือติดต่อผู้ดูแลระบบค่ะ"
        if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "ok": False,
                "error": "internal_error",
                "message": msg
            }), 500
        return render_template_string(ERROR_TEMPLATE, error_message=msg), 500

    @app.errorhandler(sqlite3.OperationalError)
    def sqlite_operational_error(e):
        from flask import render_template_string
        err_str = str(e).lower()
        if "locked" in err_str or "busy" in err_str:
            logger.warning(f"⚠️ [DB Busy/Locked] Handled by global handler: {e}")
            msg = "ระบบกำลังประมวลผลข้อมูลการเงินหรือกระทบยอดอยู่ชั่วคราว กรุณากดลองใหม่อีกครั้งใน 2-3 วินาทีค่ะ"
            if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "ok": False,
                    "error": "db_busy",
                    "message": msg
                }), 503
            return render_template_string(ERROR_TEMPLATE, error_message=msg), 503
        
        logger.exception(f"Global DB error handler caught OperationalError: {e}")
        msg = f"ระบบฐานข้อมูลขัดข้องชั่วคราว: {e}"
        if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "ok": False,
                "error": "db_error",
                "message": msg
            }), 500
        return render_template_string(ERROR_TEMPLATE, error_message=msg), 500

    @app.errorhandler(400)
    def bad_request_error(e):
        from flask import render_template_string
        msg = "คำขอไม่ถูกต้อง (Bad Request) กรุณาตรวจสอบข้อมูลที่ส่งเข้ามาค่ะ"
        if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "ok": False,
                "error": "bad_request",
                "message": str(e) or msg
            }), 400
        return render_template_string(ERROR_TEMPLATE, error_message=msg), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        from flask import render_template_string
        msg = "คุณไม่มีสิทธิ์เข้าถึงส่วนนี้ (Forbidden)"
        if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "ok": False,
                "error": "forbidden",
                "message": msg
            }), 403
        return render_template_string(ERROR_TEMPLATE, error_message=msg), 403

    @app.errorhandler(404)
    def not_found_error(e):
        from flask import render_template_string
        msg = "ไม่พบหน้าที่ต้องการ (404 Not Found)"
        if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "ok": False,
                "error": "not_found",
                "message": f"Endpoint not found: {request.path}"
            }), 404
        return render_template_string(ERROR_TEMPLATE, error_message=msg), 404

    return app


# ═══════════════════════════════════════════════════════════════
# Create the App Instance
# ═══════════════════════════════════════════════════════════════

app = create_app()

# ─── Shared references for backward compatibility ────────────
from routes.shared import socketio, update_weather_background, batch_send_push_notification


# ═══════════════════════════════════════════════════════════════
# APScheduler: Weather, Reconciliation, Daily Summary
# ═══════════════════════════════════════════════════════════════

try:
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(update_weather_background, 'interval', minutes=30)
    try:
        _scheduler.start()
        update_weather_background()
    except Exception as e:
        logger.warning(f">>> Scheduler start failed: {e}")

    def _scheduled_auto_reconciliation():
        """งานสำรอง: กระทบยอดอัตโนมัติทุก 30 นาที กันพลาด"""
        try:
            print(">>> [Scheduler] Running periodic reconciliation...", flush=True)
            # 1. Reconcile default system-level sheet first (skip if credentials are invalid)
            if google_manager.drive_service and google_manager.sheets_service and google_manager.spreadsheet_id:
                try:
                    # Pre-check: verify credentials still valid before heavy reconciliation
                    google_manager.sheets_service.spreadsheets().get(
                        spreadsheetId=google_manager.spreadsheet_id, fields='spreadsheetId'
                    ).execute()
                    google_manager.auto_reconcile_internal()
                    print(">>> [Scheduler] Periodic reconciliation complete for default sheet.", flush=True)
                except Exception as cred_err:
                    err_str = str(cred_err)
                    if 'invalid_grant' in err_str or 'Invalid JWT' in err_str or '401' in err_str:
                        logger.info(">>> [Scheduler] Default service account credentials invalid — skipping default reconciliation.")
                    else:
                        logger.error(f"Reconciliation error (default sheet): {cred_err}")
            else:
                print(">>> [Scheduler] Google services or Spreadsheet ID not ready for default sheet.", flush=True)
            
            # 2. Reconcile all connected organizations dynamically
            from oauth2_service import oauth2_service
            all_orgs = database.get_all_orgs_with_stats()
            for org in all_orgs:
                org_id = org["id"]
                if oauth2_service.is_org_connected(org_id):
                    try:
                        with google_manager.secure_context(username=None, org_id=org_id):
                            if google_manager.sheets_service and google_manager.spreadsheet_id:
                                google_manager.auto_reconcile_internal()
                                print(f">>> [Scheduler] Periodic reconciliation complete for org {org_id}.", flush=True)
                    except Exception as ex:
                        print(f">>> [Scheduler] Periodic reconciliation failed for org {org_id}: {ex}", flush=True)
        except Exception as e:
            print(f">>> [Scheduler] Recon Error: {e}", flush=True)

    _scheduler.add_job(_scheduled_auto_reconciliation, 'interval', minutes=30, id='periodic_recon')

    def _scheduled_daily_summary():
        """Run daily AI summary per org at 08:00 — ส่งเฉพาะ users ของ org นั้น"""
        try:
            all_orgs = database.get_all_orgs_with_stats()
            provider = ai_providers.get_provider()
            for org in all_orgs:
                org_id = org["id"]
                try:
                    # ไม่ส่ง AI summary ให้ free plan — ประหยัด API token
                    if billing.get_effective_plan(org_id) == "free":
                        continue
                    data = database.get_daily_activities(org_id=org_id)
                    posts = data.get("posts", [])
                    schedules = data.get("schedules", [])
                    if not posts and not schedules:
                        continue
                    posts_text = "\n".join([f"- {p['author']} โพสต์: {p['content'][:80]}" for p in posts])
                    sched_text = "\n".join([f"- {s['title']} วันที่ {s['date']} {s['time']}" for s in schedules])
                    prompt = (
                        "สรุปกิจกรรมสำคัญประจำวันในบริษัทให้เพื่อนร่วมงานฟังแบบเป็นกันเองแต่เป็นมืออาชีพ (ไม่เกิน 3 ประโยค) ใช้สำนวนภาษาไทยที่เป็นธรรมชาติเหมือนเพื่อนร่วมงานเล่าให้กันฟัง:\n"
                        f"โพสต์:{posts_text}\nตาราง:{sched_text}"
                    )
                    summary = ""
                    for chunk in provider.chat_stream(prompt, [], "คุณคือ OrgChat AI ผู้ช่วยสรุปข่าวสารองค์กร"):
                        if chunk:
                            summary += chunk
                    if summary:
                        unames = database.get_all_usernames(org_id=org_id)
                        notification_db.notify_users(
                            unames, "daily_summary", "Daily Briefing",
                            summary[:200], link="#feed"
                        )
                        batch_send_push_notification(unames, "Daily Briefing", summary[:120], url="/")
                        logger.info(f">>> Daily summary org={org_id} → {len(unames)} users")
                except Exception as _oe:
                    logger.error(f">>> Daily summary error org={org_id}: {_oe}")
        except Exception as e:
            logger.error(f">>> Scheduled daily summary error: {e}")

    _scheduler.add_job(_scheduled_daily_summary, 'cron', hour=8, minute=0, id='daily_summary')

    def _scheduled_executive_brief():
        """Aggregates business data per org and sends a smart Morning Briefing Flex Card to linked admins & members at 08:30."""
        try:
            all_orgs = database.get_all_orgs_with_stats()
            today_str = datetime.now().strftime("%d/%m/%Y")
            for org in all_orgs:
                org_id = org["id"]
                org_name = org.get("name") or "OrgChat Workspace"
                try:
                    # ดึงข้อมูลภาพรวมขององค์กร
                    data = database.get_executive_summary_data(org_id=org_id)
                    finance = data.get("finance", {})
                    leaves = data.get("leaves", [])
                    tasks = data.get("tasks", [])
                    pending_count = data.get("pending_leaves_count", 0)

                    # สร้าง LINE Flex Bubble สรุปยามเช้า
                    from routes.chat import create_morning_briefing_flex_bubble, send_line_push_notification
                    brief_bubble = create_morning_briefing_flex_bubble(
                        org_name=org_name,
                        date_str=today_str,
                        meetings=tasks,
                        leaves_today=leaves,
                        expenses_24h=finance,
                        pending_leaves_count=pending_count
                    )

                    members = database.get_org_members(org_id)
                    admin_unames = [m["username"] for m in members if m.get("role") == "admin"]
                    all_unames = [m["username"] for m in members]

                    # ส่งแจ้งเตือนในระบบเว็บ Dashboard
                    summary_web = f"🌅 สรุปยามเช้า {org_name}: วันนี้มี {len(tasks)} นัดหมาย, {len(leaves)} คนลา, ค่าใช้จ่าย 24 ชม. {finance.get('total_amount', 0):,.2f} ฿"
                    if admin_unames:
                        notification_db.notify_users(admin_unames, "exec_brief", "Smart Morning Briefing", summary_web, link="#dashboard")

                    # ส่ง LINE Push Notification หาผู้ใช้ทุกคนที่มีการผูก LINE ในองค์กร
                    for m in members:
                        uname = m["username"]
                        threading.Thread(target=send_line_push_notification, args=(
                            uname,
                            f"🌅 สรุปภาพรวมยามเช้า • {org_name}",
                            summary_web
                        ), kwargs={"flex_bubble": brief_bubble}).start()

                    logger.info(f">>> 🌅 Smart Morning Briefing delivered for org={org_id} ({org_name}) → {len(members)} members")
                except Exception as _oe:
                    logger.error(f">>> ⚠️ Morning brief error org={org_id}: {_oe}")
        except Exception as e:
            logger.error(f">>> ⚠️ Scheduled morning brief error: {e}")

    _scheduler.add_job(_scheduled_executive_brief, 'cron', hour=8, minute=30, id='morning_executive_brief')


    def _scheduled_knowledge_harvest():
        """Analyzes chat to suggest new Wiki content."""
        try:
            # Analyze recent 100 messages per org
            all_orgs = database.get_all_orgs_with_stats()
            for _org in all_orgs:
                try:
                    KnowledgeHarvester.analyze_recent_messages(org_id=_org["id"], limit=100)
                except Exception:
                    pass
            logger.info(">>> Knowledge Harvesting check completed.")
        except Exception as e:
            logger.error(f">>> Scheduled knowledge harvest error: {e}")

    _scheduler.add_job(_scheduled_knowledge_harvest, 'cron', hour=22, minute=0, id='wiki_harvest')

    # Plan expiry reminder ทุกวัน 09:00 — แทน daemon thread ที่ timing ขึ้นกับเวลา restart
    def _scheduled_expiry_reminder():
        try:
            from routes.admin import check_expiring_plans
            check_expiring_plans()
        except Exception as _e:
            logger.warning(f"[ExpiryReminder] scheduled error: {_e}")

    # SQLite backup ทุกวัน 02:00 — off-peak
    def _scheduled_db_backup():
        try:
            from routes.admin import _backup_sqlite
            _backup_sqlite()
        except Exception as _e:
            logger.warning(f"[Backup] scheduled error: {_e}")

    _scheduler.add_job(_scheduled_expiry_reminder, 'cron', hour=9, minute=0, id='expiry_reminder')

    def _scheduled_monthly_summary():
        try:
            import billing as _billing
            _billing.send_monthly_summary_all_orgs()
        except Exception as _e:
            logger.warning(f"[MonthlySummary] scheduled error: {_e}")

    # ส่งสรุปรายเดือนทุกวันสุดท้ายของเดือน เวลา 20:00
    _scheduler.add_job(_scheduled_monthly_summary, 'cron', day='last', hour=20, minute=0, id='monthly_summary')
    _scheduler.add_job(_scheduled_db_backup, 'cron', hour=2, minute=0, id='db_backup')

    # ล้าง KB processing ที่ค้างทุก 30 นาที
    def _scheduled_kb_cleanup():
        try:
            cleaned = rag_engine.cleanup_stale_processing(max_age_minutes=30)
            if cleaned:
                logger.info(f"[KBCleanup] Cleaned {cleaned} stale processing files")
        except Exception as _e:
            logger.warning(f"[KBCleanup] error: {_e}")

    _scheduler.add_job(_scheduled_kb_cleanup, 'interval', minutes=30, id='kb_cleanup')

    # เช็คและส่ง broadcast ที่ตั้งเวลาไว้ทุก 1 นาที
    def _scheduled_line_broadcasts():
        try:
            from routes.chat import broadcast_line_announcement
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            pending = database.get_pending_broadcasts(now_str)
            for item in pending:
                bid = item["id"]
                text = item["text"]
                database.update_line_broadcast_status(bid, "Processing")
                try:
                    success = broadcast_line_announcement(title="ประกาศจากแอดมิน", text=text, org_id=item.get("org_id", 1))
                    status = "success" if success else "failed"
                    database.update_line_broadcast_status(bid, status)
                    logger.info(f"Scheduled broadcast {bid} processed: {status}")
                except Exception as ex:
                    database.update_line_broadcast_status(bid, "failed")
                    logger.error(f"Error processing scheduled broadcast {bid}: {ex}")
        except Exception as _e:
            logger.warning(f"[ScheduledBroadcasts] error: {_e}")

    _scheduler.add_job(_scheduled_line_broadcasts, 'interval', minutes=1, id='line_broadcasts')

    # ⏰ แจ้งเตือนนัดหมายและการประชุมล่วงหน้า (รันตรวจเช็คทุก 1 นาที)
    def _scheduled_meeting_reminders():
        try:
            from routes.chat import send_meeting_reminder_line
            # ดึงนัดหมายที่กำลังจะเริ่มในอีก 30 นาที
            upcoming = database.get_upcoming_schedules(window_minutes=30)
            for sch in upcoming:
                sid = sch.get("id")
                try:
                    send_meeting_reminder_line(sch, minutes_before=30)
                    database.mark_schedule_reminder_sent(sid)
                    logger.info(f"⏰ [Meeting Reminder] Sent reminder for schedule #{sid}: {sch.get('title')}")
                except Exception as ex:
                    logger.error(f"Error sending meeting reminder for schedule #{sid}: {ex}")
        except Exception as _e:
            logger.warning(f"[ScheduledMeetingReminders] error: {_e}")

    _scheduler.add_job(_scheduled_meeting_reminders, 'interval', minutes=1, id='meeting_reminders')

    # 🧹 ทำความสะอาดและ Optimize ฐานข้อมูล SQLite (WAL Checkpoint ประจำวันเวลา 03:30 + Optimize วันอาทิตย์)
    def _scheduled_db_wal_checkpoint():
        try:
            res = database.optimize_and_checkpoint_db()
            logger.info(f"🧹 [Scheduled DB Maintenance] {res}")
        except Exception as _e:
            logger.warning(f"[Scheduled DB Maintenance] error: {_e}")

    _scheduler.add_job(_scheduled_db_wal_checkpoint, 'cron', hour=3, minute=30, id='db_wal_checkpoint')
    _scheduler.add_job(_scheduled_db_wal_checkpoint, 'cron', day_of_week='sun', hour=3, minute=0, id='db_optimize')

    # 📤 อัตโนมัติ Sync ข้อมูล Offline Uploads (สลิป/ใบเสร็จ) ขึ้น Google Drive & Sheets ทุก 5 นาที
    def _scheduled_offline_queue_sync():
        try:
            from tools.offline_storage import sync_all_pending_offline_uploads
            res = sync_all_pending_offline_uploads(limit=20)
            if res.get("synced", 0) > 0:
                logger.info(f"📤 [Offline Sync Auto-Job] Successfully synced {res['synced']} items to cloud.")
        except Exception as _sync_e:
            logger.warning(f"[Offline Sync Auto-Job] Error during periodic sync: {_sync_e}")

    _scheduler.add_job(_scheduled_offline_queue_sync, 'interval', minutes=5, id='offline_queue_sync')

except ImportError:
    logger.info(">>> APScheduler not installed - run: pip install APScheduler")


# ═══════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))

    # Optional sync on startup
    if os.environ.get("SKIP_SYNC") != "1":
        print(">>> Syncing and re-indexing Knowledge Base (Universal)...", flush=True)
        try:
            rag_engine.fix_categories()
            rag_engine.sync_uploads()
        except Exception as e:
            print(f"[!] Startup background update failed: {e}", flush=True)
    else:
        logger.warning(">>> Skipping startup sync as requested.")

    # ล้างไฟล์ค้าง processing จาก session ก่อน restart
    try:
        cleaned = rag_engine.cleanup_stale_processing(max_age_minutes=30)
        if cleaned:
            print(f">>> [Startup] Cleaned {cleaned} stale processing files", flush=True)
    except Exception as _ce:
        print(f"[!] Cleanup stale failed: {_ce}", flush=True)

    logger.info(f">>> Starting Org Chatbot at http://127.0.0.1:{port}")

    # Print registered routes
    logger.info(">>> Registered Routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"   {rule.endpoint:30} -> {rule.rule}")

    socketio.run(app, debug=False, port=port, host="0.0.0.0", use_reloader=False, allow_unsafe_werkzeug=True)
