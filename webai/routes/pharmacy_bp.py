# -*- coding: utf-8 -*-
"""
Pharmacy Management Blueprint for OrgChat AI
Provides access to Pharmacy System at /pharmacy while running webai!
"""

import sys
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, send_from_directory

PHARMACY_ROOT = Path(__file__).parent.parent.parent / "pharmacy_system"
sys.path.insert(0, str(PHARMACY_ROOT))

import database as pharm_db
from google_sync import google_sync
from line_service import line_bot
from ocr_service import parse_drug_from_image

pharmacy_bp = Blueprint(
    "pharmacy",
    __name__,
    url_prefix="/pharmacy",
    template_folder=str(PHARMACY_ROOT / "templates"),
    static_folder=str(PHARMACY_ROOT / "static")
)

@pharmacy_bp.route("/")
def pharmacy_home():
    return render_template("index.html", base_url="/pharmacy")

@pharmacy_bp.route("/api/drugs", methods=["GET"])
def list_drugs():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    low_stock = request.args.get("low_stock") == "1"
    drugs = pharm_db.get_all_drugs(search_query=search, category=category, low_stock_only=low_stock)
    return jsonify({"ok": True, "drugs": drugs, "count": len(drugs)})

@pharmacy_bp.route("/api/drugs/scan-lookup", methods=["GET"])
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
    drug = pharm_db.get_drug_by_code(clean_code) or pharm_db.find_drug_by_name_or_alias(clean_code)
    
    if drug:
        return jsonify({"ok": True, "found": True, "drug": drug})
    else:
        return jsonify({"ok": True, "found": False, "scanned_code": code, "clean_code": clean_code})

@pharmacy_bp.route("/api/drugs", methods=["POST"])
def create_drug():
    data = request.json or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อยา"}), 400
    new_drug = pharm_db.add_drug(data)
    try:
        google_sync.sync_all_drugs_to_sheet(pharm_db.get_all_drugs())
    except Exception:
        pass
    return jsonify({"ok": True, "drug": new_drug, "message": "เพิ่มข้อมูลยาในคลังเรียบร้อยแล้ว"})

@pharmacy_bp.route("/api/drugs/<int:drug_id>", methods=["PUT"])
def edit_drug(drug_id):
    data = request.json or {}
    updated = pharm_db.update_drug(drug_id, data)
    if not updated:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลยา"}), 404
    try:
        google_sync.sync_all_drugs_to_sheet(pharm_db.get_all_drugs())
    except Exception:
        pass
    return jsonify({"ok": True, "drug": updated, "message": "แก้ไขข้อมูลยาเรียบร้อยแล้ว"})

@pharmacy_bp.route("/api/drugs/<int:drug_id>", methods=["DELETE"])
def remove_drug(drug_id):
    pharm_db.delete_drug(drug_id)
    try:
        google_sync.sync_all_drugs_to_sheet(pharm_db.get_all_drugs())
    except Exception:
        pass
    return jsonify({"ok": True, "message": "ลบยาออกจากคลังเรียบร้อยแล้ว"})

@pharmacy_bp.route("/api/dispense", methods=["POST"])
def dispense_stock():
    data = request.json or {}
    drug_id = data.get("drug_id")
    quantity = int(data.get("quantity") or 1)
    channel = data.get("channel") or "WEB_MANUAL"
    dispensed_by = data.get("dispensed_by") or "เจ้าหน้าที่"
    patient_name = data.get("patient_name") or ""
    notes = data.get("notes") or ""

    success, result = pharm_db.deduct_stock(
        drug_id,
        quantity,
        channel=channel,
        dispensed_by=dispensed_by,
        patient_name=patient_name,
        notes=notes
    )
    if not success:
        return jsonify({"ok": False, "error": result}), 400

    try:
        google_sync.append_dispensing_log(result)
        google_sync.sync_all_drugs_to_sheet(pharm_db.get_all_drugs())
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "result": result,
        "message": f"ตัดสต็อก '{result['drug_name']}' สำเร็จ - คงเหลือ {result['balance_after']} {result['unit']}"
    })

@pharmacy_bp.route("/api/dispense/logs", methods=["GET"])
def list_logs():
    limit = int(request.args.get("limit", 100))
    date_filter = request.args.get("date")
    channel = request.args.get("channel")
    logs = pharm_db.get_dispensing_logs(limit=limit, date_filter=date_filter, channel_filter=channel)
    return jsonify({"ok": True, "logs": logs, "count": len(logs)})

@pharmacy_bp.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    stats = pharm_db.get_dashboard_stats()
    stats["google_sheet_connected"] = google_sync.is_connected
    stats["google_spreadsheet_id"] = google_sync.spreadsheet_id or "Not Configured"
    return jsonify({"ok": True, "stats": stats})

@pharmacy_bp.route("/api/scan-image", methods=["POST"])
def scan_image():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "ไม่พบไฟล์ภาพที่อัปโหลด"}), 400
    image_bytes = request.files["file"].read()
    analysis = parse_drug_from_image(image_bytes)
    return jsonify({"ok": True, "analysis": analysis})

@pharmacy_bp.route("/api/sync-sheet", methods=["POST"])
def trigger_sheet_sync():
    drugs = pharm_db.get_all_drugs()
    success, msg = google_sync.sync_all_drugs_to_sheet(drugs)
    return jsonify({"ok": success, "message": msg})

@pharmacy_bp.route("/api/google/config", methods=["GET"])
def get_google_config():
    info = google_sync.get_connection_info()
    return jsonify({"ok": True, "config": info})

@pharmacy_bp.route("/api/google/config", methods=["POST"])
def update_google_config():
    data = request.json or {}
    sheet_input = data.get("spreadsheet_id")
    drive_input = data.get("drive_folder_id")
    sa_input = data.get("service_account_json")

    info = google_sync.update_and_reconnect(sheet_input, drive_input, sa_input)
    if info.get("is_connected") and info.get("spreadsheet_id"):
        try:
            google_sync.ensure_pharmacy_spreadsheet()
            google_sync.sync_all_drugs_to_sheet(pharm_db.get_all_drugs())
        except Exception:
            pass

    return jsonify({"ok": True, "config": info, "message": "อัปเดตการเชื่อมต่อ Google Drive & Sheets เรียบร้อยแล้ว"})

@pharmacy_bp.route("/api/google/auto-create-sheet", methods=["POST"])
def auto_create_google_sheet():
    sheet_id, err = google_sync.ensure_pharmacy_spreadsheet()
    if err:
        return jsonify({"ok": False, "error": err}), 400

    try:
        google_sync.sync_all_drugs_to_sheet(pharm_db.get_all_drugs())
    except Exception:
        pass

    return jsonify({"ok": True, "config": google_sync.get_connection_info(), "message": "สร้าง Google Sheet สำหรับคลังยาสำเร็จแล้ว"})
