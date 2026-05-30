# -*- coding: utf-8 -*-
"""
Features Blueprint — Quotation/Invoice, CRM, WHT Certificate, Meeting Notes
"""
from flask import Blueprint, request, jsonify, session, send_file
import os, io, json, logging
from datetime import datetime, date

import database
import billing
from routes.shared import login_required, _limiter, get_current_org_id

logger = logging.getLogger("OrgChatAI.Features")
features_bp = Blueprint('features', __name__)


def _org() -> int | None:
    return get_current_org_id()


def _user() -> str:
    return session.get("user", "")


# ══════════════════════════════════════════════════════════════
# QUOTATION / INVOICE
# ══════════════════════════════════════════════════════════════

@features_bp.route("/api/quotations", methods=["GET"])
@login_required
def quotation_list():
    org_id = _org()
    if not org_id:
        return jsonify({"ok": False, "error": "ไม่พบองค์กร"}), 403
    status = request.args.get("status")
    type_  = request.args.get("type")
    rows = database.quotation_list(org_id, status=status, type_=type_)
    return jsonify({"ok": True, "quotations": rows})


@features_bp.route("/api/quotations", methods=["POST"])
@login_required
@_limiter.limit("30 per minute")
def quotation_create():
    org_id = _org()
    if not org_id:
        return jsonify({"ok": False, "error": "ไม่พบองค์กร"}), 403
    data = request.get_json(force=True) or {}
    data["created_by"] = _user()
    if not data.get("customer_name"):
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อลูกค้า"}), 400
    qid = database.quotation_create(org_id, data)
    q = database.quotation_get(qid, org_id)
    database.log_event(f"Quotation created: {q['quotation_no']}", user=_user(), org_id=org_id)
    return jsonify({"ok": True, "id": qid, "quotation": q})


@features_bp.route("/api/quotations/<int:qid>", methods=["GET"])
@login_required
def quotation_get(qid):
    org_id = _org()
    q = database.quotation_get(qid, org_id)
    if not q:
        return jsonify({"ok": False, "error": "ไม่พบ quotation"}), 404
    return jsonify({"ok": True, "quotation": q})


@features_bp.route("/api/quotations/<int:qid>", methods=["PUT"])
@login_required
def quotation_update(qid):
    org_id = _org()
    data = request.get_json(force=True) or {}
    ok = database.quotation_update(qid, org_id, data)
    if not ok:
        return jsonify({"ok": False, "error": "ไม่พบ quotation หรือไม่มีสิทธิ์"}), 404
    return jsonify({"ok": True})


@features_bp.route("/api/quotations/<int:qid>", methods=["DELETE"])
@login_required
def quotation_delete(qid):
    org_id = _org()
    ok = database.quotation_delete(qid, org_id)
    return jsonify({"ok": ok})


@features_bp.route("/api/quotations/<int:qid>/status", methods=["POST"])
@login_required
def quotation_status(qid):
    org_id = _org()
    data = request.get_json(force=True) or {}
    status = data.get("status", "")
    valid = ["draft", "sent", "approved", "rejected", "paid"]
    if status not in valid:
        return jsonify({"ok": False, "error": f"status ต้องเป็น {valid}"}), 400
    ok = database.quotation_set_status(qid, org_id, status)
    if ok:
        database.log_event(f"Quotation #{qid} status → {status}", user=_user(), org_id=org_id)
    return jsonify({"ok": ok})


@features_bp.route("/api/quotations/<int:qid>/pdf", methods=["GET"])
@login_required
def quotation_pdf(qid):
    """Generate PDF for quotation/invoice"""
    org_id = _org()
    q = database.quotation_get(qid, org_id)
    if not q:
        return jsonify({"ok": False, "error": "ไม่พบ quotation"}), 404

    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        type_label = "ใบแจ้งหนี้ (INVOICE)" if q.get("type") == "invoice" else "ใบเสนอราคา (QUOTATION)"
        org_profile = database.get_org_profile(org_id) or {}
        org_name = org_profile.get("business_name_th") or org_profile.get("business_name_en") or "บริษัท"

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, type_label, ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, org_name, ln=True, align="C")
        pdf.ln(4)

        # Quotation info
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(95, 6, f"เลขที่: {q['quotation_no']}", ln=False)
        pdf.cell(95, 6, f"วันที่: {q.get('created_at','')[:10]}", ln=True)
        if q.get("valid_until"):
            pdf.cell(95, 6, "", ln=False)
            pdf.cell(95, 6, f"ใช้ได้ถึง: {q['valid_until']}", ln=True)
        pdf.ln(4)

        # Customer
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "ข้อมูลลูกค้า:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f"ชื่อ: {q.get('customer_name','')} {q.get('customer_company','')}", ln=True)
        if q.get("customer_tax_id"):
            pdf.cell(0, 5, f"เลขประจำตัวผู้เสียภาษี: {q['customer_tax_id']}", ln=True)
        if q.get("customer_address"):
            pdf.multi_cell(0, 5, f"ที่อยู่: {q['customer_address']}")
        pdf.ln(4)

        # Items table
        pdf.set_font("Helvetica", "B", 9)
        col_w = [80, 20, 25, 30, 35]
        headers = ["รายการ", "จำนวน", "หน่วย", "ราคา/หน่วย", "รวม"]
        for i, h in enumerate(headers):
            pdf.cell(col_w[i], 7, h, border=1, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for item in q.get("items", []):
            name  = str(item.get("name", ""))[:40]
            qty   = item.get("qty", 1)
            unit  = str(item.get("unit", ""))
            price = float(item.get("price", 0))
            total = qty * price
            pdf.cell(col_w[0], 6, name, border=1)
            pdf.cell(col_w[1], 6, str(qty), border=1, align="C")
            pdf.cell(col_w[2], 6, unit, border=1, align="C")
            pdf.cell(col_w[3], 6, f"{price:,.2f}", border=1, align="R")
            pdf.cell(col_w[4], 6, f"{total:,.2f}", border=1, align="R")
            pdf.ln()

        pdf.ln(3)
        # Summary
        def sum_row(label, value, bold=False):
            pdf.set_font("Helvetica", "B" if bold else "", 9)
            pdf.cell(155, 6, label, align="R")
            pdf.cell(35, 6, f"{value:,.2f}", align="R", border=1)
            pdf.ln()

        sum_row("ยอดรวมก่อนภาษี:", q.get("subtotal", 0))
        if q.get("discount", 0):
            sum_row(f"ส่วนลด:", -q["discount"])
        if q.get("vat_rate", 0):
            sum_row(f"ภาษีมูลค่าเพิ่ม {q['vat_rate']}%:", q.get("vat_amount", 0))
        if q.get("wht_rate", 0):
            sum_row(f"หัก ณ ที่จ่าย {q['wht_rate']}%:", -q.get("wht_amount", 0))
        sum_row("ยอดชำระสุทธิ:", q.get("total", 0), bold=True)

        if q.get("notes"):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, "หมายเหตุ:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, q["notes"])

        buf = io.BytesIO(pdf.output())
        fname = f"{q['quotation_no']}.pdf"
        return send_file(buf, mimetype="application/pdf",
                         as_attachment=True, download_name=fname)
    except Exception as e:
        logger.error(f"[QuotationPDF] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "สร้าง PDF ไม่สำเร็จ"}), 500


# ══════════════════════════════════════════════════════════════
# CRM
# ══════════════════════════════════════════════════════════════

@features_bp.route("/api/crm/customers", methods=["GET"])
@login_required
def crm_customers_list():
    org_id = _org()
    q = request.args.get("q", "")
    rows = database.crm_customer_list(org_id, q=q)
    return jsonify({"ok": True, "customers": rows})


@features_bp.route("/api/crm/customers", methods=["POST"])
@login_required
@_limiter.limit("30 per minute")
def crm_customers_create():
    org_id = _org()
    data = request.get_json(force=True) or {}
    if not data.get("name"):
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อลูกค้า"}), 400
    data["created_by"] = _user()
    cid = database.crm_customer_create(org_id, data)
    return jsonify({"ok": True, "id": cid})


@features_bp.route("/api/crm/customers/<int:cid>", methods=["GET"])
@login_required
def crm_customers_get(cid):
    org_id = _org()
    c = database.crm_customer_get(cid, org_id)
    if not c:
        return jsonify({"ok": False, "error": "ไม่พบลูกค้า"}), 404
    deals = database.crm_deal_list(org_id, customer_id=cid)
    activities = database.crm_activities_get(org_id, customer_id=cid)
    return jsonify({"ok": True, "customer": c, "deals": deals, "activities": activities})


@features_bp.route("/api/crm/customers/<int:cid>", methods=["PUT"])
@login_required
def crm_customers_update(cid):
    org_id = _org()
    data = request.get_json(force=True) or {}
    ok = database.crm_customer_update(cid, org_id, data)
    return jsonify({"ok": ok})


@features_bp.route("/api/crm/customers/<int:cid>", methods=["DELETE"])
@login_required
def crm_customers_delete(cid):
    org_id = _org()
    ok = database.crm_customer_delete(cid, org_id)
    return jsonify({"ok": ok})


@features_bp.route("/api/crm/deals", methods=["GET"])
@login_required
def crm_deals_list():
    org_id = _org()
    stage = request.args.get("stage")
    cid   = request.args.get("customer_id", type=int)
    rows  = database.crm_deal_list(org_id, customer_id=cid, stage=stage)
    return jsonify({"ok": True, "deals": rows})


@features_bp.route("/api/crm/deals", methods=["POST"])
@login_required
@_limiter.limit("30 per minute")
def crm_deals_create():
    org_id = _org()
    data = request.get_json(force=True) or {}
    if not data.get("title"):
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อ deal"}), 400
    data["created_by"] = _user()
    did = database.crm_deal_create(org_id, data)
    return jsonify({"ok": True, "id": did})


@features_bp.route("/api/crm/deals/<int:did>", methods=["PUT"])
@login_required
def crm_deals_update(did):
    org_id = _org()
    data = request.get_json(force=True) or {}
    ok = database.crm_deal_update(did, org_id, data)
    return jsonify({"ok": ok})


@features_bp.route("/api/crm/deals/<int:did>", methods=["DELETE"])
@login_required
def crm_deals_delete(did):
    org_id = _org()
    ok = database.crm_deal_delete(did, org_id)
    return jsonify({"ok": ok})


@features_bp.route("/api/crm/activities", methods=["POST"])
@login_required
def crm_activity_add():
    org_id = _org()
    data = request.get_json(force=True) or {}
    if not data.get("content"):
        return jsonify({"ok": False, "error": "กรุณากรอกเนื้อหา"}), 400
    data["created_by"] = _user()
    aid = database.crm_activity_add(org_id, data)
    return jsonify({"ok": True, "id": aid})


# ══════════════════════════════════════════════════════════════
# WHT CERTIFICATE (ภงด)
# ══════════════════════════════════════════════════════════════

@features_bp.route("/api/wht/summary", methods=["GET"])
@login_required
def wht_summary():
    """สรุปรายการ WHT จาก expense claims ของเดือนนี้"""
    org_id = _org()
    year_month = request.args.get("ym", date.today().strftime("%Y-%m"))
    try:
        conn = database._get_conn()
        conn.row_factory = __import__('sqlite3').Row
        rows = conn.execute("""
            SELECT vendor_name, vendor_tax_id, wht_type, wht_rate, wht_amount, amount,
                   expense_date, description
            FROM expense_claims
            WHERE org_id=? AND wht_amount > 0
              AND strftime('%Y-%m', expense_date) = ?
            ORDER BY expense_date
        """, (org_id, year_month)).fetchall()
        conn.close()
        items = [dict(r) for r in rows]
        total_wht = sum(float(i.get("wht_amount") or 0) for i in items)
        total_base = sum(float(i.get("amount") or 0) for i in items)
        return jsonify({"ok": True, "items": items, "total_wht": total_wht,
                        "total_base": total_base, "year_month": year_month})
    except Exception as e:
        logger.error(f"[WHT summary] {e}", exc_info=True)
        return jsonify({"ok": True, "items": [], "total_wht": 0, "total_base": 0, "year_month": year_month})


@features_bp.route("/api/wht/pdf", methods=["POST"])
@login_required
def wht_pdf():
    """Generate ภงด.53 PDF จาก expense data"""
    org_id = _org()
    data = request.get_json(force=True) or {}
    year_month = data.get("year_month", date.today().strftime("%Y-%m"))
    org_profile = database.get_org_profile(org_id) or {}

    try:
        conn = database._get_conn()
        conn.row_factory = __import__('sqlite3').Row
        rows = conn.execute("""
            SELECT vendor_name, vendor_tax_id, wht_type, wht_rate, wht_amount, amount, expense_date, description
            FROM expense_claims
            WHERE org_id=? AND wht_amount > 0
              AND strftime('%Y-%m', expense_date) = ?
            ORDER BY expense_date
        """, (org_id, year_month)).fetchall()
        conn.close()
        items = [dict(r) for r in rows]

        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(True, 15)

        # Title
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "หนังสือรับรองการหักภาษี ณ ที่จ่าย", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "(ตามมาตรา 50 ทวิ แห่งประมวลรัษฎากร)", ln=True, align="C")
        pdf.ln(4)

        # Payer info
        biz_name = org_profile.get("business_name_th") or org_profile.get("business_name_en") or ""
        tax_id   = org_profile.get("tax_id") or ""
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 6, "ผู้มีหน้าที่หักภาษี:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, biz_name, ln=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 6, "เลขประจำตัว:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, tax_id, ln=True)
        pdf.cell(40, 6, "เดือน/ปี:", ln=False)
        pdf.cell(0, 6, year_month, ln=True)
        pdf.ln(4)

        # Table header
        pdf.set_font("Helvetica", "B", 8)
        cols = [45, 30, 30, 25, 25, 35]
        hdrs = ["ชื่อผู้ถูกหัก", "เลขประจำตัว", "ประเภทรายได้", "จำนวนเงิน", "อัตรา%", "ภาษีที่หัก"]
        for i, h in enumerate(hdrs):
            pdf.cell(cols[i], 7, h, border=1, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        total_wht = 0
        total_base = 0
        for item in items:
            wht_type_map = {"0.75": "ค่าจ้างแรงงาน", "1": "ค่าขนส่ง", "2": "ค่าโฆษณา",
                            "3": "ค่าบริการ", "5": "ค่าเช่า", "10": "วิชาชีพอิสระ", "15": "เงินปันผล"}
            wht_rate = float(item.get("wht_rate") or 0)
            wht_type = item.get("wht_type") or wht_type_map.get(str(int(wht_rate)), "ค่าบริการ")
            base = float(item.get("amount") or 0)
            wht  = float(item.get("wht_amount") or 0)
            total_base += base
            total_wht  += wht
            pdf.cell(cols[0], 6, str(item.get("vendor_name",""))[:20], border=1)
            pdf.cell(cols[1], 6, str(item.get("vendor_tax_id",""))[:15], border=1, align="C")
            pdf.cell(cols[2], 6, wht_type[:14], border=1)
            pdf.cell(cols[3], 6, f"{base:,.2f}", border=1, align="R")
            pdf.cell(cols[4], 6, f"{wht_rate:.0f}%", border=1, align="C")
            pdf.cell(cols[5], 6, f"{wht:,.2f}", border=1, align="R")
            pdf.ln()

        # Total row
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(sum(cols[:3]), 7, "รวม", border=1, align="R")
        pdf.cell(cols[3], 7, f"{total_base:,.2f}", border=1, align="R")
        pdf.cell(cols[4], 7, "", border=1)
        pdf.cell(cols[5], 7, f"{total_wht:,.2f}", border=1, align="R")
        pdf.ln(10)

        # Signature
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(95, 5, f"ลงชื่อ .................................", ln=False)
        pdf.cell(95, 5, f"วันที่ {date.today().strftime('%d/%m/%Y')}", ln=True)
        pdf.cell(95, 5, f"({biz_name or 'ผู้มีหน้าที่หักภาษี'})", ln=True, align="C")

        buf = io.BytesIO(pdf.output())
        fname = f"WHT_{year_month}.pdf"
        return send_file(buf, mimetype="application/pdf",
                         as_attachment=True, download_name=fname)
    except Exception as e:
        logger.error(f"[WHT PDF] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "สร้าง PDF ไม่สำเร็จ"}), 500


# ══════════════════════════════════════════════════════════════
# MEETING NOTES
# ══════════════════════════════════════════════════════════════

@features_bp.route("/api/meetings", methods=["GET"])
@login_required
def meeting_list():
    org_id = _org()
    rows = database.meeting_note_list(org_id)
    return jsonify({"ok": True, "meetings": rows})


@features_bp.route("/api/meetings/<int:mid>", methods=["GET"])
@login_required
def meeting_get(mid):
    org_id = _org()
    m = database.meeting_note_get(mid, org_id)
    if not m:
        return jsonify({"ok": False, "error": "ไม่พบรายการประชุม"}), 404
    return jsonify({"ok": True, "meeting": m})


@features_bp.route("/api/meetings/<int:mid>", methods=["PUT"])
@login_required
def meeting_update(mid):
    org_id = _org()
    data = request.get_json(force=True) or {}
    ok = database.meeting_note_update(mid, org_id, data)
    return jsonify({"ok": ok})


@features_bp.route("/api/meetings/<int:mid>", methods=["DELETE"])
@login_required
def meeting_delete(mid):
    org_id = _org()
    ok = database.meeting_note_delete(mid, org_id)
    return jsonify({"ok": ok})


@features_bp.route("/api/meetings/upload", methods=["POST"])
@login_required
@_limiter.limit("5 per minute")
def meeting_upload():
    """
    อัปโหลดไฟล์เสียงการประชุม → AI transcribe → สรุป + action items → บันทึก
    """
    org_id = _org()
    if not org_id:
        return jsonify({"ok": False, "error": "ไม่พบองค์กร"}), 403

    title        = request.form.get("title", "ประชุม " + date.today().strftime("%d/%m/%Y"))
    participants = request.form.get("participants", "")
    meeting_date = request.form.get("meeting_date", date.today().isoformat())

    audio_file = request.files.get("audio")
    if not audio_file:
        return jsonify({"ok": False, "error": "กรุณาแนบไฟล์เสียง"}), 400

    allowed_audio = {".mp3", ".mp4", ".wav", ".ogg", ".m4a", ".webm", ".aac"}
    ext = os.path.splitext(audio_file.filename or "")[1].lower()
    if ext not in allowed_audio:
        return jsonify({"ok": False, "error": f"รองรับ: {', '.join(allowed_audio)}"}), 400

    # บันทึกไฟล์
    import uuid
    from pathlib import Path
    import rag_engine
    save_dir = rag_engine.UPLOAD_DIR / "meetings"
    save_dir.mkdir(exist_ok=True)
    fname = f"meeting_{uuid.uuid4().hex[:8]}{ext}"
    fpath = save_dir / fname
    audio_file.save(str(fpath))

    # AI transcribe + summarize
    try:
        import ai_providers
        with open(fpath, "rb") as af:
            audio_bytes = af.read()

        mime_map = {".mp3": "audio/mpeg", ".mp4": "audio/mp4", ".wav": "audio/wav",
                    ".ogg": "audio/ogg", ".m4a": "audio/mp4", ".webm": "audio/webm", ".aac": "audio/aac"}
        mime = mime_map.get(ext, "audio/mpeg")

        # Step 1: transcribe
        raw = ai_providers.analyze_media_contents(audio_bytes, mime_type=mime)
        transcript = raw.get("summary", "") if isinstance(raw, dict) else str(raw)

        # Step 2: summarize + extract action items
        if transcript:
            prompt = f"""จากบันทึกการประชุมด้านล่าง กรุณา:
1. สรุปประเด็นสำคัญ (ไม่เกิน 5 ข้อ)
2. รายการ Action Items ในรูปแบบ JSON array: [{{"task":"...","assignee":"...","due":""}}]

บันทึกการประชุม:
{transcript}

ตอบในรูปแบบ:
SUMMARY:
<สรุป>

ACTION_ITEMS:
<json array>"""
            ai_resp = ai_providers.generate_response(prompt)

            # parse summary & action items
            summary = ""
            action_items = []
            if "SUMMARY:" in ai_resp and "ACTION_ITEMS:" in ai_resp:
                parts = ai_resp.split("ACTION_ITEMS:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                try:
                    import re
                    json_match = re.search(r'\[.*\]', parts[1], re.DOTALL)
                    if json_match:
                        action_items = json.loads(json_match.group())
                except Exception:
                    action_items = []
            else:
                summary = ai_resp
        else:
            summary = "ไม่สามารถถอดเสียงได้"
            action_items = []

    except Exception as e:
        logger.error(f"[Meeting transcribe] {e}", exc_info=True)
        transcript = ""
        summary = "เกิดข้อผิดพลาดในการถอดเสียง"
        action_items = []

    # บันทึกลงฐานข้อมูล
    mid = database.meeting_note_create(org_id, {
        "title": title,
        "audio_filename": fname,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "participants": participants,
        "meeting_date": meeting_date,
        "created_by": _user(),
    })

    # สร้าง action items เป็น Kanban cards (ถ้ามี)
    if action_items:
        try:
            boards = database.kanban_get_board(org_id) if hasattr(database, 'kanban_get_board') else None
            # พยายามหา column "To Do" หรือ column แรก
            board_data = database.kanban_get_or_create_board(org_id) if hasattr(database, 'kanban_get_or_create_board') else None
        except Exception:
            pass  # ไม่ critical

    database.log_event(f"Meeting notes created: '{title}'", user=_user(), org_id=org_id)

    meeting = database.meeting_note_get(mid, org_id)
    return jsonify({"ok": True, "id": mid, "meeting": meeting})


@features_bp.route("/api/meetings/<int:mid>/save-to-wiki", methods=["POST"])
@login_required
def meeting_save_wiki(mid):
    """บันทึก meeting notes เข้า Wiki อัตโนมัติ"""
    org_id = _org()
    m = database.meeting_note_get(mid, org_id)
    if not m:
        return jsonify({"ok": False, "error": "ไม่พบรายการประชุม"}), 404

    action_md = "\n".join(
        f"- [ ] {a.get('task','')} (ผู้รับผิดชอบ: {a.get('assignee','—')}, กำหนด: {a.get('due','—')})"
        for a in (m.get("action_items") or [])
    )

    content = f"""# {m['title']}

**วันที่ประชุม:** {m.get('meeting_date','')}
**ผู้เข้าร่วม:** {m.get('participants','')}

## สรุปประเด็นสำคัญ
{m.get('summary','')}

## Action Items
{action_md or 'ไม่มี action items'}

---
*บันทึกโดย AI Meeting Assistant*
"""
    slug = f"meeting-{mid}-{date.today().strftime('%Y%m%d')}"
    try:
        page_id = database.wiki_create_page(
            title=m["title"],
            content=content,
            author=_user(),
            slug=slug,
            org_id=org_id,
        )
        database.meeting_note_update(mid, org_id, {**m, "wiki_page_id": page_id})
        return jsonify({"ok": True, "wiki_slug": slug, "page_id": page_id})
    except Exception as e:
        logger.error(f"[Meeting→Wiki] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "บันทึกลง Wiki ไม่สำเร็จ"}), 500
