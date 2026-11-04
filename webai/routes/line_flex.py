# -*- coding: utf-8 -*-
"""
routes/line_flex.py — LINE Flex Message builders (แยกออกจาก routes/line_webhook.py)

ฟังก์ชันที่นี่สร้าง dict ของ Flex Message เป็นหลัก ไม่ผูกกับ Flask route
routes/line_webhook.py re-export ชื่อทั้งหมดไว้ เพื่อให้ import เดิม
(`from routes.line_webhook import create_expense_flex_bubble` ฯลฯ) ยังใช้ได้
"""
import re
import json
import logging
from datetime import datetime, timedelta

import database
from google_drive_service import google_manager, get_bangkok_now

logger = logging.getLogger("OrgChatAI.Line")

def clean_flex_payload(obj):
    """Recursively removes keys that violate LINE API schema, e.g. weight values other than 'bold', letterSpacing, etc."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if k == "weight" and v != "bold":
                continue
            if k in ("letterSpacing", "borderWidth"):
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

def create_leave_approval_flex_bubble(leave_id, applicant_name, leave_type, start_date, end_date, reason, department=None, position=None):
    """Creates a high-end 1-Click approval Flex Message for Managers/Admins in LINE."""
    LEAVE_MAP = {
        "Sick": "ลาป่วย (Sick Leave)",
        "Personal": "ลากิจ (Personal Leave)",
        "Vacation": "ลาพักร้อน (Vacation Leave)",
        "Military": "ลาเกณฑ์ทหาร",
        "Maternity": "ลาคลอด",
        "Other": "อื่นๆ (Other)"
    }
    leave_type_display = LEAVE_MAP.get(str(leave_type).strip(), str(leave_type))

    info_items = [
        {
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": "ผู้ขอลา", "color": "#64748B", "size": "xs", "flex": 3},
                {"type": "text", "text": str(applicant_name), "color": "#0F172A", "size": "xs", "weight": "bold", "flex": 7}
            ]
        }
    ]

    dept_pos_parts = []
    if position:
        dept_pos_parts.append(str(position))
    if department:
        dept_pos_parts.append(str(department))
    if dept_pos_parts:
        info_items.append({
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": "ตำแหน่ง/แผนก", "color": "#64748B", "size": "xs", "flex": 3},
                {"type": "text", "text": " · ".join(dept_pos_parts), "color": "#6366F1", "size": "xs", "weight": "bold", "flex": 7}
            ]
        })

    info_items.extend([
        {
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": "ประเภทการลา", "color": "#64748B", "size": "xs", "flex": 3},
                {"type": "text", "text": str(leave_type_display), "color": "#2563EB", "size": "xs", "weight": "bold", "flex": 7}
            ]
        },
        {
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": "ช่วงวันลา", "color": "#64748B", "size": "xs", "flex": 3},
                {"type": "text", "text": f"{start_date} ถึง {end_date}", "color": "#0F172A", "size": "xs", "weight": "bold", "flex": 7}
            ]
        },
        {
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": "เหตุผล", "color": "#64748B", "size": "xs", "flex": 3},
                {"type": "text", "text": str(reason or "-"), "color": "#334155", "size": "xs", "wrap": True, "flex": 7}
            ]
        }
    ])

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#0F172A",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": "HR LEAVE REQUEST",
                    "color": "#94A3B8",
                    "weight": "bold",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"คำขออนุมัติการลา #{leave_id}",
                    "color": "#FFFFFF",
                    "weight": "bold",
                    "size": "lg",
                    "margin": "xs"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": info_items
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "paddingAll": "16px",
            "backgroundColor": "#F8FAFC",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#10B981",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "✅ อนุมัติ",
                        "data": f"action=approve_leave&id={leave_id}",
                        "displayText": f"อนุมัติคำขอลา #{leave_id}"
                    }
                },
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#EF4444",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "❌ ปฏิเสธ",
                        "data": f"action=reject_leave&id={leave_id}",
                        "displayText": f"ปฏิเสธคำขอลา #{leave_id}"
                    }
                }
            ]
        }
    }
    return clean_flex_payload(bubble)

def create_morning_briefing_flex_bubble(org_name, date_str, meetings, leaves_today, expenses_24h, pending_leaves_count=0):
    """
    Creates a premium, rich Executive & Team Morning Briefing Flex Card for LINE.
    Includes:
      - 📅 Today's Meetings & Schedules
      - 🏖️ Team Members on Leave Today
      - 💰 Financial Expenses Summary (Last 24h)
      - ⏳ Pending Leave Requests requiring Admin approval
    """
    # 1. Schedule Items Box
    schedule_rows = []
    if meetings:
        for s in meetings[:4]:
            t_str = s.get('start_time') or s.get('time') or '09:00'
            title = s.get('title', 'นัดหมาย')
            schedule_rows.append({
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "•", "color": "#3B82F6", "size": "xs", "flex": 1},
                    {"type": "text", "text": f"{t_str} น.", "color": "#1D4ED8", "size": "xs", "weight": "bold", "flex": 3},
                    {"type": "text", "text": title[:30], "color": "#1E293B", "size": "xs", "weight": "bold", "flex": 8, "wrap": False}
                ]
            })
        if len(meetings) > 4:
            schedule_rows.append({
                "type": "text",
                "text": f"+ อีก {len(meetings) - 4} นัดหมายในระบบ...",
                "size": "xxs",
                "color": "#64748B",
                "margin": "xs"
            })
    else:
        schedule_rows.append({
            "type": "text",
            "text": "✨ วันนี้ไม่มีกำหนดการนัดหมาย",
            "size": "xs",
            "color": "#94A3B8",
            "style": "italic"
        })

    # 2. Leaves Today Box
    leave_rows = []
    if leaves_today:
        for lv in leaves_today[:3]:
            name = lv.get('display_name') or lv.get('username') or 'พนักงาน'
            ltype = lv.get('type') or lv.get('leave_type') or 'ลาหยุด'
            leave_rows.append({
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "🏖️", "size": "xs", "flex": 1},
                    {"type": "text", "text": name, "color": "#0F172A", "size": "xs", "weight": "bold", "flex": 6},
                    {"type": "text", "text": f"({ltype})", "color": "#E11D48", "size": "xs", "align": "end", "flex": 4}
                ]
            })
        if len(leaves_today) > 3:
            leave_rows.append({
                "type": "text",
                "text": f"+ อีก {len(leaves_today) - 3} ท่าน...",
                "size": "xxs",
                "color": "#64748B",
                "margin": "xs"
            })
    else:
        leave_rows.append({
            "type": "text",
            "text": "👥 ทุกคนปฏิบัติงานพร้อมเพรียง (ไม่มีใครลา)",
            "size": "xs",
            "color": "#10B981"
        })

    # 3. Financial Box
    exp_count = expenses_24h.get('count', 0)
    exp_total = expenses_24h.get('total_amount', 0)
    finance_text = f"บันทึก {exp_count} รายการ ({exp_total:,.2f} ฿)" if exp_count > 0 else "ไม่มีรายการใหม่ใน 24 ชม."

    # 4. Pending Approval Banner
    pending_box = []
    if pending_leaves_count > 0:
        pending_box = [
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#FEF2F2",
                "cornerRadius": "12px",
                "paddingAll": "10px",
                "margin": "md",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "⏳", "size": "xs", "flex": 1},
                            {"type": "text", "text": f"มี {pending_leaves_count} ใบลาค้างรออนุมัติ", "color": "#DC2626", "size": "xs", "weight": "bold", "flex": 10}
                        ]
                    }
                ]
            }
        ]

    bubble = {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#1E1B4B",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {
                            "type": "text",
                            "text": "SMART MORNING BRIEFING",
                            "color": "#A5B4FC",
                            "size": "xxs",
                            "weight": "bold",
                            "flex": 8
                        },
                        {
                            "type": "text",
                            "text": "🌅 08:30",
                            "color": "#FBBF24",
                            "size": "xs",
                            "weight": "bold",
                            "align": "end",
                            "flex": 4
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": f"สวัสดีตอนเช้า 🌿",
                    "color": "#FFFFFF",
                    "size": "xl",
                    "weight": "bold",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"สรุปภาพรวมประจำวัน • {org_name} ({date_str})",
                    "color": "#C7D2FE",
                    "size": "xs",
                    "margin": "xs"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF",
            "contents": [
                # Section: Meetings
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📅 กำหนดการ & นัดหมายวันนี้",
                            "size": "xs",
                            "weight": "bold",
                            "color": "#334155",
                            "margin": "none"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "sm",
                            "spacing": "xs",
                            "contents": schedule_rows
                        }
                    ]
                },
                {"type": "separator", "margin": "lg"},
                # Section: Team Leaves
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🏖️ การลางานของทีมวันนี้",
                            "size": "xs",
                            "weight": "bold",
                            "color": "#334155"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "sm",
                            "spacing": "xs",
                            "contents": leave_rows
                        }
                    ]
                },
                {"type": "separator", "margin": "lg"},
                # Section: Expenses
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "💰 บันทึกค่าใช้จ่าย (24 ชม. ที่ผ่านมา)",
                            "size": "xs",
                            "weight": "bold",
                            "color": "#334155"
                        },
                        {
                            "type": "text",
                            "text": finance_text,
                            "size": "xs",
                            "color": "#059669" if exp_count > 0 else "#64748B",
                            "weight": "bold" if exp_count > 0 else "regular",
                            "margin": "xs"
                        }
                    ]
                },
                *pending_box
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "16px",
            "backgroundColor": "#F8FAFC",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#4F46E5",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "🚀 เปิด Dashboard องค์กร",
                        "uri": "https://openchat.sbs/"
                    }
                }
            ]
        }
    }
    return clean_flex_payload(bubble)

def create_onboarding_guide_flex_bubble(base_url, link_magic_url=None):
    """Creates a welcome & onboarding guide Flex Bubble for newly joined users in LINE."""
    actions = []
    if link_magic_url:
        actions.append({
            "type": "button",
            "style": "primary",
            "color": "#6366F1",
            "height": "sm",
            "action": {
                "type": "uri",
                "label": "🔗 ผูกบัญชีผู้ใช้งานทันที",
                "uri": link_magic_url
            }
        })
    
    actions.append({
        "type": "button",
        "style": "secondary",
        "color": "#F1F5F9",
        "height": "sm",
        "action": {
            "type": "uri",
            "label": "🌐 เข้าสู่ Web Portal",
            "uri": f"{base_url}/dashboard"
        }
    })

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#4F46E5",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": "WELCOME TO ORGCHAT AI",
                    "color": "#E0E7FF",
                    "weight": "bold",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": "ยินดีต้อนรับสู่น้องพั้น AI ผู้ช่วยองค์กร ✨",
                    "color": "#FFFFFF",
                    "weight": "bold",
                    "size": "md",
                    "margin": "xs"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "น้องพั้นพร้อมช่วยคุณจัดการงานและข้อมูลองค์กรได้ง่ายๆ ใน LINE เลยค่ะ:",
                    "color": "#475569",
                    "size": "xs",
                    "wrap": True
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "📸", "size": "xs", "flex": 1},
                                {"type": "text", "text": "ส่งรูปสลิป / ใบเสร็จ → AI ถอดข้อมูลลง Google Sheets และเซฟลง Drive อัตโนมัติ", "color": "#1E293B", "size": "xs", "wrap": True, "flex": 9}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "📝", "size": "xs", "flex": 1},
                                {"type": "text", "text": "พิมพ์ 'ขอลาป่วย' หรือ 'ลากิจ' → ยื่นใบลาส่งตรงหาหัวหน้างานทันที", "color": "#1E293B", "size": "xs", "wrap": True, "flex": 9}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "📊", "size": "xs", "flex": 1},
                                {"type": "text", "text": "พิมพ์ 'สรุปรายจ่ายวันนี้' → ดูยอดเงินและหมวดหมู่การเบิกจ่าย", "color": "#1E293B", "size": "xs", "wrap": True, "flex": 9}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "📍", "size": "xs", "flex": 1},
                                {"type": "text", "text": "แชร์ตำแหน่ง (Location) → บันทึกเวลาเข้า-ออกงาน GPS พร้อมคำนวณระยะห่างออฟฟิศ", "color": "#1E293B", "size": "xs", "wrap": True, "flex": 9}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "🔍", "size": "xs", "flex": 1},
                                {"type": "text", "text": "ถามคำถามเรื่ององค์กรหรือค้นหาเอกสาร (RAG) ได้ 24 ชม.", "color": "#1E293B", "size": "xs", "wrap": True, "flex": 9}
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "16px",
            "backgroundColor": "#F8FAFC",
            "contents": actions
        }
    }
    return clean_flex_payload(bubble)

def extract_smart_amount(ext, analysis=None, qr_decoded=None, raw_result=None):
    """
    Robustly extracts financial transaction amount with multi-layer fallback:
    1. Direct ext net_amount, total_amount, amount, gross_amount, transfer_amount
    2. QR Code Tag 54 (EMVCo)
    3. AI summary regex (e.g. 'จำนวน 50.00 บาท', '50.00 THB')
    4. smart_name / filename regex (e.g. '_50.00.jpg')
    """
    import re
    if ext and isinstance(ext, dict):
        for k in ['net_amount', 'total_amount', 'amount', 'gross_amount', 'transfer_amount', 'paid_amount']:
            val = ext.get(k)
            if val is not None and str(val).strip() not in ['', '-', '0', '0.0', '0.00', 'None', 'null']:
                try:
                    c = float(str(val).replace(',', '').replace('฿', '').replace('THB', '').strip())
                    if c > 0:
                        return c
                except (ValueError, TypeError):
                    pass
    if qr_decoded and isinstance(qr_decoded, dict) and qr_decoded.get('amount'):
        try:
            c = float(str(qr_decoded['amount']).replace(',', '').strip())
            if c > 0:
                return c
        except (ValueError, TypeError):
            pass
    if not analysis and raw_result and isinstance(raw_result, dict):
        analysis = raw_result.get('analysis')
    if analysis and isinstance(analysis, dict):
        summary = analysis.get('summary', '')
        if summary:
            m = re.search(r'(?:จำนวน|ยอดเงิน|ยอดโอน|ยอดสุทธิ|ยอดรวม|เป็นเงิน)?\s*([\d,]+(?:\.\d{1,2})?)\s*(?:บาท|THB)', summary)
            if m:
                try:
                    c = float(m.group(1).replace(',', '').strip())
                    if c > 0:
                        return c
                except (ValueError, TypeError):
                    pass
        s_name = analysis.get('smart_name', '')
        if s_name:
            m = re.search(r'_([\d,]+(?:\.\d{1,2})?)\.(?:jpg|jpeg|png|pdf)', s_name, re.I)
            if m:
                try:
                    c = float(m.group(1).replace(',', '').strip())
                    if c > 0:
                        return c
                except (ValueError, TypeError):
                    pass
    return None

def create_expense_flex_bubble(sheet_name, folder_name, net_amount, date_str, memo, vendor, file_link, sheet_url, edit_data_postback, raw_result=None, org_id=None, username=None):
    """Creates an ultra-premium LINE Flex Message, custom tailored to each document type."""
    # Extract row_num safely
    row_num = 1
    if edit_data_postback:
        try:
            for part in str(edit_data_postback).split("&"):
                if part.startswith("row="):
                    row_num = int(part.split("=")[1])
        except (ValueError, IndexError):
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
        except (ValueError, IndexError):
            pass

    # Clean amount display with smart fallbacks
    if not net_amount or str(net_amount).strip() in ['0', '0.0', '0.00', 'None', '', '-']:
        smart_amt = extract_smart_amount(ext, raw_result=raw_result)
        if smart_amt is not None and smart_amt > 0:
            net_amount = smart_amt

    try:
        if isinstance(net_amount, (int, float)):
            amount_big = f"{net_amount:,.2f}"
        else:
            val_clean = str(net_amount).replace(",", "").strip()
            val_float = float(val_clean)
            amount_big = f"{val_float:,.2f}"
    except (ValueError, TypeError):
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

    # If the document has a verified QR code for a bank transfer slip, override classification to 'slip'
    qr_status = ""
    if raw_result and isinstance(raw_result, dict):
        qr_status = raw_result.get("verification_status", "")
    
    if qr_status and str(qr_status).startswith("ผ่าน"):
        norm_ai_cat = "slip"

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
            except (ValueError, TypeError):
                pass
            try:
                total_deposit += float(str(d_val).replace(',', '').strip()) if d_val and str(d_val) != '-' else 0.0
            except (ValueError, TypeError):
                pass

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
        except (ValueError, TypeError):
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
                except (ValueError, TypeError): w_float = 0.0
                try:
                    d_float = float(str(t_deposit).replace(',', '').strip()) if t_deposit and str(t_deposit) != '-' else 0.0
                except (ValueError, TypeError): d_float = 0.0

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

        v_status = raw_result.get("verification_status", "-") if raw_result else "-"
        status_color = "#334155"
        if "ผ่าน" in v_status:
            status_color = "#0D9488"
        elif "ไม่ผ่าน" in v_status or "ข้อผิดพลาด" in v_status:
            status_color = "#E11D48"

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
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "QR VERIFICATION", "color": "#64748B", "size": "xxs", "weight": "bold", "flex": 4},
                    {"type": "text", "text": v_status, "color": status_color, "size": "xs", "weight": "bold", "flex": 8, "align": "end"}
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
        except (ValueError, TypeError): gross_str = str(gross_amt)
        try: vat_str = f"{float(str(vat_amt).replace(',', '')):,.2f} THB" if vat_amt and str(vat_amt) != '-' else "-"
        except (ValueError, TypeError): vat_str = str(vat_amt)
        try: wht_str = f"{float(str(wht_amt).replace(',', '')):,.2f} THB" if wht_amt and str(wht_amt) != '-' else "-"
        except (ValueError, TypeError): wht_str = str(wht_amt)

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
        except (ValueError, TypeError): wht_str = str(wht_amt)

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
    
    # Format amount beautifully with smart fallbacks
    ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
    smart_amt = extract_smart_amount(ext, analysis=r.get('analysis'), raw_result=r)
    net_amt = smart_amt if (smart_amt is not None and smart_amt > 0) else ext.get('net_amount')
    try:
        val_clean = str(net_amt).replace(",", "").strip()
        val_float = float(val_clean)
        amt_str = f"{val_float:,.2f} THB" if val_float > 0 else "-"
    except (ValueError, TypeError):
        amt_str = f"{net_amt} THB" if net_amt and str(net_amt).strip() not in ['0', '0.0', '0.00', '-'] else "-"

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
    except (ValueError, TypeError):
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
        smart_amt = extract_smart_amount(ext, analysis=r.get('analysis'), raw_result=r)
        net_amt = smart_amt if (smart_amt is not None and smart_amt > 0) else ext.get('net_amount')
        
        parsed_amt = 0.0
        if net_amt is not None and str(net_amt).strip() not in ['-', '0', '0.0', '0.00']:
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
    except Exception as e:
        logger.warning(f"[resolve_folder_url] Error finding subfolder: {e}")
        
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

def create_line_flex_bubble(title, subtitle, fields=None, color="#2563eb"):
    """Creates a structured LINE Flex Message bubble for notifications and calendar events."""
    body_contents = [
        { "type": "text", "text": str(title), "weight": "bold", "size": "md", "color": color },
        { "type": "text", "text": str(subtitle), "size": "xs", "color": "#64748b", "margin": "xs" },
        { "type": "separator", "margin": "md" }
    ]
    
    if fields and isinstance(fields, dict):
        for k, v in fields.items():
            if not v: continue
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "sm",
                "contents": [
                    { "type": "text", "text": str(k), "color": "#64748b", "size": "xs", "flex": 2 },
                    { "type": "text", "text": str(v), "color": "#1e293b", "size": "xs", "weight": "bold", "flex": 5, "wrap": True }
                ]
            })
            
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                { "type": "text", "text": "📌 OrgChat — ระบบปฏิทินและแจ้งเตือนองค์กร", "size": "xxs", "color": "#94a3b8", "align": "center" }
            ]
        }
    }
    return clean_flex_payload(bubble)

def create_meeting_reminder_flex_bubble(schedule, minutes_before=30):
    """Creates a beautiful LINE Flex Message for upcoming meeting reminders."""
    title = schedule.get("title", "การประชุม / นัดหมาย")
    start_date = schedule.get("start_date", "-")
    start_time = schedule.get("start_time", "09:00")
    category = schedule.get("category", "Meeting")
    desc = schedule.get("description") or "-"
    owner = schedule.get("display_name") or schedule.get("username") or "ทีมงาน"

    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFBEB",
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
                            "backgroundColor": "#F59E0B",
                            "cornerRadius": "20px",
                            "paddingAll": "4px",
                            "paddingStart": "10px",
                            "paddingEnd": "10px",
                            "contents": [
                                {"type": "text", "text": "UPCOMING", "size": "xxs", "color": "#FFFFFF", "weight": "bold"}
                            ]
                        },
                        {"type": "filler"}
                    ]
                },
                {
                    "type": "text",
                    "text": f"⏰ แจ้งเตือน: อีก {minutes_before} นาทีจะถึงเวลานัด",
                    "weight": "bold",
                    "size": "md",
                    "color": "#B45309",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "xl",
                    "color": "#0F172A",
                    "margin": "xs",
                    "wrap": True
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
                {"type": "separator", "color": "#F1F5F9"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "margin": "lg",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "📅 วันที่", "size": "xs", "color": "#64748B", "flex": 2},
                                {"type": "text", "text": str(start_date), "size": "xs", "color": "#0F172A", "weight": "bold", "flex": 5}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "⏰ เวลา", "size": "xs", "color": "#64748B", "flex": 2},
                                {"type": "text", "text": f"{start_time} น.", "size": "xs", "color": "#2563EB", "weight": "bold", "flex": 5}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "🏷️ ประเภท", "size": "xs", "color": "#64748B", "flex": 2},
                                {"type": "text", "text": str(category), "size": "xs", "color": "#0F172A", "flex": 5}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "👤 ผู้จัด", "size": "xs", "color": "#64748B", "flex": 2},
                                {"type": "text", "text": str(owner), "size": "xs", "color": "#0F172A", "flex": 5}
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📌 OrgChat — ปฏิทินและระบบแจ้งเตือนองค์กร",
                    "size": "xxs",
                    "color": "#94A3B8",
                    "align": "center"
                }
            ]
        }
    }

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
        if not folders:
            # Drive connected but parent folder missing or inaccessible
            if not mgr.drive_service:
                err_msg = "Google Drive ยังไม่ได้เชื่อมต่อค่ะ\nกรุณาให้ Admin เชื่อมต่อ Drive ก่อนนะคะ 🔗"
            else:
                err_msg = "ไม่พบโฟลเดอร์ใน Google Drive ค่ะ\nอาจถูกลบหรือสิทธิ์ไม่เพียงพอ\nกรุณาให้ Admin ตรวจสอบการตั้งค่า Drive นะคะ ⚙️"
            return {
                "_drive_unavailable": True,
                "type": "flex",
                "altText": "ไม่พบโฟลเดอร์ Google Drive",
                "contents": {
                    "type": "bubble",
                    "size": "kilo",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "⚠️ Drive ไม่พร้อมใช้งาน",
                                "weight": "bold",
                                "size": "md",
                                "color": "#b45309"
                            },
                            {
                                "type": "text",
                                "text": err_msg,
                                "size": "sm",
                                "color": "#64748b",
                                "wrap": True
                            }
                        ]
                    }
                }
            }
        
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
