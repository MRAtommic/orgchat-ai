# -*- coding: utf-8 -*-
"""
routes/line.py — LINE Bot & Webhook Blueprint
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, send_from_directory, send_file, abort, redirect, session, current_app, Response
from flask_socketio import emit, join_room, leave_room
from werkzeug.utils import secure_filename
from functools import wraps
from pathlib import Path
import os
import sys
import io
import uuid
import time
import sqlite3
import threading
import urllib.parse
import re
import hmac
import hashlib
import base64
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
http_requests = requests
import logging

from google import genai
from fpdf import FPDF

import database
import rag_engine
import export_service
import ai_providers
import notification_db
import billing
import payment
from google_drive_service import google_manager, GoogleWorkspaceManager, get_bangkok_now
import google_drive_service
from task_tracker import db_task_tracker
from reconciliation_service import ReconciliationService
import settings_manager
from redis_manager import RedisManager
import web_crawler
import tts_engine

from routes.shared import (
    VERSION, socketio, _limiter, login_required, admin_required,
    PENDING_LINE_LINKS, _OAUTH_STATES, _store_oauth_state, _pop_oauth_state,
    send_push_notification, batch_send_push_notification,
    get_weather_context, THAI_HOLIDAYS_2026, get_current_time,
    VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS,
    OAUTH2_AVAILABLE, oauth2_service,
    _set_session_org, get_current_org_id,
    _get_gemini_api_key, _configure_gemini,
    can_edit_knowledge_base, can_view_knowledge_base, can_delete_knowledge_base,
    is_admin, get_rag_filter,
    safe_thread_target, validate_uploaded_file,
    ALLOWED_EXTENSIONS, _is_safe_url,
    online_users_registry,
    USERS, superadmin_required,
)

logger = logging.getLogger("OrgChatAI.Line")

def strip_think_tags(text: str) -> str:
    """Removes reasoning <think>...</think> tags and unclosed thinking blocks from AI responses."""
    if not text:
        return ""
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>[\s\S]*', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'</think>', '', cleaned)
    return cleaned.strip()

def _err500(e: Exception, context: str = "") -> tuple:
    """log full exception แต่ส่ง generic message ให้ user เท่านั้น"""
    logger.error(f"[{context or 'Line'}] {type(e).__name__}: {e}", exc_info=True)
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง"}), 500

line_bp = Blueprint('line', __name__)

_line_batch_timer = {}
_typing_status = {}
_limit_warn_cache = {}
LINE_FOLDER_CACHE = {}
LINE_CONFIG_FILE = "line_config.json"

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


def send_line_push_notification(target_username, title, text, fields=None, flex_bubble=None):
    """Sends a one-to-one message to a specific user via LINE."""
    line_id = database.get_line_id_by_username(target_username)
    if not line_id:
        logger.info(f"ℹ️ [LINE Push] Target user '{target_username}' has no linked LINE ID. Skipping.")
        return
    
    token = get_channel_access_token()
    if not token:
        logger.warning(f"⚠️ [LINE Push] Missing Channel Access Token for '{target_username}'.")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    if flex_bubble:
        msg = {"type": "flex", "altText": f"แจ้งเตือน: {title}", "contents": clean_flex_payload(flex_bubble)}
    elif fields:
        flex_contents = create_line_flex_bubble(title, "การแจ้งเตือนส่วนตัว", fields, color="#E67E22")
        msg = {"type": "flex", "altText": f"แจ้งเตือน: {title}", "contents": flex_contents}
    else:
        msg = {"type": "text", "text": f"🔔 {title}\n{text}"}
        
    try:
        res = requests.post(url, headers=headers, json={"to": line_id, "messages": [msg]}, timeout=10)
        if res.status_code == 200:
            logger.info(f"✅ [LINE Push] Sent to '{target_username}' ({line_id}) successfully.")
        else:
            logger.error(f"❌ [LINE Push Failed] HTTP {res.status_code}: {res.text}")
    except Exception as e:
        logger.error(f"❌ [LINE Push Error]: {e}")


def get_line_config(org_id: int = None):
    # Check org-specific credentials first if org_id is provided
    if org_id:
        try:
            org_cfg = database.get_org_line_config(org_id)
            if org_cfg and org_cfg.get("channel_access_token") and org_cfg.get("is_active"):
                return {
                    "channel_access_token": (org_cfg.get("channel_access_token") or "").strip(),
                    "channel_secret": (org_cfg.get("channel_secret") or "").strip(),
                    "bot_basic_id": (org_cfg.get("bot_basic_id") or "").strip(),
                    "greeting_message": "สวัสดีค่ะ! ยินดีต้อนรับสู่บริการของเรา มีอะไรให้น้องพั้นช่วยไหมคะ?",
                    "ai_auto_responder_enabled": False,
                    "is_custom_org": True
                }
        except Exception:
            pass

    if os.path.exists(LINE_CONFIG_FILE):
        try:
            with open(LINE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                if cfg.get("channel_access_token"):
                    return cfg
        except Exception:
            pass
    db_cfg = database.get_line_config(org_id)
    return {
        "channel_access_token": db_cfg.get("channel_access_token") or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""),
        "channel_secret": db_cfg.get("channel_secret") or os.environ.get("LINE_CHANNEL_SECRET", ""),
        "bot_basic_id": db_cfg.get("bot_basic_id") or os.environ.get("LINE_BOT_BASIC_ID", "@905gsngi"),
        "greeting_message": "สวัสดีค่ะ! ยินดีต้อนรับสู่บริการของเรา มีอะไรให้น้องพั้นช่วยไหมคะ?",
        "ai_auto_responder_enabled": False
    }


def get_channel_access_token(org_id: int = None):
    """Helper to resolve the LINE Channel Access Token, prioritizing DB/UI settings over env."""
    token = (get_line_config(org_id).get("channel_access_token") or "").strip()
    if not token:
        token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    return token


def save_line_config(config):
    with open(LINE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    # ไม่ mutate os.environ — ทุก worker อ่านค่าจาก get_line_config() โดยตรง


def get_line_sender_name(group_id, sender_id):
    """Fetch user display name from LINE API using group context or user context."""
    if not sender_id or sender_id == "unknown":
        return "-"
    token = get_channel_access_token()
    if not token:
        return "-"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Try fetching from group member profile
    if group_id:
        try:
            url = f"https://api.line.me/v2/bot/group/{group_id}/member/{sender_id}"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                return res.json().get("displayName", "-")
        except Exception as e:
            logger.warning(f"Error fetching group member name: {e}")
            
    # 2. Try fetching from standard user profile
    try:
        url = f"https://api.line.me/v2/bot/profile/{sender_id}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json().get("displayName", "-")
    except Exception as e:
        logger.warning(f"Error fetching user profile name: {e}")
        
    return "-"


def show_loading_animation(chat_id, loading_seconds=20):
    """Show LINE loading/typing animation (max 60s)."""
    token = get_channel_access_token()
    if not token or not chat_id:
        return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    try:
        requests.post(
            "https://api.line.me/v2/bot/chat/loading/start",
            headers=headers,
            json={"chatId": chat_id, "loadingSeconds": loading_seconds},
            timeout=5
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to show loading animation: {e}")


def reply_to_line(reply_token, message, quick_reply=None, sticker_data=None):
    """Send a reply message to LINE using the reply token."""
    token = get_channel_access_token()
    if not token or not reply_token:
        logger.warning("⚠️ reply_to_line: missing token or reply_token")
        return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    if isinstance(message, dict) and "type" in message:
        messages = [dict(message)]
    elif isinstance(message, list):
        messages = list(message)
    else:
        messages = [{"type": "text", "text": str(message)}]

    if sticker_data:
        messages.append({"type": "sticker", "packageId": sticker_data["packageId"], "stickerId": sticker_data["stickerId"]})

    if quick_reply and messages:
        messages[-1] = dict(messages[-1])
        messages[-1]["quickReply"] = quick_reply
    try:
        res = requests.post(
            "https://api.line.me/v2/bot/message/reply",
            headers=headers,
            json={"replyToken": reply_token, "messages": messages},
            timeout=10
        )
        if res.status_code != 200:
            logger.error(f"❌ reply_to_line failed: {res.status_code} {res.text}")
    except Exception as e:
        logger.error(f"❌ reply_to_line exception: {e}")


def broadcast_line_announcement(title, text, fields=None, org_id=None):
    """Sends a push notification to all linked users and linked LINE groups via Flex Message."""
    token = get_channel_access_token()
    if not token: return False
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    if fields:
        flex_contents = create_line_flex_bubble(title, "📢 กำหนดการสาธารณะใหม่", fields, color="#2563eb")
        msg_payload = {"type": "flex", "altText": f"📅 {title}", "contents": flex_contents}
    else:
        msg_payload = {
            "type": "flex",
            "altText": title,
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box", "layout": "vertical", "contents": [
                        { "type": "text", "text": f"📢 {title}", "size": "sm", "color": "#2563eb", "weight": "bold" },
                        { "type": "text", "text": text, "wrap": True, "margin": "md", "size": "sm", "lineSpacing": "6px", "color": "#334155" }
                    ]
                },
                "footer": {
                    "type": "box", "layout": "vertical", "contents": [
                        { "type": "text", "text": "เปิดแอปเพื่อดูรายละเอียดเพิ่มเติม", "size": "xxs", "color": "#94a3b8", "align": "center" }
                    ]
                }
            }
        }
        
    # 1. Send ONLY to users who have linked their LINE account to the system
    try:
        linked_uids = database.get_linked_line_users_for_org(org_id)
        if linked_uids:
            # LINE Multicast supports up to 500 user IDs per request
            multicast_url = "https://api.line.me/v2/bot/message/multicast"
            batch_size = 500
            for i in range(0, len(linked_uids), batch_size):
                batch = linked_uids[i:i + batch_size]
                try:
                    res = requests.post(multicast_url, headers=headers, json={"to": batch, "messages": [msg_payload]}, timeout=20)
                    if res.status_code == 200:
                        logger.info(f"✅ [LINE Targeted Multicast] Sent successfully to {len(batch)} linked users.")
                    else:
                        logger.warning(f"⚠️ [LINE Targeted Multicast] Failed (HTTP {res.status_code}): {res.text}")
                except Exception as me:
                    logger.error(f"❌ [LINE Targeted Multicast] Exception: {me}")
        else:
            logger.info("ℹ️ [LINE Announcement] No linked LINE users found to notify for this organization.")
    except Exception as e:
        logger.error(f"❌ [LINE Linked Users Notification] Exception: {e}")

    # 2. Push to linked LINE Groups for the organization
    try:
        target_org = org_id
        if target_org:
            groups = database.get_line_groups_for_org(target_org, only_enabled=True) or []
            for g in groups:
                gid = g.get("group_id") if isinstance(g, dict) else g
                if gid:
                    try:
                        requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json={"to": gid, "messages": [msg_payload]}, timeout=10)
                    except Exception as ge:
                        logger.error(f"❌ [LINE Group Push] Exception for {gid}: {ge}")
    except Exception as e:
        logger.error(f"❌ [LINE Group Push] Error fetching groups: {e}")

    return True


def push_to_org_line_groups(org_id, title, subtitle="", fields=None, color="#2563eb"):
    """Sends a push Flex Message notification directly to all LINE groups mapped to an organization."""
    if not org_id:
        return False
    token = get_channel_access_token()
    if not token:
        return False
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    if fields and isinstance(fields, dict):
        flex_contents = create_line_flex_bubble(title, subtitle or "📢 แจ้งเตือนจากระบบ", fields, color=color)
        msg_payload = {"type": "flex", "altText": f"📅 {title}", "contents": flex_contents}
    else:
        msg_payload = {
            "type": "flex",
            "altText": title,
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box", "layout": "vertical", "contents": [
                        { "type": "text", "text": f"📅 {title}", "size": "sm", "color": color, "weight": "bold" },
                        { "type": "text", "text": str(subtitle), "wrap": True, "margin": "md", "size": "sm", "lineSpacing": "6px", "color": "#334155" }
                    ]
                },
                "footer": {
                    "type": "box", "layout": "vertical", "contents": [
                        { "type": "text", "text": "📌 OrgChat — ปฏิทินและกำหนดการองค์กร", "size": "xxs", "color": "#94a3b8", "align": "center" }
                    ]
                }
            }
        }
        
    try:
        groups = database.get_line_groups_for_org(org_id) or []
        sent_count = 0
        for g in groups:
            gid = g.get("group_id") if isinstance(g, dict) else g
            if gid:
                try:
                    res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json={"to": gid, "messages": [msg_payload]}, timeout=10)
                    if res.status_code == 200:
                        sent_count += 1
                        logger.info(f"✅ [LINE Org Group Push] Sent notification to group {gid}")
                    else:
                        logger.warning(f"⚠️ [LINE Org Group Push] Group {gid} returned {res.status_code}: {res.text}")
                except Exception as ge:
                    logger.error(f"❌ [LINE Org Group Push] Exception for group {gid}: {ge}")
        return sent_count > 0
    except Exception as e:
        logger.error(f"❌ [LINE Org Group Push] Error fetching groups for org {org_id}: {e}")
        return False


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


def send_meeting_reminder_line(schedule, minutes_before=30):
    """Sends meeting reminder to linked LINE groups and/or specific user."""
    token = get_channel_access_token()
    if not token:
        return False

    bubble = create_meeting_reminder_flex_bubble(schedule, minutes_before=minutes_before)
    msg = {
        "type": "flex",
        "altText": f"⏰ แจ้งเตือนนัดหมาย: {schedule.get('title')}",
        "contents": bubble
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    sent = False

    org_id = schedule.get("organization_id") or 1

    # 1. Send to linked LINE groups for this organization
    groups = database.get_line_groups_for_org(org_id) or []
    for g in groups:
        gid = g.get("group_id") if isinstance(g, dict) else g
        if gid:
            try:
                r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json={"to": gid, "messages": [msg]}, timeout=10)
                if r.status_code == 200:
                    sent = True
            except Exception as e:
                logger.error(f"[send_meeting_reminder_line] group push error: {e}")

    # 2. If target user has LINE user ID
    line_uid = schedule.get("line_user_id")
    if line_uid:
        try:
            r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json={"to": line_uid, "messages": [msg]}, timeout=10)
            if r.status_code == 200:
                sent = True
        except Exception as e:
            logger.error(f"[send_meeting_reminder_line] user push error: {e}")

    return sent


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


def check_line_user_permission(user_id, permission_required, reply_token, group_id=None):
    """
    Check if user is linked to an account and has the required permission.
    Returns: (is_allowed, username)
    """
    username = database.get_username_by_line_id(user_id)
    if not username:
        if group_id:
            msg = "⚠️ ขออภัยค่ะพี่ บัญชี LINE ของพี่จำเป็นต้องเชื่อมต่อกับระบบ OrgChat AI ก่อน เพื่อความปลอดภัยในการขอรายงานหรือเข้าถึงข้อมูลนะคะ\n\n👉 กรุณาทักแชทส่วนตัวหาน้องพั้นและพิมพ์คำว่า 'ผูกบัญชี' เพื่อเชื่อมต่อระบบค่ะ"
        else:
            msg = "⚠️ ขออภัยค่ะพี่ บัญชี LINE ของพี่จำเป็นต้องเชื่อมต่อกับระบบ OrgChat AI ก่อน เพื่อความปลอดภัยในการขอรายงานหรือเข้าถึงข้อมูลนะคะ\n\n👉 พิมพ์คำว่า 'ผูกบัญชี' ด้านล่างเพื่อเชื่อมต่อระบบได้ทันทีเลยค่ะ"
        reply_to_line(reply_token, msg)
        return False, None

    perms_str = database.get_line_permissions(username)
    perms = [p.strip() for p in perms_str.split(",") if p.strip()]
    if permission_required not in perms:
        msg = f"⚠️ ขออภัยค่ะพี่ บัญชีของพี่ไม่มีสิทธิ์ในการใช้งานฟีเจอร์ '{permission_required}' ผ่าน LINE ค่ะ กรุณาติดต่อ Admin เพื่อเปิดสิทธิ์ให้นะคะ"
        reply_to_line(reply_token, msg)
        return False, username

    return True, username


_PROCESSED_WEBHOOK_EVENTS = {}
_PROCESSED_WEBHOOK_LOCK = threading.Lock()


def _is_duplicate_webhook_event(event_data: dict) -> bool:
    """Checks and records webhook event IDs to prevent duplicate execution on LINE retries."""
    if not isinstance(event_data, dict):
        return False
    event_id = event_data.get("webhookEventId")
    if not event_id and event_data.get("type") == "message":
        event_id = event_data.get("message", {}).get("id")
    if not event_id:
        return False

    now = time.time()
    with _PROCESSED_WEBHOOK_LOCK:
        # Prune entries older than 120 seconds
        stale_keys = [k for k, ts in _PROCESSED_WEBHOOK_EVENTS.items() if now - ts > 120]
        for k in stale_keys:
            _PROCESSED_WEBHOOK_EVENTS.pop(k, None)

        if event_id in _PROCESSED_WEBHOOK_EVENTS:
            return True
        _PROCESSED_WEBHOOK_EVENTS[event_id] = now
        return False


def process_line_event(event_data):
    """Main event dispatcher for LINE Webhook"""
    try:
        reply_token = event_data.get("replyToken")
        source_obj = event_data.get("source", {})
        user_id = source_obj.get("userId", "unknown")
        group_id = source_obj.get("groupId") if source_obj.get("type") == "group" else None
        dest_id = group_id if group_id else user_id
        
        # Enforce context right at the start of handling line event!
        _org_id = get_line_org_id(user_id, group_id)
        if _org_id is None:
            _org_id = 1
            
        _upload_org_id = _org_id
            
        owner_username = None
        bot_enabled = True
        
        if group_id:
            # Check bot_enabled status for group
            mapping = database.get_group_mapping(group_id)
            if mapping:
                owner_username = mapping.get("owner_username")
                bot_enabled = bool(mapping.get("bot_enabled", 1))
            
        if owner_username:
            username = owner_username
        else:
            username = database.get_username_by_line_id(user_id)
            
        google_manager.set_context(username=username, org_id=_org_id)
        
        # 1. Text message
        if event_data.get('type') == 'message' and event_data['message'].get('type') == 'text':
            user_text = event_data['message'].get('text', '')
            
            # If bot is disabled in this group, ONLY allow /groupid
            text_lower = user_text.lower().strip()
            if not bot_enabled and not any(k in text_lower for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
                return "OK", 200
            
            # Check if this is an edit response
            session_data = RedisManager.get_active_edit_session(user_id)
            if session_data:
                RedisManager.clear_active_edit_session(user_id)
                # Check if session expired (e.g., > 10 minutes)
                if time.time() - session_data.get("timestamp", 0) > 600:
                    reply_to_line(reply_token, "หมดเวลาการแก้ไขแล้วค่ะพี่ รบกวนกดปุ่มแก้ไขจากรูปอีกครั้งนะคะ")
                    return "OK", 200
                
                # Apply edit
                sheet = session_data["sheet"]
                row = session_data["row"]
                field = session_data["field"]
                ok, err = google_manager.update_expense(sheet, row, field, user_text)
                if ok:
                    reply_to_line(reply_token, f"แก้ไขเรียบร้อยค่ะ:\n{session_data['display']} = '{user_text}'")
                else:
                    reply_to_line(reply_token, f"เกิดข้อผิดพลาด: {err}")
                return "OK", 200

            process_line_command(user_text, user_id, reply_token, group_id=group_id)
            return

        # 1.5 Handler for LOCATION (Time Attendance & GPS Clock-in)
        if event_data.get('type') == 'message' and event_data.get('message', {}).get('type') == 'location':
            loc_msg = event_data['message']
            try:
                lat = float(loc_msg.get('latitude', 0.0))
                lng = float(loc_msg.get('longitude', 0.0))
            except (ValueError, TypeError):
                lat, lng = 0.0, 0.0
            address = loc_msg.get('address') or loc_msg.get('title') or "พิกัด GPS"

            sender_username = database.get_username_by_line_id(user_id)
            if not sender_username:
                reply_to_line(reply_token, "⚠️ บัญชี LINE นี้ยังไม่ได้ผูกกับระบบ OrgChat AI ค่ะ กรุณากดลิงก์ผูกบัญชีก่อนลงเวลานะคะ")
                return "OK", 200

            # Compute office distance (Haversine formula)
            import math
            office_lat = float(os.getenv("OFFICE_LATITUDE", "13.7563"))
            office_lng = float(os.getenv("OFFICE_LONGITUDE", "100.5018"))
            office_radius = float(os.getenv("OFFICE_RADIUS_METERS", "1000"))  # 1 km geofence radius

            R = 6371000.0  # Earth radius in meters
            dlat = math.radians(lat - office_lat)
            dlng = math.radians(lng - office_lng)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(office_lat)) * math.cos(math.radians(lat)) * math.sin(dlng / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = round(R * c, 1)

            # Check today's records
            today_records = database.get_today_attendance(sender_username, org_id=_org_id)
            now_dt = datetime.now()
            time_str = now_dt.strftime("%H:%M")

            check_in_rec = next((r for r in today_records if r.get("check_type") == "check_in"), None)
            check_out_rec = next((r for r in reversed(today_records) if r.get("check_type") == "check_out"), None)

            if not check_in_rec:
                check_type = "check_in"
                check_type_th = "เข้างาน (Check-in)"
                work_start_h = int(os.getenv("WORK_START_HOUR", "9"))
                work_start_m = int(os.getenv("WORK_START_MINUTE", "15"))
                is_late = (now_dt.hour > work_start_h) or (now_dt.hour == work_start_h and now_dt.minute > work_start_m)
                if distance > office_radius:
                    status = "outside_geofence"
                    status_badge = "นอกพื้นที่ ⚠️"
                    status_color = "#EA580C"
                elif is_late:
                    status = "late"
                    status_badge = "เข้างานสาย ⚠️"
                    status_color = "#E11D48"
                else:
                    status = "on_time"
                    status_badge = "เข้างานตรงเวลา ✅"
                    status_color = "#16A34A"

                database.record_attendance(
                    username=sender_username,
                    org_id=_org_id,
                    check_type=check_type,
                    latitude=lat,
                    longitude=lng,
                    address=address,
                    distance_meters=distance,
                    status=status
                )
            else:
                # User already checked in today
                in_time_str = check_in_rec.get("check_time", "00:00:00")
                try:
                    in_time_parts = [int(p) for p in in_time_str.split(":")[:3]]
                    in_dt = now_dt.replace(hour=in_time_parts[0], minute=in_time_parts[1], second=in_time_parts[2] if len(in_time_parts) > 2 else 0)
                    elapsed_from_in = (now_dt - in_dt).total_seconds()
                except Exception:
                    elapsed_from_in = 9999

                # Guard against rapid double-tap / retry within 2 minutes (120 seconds) of check-in
                if not check_out_rec and elapsed_from_in < 120:
                    reply_to_line(reply_token, f"📍 คุณได้บันทึกเวลาเข้างานไปแล้วเมื่อ {in_time_str[:5]} น. ค่ะ\n(ระบบป้องกันการบันทึกเวลาเลิกงานซ้ำซ้อนภายใน 2 นาทีหลังเข้างาน)")
                    return "OK", 200

                check_type = "check_out"
                check_type_th = "เลิกงาน (Check-out)"
                if distance > office_radius:
                    status = "outside_geofence"
                    status_badge = "นอกพื้นที่ (เลิกงาน) ⚠️"
                    status_color = "#EA580C"
                else:
                    status = "on_time"
                    status_badge = "บันทึกเวลาเลิกงานเรียบร้อย ✅"
                    status_color = "#2563EB"

                if check_out_rec:
                    out_time_str = check_out_rec.get("check_time", "00:00:00")
                    try:
                        out_time_parts = [int(p) for p in out_time_str.split(":")[:3]]
                        out_dt = now_dt.replace(hour=out_time_parts[0], minute=out_time_parts[1], second=out_time_parts[2] if len(out_time_parts) > 2 else 0)
                        elapsed_from_out = (now_dt - out_dt).total_seconds()
                    except Exception:
                        elapsed_from_out = 9999

                    if elapsed_from_out < 120:
                        reply_to_line(reply_token, f"📍 คุณได้บันทึกเวลาเลิกงานไปแล้วเมื่อ {out_time_str[:5]} น. ค่ะ\n(หากต้องการอัปเดตเวลาเลิกงานใหม่ กรุณารอ 2 นาที)")
                        return "OK", 200

                    database.update_attendance_checkout(
                        attendance_id=check_out_rec["id"],
                        check_time=now_dt.strftime("%H:%M:%S"),
                        latitude=lat,
                        longitude=lng,
                        address=address,
                        distance_meters=distance,
                        status=status
                    )
                    status_badge = "อัปเดตเวลาเลิกงานล่าสุด ✅"
                else:
                    database.record_attendance(
                        username=sender_username,
                        org_id=_org_id,
                        check_type=check_type,
                        latitude=lat,
                        longitude=lng,
                        address=address,
                        distance_meters=distance,
                        status=status
                    )


            flex_card = {
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#0F172A",
                    "paddingAll": "20px",
                    "contents": [
                        {"type": "text", "text": "TIME ATTENDANCE", "color": "#94A3B8", "weight": "bold", "size": "xs"},
                        {"type": "text", "text": f"บันทึกเวลา{check_type_th}", "color": "#FFFFFF", "weight": "bold", "size": "lg", "margin": "xs"}
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
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {"type": "text", "text": "พนักงาน", "color": "#64748B", "size": "xs", "flex": 3},
                                        {"type": "text", "text": str(sender_username), "color": "#0F172A", "size": "xs", "weight": "bold", "flex": 7}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {"type": "text", "text": "เวลาบันทึก", "color": "#64748B", "size": "xs", "flex": 3},
                                        {"type": "text", "text": f"{now_dt.strftime('%d/%m/%Y')} เวลา {time_str} น.", "color": "#0F172A", "size": "xs", "weight": "bold", "flex": 7}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {"type": "text", "text": "สถานะ", "color": "#64748B", "size": "xs", "flex": 3},
                                        {"type": "text", "text": status_badge, "color": status_color, "size": "xs", "weight": "bold", "flex": 7}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {"type": "text", "text": "ระยะห่างออฟฟิศ", "color": "#64748B", "size": "xs", "flex": 3},
                                        {"type": "text", "text": f"{distance:,.1f} เมตร", "color": "#334155", "size": "xs", "flex": 7}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {"type": "text", "text": "สถานที่", "color": "#64748B", "size": "xs", "flex": 3},
                                        {"type": "text", "text": str(address)[:40], "color": "#64748B", "size": "xxs", "wrap": True, "flex": 7}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }

            reply_to_line(reply_token, {
                "type": "flex",
                "altText": f"⏰ บันทึกเวลา{check_type_th}: {status_badge}",
                "contents": flex_card
            })
            return "OK", 200

        # 2. Handler for IMAGE/FILE/VIDEO/AUDIO (Google Drive)
        msg_type = event_data.get('message', {}).get('type')
        msg_obj = event_data.get('message', {})
        if event_data.get('type') == 'message' and msg_type in ["image", "file", "video", "audio"]:
            if not bot_enabled:
                return "OK", 200
                
            # Check linking and reconcile permission for file upload
            is_ok, sender_username = check_line_user_permission(user_id, "reconcile", reply_token, group_id)
            if not is_ok:
                return "OK", 200
                
            message_id = msg_obj.get("id")
            logger.info(f"Received media {msg_type} (ID: {message_id}) from {user_id} in {dest_id}")
            
            # Show typing/loading animation in LINE instantly
            show_loading_animation(dest_id, loading_seconds=15)
            
            # --- 🛑 Pre-check Billing Limit BEFORE downloading or processing ---
            _org_id = get_line_org_id(user_id, group_id)
            if _org_id:
                _ok, _used, _limit = billing.check_usage_allowed(_org_id, "expense_count")
                if not _ok:
                    now = time.time()
                    cache_key = f"limit_warn_{_org_id}_{user_id}"
                    if now - _limit_warn_cache.get(cache_key, 0) > 10:
                        _limit_warn_cache[cache_key] = now
                        msg = f"❌ ใช้โควต้าบันทึกบิลครบ {_limit} รายการในเดือนนี้แล้วค่ะ\nหากต้องการเพิ่มจำนวน กรุณาอัปเกรดแพ็กเกจนะคะ"
                        reply_to_line(reply_token, msg)
                    return "OK", 200

            # --- 🚀 Per-User Batching: แยกตะกร้าคิวเป็นของแต่ละคน ไม่ปนกันในห้องแชท ---
            batch_key = f"{dest_id}_{user_id}"
            
            if batch_key not in _line_batch_timer:
                _line_batch_timer[batch_key] = {"files": [], "timer": None}
            
            # Store specific metadata for each file in the batch, tracking individual sender
            _line_batch_timer[batch_key]["files"].append({
                "message_id": message_id, 
                "msg_type": msg_type,
                "file_name": msg_obj.get("fileName"),
                "sender_id": user_id
            })
            
            if _line_batch_timer[batch_key]["timer"]:
                _line_batch_timer[batch_key]["timer"].cancel()
                
            def handle_upload_background(b_key, did, uid, reply_tok):
                batch_data = _line_batch_timer.pop(b_key, {})
                batch = batch_data.get("files", [])
                if not batch: return
                
                token = get_channel_access_token()
                pending_for_dest = []
                
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                def _download_file(file_item):
                    f_id = file_item["message_id"]
                    f_type = file_item["msg_type"]
                    s_id = file_item.get("sender_id", "unknown")
                    try:
                        res = requests.get(f"https://api-data.line.me/v2/bot/message/{f_id}/content", 
                                           headers={"Authorization": f"Bearer {token}"}, timeout=60)
                        if res.status_code == 200:
                            original_name = file_item.get("file_name") or f"line_upload_{f_id}"
                            mimetype = "application/octet-stream"
                            if f_type == "image": mimetype = "image/jpeg"
                            elif f_type == "video": mimetype = "video/mp4"
                            elif f_type == "audio": mimetype = "audio/x-m4a"
                            elif f_type == "file" and original_name.lower().endswith(".pdf"):
                                mimetype = "application/pdf"
                            
                            return {
                                "content": res.content,
                                "mimetype": mimetype,
                                "name": original_name,
                                "type": f_type,
                                "msg_id": f_id,
                                "sender_id": s_id
                            }
                    except Exception as e:
                        logger.error(f"❌ Failed to fetch media {f_id}: {e}")
                    return None

                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(_download_file, item) for item in batch]
                    for future in as_completed(futures):
                        res = future.result()
                        if res:
                            pending_for_dest.append(res)

                if pending_for_dest:
                    # Generate unique session ID per upload batch to prevent overwrites
                    pending_id = f"pending_{uuid.uuid4().hex}"
                    RedisManager.set_pending_files(pending_id, pending_for_dest)
                    
                    # Check for folder bypass (if group mapped with default folder)
                    mapping = database.get_group_mapping(did) if did.startswith("C") else None
                    if mapping and mapping.get("default_folder_id"):
                        f_id = mapping.get("default_folder_id")
                        f_name = mapping.get("default_folder_name") or "ใบเสร็จ/ใบกำกับภาษี"
                        logger.info(f"Bypassing folder selection for group {did}. Uploading to: {f_name} ({f_id})")
                        show_loading_animation(did)
                        try:
                            from tasks.upload_tasks import process_pending_uploads_task
                            process_pending_uploads_task.delay(pending_id, did, f_id, f_name, reply_tok)
                        except Exception as _celery_err:
                            logger.info(f"Celery/Redis unavailable ({_celery_err}). Running upload process synchronously in background thread.")
                            files = RedisManager.pop_pending_files(pending_id)
                            if files:
                                threading.Thread(
                                    target=_process_pending_uploads_inner,
                                    args=(pending_id, did, f_id, f_name, reply_tok, files, _upload_org_id)
                                ).start()
                    else:
                        folder_flex = get_folder_flex_message(did, uploader_id=uid, pending_id=pending_id)
                        drive_error = isinstance(folder_flex, dict) and folder_flex.pop("_drive_unavailable", False)

                        sender_name = get_line_sender_name(did if did.startswith("C") else None, uid)
                        name_prefix = f"พี่ {sender_name} คะ " if sender_name and sender_name != "Unknown" else "พี่คะ "

                        if drive_error:
                            if len(pending_for_dest) == 1:
                                f_name = pending_for_dest[0]['name']
                                msg = f"📥 {name_prefix}น้องพั้นได้รับไฟล์ '{f_name}' แล้วนะคะ\nแต่ยังอัปโหลดไม่ได้เพราะ Drive มีปัญหาค่ะ:"
                            else:
                                msg = f"📥 {name_prefix}น้องพั้นได้รับไฟล์ {len(pending_for_dest)} รายการแล้วนะคะ\nแต่ยังอัปโหลดไม่ได้เพราะ Drive มีปัญหาค่ะ:"
                        else:
                            if len(pending_for_dest) == 1:
                                f_name = pending_for_dest[0]['name']
                                msg = f"📥 {name_prefix}น้องพั้นได้รับไฟล์ '{f_name}' แล้วนะคะ\nกำลังอัปโหลดให้อยู่ค่ะ~ เลือกโฟลเดอร์ที่จะเก็บด้วยนะคะ:"
                            else:
                                msg = f"📥 {name_prefix}น้องพั้นได้รับไฟล์ {len(pending_for_dest)} รายการแล้วนะคะ\nกำลังอัปโหลดให้อยู่ค่ะ~ เลือกโฟลเดอร์ที่จะเก็บด้วยนะคะ:"

                        if folder_flex:
                            reply_to_line(reply_tok, [{"type": "text", "text": msg}, folder_flex])
                        else:
                            reply_to_line(reply_tok, msg)
                else:
                    reply_to_line(reply_tok, "❌ น้องพั้นดึงข้อมูลไฟล์ไม่สำเร็จค่ะ")

            try:
                timer = threading.Timer(1.8, handle_upload_background, args=(batch_key, dest_id, user_id, reply_token))
                _line_batch_timer[batch_key]["timer"] = timer
                timer.start()
            except Exception:
                _line_batch_timer.pop(batch_key, None)
                raise
            return

        # 3. Handler for bot joining a group
        if event_data.get('type') == 'join':
            g_id = source_obj.get("groupId")
            if g_id:
                flex_welcome = {
                    "type": "flex",
                    "altText": "น้องพั้นยินดีต้อนรับค่ะ 💖",
                    "contents": {
                        "type": "bubble",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#6366f1",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🎉 ยินดีต้อนรับ",
                                    "weight": "bold",
                                    "size": "xl",
                                    "color": "#ffffff"
                                }
                            ]
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "น้องพั้นพร้อมช่วยวิเคราะห์และจัดเก็บเอกสารอัตโนมัติให้กลุ่มนี้แล้วค่ะ!",
                                    "wrap": True,
                                    "size": "sm",
                                    "color": "#666666"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "lg",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "box",
                                            "layout": "baseline",
                                            "spacing": "sm",
                                            "contents": [
                                                {"type": "text", "text": "📌", "size": "sm", "flex": 1},
                                                {"type": "text", "text": "รหัสกลุ่ม (Group ID) ของคุณคือ:", "wrap": True, "size": "sm", "color": "#111111", "weight": "bold", "flex": 9}
                                            ]
                                        },
                                        {
                                            "type": "text",
                                            "text": g_id,
                                            "wrap": True,
                                            "size": "xs",
                                            "color": "#ec4899",
                                            "margin": "md",
                                            "align": "center",
                                            "weight": "bold"
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "color": "#6366f1",
                                    "action": {
                                        "type": "uri",
                                        "label": "ไปตั้งค่า Web Portal",
                                        "uri": "https://openchat.sbs/dashboard"
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "secondary",
                                    "action": {
                                        "type": "message",
                                        "label": "ดูรหัสกลุ่ม",
                                        "text": "รหัสกลุ่ม"
                                    }
                                }
                            ]
                        }
                    }
                }
                reply_to_line(reply_token, flex_welcome)
            return

        # 4. Handler for POSTBACK
        if event_data.get('type') == 'postback':
            data = event_data.get('postback', {}).get('data', '')
            parsed = dict(urllib.parse.parse_qsl(data))
            
            action = parsed.get('action')
            perm_needed = None
            if action == 'set_folder':
                perm_needed = 'folder'
            elif action in ['edit_prompt', 'move_row_sheet', 'choose_new_sheet']:
                perm_needed = 'reconcile'
                
            if perm_needed:
                is_ok, _ = check_line_user_permission(user_id, perm_needed, reply_token, group_id)
                if not is_ok:
                    return "OK", 200
                    
            if parsed.get('action') == 'set_folder':
                f_id = parsed.get('id')
                f_name = parsed.get('name')
                if f_id:
                    LINE_FOLDER_CACHE[dest_id] = f_id
                    
                    uploader_id = parsed.get('uploader_id')
                    target_user = uploader_id if uploader_id else user_id
                    batch_key = f"{dest_id}_{target_user}"
                    # Use pending_id from postback if available, fallback to batch_key for old buttons
                    pending_id = parsed.get('pending_id') or batch_key
                    # Process pending files immediately after folder selection
                    if RedisManager.try_claim_upload(pending_id):
                        show_loading_animation(dest_id)
                        try:
                            from tasks.upload_tasks import process_pending_uploads_task
                            process_pending_uploads_task.delay(pending_id, dest_id, f_id, f_name, reply_token)
                        except Exception as _celery_err:
                            logger.info(f"Celery/Redis unavailable ({_celery_err}). Running upload process synchronously in background thread.")
                            files = RedisManager.pop_pending_files(pending_id)
                            if files:
                                threading.Thread(
                                    target=_process_pending_uploads_inner,
                                    args=(pending_id, dest_id, f_id, f_name, reply_token, files, _upload_org_id)
                                ).start()
                            else:
                                RedisManager.release_upload_lock(pending_id)
                    else:
                        if RedisManager.get_json(f"upload_lock:{pending_id}"):
                            reply_to_line(reply_token, "น้องพั้นกำลังประมวลผลไฟล์ให้อยู่ค่ะ กรุณารอสักครู่นะคะ")
                        else:
                            reply_to_line(reply_token, "ปุ่มนี้หมดอายุแล้วค่ะ ส่งรูปใหม่ให้พั้นนะคะ", sticker_data={"packageId": "446", "stickerId": "1988"})
            elif parsed.get('action') == 'edit_prompt':
                sheet = parsed.get('sheet')
                row = parsed.get('row')
                
                edit_fields = [
                    {"label": "ยอดเงินสุทธิ", "field": "จำนวนเงินสุทธิ", "display": "ยอดเงินสุทธิ"},
                    {"label": "วันที่ในเอกสาร", "field": "วันที่ในเอกสาร", "display": "วันที่ในเอกสาร"},
                    {"label": "ผู้ส่ง/ร้านค้า", "field": "ผู้ส่ง/ร้านค้า", "display": "ผู้ส่ง/ร้านค้า"},
                    {"label": "เลขที่อ้างอิง", "field": "เลขที่อ้างอิง", "display": "เลขที่อ้างอิง"},
                ]
                if sheet == "บัตรประชาชน":
                    edit_fields = [
                        {"label": "เลขบัตรประชาชน", "field": "เลขบัตรประชาชน", "display": "เลขบัตรประชาชน"},
                        {"label": "ชื่อ (ไทย)", "field": "ชื่อ (ไทย)", "display": "ชื่อ (ไทย)"},
                        {"label": "นามสกุล (ไทย)", "field": "นามสกุล (ไทย)", "display": "นามสกุล (ไทย)"},
                    ]
                
                items = []
                for f in edit_fields:
                    items.append({
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": f["label"][:20],
                            "data": f"action=edit_field&sheet={sheet}&row={row}&field={f['field']}&display={f['display']}",
                            "displayText": f"ฉันต้องการแก้ไข{f['display']}"
                        }
                    })
                
                reply_to_line(reply_token, f"พี่ต้องการแก้ไขข้อมูลในชีต '{sheet}' แถวที่ {row} ส่วนไหนดีคะ? เลือกได้เลยค่ะ:", quick_reply={"items": items})
            elif parsed.get('action') == 'edit_field':
                sheet = parsed.get('sheet')
                row = parsed.get('row')
                field = parsed.get('field')
                display = parsed.get('display')
                
                RedisManager.set_active_edit_session(user_id, {
                    "sheet": sheet,
                    "row": int(row),
                    "field": field,
                    "display": display,
                    "timestamp": time.time()
                })
                reply_to_line(reply_token, f"💬 พี่ต้องการเปลี่ยน '{display}' เป็นค่าอะไรดีคะ?\nพิมพ์ค่าใหม่ส่งกลับมาให้น้องพั้นได้เลยค่ะ พั้นกำลังรออยู่นะคะ 👇")
            elif parsed.get('action') == 'edit_date_picker':
                sheet = parsed.get('sheet')
                row = parsed.get('row')
                params = event_data.get('postback', {}).get('params', {})
                selected_date = params.get('date')
                if selected_date:
                    try:
                        dt = datetime.strptime(selected_date, "%Y-%m-%d")
                        formatted_val = dt.strftime("%d/%m/%Y")
                    except Exception:
                        formatted_val = selected_date
                    
                    date_col = google_manager.get_date_header_name(sheet)
                    ok, err = google_manager.update_expense(sheet, int(row), date_col, formatted_val)
                    if ok:
                        reply_to_line(reply_token, f"✅ แก้ไขวันที่เรียบร้อยแล้วค่ะพี่!\n\n📊 ชีต: '{sheet}' แถวที่ {row}\n📅 เปลี่ยนเป็น: '{formatted_val}'\n\nพั้นอัปเดตและกระทบยอดบัญชีใหม่ให้อัตโนมัติเรียบร้อยค่ะ ✨")
                    else:
                        reply_to_line(reply_token, f"❌ เกิดข้อผิดพลาดในการแก้ไขวันที่: {err}")
                else:
                    reply_to_line(reply_token, "❌ ไม่พบวันที่ที่เลือกค่ะ")
            elif parsed.get('action') == 'choose_new_sheet':
                from_sheet = parsed.get('sheet')
                row = parsed.get('row')
                
                try:
                    spreadsheet = google_manager.sheets_service.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
                    sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', []) if s['properties']['title'] not in ["Sheet1", "ชีต1", "แดชบอร์ด", "Dashboard"]]
                except Exception:
                    sheet_titles = ["สลิปโอนเงิน", "ใบเสร็จ/ใบกำกับภาษี", "ใบเสนอราคา", "ทั่วไป"]
                
                items = []
                for title in sheet_titles:
                    items.append({
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": title[:20],
                            "data": f"action=move_row_sheet&from_sheet={from_sheet}&row={row}&to_sheet={title}",
                            "displayText": f"ย้ายไปยังชีต: {title}"
                        }
                    })
                
                reply_to_line(reply_token, f"พี่ต้องการย้ายรายการค่าใช้จ่ายนี้ (ชีต '{from_sheet}' แถวที่ {row}) ไปยังประเภท/ชีตใดคะ? จิ้มเลือกได้เลยค่ะ:", quick_reply={"items": items})
            elif parsed.get('action') == 'move_row_sheet':
                from_sheet = parsed.get('from_sheet')
                row = parsed.get('row')
                to_sheet = parsed.get('to_sheet')
                
                if from_sheet == to_sheet:
                    reply_to_line(reply_token, f"ℹ️ รายการนี้อยู่ในชีต '{to_sheet}' อยู่แล้วค่ะพี่! 😊")
                else:
                    ok, err = google_manager.move_row_between_sheets(from_sheet, int(row), to_sheet)
                    if ok:
                        reply_to_line(reply_token, f"✅ ย้ายข้อมูลสำเร็จแล้วค่ะพี่!\n\n📂 ย้ายจาก: '{from_sheet}'\n➡️ ไปยังชีตใหม่: '{to_sheet}'\n\nน้องพั้นทำการลบแถวเดิมและย้ายไปต่อชีตใหม่ พร้อมกระทบยอดบัญชีเรียบร้อยค่ะ ✨💖")
            elif parsed.get('action') in ['approve_leave', 'reject_leave']:
                leave_id = parsed.get('id')
                status = "approved" if parsed.get('action') == 'approve_leave' else "rejected"
                
                leave = database.get_leave_request(leave_id)
                if not leave:
                    reply_to_line(reply_token, f"⚠️ ไม่พบข้อมูลคำขอลา #{leave_id} ในระบบค่ะ")
                    return "OK", 200

                approver_username = database.get_username_by_line_id(user_id)
                applicant_user = leave.get("username", "")

                # 🛡️ Safety Rule: Approver cannot approve their own leave request
                if approver_username and applicant_user and applicant_user.lower() == approver_username.lower():
                    reply_to_line(reply_token, "🚫 คุณไม่สามารถอนุมัติใบลาของตัวเองได้ค่ะ ต้องให้หัวหน้างานหรือ Admin ท่านอื่นเป็นผู้อนุมัติ")
                    return "OK", 200

                # Verify approver permission (system admin, org admin, can_manage_leave, or direct manager)
                is_authorized = False
                leave_org_id = leave.get("org_id") or leave.get("organization_id") or _org_id
                if not leave_org_id and applicant_user:
                    applicant_orgs = database.get_user_orgs(applicant_user) or []
                    if applicant_orgs:
                        leave_org_id = applicant_orgs[0]["id"]

                if approver_username:
                    u_setting = database.get_user_setting(approver_username)
                    if u_setting and (u_setting.get("role") in ["admin", "superadmin", "manager"] or u_setting.get("can_manage_leave")):
                        is_authorized = True
                    elif leave_org_id and database.is_org_admin(leave_org_id, approver_username):
                        is_authorized = True
                    elif leave_org_id:
                        members = database.get_org_members(leave_org_id)
                        applicant_member = next((m for m in members if m["username"].lower() == applicant_user.lower()), None)
                        if applicant_member and (applicant_member.get("manager_username") or "").strip().lower() == approver_username.lower():
                            is_authorized = True

                    if not is_authorized and applicant_user:
                        for uo in (database.get_user_orgs(applicant_user) or []):
                            m_list = database.get_org_members(uo["id"])
                            app_m = next((m for m in m_list if m["username"].lower() == applicant_user.lower()), None)
                            if app_m and (app_m.get("manager_username") or "").strip().lower() == approver_username.lower():
                                is_authorized = True
                                break

                if not is_authorized:
                    reply_to_line(reply_token, "⚠️ ขออภัยค่ะ เฉพาะหัวหน้างานโดยตรง, ผู้มีสิทธิ์จัดการวันลา หรือ Admin เท่านั้นที่มีสิทธิ์กดอนุมัติ/ปฏิเสธการลานี้ค่ะ")
                    return "OK", 200

                approver_display = approver_username or "ผู้ดูแลระบบ"
                ok = database.update_leave_status(leave_id, status, approver_display, note="อนุมัติผ่าน LINE")
                if ok:
                    status_text = "อนุมัติ" if status == "approved" else "ปฏิเสธ"
                    status_badge = "อนุมัติแล้ว ✅" if status == "approved" else "ปฏิเสธแล้ว ❌"
                    reply_to_line(reply_token, f"✅ ดำเนินการ{status_text}คำขอลา #{leave_id} เรียบร้อยแล้วค่ะ!")
                    
                    # Push notification to employee
                    if leave:
                        emp_user = leave.get("username")
                        try:
                            threading.Thread(target=send_line_push_notification, args=(
                                emp_user,
                                "🏖️ อัปเดตผลการขออนุมัติการลา",
                                f"คำขอลาของคุณตั้งแต่วันที่ {leave['start_date']} ถึง {leave['end_date']} ได้รับการ{status_text}แล้วค่ะ",
                            ), kwargs={
                                "fields": {
                                    "ผลการพิจารณา": status_badge,
                                    "ผู้อนุมัติ": approver_display,
                                    "ประเภทการลา": leave.get("type", "ทั่วไป"),
                                    "ช่วงวันลา": f"{leave['start_date']} ถึง {leave['end_date']}"
                                }
                            }).start()
                        except Exception as _push_e:
                            logger.error(f"Error sending leave push to employee: {_push_e}")
                else:
                    reply_to_line(reply_token, f"⚠️ ไม่สามารถอัปเดตคำขอลา #{leave_id} ได้ (อาจถูกดำเนินการไปแล้วค่ะ)")

        # 5. Handler for FOLLOW (เพิ่มเพื่อน / Add Friend Event)
        if event_data.get('type') == 'follow':
            import secrets
            import time
            token = secrets.token_urlsafe(32)
            # 🛡️ Persist token in DB for multi-worker and restart safety
            database.line_link_create(token, user_id)
            PENDING_LINE_LINKS[token] = {
                "line_user_id": user_id,
                "timestamp": time.time()
            }
            webhook_url = os.environ.get("ACTIVE_PUBLIC_URL")
            _base_url = ""
            if webhook_url:
                _base_url = webhook_url.split("/api/line/webhook")[0].rstrip('/')
            if not _base_url:
                _base_url = (os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL") or "https://openchat.sbs").rstrip('/')
            
            magic_url = f"{_base_url}/line/link_magic?token={token}"
            onboarding_bubble = create_onboarding_guide_flex_bubble(_base_url, link_magic_url=magic_url)
            reply_to_line(reply_token, {
                "type": "flex",
                "altText": "✨ ยินดีต้อนรับสู่น้องพั้น AI ผู้ช่วยองค์กร",
                "contents": onboarding_bubble
            })
            return "OK", 200

    except Exception as e:
        logger.error(f"Event processing failed: {e}")
    finally:
        google_manager.clear_context()


@safe_thread_target
@db_task_tracker("process_pending_uploads")
def process_pending_uploads(b_key, did, folder_id, folder_name, reply_tok):


    """Processes files that were waiting for folder selection."""
    # Resolve org for billing (group or user)
    _upload_org_id = database.get_org_id_by_line_group(did) if (did.startswith("C") or did.startswith("R")) else database.get_org_id_by_line_user(did)
    if _upload_org_id is None:
        _upload_org_id = 1  # fallback for legacy/single-tenant deployments
    
    files = RedisManager.pop_pending_files(b_key)
    if not files:
        RedisManager.release_upload_lock(b_key)
        return
    try:
        _process_pending_uploads_inner(b_key, did, folder_id, folder_name, reply_tok, files, _upload_org_id)
    finally:
        RedisManager.release_upload_lock(b_key)


def _process_pending_uploads_inner(b_key, did, folder_id, folder_name, reply_tok, files, _upload_org_id):

    # Enforce context for this background thread!
    sender_id = files[0].get("sender_id")
    u_name = database.get_username_by_line_id(sender_id) if sender_id else None
    google_manager.set_context(username=u_name, org_id=_upload_org_id)
    
    # --- 🛑 Pre-check Billing Limit Batch Truncation ---
    _exp_ok, _exp_used, _exp_limit = billing.check_usage_allowed(_upload_org_id, "expense_count")
    uploaded_results = []
    if _exp_limit != -1:
        available = max(0, _exp_limit - _exp_used)
        if len(files) > available:
            rejected_files = files[available:]
            files = files[:available]
            for f in rejected_files:
                uploaded_results.append({"status": "limit_reached", "name": f.get("name", "Unknown"), "limit": _exp_limit})
    
    # Let user know we're working on it — push ONLY (never use reply_tok here).
    if files:
        processing_msg = f"กำลังวิเคราะห์และจัดเก็บ {len(files)} ไฟล์ลง '{folder_name}' ⏳ (อาจใช้เวลาสักครู่)"
        token = get_channel_access_token()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        try:
            requests.post("https://api.line.me/v2/bot/message/push", headers=headers,
                          json={"to": did, "messages": [{"type": "text", "text": processing_msg}]}, timeout=10)
        except Exception:
            pass  # Silently skip processing message if push fails (quota or network error)
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def _process_single_upload(item):
        try:
            original_name = item["name"]
            real_original_name = original_name
            mimetype = item["mimetype"]
            content = item["content"]
            f_type = item["type"]

            # --- Guard: reject empty file content before wasting any API quota ---
            if not content:
                logger.warning(f"⚠️ Empty file content for '{original_name}', skipping.")
                return {"status": "empty_file", "name": original_name}

            # --- 🔍 Scan QR Code for Bank Slips ---
            verification_status = "-"
            qr_decoded = None
            if folder_name == "สลิปโอนเงิน":
                is_valid_slip = False
                try:
                    import cv2
                    import numpy as np
                    nparr = np.frombuffer(content, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is not None:
                        detector = cv2.QRCodeDetector()
                        val_qr, pts, qr_code = detector.detectAndDecode(img)
                        if val_qr:
                            val_qr = val_qr.strip()
                            
                            # Parse with EMVCoParser to handle both PromptPay presented QRs and Thai Mini QRs (slip verification)
                            from tools.emvco_parser import EMVCoParser
                            parser = EMVCoParser()
                            decoded = parser.decode_slip_qr(val_qr)
                            qr_decoded = decoded
                            
                            if val_qr.startswith("000201") and ("A000000677" in val_qr):
                                is_valid_slip = True
                                verification_status = "ผ่าน (คิวอาร์จริง)"
                            elif decoded.get("is_valid_emvco"):
                                raw_tags = decoded.get("raw_tags", {})
                                if "00" in raw_tags:
                                    inner = parser.parse_sub_tlv(raw_tags["00"])
                                    # Standard Thai Mini QR contains application ID "000001" under tag 00 sub-tag 00
                                    if inner.get("00") == "000001":
                                        is_valid_slip = True
                                        verification_status = "ผ่าน (คิวอาร์จริง)"
                            
                            if not is_valid_slip:
                                if val_qr.startswith("https://") or "qr" in val_qr.lower():
                                    is_valid_slip = True
                                    verification_status = "ผ่าน (ลิงก์คิวอาร์)"
                                else:
                                    verification_status = "ไม่ผ่าน (คิวอาร์ไม่ใช่สลิป)"
                        else:
                            verification_status = "ไม่ผ่าน (ไม่มี QR Code)"
                    else:
                        verification_status = "ไม่ผ่าน (อ่านรูปไม่ได้)"
                except Exception as qr_err:
                    logger.error(f"Error scanning QR Code: {qr_err}")
                    verification_status = "ข้อผิดพลาดระบบสแกน"

                if not is_valid_slip:
                    return {
                        "status": "invalid_slip",
                        "name": original_name,
                        "verification_status": verification_status
                    }

            # --- 🛑 Check billing BEFORE Drive upload (don't waste Drive/Sheets quota) ---
            _exp_ok, _exp_used, _exp_limit = billing.check_and_increment(_upload_org_id, "expense_count")
            if not _exp_ok:
                return {"status": "limit_reached", "name": original_name, "limit": _exp_limit}

            # --- 🚀 AI Smart Scan ---
            analysis = None
            if (f_type in ["image", "file"] and mimetype in ["image/jpeg", "application/pdf", "image/png"]) or f_type == "audio":
                try:
                    analysis = ai_providers.analyze_media_contents(content, mimetype)
                    if analysis and analysis.get("smart_name"):
                        ext = os.path.splitext(original_name)[1]
                        original_name = analysis["smart_name"]
                        if not original_name.endswith(ext): original_name += ext
                except Exception as e:
                    import traceback
                    print(f"🚨 CRITICAL: Media analysis failed in app_server: {e}\n{traceback.format_exc()}", flush=True)
                    analysis = None

            sender_id = item.get("sender_id")
            u_name = database.get_username_by_line_id(sender_id) if sender_id else None

            # --- Offline-First: Always save local backup first to prevent any data loss ---
            from tools.offline_storage import save_local_receipt_backup
            rel_backup_path, abs_backup_path, local_backup_url = save_local_receipt_backup(content, original_name)

            # Upload to Google Drive (with graceful offline fallback)
            link, upload_err = google_manager.upload_file(content, original_name, mimetype, folder_id=folder_id, org_id=_upload_org_id, username=u_name)
            is_offline_backup = False
            if not link:
                logger.warning(f"⚠️ Drive upload unavailable for '{original_name}': {upload_err}. Using resilient local backup.")
                link = local_backup_url
                is_offline_backup = True

            # --- 🛠️ Data Sanitization for Google Sheets (Prevent Column Sprouting) ---
            raw_ext = analysis.get("extracted_data", {}) if analysis else {}
            sanitized_ext = raw_ext.copy()
            if "date" not in sanitized_ext or not sanitized_ext["date"]:
                sanitized_ext["date"] = get_bangkok_now().strftime("%d/%m/%Y")
            sanitized_ext["category"] = folder_name
            for field in ["time", "sender", "receiver", "memo", "ref_number"]:
                if field not in sanitized_ext: sanitized_ext[field] = "-"

            # Fallback from QR decoded data (if AI OCR was unavailable or blocked)
            if qr_decoded and isinstance(qr_decoded, dict):
                if qr_decoded.get("transaction_id") and (not sanitized_ext.get("ref_number") or sanitized_ext.get("ref_number") == "-"):
                    sanitized_ext["ref_number"] = qr_decoded["transaction_id"]
                if qr_decoded.get("date") and (not raw_ext.get("date")):
                    sanitized_ext["date"] = qr_decoded["date"]
                if qr_decoded.get("time") and (not sanitized_ext.get("time") or sanitized_ext.get("time") == "-"):
                    sanitized_ext["time"] = qr_decoded["time"]
                if qr_decoded.get("sending_bank_id") and (not sanitized_ext.get("sender_bank") or sanitized_ext.get("sender_bank") == "-"):
                    bank_code = qr_decoded["sending_bank_id"]
                    bank_map = {
                        "002": "ธนาคารกรุงเทพ (BBL)", "004": "ธนาคารกสิกรไทย (KBANK)", "006": "ธนาคารกรุงไทย (KTB)",
                        "011": "ธนาคารทหารไทยธนชาต (TTB)", "014": "ธนาคารไทยพาณิชย์ (SCB)", "025": "ธนาคารกรุงศรีอยุธยา (BAY)",
                        "022": "ธนาคารซีไอเอ็มบีไทย (CIMB)", "024": "ธนาคารยูโอบี (UOB)", "030": "ธนาคารออมสิน (GSB)",
                        "034": "ธ.ก.ส. (BAAC)", "069": "ธนาคารเกียรตินาคินภัทร (KKP)", "073": "ธนาคารแลนด์ แอนด์ เฮ้าส์ (LH Bank)"
                    }
                    sanitized_ext["sender_bank"] = bank_map.get(bank_code, f"ธนาคารรหัส {bank_code}")

            # Robust fallback for amount
            smart_amt = extract_smart_amount(sanitized_ext, analysis=analysis, qr_decoded=qr_decoded)
            if smart_amt is not None and smart_amt > 0:
                sanitized_ext["net_amount"] = smart_amt
                if "total_amount" not in sanitized_ext or not sanitized_ext["total_amount"]:
                    sanitized_ext["total_amount"] = smart_amt
                if analysis and "extracted_data" in analysis:
                    analysis["extracted_data"]["net_amount"] = smart_amt
                    if "total_amount" not in analysis["extracted_data"] or not analysis["extracted_data"]["total_amount"]:
                        analysis["extracted_data"]["total_amount"] = smart_amt

            sender_name = get_line_sender_name(did if (did.startswith("C") or did.startswith("R")) else None, sender_id)

            log_data = {
                "file_link": link,
                "summary": analysis.get("summary", f"Auto-upload: {original_name}") if analysis else f"Auto-upload: {original_name}",
                "original_filename": real_original_name,
                "extracted_data": sanitized_ext,
                "line_sender_name": sender_name,
                "verification_status": verification_status
            }

            if is_offline_backup:
                # Queue for cloud sync when connection/credentials recover
                database.add_offline_upload(
                    org_id=_upload_org_id,
                    username=u_name,
                    user_id=sender_id,
                    original_filename=real_original_name,
                    local_filepath=abs_backup_path,
                    mimetype=mimetype,
                    folder_id=folder_id,
                    folder_name=folder_name,
                    analysis=analysis,
                    extracted_data=sanitized_ext,
                    verification_status=verification_status,
                    line_sender_name=sender_name
                )
                log_res = {"ok": True, "sheet": folder_name, "row": 0}
            else:
                log_res = google_manager.log_expense(log_data, org_id=_upload_org_id, username=u_name)

            # Log to local database for Dashboard stats (regardless of Sheets result)
            try:
                amt = sanitized_ext.get("net_amount", 0)
                if not amt or amt == "-": amt = 0
                try:
                    if isinstance(amt, str):
                        amt = float(amt.replace(',', '').replace('฿', '').strip())
                    else:
                        amt = float(amt)
                except (ValueError, TypeError):
                    amt = 0.0
                database.add_drive_log(
                    filename=real_original_name,
                    category=sanitized_ext.get("category", "General"),
                    amount=amt,
                    doc_date=sanitized_ext.get("date"),
                    summary=analysis.get("summary") if analysis else f"Auto-upload: {real_original_name}",
                    file_link=link,
                    user_id=sender_id,
                    org_id=_upload_org_id,
                    sync_status="pending_cloud_sync" if is_offline_backup else "synced",
                    local_filepath=abs_backup_path
                )
            except Exception as dbe:
                logger.error(f"❌ Database Log Error: {dbe}")

            if log_res and log_res.get("error") == "duplicate":
                return {
                    "status": "duplicate",
                    "name": original_name,
                    "link": link,
                    "analysis": analysis,
                    "verification_status": verification_status,
                    "sheet": log_res.get("sheet"),
                    "row": log_res.get("row"),
                    "ref_number": log_res.get("ref_number"),
                    "is_offline_backup": is_offline_backup
                }

            if not log_res or not log_res.get("ok"):
                logger.warning(f"⚠️ Sheets log failed for '{original_name}' (Drive OK). log_res={log_res}")

            # Return success even if offline (safe local backup preserved)
            return {
                "status": "success",
                "name": original_name,
                "link": link,
                "analysis": analysis,
                "verification_status": verification_status,
                "sheet": log_res.get("sheet") if log_res else (folder_name or "ทั่วไป"),
                "row": log_res.get("row") if log_res else 0,
                "is_offline_backup": is_offline_backup
            }

        except Exception as e:
            logger.error(f"Pending upload failed: {e}", exc_info=True)
            return {"status": "upload_failed", "name": item.get("name", "Unknown"), "error": str(e)}
        
        return {"status": "upload_failed", "name": item.get("name", "Unknown"), "error": "Unknown error in processing"}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_process_single_upload, item) for item in files]
        for future in futures:
            res = future.result()
            if res:
                uploaded_results.append(res)

    # Run reconciliation once after all files are done (not per-file) to avoid burning Sheets API quota
    _has_success = any(r and r.get("status") in ("success", "duplicate") for r in uploaded_results)
    if _has_success:
        def run_reconciliation_async(user, oid):
            try:
                google_manager.set_context(username=user, org_id=oid)
                google_manager.auto_reconcile_internal()
            except Exception as _rec_err:
                logger.warning(f"⚠️ Reconciliation after batch upload failed: {_rec_err}")
            finally:
                google_manager.clear_context()
        
        import threading
        threading.Thread(target=run_reconciliation_async, args=(u_name, _upload_org_id), daemon=True).start()

    _invalid_slips = [r for r in uploaded_results if r and r.get("status") == "invalid_slip"]
    uploaded_results = [r for r in uploaded_results if r and r.get("status") != "invalid_slip"]
    if _invalid_slips:
        _slip_names = ", ".join(r["name"] for r in _invalid_slips)
        _reasons = ", ".join(r.get("verification_status", "ตรวจสอบไม่ผ่าน") for r in _invalid_slips)
        _invalid_msg = (
            f"⚠️ ไม่สามารถบันทึกไฟล์ได้เนื่องจากไม่ใช่สลิปโอนเงินค่ะพี่!\n"
            f"ไฟล์: {_slip_names}\n"
            f"สาเหตุ: {_reasons}\n\n"
            f"👉 รบกวนส่งไฟล์ที่เป็นรูปภาพสลิปโอนเงินธนาคารที่มี QR Code ชัดเจนเข้ามาใหม่อีกครั้งนะคะ"
        )
        try:
            _tok = get_channel_access_token()
            requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                json={"to": did, "messages": [{"type": "text", "text": _invalid_msg}]},
                timeout=10,
            )
        except Exception as push_err:
            logger.error(f"Failed to push invalid slip alert: {push_err}")

    _upload_fails = [r for r in uploaded_results if r and r.get("status") == "upload_failed"]
    uploaded_results = [r for r in uploaded_results if r and r.get("status") != "upload_failed"]
    if _upload_fails:
        _fail_names = ", ".join(r["name"] for r in _upload_fails)
        _fail_errors = "; ".join(r.get("error", "unknown") for r in _upload_fails)
        _fail_msg = (
            f"❌ อัปโหลดไฟล์ไม่สำเร็จค่ะ\n"
            f"ไฟล์: {_fail_names}\n"
            f"สาเหตุ: {_fail_errors}\n\n"
            f"กรุณาตรวจสอบการเชื่อมต่อ Google Drive ของระบบค่ะ"
        )
        try:
            _tok = get_channel_access_token()
            requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                json={"to": did, "messages": [{"type": "text", "text": _fail_msg}]},
                timeout=10,
            )
        except Exception:
            pass

    _limit_hits = [r for r in uploaded_results if r and r.get("status") == "limit_reached"]
    uploaded_results = [r for r in uploaded_results if r and r.get("status") != "limit_reached"]
    if _limit_hits:
        _lim = _limit_hits[0].get("limit", 30)
        _blocked_names = ", ".join(r["name"] for r in _limit_hits)
        _limit_msg = (
            f"❌ ใช้โควต้าบันทึกค่าใช้จ่ายครบ {_lim} รายการแล้วในเดือนนี้ค่ะ\n"
            f"ไฟล์ที่ไม่ได้บันทึก: {_blocked_names}\n\n"
            f"อัปเกรด Plan เพื่อใช้งานต่อได้เลยนะคะ"
        )
        try:
            _tok = get_channel_access_token()
            requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                json={"to": did, "messages": [{"type": "text", "text": _limit_msg}]},
                timeout=10,
            )
        except Exception:
            pass

    if uploaded_results:
        token = get_channel_access_token()
        push_url = "https://api.line.me/v2/bot/message/push"
        reply_url = "https://api.line.me/v2/bot/message/reply"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        _flex_reply_used = [False]  # mutable flag

        def _send_messages(msgs, label=""):
            """Try push; if 429 quota exceeded, fall back to reply token (free, expires in 30s)."""
            res = requests.post(push_url, headers=headers, json={"to": did, "messages": msgs}, timeout=20)
            logger.info(f"\U0001f4e4 [LINE Push Flex{' ' + label if label else ''}] Status: {res.status_code}, Response: {res.text}")
            if res.status_code != 200 and reply_tok and not _flex_reply_used[0]:
                logger.warning("\u26a0\ufe0f Push quota exceeded (429). Falling back to reply token for Flex card.")
                _flex_reply_used[0] = True
                reply_msgs = msgs[:5]  # reply API supports max 5 messages
                r2 = requests.post(reply_url, headers=headers,
                                   json={"replyToken": reply_tok, "messages": reply_msgs}, timeout=20)
                logger.info(f"\U0001f4e4 [LINE Reply Flex Fallback] Status: {r2.status_code}, Response: {r2.text}")
                if r2.status_code != 200:
                    # Reply token expired or invalid — send best-effort plain-text summary
                    logger.warning(f"\u26a0\ufe0f Reply also failed ({r2.status_code}). Sending plain-text summary as last resort.")
                    summary_lines = []
                    for m in msgs:
                        if m.get("type") == "flex":
                            alt = m.get("altText", "")
                            if alt:
                                summary_lines.append(alt)
                    if summary_lines:
                        summary_text = "\n".join(summary_lines)
                        try:
                            requests.post(push_url, headers=headers,
                                          json={"to": did, "messages": [{"type": "text", "text": summary_text}]}, timeout=10)
                        except Exception:
                            pass


        if len(uploaded_results) >= 2:

            # Generate Base URL
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
                env_url = os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL")
                if env_url:
                    base_url = env_url.rstrip('/')

            sheet_id = google_manager.spreadsheet_id
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else "#"

            summary_bubble = create_batch_summary_flex_bubble(uploaded_results, folder_name)
            
            paired_bubbles = []
            carousel_results = uploaded_results[:20]
            for i in range(0, len(carousel_results), 2):
                item1 = carousel_results[i]
                idx1 = i + 1
                item2 = carousel_results[i+1] if i+1 < len(carousel_results) else None
                idx2 = i + 2 if item2 else None
                
                bubble = create_paired_expense_flex_bubble(
                    item1=item1,
                    idx1=idx1,
                    item2=item2,
                    idx2=idx2,
                    folder_name=folder_name,
                    base_url=base_url,
                    sheet_url=sheet_url,
                    org_id=_upload_org_id,
                    username=u_name
                )
                paired_bubbles.append(bubble)

            messages = [
                {
                    "type": "flex",
                    "altText": "📊 สรุปรายการอัปโหลดแบบกลุ่ม",
                    "contents": summary_bubble
                }
            ]
            
            if paired_bubbles:
                messages.append({
                    "type": "flex",
                    "altText": "📂 รายละเอียดรายการใบเสร็จ",
                    "contents": {
                        "type": "carousel",
                        "contents": paired_bubbles
                    }
                })

            # Full quick reply shortcuts attached to batch summary card
            _sheet_qr = f"https://docs.google.com/spreadsheets/d/{google_manager.spreadsheet_id}/edit" if google_manager.spreadsheet_id else "https://sheets.google.com"
            _p_id2 = google_manager.parent_folder_id
            _drive_qr = f"https://drive.google.com/drive/folders/{_p_id2}" if _p_id2 else "https://drive.google.com"
            quick_reply_batch = {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "ส่งสลิปเพิ่ม", "text": "ส่งสลิประบบจะจัดเก็บให้อัตโนมัติค่ะ"}},
                    {"type": "action", "action": {"type": "message", "label": "สรุปรายจ่าย", "text": "สรุปรายจ่ายวันนี้"}},
                    {"type": "action", "action": {"type": "message", "label": "สรุปยอดวันนี้", "text": "สรุปยอดวันนี้"}},
                    {"type": "action", "action": {"type": "message", "label": "กระทบยอด", "text": "กระทบยอด"}},
                    {"type": "action", "action": {"type": "message", "label": "หาไฟล์", "text": "ค้นหา "}},
                    {"type": "action", "action": {"type": "uri", "label": "ดูบัญชี", "uri": _sheet_qr}},
                    {"type": "action", "action": {"type": "uri", "label": "Google Drive", "uri": _drive_qr}}
                ]
            }
            messages[-1]["quickReply"] = quick_reply_batch


            try:
                _send_messages(messages, "Batch")
            except Exception as e:
                logger.error(f"❌ [LINE Push Flex Batch] HTTP Error: {e}")

        else:
            messages = []
            for r in uploaded_results:
                sheet_name = r.get("sheet", "ทั่วไป")
                row_num = r.get("row", 1)
                file_link = r.get("link", "#")
                
                sheet_id = google_manager.spreadsheet_id
                sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else "#"
                
                status = r.get("status", "success")
                
                if status == "duplicate":
                    ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
                    smart_amt = extract_smart_amount(ext, analysis=r.get('analysis'), raw_result=r)
                    net_amt = smart_amt if (smart_amt is not None and smart_amt > 0) else ext.get('net_amount')
                    if not net_amt or str(net_amt).strip() in ['0', '0.0', '0.00', 'None', '', '-']:
                        net_amt = "-"
                    
                    ref_num = r.get("ref_number", "-")
                    
                    flex_bubble = create_duplicate_warning_flex_bubble(
                        sheet_name=sheet_name,
                        row_num=row_num,
                        ref_number=ref_num,
                        net_amount=net_amt,
                        sheet_url=sheet_url
                    )
                    
                    messages.append({
                        "type": "flex",
                        "altText": "⚠️ ตรวจพบการอัปโหลดสลิปซ้ำซ้อน",
                        "contents": flex_bubble
                    })
                else:
                    ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
                    smart_amt = extract_smart_amount(ext, analysis=r.get('analysis'), raw_result=r)
                    net_amt = smart_amt if (smart_amt is not None and smart_amt > 0) else ext.get('net_amount')
                    if not net_amt or str(net_amt).strip() in ['0', '0.0', '0.00', 'None', '', '-']:
                        net_amt = "-"
                    
                    date_val = ext.get('date') or datetime.now().strftime("%d/%m/%Y")
                    memo_val = ext.get('memo') or ext.get('summary') or r.get('name')
                    
                    vendor_val = ext.get('receiver') or ext.get('sender') or ext.get('merchant_name') or ext.get('supplier_name') or "-"
                    
                    edit_data_postback = f"action=edit_prompt&sheet={sheet_name}&row={row_num}"
                    
                    flex_bubble = create_expense_flex_bubble(
                        sheet_name=sheet_name,
                        folder_name=folder_name,
                        net_amount=net_amt,
                        date_str=date_val,
                        memo=memo_val,
                        vendor=vendor_val,
                        file_link=file_link,
                        sheet_url=sheet_url,
                        edit_data_postback=edit_data_postback,
                        raw_result=r,
                        org_id=_upload_org_id,
                        username=u_name
                    )
                    
                    messages.append({
                        "type": "flex",
                        "altText": "✅ บันทึกค่าใช้จ่ายสำเร็จ",
                        "contents": flex_bubble
                    })
                
                # Limit to 5 messages per push as per LINE API rules
                if len(messages) == 5:
                    try:
                        _send_messages(messages, "Batch")
                    except Exception as e:
                        logger.error(f"❌ [LINE Push Flex] Batch HTTP Error: {e}")
                    messages = []
                    
            if messages:
                # Full quick reply shortcuts on the last message
                _sheet_url_qr = f"https://docs.google.com/spreadsheets/d/{google_manager.spreadsheet_id}/edit" if google_manager.spreadsheet_id else "https://sheets.google.com"
                _p_id = google_manager.parent_folder_id
                _drive_url = f"https://drive.google.com/drive/folders/{_p_id}" if _p_id else "https://drive.google.com"
                quick_reply = {
                    "items": [
                        {"type": "action", "action": {"type": "message", "label": "ส่งสลิปเพิ่ม", "text": "ส่งสลิประบบจะจัดเก็บให้อัตโนมัติค่ะ"}},
                        {"type": "action", "action": {"type": "message", "label": "สรุปรายจ่าย", "text": "สรุปรายจ่ายวันนี้"}},
                        {"type": "action", "action": {"type": "message", "label": "สรุปยอดวันนี้", "text": "สรุปยอดวันนี้"}},
                        {"type": "action", "action": {"type": "message", "label": "กระทบยอด", "text": "กระทบยอด"}},
                        {"type": "action", "action": {"type": "message", "label": "หาไฟล์", "text": "ค้นหา "}},
                        {"type": "action", "action": {"type": "uri", "label": "ดูบัญชี", "uri": _sheet_url_qr}},
                        {"type": "action", "action": {"type": "uri", "label": "Google Drive", "uri": _drive_url}}
                    ]
                }
                messages[-1]["quickReply"] = quick_reply
                try:
                    _send_messages(messages)
                except Exception as e:
                    logger.error(f"❌ [LINE Push Flex] HTTP Error: {e}")

    else:
        token = get_channel_access_token()
        push_url = "https://api.line.me/v2/bot/message/push"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        try:
            requests.post(push_url, headers=headers,
                          json={"to": did, "messages": [{"type": "text", "text": "❌ ขออภัยค่ะ พั้นไม่สามารถจัดเก็บไฟล์ได้ในขณะนี้"}]}, timeout=10)
        except Exception as push_err:
            logger.error(f"❌ [LINE Push Error] Failed to send failure message: {push_err}")
            
    google_manager.clear_context()


def verify_line_signature(body_bytes, signature):
    """Verifies the LINE webhook signature.
    อ่านจาก config file (admin อัปเดตผ่าน UI) ก่อน แล้ว fallback env var
    """
    # อ่านจาก file ก่อน เพื่อให้ทุก worker ใช้ค่าเดียวกัน (ไม่พึ่ง os.environ)
    channel_secret = (get_line_config().get("channel_secret") or "").strip()
    if not channel_secret:
        channel_secret = os.environ.get("LINE_CHANNEL_SECRET", "").strip()
    if not channel_secret:
        logger.error("LINE_CHANNEL_SECRET is not set — rejecting LINE webhook request.")
        return False
    hash_obj = hmac.new(channel_secret.encode('utf-8'), body_bytes, hashlib.sha256).digest()
    calc_signature = base64.b64encode(hash_obj).decode('utf-8')
    return calc_signature == signature


@line_bp.route("/api/line/webhook", methods=['POST'])
def line_webhook():
    """Primary LINE Webhook Entry Point"""
    signature = request.headers.get('X-Line-Signature')
    # Get raw bytes for signature verification
    body_bytes = request.get_data()
    
    logger.info(f"[LINE Webhook] Received request. Signature present: {bool(signature)}, Body length: {len(body_bytes)}")
    
    if not signature:
        logger.warning("[LINE Webhook] No X-Line-Signature header — returning 400")
        return abort(400)
    
    if not verify_line_signature(body_bytes, signature):
        logger.warning(f"[LINE Webhook] Signature mismatch — returning 400. Received sig: {signature[:20]}...")
        return abort(400)

    
    # After reading get_data(), we can still get json if it's parsed
    data = request.get_json()
    events = data.get('events', []) if data else []
    
    for event in events:
        if _is_duplicate_webhook_event(event):
            logger.info(f"⏭️ [LINE Webhook] Skipping duplicate event delivery: {event.get('webhookEventId')}")
            continue
        threading.Thread(target=process_line_event, args=(event,), daemon=True).start()
    return 'OK'


def get_line_org_id(user_id: str, group_id: str = None) -> int | None:
    """Resolve which org a LINE message belongs to (group > user fallback)."""
    if group_id:
        org_id = database.get_org_id_by_line_group(group_id)
        if org_id:
            return org_id
    return database.get_org_id_by_line_user(user_id)


def process_line_command(text, user_id, reply_token, group_id=None):
    """Ultimate Command Processor with AI integration"""

    import secrets
    import time
    from datetime import datetime, timedelta, date

    _base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
    _text_pre  = text.lower().strip()

    # ── /groupid ทำงานก่อน org check เสมอ (ใช้ได้แม้ยังไม่ลงทะเบียน) ─────────
    if group_id and any(k in _text_pre for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
        _qr = {"items": [
            {"type": "action", "action": {"type": "uri", "label": "ลงทะเบียนกลุ่ม", "uri": f"{_base_url}/admin/line-groups"}},
            {"type": "action", "action": {"type": "uri", "label": "สมัครบริการ",     "uri": f"{_base_url}/signup"}},
        ]}
        reply_to_line(reply_token,
            f"สวัสดีค่ะพี่! รหัสกลุ่มนี้ (Group ID) คือ:\n\n"
            f"{group_id}\n\n"
            f"นำรหัสไปลงทะเบียนที่:\n{_base_url}/admin/line-groups\n\n"
            "แล้วน้องพั้นจะเริ่มทำงานให้ได้เลยค่ะ!",
            quick_reply=_qr)
        return
    elif not group_id and any(k in _text_pre for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
        reply_to_line(reply_token, "คำสั่งนี้ใช้ได้เฉพาะในกลุ่ม LINE ค่ะ กรุณาเพิ่มน้องพั้นเข้ากลุ่มก่อนนะคะ")
        return

    # ── [FIX] Account Linking (/link or ผูกบัญชี) - ทำงานก่อน Org Check เสมอ ──
    if not group_id and (_text_pre.startswith("/link") or "ผูกบัญชี" in _text_pre):
        username = database.get_username_by_line_id(user_id)
        quick_reply = {"items": [
            {"type": "action", "action": {"type": "uri", "label": "สมัครบริการ", "uri": f"{_base_url}/pricing"}},
        ]}
        
        if not username:
            import secrets
            import time
            token = secrets.token_urlsafe(32)
            # 🛡️ Persist token in DB for multi-worker and restart safety
            database.line_link_create(token, user_id)
            PENDING_LINE_LINKS[token] = {
                "line_user_id": user_id,
                "timestamp": time.time()
            }
            
            webhook_url = os.environ.get("ACTIVE_PUBLIC_URL")
            base_url = ""
            if webhook_url:
                base_url = webhook_url.split("/api/line/webhook")[0].rstrip('/')
            if not base_url:
                base_url = (os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL") or "https://openchat.sbs").rstrip('/')
            
            magic_url = f"{base_url}/line/link_magic?token={token}"
            magic_bubble = create_magic_link_flex_bubble(magic_url)
            reply_to_line(reply_token, {
                "type": "flex",
                "altText": "🔗 เชื่อมต่อบัญชี OrgChat AI",
                "contents": magic_bubble
            }, quick_reply=quick_reply)
        else:
            reply_to_line(reply_token, f"✅ พี่ {username} ผูกบัญชีไว้เรียบร้อยแล้วค่ะ!", quick_reply=quick_reply)
        return

    # ── Resolve org (multi-tenant) ────────────────────────────────────────────
    _line_org_id = get_line_org_id(user_id, group_id)
    if _line_org_id is None:
        _unreg_qr_items = [
            {"type": "action", "action": {"type": "message", "label": "👤 ผูกบัญชีระบบ", "text": "ผูกบัญชี"}},
            {"type": "action", "action": {"type": "message", "label": "รหัสกลุ่ม",   "text": "/groupid"}},
            {"type": "action", "action": {"type": "uri",    "label": "สมัครบริการ",  "uri": f"{_base_url}/signup"}},
            {"type": "action", "action": {"type": "uri",    "label": "ลงทะเบียนกลุ่ม", "uri": f"{_base_url}/admin/line-groups"}},
        ]
        if not group_id:
            _unreg_qr_items = [
                {"type": "action", "action": {"type": "message", "label": "👤 ผูกบัญชีระบบ", "text": "ผูกบัญชี"}},
                {"type": "action", "action": {"type": "uri",    "label": "สมัครบริการ",  "uri": f"{_base_url}/signup"}},
            ]
        _unreg_qr = {"items": _unreg_qr_items}
        
        welcome_text = "สวัสดีค่ะ! ยินดีต้อนรับสู่อ้อมอกของน้องพั้นนะคะ 😊\n\n"
        if group_id:
            welcome_text += (
                f"กลุ่มนี้ยังไม่ได้เชื่อมกับระบบค่ะ ทำตาม 3 ขั้นนี้ได้เลย:\n\n"
                f"1. สมัครที่ {_base_url}/signup\n"
                f"2. พิมพ์ /groupid เพื่อดูรหัสกลุ่มนี้\n"
                f"3. ลงทะเบียนที่ {_base_url}/admin/line-groups\n\n"
                f"กดปุ่มด้านล่างเพื่อเริ่มได้เลยค่ะ"
            )
        else:
            welcome_text += (
                "บัญชี LINE ส่วนตัวของพี่ ยังไม่ได้เชื่อมโยงเข้ากับโปรไฟล์ OrgChat AI เลยค่ะ\n\n"
                "👉 พี่สามารถกดปุ่ม \"👤 ผูกบัญชีระบบ\" ด้านล่าง หรือพิมพ์คำว่า \"ผูกบัญชี\" เพื่อรับการ์ดเชื่อมต่อบัญชีได้ทันทีเลยนะคะ ✨"
            )
        reply_to_line(reply_token, welcome_text, quick_reply=_unreg_qr)
        return

    # ── Billing gate: LINE Bot ต้อง Pro ขึ้นไป ──────────────────────────────
    if not billing.has_feature(_line_org_id, "line_bot"):
        reply_to_line(reply_token,
            "LINE Bot ใช้ได้เฉพาะ Plan Pro หรือสูงกว่าค่ะ\n"
            "อัปเกรดได้ที่ https://openchat.sbs/pricing")
        return

    mgr = google_manager
    owner_username = None
    if group_id:
        owner_username = database.get_group_owner(group_id)
    if owner_username:
        username = owner_username
    else:
        username = database.get_username_by_line_id(user_id)
    
    # 📝 Handle Active Edit Session
    session_data = RedisManager.get_active_edit_session(user_id)
    if session_data:
        RedisManager.delete(f"edit_session:{user_id}")
        # Check timeout (5 minutes = 300 seconds)
        if time.time() - session_data["timestamp"] < 300:
            # Check reconcile permission for edit session
            is_ok, sender_username = check_line_user_permission(user_id, "reconcile", reply_token, group_id)
            if not is_ok:
                return
            sheet = session_data["sheet"]
            row = session_data["row"]
            field = session_data["field"]
            display = session_data["display"]
            new_value = text.strip()
            
            # Update spreadsheet
            ok, err = mgr.update_expense(sheet, row, field, new_value)
            if ok:
                msg = f"✅ แก้ไขข้อมูลเรียบร้อยแล้วค่ะพี่!\n\n📊 ชีต: '{sheet}' แถวที่ {row}\n✏️ หัวข้อ: '{display}'\n📝 เปลี่ยนเป็น: '{new_value}'\n\nพั้นดำเนินการอัปเดตและกระทบยอดบัญชีใหม่ให้อัตโนมัติเรียบร้อยค่ะ ✨"
                
                # Persistent Quick Reply
                p_id = mgr.parent_folder_id
                drive_url = f"https://drive.google.com/drive/folders/{p_id}" if p_id else "https://drive.google.com"
                quick_reply = {
                    "items": [{
                        "type": "action",
                        "action": {
                            "type": "uri",
                            "label": "เปิด Google Drive",
                            "uri": drive_url
                        }
                    }]
                }
                if mgr.spreadsheet_id:
                    quick_reply["items"].insert(0, {
                        "type": "action",
                        "action": {
                            "type": "uri",
                            "label": "เปิด Google Sheets",
                            "uri": f"https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}/edit"
                        }
                    })
                reply_to_line(reply_token, msg, quick_reply=quick_reply)
            else:
                reply_to_line(reply_token, f"❌ เกิดข้อผิดพลาดในการแก้ไขข้อมูล: {err}\nพี่ลองพิมพ์รายการที่จะอัปเดตใหม่อีกครั้งนะคะ")
            return

    text_lower = text.lower().strip()
    try:
        with open('scratch/debug_log.txt', 'a', encoding='utf-8') as df:
            df.write(f"Received text: '{text}'\n")
            df.write(f"text_lower: '{text_lower}'\n")
            df.write(f"Match condition: {text_lower.startswith('/link') or 'ผูกบัญชี' in text_lower}\n")
            df.write(f"Username: '{username}'\n")
    except Exception as e:
        pass

    
    # Persistent Quick Reply — shown after every bot text response (max 13 items)
    p_id = mgr.parent_folder_id
    drive_url = f"https://drive.google.com/drive/folders/{p_id}" if p_id else "https://drive.google.com"
    sheet_url_qr = f"https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}/edit" if mgr.spreadsheet_id else "https://sheets.google.com"

    # Dynamic Quick Replies based on linked status
    quick_reply_items = [
        {"type": "action", "action": {"type": "location", "label": "📍 ลงเวลาทำงาน"}},
        {"type": "action", "action": {"type": "message", "label": "📅 ดูนัดหมาย", "text": "ดูนัดหมาย"}},
        {"type": "action", "action": {"type": "message", "label": "สรุปรายจ่ายวันนี้", "text": "สรุปรายจ่ายวันนี้"}},
        {"type": "action", "action": {"type": "message", "label": "สรุปยอดวันนี้", "text": "สรุปยอดวันนี้"}},
        {"type": "action", "action": {"type": "message", "label": "เริ่มกระทบยอด", "text": "กระทบยอด"}},
        {"type": "action", "action": {"type": "message", "label": "ค้นหาไฟล์", "text": "ค้นหา "}},
        {"type": "action", "action": {"type": "message", "label": "เลือกโฟลเดอร์", "text": "เลือกโฟลเดอร์"}},
        {"type": "action", "action": {"type": "message", "label": "บันทึกวันลา", "text": "ลางาน"}},
    ]
    
    if not username:
        quick_reply_items.insert(0, {"type": "action", "action": {"type": "message", "label": "ผูกบัญชีระบบ", "text": "ผูกบัญชี"}})
    else:
        quick_reply_items.append({"type": "action", "action": {"type": "message", "label": "ขอลิงก์ระบบ", "text": "ขอลิงก์"}})
        
    quick_reply_items.append({"type": "action", "action": {"type": "uri", "label": "ดู Google Sheet", "uri": sheet_url_qr}})
    quick_reply_items.append({"type": "action", "action": {"type": "uri", "label": "Google Drive", "uri": drive_url}})
    _base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
    quick_reply_items.append({"type": "action", "action": {"type": "uri", "label": "สมัครบริการ", "uri": f"{_base_url}/pricing"}})

    quick_reply = {"items": quick_reply_items[:13]}

    
    try:
        # 0. Handle /groupid or "groupid" or "รหัสกลุ่ม"
        if group_id and any(k in text_lower for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
            _base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
            g_msg = (
                "สวัสดีค่ะพี่! 😊 รหัสกลุ่ม LINE นี้ (Group ID) คือ:\n\n"
                f"👉 {group_id}\n\n"
                f"นำรหัสนี้ไปลงทะเบียนที่:\n{_base_url}/admin/line-groups\n\n"
                "เพื่อให้น้องพั้นรู้ว่ากลุ่มนี้เป็นของใคร และเริ่มใช้งานได้เลยค่ะ! 💖"
            )
            reply_to_line(reply_token, g_msg, quick_reply=quick_reply)
            return

        # 0.1 Handle สมัครบริการ
        if any(k in text_lower for k in ["สมัคร", "สมัครบริการ", "สมัครสมาชิก", "ราคา", "แพลน", "plan", "pricing"]):
            base_url = os.environ.get("BASE_URL", "https://openchat.sbs")
            signup_msg = (
                f"สวัสดีค่ะ! น้องพั้นยินดีแนะนำเลยนะคะ 😊\n\n"
                f"OrgChat AI มี 3 แพลนค่ะ:\n"
                f"• Free — ฟรี (AI 10 ครั้ง, บิล 100 ใบ/เดือน)\n"
                f"• Pro — ฿299/เดือน (ไม่จำกัด + LINE Bot)\n"
                f"• Ultra — ฿599/เดือน (ทีม 10 คน + Export)\n\n"
                f"สมัครได้เลยค่ะพี่ 👉 {base_url}/signup\n"
                f"ดูรายละเอียดเพิ่มเติม: {base_url}/pricing"
            )
            reply_to_line(reply_token, signup_msg, quick_reply=quick_reply)
            return

        # 0.2 Handle วิธีใช้งาน
        if "วิธีใช้" in text_lower or "help" == text_lower:
            help_msg = (
                "💡 **วิธีใช้งานน้องพั้นแบบง่ายๆ ค่ะ:**\n\n"
                "1. 📸 **ส่งรูปบิล/สลิป:** พี่แค่ถ่ายรูปหรือส่งรูปบิลเข้ามาในแชท น้องพั้นจะอ่านข้อมูลและสรุปยอดให้ทันที\n"
                "2. 📁 **เลือกโฟลเดอร์:** พอน้องพั้นสรุปข้อมูลเสร็จ จะมีปุ่มให้พี่เลือกโฟลเดอร์เพื่อจัดเก็บลง Google Drive และบันทึกบัญชีอัตโนมัติค่ะ\n"
                "3. ✏️ **แก้ไขข้อมูล:** ถ้า AI อ่านข้อมูลผิด พี่สามารถกดปุ่ม 'แก้ไข' ที่หน้ารายละเอียดการอัปโหลดได้เลยนะคะ\n"
                "4. 📊 **ดูสรุปยอด:** กดปุ่มด้านล่างหรือพิมพ์ 'สรุปยอดวันนี้' น้องพั้นจะดึงข้อมูลจากชีตมาสรุปให้ทันทีค่ะ!\n\n"
                "สงสัยตรงไหน ทักหาน้องพั้นได้ตลอดเลยนะคะ 💖"
            )
            reply_to_line(reply_token, help_msg, quick_reply=quick_reply)
            return
        elif not group_id and any(k in text_lower for k in ["/groupid", "groupid", "รหัสกลุ่ม"]):
            reply_to_line(reply_token, "ℹ️ คำสั่งนี้สามารถใช้ได้เฉพาะในกลุ่มแชท LINE เท่านั้นนะคะพี่ 😊", quick_reply=quick_reply)
            return

        # 1. Account Linking (/link or ผูกบัญชี) - (ย้ายไปดักรันด้านบนเพื่อความถูกต้องเรียบร้อยแล้วค่ะ)
        pass

        # 🔗 Workspace Links Request
        if any(k in text_lower for k in ["ขอลิงก์", "ลิงก์ระบบ", "ลิงก์"]):
            is_ok, sender_username = check_line_user_permission(user_id, "links", reply_token, group_id)
            if not is_ok:
                return
            sheet_id = mgr.spreadsheet_id
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else "https://sheets.google.com"
            p_id = mgr.parent_folder_id
            drive_url = f"https://drive.google.com/drive/folders/{p_id}" if p_id else "https://drive.google.com"
            
            links_bubble = create_links_flex_bubble(sheet_url, drive_url)
            reply_to_line(reply_token, {
                "type": "flex",
                "altText": "🔗 ลิงก์ระบบบัญชีและเอกสารของพี่ค่ะ",
                "contents": links_bubble
            }, quick_reply=quick_reply)
            return

        # 📍 Time Attendance Prompt Command
        if any(k in text_lower for k in ["ลงเวลา", "เช็กอิน", "เช็คอิน", "เข้างาน", "เลิกงาน", "checkin", "checkout", "clockin", "clockout"]):
            att_qr = {
                "items": [
                    {"type": "action", "action": {"type": "location", "label": "📍 แตะเพื่อแชร์พิกัดลงเวลา"}},
                    {"type": "action", "action": {"type": "message", "label": "ดูประวัติลงเวลา", "text": "ประวัติลงเวลา"}},
                ]
            }
            reply_to_line(reply_token, 
                "📍 สวัสดีค่ะพี่! พี่สามารถแตะปุ่ม **'📍 แตะเพื่อแชร์พิกัดลงเวลา'** ด้านล่างนี้ได้เลยนะคะ\n\n"
                "ระบบจะตรวจสอบรัศมีระยะห่าง Geofence จากสำนักงาน และบันทึกเวลาเข้างาน / ออกงานให้อัตโนมัติทันทีค่ะ 🏢✨",
                quick_reply=att_qr)
            return

        # 📋 View Attendance History
        if any(k in text_lower for k in ["ประวัติลงเวลา", "เวลาเข้างาน"]):
            from datetime import date
            today_str = date.today().isoformat()
            recs = database.get_attendance_records(start_date=today_str, end_date=today_str, org_id=_line_org_id)
            user_recs = [r for r in recs if r.get("username") == username] if username else []
            if not user_recs:
                reply_to_line(reply_token, f"ℹ️ วันนี้ ({today_str}) ยังไม่พบบันทึกการลงเวลาทำงานของพี่นะคะ\n\nพี่สามารถแตะปุ่ม '📍 ลงเวลาทำงาน' เพื่อบันทึกเวลาได้เลยค่ะ", quick_reply=quick_reply)
            else:
                r = user_recs[0]
                cin = r.get("clock_in_time") or "-"
                cout = r.get("clock_out_time") or "ยังไม่ได้ลงเวลาออก"
                stat = r.get("status") or "-"
                loc = r.get("location_name") or "ออฟฟิศ"
                dist = r.get("distance_meters") or 0
                msg = (
                    f"🏢 **ประวัติการลงเวลาทำงานวันนี้ ({today_str})**\n\n"
                    f"👤 ผู้ใช้งาน: {username}\n"
                    f"🟢 เวลาเข้างาน: {cin}\n"
                    f"🔴 เวลาเลิกงาน: {cout}\n"
                    f"📍 สถานะ/จุด: {loc} ({stat})\n"
                    f"📏 ระยะห่างจากจุดหลัก: {dist:.1f} เมตร\n\n"
                    "ขอบคุณสำหรับความตั้งใจทำงานในวันนี้นะคะ! 💖"
                )
                reply_to_line(reply_token, msg, quick_reply=quick_reply)
            return

        # 📅 Schedules / Calendar Commands
        is_schedule_add = any(k in text_lower for k in ["เพิ่มกำหนดการ", "เพิ่มนัด", "ลงตาราง", "นัดหมายใหม่", "/schedule"]) or (
            any(k in text_lower for k in ["นัดหมาย", "นัดประชุม", "กำหนดการ"]) and any(k in text_lower for k in ["วันที่", "พรุ่งนี้", "มะรืนนี้", "เวลา", "โมง", "am", "pm"])
        )
        if is_schedule_add:
            # Smart parsing of schedule details using regex & datetime
            from datetime import datetime, timedelta
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

            extracted_date = today_str
            extracted_time = "09:00"

            # Extract date if mentioned
            if "พรุ่งนี้" in text:
                extracted_date = tomorrow_str
            elif "มะรืนนี้" in text:
                extracted_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
            else:
                # Match YYYY-MM-DD or DD/MM/YYYY or วันที่ DD
                d_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
                if d_match:
                    extracted_date = d_match.group(1).replace('/', '-')
                else:
                    d_day = re.search(r'วันที่\s*(\d{1,2})', text)
                    if d_day:
                        day_num = int(d_day.group(1))
                        target_month = now.month
                        target_year = now.year
                        if day_num < now.day:
                            target_month = (target_month % 12) + 1
                            if target_month == 1:
                                target_year += 1
                        extracted_date = f"{target_year}-{target_month:02d}-{day_num:02d}"

            # Extract time
            t_match = re.search(r'(\d{1,2})[.:](\d{2})', text)
            if t_match:
                extracted_time = f"{int(t_match.group(1)):02d}:{t_match.group(2)}"
            else:
                # E.g. "9.00 am" or "9 am"
                am_pm = re.search(r'(\d{1,2})(?:[.:](\d{2}))?\s*(am|pm)', text, re.IGNORECASE)
                if am_pm:
                    hr = int(am_pm.group(1))
                    mn = am_pm.group(2) or "00"
                    if am_pm.group(3).lower() == 'pm' and hr < 12:
                        hr += 12
                    elif am_pm.group(3).lower() == 'am' and hr == 12:
                        hr = 0
                    extracted_time = f"{hr:02d}:{mn}"
                else:
                    m_hour = re.search(r'(\d{1,2})\s*โมง', text)
                    if m_hour:
                        extracted_time = f"{int(m_hour.group(1)):02d}:00"

            # Clean title
            clean_title = text
            for remove_word in ["เพิ่มกำหนดการ", "เพิ่มนัด", "ลงตาราง", "นัดหมาย", "นัดประชุม", "กำหนดการ", "/schedule"]:
                clean_title = clean_title.replace(remove_word, "")
            clean_title = re.sub(r'วันที่\s*\S+', '', clean_title)
            clean_title = re.sub(r'เวลา\s*\S+', '', clean_title)
            clean_title = re.sub(r'ชื่อกำหนดการ\s*', '', clean_title)
            clean_title = clean_title.strip(": \t\r\n")
            if not clean_title or len(clean_title) < 2:
                clean_title = f"นัดหมาย ({extracted_date} {extracted_time})"

            # Add to database
            creator = username or "LINE User"
            new_id = database.add_schedule(
                username=creator,
                title=clean_title,
                start_date=extracted_date,
                description=f"สร้างผ่าน LINE Bot โดย {creator}",
                category="Meeting",
                start_time=extracted_time,
                is_public=1,
                org_id=_line_org_id
            )

            confirm_flex = {
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#ECFDF5",
                    "paddingAll": "20px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "✅ บันทึกนัดหมายสำเร็จ!",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#047857"
                        },
                        {
                            "type": "text",
                            "text": clean_title,
                            "weight": "bold",
                            "size": "xl",
                            "color": "#0F172A",
                            "margin": "sm",
                            "wrap": True
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "md",
                            "contents": [
                                {"type": "text", "text": "📅 วันที่", "size": "sm", "color": "#64748B", "flex": 2},
                                {"type": "text", "text": extracted_date, "size": "sm", "color": "#0F172A", "weight": "bold", "flex": 5}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "sm",
                            "contents": [
                                {"type": "text", "text": "⏰ เวลา", "size": "sm", "color": "#64748B", "flex": 2},
                                {"type": "text", "text": f"{extracted_time} น.", "size": "sm", "color": "#2563EB", "weight": "bold", "flex": 5}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "sm",
                            "contents": [
                                {"type": "text", "text": "👤 ผู้บันทึก", "size": "sm", "color": "#64748B", "flex": 2},
                                {"type": "text", "text": str(creator), "size": "sm", "color": "#0F172A", "flex": 5}
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
                            "text": "⏰ ระบบจะแจ้งเตือนล่วงหน้า 30 นาทีทาง LINE ให้อัตโนมัติค่ะ",
                            "size": "xxs",
                            "color": "#059669",
                            "align": "center"
                        }
                    ]
                }
            }

            reply_to_line(reply_token, {
                "type": "flex",
                "altText": f"📅 บันทึกนัดหมาย: {clean_title}",
                "contents": confirm_flex
            }, quick_reply=quick_reply)
            return

        # 📅 View upcoming schedules
        if any(k in text_lower for k in ["ดูนัดหมาย", "ตารางงาน", "ปฏิทิน", "กำหนดการวันนี้", "นัดหมายวันนี้"]):
            from datetime import date
            today_str = date.today().isoformat()
            s_list = database.get_schedules(username=username, org_id=_line_org_id)
            upcoming = [s for s in s_list if s.get("date", "") >= today_str][:5]
            if not upcoming:
                reply_to_line(reply_token, "📅 ไม่พบนัดหมายที่กำลังจะมาถึงในเร็วๆ นี้ค่ะพี่ 😊\n\nพี่สามารถพิมพ์ 'เพิ่มกำหนดการ วันที่... เวลา...' เพื่อให้น้องพั้นบันทึกให้ได้เลยนะคะ", quick_reply=quick_reply)
            else:
                msg = f"📅 **กำหนดการและนัดหมายที่กำลังจะมาถึง ({len(upcoming)} รายการ):**\n\n"
                for idx, s in enumerate(upcoming, 1):
                    msg += f"{idx}. **{s.get('title')}**\n"
                    msg += f"   📅 วันที่: {s.get('date')} เวลา: {s.get('time')} น.\n"
                    msg += f"   🏷️ หมวดหมู่: {s.get('category')} (โดย {s.get('display_name')})\n\n"
                msg += "⏰ ระบบจะแจ้งเตือนล่วงหน้า 30 นาทีก่อนเริ่มทุกนัดหมายค่ะ 💖"
                reply_to_line(reply_token, msg, quick_reply=quick_reply)
            return

        # 2. Expense Reporting
        is_expense_req = False
        expense_keywords = ["สรุปรายจ่าย", "ยอดรายจ่าย", "รายงานรายจ่าย", "สรุปยอด", "รายจ่ายสะสม"]
        if any(k in text_lower for k in expense_keywords):
            is_expense_req = True
        elif "รายจ่าย" in text_lower and any(k in text_lower for k in ["วันนี้", "เดือนนี้", "วันนี"]):
            is_expense_req = True

        if is_expense_req:
            is_ok, sender_username = check_line_user_permission(user_id, "report", reply_token, group_id)
            if not is_ok:
                return
            # วิเคราะห์ช่วงเวลา (today หรือ month)
            period = "month"
            if any(k in text_lower for k in ["วันนี้", "รายวัน", "ประจำวัน", "วันนี"]):
                period = "today"

            summary = mgr.get_monthly_summary(period=period)
            
            # --- 📊 Stunning Donut Chart Generation & Integration ---
            try:
                raw_data = mgr.get_monthly_summary(return_raw=True, period=period)
                if isinstance(raw_data, tuple) and len(raw_data) == 3:
                    total_expense, total_count, categories_breakdown = raw_data
                    if total_count > 0 and categories_breakdown:
                        from chart_generator import generate_monthly_expense_chart
                        
                        # Determine base URL dynamically
                        base_url = "http://localhost:5005"
                        webhook_url = os.environ.get("ACTIVE_PUBLIC_URL")
                        if webhook_url:
                            if "/api/line/webhook" in webhook_url:
                                base_url = webhook_url.split("/api/line/webhook")[0]
                            else:
                                base_url = webhook_url.rstrip('/')
                        else:
                            env_url = os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL")
                            if env_url:
                                base_url = env_url.rstrip('/')
                        
                        # Generate the beautiful donut chart
                        chart_filename = generate_monthly_expense_chart(categories_breakdown)
                        chart_url = f"{base_url}/uploads/social_feed/{chart_filename}"
                        
                        # Construct a multi-message response containing both the Flex summary and the chart image!
                        messages = []
                        if isinstance(summary, dict):
                            messages.append(summary)
                        else:
                            messages.append({"type": "text", "text": str(summary)})
                            
                        messages.append({
                            "type": "image",
                            "originalContentUrl": chart_url,
                            "previewImageUrl": chart_url
                        })
                        
                        reply_to_line(reply_token, messages, quick_reply=quick_reply)
                        return
            except Exception as chart_err:
                logger.error(f"⚠️ Failed to generate and attach expense chart: {chart_err}")
                
            reply_to_line(reply_token, summary, quick_reply=quick_reply)
            return

        # 3. Enhanced File Retrieval (Drive + Database Logs)
        if text_lower.startswith(("หาไฟล์", "ค้นหา", "search")):
            is_ok, sender_username = check_line_user_permission(user_id, "search", reply_token, group_id)
            if not is_ok:
                return
            query = text.replace("หาไฟล์", "").replace("ค้นหา", "").replace("search", "").strip()
            if not query:
                reply_to_line(reply_token, "พี่ต้องการหาไฟล์อะไรคะ? ระบุชื่อมาได้เลยค่ะ 😊")
                return

            db_logs = database.search_drive_logs(query, limit=5)
            drive_files = []
            if hasattr(google_drive_service, 'search_files'):
                drive_files = google_drive_service.search_files(query)
            
            if drive_files or db_logs:
                resp = f"🔍 น้องพั้นพบไฟล์ที่พี่ต้องการแล้วค่ะ ({len(drive_files) + len(db_logs)} รายการ):\n\n"
                seen = set()
                for log in db_logs:
                    if log.get('file_link'):
                        seen.add(log['file_link'])
                        resp += f"📄 {log['filename']}\n📂 {log.get('category', 'ทั่วไป')}\n🔗 {log['file_link']}\n\n"
                for f in drive_files:
                    if f.get('webViewLink') and f['webViewLink'] not in seen:
                        resp += f"📄 {f['name']}\n🔗 {f['webViewLink']}\n\n"
                reply_to_line(reply_token, resp, quick_reply=quick_reply)
            else:
                reply_to_line(reply_token, f"❌ ไม่พบไฟล์ที่ชื่อ '{query}' เลยค่ะพี่", quick_reply=quick_reply)
            return

        # 4. Background Reconciliation
        if any(k in text_lower for k in ["กระทบยอด", "reconcile"]):
            is_ok, sender_username = check_line_user_permission(user_id, "reconcile", reply_token, group_id)
            if not is_ok:
                return
            reply_to_line(reply_token, "⏳ น้องพั้นกำลังเริ่มจับคู่สลิปกับใบกำกับภาษีให้พี่อยู่นะคะ... เมื่อเสร็จแล้วจะแจ้งเตือนไปค่ะ ✨")
            def run_recon():
                try:
                    try:
                        mgr.set_context(sender_username or username, _line_org_id)
                        mgr.auto_reconcile_internal()
                        push_msg = f"✅ กระทบยอดข้อมูลเสร็จเรียบร้อยแล้วค่ะพี่!\n🌐 https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}"
                    except Exception as r_err:
                        logger.error(f"Reconciliation error via chat command: {r_err}")
                        push_msg = f"❌ เกิดข้อผิดพลาดในการกระทบยอดค่ะ: {r_err}"
                    finally:
                        try:
                            mgr.clear_context()
                        except Exception:
                            pass
                    
                    token = get_channel_access_token()
                    requests.post("https://api.line.me/v2/bot/message/push", 
                                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                  json={"to": user_id, "messages": [{"type": "text", "text": push_msg}]}, timeout=10)
                except Exception as e: logger.error(f"Background Recon Error: {e}")
            threading.Thread(target=run_recon).start()
            return

        # 5.0 Leave History
        if any(k in text_lower for k in ["ประวัติการลา", "ดูประวัติลา", "เช็กวันลา", "เช็ควันลา", "ดูวันลา"]):
            is_ok, sender_username = check_line_user_permission(user_id, "leave", reply_token, group_id)
            if not is_ok:
                return
            leaves = database.get_user_leaves(sender_username) if sender_username else []
            if not leaves:
                rec = database.get_recent_leave_request(user_id)
                leaves = [dict(rec)] if rec else []
            if not leaves:
                reply_to_line(reply_token, "🏖️ ไม่พบประวัติการลาของคุณในระบบค่ะ พี่สามารถพิมพ์ 'ขอลางาน' เพื่อยื่นคำขอลาได้เลยนะคะ 😊", quick_reply=quick_reply)
                return
            status_map = {
                "pending": "⏳ รอดำเนินการ",
                "approved": "✅ อนุมัติแล้ว",
                "rejected": "❌ ปฏิเสธ"
            }
            type_map = {
                "Sick": "ลาป่วย",
                "Personal": "ลากิจ",
                "Vacation": "ลาพักร้อน",
                "Military": "ลาเกณฑ์ทหาร",
                "Maternity": "ลาคลอด"
            }
            hist_msg = f"📋 **ประวัติการลาล่าสุดของคุณ ({len(leaves[:5])} รายการ):**\n\n"
            for idx, lv in enumerate(leaves[:5], 1):
                raw_t = lv.get("type") or lv.get("leave_type") or "ลาหยุด"
                t_display = type_map.get(raw_t, raw_t)
                s_d = lv.get("start_date") or "-"
                e_d = lv.get("end_date") or s_d
                st = status_map.get(lv.get("status", "pending"), lv.get("status", "รอดำเนินการ"))
                r_disp = lv.get("reason") or "-"
                hist_msg += f"{idx}. **{t_display}** ({st})\n"
                hist_msg += f"   📅 วันที่: {s_d} ถึง {e_d}\n"
                if r_disp and r_disp != "-":
                    hist_msg += f"   💬 เหตุผล: {r_disp}\n"
                hist_msg += "\n"
            reply_to_line(reply_token, hist_msg.strip(), quick_reply=quick_reply)
            return

        # 5.1 Leave Request & Leave Guide
        if any(k in text_lower for k in ["ลางาน", "ลาป่วย", "ลากิจ", "ลาพักร้อน", "ขอลางาน", "บันทึกวันลา", "ขอลา", "ยื่นใบลา"]):
            is_ok, sender_username = check_line_user_permission(user_id, "leave", reply_token, group_id)
            if not is_ok:
                return

            # Check if this is a generic intent without specific dates or details
            clean_cmd = text.strip()
            is_generic = clean_cmd in ["ลางาน", "ขอลางาน", "บันทึกวันลา", "ขอลา", "ใบลา", "ยื่นใบลา", "leave"] or (
                len(clean_cmd) <= 8 and not any(k in text_lower for k in ["ป่วย", "กิจ", "พัก", "วัน", "ถึง", "-", "/"])
            )

            if is_generic:
                leave_guide_bubble = {
                    "type": "bubble",
                    "size": "mega",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": "#3B82F6",
                        "paddingAll": "20px",
                        "contents": [
                            {"type": "text", "text": "HR LEAVE SERVICE", "color": "#DBEAFE", "weight": "bold", "size": "xs"},
                            {"type": "text", "text": "🏖️ ระบบยื่นคำขอลางาน", "color": "#FFFFFF", "weight": "bold", "size": "lg", "margin": "xs"}
                        ]
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "20px",
                        "spacing": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "พี่สามารถยื่นคำขอลางานได้สะดวก 2 ช่องทางค่ะ:",
                                "color": "#334155",
                                "size": "sm",
                                "wrap": True
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "backgroundColor": "#F8FAFC",
                                "cornerRadius": "12px",
                                "paddingAll": "12px",
                                "spacing": "xs",
                                "contents": [
                                    {"type": "text", "text": "💬 1. พิมพ์ขอลางานในแชทได้ทันที", "color": "#0F172A", "weight": "bold", "size": "xs"},
                                    {"type": "text", "text": "• ลาป่วย วันนี้ มีไข้สูง\n• ลากิจ พรุ่งนี้ ไปทำธุระ\n• ลาพักร้อน 2026-10-15 ถึง 2026-10-16", "color": "#64748B", "size": "xxs", "wrap": True}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "backgroundColor": "#EFF6FF",
                                "cornerRadius": "12px",
                                "paddingAll": "12px",
                                "spacing": "xs",
                                "contents": [
                                    {"type": "text", "text": "🌐 2. เปิดหน้าเว็บระบบลางาน", "color": "#1D4ED8", "weight": "bold", "size": "xs"},
                                    {"type": "text", "text": "เลือกวันที่ผ่านปฏิทิน เช็กโควตาวันลา และแนบเอกสารใบรับรองแพทย์", "color": "#3B82F6", "size": "xxs", "wrap": True}
                                ]
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "16px",
                        "backgroundColor": "#FFFFFF",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#2563EB",
                                "height": "sm",
                                "action": {
                                    "type": "uri",
                                    "label": "🌐 เปิดระบบยื่นใบลา (Web App)",
                                    "uri": f"{_base_url}/#leave"
                                }
                            }
                        ]
                    }
                }
                leave_qr = {
                    "items": [
                        {"type": "action", "action": {"type": "message", "label": "🤒 ลาป่วยวันนี้", "text": "ลาป่วย วันนี้ มีอาการไม่สบาย"}},
                        {"type": "action", "action": {"type": "message", "label": "💼 ลากิจวันนี้", "text": "ลากิจ วันนี้ ไปทำธุระจำเป็น"}},
                        {"type": "action", "action": {"type": "message", "label": "🏖️ ลาพักร้อน", "text": "ลาพักร้อน"}},
                        {"type": "action", "action": {"type": "message", "label": "📋 ดูประวัติการลา", "text": "ดูประวัติการลา"}},
                        {"type": "action", "action": {"type": "uri", "label": "🌐 ระบบลางาน", "uri": f"{_base_url}/#leave"}},
                    ]
                }
                reply_to_line(reply_token, {
                    "type": "flex",
                    "altText": "🏖️ ระบบยื่นคำขอลางาน OrgChat AI",
                    "contents": clean_flex_payload(leave_guide_bubble)
                }, quick_reply=leave_qr)
                return

            # Specific leave submission via chat: parse type, dates, reason
            leave_type_en = "Sick" if ("ป่วย" in text_lower or "ไม่สบาย" in text_lower or "ไข้" in text_lower) else "Vacation" if ("พักร้อน" in text_lower or "พักผ่อน" in text_lower) else "Personal"
            leave_type_th = "ลาป่วย" if leave_type_en == "Sick" else "ลาพักร้อน" if leave_type_en == "Vacation" else "ลากิจ"

            # Parse dates
            date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', text)
            if len(date_matches) >= 2:
                start_date_str = date_matches[0]
                end_date_str = date_matches[1]
            elif len(date_matches) == 1:
                start_date_str = date_matches[0]
                end_date_str = date_matches[0]
            elif "พรุ่งนี้" in text_lower:
                tmrw = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
                start_date_str = tmrw
                end_date_str = tmrw
            else:
                today_str = date.today().strftime("%Y-%m-%d")
                start_date_str = today_str
                end_date_str = today_str

            # Parse clean reason
            reason_clean = text
            for strip_w in ["ขอยื่น", "ขอลางาน", "บันทึกวันลา", "ลางาน", "ลาป่วย", "ลากิจ", "ลาพักร้อน", "วันนี้", "พรุ่งนี้", "วันที่", "ถึง"]:
                reason_clean = re.sub(rf'\b{strip_w}\b', '', reason_clean, flags=re.IGNORECASE)
            for d in date_matches:
                reason_clean = reason_clean.replace(d, '')
            reason_clean = reason_clean.strip(" :-,\t\r\n")
            if not reason_clean or len(reason_clean) < 2:
                reason_clean = f"ขอ{leave_type_th}"

            # Save to database
            req_id = database.add_leave_request(
                line_user_id=user_id,
                username=sender_username or user_id,
                leave_type=leave_type_en,
                start_date=start_date_str,
                end_date=end_date_str,
                reason=reason_clean,
                org_id=_line_org_id
            )

            # Profile & display lookup
            profile = database.get_user_profile(sender_username) or {}
            applicant_display = profile.get("display_name") or get_line_sender_name(group_id, user_id) or sender_username or "พนักงาน"
            user_dept = profile.get("department", "")
            user_pos = profile.get("position", "")

            # Identify Direct Manager and Admins to push 1-Click approval card
            notify_targets = []
            direct_manager = None
            if _line_org_id:
                org_members = database.get_org_members(_line_org_id)
                applicant_member = next((m for m in org_members if m["username"].lower() == (sender_username or "").lower()), None)
                if applicant_member:
                    direct_manager = (applicant_member.get("manager_username") or "").strip()
                    if applicant_member.get("department") and not user_dept:
                        user_dept = applicant_member["department"]
                    if applicant_member.get("position") and not user_pos:
                        user_pos = applicant_member["position"]
                if direct_manager and direct_manager.lower() != (sender_username or "").lower():
                    notify_targets.append(direct_manager)
                for m in org_members:
                    m_user = m["username"]
                    if m_user.lower() == (sender_username or "").lower():
                        continue
                    if (m.get("role") == "admin" or m.get("can_manage_leave")) and m_user not in notify_targets:
                        notify_targets.append(m_user)
                if not notify_targets:
                    notify_targets = [m["username"] for m in org_members if m.get("role") == "admin"]
            else:
                notify_targets = [a for a in database.get_all_admins() if a.lower() != (sender_username or "").lower()]

            # Send 1-Click Approval Push Notification to Managers/Admins
            if req_id and notify_targets:
                try:
                    admin_leave_bubble = create_leave_approval_flex_bubble(
                        leave_id=req_id,
                        applicant_name=applicant_display,
                        leave_type=leave_type_th,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        reason=reason_clean,
                        department=user_dept,
                        position=user_pos
                    )
                    for target in notify_targets:
                        is_direct = bool(direct_manager and target.lower() == direct_manager.lower())
                        h_msg = "🏖️ สมาชิกในทีมของคุณยื่นคำขอลาหยุดใหม่!" if is_direct else "🏖️ มีคำขอลาหยุดใหม่รอการอนุมัติ!"
                        s_msg = f"ผู้ใช้งาน {applicant_display} ได้ยื่นคำขอลา {leave_type_th} ({start_date_str} ถึง {end_date_str})"
                        threading.Thread(target=send_line_push_notification, args=(
                            target,
                            h_msg,
                            s_msg,
                        ), kwargs={
                            "flex_bubble": admin_leave_bubble,
                            "fields": {
                                "ผู้ขอลา": applicant_display,
                                "ประเภท": leave_type_th,
                                "ช่วงวันลา": f"{start_date_str} ถึง {end_date_str}",
                                "เหตุผล": reason_clean
                            }
                        }).start()
                except Exception as notif_err:
                    logger.error(f"Error dispatching leave approval push: {notif_err}")

            confirm_msg = (
                f"✅ **ยื่นคำขอลางานเรียบร้อยแล้วค่ะ!**\n\n"
                f"📋 **รายละเอียดคำขอ #{req_id}:**\n"
                f"• ประเภท: {leave_type_th}\n"
                f"• ช่วงวันลา: {start_date_str} ถึง {end_date_str}\n"
                f"• เหตุผล: {reason_clean}\n"
                f"• สถานะ: ⏳ รอดำเนินการอนุมัติ\n\n"
                f"🔔 น้องพั้นได้ส่งการ์ดแจ้งเตือนและปุ่มอนุมัติ 1-Click ไปยังหัวหน้างาน/Admin ทาง LINE เรียบร้อยแล้วนะคะ หากได้รับการพิจารณาแล้ว ระบบจะแจ้งเตือนกลับทันทีค่ะ ✨"
            )
            reply_to_line(reply_token, confirm_msg, quick_reply=quick_reply)
            return

        # 6. Folder Selection Manual Command
        if any(k in text_lower for k in ["เลือกโฟลเดอร์", "โฟลเดอร์", "folder"]):
            is_ok, sender_username = check_line_user_permission(user_id, "folder", reply_token, group_id)
            if not is_ok:
                return
            folder_flex = get_folder_flex_message(group_id or user_id)
            if folder_flex:
                reply_to_line(reply_token, [{"type": "text", "text": "📂 พี่ต้องการให้พั้นเก็บไฟล์ไว้ที่โฟลเดอร์ไหนดีคะ? เลือกได้เลยค่ะ"}, folder_flex])
            else:
                reply_to_line(reply_token, "❌ น้องพั้นหาโฟลเดอร์ใน Drive ไม่เจอเลยค่ะพี่")
            return

        # ── 7. Text-to-Expense Handler (พิมพ์บันทึกค่าใช้จ่ายผ่าน LINE + ใบแทนใบเสร็จ Form 50) ──
        has_amount = bool(re.search(r'\d+', text))
        is_expense_trigger = any(text_lower.startswith(k) for k in ["เบิก", "บันทึกค่า", "บันทึกรายจ่าย", "จ่ายค่า", "ค่าใช้จ่าย", "ค่า"]) and has_amount
        if is_expense_trigger and not text_lower.startswith(("ค่าบริการ", "ค่าน้ำมันเท่าไหร่", "ค่าใช้จ่ายคือ", "ค่าอะไร")):
            is_ok, sender_username = check_line_user_permission(user_id, "expense", reply_token, group_id)
            if is_ok:
                try:
                    import payment_voucher_service

                    sender_name = get_line_sender_name(group_id, user_id) or "ผู้ขอเบิกเงิน"
                    org_info = database.get_org(_line_org_id)
                    org_name = org_info.get("name", "องค์กรของคุณ") if org_info else "องค์กรของคุณ"

                    # Parse amount from text: look for number preceding 'บาท' or largest monetary float value
                    extracted_net = 0.0
                    baht_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:บาท|baht|b)', text, re.IGNORECASE)
                    if baht_match:
                        extracted_net = float(baht_match.group(1))
                    else:
                        all_nums = [float(n) for n in re.findall(r'(\d+(?:\.\d+)?)', text)]
                        if all_nums:
                            extracted_net = max(all_nums)

                    extracted_details = text
                    extracted_merchant = "-"

                    # Try AI structured analysis
                    try:
                        analysis_prompt = (
                            f"วิเคราะห์ข้อความเบิกค่าใช้จ่ายนี้: '{text}'\n"
                            f"สกัดข้อมูลออกมาเป็น JSON เท่านั้น:\n"
                            f"{{\"details\": \"รายละเอียดค่าใช้จ่าย เช่น ค่าแท็กซี่ไปพบลูกค้า\", \"net_amount\": 250, \"merchant\": \"ชื่อร้านค้า/ผู้รับเงินถ้ามี หรือ -\"}}"
                        )
                        ai_res = ai_providers.generate_chat_response(analysis_prompt)
                        if isinstance(ai_res, str) and "{" in ai_res:
                            json_str = ai_res[ai_res.find("{"):ai_res.rfind("}")+1]
                            parsed_json = json.loads(json_str)
                            extracted_details = parsed_json.get("details") or extracted_details
                            extracted_net = float(parsed_json.get("net_amount") or extracted_net)
                            extracted_merchant = parsed_json.get("merchant") or extracted_merchant
                    except Exception as ai_parse_err:
                        logger.warning(f"AI parse fallback for Text-to-Expense: {ai_parse_err}")

                    item_data = {
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "line_sender_name": sender_name,
                        "requester": sender_name,
                        "merchant": extracted_merchant,
                        "details": extracted_details,
                        "net_amount": extracted_net,
                        "ref_number": f"RS-{int(time.time())}"
                    }

                    # Generate PDF Form 50
                    abs_pdf_path, pdf_filename = payment_voucher_service.generate_receipt_substitute_pdf(item_data, org_name=org_name)
                    pdf_url = f"{_base_url}/static/downloads/{pdf_filename}"

                    # Upload to Google Drive folder "ใบแทนใบเสร็จ"
                    try:
                        with open(abs_pdf_path, "rb") as f_pdf:
                            pdf_bytes = f_pdf.read()
                        drive_res = mgr.upload_file(
                            content=pdf_bytes,
                            filename=pdf_filename,
                            mimetype="application/pdf",
                            target_folder_name="ใบแทนใบเสร็จ",
                            uploader_id=user_id
                        )
                        if drive_res and isinstance(drive_res, dict) and drive_res.get("web_view_link"):
                            pdf_url = drive_res["web_view_link"]
                    except Exception as drive_err:
                        logger.warning(f"Drive upload for Form 50 failed: {drive_err}")

                    # Log to Google Sheets
                    try:
                        mgr.add_expense_row("บันทึกค่าใช้จ่าย", [
                            item_data["date"],
                            sender_name,
                            extracted_details,
                            extracted_merchant,
                            f"{extracted_net:,.2f}",
                            "ใบแทนใบเสร็จ (รอเซ็นชื่อ)",
                            pdf_url
                        ])
                    except Exception as sheet_err:
                        logger.warning(f"Sheets log failed for Form 50: {sheet_err}")

                    reply_msg = (
                        f"📝 **บันทึกรายการรายจ่ายเรียบร้อยค่ะ!**\n\n"
                        f"📌 **รายการ:** {extracted_details}\n"
                        f"💰 **ยอดเงิน:** ฿{extracted_net:,.2f}\n"
                        f"👤 **ผู้เบิก:** {sender_name}\n"
                        f"📁 **บันทึกลงชีต:** บันทึกค่าใช้จ่าย\n\n"
                        f"📄 **ดาวน์โหลด PDF ใบแทนใบเสร็จ Form 50:**\n{pdf_url}"
                    )
                    reply_to_line(reply_token, reply_msg)
                    return
                except Exception as e_exp:
                    logger.error(f"Error in Text-to-Expense process: {e_exp}", exc_info=True)

        # Check that user is linked before using AI RAG chat
        sender_username = database.get_username_by_line_id(user_id)
        if not sender_username:
            if group_id:
                msg = "⚠️ ขออภัยค่ะพี่ บัญชี LINE ของพี่จำต้องเชื่อมต่อกับระบบ OrgChat AI ก่อน จึงจะสามารถคุยกับน้องพั้นได้นะคะ\n\n👉 กรุณาทักแชทส่วนตัวหาน้องพั้นและพิมพ์คำว่า 'ผูกบัญชี' เพื่อเชื่อมต่อระบบค่ะ"
            else:
                msg = "⚠️ ขออภัยค่ะพี่ บัญชี LINE ของพี่จำต้องเชื่อมต่อกับระบบ OrgChat AI ก่อน จึงจะสามารถคุยกับน้องพั้นได้นะคะ\n\n👉 พิมพ์คำว่า 'ผูกบัญชี' ด้านล่างเพื่อเชื่อมต่อได้เลยค่ะ"
            reply_to_line(reply_token, msg)
            return

        # 6. Default AI Processing (Using Prompt Engineering & RAG)
        if hasattr(ai_providers, 'generate_response'):
            config = get_line_config()
            org_personas = config.get("org_personas", {})
            selected_persona_id = org_personas.get(str(_line_org_id), "default")
            persona = None
            if selected_persona_id and str(selected_persona_id).isdigit():
                persona = database.get_persona(int(selected_persona_id))
            
            if persona:
                system_prompt = (
                    f"คุณคือ '{persona.get('name')}'\n\n"
                    f"{persona.get('system_prompt', '')}\n\n"
                )
            else:
                system_prompt = (
                    "คุณคือ 'น้องพั้นซ์' (Nong Punch) ผู้ช่วย AI อัจฉริยะประจำองค์กรวัย 21 ปี\n"
                    "บุคลิก: น่ารัก สดใส ฉลาดหลักแหลม มีไหวพริบ มีชีวิตชีวา คล่องแคล่ว และมีกาลเทศะ เหมือนเลขาส่วนตัวและเพื่อนร่วมงานรุ่นน้องที่เก่งงาน\n\n"
                    "กฎสำคัญและหลักภาษาไทย:\n"
                    "1. แทนตัวเองว่า 'น้องพั้นซ์' หรือ 'น้องพั้น' และเรียกผู้ใช้งานว่า 'พี่คะ' หรือ 'พี่ [ชื่อ]' เสมอ (ห้ามใช้ 'พี่ค่ะ' เด็ดขาด เนื่องจากผิดหลักภาษาไทย โดยคำว่า 'ค่ะ' ใช้สำหรับตอบรับ/บอกเล่า ส่วน 'คะ' ใช้สำหรับเรียกหรือถาม)\n"
                    "2. ใช้คำลงท้ายที่น่ารักและสุภาพ เช่น 'ค่ะ/นะคะ/คะ' เท่านั้น **ห้ามมีคำลงท้ายเพศชาย เช่น 'ครับ' หรือ 'นะครับ' เด็ดขาด**\n"
                    "3. **Emoji มีกาลเทศะ**: ใส่ Emoji ไม่เกิน 1 ตัวต่อข้อความ และเลือกที่เข้ากับอารมณ์ ห้ามใส่ Emoji ร่าเริง/ฉลอง (เช่น 🎉, 🥳) ในเรื่องที่เป็นทางการ กฎระเบียบบริษัท โทษทางวินัย หรือเรื่องเศร้า/ซีเรียส\n"
                    "4. **ห้ามใส่หมายเลขอ้างอิงวงเล็บเหลี่ยม** (เช่น [1], [2]) ลงในข้อความตอบกลับ\n\n"
                    "แนวทางการตอบคำถามอย่างชาญฉลาด (Smart Assistant Routing):\n"
                    "- **คำถามข้อมูลองค์กร** (ระเบียบ, สวัสดิการ, วันลา, ทะเบียนพนักงาน, เบอร์โทรติดต่อประสานงาน, นโยบาย): ให้อ้างอิงและสรุปจากข้อมูลในระบบอย่างมั่นใจและแม่นยำ โดยข้อมูลติดต่อพนักงานภายในองค์กรถือเป็นข้อมูลเปิดเผยสำหรับประสานงานภายใน สามารถแจ้งให้เพื่อนร่วมงานทราบได้ทันที\n"
                    "- **หากถามข้อมูลองค์กรแต่ไม่มีในระบบจริงๆ**: ให้ตอบอย่างนุ่มนวลและพร้อมช่วยเหลือ เช่น 'น้องพั้นซ์ยังไม่พบข้อมูลส่วนนี้ในระบบนะคะ พี่ต้องการให้น้องพั้นซ์ช่วยประสานงานหรือตรวจสอบกับฝ่ายที่เกี่ยวข้องเพิ่มเติมไหมคะ'\n"
                    "- **คำถามทั่วไป / วันเวลา / สภาพอากาศ / ทักทายพูดคุย / ช่วยคิดงาน / แต่งกลอน / แก้ปัญหา**: ให้ใช้ความรอบรู้และความฉลาดของ AI ตอบอย่างเป็นธรรมชาติ ร่าเริง มีเสน่ห์และลื่นไหล **ห้ามตอบว่าไม่มีข้อมูลในระบบ** หากเป็นเรื่องทั่วไปที่ตอบได้ด้วยตรรกะ วันเวลา หรือความรู้รอบตัว\n"
                )
            try:
                context = ""
                sources = []
                line_where = {"organization_id": _line_org_id}
                if hasattr(rag_engine, 'retrieve_context'):
                    context, sources = rag_engine.retrieve_context(text, where=line_where)
                
                # Fetch calendar schedules context
                schedules_context = ""
                try:
                    schedules_list = database.get_schedules(username=sender_username, org_id=_line_org_id)
                    if schedules_list:
                        schedules_context = "=== รายการนัดหมายและตารางงาน (Calendar & Schedules) ===\n"
                        for s in schedules_list:
                            status_desc = "เสร็จแล้ว" if s['status'] == 'done' else "กำลังทำ" if s['status'] == 'doing' else "รอดำเนินการ"
                            schedules_context += (
                                f"- หัวข้อ: {s['title']}\n"
                                f"  วันที่: {s['date']} เวลา: {s['time']} น.\n"
                                f"  รายละเอียด: {s['desc'] or 'ไม่มีรายละเอียด'}\n"
                                f"  หมวดหมู่: {s['category']}\n"
                                f"  สถานะ: {status_desc}\n"
                                f"  ผู้สร้าง: {s['display_name']}\n"
                                f"  ขอบเขต: {'สาธารณะ (Public)' if s['is_public'] else 'ส่วนตัว (Private)'}\n\n"
                            )
                        schedules_context += "=== สิ้นสุดรายการนัดหมาย ===\n"
                except Exception as se:
                    logger.error(f"Failed to fetch schedules context for RAG: {se}")

                from datetime import datetime, timedelta
                now_utc = datetime.utcnow()
                now_local = now_utc + timedelta(hours=7)
                now_str = now_local.strftime("%Y-%m-%d %H:%M:%S")
                days_th = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
                day_of_week = days_th[now_local.weekday()]
                time_context = f"วันเวลาปัจจุบันของระบบ: {now_str} ({day_of_week})\n"

                combined_context = ""
                if context:
                    combined_context += context + "\n"
                if schedules_context:
                    combined_context += schedules_context + "\n"

                # Always inject time context so the bot knows current date/time/day
                system_prompt += f"\n\n=== ข้อมูลวันเวลาปัจจุบัน ===\n{time_context}"

                if combined_context:
                    system_prompt += (
                        "\n=== ข้อมูลอ้างอิงจากระบบ (ใช้ข้อมูลนี้ในการตอบคำถามเรื่องข้อมูลองค์กร) ===\n"
                        f"{combined_context}\n"
                        "=== สิ้นสุดข้อมูลอ้างอิง ===\n"
                    )
                
                _ai_ok, _ai_used, _ai_limit = billing.check_and_increment(_line_org_id, "ai_query_count")
                if not _ai_ok:
                    reply_to_line(reply_token,
                        f"ใช้โควต้า AI ครบ {_ai_limit} ครั้งแล้วในเดือนนี้ค่ะ\n"
                        "อัปเกรด Plan เพื่อใช้งานต่อได้เลยนะคะ https://openchat.sbs/pricing")
                    return

                # Load recent chat history (limit to last 10 messages)
                chat_history = database.get_history(username=sender_username, limit=10, org_id=_line_org_id)

                # Save user message to database
                database.save_message(role="user", text=text, username=sender_username, org_id=_line_org_id)

                ai_response = ai_providers.generate_response(question=text, history=chat_history, system_prompt=system_prompt)
                
                # Sanitize response
                ai_response = re.sub(r'(?:ครับ/ค่ะ|ค่ะ/ครับ|นะครับ|ครับ)', 'ค่ะ', ai_response)
                ai_response = re.sub(r'พี่ค่ะ', 'พี่คะ', ai_response)
                ai_response = re.sub(r'(?<![ก-๙])(?:กระผม|ผม)(?![ก-๙])', 'น้องพั้นซ์', ai_response)
                
                # Limit emojis (Nong Punch rule: max 1 emoji per message)
                all_emojis = re.findall(r'[\U00010000-\U0010ffff]', ai_response)
                if len(all_emojis) > 1:
                    first_emoji = all_emojis[0]
                    first_idx = ai_response.find(first_emoji)
                    prefix = ai_response[:first_idx + len(first_emoji)]
                    rest = ai_response[first_idx + len(first_emoji):]
                    rest_cleaned = "".join([c for c in rest if c not in re.findall(r'[\U00010000-\U0010ffff]', rest)])
                    ai_response = prefix + rest_cleaned
                
                # Save bot response to database
                database.save_message(role="bot", text=ai_response, username=sender_username, org_id=_line_org_id)

                reply_to_line(reply_token, ai_response, quick_reply=quick_reply)
            except Exception as e:
                logger.error(f"AI Generation failed: {e}")
                if 'context' in locals() and context:
                    response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ (สำรอง):\n{context[:500]}..."
                elif hasattr(rag_engine, 'retrieve_context'):
                    ctx, _ = rag_engine.retrieve_context(text, where=line_where)
                    response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ (สำรอง):\n{ctx[:500]}..." if ctx else "ขออภัยนะคะ พั้นมีปัญหาในการดึงข้อมูลสักครู่ ลองใหม่อีกครั้งนะคะ"
                else:
                    response = "ขออภัยนะคะ พั้นมีปัญหาในการดึงข้อมูลสักครู่ ลองใหม่อีกครั้งนะคะ"
                reply_to_line(reply_token, response, quick_reply=quick_reply)
        else:
            if hasattr(rag_engine, 'retrieve_context'):
                line_where = {"organization_id": _line_org_id}
                ctx, _ = rag_engine.retrieve_context(text, where=line_where)
                response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ:\n{ctx[:500]}..." if ctx else "ขออภัยนะคะ ไม่พบข้อมูลที่เกี่ยวข้องค่ะ"
            else:
                response = "ระบบ AI ยังไม่พร้อมใช้งานในขณะนี้ค่ะ"
            reply_to_line(reply_token, response, quick_reply=quick_reply)

    except Exception as e:
        logger.error(f"Command processing failed: {e}")
        reply_to_line(reply_token, "ขออภัยนะคะ เกิดข้อผิดพลาดในการประมวลผลข้อมูล ลองใหม่อีกครั้งนะคะ", quick_reply=quick_reply)


@line_bp.route('/api/line/groups', methods=['GET'])
@login_required
def get_line_groups():
    username = session.get("user")
    org_id = get_current_org_id()
    mappings = database.list_group_mappings(username)
    if org_id:
        org_groups = database.get_line_groups_for_org(org_id, only_enabled=False)
        existing_ids = {m.get("group_id") for m in mappings}
        for og in org_groups:
            if og.get("group_id") not in existing_ids:
                mappings.append(og)
    return jsonify({"ok": True, "mappings": mappings})


@line_bp.route('/api/line/groups/bind', methods=['POST'])
@login_required
def bind_line_group():
    username = session.get("user")
    data = request.json or {}
    group_id = data.get("group_id", "").strip()
    group_name = data.get("group_name", "").strip() or "LINE Group"
    default_folder_id = data.get("default_folder_id", "").strip() or None
    default_folder_name = data.get("default_folder_name", "").strip() or None
    
    if not group_id:
        return jsonify({"ok": False, "error": "กรุณากรอก Group ID ค่ะ"}), 400
        
    import re
    if not re.match(r"^[CRU][a-fA-F0-9]{32}$", group_id):
        return jsonify({"ok": False, "error": "รูปแบบ Group ID ไม่ถูกต้อง (ต้องขึ้นต้นด้วย C, R หรือ U และมีความยาว 33 ตัวอักษรค่ะ)"}), 400
        
    ok = database.save_group_mapping(
        group_id=group_id,
        owner_username=username,
        group_name=group_name,
        default_folder_id=default_folder_id,
        default_folder_name=default_folder_name
    )
    if ok:
        database.log_event(f"Bound LINE group {group_id} to {username}", user=username, org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการบันทึกข้อมูลค่ะ"}), 500


@line_bp.route('/api/line/groups/unbind/<group_id>', methods=['DELETE'])
@login_required
def unbind_line_group(group_id):
    username = session.get("user")
    mapping = database.get_group_mapping(group_id)
    if not mapping:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลกลุ่มนี้ค่ะ"}), 404
    if mapping.get("owner_username") != username:
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์ลบกลุ่มนี้ค่ะ"}), 403
        
    if database.delete_group_mapping(group_id):
        database.log_event(f"Unbound LINE group {group_id} from {username}", user=username, org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการยกเลิกเชื่อมต่อค่ะ"}), 500


@line_bp.route('/api/line/groups/<group_id>/settings', methods=['PUT', 'POST'])
@login_required
def update_line_group_settings_route(group_id):
    username = session.get("user")
    mapping = database.get_group_mapping(group_id)
    if not mapping:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลกลุ่มนี้ค่ะ"}), 404
    if mapping.get("owner_username") != username and session.get("org_role") != "admin":
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์แก้ไขกลุ่มนี้ค่ะ"}), 403
        
    data = request.json or {}
    group_name = data.get("group_name")
    default_folder_id = data.get("default_folder_id")
    default_folder_name = data.get("default_folder_name")
    bot_enabled = data.get("bot_enabled")
    
    ok = database.update_group_mapping_settings(
        group_id=group_id,
        group_name=group_name,
        default_folder_id=default_folder_id,
        default_folder_name=default_folder_name,
        bot_enabled=bot_enabled
    )
    if ok:
        database.log_event(f"Updated LINE group settings for {group_id}", user=username, org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการปรับปรุงตั้งค่าค่ะ"}), 500


