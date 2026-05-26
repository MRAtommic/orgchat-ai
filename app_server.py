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
print(">>> all imports done.", flush=True)

# ─── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot_debug.log", encoding="utf-8")
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

def async_startup_tasks():
    """Run heavy initialization tasks in background to avoid Cloudflare 524."""
    print(">>> Starting background initialization tasks...", flush=True)
    try:
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
    CORS(app, supports_credentials=True)

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
    except:
        pass

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
                    unames, "daily_summary", "Daily Briefing",
                    summary[:200], link="#feed"
                )
                batch_send_push_notification(unames, "Daily Briefing", summary[:120], url="/")
                print(f">>> Daily summary sent to {len(unames)} users")
        except Exception as e:
            print(f">>> Scheduled daily summary error: {e}")

    _scheduler.add_job(_scheduled_daily_summary, 'cron', hour=8, minute=0, id='daily_summary')
except ImportError:
    print(">>> APScheduler not installed - run: pip install APScheduler")


# ═══════════════════════════════════════════════════════════════
# Daily Reminder Thread (Plan Expiry + SQLite Backup)
# ═══════════════════════════════════════════════════════════════

def _run_daily_reminders():
    import time as _t
    _t.sleep(3600)
    while True:
        try:
            # Import from admin blueprint where check_expiring_plans lives
            from routes.admin import check_expiring_plans, _backup_sqlite
            check_expiring_plans()
            _backup_sqlite()
        except Exception as _e:
            logger.warning(f"[DailyReminder] error: {_e}")
        _t.sleep(86400)

threading.Thread(target=_run_daily_reminders, daemon=True).start()


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

    print(f">>> Starting Org Chatbot at http://127.0.0.1:{port}")

    # Print registered routes
    print(">>> Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"   {rule.endpoint:30} -> {rule.rule}")

    socketio.run(app, debug=False, port=port, host="0.0.0.0", use_reloader=False, allow_unsafe_werkzeug=True)
