# ULTIMATE CACHE BUSTER - v11.0.4 [THAI-VOICE]
import sys
import os
import io
# ระบบรันบน app_server.py เพื่อบังคับให้ Railway ล้างแคชใหม่ทั้งหมดครับ
print(">>> SYSTEM v11.0.4 [ULTIMATE/THAI-VOICE/GTHREAD/BLUEPRINT] READY.", flush=True)

# Force UTF-8 output encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8': 
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
from pathlib import Path
BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / ".env", override=True)

import uuid
import time
import sqlite3
import threading
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

print(">>> flask...", flush=True)
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

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
print(">>> billing...", flush=True)
import billing
print(">>> payment...", flush=True)
import payment
print(">>> google_drive_service...", flush=True)
import google_drive_service
from google_drive_service import google_manager, GoogleWorkspaceManager
print(">>> settings_manager...", flush=True)
import settings_manager
print(">>> redis_manager...", flush=True)
from redis_manager import RedisManager
print(">>> reconciliation_service...", flush=True)
from reconciliation_service import ReconciliationService
print(">>> importing task_tracker...", flush=True)
from task_tracker import db_task_tracker
from knowledge_harvester import KnowledgeHarvester
print(">>> all imports done.", flush=True)

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

# ─── Sentry Initialization ───────────────────────────────────
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
                cursor.execute("INSERT INTO chat_rooms (id, name, owner) VALUES (1, 'กลุ่มทั่วไป (General)', 'System')")

            cursor.execute("INSERT OR IGNORE INTO user_profiles (username, display_name, avatar_url) VALUES ('AI-Assistant', 'น้องพั้น (Nong Punch)', 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png')")
            cursor.execute("UPDATE user_profiles SET display_name = 'น้องพั้น (Nong Punch)' WHERE username = 'AI-Assistant'")
            cursor.execute("INSERT OR IGNORE INTO user_settings (username, role) VALUES ('Admin', 'admin')")
            cursor.execute("UPDATE user_settings SET role = 'admin' WHERE username = 'Admin'")

            temp_users = ["admin", "few", "do", "AI-Assistant"]
            for u in temp_users:
                cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (1, ?)", (u.capitalize(),))

            conn.commit()
        finally:
            conn.close()
        print(">>> Background initialization complete.", flush=True)
    except Exception as e:
        print(f">>> Background startup error: {e}", flush=True)

    # Ensure critical directories exist
    os.makedirs("uploads/social_feed", exist_ok=True)
    os.makedirs("uploads/kb", exist_ok=True)
    os.makedirs("exports", exist_ok=True)


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

threading.Thread(target=async_startup_tasks, daemon=True).start()


# ═══════════════════════════════════════════════════════════════
# App Factory
# ═══════════════════════════════════════════════════════════════

def create_app():
    """Flask Application Factory — creates, configures, and returns the app."""
    app = Flask(__name__)

    # ─── Secret Key ──────────────────────────────────────────
    _secret = os.environ.get("FLASK_SECRET_KEY", "")
    if not _secret or _secret == "orgchat-super-secret-key-1234":
        import secrets as _sec
        _secret = _sec.token_hex(32)
        logger.warning(">>> FLASK_SECRET_KEY not set - using random key (sessions reset on restart). Set it in .env!")
    app.secret_key = _secret
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload

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
        # HSTS เปิดเฉพาะเมื่อ BASE_URL เป็น https
        base = os.environ.get("BASE_URL", "")
        if base.startswith("https://"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    # ─── Idle Session Timeout (2 hours) ──────────────────────
    _IDLE_SECONDS = 2 * 60 * 60  # 2 ชั่วโมง

    _ORG_CHECK_INTERVAL = 5 * 60  # re-validate org membership ทุก 5 นาที

    @app.before_request
    def _refresh_session_or_expire():
        from flask import session, request as _req
        import time as _time
        # ข้ามสำหรับ static files และ uploads
        if _req.path.startswith('/static') or _req.path.startswith('/uploads'):
            return
        if 'user' not in session:
            return
        now = _time.time()
        last = session.get('_last_active', now)
        if now - last > _IDLE_SECONDS:
            session.clear()
            # API / webhook → return 401 JSON; page request → redirect to login
            if _req.path.startswith('/api/') or _req.path.startswith('/line/') or _req.is_json:
                from flask import jsonify as _json
                return _json({"ok": False, "error": "session_expired", "message": "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่"}), 401
            from flask import redirect as _redir
            return _redir('/?session_expired=1')
        session['_last_active'] = now

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
            if google_manager.drive_service and google_manager.sheets_service and google_manager.spreadsheet_id:
                google_manager.auto_reconcile_internal()
                print(">>> [Scheduler] Periodic reconciliation complete.", flush=True)
            else:
                print(">>> [Scheduler] Google services or Spreadsheet ID not ready.", flush=True)
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
                        print(f">>> Daily summary org={org_id} → {len(unames)} users")
                except Exception as _oe:
                    print(f">>> Daily summary error org={org_id}: {_oe}")
        except Exception as e:
            print(f">>> Scheduled daily summary error: {e}")

    _scheduler.add_job(_scheduled_daily_summary, 'cron', hour=8, minute=0, id='daily_summary')

    def _scheduled_executive_brief():
        """Aggregates business data per org and sends a briefing to each org's admins only."""
        try:
            all_orgs = database.get_all_orgs_with_stats()
            for org in all_orgs:
                org_id = org["id"]
                try:
                    # ส่งเฉพาะ paid plan — free plan ไม่มี financial dashboard
                    if billing.get_effective_plan(org_id) == "free":
                        continue

                    data = database.get_executive_summary_data(org_id=org_id)
                    finance = data.get("finance", {})
                    leaves = data.get("leaves", [])
                    tasks = data.get("tasks", [])

                    cf_data = database.get_cash_flow_projection(org_id=org_id)
                    projection = cf_data.get("projection", 0)
                    top_cats = cf_data.get("top_categories", [])

                    summary = "📊 **สรุปภาพรวมผู้บริหาร (Executive Brief)**\n\n"
                    summary += f"💰 **การเงิน:** มีรายจ่ายใหม่ {finance.get('count', 0)} รายการ ยอดรวม {finance.get('total_amount', 0):,.2f} บาท\n"
                    summary += f"📈 **พยากรณ์รายจ่ายเดือนหน้า:** ~{projection:,.0f} บาท\n"

                    if top_cats:
                        summary += f"🔍 **หมวดหมู่หลัก:** {', '.join(c['category'] for c in top_cats)}\n"

                    summary += "\n"
                    if leaves:
                        summary += "👤 **พนักงานลา:** " + ", ".join([f"{l['display_name']} ({l['leave_type']})" for l in leaves]) + "\n"
                    else:
                        summary += "👤 **พนักงานลา:** วันนี้ไม่มีพนักงานแจ้งลา\n"

                    if tasks:
                        summary += f"📅 **งานวันนี้ ({len(tasks)}):** " + ", ".join([t['title'] for t in tasks[:3]]) + ("..." if len(tasks) > 3 else "") + "\n"

                    # ส่งเฉพาะ admin ของ org — ไม่ใช่ทุกคน (exec brief = สำหรับผู้บริหาร)
                    members = database.get_org_members(org_id)
                    admin_unames = [m["username"] for m in members if m.get("role") == "admin"]
                    if not admin_unames:
                        continue
                    notification_db.notify_users(admin_unames, "exec_brief", "Executive Summary", summary, link="#dashboard")
                    print(f">>> Executive Briefing org={org_id} → {len(admin_unames)} admins")
                except Exception as _oe:
                    print(f">>> Executive brief error org={org_id}: {_oe}")
        except Exception as e:
            print(f">>> Scheduled executive brief error: {e}")

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
            print(">>> Knowledge Harvesting check completed.")
        except Exception as e:
            print(f">>> Scheduled knowledge harvest error: {e}")

    _scheduler.add_job(_scheduled_executive_brief, 'cron', hour=8, minute=30, id='exec_brief')
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

except ImportError:
    print(">>> APScheduler not installed - run: pip install APScheduler")


# ═══════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
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

    # ล้างไฟล์ค้าง processing จาก session ก่อน restart
    try:
        cleaned = rag_engine.cleanup_stale_processing(max_age_minutes=30)
        if cleaned:
            print(f">>> [Startup] Cleaned {cleaned} stale processing files", flush=True)
    except Exception as _ce:
        print(f"[!] Cleanup stale failed: {_ce}", flush=True)

    print(f">>> Starting Org Chatbot at http://127.0.0.1:{port}")

    # Print registered routes
    print(">>> Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"   {rule.endpoint:30} -> {rule.rule}")

    socketio.run(app, debug=False, port=port, host="0.0.0.0", use_reloader=False, allow_unsafe_werkzeug=True)
