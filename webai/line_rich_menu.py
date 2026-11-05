# -*- coding: utf-8 -*-
"""
line_rich_menu.py — Rich Menu ปรับตามบทบาท (พนักงาน / หัวหน้า / แอดมิน)

  setup_menus(org_id, token)        สร้างเมนู 3 แบบบน LINE OA + อัปโหลดรูป + ตั้งเมนูพนักงานเป็นค่าเริ่มต้น
  apply_role_menu(line_id, role...) ผูกเมนูตามบทบาทให้ผู้ใช้รายคน
  ensure_user_menu(...)             เรียกตอนผู้ใช้ทักเข้ามา — ผูกเมนูให้ถูกบทบาทเมื่อบทบาทเปลี่ยน

ตัวเรียก HTTP รับเป็นพารามิเตอร์ (http=requests) เพื่อทดสอบโดยไม่ยิง LINE จริง
"""
import io
import logging
import os
import threading
import time

from db import org_features

logger = logging.getLogger("OrgChatAI.RichMenu")

WIDTH, HEIGHT = 2500, 1686
CELL_W, CELL_H = (833, 833, 834), 843

# (ข้อความบนปุ่ม, ไอคอน, สี, action)  action = ("message", text) | ("uri", path)
MENUS = {
    "employee": [
        ("ค้นหาเอกสาร", "🔍", "#06b6d4", ("message", "ค้นหา ")),
        ("ขอลางาน", "📝", "#ec4899", ("message", "ลางาน")),
        ("เบิกจ่าย", "💰", "#10b981", ("message", "เบิก")),
        ("ประวัติการลา", "📋", "#f59e0b", ("message", "ประวัติการลา")),
        ("เปิดเว็บ", "🌐", "#6366f1", ("uri", "/")),
        ("ผูกบัญชี", "👤", "#8b5cf6", ("message", "ผูกบัญชี")),
    ],
    "manager": [
        ("รออนุมัติ", "✅", "#10b981", ("message", "รออนุมัติ")),
        ("ค้นหาเอกสาร", "🔍", "#06b6d4", ("message", "ค้นหา ")),
        ("สรุปรายจ่าย", "📈", "#f59e0b", ("message", "สรุปรายจ่ายวันนี้")),
        ("ขอลางาน", "📝", "#ec4899", ("message", "ลางาน")),
        ("เบิกจ่าย", "💰", "#6366f1", ("message", "เบิก")),
        ("เปิดเว็บ", "🌐", "#8b5cf6", ("uri", "/")),
    ],
    "admin": [
        ("แดชบอร์ด", "📊", "#6366f1", ("uri", "/dashboard")),
        ("รออนุมัติ", "✅", "#10b981", ("message", "รออนุมัติ")),
        ("สรุปรายจ่าย", "📈", "#f59e0b", ("message", "สรุปรายจ่ายวันนี้")),
        ("ลิงก์ชีต/ไดรฟ์", "🔗", "#06b6d4", ("message", "ขอลิงก์")),
        ("ค้นหาเอกสาร", "🔍", "#ec4899", ("message", "ค้นหา ")),
        ("จัดการองค์กร", "🏢", "#8b5cf6", ("uri", "/")),
    ],
}
MENU_TITLE = {"employee": "เมนูพนักงาน", "manager": "เมนูหัวหน้า", "admin": "เมนูผู้ดูแล"}


def _areas(role: str, base_url: str) -> list:
    areas = []
    for i, (_label, _icon, _color, (kind, val)) in enumerate(MENUS[role]):
        col, row = i % 3, i // 3
        x = sum(CELL_W[:col])
        action = ({"type": "message", "text": val} if kind == "message"
                  else {"type": "uri", "uri": base_url.rstrip("/") + val})
        areas.append({"bounds": {"x": x, "y": row * CELL_H, "width": CELL_W[col], "height": CELL_H}, "action": action})
    return areas


def render_image(role: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (WIDTH, HEIGHT), "#0f172a")
    d = ImageDraw.Draw(img)

    def font(size, emoji=False):
        names = (["seguiemj.ttf"] if emoji else []) + ["tahoma.ttf", "Tahoma.ttf", "THSarabunNew.ttf", "Sarabun-Regular.ttf",
                                                       "NotoSansThai-Regular.ttf", "DejaVuSans.ttf"]
        for base in ("C:\\Windows\\Fonts\\", "/usr/share/fonts/truetype/dejavu/", ""):
            for n in names:
                try:
                    return ImageFont.truetype(base + n, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    f_text, f_icon = font(76), font(96, emoji=True)
    d.line([(833, 0), (833, HEIGHT)], fill="#1e293b", width=5)
    d.line([(1666, 0), (1666, HEIGHT)], fill="#1e293b", width=5)
    d.line([(0, 843), (WIDTH, 843)], fill="#1e293b", width=5)
    for i, (label, icon, color, _a) in enumerate(MENUS[role]):
        cx = sum(CELL_W[:i % 3]) + CELL_W[i % 3] // 2
        cy = (i // 3) * CELL_H + CELL_H // 2
        try:
            d.text((cx, cy - 90), icon, font=f_icon, fill=color, anchor="mm", embedded_color=True)
        except Exception:
            pass
        d.text((cx, cy + 110), label, font=f_text, fill="#f8fafc", anchor="mm")
    d.rectangle([(0, 0), (WIDTH, 15)], fill={"employee": "#06b6d4", "manager": "#10b981", "admin": "#6366f1"}[role])
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _hdr(token, ctype="application/json"):
    return {"Authorization": f"Bearer {token}", "Content-Type": ctype}


def setup_menus(org_id: int, token: str, base_url: str = None, http=None) -> dict:
    """สร้างเมนูครบ 3 บทบาท  คืน {"ok", "menus": {role: id}, "errors": [...]}"""
    if http is None:
        import requests as http
    base_url = (base_url or os.environ.get("BASE_URL") or "https://openchat.sbs").rstrip("/")
    old = org_features.get_menu_ids(org_id)
    result, errors = {}, []
    for role in org_features.MENU_ROLES:
        body = {"size": {"width": WIDTH, "height": HEIGHT}, "selected": role == "employee",
                "name": f"OrgChat-{role}-org{org_id}", "chatBarText": MENU_TITLE[role], "areas": _areas(role, base_url)}
        r = http.post("https://api.line.me/v2/bot/richmenu", headers=_hdr(token), json=body, timeout=15)
        if r.status_code != 200:
            errors.append(f"{role}: สร้างเมนูไม่สำเร็จ ({r.status_code})")
            continue
        mid = r.json().get("richMenuId")
        up = http.post(f"https://api-data.line.me/v2/bot/richmenu/{mid}/content", headers=_hdr(token, "image/png"),
                       data=render_image(role), timeout=30)
        if up.status_code != 200:
            errors.append(f"{role}: อัปโหลดรูปไม่สำเร็จ ({up.status_code})")
            try:
                http.delete(f"https://api.line.me/v2/bot/richmenu/{mid}", headers=_hdr(token), timeout=10)
            except Exception:
                pass
            continue
        org_features.save_menu_id(org_id, role, mid)
        result[role] = mid
        if old.get(role):  # เก็บกวาดเมนูเดิมของระบบนี้ (ไม่แตะเมนูอื่นของ OA)
            try:
                http.delete(f"https://api.line.me/v2/bot/richmenu/{old[role]}", headers=_hdr(token), timeout=10)
            except Exception:
                pass
    if result.get("employee"):
        d = http.post(f"https://api.line.me/v2/bot/user/all/richmenu/{result['employee']}", headers=_hdr(token), timeout=15)
        if d.status_code != 200:
            errors.append(f"ตั้งเมนูเริ่มต้นไม่สำเร็จ ({d.status_code})")
    _ROLE_CACHE.clear()
    return {"ok": len(result) == len(org_features.MENU_ROLES) and not errors, "menus": result, "errors": errors}


def apply_role_menu(line_user_id: str, role: str, org_id: int, token: str, http=None) -> bool:
    if role not in org_features.MENU_ROLES:
        role = "employee"
    mid = org_features.get_menu_ids(org_id).get(role)
    if not (mid and token and line_user_id):
        return False
    if http is None:
        import requests as http
    try:
        r = http.post(f"https://api.line.me/v2/bot/user/{line_user_id}/richmenu/{mid}", headers=_hdr(token), timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.warning(f"[rich-menu] link failed: {e}")
        return False


_ROLE_CACHE: dict = {}
_ROLE_TTL = 600


def ensure_user_menu(line_user_id: str, username: str, org_id, token: str, http=None, background=True) -> None:
    """ผูกเมนูตามบทบาทเมื่อบทบาทเปลี่ยน (cache ในหน่วยความจำ 10 นาที ไม่ยิง LINE ทุกข้อความ)"""
    if not (line_user_id and username and org_id and token):
        return
    role = org_features.role_for_menu(username, org_id)
    hit = _ROLE_CACHE.get(line_user_id)
    if hit and hit[0] == role and time.time() - hit[1] < _ROLE_TTL:
        return

    def _do():
        if apply_role_menu(line_user_id, role, org_id, token, http=http):
            _ROLE_CACHE[line_user_id] = (role, time.time())

    if background:
        threading.Thread(target=_do, daemon=True).start()
    else:
        _do()
