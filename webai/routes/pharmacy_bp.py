# -*- coding: utf-8 -*-
"""
Pharmacy Management Blueprint for OrgChat AI
Provides access to Pharmacy System at /pharmacy while running webai!
Includes full feature parity with standalone PharmaCore (Inventory, Stock-In,
Dispensing, Expiry Alerts, Excel Exports, PWA, Image OCR, and Analytics).
"""

import os
import sys
import uuid
from io import BytesIO
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, send_from_directory, make_response, redirect

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
    static_folder=str(PHARMACY_ROOT / "static"),
    static_url_path="/static"
)

# ─────────────────────────────────────────────────────────────
# HTML Views & PWA
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/")
def pharmacy_home():
    return render_template("index.html", base_prefix="/pharmacy", base_url="/pharmacy")

@pharmacy_bp.route("/scanner")
def pharmacy_scanner():
    return render_template("index.html", initial_view="scanner", base_prefix="/pharmacy", base_url="/pharmacy")

@pharmacy_bp.route("/manifest.json")
def manifest():
    return send_from_directory(str(PHARMACY_ROOT / "static"), "manifest.json", mimetype="application/manifest+json")

@pharmacy_bp.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory(str(PHARMACY_ROOT / "static"), "sw.js", mimetype="application/javascript"))
    response.headers["Service-Worker-Allowed"] = "/pharmacy"
    return response

# ─────────────────────────────────────────────────────────────
# Drug Inventory API (CRUD & Search)
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/drugs", methods=["GET"])
def list_drugs():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    low_stock = request.args.get("low_stock") == "1"
    
    expiring_param = request.args.get("expiring_days")
    if expiring_param:
        try:
            expiring_days = int(expiring_param)
        except ValueError:
            expiring_days = 60
    elif request.args.get("expiring") == "1":
        expiring_days = 60
    else:
        expiring_days = None

    drugs = pharm_db.get_all_drugs(search_query=search, category=category, low_stock_only=low_stock, expiring_soon_days=expiring_days)
    return jsonify({"ok": True, "drugs": drugs, "count": len(drugs)})

@pharmacy_bp.route("/api/drugs/expiring", methods=["GET"])
def list_expiring_drugs():
    days = int(request.args.get("days", 60))
    drugs = pharm_db.get_expiring_drugs(days=days)
    return jsonify({"ok": True, "days": days, "drugs": drugs, "count": len(drugs)})

@pharmacy_bp.route("/api/drugs/<int:drug_id>", methods=["GET"])
def get_drug(drug_id):
    drug = pharm_db.get_drug_by_id(drug_id)
    if not drug:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลยา"}), 404
    return jsonify({"ok": True, "drug": drug})

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

# ─────────────────────────────────────────────────────────────
# Dispensing API
# ─────────────────────────────────────────────────────────────

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
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    channel = request.args.get("channel")
    logs = pharm_db.get_dispensing_logs(
        limit=limit,
        date_filter=date_filter,
        channel_filter=channel,
        start_date=start_date,
        end_date=end_date
    )
    return jsonify({"ok": True, "logs": logs, "count": len(logs)})

# ─────────────────────────────────────────────────────────────
# Stock In & Receiving API (Batch & Lot Management)
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/stock-in", methods=["POST"])
def stock_in_endpoint():
    data = request.json or {}
    target = data.get("drug_id") or data.get("drug_code")
    if not target:
        return jsonify({"ok": False, "error": "กรุณาระบุรหัสยาหรือเลือกรายการยา"}), 400

    try:
        quantity = int(data.get("quantity") or 0)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "จำนวนรับเข้าต้องเป็นตัวเลข"}), 400

    if quantity <= 0:
        return jsonify({"ok": False, "error": "จำนวนรับเข้าต้องมากกว่า 0"}), 400

    lot_number = (data.get("lot_number") or "").strip()
    cost_per_unit = data.get("cost_per_unit")
    expiry_date = (data.get("expiry_date") or "").strip()
    supplier = (data.get("supplier") or "องค์การเภสัชกรรม (GPO)").strip()
    received_by = (data.get("received_by") or "เภสัชกร/เจ้าหน้าที่").strip()
    notes = (data.get("notes") or "").strip()

    success, result = pharm_db.stock_in(
        drug_id_or_code=target,
        quantity=quantity,
        lot_number=lot_number,
        cost_per_unit=cost_per_unit,
        expiry_date=expiry_date,
        supplier=supplier,
        received_by=received_by,
        notes=notes
    )

    if not success:
        return jsonify({"ok": False, "error": result}), 400

    try:
        google_sync.sync_all_drugs_to_sheet(pharm_db.get_all_drugs())
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "result": result,
        "message": f"รับเข้า '{result['drug_name']}' จำนวน {result['quantity']} {result['unit']} สำเร็จ (คงเหลือใหม่ {result['balance_after']} {result['unit']})"
    })

@pharmacy_bp.route("/api/stock-in/logs", methods=["GET"])
def list_stock_in_logs():
    limit = int(request.args.get("limit", 100))
    date_filter = request.args.get("date")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    drug_id = request.args.get("drug_id")
    logs = pharm_db.get_stock_in_logs(
        limit=limit,
        drug_id=drug_id,
        date_filter=date_filter,
        start_date=start_date,
        end_date=end_date
    )
    return jsonify({"ok": True, "logs": logs, "count": len(logs)})

# ─────────────────────────────────────────────────────────────
# Analytics & Dashboard Stats
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/analytics/summary", methods=["GET"])
def analytics_summary():
    summary = pharm_db.get_analytics_summary()
    return jsonify({"ok": True, "analytics": summary})

@pharmacy_bp.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    stats = pharm_db.get_dashboard_stats()
    stats["google_sheet_connected"] = google_sync.is_connected
    stats["google_spreadsheet_id"] = google_sync.spreadsheet_id or "Not Configured"
    return jsonify({"ok": True, "stats": stats})

# ─────────────────────────────────────────────────────────────
# Image Upload & Scan OCR
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/scan-image", methods=["POST"])
def scan_image():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "ไม่พบไฟล์ภาพที่อัปโหลด"}), 400
    image_bytes = request.files["file"].read()
    if not image_bytes:
        return jsonify({"ok": False, "error": "ไฟล์ภาพว่างเปล่า"}), 400
    analysis = parse_drug_from_image(image_bytes)
    return jsonify({"ok": True, "analysis": analysis})

@pharmacy_bp.route("/api/upload/drug-image", methods=["POST"])
def upload_drug_image():
    file = request.files.get("image") or request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"ok": False, "error": "ไม่พบไฟล์ภาพที่อัปโหลด"}), 400
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in {"png", "jpg", "jpeg", "webp", "gif"}:
        return jsonify({"ok": False, "error": "รองรับเฉพาะไฟล์รูปภาพ (PNG, JPG, JPEG, WEBP, GIF)"}), 400
    
    upload_dir = PHARMACY_ROOT / "static" / "uploads" / "drugs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"drug_{uuid.uuid4().hex[:12]}.{ext}"
    file.save(str(upload_dir / unique_name))
    return jsonify({"ok": True, "image_url": f"/pharmacy/static/uploads/drugs/{unique_name}"})

# ─────────────────────────────────────────────────────────────
# Google Workspace Sync API
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/sync-sheet", methods=["POST"])
def trigger_sheet_sync():
    drugs = pharm_db.get_all_drugs()
    success1, msg1 = google_sync.sync_all_drugs_to_sheet(drugs)
    success2, msg2 = google_sync.sync_all_dispensing_logs()
    return jsonify({
        "ok": success1 and success2,
        "message": "ซิงค์ข้อมูลทั้งคลังยาและประวัติการตัดสต็อกขึ้น Google Sheets เรียบร้อยแล้ว"
    })

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

@pharmacy_bp.route("/api/google/disconnect", methods=["POST"])
def disconnect_google_endpoint():
    google_sync.disconnect_google()
    return jsonify({"ok": True, "message": "ตัดการเชื่อมต่อ Google สำเร็จแล้ว"})

# ─────────────────────────────────────────────────────────────
# LINE Notification & Expiry Alert API
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/line/config", methods=["GET", "POST"])
def pharmacy_line_config():
    if request.method == "POST":
        data = request.json or {}
        target_id = data.get("target_id")
        days = data.get("expiry_alert_days")
        if target_id is not None:
            pharm_db.set_app_setting("line_notify_target", str(target_id).strip())
        if days is not None:
            try:
                pharm_db.set_app_setting("expiry_alert_days", int(days))
            except ValueError:
                pass
        return jsonify({"ok": True, "message": "อัปเดตการตั้งค่า LINE เรียบร้อยแล้ว"})

    subscribers = pharm_db.get_line_subscribers()
    days = int(pharm_db.get_app_setting("expiry_alert_days") or 60)
    expiring = pharm_db.get_expiring_drugs(days=days)
    return jsonify({
        "ok": True,
        "is_configured": True,
        "expiry_alert_days": days,
        "expiring_count": len(expiring),
        "subscribers_count": len(subscribers),
        "subscribers": subscribers[:10]
    })

@pharmacy_bp.route("/api/line/send-expiry-alert", methods=["POST"])
def send_expiry_alert():
    data = request.json or {}
    days = int(data.get("days") or pharm_db.get_app_setting("expiry_alert_days") or 60)
    result = line_bot.send_expiring_drugs_alert(days=days, target_id=data.get("target_id"), force=True)
    return jsonify(result)

# ─────────────────────────────────────────────────────────────
# Excel Export Endpoints
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/export/inventory", methods=["GET"])
def export_inventory_excel():
    """Export all drug inventory to a styled Excel (.xlsx) file."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return jsonify({"ok": False, "error": "openpyxl is not installed"}), 500

    drugs = pharm_db.get_all_drugs()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "รายการยาในคลัง"

    header_fill = PatternFill("solid", fgColor="1E3A5F")
    low_fill    = PatternFill("solid", fgColor="FFF1F2")
    alt_fill    = PatternFill("solid", fgColor="F8FAFC")
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    body_font   = Font(name="Calibri", size=10)
    bold_font   = Font(name="Calibri", bold=True, size=10)
    danger_font = Font(name="Calibri", bold=True, color="E11D48", size=10)
    center      = Alignment(horizontal="center", vertical="center", wrap_text=False)
    left        = Alignment(horizontal="left", vertical="center", wrap_text=False)
    thin_side   = Side(style="thin", color="CBD5E1")
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    ws.merge_cells("A1:K1")
    title_cell = ws["A1"]
    title_cell.value = f"รายงานคลังยา — PharmaCore (ส่งออก {datetime.now().strftime('%d/%m/%Y %H:%M')})"
    title_cell.font  = Font(name="Calibri", bold=True, color="1E3A5F", size=14)
    title_cell.alignment = left
    ws.row_dimensions[1].height = 26

    headers = ["ลำดับ", "รหัสยา", "ชื่อยา", "ชื่อสามัญ", "หมวดหมู่",
               "รูปแบบยา", "สต็อกคงเหลือ", "หน่วย", "จุดเตือนขั้นต่ำ",
               "ราคา (บาท)", "ตำแหน่งจัดเก็บ"]
    col_widths = [6, 13, 30, 25, 22, 20, 15, 10, 17, 13, 20]

    ws.append(headers)
    for c_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=2, column=c_idx)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(c_idx)].width = width
    ws.row_dimensions[2].height = 22

    for row_num, d in enumerate(drugs, start=1):
        is_low = (d.get("stock_qty", 0) or 0) <= (d.get("min_threshold", 10) or 10)
        row_data = [
            row_num,
            d.get("code", ""),
            d.get("name", ""),
            d.get("generic_name") or "",
            d.get("category", ""),
            d.get("dosage_form") or "",
            d.get("stock_qty", 0),
            d.get("unit", ""),
            d.get("min_threshold", 10),
            d.get("price") or 0,
            d.get("location") or "",
        ]
        ws.append(row_data)
        xlsx_row = row_num + 2
        row_fill = low_fill if is_low else (alt_fill if row_num % 2 == 0 else None)
        for c_idx in range(1, 12):
            cell = ws.cell(row=xlsx_row, column=c_idx)
            cell.border    = thin_border
            cell.alignment = center if c_idx in (1, 7, 8, 9, 10) else left
            cell.font      = (danger_font if c_idx == 7 and is_low else body_font)
            if c_idx in (1, 2):
                cell.font = bold_font
            if row_fill:
                cell.fill = row_fill
        ws.row_dimensions[xlsx_row].height = 18

    buf = BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()
    filename = f"pharmacore_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    resp = make_response(xlsx_bytes)
    resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

@pharmacy_bp.route("/api/export/logs", methods=["GET"])
def export_dispense_logs_excel():
    """Export dispensing history to Excel (.xlsx) file."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return jsonify({"ok": False, "error": "openpyxl is not installed"}), 500

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    logs = pharm_db.get_dispensing_logs(limit=5000, start_date=start_date, end_date=end_date)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ประวัติการจ่ายยา"

    header_fill = PatternFill("solid", fgColor="065F46")
    alt_fill    = PatternFill("solid", fgColor="F0FDF4")
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    body_font   = Font(name="Calibri", size=10)
    bold_font   = Font(name="Calibri", bold=True, size=10)
    center      = Alignment(horizontal="center", vertical="center")
    left        = Alignment(horizontal="left", vertical="center")
    thin_side   = Side(style="thin", color="CBD5E1")
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    ws.merge_cells("A1:I1")
    title_cell = ws["A1"]
    title_cell.value = f"ประวัติการตัดสต็อก / จ่ายยา — PharmaCore (ส่งออก {datetime.now().strftime('%d/%m/%Y %H:%M')})"
    title_cell.font  = Font(name="Calibri", bold=True, color="065F46", size=14)
    title_cell.alignment = left
    ws.row_dimensions[1].height = 26

    headers = ["ลำดับ", "วัน-เวลา", "รหัสยา", "ชื่อยา", "จำนวนที่จ่าย",
               "คงเหลือก่อน", "คงเหลือหลัง", "ช่องทาง", "ผู้ดำเนินการ"]
    col_widths = [6, 18, 13, 28, 14, 13, 13, 14, 18]

    ws.append(headers)
    for c_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=2, column=c_idx)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(c_idx)].width = width
    ws.row_dimensions[2].height = 22

    for row_num, log in enumerate(logs, start=1):
        row_data = [
            row_num,
            log.get("created_at", ""),
            log.get("drug_code", ""),
            log.get("drug_name", ""),
            log.get("quantity", 0),
            log.get("balance_before", 0),
            log.get("balance_after", 0),
            log.get("channel", ""),
            log.get("dispensed_by", ""),
        ]
        ws.append(row_data)
        xlsx_row = row_num + 2
        row_fill = alt_fill if row_num % 2 == 0 else None
        for c_idx in range(1, 10):
            cell = ws.cell(row=xlsx_row, column=c_idx)
            cell.border    = thin_border
            cell.alignment = center if c_idx in (1, 2, 3, 5, 6, 7, 8) else left
            cell.font      = bold_font if c_idx == 5 else body_font
            if row_fill:
                cell.fill = row_fill
        ws.row_dimensions[xlsx_row].height = 18

    buf = BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()
    filename = f"pharmacore_dispense_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    resp = make_response(xlsx_bytes)
    resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

@pharmacy_bp.route("/api/export/stock-in", methods=["GET"])
def export_stock_in_excel():
    """Export receiving/stock-in history to Excel (.xlsx) file."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return jsonify({"ok": False, "error": "openpyxl is not installed"}), 500

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    logs = pharm_db.get_stock_in_logs(limit=5000, start_date=start_date, end_date=end_date)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ประวัติการรับเข้ายา"

    header_fill = PatternFill("solid", fgColor="1E40AF")
    alt_fill    = PatternFill("solid", fgColor="EFF6FF")
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    body_font   = Font(name="Calibri", size=10)
    bold_font   = Font(name="Calibri", bold=True, size=10)
    center      = Alignment(horizontal="center", vertical="center")
    left        = Alignment(horizontal="left", vertical="center")
    thin_side   = Side(style="thin", color="CBD5E1")
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    ws.merge_cells("A1:K1")
    title_cell = ws["A1"]
    title_cell.value = f"ประวัติการรับเข้าคลังยา (Stock-In) — PharmaCore (ส่งออก {datetime.now().strftime('%d/%m/%Y %H:%M')})"
    title_cell.font  = Font(name="Calibri", bold=True, color="1E40AF", size=14)
    title_cell.alignment = left
    ws.row_dimensions[1].height = 26

    headers = ["ลำดับ", "วัน-เวลา", "รหัสยา", "ชื่อยา", "Lot No.", "จำนวนรับเข้า",
               "คงเหลือก่อน", "คงเหลือหลัง", "ราคาทุน/หน่วย", "ยอดรวมทุน", "ผู้จัดส่ง/บริษัท"]
    col_widths = [6, 18, 13, 28, 14, 14, 13, 13, 14, 14, 22]

    ws.append(headers)
    for c_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=2, column=c_idx)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(c_idx)].width = width
    ws.row_dimensions[2].height = 22

    for row_num, log in enumerate(logs, start=1):
        row_data = [
            row_num,
            log.get("created_at", ""),
            log.get("drug_code", ""),
            log.get("drug_name", ""),
            log.get("lot_number", ""),
            log.get("quantity", 0),
            log.get("balance_before", 0),
            log.get("balance_after", 0),
            log.get("cost_per_unit", 0.0),
            log.get("total_cost", 0.0),
            log.get("supplier", ""),
        ]
        ws.append(row_data)
        xlsx_row = row_num + 2
        row_fill = alt_fill if row_num % 2 == 0 else None
        for c_idx in range(1, 12):
            cell = ws.cell(row=xlsx_row, column=c_idx)
            cell.border    = thin_border
            cell.alignment = center if c_idx in (1, 2, 3, 5, 6, 7, 8) else left
            cell.font      = bold_font if c_idx == 6 else body_font
            if row_fill:
                cell.fill = row_fill
        ws.row_dimensions[xlsx_row].height = 18

    buf = BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()
    filename = f"pharmacore_stock_in_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    resp = make_response(xlsx_bytes)
    resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

# ─────────────────────────────────────────────────────────────
# System Status & Health Check
# ─────────────────────────────────────────────────────────────

@pharmacy_bp.route("/api/status", methods=["GET"])
def system_status():
    return jsonify({
        "status": "healthy",
        "app": "Pharmacy Stock Management System (OrgChat AI Blueprint)",
        "version": "1.2.0",
        "database": pharm_db.Config.DB_PATH,
        "google_sheets_connected": google_sync.is_connected,
        "google_spreadsheet_id": google_sync.spreadsheet_id,
        "line_bot_configured": bool(pharm_db.Config.LINE_CHANNEL_ACCESS_TOKEN),
        "expiry_alert_configured": True
    })
