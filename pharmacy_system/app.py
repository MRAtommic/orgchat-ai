"""
🏥 Pharmacy Stock Management & Dispensing System
Flask Application Entry Point
"""

import sys
import os
import json
import logging
import secrets
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect
from config import Config
import database
from google_sync import google_sync
from line_service import line_bot
from ocr_service import parse_drug_from_image

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static")
)
app.config.from_object(Config)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

logger = logging.getLogger("pharmacy_app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

@app.after_request
def disable_cache_for_dev(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ─────────────────────────────────────────────────────────────
# HTML Views
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", base_url=Config.BASE_URL)

@app.route("/scanner")
def mobile_scanner():
    return render_template("index.html", initial_view="scanner", base_url=Config.BASE_URL)

# ─────────────────────────────────────────────────────────────
# Drug Inventory API (CRUD & Search)
# ─────────────────────────────────────────────────────────────

@app.route("/api/drugs", methods=["GET"])
def list_drugs():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    low_stock = request.args.get("low_stock") == "1"
    drugs = database.get_all_drugs(search_query=search, category=category, low_stock_only=low_stock)
    return jsonify({"ok": True, "drugs": drugs, "count": len(drugs)})

@app.route("/api/drugs/<int:drug_id>", methods=["GET"])
def get_drug(drug_id):
    drug = database.get_drug_by_id(drug_id)
    if not drug:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลยา"}), 404
    return jsonify({"ok": True, "drug": drug})

@app.route("/api/drugs/scan-lookup", methods=["GET"])
def scan_lookup():
    code = request.args.get("code", "").strip()
    if not code:
        return jsonify({"ok": False, "error": "กรุณาระบุรหัสที่สแกน"}), 400

    clean_code = code
    if "http://" in clean_code or "https://" in clean_code:
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(clean_code)
            qs = parse_qs(parsed.query)
            extracted = qs.get("scan", [None])[0] or qs.get("code", [None])[0] or qs.get("dispense", [None])[0]
            if extracted:
                clean_code = extracted.strip()
            else:
                parts = [p for p in parsed.path.split('/') if p]
                if parts:
                    clean_code = parts[-1].strip()
        except Exception:
            pass

    clean_code = clean_code.replace("PHARM:", "").strip()
    drug = database.get_drug_by_code(clean_code) or database.find_drug_by_name_or_alias(clean_code)
    
    if drug:
        return jsonify({"ok": True, "found": True, "drug": drug})
    else:
        return jsonify({"ok": True, "found": False, "scanned_code": code, "clean_code": clean_code})

def trigger_bg_sheet_sync():
    """Run Google Sheet sync in daemon thread so API responses are lightning fast."""
    import threading
    def _run():
        try:
            google_sync.sync_all_drugs_to_sheet(database.get_all_drugs())
        except Exception as e:
            logger.warning(f"Background sheet sync error: {e}")
    threading.Thread(target=_run, daemon=True).start()

@app.route("/api/drugs", methods=["POST"])
def create_drug():
    data = request.json or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อยา"}), 400

    new_drug = database.add_drug(data)
    trigger_bg_sheet_sync()
    return jsonify({"ok": True, "drug": new_drug, "message": "เพิ่มข้อมูลยาในคลังเรียบร้อยแล้ว"})

@app.route("/api/drugs/<int:drug_id>", methods=["PUT"])
def edit_drug(drug_id):
    data = request.json or {}
    updated = database.update_drug(drug_id, data)
    if not updated:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลยาที่ต้องการแก้ไข"}), 404

    trigger_bg_sheet_sync()
    return jsonify({"ok": True, "drug": updated, "message": "แก้ไขข้อมูลยาเรียบร้อยแล้ว"})

@app.route("/api/drugs/<int:drug_id>", methods=["DELETE"])
def remove_drug(drug_id):
    database.delete_drug(drug_id)
    trigger_bg_sheet_sync()
    return jsonify({"ok": True, "message": "ลบยาออกจากคลังเรียบร้อยแล้ว"})

# ─────────────────────────────────────────────────────────────
# Stock Dispensing & Deduction API
# ─────────────────────────────────────────────────────────────

@app.route("/api/dispense", methods=["POST"])
def dispense_stock():
    """
    Deduct stock via Web UI (Manual or QR Scan).
    Payload: {drug_id: int, quantity: int, channel: str, dispensed_by: str, patient_name: str, notes: str}
    """
    data = request.json or {}
    drug_id = data.get("drug_id")
    quantity = int(data.get("quantity") or 1)
    channel = data.get("channel") or "WEB_MANUAL"
    dispensed_by = data.get("dispensed_by") or "เภสัชกร/เจ้าหน้าที่"
    patient_name = data.get("patient_name") or ""
    notes = data.get("notes") or ""

    if not drug_id:
        return jsonify({"ok": False, "error": "กรุณาระบุรหัสยาที่ต้องการตัดสต็อก"}), 400

    success, result = database.deduct_stock(
        drug_id,
        quantity,
        channel=channel,
        dispensed_by=dispensed_by,
        patient_name=patient_name,
        notes=notes
    )

    if not success:
        return jsonify({"ok": False, "error": result}), 400

    # Sync to Google Sheets
    try:
        google_sync.append_dispensing_log(result)
        google_sync.sync_all_drugs_to_sheet(database.get_all_drugs())
    except Exception as e:
        logger.error(f"Error syncing to sheet after dispense: {e}")

    return jsonify({
        "ok": True,
        "result": result,
        "message": f"ตัดสต็อก '{result['drug_name']}' สำเร็จ - คงเหลือ {result['balance_after']} {result['unit']}"
    })

@app.route("/api/dispense/logs", methods=["GET"])
def list_logs():
    limit = int(request.args.get("limit", 100))
    date_filter = request.args.get("date")
    channel = request.args.get("channel")
    logs = database.get_dispensing_logs(limit=limit, date_filter=date_filter, channel_filter=channel)
    return jsonify({"ok": True, "logs": logs, "count": len(logs)})

@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    stats = database.get_dashboard_stats()
    stats["google_sheet_connected"] = google_sync.is_connected
    stats["google_spreadsheet_id"] = google_sync.spreadsheet_id or "Not Configured"
    return jsonify({"ok": True, "stats": stats})

# ─────────────────────────────────────────────────────────────
# Google Drive & Sheets Connection Settings API
# ─────────────────────────────────────────────────────────────

@app.route("/api/google/config", methods=["GET"])
def get_google_config():
    info = google_sync.get_connection_info()
    return jsonify({"ok": True, "config": info})

@app.route("/api/google/config", methods=["POST"])
def update_google_config():
    data = request.json or {}
    sheet_input = data.get("spreadsheet_id")
    drive_input = data.get("drive_folder_id")
    sa_input = data.get("service_account_json")

    info = google_sync.update_and_reconnect(sheet_input, drive_input, sa_input)
    if info.get("is_connected") and info.get("spreadsheet_id"):
        try:
            google_sync.ensure_pharmacy_spreadsheet()
            google_sync.sync_all_drugs_to_sheet(database.get_all_drugs())
        except Exception as e:
            logger.warning(f"Sync after config update error: {e}")

    return jsonify({"ok": True, "config": info, "message": "อัปเดตการเชื่อมต่อ Google Drive & Sheets เรียบร้อยแล้ว"})

@app.route("/api/google/auto-create-sheet", methods=["POST"])
def auto_create_google_sheet():
    sheet_id, err = google_sync.ensure_pharmacy_spreadsheet()
    if err:
        return jsonify({"ok": False, "error": err}), 400

    try:
        google_sync.sync_all_drugs_to_sheet(database.get_all_drugs())
    except Exception:
        pass

    return jsonify({"ok": True, "config": google_sync.get_connection_info(), "message": "สร้าง Google Sheet สำหรับคลังยาสำเร็จแล้ว"})

# ─────────────────────────────────────────────────────────────
# Google OAuth2 Automatic Authorization (Drive & Sheets Auto-Create)
# ─────────────────────────────────────────────────────────────

def _determine_redirect_uri():
    cf_ray = request.headers.get("cf-ray")
    cf_host = request.headers.get("x-forwarded-host") or request.host or ""
    
    # If accessing via public domain or Cloudflare tunnel
    if cf_ray or "openchat.sbs" in cf_host:
        return "https://openchat.sbs/api/auth/google/callback"
    
    # If direct local access
    if "localhost" in cf_host or "127.0.0.1" in cf_host:
        return "http://localhost:5005/api/auth/google/callback"

    return Config.OAUTH2_REDIRECT_URI or "https://openchat.sbs/api/auth/google/callback"

@app.route("/api/auth/google/login")
def google_oauth_login():
    """Start Google OAuth flow to grant Drive & Sheets access automatically."""
    client_id = Config.GOOGLE_OAUTH2_CLIENT_ID
    if not client_id:
        return "Google OAuth2 Client ID not configured", 500

    redirect_uri = _determine_redirect_uri()
    state_token = secrets.token_urlsafe(32)
    database.set_setting(f"oauth_state_{state_token}", redirect_uri)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/spreadsheets",
        "access_type": "offline",
        "prompt": "consent",
        "state": state_token
    }
    auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
    return redirect(auth_url)

@app.route("/api/auth/google/callback")
def google_oauth_callback():
    """Exchange authorization code for tokens and auto-create Google Drive & Sheet."""
    error = request.args.get("error")
    if error:
        return redirect("/?google_error=" + urllib.parse.quote(error))

    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return redirect("/?google_error=no_code")

    saved_redirect_uri = database.get_setting(f"oauth_state_{state}") or _determine_redirect_uri()

    try:
        # Exchange code for token with Google
        token_payload = urllib.parse.urlencode({
            "code": code,
            "client_id": Config.GOOGLE_OAUTH2_CLIENT_ID,
            "client_secret": Config.GOOGLE_OAUTH2_CLIENT_SECRET,
            "redirect_uri": saved_redirect_uri,
            "grant_type": "authorization_code"
        }).encode("utf-8")

        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_payload, method="POST")
        with urllib.request.urlopen(req) as resp:
            token_res = json.loads(resp.read().decode("utf-8"))

        access_token = token_res.get("access_token")
        refresh_token = token_res.get("refresh_token")

        # Get user email
        userinfo_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(userinfo_req) as resp:
            user_info = json.loads(resp.read().decode("utf-8"))
        google_email = user_info.get("email", "unknown@gmail.com")

        # Setup workspace automatically
        ok, res = google_sync.setup_oauth_workspace(google_email, access_token, refresh_token)
        if ok:
            return redirect(f"/?google_connected=1&email={urllib.parse.quote(google_email)}")
        else:
            return redirect(f"/?google_error={urllib.parse.quote(str(res))}")

    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return redirect(f"/?google_error={urllib.parse.quote(str(e))}")

@app.route("/api/google/disconnect", methods=["POST"])
def google_disconnect():
    google_sync.disconnect_google()
    return jsonify({"ok": True, "message": "ตัดการเชื่อมต่อ Google เรียบร้อยแล้ว"})


# ─────────────────────────────────────────────────────────────
# Image Upload & OCR Analysis (Prescription / QR scan)
# ─────────────────────────────────────────────────────────────

@app.route("/api/scan-image", methods=["POST"])
def scan_image():
    """
    Accepts uploaded photo of prescription, label, or QR code.
    Runs OCR and returns detected drug and quantity.
    """
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "ไม่พบไฟล์ภาพที่อัปโหลด"}), 400

    f = request.files["file"]
    image_bytes = f.read()
    if not image_bytes:
        return jsonify({"ok": False, "error": "ไฟล์ภาพว่างเปล่า"}), 400

    analysis = parse_drug_from_image(image_bytes)
    return jsonify({"ok": True, "analysis": analysis})

@app.route("/api/sync-sheet", methods=["POST"])
def trigger_sheet_sync():
    """Manually force re-sync with Google Sheets."""
    drugs = database.get_all_drugs()
    success, msg = google_sync.sync_all_drugs_to_sheet(drugs)
    return jsonify({"ok": success, "message": msg})

# ─────────────────────────────────────────────────────────────
# LINE Webhook Endpoint
# ─────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST", "GET"])
@app.route("/api/line-webhook", methods=["POST", "GET"])
def line_webhook():
    if request.method == "GET":
        return "Pharmacy LINE Bot Webhook Active", 200

    body = request.get_data(as_text=True)
    try:
        events = json.loads(body).get("events", [])
        for ev in events:
            line_bot.handle_webhook_event(ev)
        return "OK", 200
    except Exception as e:
        logger.error(f"Error handling LINE webhook: {e}")
        return "Internal Error", 500

# ─────────────────────────────────────────────────────────────
# System Status & Health
# ─────────────────────────────────────────────────────────────

@app.route("/api/status", methods=["GET"])
def system_status():
    return jsonify({
        "status": "healthy",
        "app": "Pharmacy Stock Management System",
        "version": "1.0.0",
        "port": Config.PORT,
        "database": Config.DB_PATH,
        "google_sheets_connected": google_sync.is_connected,
        "google_spreadsheet_id": google_sync.spreadsheet_id,
        "line_bot_configured": bool(Config.LINE_CHANNEL_ACCESS_TOKEN)
    })

if __name__ == "__main__":
    port = Config.PORT
    print(f"\n=======================================================")
    print(f"🏥 PHARMACY STOCK MANAGEMENT SYSTEM RUNNING ON PORT {port}")
    print(f"👉 Local Access:   http://localhost:{port}")
    print(f"👉 Public Domain:  {Config.BASE_URL}")
    print(f"👉 LINE Webhook:   {Config.BASE_URL}/webhook")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
