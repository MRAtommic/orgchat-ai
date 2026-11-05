# -*- coding: utf-8 -*-
"""
line_approvals.py — อนุมัติคำขอเบิกจ่ายผ่าน LINE

ขั้นตอน
  1. พนักงานพิมพ์ใน LINE ส่วนตัว:  "เบิก 500 ค่าเดินทาง"
  2. ระบบสร้างคำขอ แล้วส่งการ์ดอนุมัติไปให้ผู้อนุมัติ (หัวหน้าโดยตรง → หัวหน้าแผนก → แอดมินองค์กร)
  3. ผู้อนุมัติกด ✅/❌ → บันทึกผลแบบครั้งเดียว (กดซ้ำไม่ได้), แจ้งผู้ขอ, และบันทึกลง Google Sheets ขององค์กร

ฟังก์ชันรับตัวส่ง LINE (push) เป็นพารามิเตอร์ เพื่อทดสอบได้โดยไม่ต้องต่อ LINE จริง
"""
import logging
import threading

import database
from db import org_features

logger = logging.getLogger("OrgChatAI.Approvals")

KIND_ICON = {"expense": "💰", "leave": "🏖️", "other": "📄"}


def _money(v) -> str:
    try:
        return f"{float(v):,.2f}".rstrip("0").rstrip(".") + " บาท"
    except Exception:
        return str(v)


def build_approval_flex(req: dict, requester_display: str, dept: str = "") -> dict:
    rid = req["id"]
    rows = [
        ("ผู้ขอ", requester_display + (f" ({dept})" if dept else "")),
        ("รายการ", req["title"]),
        ("จำนวนเงิน", _money(req["amount"])),
        ("เลขที่คำขอ", f"#{rid}"),
    ]
    body = [{
        "type": "box", "layout": "baseline", "spacing": "sm",
        "contents": [
            {"type": "text", "text": k, "color": "#64748B", "size": "sm", "flex": 2},
            {"type": "text", "text": str(v), "wrap": True, "size": "sm", "color": "#0F172A", "flex": 5},
        ],
    } for k, v in rows]
    return {
        "type": "bubble", "size": "mega",
        "header": {"type": "box", "layout": "vertical", "backgroundColor": "#0F172A", "paddingAll": "18px",
                   "contents": [
                       {"type": "text", "text": "คำขออนุมัติเบิกจ่าย", "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                       {"type": "text", "text": "รอการพิจารณาจากคุณ", "color": "#94A3B8", "size": "xs", "margin": "xs"}]},
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "18px", "contents": body},
        "footer": {"type": "box", "layout": "horizontal", "spacing": "md", "paddingAll": "14px", "contents": [
            {"type": "button", "style": "primary", "color": "#10B981", "height": "sm",
             "action": {"type": "postback", "label": "✅ อนุมัติ", "data": f"action=approve_expense&id={rid}",
                        "displayText": f"อนุมัติคำขอ #{rid}"}},
            {"type": "button", "style": "primary", "color": "#EF4444", "height": "sm",
             "action": {"type": "postback", "label": "❌ ปฏิเสธ", "data": f"action=reject_expense&id={rid}",
                        "displayText": f"ปฏิเสธคำขอ #{rid}"}},
        ]},
    }


def _display(username: str) -> str:
    try:
        p = database.get_user_profile(username) if hasattr(database, "get_user_profile") else None
        if p and p.get("display_name"):
            return p["display_name"]
    except Exception:
        pass
    return username


def submit_expense(requester: str, org_id: int, amount: float, title: str, push) -> dict:
    """สร้างคำขอ + ส่งการ์ดให้ผู้อนุมัติ  push(line_user_id, message_dict) -> None
    คืน {"ok", "id", "notified": [username...], "no_approver": bool}"""
    try:
        rid = org_features.create_request(org_id, requester, title, amount, kind="expense")
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    req = org_features.get_request(rid)
    approvers = org_features.find_approvers(org_id, requester)
    bubble = build_approval_flex(req, _display(requester), org_features.get_user_department(requester))
    msg = {"type": "flex", "altText": f"คำขออนุมัติเบิก {_money(amount)} จาก {requester}", "contents": bubble}
    notified = []
    for a in approvers:
        lid = database.get_line_id_by_username(a)
        if not lid:
            continue
        try:
            push(lid, msg)
            notified.append(a)
        except Exception as e:
            logger.error(f"[approval] push to {a} failed: {e}")
    return {"ok": True, "id": rid, "notified": notified, "no_approver": not notified, "approvers": approvers}


def handle_decision(action: str, req_id, line_user_id: str, push_text) -> str:
    """ประมวลผลการกดอนุมัติ/ปฏิเสธ คืนข้อความตอบกลับผู้กด
    push_text(username, text) ใช้แจ้งผลกลับไปยังผู้ขอ"""
    status = "approved" if action == "approve_expense" else "rejected"
    try:
        req = org_features.get_request(int(req_id))
    except (TypeError, ValueError):
        req = None
    if not req:
        return f"⚠️ ไม่พบคำขอ #{req_id} ในระบบค่ะ"
    approver = database.get_username_by_line_id(line_user_id)
    if not approver:
        return "⚠️ ยังไม่ได้ผูกบัญชี LINE กับระบบ จึงไม่สามารถอนุมัติได้ค่ะ"
    if req["status"] != "pending":
        return f"ℹ️ คำขอ #{req['id']} ถูก{org_features.STATUS_LABEL.get(req['status'], req['status'])}ไปแล้วโดย {req.get('approver') or '-'} ค่ะ"
    if not org_features.can_decide(req["org_id"], approver, req):
        if (req["requester"] or "").lower() == approver.lower():
            return "🚫 ไม่สามารถอนุมัติคำขอของตัวเองได้ค่ะ"
        return "⚠️ เฉพาะหัวหน้าโดยตรง หัวหน้าแผนก หรือแอดมินเท่านั้นที่อนุมัติคำขอนี้ได้ค่ะ"
    if not org_features.decide_request(req["id"], status, approver, note="ผ่าน LINE"):
        return f"ℹ️ คำขอ #{req['id']} ถูกดำเนินการไปแล้วค่ะ"

    req = org_features.get_request(req["id"])
    label = org_features.STATUS_LABEL[status]
    try:
        push_text(req["requester"],
                  f"{'✅' if status == 'approved' else '❌'} คำขอเบิก #{req['id']} ({req['title']} {_money(req['amount'])}) "
                  f"ได้รับการ{label}โดย {approver}")
    except Exception as e:
        logger.error(f"[approval] notify requester failed: {e}")
    threading.Thread(target=org_features.append_to_sheet, args=(req,), daemon=True).start()
    return f"{'✅' if status == 'approved' else '❌'} {label}คำขอ #{req['id']} เรียบร้อยแล้วค่ะ และบันทึกลงชีตให้แล้ว"


def log_leave_decision(leave: dict, status: str, approver: str, org_id):
    """บันทึกผลการอนุมัติลา (ที่มีอยู่เดิม) ลงชีตเดียวกับคำขอเบิก เพื่อดูรวมที่เดียว"""
    try:
        req = {
            "id": f"L{leave.get('id')}", "org_id": org_id, "kind": "leave",
            "requester": leave.get("username") or "",
            "title": f"{leave.get('type') or leave.get('leave_type') or 'ลา'} {leave.get('start_date')} – {leave.get('end_date')}",
            "amount": 0, "status": status, "approver": approver, "note": "ผ่าน LINE",
            "created_at": str(leave.get("created_at") or ""), "decided_at": "",
        }
        threading.Thread(target=org_features.append_to_sheet, args=(req,), daemon=True).start()
    except Exception as e:
        logger.error(f"[approval] leave sheet log failed: {e}")


def pending_summary(username: str, org_id: int) -> str:
    """รายการรออนุมัติที่ผู้ใช้คนนี้มีสิทธิ์พิจารณา (คำสั่ง "รออนุมัติ")"""
    items = []
    for r in org_features.list_requests(org_id, status="pending", limit=50):
        if org_features.can_decide(org_id, username, r):
            items.append(r)
    if not items:
        return "ไม่มีคำขอที่รออนุมัติค่ะ ✨"
    lines = [f"📋 คำขอรออนุมัติ {len(items)} รายการ"]
    for r in items[:10]:
        lines.append(f"• #{r['id']} {r['requester']} — {r['title']} {_money(r['amount'])}")
    lines.append("กดอนุมัติได้ที่การ์ดที่ระบบส่งให้ค่ะ")
    return "\n".join(lines)
