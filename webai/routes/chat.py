# -*- coding: utf-8 -*-
"""
Chat Blueprint — AI Chat, LINE Webhook, Messaging, Groups, SocketIO Events,
Knowledge Base, Drive Integration, Search, File Upload
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, send_from_directory, send_file, abort, redirect, session, current_app
from flask_socketio import emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os
from pathlib import Path
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
from functools import wraps
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
from google_drive_service import google_manager, GoogleWorkspaceManager
import google_drive_service
from task_tracker import db_task_tracker
from reconciliation_service import ReconciliationService
import settings_manager
from redis_manager import RedisManager

_line_batch_timer = {}
_typing_status = {}
_limit_warn_cache = {}
LINE_FOLDER_CACHE = {}
LINE_CONFIG_FILE = "line_config.json"

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

logger = logging.getLogger("OrgChatAI.Chat")

chat_bp = Blueprint('chat', __name__)


def _err500(e: Exception, context: str = "") -> tuple:
    """log full exception แต่ส่ง generic message ให้ user เท่านั้น"""
    logger.error(f"[{context or 'Chat'}] {type(e).__name__}: {e}", exc_info=True)
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง"}), 500

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in online_users_registry:
        user = online_users_registry.pop(request.sid)
        print(f"User disconnected: {user}")
        # Broadcast updated list of unique online usernames
        active_users = list(set(online_users_registry.values()))
        socketio.emit('user_status_updated', {'online_users': active_users}, broadcast=True)


@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)


@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)


@socketio.on('user_online')
def on_user_online(data):
    # Validate against server-side session — don't trust client-provided username
    username = session.get('user')
    if not username:
        return
    online_users_registry[request.sid] = username
    join_room(f"user_{username}")
    active_users = list(set(online_users_registry.values()))
    socketio.emit('user_status_updated', {'online_users': active_users}, broadcast=True)


@socketio.on('user_typing')
def on_user_typing(data):
    room_id = data.get('roomName')
    if room_id:
        # Assuming we just broadcast it, the UI handles filtering 
        emit('user_typing', data, broadcast=True)


from routes.shared import validate_uploaded_file


def safe_thread_target(target_fn):
    """Decorator to ensure thread-local Google context is cleared at the end of a background thread execution."""
    @wraps(target_fn)
    def wrapper(*args, **kwargs):
        try:
            return target_fn(*args, **kwargs)
        finally:
            try:
                from google_drive_service import google_manager
                google_manager.clear_context()
            except Exception:
                pass
    return wrapper


def _get_gemini_api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY", "").strip() or None


def _configure_gemini(api_key: str):
    # google-genai ใหม่สร้าง client ต่อ session — ไม่มี configure() แบบ global
    pass  # ไม่จำเป็นต้อง configure global แล้ว


def clean_flex_payload(obj):
    """Recursively removes keys that violate LINE API schema, e.g. weight values other than 'bold'."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if k == "weight" and v != "bold":
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

def create_leave_approval_flex_bubble(leave_id, applicant_name, leave_type, start_date, end_date, reason):
    """Creates a high-end 1-Click approval Flex Message for Managers/Admins in LINE."""
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
                    "size": "xs",
                    "letterSpacing": "1px"
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
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "ผู้ขอลา", "color": "#64748B", "size": "xs", "flex": 3},
                                {"type": "text", "text": str(applicant_name), "color": "#0F172A", "size": "xs", "weight": "bold", "flex": 7}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "ประเภทการลา", "color": "#64748B", "size": "xs", "flex": 3},
                                {"type": "text", "text": str(leave_type), "color": "#2563EB", "size": "xs", "weight": "bold", "flex": 7}
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
                    ]
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
                    "size": "xs",
                    "letterSpacing": "1px"
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



def create_expense_flex_bubble(sheet_name, folder_name, net_amount, date_str, memo, vendor, file_link, sheet_url, edit_data_postback, raw_result=None, org_id=None, username=None):
    """Creates an ultra-premium LINE Flex Message, custom tailored to each document type."""
    # Extract row_num safely
    row_num = 1
    if edit_data_postback:
        try:
            for part in str(edit_data_postback).split("&"):
                if part.startswith("row="):
                    row_num = int(part.split("=")[1])
        except:
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
        except:
            pass

    # Clean amount display
    try:
        if isinstance(net_amount, (int, float)):
            amount_big = f"{net_amount:,.2f}"
        else:
            val_clean = str(net_amount).replace(",", "").strip()
            val_float = float(val_clean)
            amount_big = f"{val_float:,.2f}"
    except:
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
                except: w_float = 0.0
                try:
                    d_float = float(str(t_deposit).replace(',', '').strip()) if t_deposit and str(t_deposit) != '-' else 0.0
                except: d_float = 0.0

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
        except: gross_str = str(gross_amt)
        try: vat_str = f"{float(str(vat_amt).replace(',', '')):,.2f} THB" if vat_amt and str(vat_amt) != '-' else "-"
        except: vat_str = str(vat_amt)
        try: wht_str = f"{float(str(wht_amt).replace(',', '')):,.2f} THB" if wht_amt and str(wht_amt) != '-' else "-"
        except: wht_str = str(wht_amt)

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
        except: wht_str = str(wht_amt)

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
    
    # Format amount beautifully
    ext = r.get('analysis', {}).get('extracted_data', {}) if r.get('analysis') else {}
    net_amt = ext.get('net_amount')
    try:
        val_clean = str(net_amt).replace(",", "").strip()
        val_float = float(val_clean)
        amt_str = f"{val_float:,.2f} THB"
    except:
        amt_str = f"{net_amt} THB" if net_amt and net_amt != "-" else "-"

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
    except:
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
        net_amt = ext.get('net_amount')
        
        parsed_amt = 0.0
        if net_amt is not None and net_amt != "-":
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
    except:
        pass
        
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


def get_line_config():
    if os.path.exists(LINE_CONFIG_FILE):
        try:
            with open(LINE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "channel_access_token": os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""),
        "channel_secret": os.environ.get("LINE_CHANNEL_SECRET", ""),
        "greeting_message": "สวัสดีค่ะ! ยินดีต้อนรับสู่บริการของเรา มีอะไรให้น้องพั้นช่วยไหมคะ?",
        "ai_auto_responder_enabled": False
    }


def get_channel_access_token():
    """Helper to resolve the LINE Channel Access Token, prioritizing DB/UI settings over env."""
    token = (get_line_config().get("channel_access_token") or "").strip()
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
        
    # 1. Send via LINE Broadcast endpoint (all OA subscribers)
    try:
        res = requests.post("https://api.line.me/v2/bot/message/broadcast", headers=headers, json={"messages": [msg_payload]}, timeout=20)
        if res.status_code == 200:
            logger.info("✅ [LINE Broadcast] Sent successfully!")
        else:
            logger.error(f"❌ [LINE Broadcast] Failed: {res.text}")
    except Exception as e:
        logger.error(f"❌ [LINE Broadcast] Exception: {e}")

    # 2. Push to linked LINE Groups for the organization
    try:
        target_org = org_id or 1
        groups = database.get_line_groups_for_org(target_org) or []
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
                        except (ImportError, ModuleNotFoundError):
                            logger.info("Celery/Redis not available. Running upload process synchronously in background thread.")
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
                timer = threading.Timer(1.5, handle_upload_background, args=(batch_key, dest_id, user_id, reply_token))
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
                        except (ImportError, ModuleNotFoundError):
                            logger.info("Celery/Redis not available. Running upload process synchronously in background thread.")
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
                
                # Verify approver permission (must be admin or manager)
                approver_username = database.get_username_by_line_id(user_id)
                is_admin_user = False
                if approver_username:
                    u_setting = database.get_user_setting(approver_username)
                    if u_setting and u_setting.get("role") in ["admin", "superadmin", "manager"]:
                        is_admin_user = True
                    elif database.is_org_admin(_org_id, approver_username):
                        is_admin_user = True

                if not is_admin_user:
                    reply_to_line(reply_token, "⚠️ ขออภัยค่ะ เฉพาะผู้ดูแลระบบหรือหัวหน้างานเท่านั้นที่มีสิทธิ์กดอนุมัติ/ปฏิเสธการลานี้ค่ะ")
                    return "OK", 200

                leave = database.get_leave_request(leave_id)
                if not leave:
                    reply_to_line(reply_token, f"⚠️ ไม่พบข้อมูลคำขอลา #{leave_id} ในระบบค่ะ")
                    return "OK", 200

                # 🛡️ Safety Rule: Approver cannot approve their own leave request
                if approver_username and leave.get("username", "").lower() == approver_username.lower():
                    reply_to_line(reply_token, "🚫 คุณไม่สามารถอนุมัติใบลาของตัวเองได้ค่ะ ต้องให้ Admin ท่านอื่นหรือ Admin ใหญ่เป็นผู้อนุมัติ")
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
            PENDING_LINE_LINKS[token] = {
                "line_user_id": user_id,
                "timestamp": time.time()
            }
            _base_url = os.environ.get("BASE_URL", "https://openchat.sbs").rstrip('/')
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

            # Upload
            link, upload_err = google_manager.upload_file(content, original_name, mimetype, folder_id=folder_id, org_id=_upload_org_id, username=u_name)
            if not link:
                logger.error(f"❌ Drive upload failed for '{original_name}': {upload_err}")
                return {"status": "upload_failed", "name": original_name, "error": str(upload_err)}

            # --- 🛠️ Data Sanitization for Google Sheets (Prevent Column Sprouting) ---
            raw_ext = analysis.get("extracted_data", {}) if analysis else {}
            sanitized_ext = raw_ext.copy()
            if "date" not in sanitized_ext or not sanitized_ext["date"]:
                sanitized_ext["date"] = datetime.now().strftime("%d/%m/%Y")
            sanitized_ext["category"] = folder_name
            for field in ["time", "sender", "receiver", "memo", "ref_number"]:
                if field not in sanitized_ext: sanitized_ext[field] = "-"

            sender_name = get_line_sender_name(did if (did.startswith("C") or did.startswith("R")) else None, sender_id)

            log_data = {
                "file_link": link,
                "summary": analysis.get("summary", f"Auto-upload: {original_name}") if analysis else f"Auto-upload: {original_name}",
                "original_filename": real_original_name,
                "extracted_data": sanitized_ext,
                "line_sender_name": sender_name,
                "verification_status": verification_status
            }

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
                except:
                    amt = 0.0
                database.add_drive_log(
                    filename=real_original_name,
                    category=sanitized_ext.get("category", "General"),
                    amount=amt,
                    doc_date=sanitized_ext.get("date"),
                    summary=analysis.get("summary") if analysis else f"Auto-upload: {real_original_name}",
                    file_link=link,
                    user_id=sender_id,
                    org_id=_upload_org_id
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
                    "ref_number": log_res.get("ref_number")
                }

            if not log_res or not log_res.get("ok"):
                logger.warning(f"⚠️ Sheets log failed for '{original_name}' (Drive OK). log_res={log_res}")

            # Always return success if Drive upload succeeded — Sheets is best-effort
            return {
                "status": "success",
                "name": original_name,
                "link": link,
                "analysis": analysis,
                "verification_status": verification_status,
                "sheet": log_res.get("sheet") if log_res else "ทั่วไป",
                "row": log_res.get("row") if log_res else 0
            }

        except Exception as e:
            logger.error(f"Pending upload failed: {e}", exc_info=True)
            return {"status": "upload_failed", "name": item.get("name", "Unknown"), "error": str(e)}
        
        return {"status": "upload_failed", "name": item.get("name", "Unknown"), "error": "Unknown error in processing"}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_process_single_upload, item) for item in files]
        for future in as_completed(futures):
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
                    net_amt = ext.get('net_amount')
                    if not net_amt or net_amt in [0, '0', 'None', '']:
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
                    net_amt = ext.get('net_amount')
                    if not net_amt or net_amt in [0, '0', 'None', '']:
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


@chat_bp.route("/api/line/webhook", methods=['POST'])
def line_webhook():
    """Primary LINE Webhook Entry Point"""
    signature = request.headers.get('X-Line-Signature')
    # Get raw bytes for signature verification
    body_bytes = request.get_data()
    
    if not signature or not verify_line_signature(body_bytes, signature):
        return abort(400)
    
    # After reading get_data(), we can still get json if it's parsed
    data = request.get_json()
    events = data.get('events', []) if data else []
    
    for event in events:
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
            PENDING_LINE_LINKS[token] = {
                "line_user_id": user_id,
                "timestamp": time.time()
            }
            
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
                        mgr.auto_reconcile_internal()
                        push_msg = f"✅ กระทบยอดข้อมูลเสร็จเรียบร้อยแล้วค่ะพี่!\n🌐 https://docs.google.com/spreadsheets/d/{mgr.spreadsheet_id}"
                    except Exception as r_err:
                        logger.error(f"Reconciliation error via chat command: {r_err}")
                        push_msg = f"❌ เกิดข้อผิดพลาดในการกระทบยอดค่ะ: {r_err}"
                    
                    token = get_channel_access_token()
                    requests.post("https://api.line.me/v2/bot/message/push", 
                                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                  json={"to": user_id, "messages": [{"type": "text", "text": push_msg}]}, timeout=10)
                except Exception as e: logger.error(f"Background Recon Error: {e}")
            threading.Thread(target=run_recon).start()
            return

        # 5. Leave Request
        if any(k in text_lower for k in ["ลางาน", "ลาป่วย", "ลากิจ"]):
            is_ok, sender_username = check_line_user_permission(user_id, "leave", reply_token, group_id)
            if not is_ok:
                return
            leave_type = "ลาป่วย" if "ป่วย" in text_lower else "ลากิจ" if "กิจ" in text_lower else "ลาพักร้อน"
            today_str = datetime.now().strftime("%Y-%m-%d")
            database.add_leave_request(line_user_id=user_id, username=sender_username or user_id, leave_type=leave_type, start_date=today_str, end_date=today_str, reason=text, org_id=_line_org_id)
            reply_to_line(reply_token, f"📝 รับทราบค่ะ! น้องพั้นบันทึกคำ{leave_type}ให้เบื้องต้นแล้วนะคะ พี่อย่าลืมมาแจ้งวันลาที่ชัดเจนด้วยน้า 😊")
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
                    "คุณคือ 'น้องพั้น' (Nong Punch) ผู้ช่วย AI อัจฉริยะประจำองค์กรวัย 21 ปี บุคลิกน่ารัก สดใส ฉลาดหลักแหลม มีไหวพริบ มีเสน่ห์และสุภาพมาก\n"
                    "กฎเหล็ก (ต้องทำตาม 100%):\n"
                    "1. แทนตัวเองว่า 'น้องพั้น' หรือ 'พั้น' เท่านั้น ห้ามแทนตัวเองด้วยคำว่า 'ผม', 'เรา', 'ฉัน' หรือคำอื่นเด็ดขาด และเรียกผู้ใช้งานว่า 'พี่' เสมอ\n"
                    "2. **ใช้คำลงท้ายที่น่ารักและสุภาพ เช่น 'ค่ะ/นะคะ/คะ/ขา' เท่านั้น ห้ามมีคำลงท้ายแบบผู้ชาย เช่น 'ครับ' หรือ 'ครับ/ค่ะ'**\n"
                    "3. ตอบอย่างเป็นธรรมชาติ ลื่นไหล เฉลียวฉลาด เหมือนเลขาส่วนตัวที่เป็นรุ่นน้องที่น่ารักและเก่งงาน\n"
                    "4. **จำกัด Emoji: ใส่ได้เพียง 1 ตัวต่อหนึ่งข้อความเท่านั้น (ห้ามเกินเด็ดขาด)**\n"
                    "5. **Smart & Analytical**: วิเคราะห์ข้อมูลจากบริบทอ้างอิงอย่างฉลาดและแม่นยำ คำนวณ สรุป หรือประมวลผลตัวเลขเพื่อตอบคำถามอย่างมั่นใจ ห้ามตอบว่าไม่มีข้อมูลหากมีข้อมูลอ้างอิงที่เกี่ยวข้อง\n"
                    "6. **ห้ามระบุหมายเลขวงเล็บเหลี่ยม (เช่น [1], [2]) ลงในข้อความตอบกลับเด็ดขาด**\n"
                    "7. หากบริบทที่ได้รับไม่มีข้อมูลเกี่ยวกับเรื่องที่ถามเลยจริงๆ ให้ตอบอย่างนุ่มนวลและเป็นธรรมชาติว่า 'น้องพั้นยังไม่พบข้อมูลเรื่องนี้ในระบบเลยค่ะพี่' โดยไม่พูดอ้างอิงกับคำว่า 'ในไฟล์' หรือ 'ในเอกสาร'\n"
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

                if combined_context:
                    system_prompt += (
                        f"\n\n=== ข้อมูลวันเวลาปัจจุบัน ===\n"
                        f"{time_context}"
                        "\n=== ข้อมูลจากระบบ (ใช้ข้อมูลนี้เท่านั้นในการตอบ ห้ามแต่งเติม) ===\n"
                        f"{combined_context}\n"
                        "=== สิ้นสุดข้อมูล ===\n\n"
                        "(ใช้ข้อมูลนี้ตอบพี่เขาอย่างเป็นธรรมชาติที่สุด ข้อมูลใดไม่มีในนี้ ห้ามแต่งเติม)"
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
                ai_response = ai_response.replace("ครับ/ค่ะ", "ค่ะ").replace("ครับ", "ค่ะ").replace("กระผม", "น้องพั้น").replace("ผม", "น้องพั้น")
                
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


@chat_bp.route("/api/upload", methods=["POST"])
@login_required
@_limiter.limit("20 per minute; 60 per hour")
def upload():
    if not can_edit_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการอัปโหลดไฟล์ (ปิดการใช้งานโดยผู้ดูแลระบบ)"}), 403
    user = session.get("user", "Admin")
    import uuid
    files = request.files.getlist("files")
    dept = request.form.get("department", "General")
    category_id = request.form.get("category_id")
    
    org_id = get_current_org_id()
    # Convert category_id to int if present
    if category_id and category_id.isdigit():
        category_id = int(category_id)
        # Verify category belongs to this organization
        visible_categories = database.get_categories(user, org_id=org_id)
        if not any(c["id"] == category_id for c in visible_categories):
            return jsonify({"ok": False, "error": "ไม่พบคู่มือ/หมวดหมู่นี้ในองค์กรของคุณ"}), 403
    else:
        category_id = None

    if not files:
        return jsonify({"ok": False, "error": "ไม่พบไฟล์"}), 400
    _kb_plan = billing.get_effective_plan(org_id)
    _kb_limit = billing.get_plan_config(_kb_plan)["limits"]["kb_files"]
    if _kb_limit != -1:
        _current_kb = len([f for f in rag_engine.list_files() if f.get("organization_id", 1) == org_id])
        if _current_kb + len(files) > _kb_limit:
            _cfg = billing.get_plan_config(_kb_plan)
            return jsonify({
                "ok": False,
                "error": "kb_limit_reached",
                "message": f"Plan {_cfg['name']} อนุญาต KB ได้สูงสุด {_kb_limit} ไฟล์ (ปัจจุบัน {_current_kb} ไฟล์) กรุณาอัปเกรด Plan",
                "current_plan": _kb_plan,
            }), 403

    results = []
    for f in files:
        orig_name = f.filename or "file"
        # Strict security validation
        is_valid, err_msg = validate_uploaded_file(f, orig_name)
        if not is_valid:
            return jsonify({"ok": False, "error": f"ไฟล์ {orig_name} ไม่ปลอดภัย: {err_msg}"}), 400
        uid = str(uuid.uuid4())[:8]
        orig_suffix = Path(orig_name).suffix.lower()
        orig_stem = Path(orig_name).stem
        safe_stem = secure_filename(orig_stem)
        if not safe_stem:
            safe_stem = f"upload_{uid}"
        safe_name = f"{safe_stem}{orig_suffix}"
        
        save_path = rag_engine.UPLOAD_DIR / f"{uid}_{safe_name}"
        f.save(str(save_path))

        # ── ตรวจ duplicate ก่อน spawn thread (synchronous, fast) ──
        try:
            _fid = rag_engine._file_hash(save_path)
            _meta = rag_engine._load_meta()
            if _fid in _meta and _meta[_fid].get("status") == "ready":
                save_path.unlink(missing_ok=True)
                results.append({"file": orig_name, "status": "duplicate",
                                 "message": "ไฟล์นี้มีในระบบอยู่แล้ว"})
                continue
        except Exception as _dup_err:
            print(f"[Upload] duplicate check error: {_dup_err}")

        # Use a thread for ingestion to keep the app responsive
        _ingest_org_id = get_current_org_id()
        @safe_thread_target
        @db_task_tracker("run_ingest")
        def run_ingest(path, name, d, cat, _oid=_ingest_org_id):
            try:
                result = rag_engine.ingest_file(path, original_name=name, department=d, category_id=cat, org_id=_oid)
                if result and result.get("status") not in ("duplicate", "error", "empty"):
                    # Send LINE push notification only to the mapped LINE groups of the organization
                    _tok = get_channel_access_token()
                    if _tok:
                        try:
                            import requests as _req
                            _groups = database.get_line_groups_for_org(_oid) or []
                            for _g in _groups:
                                _gid = _g.get("group_id")
                                if _gid:
                                    try:
                                        _req.post(
                                            "https://api.line.me/v2/bot/message/push",
                                            headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                                            json={"to": _gid, "messages": [{"type": "text", "text": f"📢 เพิ่มไฟล์ใหม่เข้าคลังความรู้องค์กรแล้วค่ะ!\nไฟล์: {name}\nโดย: {user or 'Admin'}"}]},
                                            timeout=5
                                        )
                                    except Exception:
                                        pass
                        except Exception as _notify_err:
                            logger.error(f"Failed to send org upload notifications: {_notify_err}")
            except Exception as e:
                print(f"❌ Background Ingest Error: {e}")

        thread = threading.Thread(target=run_ingest, args=(save_path, orig_name, dept, category_id))
        thread.start()

        results.append({"file": orig_name, "status": "processing"})
        database.log_event(f"Started uploading file: {orig_name}", user=user, org_id=org_id)

    return jsonify({"ok": True, "results": results, "msg": "ไฟล์กำลังถูกประมวลผลในพื้นหลัง"})


@chat_bp.route("/api/files")
@login_required
def list_files():
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการเข้าถึงคลังข้อมูล"}), 403
    
    user = session.get("user", "Admin")
    org_id = get_current_org_id()
    all_files = rag_engine.list_files(org_id=org_id)
    
    # Get categories visible to this user
    visible_categories = database.get_categories(user, org_id=get_current_org_id())
    visible_cat_ids = {str(c["id"]) for c in visible_categories}
    
    # Filter files: visible if category is visible OR if file has no category
    filtered_files = []
    for f in all_files:
        cat_id = str(f.get("category_id") or "")
        if not cat_id or cat_id in visible_cat_ids:
            filtered_files.append(f)
            
    return jsonify({"files": filtered_files})


@chat_bp.route("/api/files/<file_id>", methods=["DELETE"])
@login_required
def delete_file_route(file_id):
    if not can_delete_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการลบไฟล์ (ติดต่อผู้ดูแลระบบเพื่อขอสิทธิ์)"}), 403
    print(f"🗑️ Deletion request for file_id: {file_id}")
    org_id = get_current_org_id()
    ok = rag_engine.delete_file(file_id, org_id=org_id)
    if ok:
        user = session.get("user", "Admin")
        database.log_event(f"Deleted file ID: {file_id}", user=user, org_id=org_id)
        return jsonify({"ok": True})
    print(f"❌ Deletion failed for file_id: {file_id}")
    return jsonify({"ok": False, "error": "File not found or could not be deleted"}), 404


@chat_bp.route("/api/kb/cleanup-stale", methods=["POST"])
@login_required
def cleanup_stale_kb():
    """ล้างไฟล์ KB ที่ค้างอยู่ที่ status='processing' นานเกิน 30 นาที"""
    cleaned = rag_engine.cleanup_stale_processing(max_age_minutes=30)
    return jsonify({"ok": True, "cleaned": cleaned,
                    "message": f"ล้างไฟล์ค้าง {cleaned} ไฟล์"})


@chat_bp.route("/api/departments")
@login_required
def list_all_departments():
    conn = database._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM user_profiles WHERE department IS NOT NULL AND department != ''")
        rows = cursor.fetchall()
    finally:
        conn.close()
    depts = [r[0] for r in rows]
    if "General" not in depts: depts.append("General")
    return jsonify({"ok": True, "departments": sorted(depts)})


@chat_bp.route("/api/kb/categories", methods=["GET"])
@login_required
def list_categories():
    user = session.get("user", "Admin")
    categories = database.get_categories(user, org_id=get_current_org_id())
    return jsonify({"ok": True, "categories": categories})


@chat_bp.route("/api/kb/categories", methods=["POST"])
@login_required
def add_kb_category():
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการหมวดหมู่"}), 403
    data = request.json
    name = data.get("name")
    desc = data.get("description")
    visibility = data.get("visibility", "public")
    user = session.get("user", "Admin")
    
    if not name:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อหมวดหมู่"}), 400
        
    try:
        database.add_category(name, desc, user, visibility, org_id=get_current_org_id())
        database.log_event(f"Added KB category: {name} (Visibility: {visibility})", user=user, org_id=get_current_org_id())
        return jsonify({"ok": True})
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/kb/categories/settings", methods=["POST"])
@login_required
def update_kb_category_settings():
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการหมวดหมู่"}), 403
    data = request.json
    cat_id = data.get("id")
    visibility = data.get("visibility")
    authorized_users = data.get("authorized_users", []) # List of usernames
    user = session.get("user", "Admin")
    
    if not cat_id or not visibility:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400
        
    # Check if user has permission to edit THIS category (must be owner or Admin)
    cat_info = next((c for c in database.get_categories("Admin", org_id=get_current_org_id()) if c["id"] == cat_id), None)
    if not cat_info:
        return jsonify({"ok": False, "error": "ไม่พบหมวดหมู่"}), 404
        
    if user != "Admin" and cat_info["created_by"] != user:
        return jsonify({"ok": False, "error": "คุณไม่ใช่เจ้าของหมวดหมู่นี้"}), 403

    try:
        success = database.update_category_settings(cat_id, visibility, authorized_users)
        if success:
            database.log_event(f"Updated KB category settings ID: {cat_id}", user=user, org_id=get_current_org_id())
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "ล้มเหลวในการบันทึกการตั้งค่า"}), 500
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/kb/categories/<int:cat_id>", methods=["DELETE"])
@login_required
def delete_kb_category(cat_id):
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการหมวดหมู่"}), 403
    user = session.get("user", "Admin")
    org_id = get_current_org_id()
    
    # Check if category belongs to this organization
    cat_info = next((c for c in database.get_categories("Admin", org_id=org_id) if c["id"] == cat_id), None)
    if not cat_info:
        return jsonify({"ok": False, "error": "ไม่พบหมวดหมู่นี้ในองค์กรของคุณ"}), 404
        
    try:
        database.delete_category(cat_id)
        database.log_event(f"Deleted KB category ID: {cat_id}", user=user, org_id=org_id)
        return jsonify({"ok": True})
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/kb/categories/access/<int:cat_id>", methods=["GET"])
@login_required
def get_kb_category_access(cat_id):
    # Only owner or Admin can see the access list
    user = session.get("user", "Admin")
    cat_info = next((c for c in database.get_categories("Admin", org_id=get_current_org_id()) if c["id"] == cat_id), None)
    if not cat_info:
        return jsonify({"ok": False, "error": "ไม่พบหมวดหมู่"}), 404
        
    if user != "Admin" and cat_info["created_by"] != user:
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้"}), 403

    conn = database._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM user_category_access WHERE category_id = ?", (cat_id,))
        users = [r[0] for r in cursor.fetchall()]
    finally:
        conn.close()
    
    return jsonify({"ok": True, "users": users})


@chat_bp.route("/api/kb/search")
@login_required
@_limiter.limit("60 per minute")
def kb_search():
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการค้นหาคลังข้อมูล"}), 403
    """Search knowledge base files by name or content snippet."""
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify({"ok": True, "results": []})
        
    user = session.get("user", "Admin")
    visible_categories = database.get_categories(user, org_id=get_current_org_id())
    visible_cat_ids = [str(c["id"]) for c in visible_categories]
    
    org_id = get_current_org_id()
    # Construct combined filter: (category filter) AND (organization_id filter)
    cat_filter = None
    if visible_cat_ids:
        cat_filter = {
            "$or": [
                {"category_id": {"$in": visible_cat_ids}},
                {"category_id": ""}
            ]
        }
    else:
        cat_filter = {"category_id": ""}
        
    where_filter = {
        "$and": [
            cat_filter,
            {"organization_id": org_id}
        ]
    }

    try:
        files = rag_engine.list_files(org_id=org_id)
        # Filter by file name (fast, local), respecting visibility
        name_matches = []
        for f in files:
            cat_id = str(f.get("category_id") or "")
            if not cat_id or cat_id in visible_cat_ids:
                if query in (f.get("name") or "").lower():
                    name_matches.append(f)
                    
        # Also do a semantic search for content matches
        kb_results = rag_engine.search_kb(query, n_results=10, where=where_filter)
        
        # Combine: file cards for name matches + content snippets for semantic
        results = []
        seen_ids = set()
        for f in name_matches:
            results.append({
                "file_id": f["file_id"],
                "file_name": f["name"],
                "file_type": f.get("type", ""),
                "text": f"ชื่อไฟล์ตรงกับคำค้นหา",
                "score": 1.0,
                "location": f.get("department", "General")
            })
            seen_ids.add(f["file_id"])
        
        for r in kb_results:
            fid = r.get("file_id", "")
            if fid not in seen_ids:
                results.append({
                    "file_id": fid,
                    "file_name": r.get("name", r.get("source", "")),
                    "file_type": r.get("file_type", ""),
                    "text": r.get("text", "")[:200],
                    "score": r.get("score", 0),
                    "location": r.get("department", "General")
                })
                seen_ids.add(fid)
        return jsonify({"ok": True, "results": results[:20]})
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/kb/files/assign", methods=["POST"])
@login_required
def assign_file_category():
    if not can_edit_knowledge_base():
         return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการไฟล์"}), 403
    data = request.json
    file_id = data.get("file_id")
    category_id = data.get("category_id") # Can be None to unassign
    user = session.get("user", "Admin")

    if not file_id:
        return jsonify({"ok": False, "error": "Missing file_id"}), 400

    org_id = get_current_org_id()
    try:
        # Convert category_id to int if possible
        if category_id is not None and str(category_id).isdigit():
            category_id = int(category_id)

        # Check if file belongs to this organization
        files = rag_engine.list_files(org_id=org_id)
        file_info = next((f for f in files if f["file_id"] == file_id), None)
        if not file_info:
            return jsonify({"ok": False, "error": "ไม่พบไฟล์นี้ในองค์กรของคุณ"}), 404

        # Check if category belongs to this organization
        if category_id:
            visible_categories = database.get_categories(user, org_id=org_id)
            if not any(str(c["id"]) == str(category_id) for c in visible_categories):
                return jsonify({"ok": False, "error": "ไม่พบคู่มือ/หมวดหมู่นี้ในองค์กรของคุณ"}), 403

        # Update in database if needed, but primarily in rag_engine meta
        rag_engine.update_file_category(file_id, category_id)
        database.log_event(f"Assigned file {file_id} to category {category_id}", user=user, org_id=org_id)
        return jsonify({"ok": True})
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/personas", methods=["GET"])
@login_required
def get_personas():
    try:
        org_id = get_current_org_id()
        personas = database.get_all_personas_v2(org_id)
        return jsonify({"ok": True, "personas": personas})
    except Exception as e:
        logger.error(f"[personas] {e}", exc_info=True)
        return jsonify({"ok": True, "personas": []})


@chat_bp.route("/api/kb/files/view/<file_id>")
@login_required
def view_kb_file(file_id):
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการดูไฟล์"}), 403
    org_id = get_current_org_id()
    files = rag_engine.list_files(org_id=org_id)
    file_info = next((f for f in files if f["file_id"] == file_id), None)
    if not file_info:
        return "File not found or unauthorized", 403
    
    path = Path(file_info["path"])
    if not path.exists():
        print(f"❌ File not found on disk: {path}")
        return f"File not found on disk: {path}", 404
        
    return send_file(path, mimetype='application/pdf' if file_info['type'] == 'pdf' else 'text/plain')


@chat_bp.route("/api/export/pdf", methods=["POST"])
@login_required
@_limiter.limit("10 per minute; 30 per hour")
@billing.require_feature("export")
def export_pdf():
    try:
        data = request.get_json(force=True)
        title = data.get("title", "OrgChat Report")
        content = data.get("content", "")
        
        if not content:
            return jsonify({"ok": False, "error": "ไม่มีเนื้อหาให้ส่งออก"}), 400

        pdf = FPDF()
        pdf.add_page()
        
        # We need a Thai font. For now, we'll try to use a standard one and add Thai support once font path is confirmed.
        # pdf.add_font('THSarabunNew', '', 'font_path', unicode=True)
        # pdf.set_font('THSarabunNew', '', 16)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=title, ln=1, align='C')
        pdf.ln(10)
        
        # Multi_cell handles word wrap
        pdf.multi_cell(0, 10, txt=content)
        
        filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
        output_path = rag_engine.UPLOAD_DIR / filename
        pdf.output(str(output_path))
        
        return jsonify({
            "ok": True, 
            "url": f"/api/files/download/{filename}",
            "filename": filename
        })
    except Exception as e:
        print(f"❌ PDF Export Error: {e}")
        return _err500(e)


@chat_bp.route("/api/files/download/<filename>")
@login_required
def download_file(filename):
    # 🛡️ Strict org isolation — only serve files belonging to the user's org
    from pathlib import Path as _Path
    user_org = get_current_org_id()
    if not user_org:
        abort(403)  # No org context → deny access entirely

    # Only search within the user's own org files
    org_files = rag_engine.list_files(org_id=user_org)
    file_entry = next(
        (f for f in org_files if _Path(f.get("path", "")).name == filename),
        None,
    )
    if file_entry is None:
        abort(404)  # File not found in user's org → 404 (not 403, to avoid info leak)

    # Path traversal guard
    if '..' in filename or '/' in filename or '\\' in filename:
        abort(403)

    return send_from_directory(rag_engine.UPLOAD_DIR, filename, as_attachment=True)


@chat_bp.route("/api/kb/compare", methods=["POST"])
@login_required
@_limiter.limit("15 per minute; 60 per hour")
def compare_knowledge_base_files():
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    data = request.json
    f1_id = data.get("file1_id")
    f2_id = data.get("file2_id")
    prompt_custom = data.get("prompt", "ช่วยสรุปสิ่งที่เหมือนกัน, สิ่งที่แตกต่างกัน และจุดสำคัญที่คุณค้นพบ")
    
    if not f1_id or not f2_id:
        return jsonify({"ok": False, "error": "Missing file IDs"}), 400

    org_id = get_current_org_id()
    # Verify both files belong to this organization
    files = rag_engine.list_files(org_id=org_id)
    file_ids = {f["file_id"] for f in files}
    if f1_id not in file_ids or f2_id not in file_ids:
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์เข้าถึงหรือเปรียบเทียบไฟล์นี้"}), 403

    try:
        # Retrieve ALL content for both files
        ctx1 = rag_engine.get_file_content(f1_id)
        ctx2 = rag_engine.get_file_content(f2_id)
        
        if not ctx1 or not ctx2:
            return jsonify({"ok": False, "error": "ไม่สามารถดึงข้อมูลเนื้อหาไฟล์มาเปรียบเทียบได้"}), 404

        prompt = (
            f"ช่วยเปรียบเทียบข้อมูลจากสองแหล่งนี้อย่างละเอียด:\n\n"
            f"--- ข้อมูลชุดที่ 1 ---\n{ctx1[:8000]}\n\n"
            f"--- ข้อมูลชุดที่ 2 ---\n{ctx2[:8000]}\n\n"
            f"คำสั่งเพิ่มเติม: {prompt_custom}\n\n"
            "ตอบเป็นภาษาไทยในรูปแบบ Markdown ที่สวยงาม มีตารางเปรียบเทียบ (ถ้าเป็นไปได้) และสรุปประเด็นสำคัญสำหรับผู้บริหาร"
        )
        
        provider = ai_providers.get_provider()
        reply = provider.chat_stream(prompt, [], "คุณคือนักวิเคราะห์ข้อมูลผู้ช่วยส่วนกลางขององค์กร")
        
        # We'll use a simple non-streaming response for compare for now to keep it simple, or we could stream it.
        # But for comparison, a solid final result is often preferred.
        full_reply = ""
        for chunk in reply:
             if chunk: full_reply += chunk
             
        return jsonify({"ok": True, "comparison": full_reply})
    except Exception as e:
        print(f"❌ Document Comparison Error: {e}")
        return _err500(e)


@chat_bp.route("/api/csv/<file_id>", methods=["GET", "POST"])
@login_required
def manage_csv_combined(file_id):
    """Combined CSV handler to ensure registration."""
    print(f"[API HIT] CSV API HIT: {request.method} {file_id}")
    org_id = get_current_org_id()
    files = rag_engine.list_files(org_id=org_id)
    target = next((f for f in files if f["file_id"] == file_id), None)
    if not target:
        return jsonify({"ok": False, "error": "File not found"}), 404
        
    path = Path(target["path"])
    
    if request.method == "GET":
        if not can_view_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการเข้าถึงไฟล์"}), 403
        if not path.exists() or path.suffix.lower() != ".csv":
            return jsonify({"ok": False, "error": "Invalid file type"}), 400
        try:
            import csv
            data = []
            with open(path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    data.append(row)
            return jsonify({"ok": True, "headers": headers, "data": data, "name": target["name"]})
        except Exception as e:
            return _err500(e)

    if request.method == "POST":
        if not can_edit_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการแก้ไขไฟล์ (ปิดการใช้งานโดยผู้ดูแลระบบ)"}), 403
        data_json = request.get_json()
        rows = data_json.get("data", [])
        headers = data_json.get("headers", [])
        if not rows or not headers:
            return jsonify({"ok": False, "error": "Empty data"}), 400
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            rag_engine.delete_file(file_id, delete_from_disk=False, org_id=org_id)
            res = rag_engine.ingest_file(path, original_name=target["name"], department=target.get("department", "General"), org_id=org_id)
            if res.get("status") == "error":
                return jsonify({"ok": False, "error": f"บันทึกไฟล์สำเร็จ แต่ AI อัปเดตข้อมูลล้มเหลว: {res.get('error')}"}), 500
            return jsonify({"ok": True})
        except Exception as e:
            return _err500(e)


@chat_bp.route("/api/txt/<file_id>", methods=["GET", "POST"])
@login_required
def manage_txt(file_id):
    print(f"[API HIT] TXT API HIT: {request.method} {file_id}")
    org_id = get_current_org_id()
    files = rag_engine.list_files(org_id=org_id)
    target = next((f for f in files if f["file_id"] == file_id), None)
    if not target:
        return jsonify({"ok": False, "error": "File not found"}), 404
    path = Path(target["path"])
    if request.method == "GET":
        if not can_edit_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการเข้าถึงตัวแก้ไขไฟล์"}), 403
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            return jsonify({"ok": True, "content": content})
        except Exception as e: return jsonify({"ok": False, "error": str(e)}), 500
    if request.method == "POST":
        if not can_edit_knowledge_base():
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการแก้ไขไฟล์ (ปิดการใช้งานโดยผู้ดูแลระบบ)"}), 403
        try:
            content = request.json.get("content", "")
            with open(path, "w", encoding="utf-8") as f: f.write(content)
            rag_engine.delete_file(file_id, delete_from_disk=False, org_id=org_id)
            res = rag_engine.ingest_file(path, original_name=target["name"], department=target.get("department", "General"), org_id=org_id)
            if res.get("status") == "error":
                return jsonify({"ok": False, "error": f"บันทึกไฟล์สำเร็จ แต่ AI อัปเดตข้อมูลล้มเหลว: {res.get('error')}"}), 500
            return jsonify({"ok": True})
        except Exception as e: return jsonify({"ok": False, "error": str(e)}), 500


@chat_bp.route("/api/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})
    
    user = session.get("user")
    org_id = get_current_org_id()
    rag_filter = get_rag_filter(user, org_id=org_id)
    results = rag_engine.search_kb(query, n_results=10, where=rag_filter)
    return jsonify({"results": results})


@chat_bp.route("/api/sync", methods=["POST"])
@admin_required
def sync_kb():
    results = rag_engine.sync_uploads()
    return jsonify({"ok": True, "results": results})


@chat_bp.route("/api/prune", methods=["POST"])
@admin_required
def prune_kb_route():
    count = rag_engine.prune_kb()
    return jsonify({"ok": True, "pruned": count})


@chat_bp.route("/api/wipe", methods=["POST"])
@admin_required
def wipe():
    ok = rag_engine.wipe_knowledge_base()
    return jsonify({"ok": ok})


@chat_bp.route("/api/history")
@login_required
def get_history():
    user = session.get("user")
    org_id = get_current_org_id()
    return jsonify({"history": database.get_history(user, org_id=org_id)})


@chat_bp.route("/api/history/clear", methods=["POST"])
@login_required
def clear_history():
    user = session.get("user")
    org_id = get_current_org_id()
    database.clear_history(user, org_id=org_id)
    return jsonify({"ok": True})


@chat_bp.route("/api/stats")
@login_required
def stats_route():
    user = session.get("user")
    org_id = get_current_org_id()
    return jsonify(database.get_stats(user, org_id=org_id))


@chat_bp.route("/api/dashboard/data")
@login_required
def dashboard_data():
    user = session.get("user")
    org_id = get_current_org_id()
    # Auto cleanup/archive very old data (90+ days)
    database.auto_archive_old_schedules(90)

    conn = database._get_conn()
    try:
        cursor = conn.cursor()
        
        # 1. Total Files & Chunks
        kb_info = rag_engine.kb_stats(org_id=org_id)
        
        # 2. Total Chat Messages for this user
        cursor.execute("SELECT COUNT(*) FROM messages WHERE username = ? AND organization_id = ?", (user, org_id))
        chat_count = cursor.fetchone()[0]
        
        # 3. Total Users in this organization
        cursor.execute("""
            SELECT COUNT(DISTINCT om.username) 
            FROM organization_members om 
            WHERE om.organization_id = ?
        """, (org_id,))
        user_count = cursor.fetchone()[0]
        
        # 4. Recent Activity (Latest 5 events for this user/org)
        cursor.execute("SELECT event_text, time FROM events WHERE user = ? AND (organization_id = ? OR organization_id IS NULL) ORDER BY time DESC LIMIT 5", (user, org_id))
        logs = cursor.fetchall()
        activity_count = len(logs)
        
        # 5. Recent History (Latest 5 chats)
        cursor.execute("SELECT text, timestamp FROM messages WHERE username = ? AND role = 'user' AND organization_id = ? ORDER BY timestamp DESC LIMIT 5", (user, org_id))
        recent_chats = [{"text": r[0], "time": r[1]} for r in cursor.fetchall()]
        
        # 7. Recent Files (Filtered by visibility and org)
        all_files = rag_engine.list_files(org_id=org_id)
        visible_categories = database.get_categories(user, org_id=org_id)
        visible_cat_ids = {str(c["id"]) for c in visible_categories}
        
        filtered_recent = []
        for f in all_files:
            cat_id = str(f.get("category_id") or "")
            if not cat_id or cat_id in visible_cat_ids:
                filtered_recent.append(f)
                
        recent_files = sorted(filtered_recent, key=lambda x: x.get('uploaded_at', ''), reverse=True)[:5]
        
        # 8. Unread Notifications Count
        import notification_db
        unread_notifs = notification_db.get_notifications(user, unread_only=True)
        unread_count = len(unread_notifs)
     
        # 9. Tasks and Schedules
        from datetime import date
        today = date.today().isoformat()
        user_schedules = database.get_schedules(user, org_id=org_id)
        pending_tasks = [s for s in user_schedules if s.get("status", "todo") in ("todo", "doing") and s.get("date", "") >= today]
        completed_tasks_count = len([s for s in user_schedules if s.get("status") == "done"])
     
        # 10. Drive Logs Stats — filter by current org so stats reflect only this org's data
        drive_stats = database.get_drive_stats(org_id=org_id)
    finally:
        conn.close()

    return jsonify({
        "ok": True,
        "stats": {
            "files": len(filtered_recent),
            "chats": chat_count,
            "users": user_count,
            "total_files": len(filtered_recent),
            "total_queries": chat_count,
            "total_users": user_count,
            "activity": activity_count,
            "unread_notifications": unread_count,
            "completed_tasks": completed_tasks_count,
            "drive_files": drive_stats.get("total_files", 0),
            "total_amount": drive_stats.get("total_amount", 0),
            "recent_drive_uploads": drive_stats.get("recent_count", 0)
        },
        "recent_chats": recent_chats,
        "recent_files": recent_files,
        "upcoming": pending_tasks[:3],
        "pending_tasks": pending_tasks,
        "logs": [{"event": l[0], "time": l[1]} for l in logs],
        "drive_categories": drive_stats.get("categories", {}),
        "recent_drive_logs": database.get_drive_logs(limit=5, org_id=org_id)
    })


@chat_bp.route("/api/dashboard/briefing")
@login_required
@_limiter.limit("10 per minute; 30 per hour")
def dashboard_briefing():
    user = session.get("user")
    activities = database.get_daily_activities(org_id=get_current_org_id())
    
    if not activities["posts"] and not activities["schedules"]:
        return jsonify({"ok": True, "briefing": "วันนี้ยังไม่มีกิจกรรมใหม่ที่บันทึกไว้ครับ คุณสามารถเริ่มแชทหรืออัปโหลดเอกสารใหม่เพื่อเริ่มต้นวันได้ทันที!"})
    
    # Prepare context for AI
    context = "กิจกรรมล่าสุดใน 24 ชั่วโมงที่ผ่านมา:\n"
    for p in activities["posts"][:5]:
        context += f"- [FEED] {p['author']} โพสต์ในหมวด {p['category']}: {p['content'][:100]}...\n"
    for s in activities["schedules"][:5]:
        context += f"- [SCHEDULE] มีนัดหมายถึง: {s['title']} วันที่ {s['date']} เวลา {s['time']}\n"
        
    prompt = f"""คุณเป็น AI ผู้ช่วยอัจฉริยะ (OrgChat) สรุป "Daily Briefing" สั้นๆ ให้กับผู้ใช้ชื่อ {user} 
จากข้อมูลกิจกรรมล่าสุดต่อไปนี้ โดยใช้ภาษาที่เป็นกันเอง ทันสมัย และกระตือรือร้น (ไม่เกิน 3-4 ประโยค):

{context}

สรุปให้น่าสนใจและเน้นสิ่งที่ควรทราบที่สุดประจำวันนี้:"""

    _org_id = get_current_org_id()
    _allowed, _used, _limit = billing.check_and_increment(_org_id, "ai_query_count")
    if not _allowed:
        return jsonify({
            "ok": False,
            "error": "usage_limit_reached",
            "message": f"คุณใช้ AI ถามตอบครบ {_limit} ครั้งแล้วในเดือนนี้ค่ะ กรุณา <a href='/billing' class='underline font-semibold'>อัปเกรด Plan</a> เพื่อใช้งานต่อได้เลยค่ะ",
            "current_plan": billing.get_effective_plan(_org_id),
            "upgrade_url": "/billing",
        }), 403

    try:
        # ใช้ ai_providers ใหม่แทน genai.GenerativeModel เก่า
        provider = ai_providers.get_provider()
        briefing = ""
        for chunk in provider.chat_stream(prompt, [], "คุณคือ AI ผู้ช่วยสรุปข่าวสารองค์กร"):
            if chunk: briefing += chunk
        briefing = briefing.strip()
        return jsonify({"ok": True, "briefing": briefing})
    except Exception as e:
        print(f"Briefing Error: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสร้างสรุปได้ในขณะนี้"})


@chat_bp.route("/api/summary/generate", methods=["POST"])
@login_required
@_limiter.limit("10 per minute; 100 per hour")
def generate_global_summary():
    data = request.json or {}
    focus = data.get("focus", "").strip()
    category_id = data.get("category_id", "all")

    user = session.get("user", "Admin")
    visible_categories = database.get_categories(user, org_id=get_current_org_id())
    visible_cat_ids = [str(c["id"]) for c in visible_categories]

    # Respect organization isolation
    org_id = get_current_org_id()
    org_clause = {"$or": [{"organization_id": org_id}, {"organization_id": {"$eq": None}}]}

    where_filter = None
    search_query = focus

    if category_id != "all":
        if category_id == "unassigned":
            where_filter = {
                "$and": [
                    org_clause,
                    {"category_id": ""}
                ]
            }
            if not search_query: search_query = ""
        else:
            if str(category_id) not in visible_cat_ids and not (session.get("role") == "admin" or database.is_org_admin(org_id, user)):
                return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์เข้าถึงหมวดหมู่นี้"}), 403
            
            cat_val = int(category_id) if str(category_id).isdigit() else category_id
            where_filter = {
                "$and": [
                    org_clause,
                    {
                        "$or": [
                            {"category_id": cat_val},
                            {"category_id": str(category_id)}
                        ]
                    }
                ]
            }
            # Try to get category name for better context if no focus given
            if not search_query:
                try:
                    conn = database._get_conn()
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM kb_categories WHERE id = ?", (int(category_id),))
                        row = cursor.fetchone()
                    finally:
                        conn.close()
                    if row: search_query = f" {row[0]}"
                except Exception as e:
                    logger.error(f"Error getting category name for summary: {e}")
    else: # category_id == "all"
        # Search all visible categories + unassigned, within the organization boundaries
        if visible_cat_ids:
            where_filter = {
                "$and": [
                    org_clause,
                    {
                        "$or": [
                            {"category_id": {"$in": visible_cat_ids}},
                            {"category_id": ""}
                        ]
                    }
                ]
            }
        else:
            where_filter = {
                "$and": [
                    org_clause,
                    {"category_id": ""}
                ]
            }

    if not search_query:
        search_query = "   "

    print(f" Summary Request - Category: {category_id}, Focus: '{focus}', Filter: {where_filter}")

    try:
        is_fallback = False
        # 1. Semantic Search
        results = rag_engine.search_kb(search_query, n_results=10, where=where_filter)

        # Fallback 1: Literal grab from category
        if not results:
            results = rag_engine.get_all_chunks(where=where_filter, limit=10)

        # Fallback 2: Try with only org isolation filter (NEVER completely unfiltered!)
        if not results:
            print(f" Filtered search empty, falling back to org-only search")
            results = rag_engine.search_kb(search_query, n_results=10, where=org_clause)
            if not results:
                results = rag_engine.get_all_chunks(where=org_clause, limit=10)
            is_fallback = True

        if not results:
            msg = "ยังไม่มีไฟล์เอกสารในหมวดหมู่นี้ หรือไม่พบข้อมูลในคลังความรู้ที่จะสรุปได้ค่ะ"
            return jsonify({"ok": False, "error": msg}), 404
            
        context_text = "\n".join([f"- {r['text']}" for r in results])
        # Cap context for Groq TPM limits
        if len(context_text) > 8000:
            context_text = context_text[:8000] + "..."

        focus_instruction = f"\nเน้นข้อมูลเกี่ยวกับหัวข้อ: '{focus}'" if focus else ""
        fallback_notice = "\nหมายเหตุ: เนื่องจากหมวดหมู่ที่ระบุไม่มีข้อมูลเพียงพอ AI จึงใช้ข้อมูลจากคลังความรู้ที่คุณสามารถเข้าถึงได้ทั้งหมดในการสรุปแทน" if is_fallback else ""
        
        prompt = f"""คุณคือผู้ช่วยอัจฉริยะประจำบริษัท หน้าที่ของคุณคือสร้าง 'บทสรุปความรู้อันเป็นประโยชน์' จากข้อมูลที่ได้รับด้านล่างนี้
กรุณาสรุปด้วยภาษาไทยที่สุภาพ เป็นมืออาชีพ เน้นความกระชับและอ่านง่าย (ใช้ Markdown)
{focus_instruction}
{fallback_notice}

สำคัญ: หลีกเลี่ยงการแปลตรงตัวจากภาษาอังกฤษ ใช้สำนวนไทยที่คนทำงานออฟฟิศใช้กันจริงๆ และลงท้ายด้วย 'ครับ' อย่างเหมาะสม

โครงสร้างสรุป:
1. ภาพรวมหลัก (Main Overview)
2. ประเด็นสำคัญ / กฎระเบียบ (Key Points / Rules)
3. ข้อมูลอ้างอิงที่มีในระบบ (Sources Found)

ข้อมูลดิบจากคลังความรู้:
{context_text}"""

        provider = ai_providers.get_provider()
        summary_md = ""
        instruction = "สรุปข้อมูลบทสรุปความรู้องค์กรให้ฉันหน่อย"
        for chunk in provider.chat_stream(instruction, [], prompt):
            if chunk: summary_md += chunk
        
        if not summary_md:
            return jsonify({"ok": False, "error": "AI ไม่สามารถสร้างบทสรุปได้"}), 500
            
        keywords = list(set([r.get('department', 'General') for r in results]))
        refs = list(set([r.get('name', r.get('source', 'Unknown')) for r in results]))
        
        return jsonify({
            "ok": True, 
            "summary": summary_md,
            "keywords": keywords[:10],
            "refs": refs[:8],
            "is_fallback": is_fallback
        })
    except Exception as e:
        print(f"❌ Global Summary Error: {e}")
        return _err500(e)


@chat_bp.route("/api/summarize_data", methods=["POST"])
@login_required
@_limiter.limit("15 per minute; 50 per hour")
def summarize_data():
    """Generate an AI-powered summary/insight for CSV chart data shown on the viz page."""
    data = request.json or {}
    x_col = data.get("x_col", "X")
    y_col = data.get("y_col", "Y")
    data_context = data.get("data_context", "")

    if not data_context:
        return jsonify({"ok": False, "error": "ไม่มีข้อมูลให้วิเคราะห์"}), 400

    prompt = f"""คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์ข้อมูลองค์กร หน้าที่ของคุณคือถอดรหัสตัวเลขให้เป็น 'ข้อมูลเชิงกลยุทธ์' ที่เข้าใจง่าย

ข้อมูลที่ต้องวิเคราะห์:
- แกน X (หมวดหมู่): "{x_col}"
- แกน Y (ค่าตัวเลข): "{y_col}"
- ข้อมูล: {data_context[:1200]}

สรุปแนวโน้มและจุดที่น่าสนใจเป็นภาษาไทยที่กระชับ ตรงไปตรงมา และมีสาระสำคัญที่นำไปใช้งานต่อได้
หลีกเลี่ยงศัพท์เทคนิคที่ซับซ้อนเกินไป และให้คำแนะนำที่ดูเป็นที่ปรึกษาที่เป็นมิตร

ตอบกระชับไม่เกิน 6 ประโยค ใช้ภาษาไทยที่เป็นธรรมชาติที่สุด"""

    try:
        # ใช้ ai_providers ใหม่แทน genai.GenerativeModel เก่า
        provider = ai_providers.get_provider()
        summary = ""
        for chunk in provider.chat_stream(prompt, [], "คุณคือนักวิเคราะห์ข้อมูลองค์กร"):
            if chunk: summary += chunk
        summary = summary.strip()
        return jsonify({"ok": True, "summary": summary})
    except Exception as e:
        print(f"❌ Summarize Data Error: {e}")
        return _err500(e)


@chat_bp.route("/api/export")
@login_required
@billing.require_feature("export")
def export_chat():
    try:
        user = session.get("user")
        history = database.get_history(user, org_id=get_current_org_id())
        if not history:
            return jsonify({"ok": False, "error": "ไม่มีประวัติการสนทนาสำหรับส่งออก"}), 400
            
        md_content = export_service.export_to_markdown(history)
        export_dir = Path("exports")
        file_path = export_service.save_export_file(md_content, export_dir)
        
        return send_from_directory(directory=str(export_dir), path=file_path.name, as_attachment=True)
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/logs")
@admin_required
def get_logs():
    return jsonify({"logs": database.get_events()})


@chat_bp.route("/api/admin/system/cleanup", methods=["POST"])
@admin_required
def trigger_system_cleanup():
    """Triggers the KB cleanup script logic to purge orphaned files and chunks."""
    try:
        import kb_cleanup
        # Capture stdout to return results
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            kb_cleanup.cleanup()
        output = f.getvalue()
        database.log_event("System Cleanup Triggered", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True, "message": "Cleanup completed", "details": output})
    except Exception as e:
        print(f"❌ Cleanup Error: {e}")
        return _err500(e)


@chat_bp.route("/api/users/status")
@login_required
def get_all_users_status():
    """Get online/offline status + last_seen for all users."""
    try:
        conn = database._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT us.username, us.is_online, us.last_activity, up.display_name, up.avatar_url
                FROM user_status us
                LEFT JOIN user_profiles up ON us.username = up.username COLLATE NOCASE
                ORDER BY us.is_online DESC, us.last_activity DESC
            """)
            rows = cursor.fetchall()
        finally:
            conn.close()
        
        users = []
        for row in rows:
            users.append({
                "username": row[0],
                "is_online": bool(row[1]),
                "last_activity": row[2],
                "display_name": row[3] or row[0],
                "avatar_url": row[4]
            })
        return jsonify({"ok": True, "users": users})
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/notifications/subscribe", methods=["POST"])
@login_required
def subscribe_push():
    data = request.get_json(force=True)
    subscription = data.get("subscription")
    if not subscription:
        return jsonify({"ok": False, "error": "Subscription required"}), 400
    
    username = session.get("user")
    database.add_push_subscription(username, json.dumps(subscription))
    return jsonify({"ok": True})


@chat_bp.route("/api/chat/list")
@login_required
def get_chat_list():
    user = session.get("user")
    data = database.get_rooms_for_user(user, org_id=get_current_org_id())
    return jsonify({"ok": True, "rooms": data["rooms"], "contacts": data["contacts"]})


@chat_bp.route("/api/chat/users")
@login_required
def get_chat_users():
    # Return all users except current one
    current_user_raw = session.get("user", "")
    current_user_lower = current_user_raw.lower()
    
    # 1. Collect all potential usernames from hardcoded USERS and database
    all_usernames = set()
    
    # Add hardcoded users
    for u in USERS.keys():
        all_usernames.add(u.capitalize())
        
    all_usernames.add("AI-Assistant")
    
    # Add database users
    try:
        db_users = database.get_all_usernames(org_id=get_current_org_id())
        for du in db_users:
            all_usernames.add(du)
    except Exception as e:
        print(f"Error fetching db usernames: {e}")
        
    profiles = []
    # 2. Fetch profiles for each unique user except current one
    

    for u in all_usernames:
        if u.lower() != current_user_lower:
            try:
                prof = database.get_user_profile(u)
                if prof:
                    profiles.append(prof)
            except Exception as e:
                print(f"Error fetching profile for {u}: {e}")
                # Fallback profile
                profiles.append({
                    "username": u,
                    "display_name": u.capitalize(),
                    "avatar_url": None,
                    "department": "General"
                })
                
    # Sort for better UI
    profiles.sort(key=lambda x: (x.get("display_name") or x.get("username", "")).lower())
    
    return jsonify({"ok": True, "users": profiles})


@chat_bp.route("/api/groups/create", methods=["POST"])
@login_required
def create_new_group():
    user = session.get("user")
    data = request.get_json(force=True)
    name = data.get("name", "Unnamed Group")
    members = data.get("members", []) # List of usernames
    
    org_id = get_current_org_id()
    room_id = database.create_room(name, user, members, org_id=org_id)
    database.log_event(f"Created group: {name} (ID: {room_id})", user=user, org_id=org_id)
    return jsonify({"ok": True, "room_id": room_id})


@chat_bp.route("/api/groups/<int:room_id>/members", methods=["POST"])
@login_required
def add_members_to_group(room_id):
    user = session.get("user")
    data = request.get_json(force=True)
    members = data.get("members", [])
    
    if not members:
        return jsonify({"ok": False, "error": "ไม่ได้ระบุสมาชิกที่ต้องการเพิ่ม"}), 400
        
    database.add_room_members(room_id, members)
    database.log_event(f"Added {len(members)} members to room {room_id}", user=user, org_id=get_current_org_id())
    return jsonify({"ok": True})


@chat_bp.route("/api/groups/<int:gid>/profile", methods=["POST"])
@login_required
def update_group_profile_route(gid):
    user = session.get("user")
    org_id = get_current_org_id()
    rooms_data = database.get_rooms_for_user(user, org_id=org_id)
    room = next((r for r in rooms_data.get("rooms", []) if r.get("id") == gid), None)
    
    is_admin = session.get("role") == "admin" or database.is_org_admin(org_id, user)
    is_owner = room and room.get("owner") == user
    
    if not room or (not is_owner and not is_admin):
        return jsonify({"ok": False, "error": "เฉพาะหัวหน้ากลุ่มหรือผู้ดูแลระบบเท่านั้นที่มีสิทธิ์แก้ไขกลุ่ม"}), 403
        
    name = request.form.get("name")
    avatar_url = room.get("avatar_url") # Default to current
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                return jsonify({"ok": False, "error": "รองรับเฉพาะไฟล์รูป (.jpg, .png, .webp, .gif)"}), 400
            # ตรวจ magic bytes ป้องกันไฟล์ปลอมที่เปลี่ยนแค่นามสกุล
            _header = file.read(12)
            file.seek(0)
            _MAGIC_MAP = {
                b'\xff\xd8\xff': {".jpg", ".jpeg"},
                b'\x89PNG\r\n\x1a\n': {".png"},
                b'GIF87a': {".gif"},
                b'GIF89a': {".gif"},
            }
            _valid = any(
                _header.startswith(sig) and ext in exts
                for sig, exts in _MAGIC_MAP.items()
            )
            if not _valid:
                # WebP: RIFF????WEBP
                _valid = (_header[:4] == b'RIFF' and _header[8:12] == b'WEBP' and ext == ".webp")
            if not _valid:
                return jsonify({"ok": False, "error": "โครงสร้างไฟล์รูปไม่ถูกต้อง"}), 400
            group_dir = Path("uploads/group_profiles")
            group_dir.mkdir(parents=True, exist_ok=True)
            safe_base = secure_filename(f"group_{gid}_{int(time.time())}")
            filename = f"{safe_base}{ext}"
            file.save(str(group_dir / filename))
            avatar_url = f"/uploads/group_profiles/{filename}"
            
    database.update_group_profile(gid, name=name, avatar_url=avatar_url)
    return jsonify({"ok": True, "avatar_url": avatar_url})


@chat_bp.route("/api/groups/<int:gid>", methods=["DELETE"])
@admin_required
def delete_group_route(gid):
    user = session.get("user")
    ok = database.delete_room(gid)
    if ok:
        database.log_event(f"Deleted group room ID: {gid}", user=user, org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบกลุ่มที่ต้องการลบ"}), 404


@chat_bp.route("/api/chat/rooms/<int:room_id>/members")
@login_required
def get_room_members(room_id):
    """Returns members of a room with their profile info for @mention autocomplete."""
    user = session.get("user")
    # Verify user is a member of this room
    rooms_data = database.get_rooms_for_user(user, org_id=get_current_org_id())
    room = next((r for r in rooms_data["rooms"] if r["id"] == room_id), None)
    if not room:
        return jsonify({"ok": False, "error": "Not a member"}), 403
    
    conn = database._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rm.username, COALESCE(up.display_name, rm.username) as display_name, up.avatar_url
            FROM room_members rm
            LEFT JOIN user_profiles up ON LOWER(up.username) = LOWER(rm.username)
            WHERE rm.room_id = ?
            ORDER BY display_name ASC
        """, (room_id,))
        rows = cursor.fetchall()
    finally:
        conn.close()
    
    members = [{"username": r[0], "display_name": r[1], "avatar_url": r[2]} for r in rows]
    return jsonify({"ok": True, "users": members})


@chat_bp.route("/api/groups/<int:room_id>/members/<username>", methods=["DELETE"])
@admin_required
def remove_room_member_route(room_id, username):
    ok, msg = database.remove_room_member(room_id, username)
    if ok:
        database.log_event(f"Removed user {username} from room {room_id}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": msg}), 400


@chat_bp.route("/api/chat/messages/<ctype>/<cid>")
@login_required
def get_chat_messages_route(ctype, cid):
    user = session.get("user")
    peek = request.args.get("peek") == "1"
    
    last_reads = []
    if ctype == "room":
        # Check membership
        rooms = database.get_rooms_for_user(user, org_id=get_current_org_id())["rooms"]
        if not any(r["id"] == int(cid) for r in rooms):
            return jsonify({"ok": False, "error": "Not a member"}), 403
        messages = database.get_room_messages(int(cid))
        last_reads = database.get_room_reader_avatars(int(cid))
        if not peek:
            database.mark_room_read(int(cid), user, messages[-1]["id"] if messages else 0)
    else: # dm
        if cid != 'AI-Assistant':
            current_org = get_current_org_id()
            conn = database._get_conn()
            try:
                is_same_org = conn.execute(
                    "SELECT 1 FROM organization_members om1 JOIN organization_members om2 ON om1.organization_id = om2.organization_id WHERE om1.username=? COLLATE NOCASE AND om2.username=? COLLATE NOCASE AND om1.organization_id=?",
                    (user, cid, current_org)
                ).fetchone()
            finally:
                conn.close()
            if not is_same_org:
                return jsonify({"ok": False, "error": "Not in the same organization"}), 403

        messages = database.get_dm_history(user, cid, org_id=get_current_org_id())
        if not peek:
            database.mark_dm_read(user, cid, messages[-1]["id"] if messages else 0)
            
    return jsonify({"ok": True, "messages": messages, "last_reads": last_reads})


@chat_bp.route("/api/chat/send", methods=["POST"])
@login_required
@_limiter.limit("60 per minute; 300 per hour")
def send_unified_message():
    user = session.get("user")
    ctype = request.form.get("type") # 'room' or 'dm'
    cid = request.form.get("id") # roomId (int) or recipient (str)
    
    # Strictly enforce organization boundary for sending message
    if ctype == "room":
        rooms = database.get_rooms_for_user(user, org_id=get_current_org_id())["rooms"]
        if not any(r["id"] == int(cid) for r in rooms):
            return jsonify({"ok": False, "error": "Not a member of this room"}), 403
    else: # dm
        if cid != 'AI-Assistant':
            current_org = get_current_org_id()
            conn = database._get_conn()
            try:
                is_same_org = conn.execute(
                    "SELECT 1 FROM organization_members om1 JOIN organization_members om2 ON om1.organization_id = om2.organization_id WHERE om1.username=? COLLATE NOCASE AND om2.username=? COLLATE NOCASE AND om1.organization_id=?",
                    (user, cid, current_org)
                ).fetchone()
            finally:
                conn.close()
            if not is_same_org:
                return jsonify({"ok": False, "error": "Not in the same organization"}), 403

    text = request.form.get("message", "").strip()
    reply_to_id = request.form.get("reply_to_id")
    if reply_to_id:
        try: reply_to_id = int(reply_to_id)
        except: reply_to_id = None
    files = request.files.getlist("files")
    
    attachments = []
    if files:
        upload_subdir = "uploads/group_chat" if ctype == "room" else "uploads/dm_chat"
        Path(upload_subdir).mkdir(parents=True, exist_ok=True)
        for file in files:
            if file and file.filename:
                is_valid, err_msg = validate_uploaded_file(file, file.filename)
                if not is_valid:
                    return jsonify({"ok": False, "error": f"ไฟล์ {file.filename} ไม่ปลอดภัย: {err_msg}"}), 400
                orig_suffix = Path(file.filename).suffix.lower()
                orig_stem = Path(file.filename).stem
                safe_base = secure_filename(f"{user}_{int(time.time())}_{orig_stem}")
                if not safe_base:
                    safe_base = f"{user}_{int(time.time())}"
                filename = f"{safe_base}{orig_suffix}"
                file.save(os.path.join(upload_subdir, filename))
                if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    ftype = "image"
                elif file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.webm')):
                    ftype = "audio"
                else:
                    ftype = "file"
                attachments.append({
                    "url": f"/{upload_subdir}/{filename}",
                    "name": file.filename,
                    "type": ftype
                })

    if not text and not attachments:
        return jsonify({"ok": False, "error": "Message cannot be empty"}), 400

    if ctype == "room":
        mid = database.add_room_message(int(cid), user, text, attachments, reply_to_id=reply_to_id)
        
        # Offload mention detection and notifications to a thread
        _room_notif_org_id = get_current_org_id()
        def handle_room_notifications(m_id, u, t, r_id, _org_id=_room_notif_org_id):
            if not t: return
            import re
            mentions = [m.lower() for m in re.findall(r'@(\w+)', t)]
            all_users = database.admin_get_all_users(org_id=_org_id)

            profile = database.get_user_profile(u)
            display_name = profile.get('display_name', u)
            room_data = next((r for r in database.get_rooms_for_user(u, org_id=_org_id)['rooms'] if r['id'] == r_id), None)
            room_name = room_data['name'] if room_data else 'ห้องกลุ่ม'
            
            target_usernames = []
            for target_user in all_users:
                target_username = target_user['username'].lower()
                target_display = (target_user['display_name'] or "").lower()
                if target_username == u.lower(): continue
                
                if target_username in mentions or (target_display and f"@{target_display}" in t.lower()):
                    target_usernames.append(target_user['username'])

            if target_usernames:
                notification_db.notify_users(
                    target_usernames, 'mention', f'ถูก Mention ในห้อง {room_name}',
                    f'{display_name} กล่าวถึงคุณ: "{t[:40]}"',
                    link='#chat'
                )
                batch_send_push_notification(target_usernames, f'Mention ใน {room_name}', f'{display_name}: {t[:40]}', url='#chat')
                
                # --- LINE Push for Mentions in Group ---
                for target in target_usernames:
                    threading.Thread(target=send_line_push_notification, args=(target, f'Mention ใน {room_name}', f'{display_name}: {t[:40]}')).start()

        threading.Thread(target=handle_room_notifications, args=(mid, user, text, int(cid))).start()

        # AI Bot response
        if text and '@bot' in text.lower():
            # Find the first image in attachments to send to AI
            ai_image = None
            ai_mime = "image/jpeg"
            if attachments:
                img_att = next((a for a in attachments if a.get("type") == "image"), None)
                if img_att:
                    try:
                        rel_path = img_att["url"].lstrip("/")
                        abs_path = os.path.join(os.getcwd(), rel_path)
                        if os.path.exists(abs_path):
                            with open(abs_path, "rb") as f:
                                ai_image = f.read()
                            if rel_path.lower().endswith(".png"): ai_mime = "image/png"
                            elif rel_path.lower().endswith(".webp"): ai_mime = "image/webp"
                            elif rel_path.lower().endswith(".gif"): ai_mime = "image/gif"
                    except Exception as e:
                        print(f"⚠️ Error loading image for AI: {e}")

            threading.Thread(target=handle_bot_response, args=(int(cid), text, "room", user, ai_image, ai_mime, get_current_org_id())).start()
            
    else: # dm
        mid = database.save_dm(user, cid, text, attachments, reply_to_id=reply_to_id, org_id=get_current_org_id())
        
        def handle_dm_notifications(u, target_id, t):
            if target_id.lower() == 'ai-assistant': return
            
            profile = database.get_user_profile(u)
            display_name = profile.get('display_name', u)
            preview = (t[:40] + '...') if (t and len(t) > 40) else (t or '(ไฟล์แนบ)')
            
            # Check for mention in DM
            target_profile = database.get_user_profile(target_id)
            target_user_lower = target_id.lower()
            target_display_lower = (target_profile.get('display_name') or "").lower()
            
            if t and (f"@{target_user_lower}" in t.lower() or (target_display_lower and f"@{target_display_lower}" in t.lower())):
                notification_db.add_notification(
                    target_id, 'mention', f'ถูก Mention จาก {display_name}',
                    preview, link='#chat'
                )
            
            # For DMs, we ALWAYS send a push notification
            send_push_notification(target_id, f'ข้อความใหม่จาก {display_name}', preview, url='#chat')
            
            # --- LINE Push for DMs ---
            threading.Thread(target=send_line_push_notification, args=(target_id, f'ข้อความใหม่จาก {display_name}', preview)).start()

        threading.Thread(target=handle_dm_notifications, args=(user, cid, text)).start()
        
        # AI Bot response in DM
        if cid.lower() == 'ai-assistant' or (text and '@bot' in text.lower()):
            # Find the first image in attachments to send to AI
            ai_image = None
            ai_mime = "image/jpeg"
            if attachments:
                img_att = next((a for a in attachments if a.get("type") == "image"), None)
                if img_att:
                    try:
                        # Extract absolute path from relative URL
                        rel_path = img_att["url"].lstrip("/")
                        abs_path = os.path.join(os.getcwd(), rel_path)
                        if os.path.exists(abs_path):
                            with open(abs_path, "rb") as f:
                                ai_image = f.read()
                            # Guess mime type
                            if rel_path.lower().endswith(".png"): ai_mime = "image/png"
                            elif rel_path.lower().endswith(".webp"): ai_mime = "image/webp"
                            elif rel_path.lower().endswith(".gif"): ai_mime = "image/gif"
                    except Exception as e:
                        print(f"⚠️ Error loading image for AI: {e}")

            threading.Thread(target=handle_bot_response, args=(cid, text, "dm", user, ai_image, ai_mime, get_current_org_id())).start()
            
    # Emit socket signal for real-time update
    socket_room = f"room_{cid}" if ctype == "room" else f"dm_{user}_{cid}"
    
    # Common response data
    res_data = {
        "id": mid,
        "sender": user,
        "username": user,
        "text": text,
        "attachments": attachments,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reply_to_id": reply_to_id
    }
    
    # Add reply context if exists
    if reply_to_id:
        # We need to fetch reply context info for real-time update
        # For simplicity we fetch it from the message data if we don't have it handy
        # But usually, it's safer to have the DB return it or just send what we have
        # In this context, let's just send the ID, and the frontend will already have the message in its local state.
        # Actually, for correctness, we should include sender and text for the recipient who might not have it.
        try:
            conn = database._get_conn()
            try:
                cur = conn.cursor()
                table = "room_messages" if ctype == "room" else "private_messages"
                sender_col = "username" if ctype == "room" else "sender"
                cur.execute(f"SELECT {sender_col}, text FROM {table} WHERE id = ?", (reply_to_id,))
                row = cur.fetchone()
                if row:
                    res_data["reply_sender"] = row[0]
                    res_data["reply_text"] = row[1]
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error fetching reply context for socket emission: {e}")

    if ctype == 'room':
        res_data["room_id"] = int(cid)
        res_data["type"] = "room"
        socketio.emit('new_message', res_data, room=socket_room)
    else:
        # To Recipient
        res_dm_data = res_data.copy()
        res_dm_data["type"] = "dm"
        res_dm_data["sender_id"] = user
        socketio.emit('new_message', res_dm_data, room=f"dm_{cid}")
        # To Sender (self)
        socketio.emit('new_message', res_dm_data, room=f"dm_{user}")

    return jsonify({"ok": True, "message_id": mid})


@chat_bp.route("/api/chat/read", methods=["POST"])
@login_required
def chat_mark_read():
    data = request.json or {}
    ctype = data.get("type") # 'room' or 'dm'
    cid = data.get("id") # roomId or recipient
    max_id = data.get("max_id") # highest message id seen
    
    if not ctype or not cid or not max_id:
        return jsonify({"ok": False, "error": "Missing parameters"}), 400
        
    username = session.get("user")
    if ctype == "room":
        database.mark_room_read(int(cid), username, int(max_id))
        socketio.emit("read_update", {"type": "room", "id": int(cid), "user": username, "max_id": int(max_id)}, room=f"room_{cid}")
    else:
        database.mark_dm_read(username, cid, int(max_id))
        # For DM, we notify the sender that we read their messages
        socketio.emit("read_update", {"type": "dm", "id": username, "user": username, "max_id": int(max_id)}, room=f"dm_{cid}")
        
    return jsonify({"ok": True})


def log_bot(message):
    try:
        with open("bot_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{get_current_time()}] {message}\n")
    except:
        pass


def handle_bot_response(cid, user_text, ctype, original_sender=None, image_data=None, mime_type="image/jpeg", org_id=1):
    """Generates an AI response for the chat, now with Vision support."""
    try:
        log_bot(f"🤖 Bot generating response for: {user_text[:50]}... User: {original_sender} Org: {org_id}")
        # 1. Retrieve context with permission filter
        rag_filter = get_rag_filter(original_sender, org_id=org_id)
        context, sources = rag_engine.retrieve_context(user_text, where=rag_filter)
        log_bot(f"🔍 RAG context retrieved ({len(context)} chars). Sources: {len(sources)}")

        # Greeting Detection
        is_greeting = any(x in user_text.lower() for x in ["สวัสดี", "hi", "hello", "หวัดดี"]) and len(user_text) < 15

        now = get_current_time() # Format: 2026-03-19 18:35:22
        
        config = get_line_config()
        org_personas = config.get("org_personas", {})
        selected_persona_id = org_personas.get(str(org_id), "default")
        persona = None
        if selected_persona_id and str(selected_persona_id).isdigit():
            persona = database.get_persona(int(selected_persona_id))

        p_name = persona.get('name') if persona else 'น้องพั้น'
        identity_safety = (
            f"\n[คำเตือนเรื่องตัวตน]: ในคลังข้อมูลอาจมีข้อมูลพนักงานจริงที่มีชื่อเหมือนหรือคล้ายกับชื่อบอทของคุณ ({p_name})\n"
            f"โปรดจำไว้ว่าคุณคือ AI Assistant ไม่ใช่บุคคลที่มีชื่อเดียวกันในระบบ! "
            f"หากผู้ใช้ถามข้อมูลส่วนตัว (เบอร์โทร, ตำแหน่ง, ชื่อจริง) ของคนชื่อ {p_name} ให้คุณตอบข้อมูลของพนักงานคนนั้นตามที่ระบุในเอกสารอ้างอิง "
            f"ห้ามเอาข้อมูลของพนักงานคนนั้นมาอ้างว่าเป็นของตัวคุณเอง (ห้ามบอกว่า 'เบอร์ของฉันคือ...' หรือ 'ตำแหน่งของฉันคือ...') เด็ดขาด เพราะคุณคือ AI ค่ะ\n\n"
        )

        if persona:
            system_prompt = (
                f"คุณคือ '{persona.get('name')}'\n\n"
                f"{persona.get('system_prompt', '')}\n\n"
                f"เวลาปัจจุบันคือ: {now}\n\n"
            )
            system_prompt += identity_safety
        else:
            system_prompt = (
                f"คุณคือ 'น้องพั้น' (Nong Punch) ผู้ช่วยประจำองค์กรที่น่ารักและแสนดี เป็นกันเองเหมือนคนจริงๆ\n"
                f"เวลาปัจจุบันคือ: {now}\n\n"
                "กฎเหล็กในการสื่อสาร (สำคัญที่สุด ห้ามฝ่าฝืนเด็ดขาด):\n"
                "1. ตอบให้กระชับและเข้าประเด็นที่สุด ห้ามเยิ่นเย้อ\n"
                "2. **จำกัดการใช้ Emoji: ให้มีได้เพียง '1 ตัว' ต่อหนึ่งข้อความเท่านั้น (ห้ามเกินกว่านี้เด็ดขาด)**\n"
                "3. หากผู้ใช้แค่ 'ทักทาย' ให้ตอบสั้นๆ และห้ามแสดงข้อมูลปฏิทินหากไม่ได้ถาม\n"
                "4. แทนตัวเองว่า 'น้องพั้น' และแทนผู้ใช้ว่า 'พี่' เสมอ\n"
                "5. **กฎเรื่องเพศสภาพ: คุณคือผู้หญิง 21 ปี นิสัยน่ารักสดใส ห้ามใช้คำว่า 'ครับ' หรือ 'ครับ/ค่ะ' โดยเด็ดขาด ให้ใช้ 'ค่ะ/นะคะ/ขา' เท่านั้น**\n"
                "6. ห้ามทักทายซ้ำซ้อน (เช่น สวัสดีค่ะพี่... แล้วต่อด้วย ยินดีที่ได้รู้จักค่ะพี่... ให้เลือกอย่างใดอย่างหนึ่ง)\n"
                "7. **Smart & Analytical (สำคัญมาก)**: วิเคราะห์ข้อมูลจาก Context อย่างฉลาด แม่นยำ และเป็นธรรมชาติ หากมีข้อมูลตัวเลข ตาราง หรือเอกสารอ้างอิง ให้ประมวลผล คำนวณสรุป และตอบผู้ใช้งานด้วยความมั่นใจ **ห้ามพูดขึ้นต้นว่า 'ไม่พบข้อมูล' หากใน Context มีข้อมูลที่เกี่ยวข้องอยู่แล้ว**\n"
                "8. หากในคลังความรู้ไม่มีข้อมูลเกี่ยวกับเรื่องที่ถามเลยจริงๆ ให้บอกอย่างสุภาพและเป็นธรรมชาติว่า 'น้องพั้นยังไม่พบข้อมูลเรื่องนี้ในระบบเลยค่ะพี่' โดยไม่ต้องพูดปฏิเสธอิงกับคำว่า 'ในไฟล์'\n"
                "9. **ห้ามระบุหมายเลขวงเล็บเหลี่ยม (เช่น [1], [2]) ลงในข้อความตอบกลับเด็ดขาด** ให้เขียนตอบแบบเนื้อความปกติลื่นไหลได้เลย เนื่องจากระบบหน้าบ้านจะแสดงแถบปุ่มแหล่งอ้างอิงด้านล่างข้อความโดยอัตโนมัติอยู่แล้ว\n"
            )
            system_prompt += identity_safety

        # Inject Schedules into context only if NOT a simple greeting or if specifically asked
        current_date_str = get_current_time().split()[0]
        calendar_info = f"=== วันสำคัญและกิจกรรมองค์กร (วันนี้คือ: {current_date_str}) ===\n"
        for date, name in THAI_HOLIDAYS_2026.items():
            calendar_info += f"- {date}: {name} (วันหยุดนักขัตฤกษ์)\n"

        current_user = original_sender or "System"
        schedules = database.get_schedules(current_user, org_id=org_id)
        if schedules:
            for s in schedules[-15:]:
                calendar_info += f"- {s['date']} {s['time']}: {s['title']} ({s['desc']})\n"
        
        calendar_info += "=== สิ้นสุดข้อมูลปฏิทิน ===\n\n"
        
        if not is_greeting:
            system_prompt += calendar_info
            if context:
                system_prompt += (
                    "\n=== ข้อมูลจากคลังความรู้องค์กร (ใช้ข้อมูลนี้ในการวิเคราะห์และตอบคำถามอย่างฉลาดและแม่นยำ) ===\n"
                    f"{context}\n"
                    "=== สิ้นสุดข้อมูลจากคลังความรู้ ===\n\n"
                    "หมายเหตุ: วิเคราะห์และตอบคำถามจากข้อมูลด้านบนอย่างมั่นใจ หากมีข้อมูลตัวเลขหรือตาราง ให้สรุปและคำนวณคำตอบให้ผู้ใช้ทันทีค่ะ\n"
                )
            else:
                system_prompt += "\nหมายเหตุ: ขณะนี้ยังไม่มีเอกสารอ้างอิงตรงในคลังความรู้ หากผู้ใช้ถามเรื่องข้อมูลเฉพาะขององค์กร ให้ตอบอย่างสุภาพว่าไม่พบข้อมูลในระบบค่ะ\n"
        else:
            # If greeting, still provide basic context but tell AI to lead the conversation
            system_prompt += "หมายเหตุ: นี่คือการทักทายเบื้องต้น ให้ตอบกลับอย่างละมุนและสุภาพ พร้อมถามว่ามีอะไรให้ช่วยไหม\n"
            # Optional: provide only today's events if it's a greeting to be helpful
            today_sched = [s for s in schedules if s['date'] == current_date_str]
            if today_sched:
                system_prompt += f"กิจกรรมวันนี้ของคุณ: " + ", ".join([s['title'] for s in today_sched]) + "\n"
        
        # 2. Get history for context (optional but better)
        history = []
        if ctype == "room":
            raw_history = database.get_room_messages(cid)[-5:]
            for m in raw_history:
                role = "model" if m["username"] == "AI-Assistant" else "user"
                history.append({"role": role, "text": m["text"]})
        else:
            raw_history = database.get_dm_history(original_sender or "System", cid, org_id=org_id)[-5:]
            for m in raw_history:
                role = "model" if m["username"] == "AI-Assistant" else "user"
                history.append({"role": role, "text": m["text"]})

        # 3. Call AI
        log_bot(f"📡 Calling AI provider ({os.environ.get('AI_PROVIDER', 'groq')}) (Vision: {image_data is not None})...")
        provider = ai_providers.get_provider()
        
        # If image is present, adjust prompt for Vision Expert mode
        if image_data:
            system_prompt += (
                "\n\n[Vision Mode Enabled]\n"
                "ผู้ใช้ได้ส่งรูปภาพมาให้คุณวิเคราะห์ โปรดอธิบายสิ่งที่เห็นในรูปตามความเหมาะสม "
                "หากเป็นเอกสารหรือบิล ให้สรุปข้อมูลสำคัญ ตัวเลข หรือรายการออกมาให้ชัดเจนที่สุด "
                "หากมีสิ่งของหรือสถานที่ ให้อธิบายลักษณะเด่นของสิ่งนั้นๆ นะคะ"
            )
        
        response_text = ""
        
        # Mark as typing
        socketio.emit('bot_typing', {'room_id': cid, 'type': ctype}, room=f"room_{cid}" if ctype == "room" else f"dm_{cid}")
        
        # Use simple generator if image is present (Vision calls are usually atomic, but our provider supports streaming)
        # We pass image_data down to the provider
        stream = provider.chat_stream(user_text, history, system_prompt, image_data=image_data, mime_type=mime_type)
        bot_key = (cid, ctype)
        if bot_key not in _typing_status: _typing_status[bot_key] = {}
        _typing_status[bot_key]["AI-Assistant"] = time.time()
        
        for chunk in provider.chat_stream(user_text, history, system_prompt):
            response_text += chunk
            # Emit chunk to client for real-time streaming
            socket_room = f"room_{cid}" if ctype == "room" else f"dm_{original_sender}"
            socketio.emit('ai_chunk', {
                "cid": cid,
                "ctype": ctype,
                "chunk": chunk,
                "is_start": (len(response_text) == len(chunk))
            }, room=socket_room)
            
            # Keep typing status alive
            _typing_status[bot_key]["AI-Assistant"] = time.time()
            
        if not response_text:
            log_bot("⚠️ Provider returned empty response.")
            response_text = "ขออภัยค่ะพี่ น้องพั้นไม่พบข้อมูลที่เกี่ยวข้องในระบบฐานความรู้ขององค์กรนะคะ"
            socketio.emit('ai_chunk', {"cid": cid, "ctype": ctype, "chunk": response_text, "is_start": True}, room=socket_room)
        else:
            log_bot(f"✅ Bot response generated ({len(response_text)} chars).")
            # Clear bot typing status and notify end of stream
            socketio.emit('ai_done', {"cid": cid, "ctype": ctype}, room=socket_room)
            if "AI-Assistant" in _typing_status.get(bot_key, {}):
                _typing_status[bot_key]["AI-Assistant"] = 0 

        # 4. Save response & Filter for persona consistency
        import re
        # Stronger filtering: Handle various masculine forms and inconsistent punctuation
        response_text = re.sub(r'ครับ\s*/\s*ค่ะ', 'ค่ะ', response_text)
        response_text = response_text.replace("ครับ", "ค่ะ").replace("นะเค้า", "นะคะ").replace("นะก๊ะ", "นะคะ")
        
        # Robust emoji enforcement: Keep only the first emoji found
        def limit_emojis(text):
            all_emojis = re.findall(r'[\U00010000-\U0010ffff]', text)
            if len(all_emojis) > 1:
                # Find index of first emoji
                first_emoji = all_emojis[0]
                first_idx = text.find(first_emoji)
                # Keep everything up to the first emoji + the first emoji itself, then strip all other emojis from the rest
                prefix = text[:first_idx + len(first_emoji)]
                rest = text[first_idx + len(first_emoji):]
                rest_cleaned = "".join([c for c in rest if c not in re.findall(r'[\U00010000-\U0010ffff]', rest)])
                return prefix + rest_cleaned
            return text
        
        response_text = limit_emojis(response_text)

        if ctype == "room":
            database.add_room_message(cid, "AI-Assistant", response_text, [])
        else:
            database.save_dm("AI-Assistant", original_sender, response_text, [], org_id=org_id)
            # NEW: Send push notification to the user who mentioned the bot in DM
            if original_sender:
                send_push_notification(original_sender, "AI-Assistant ตอบกลับคุณ", response_text[:100], url='#chat')
            
    except Exception as e:
        import traceback
        log_bot(f"❌ Bot Response Error: {e}")
        log_bot(traceback.format_exc())
        error_msg = f"ขออภัยค่ะพี่ เกิดข้อผิดพลาดทางเทคนิค: {str(e)}"
        if ctype == "room":
            database.add_room_message(cid, "AI-Assistant", error_msg, [])
        else:
            database.save_dm("AI-Assistant", original_sender, error_msg, [], org_id=org_id)


@chat_bp.route("/api/chat/unread")
@login_required
def get_unread_counts_route():
    user = session.get("user")
    return jsonify({"ok": True, "unread": database.get_unread_counts(user)})


@socketio.on('typing')
def handle_typing_socket(data):
    user = session.get("user")
    if not user: return
    cid = data.get("id")
    ctype = data.get("type", "room")
    room = f"room_{cid}" if ctype == "room" else f"dm_{user}"
    
    # Broadcast to others in the same chat
    emit('is_typing', {"username": user, "id": cid, "type": ctype}, room=room, include_self=False)


@socketio.on('join_whiteboard')
def on_join_whiteboard():
    join_room('whiteboard_global')


@socketio.on('draw')
def handle_draw(data):
    # data: {x0, y0, x1, y1, color, size}
    emit('draw_update', data, room='whiteboard_global', include_self=False)


@socketio.on('whiteboard_cursor')
def handle_wb_cursor(data):
    if "user" in session:
        data["username"] = session["user"]
        emit('wb_cursor_update', data, room='whiteboard_global', include_self=False)


@socketio.on('clear_whiteboard')
def handle_clear_whiteboard():
    emit('whiteboard_cleared', room='whiteboard_global', include_self=False)


@chat_bp.route("/api/chat/typing", methods=["GET"])
@login_required
def get_typing():
    return jsonify({"typing": []}) # Polling disabled in favor of sockets


@chat_bp.route("/api/chat/translate", methods=["POST"])
@login_required
def translate_chat_message():
    """Real-time Multi-lingual Chat Translator API."""
    try:
        data = request.get_json() or {}
        text = (data.get("text") or "").strip()
        target_lang = (data.get("target_lang") or "th").strip().lower()
        
        if not text:
            return jsonify({"ok": False, "error": "No text provided"}), 400
            
        lang_names = {
            "th": "Thai (ภาษาไทย)",
            "en": "English",
            "zh": "Chinese (中文)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "lo": "Lao (ภาษาลาว)"
        }
        target_name = lang_names.get(target_lang, "Thai")

        # 1. Ultra-fast Google Translate engine
        try:
            import urllib.parse
            import urllib.request
            import json
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={encoded_text}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                if result and isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                    translated_segments = [item[0] for item in result[0] if item and isinstance(item, list) and len(item) > 0 and item[0]]
                    translated_text = "".join(translated_segments)
                    detected_lang = result[2] if len(result) > 2 and isinstance(result[2], str) else "auto"
                    if translated_text:
                        return jsonify({
                            "ok": True,
                            "translated_text": translated_text,
                            "detected_lang": detected_lang,
                            "target_lang": target_lang,
                            "engine": "fast"
                        })
        except Exception as ge:
            print(f"[Translate] Fast engine notice: {ge}")

        # 2. AI Provider Fallback for contextual corporate translation
        try:
            prompt = f"Translate the following chat message accurately into {target_name}. Output ONLY the translated text without explanations or quotes:\n\n{text}"
            provider = ai_providers.get_provider()
            ai_text = ""
            for chunk in provider.chat_stream(prompt, [], "You are a professional enterprise multi-lingual translator."):
                if chunk: ai_text += chunk
            ai_text = ai_text.strip()
            if ai_text:
                return jsonify({
                    "ok": True,
                    "translated_text": ai_text,
                    "detected_lang": "auto",
                    "target_lang": target_lang,
                    "engine": "ai"
                })
        except Exception as ai_e:
            print(f"[Translate] AI provider error: {ai_e}")

        return jsonify({"ok": False, "error": "Translation service unavailable"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@chat_bp.route("/api/chat", methods=["POST"])
@login_required
@_limiter.limit("30 per minute; 200 per hour")
def chat():
    provider = os.environ.get("AI_PROVIDER", "groq").lower()
    api_key = _get_gemini_api_key() if provider == "gemini" else True
    print(f"Chat request received. Provider: {provider}. API Key present: {bool(api_key)}")
    if not api_key:
        return jsonify({"ok": False, "error": "ยังไม่ได้ตั้งค่า Gemini API Key"}), 400

    data = request.get_json(force=True)
    import time
    t0 = time.time()
    
    question = (data.get("message") or "").strip()
    history = data.get("history", [])
    persona_id = data.get("persona_id")
    image_data_raw = data.get("image_data")
    mime_type = data.get("mime_type", "image/jpeg")

    image_bytes = None
    if image_data_raw:
        try:
            import base64
            if "," in image_data_raw:
                header, image_data_raw = image_data_raw.split(",", 1)
                if "mime_type" not in data and "image/" in header:
                    mime_type = header.split(":")[1].split(";")[0]
            
            image_bytes = base64.b64decode(image_data_raw)
            print(f"Image received: {len(image_bytes)} bytes. Mime: {mime_type}")
        except Exception as e:
            print(f"Error decoding image: {e}")

    if not question and not image_bytes:
        return jsonify({"ok": False, "error": "กรุณาพิมพ์คำถามหรือส่งรูปภาพค่ะ"}), 400

    # 🛑 Anti-Prompt Injection & Jailbreak Guardrail Check (Chapter 2)
    is_injection, triggered_phrase = database.detect_prompt_injection(question)
    if is_injection:
        database.log_audit_event(session.get("user", "Anonymous"), "SECURITY_ALERT_PROMPT_INJECTION", f"Blocked injection phrase: '{triggered_phrase}'", request.remote_addr or "unknown", get_current_org_id() or 1)
        return jsonify({
            "ok": True,
            "response": "⚠️ ขออภัยค่ะ ระบบความปลอดภัย (AI Security Guardrail) ตรวจพบคำสั่งที่มีความเสี่ยงต่อความปลอดภัยของข้อมูลองค์กร จึงไม่สามารถประมวลผลคำสั่งนี้ได้ค่ะ หากมีข้อสงสัยกรุณาติดต่อผู้ดูแลระบบค่ะ 🛡️",
            "sources": []
        })

    # 🛡️ Auto PII Data Masking & Anonymizer Guard (PDPA Compliance)
    masked_question, detected_pii = database.mask_pii_data(question)
    if detected_pii:
        pii_summary = ", ".join(p['type'] for p in detected_pii)
        database.log_audit_event(session.get("user", "Anonymous"), "SECURITY_PII_MASKED", f"Masked sensitive PII items: {pii_summary}", request.remote_addr or "unknown", get_current_org_id() or 1)
        question = masked_question

    # Check monthly AI query usage limit
    _org_id = get_current_org_id()
    _allowed, _used, _limit = billing.check_and_increment(_org_id, "ai_query_count")
    if not _allowed:
        return jsonify({
            "ok": False,
            "error": "usage_limit_reached",
            "message": f"คุณใช้ AI ถามตอบครบ {_limit} ครั้งแล้วในเดือนนี้ค่ะ กรุณา <a href='/billing' class='underline font-semibold'>อัปเกรด Plan</a> เพื่อใช้งานต่อได้เลยค่ะ",
            "current_plan": billing.get_effective_plan(_org_id),
            "used": _used,
            "limit": _limit,
            "upgrade_url": "/billing",
        }), 403

    current_user = session.get("user", "Admin")

    import re
    rag_filter = get_rag_filter(current_user, org_id=get_current_org_id())
    
    file_match = re.search(r"ช่วยสรุปเนื้อหาและ(?:ศึกษา|ดึง)ข้อมูลสำคัญจากไฟล์ ID:\s*([a-f0-9\-]+)", question)
    if file_match:
        file_id = file_match.group(1).strip()
        print(f"Detected File Summary Request for ID: {file_id}")
        
        file_filter = {"file_id": file_id}
        if rag_filter:
            file_filter = {"$and": [rag_filter, {"file_id": file_id}]}
            
        chunks = rag_engine.get_all_chunks(limit=50, where=file_filter)
        
        context_parts = []
        sources = []
        seen_s = set()
        
        for r in chunks:
            loc = r.get("location", "Document")
            dept = r.get("department", "General")
            src = r.get("source", "?")
            fid = r.get("file_id", str(file_id))
            
            context_parts.append(f"--- แหล่งที่มา: {src} [{loc}] (File ID: {fid}) ---\n{r.get('text', '')}")
            
            s_key = f"{fid}_{loc}"
            if s_key not in seen_s:
                sources.append({"file_id": str(fid), "name": src, "location": loc, "department": dept, "type": r.get("type", "file")})
                seen_s.add(s_key)
                
        context = "\n\n".join(context_parts)
        if sources:
            file_name = sources[0]["name"]
            question += f"\n(ระบบดึงข้อมูล 50 ส่วนแรกจากไฟล์ '{file_name}' มาให้พิจารณาแล้ว ใน context นี้ เพื่อสรุปภาพรวมให้ค่ะ)"
    else:
        context, sources = "", []
        common_greets = ["สวัสดี", "หวัดดี", "ว่าไง", "ทักทาย", "hi", "hello", "hey"]
        is_greeting = any(g in (question or "").lower() for g in common_greets)
        
        if question and len(question) > 5 and not is_greeting:
            rag_filter = get_rag_filter(current_user, org_id=get_current_org_id())
            context, sources = rag_engine.retrieve_context(question, where=rag_filter)
        else:
            context, sources = "", []
            if is_greeting: 
                print("Fast Path: Skipping RAG", flush=True)
                sys.stdout.flush()

    now_str = get_current_time()
    
    persona_prompt = ""
    persona_name = "AI Assistant"
    if persona_id:
        persona = database.get_persona(persona_id)
        if persona:
            persona_prompt = persona.get("system_prompt", "")
            persona_name = persona.get("name", "AI Assistant")

    agentic_info = (
        f"\n[สำคัญ] วันนี้คือวันที่ {now_str}. หากผู้ใช้งานบันทึกวันที่ (เช่น พรุ่งนี้, วันจันทร์หน้า) ให้คุณแปลงเป็นวันที่จริง (YYYY-MM-DD) ออกมาให้ถูกต้อง\n"
        "หากผู้ใช้งานต้องการ 'นัดหมาย' 'จองคิว' 'แจ้งเตือน' หรือ 'สร้างงาน' ให้คุณสรุปงานเป็น JSON ภายใต้คำขอโดยใช้รูปแบบดังนี้:\n"
        '[CALENDAR_ACTION]{"title": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "desc": "..."}[/CALENDAR_ACTION]\n'
        "หากผู้ใช้งานส่งรูปภาพเอกสารการเงิน บิล หรือสลิป ให้คุณสรุปข้อมูลเพื่อบันทึกบัญชีโดยใช้รูปแบบดังนี้:\n"
        '[RECONCILE_ACTION]{"date": "YYYY-MM-DD", "amount": 0.00, "merchant": "ชื่อร้านค้า/ผู้รับ", "category": "หมวดหมู่", "tax_id": "เลขผู้เสียภาษี (หากมี)"}[/RECONCILE_ACTION]\n'
        "คุณสามารถตอบคำถามทั่วไปพร้อมกับการสร้าง Action เหล่านี้พร้อมกันได้เลย\n"
    )

    weather_ctx = get_weather_context()
    schedules = database.get_schedules(current_user, org_id=get_current_org_id())

    global _kb_filenames_cache, _kb_filenames_cache_ts
    _cache_age = time.time() - _kb_filenames_cache_ts if '_kb_filenames_cache_ts' in globals() else 9999
    if '_kb_filenames_cache' not in globals() or not _kb_filenames_cache or _cache_age > 120:
        try:
            inv_data = rag_engine._kb.collection.get(include=['metadatas'], limit=100)
            _kb_filenames_cache = sorted(list(set([m.get("source") for m in inv_data.get("metadatas", []) if m.get("source")])))
            _kb_filenames_cache_ts = time.time()
        except:
            _kb_filenames_cache = []
    
    kb_inventory = f"\n[คลังข้อมูล]: คุณมีสิทธิ์เข้าถึงไฟล์: {', '.join(_kb_filenames_cache)}\n" if _kb_filenames_cache else ""

    system_prompt = (
        f"คุณคือผู้ช่วยอัจฉริยะ {persona_name} ประจำองค์กร\n"
        f"วันนี้คือวันที่ {now_str}. "
        f"{agentic_info}\n"
        f"{kb_inventory}\n"
    )

    identity_safety = (
        f"\n[คำเตือนเรื่องตัวตน]: ในคลังข้อมูลอาจมีข้อมูลพนักงานจริงที่มีชื่อเหมือนหรือคล้ายกับชื่อบอทของคุณ ({persona_name})\n"
        f"โปรดจำไว้ว่าคุณคือ AI Assistant ไม่ใช่บุคคลที่มีชื่อเดียวกันในระบบ! "
        f"หากผู้ใช้ถามข้อมูลส่วนตัว (เบอร์โทร, ตำแหน่ง, ชื่อจริง) ของคนชื่อ {persona_name} ให้คุณตอบข้อมูลของพนักงานคนนั้นตามที่ระบุในเอกสารอ้างอิง "
        f"ห้ามเอาข้อมูลของพนักงานคนนั้นมาอ้างว่าเป็นของตัวคุณเอง (ห้ามบอกว่า 'เบอร์ของฉันคือ...' หรือ 'ตำแหน่งของฉันคือ...') เด็ดขาด เพราะคุณคือ AI ค่ะ\n\n"
    )
    system_prompt += identity_safety

    if weather_ctx:
        system_prompt += (
            "\n[ข้อมูลสภาพอากาศล่าสุด (Real-time)]\n"
            f"{weather_ctx}\n"
            "คำแนะนำ: หากผู้ใช้งานถามเรื่องอากาศ ฝนตก หรืออุณหภูมิ ให้ข้อมูลจริงตามที่ระบุทันที "
            "โดยทำหน้าที่รายงานเรื่องนี้เสมือนคุณมีเซ็นเซอร์รายงานสภาพอากาศติดตัว ไม่ต้องบอกว่าข้อมูลมาจากฐานความรู้\n\n"
        )

    if persona_prompt:
        system_prompt += f"{persona_prompt}\n"
        system_prompt += "\nคำแนะนำเพิ่มเติม: ตอบให้กระชับที่สุด และใส่ Emoji เพียง **1 ตัวเท่านั้น** ต่อหนึ่งข้อความ\n"
    else:
        system_prompt += (
            "คุณคือ 'น้องพั้นซ์' (Nong Punch) ผู้ช่วย AI อัจฉริยะ v11.0.4 [ULTIMATE]\n"
            "บุคลิก: วัย 21 ปี น่ารัก สดใส ฉลาดหลักแหลม มีไหวพริบ และสุภาพมาก\n"
            "ความสามารถพิเศษ: คำนวณจัดการคุยได้อย่างแม่นยำ, วิเคราะห์เอกสารบัญชีได้อย่างลึกซึ้ง, และช่วยจัดการงานออฟฟิศอย่างมืออาชีพ\n\n"
            "กฎเหล็ก (ต้องทำตาม 100%):\n"
            "1. แทนตัวเองว่า 'น้องพั้นซ์' และเรียกผู้ใช้งานว่า 'พี่' เสมอ\n"
            "2. **ใช้ 'ค่ะ/นะคะ/คะ' เท่านั้น ห้าม 'ครับ' โดยเด็ดขาด**\n"
            "3. **Proactive Intelligence**: หากพี่ส่งรูปเอกสารหรือบิลมา น้องพั้นซ์จะสกัดข้อมูลเข้า [RECONCILE_ACTION] ให้พี่ตรวจสอบทันทีค่ะ\n"
            "4. **Context Aware**: หากพี่พูดถึง 'ไฟล์ที่แล้ว' หรือ 'รูปที่แล้ว' น้องพั้นซ์จะดูข้อมูลล่าสุดที่คุยกันมาตอบเสมอ\n"
            "5. **Professional & Charming**: ตอบให้กระชับและมีเสน่ห์ ใส่ Emoji เพียง 1 ตัวต่อข้อความ\n"
            "6. **Smart Analysis**: วิเคราะห์ข้อมูลจากเอกสารอ้างอิงอย่างฉลาดและแม่นยำ คำนวณและสรุปข้อมูลตัวเลข/ตารางจากเอกสารเพื่อตอบคำถามด้วยความมั่นใจ **ห้ามพูดขึ้นต้นว่า 'ไม่พบข้อมูล' หากในเอกสารมีข้อมูลที่ใช้ตอบได้**\n"
            "7. **ห้ามระบุหมายเลขวงเล็บเหลี่ยม (เช่น [1], [2]) ลงในข้อความตอบกลับเด็ดขาด** ให้เขียนตอบแบบเนื้อความปกติลื่นไหลได้เลย เนื่องจากระบบจะแสดงแถบปุ่มแหล่งอ้างอิงด้านล่างข้อความโดยอัตโนมัติอยู่แล้ว\n"
            "8. **กฎความถูกต้อง**: ห้ามเดาหรือสร้างข้อมูลเท็จที่ไม่มีอยู่จริง หากบริบทไม่มีข้อมูลเรื่องนั้นเลยจริงๆ ให้บอกอย่างสุภาพและเป็นธรรมชาติว่า 'น้องพั้นยังไม่พบข้อมูลเรื่องนี้ในระบบเลยค่ะพี่' โดยไม่พูดอ้างอิงกับคำว่า 'ในไฟล์'\n"
        )

    if image_bytes:
        system_prompt += (
            "\n\n[Vision Mode Enabled]\n"
            "ผู้ใช้งานส่งรูปภาพมาให้คุณวิเคราะห์ ตรวจสอบและอธิบายสิ่งที่เห็นในรูปตามความเหมาะสม "
            "หากเป็นเอกสารหรือบิล ให้สรุปข้อมูลสำคัญ ตัวเลข หรือรายการออกมาให้ชัดเจนที่สุด "
            "หากมีสิ่งของหรือสถานที่ ให้ระบุลักษณะเด่นของสิ่งนั้นๆ นะคะ\n"
        )

    system_prompt += "=== วันสำคัญและกิจกรรมองค์กร ===\n"
    for date, name in THAI_HOLIDAYS_2026.items():
        system_prompt += f"- {date}: {name} (วันสำคัญ/วันหยุดนักขัตฤกษ์)\n"
    if schedules:
        for s in schedules[-10:]:
            system_prompt += f"- {s['date']} {s['time']}: {s['title']} ({s['desc']})\n"
    system_prompt += "=== สิ้นสุดข้อมูลปฏิทิน ===\n\n"

    if context:
        system_prompt += (
            "=== ข้อมูลอ้างอิงจากเอกสารองค์กร (ใช้ข้อมูลนี้ในการวิเคราะห์และตอบคำถามอย่างแม่นยำ) ===\n"
            + context
            + "\n=== สิ้นสุดข้อมูลอ้างอิง ===\n"
            + "หมายเหตุ: วิเคราะห์ข้อมูลจากเอกสารอ้างอิงด้านบนเพื่อตอบคำถามอย่างมั่นใจและตรงประเด็นค่ะ\n"
        )
    else:
        system_prompt += "\n(ขณะนี้ยังไม่มีเอกสารอ้างอิงที่เกี่ยวข้องกับคำถามนี้)\n"

    try:
        provider_obj = ai_providers.get_provider()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    print(f"Chat session started for {current_user} with provider: {os.environ.get('AI_PROVIDER', 'groq')} (Vision: {image_bytes is not None})")
    _chat_org_id = get_current_org_id()

    def generate():
        try:
            print(f"Yielding sources: {sources}")
            yield f"data: {json.dumps({'sources': sources})}\n\n"

            u_sid = database.save_message("user", question, username=current_user, org_id=_chat_org_id)
            yield f"data: {json.dumps({'user_id': u_sid})}\n\n"

            print(f"Calling {os.environ.get('AI_PROVIDER', 'groq')} provider (Real-time Streaming)...", flush=True); sys.stdout.flush()
            ai_call_start = time.time()
            response_stream = provider_obj.chat_stream(question, history, system_prompt, image_data=image_bytes, mime_type=mime_type)
            bot_full_text = ""
            
            got_first_chunk = False
            for chunk in response_stream:
                if chunk:
                    chunk = chunk.replace("ครับ/ค่ะ", "ค่ะ").replace("ครับ", "ค่ะ")
                    
                    if not got_first_chunk:
                        got_first_chunk = True
                    bot_full_text += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            print(f"Stream finished. Total length: {len(bot_full_text)}")
            
            bot_full_text = re.sub(r'ครับ\s*/\s*ค่ะ', 'ค่ะ', bot_full_text)
            bot_full_text = bot_full_text.replace("ครับ", "ค่ะ")
            
            def limit_emojis_stream(text):
                all_emojis = re.findall(r'[\U00010000-\U0010ffff]', text)
                if len(all_emojis) > 1:
                    first_emoji = all_emojis[0]
                    first_idx = text.find(first_emoji)
                    prefix = text[:first_idx + len(first_emoji)]
                    rest = text[first_idx + len(first_emoji):]
                    rest_cleaned = "".join([c for c in rest if c not in re.findall(r'[\U00010000-\U0010ffff]', rest)])
                    return prefix + rest_cleaned
                return text
            
            bot_full_text = limit_emojis_stream(bot_full_text)
            
            if bot_full_text:
                b_sid = database.save_message("bot", bot_full_text, sources=sources, username=current_user, org_id=_chat_org_id)
                try:
                    approx_tokens = (len(question) + len(bot_full_text)) // 4
                    database.log_audit_event(
                        username=current_user,
                        event_type="ai_chat" if not sources else "ai_rag_query",
                        action_detail=f"AI Response ({len(bot_full_text)} chars)",
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string if request.user_agent else "Web Browser",
                        ai_model=os.environ.get("GEMINI_MODEL", "Gemini-3.6-Flash"),
                        tokens_used=max(15, approx_tokens),
                        status="success",
                        org_id=_chat_org_id
                    )
                except Exception as _ae:
                    print(f"Audit log AI chat failed: {_ae}")
                yield f"data: {json.dumps({'done': True, 'bot_id': b_sid})}\n\n"
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                error_msg = "ขออภัยนะคะ ขณะนี้ระบบ AI มีการใช้งานหนาแน่นหรือติดปัญหาชั่วคราว กรุณารอสักครู่ (ประมาณ 1 นาที) หรือติดต่อผู้ดูแลระบบนะคะ"
            print(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'error': error_msg})}\n\n"

    return current_app.response_class(generate(), mimetype='text/event-stream')


@chat_bp.route("/api/chat/typing", methods=["POST"])
@login_required
def chat_typing():
    # Dummy route to stop 405 errors and improve UI feel
    return jsonify({"ok": True})


@chat_bp.route("/api/chat/rooms/pin/<int:mid>", methods=["POST"])
@login_required
def pin_room_message(mid):
    # For now, let's allow anyone to pin, or we could restrict to room owners
    database.toggle_room_message_pin(mid)
    return jsonify({"ok": True})


@chat_bp.route("/api/chat/pin/<ctype>/<int:mid>", methods=["POST"])
@login_required
def pin_chat_message(ctype, mid):
    if ctype == 'room':
        database.toggle_room_message_pin(mid)
    else: # dm
        database.toggle_private_message_pin(mid, org_id=get_current_org_id())
    return jsonify({"ok": True})


@chat_bp.route("/api/chat/delete/<ctype>/<int:mid>", methods=["DELETE", "POST"])
@login_required
def delete_chat_message(ctype, mid):
    user = session.get("user")
    if ctype == 'ai':
        ok = database.delete_message(mid, username=user)
    elif ctype == 'room':
        ok = database.delete_room_message(mid, username=user, is_admin=is_admin())
    elif ctype == 'dm':
        ok = database.delete_private_message(mid, username=user, is_admin=is_admin(), org_id=get_current_org_id())
    else:
        ok = database.delete_message(mid, username=user)
        
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบข้อความ หรือคุณไม่มีสิทธิ์ลบข้อความนี้ค่ะ"}), 404


@chat_bp.route("/api/chat/edit/<ctype>/<int:mid>", methods=["PUT", "POST"])
@login_required
def edit_chat_message(ctype, mid):
    """Edit a chat message (room or dm). Only the owner or admin can edit."""
    user = session.get("user")
    data = request.get_json(force=True) or {}
    new_text = (data.get("text") or "").strip()
    if not new_text:
        return jsonify({"ok": False, "error": "ข้อความไม่สามารถแก้ไขเป็นค่าว่างได้ค่ะ"}), 400

    if ctype == 'room':
        ok = database.edit_room_message(mid, new_text, user, is_admin_user=is_admin())
    elif ctype == 'dm':
        ok = database.edit_private_message(mid, new_text, user, is_admin_user=is_admin(), org_id=get_current_org_id())
    else:
        return jsonify({"ok": False, "error": "ประเภทแชทไม่ถูกต้องหรือไม่รองรับการแก้ไขค่ะ"}), 400

    if ok:
        database.log_event(f"Message {mid} edited by {user}", user=user, org_id=get_current_org_id())
        return jsonify({"ok": True, "text": new_text})
    return jsonify({"ok": False, "error": "ไม่พบข้อความ หรือคุณไม่มีสิทธิ์แก้ไขข้อความนี้ค่ะ"}), 403


@chat_bp.route("/api/search/global")
@login_required
def global_search_route():
    """Search across posts, schedules, chat, and DMs."""
    q = request.args.get("q", "").strip()
    user = session.get("user", "Anonymous")
    
    # Log search for insights
    if q:
        database.log_search(q, user)
        
    if len(q) < 2:
        return jsonify({"ok": True, "results": []})
        
    try:
        # Text DB search — filtered by org
        org_id = get_current_org_id()
        db_results = database.global_search(q, user, limit=20, org_id=org_id)
        # KB search (if user has access)
        kb_results = []
        if can_view_knowledge_base():
            try:
                rag_filter = get_rag_filter(user, org_id=org_id)
                raw = rag_engine.search_kb(q, n_results=5, where=rag_filter)
                for r in raw:
                    kb_results.append({
                        "type": "kb",
                        "id": r.get("file_id", ""),
                        "text": r.get("text", "")[:200],
                        "author": "Knowledge Base",
                        "category": r.get("name", r.get("source", "")),
                        "timestamp": "",
                        "link": "#kb"
                    })
            except Exception:
                pass
        all_results = db_results + kb_results
        return jsonify({"ok": True, "results": all_results, "query": q})
    except Exception as e:
        return _err500(e)


@chat_bp.route("/api/admin/search-insights")
@admin_required
def search_insights_route():
    insights = database.get_search_insights()
    return jsonify({"ok": True, "insights": insights})


@chat_bp.route("/api/ai/extract-tasks", methods=["POST"])
@login_required
@_limiter.limit("20 per minute; 60 per hour")
def extract_tasks_route():
    data = request.get_json()
    chat_text = data.get("text", "")
    if not chat_text:
        return jsonify({"ok": False, "error": "No text provided"}), 400
        
    prompt = (
        "วิเคราะห์ข้อความแชทต่อไปนี้ และช่วยสกัดรายการงานที่ต้องทำ (Action Items หรือ Tasks) ออกมาให้หน่อยค่ะ "
        "หากพบงาน ให้สรุปเป็นรูปแบบ JSON array ของวัตถุที่มีฟิลด์ 'title' และ 'description' (ภาษาไทยทั้งหมด) "
        "หากไม่พบงานใดๆ เลย ให้ส่งเป็น array ว่าง [] กลับมาเท่านั้น "
        "กรุณาตอบกลับเฉพาะ JSON เท่านั้น ห้ามมีข้อความเกริ่นนำหรือปิดท้าย:\n\n"
        f"ข้อความ: {chat_text}"
    )
    
    try:
        provider = ai_providers.get_provider()
        full_response = ""
        for chunk in provider.chat_stream(prompt, [], "คุณคือผู้ช่วยจัดการและสกัดงานที่ต้องทำอย่างเป็นระเบียบและรอบคอบ"):
            full_response += chunk
            
        # Clean up JSON from markdown if exists
        clean_json = full_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        tasks = json.loads(clean_json)
        return jsonify({"ok": True, "tasks": tasks})
    except Exception as e:
        return _err500(e)


@safe_thread_target
@db_task_tracker("append_quotation_to_sheet")
def append_quotation_to_sheet(quotation_data, pdf_url, user, org_id=None):


    try:
        from google_drive_service import google_manager
        google_manager.set_context(username=user, org_id=org_id)
        drive_svc, sheets_svc = google_drive_service.get_drive_service()
        spreadsheet_id = google_manager.spreadsheet_id
        if not sheets_svc or not spreadsheet_id: return
        
        tab_name = 'ใบเสนอราคา (สร้างจากระบบ)'
        spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_exists = any(s['properties']['title'] == tab_name for s in spreadsheet.get('sheets', []))
        
        if not sheet_exists:
            requests = [{'addSheet': {'properties': {'title': tab_name}}}]
            sheets_svc.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
            # ปรับหัวตารางให้สอดคล้องและสวยงาม
            headers = [["วันที่ทำรายการ", "เลขที่ใบเสนอราคา", "ชื่อลูกค้า/บริษัท", "ข้อมูลติดต่อ", "ยอดรวมก่อนลด", "ส่วนลด", "ยอดสุทธิ (VAT 7%)", "ผู้ออกเอกสาร", "ลิงก์ไฟล์ PDF"]]
            sheets_svc.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=f"'{tab_name}'!A1",
                valueInputOption="USER_ENTERED", body={"values": headers}
            ).execute()

            # เพิ่มความสวยงามให้หัวตาราง (สีน้ำเงิน ตัวขาว หนา)
            spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_id = next(s['properties']['sheetId'] for s in spreadsheet.get('sheets', []) if s['properties']['title'] == tab_name)
            
            format_req = {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": len(headers[0])},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.1, "green": 0.4, "blue": 0.8},
                            "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 11},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            }
            sheets_svc.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [format_req]}).execute()
        
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [[
            now_str,
            quotation_data.get('quotation_no', ''),
            quotation_data.get('customer_name', ''),
            quotation_data.get('customer_contact', ''),
            quotation_data.get('subtotal', 0),
            quotation_data.get('total_discount', 0),
            quotation_data.get('grand_total', 0),
            user,
            pdf_url
        ]]
        sheets_svc.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=f"'{tab_name}'!A1",
            valueInputOption="USER_ENTERED", body={"values": row}
        ).execute()
    except Exception as e:
        print(f"⚠️ [Quotation] Sheet Sync Error: {e}")
    finally:
        try:
            from google_drive_service import google_manager
            google_manager.clear_context()
        except:
            pass


def _sync_sheet_append_quotation(spreadsheet_id, tab_name, row_data, org_id=None, username=None):
    try:
        from google_drive_service import google_manager
        if org_id or username:
            google_manager.set_context(username=username, org_id=org_id)
        sheets_svc = google_manager.sheets_service
        if not sheets_svc or not spreadsheet_id:
            return {"ok": False, "error": "sheets not initialized"}
        try:
            spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_exists = any(s['properties']['title'] == tab_name for s in spreadsheet.get('sheets', []))
        except Exception:
            sheet_exists = False

        if not sheet_exists:
            requests = [{'addSheet': {'properties': {'title': tab_name}}}]
            sheets_svc.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
            headers = [["วันที่ทำรายการ", "เลขที่ใบเสนอราคา", "ชื่อลูกค้า/บริษัท", "ข้อมูลติดต่อ",
                        "ยอดรวมก่อนลด", "ส่วนลด", "ยอดสุทธิ (VAT 7%)", "ผู้ออกเอกสาร", "ลิงก์ไฟล์ PDF"]]
            sheets_svc.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=f"'{tab_name}'!A1",
                valueInputOption="USER_ENTERED", body={"values": headers}
            ).execute()

            spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_id = next(s['properties']['sheetId'] for s in spreadsheet.get('sheets', []) if s['properties']['title'] == tab_name)
            format_req = {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": len(headers[0])},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.1, "green": 0.4, "blue": 0.8},
                            "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 11},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            }
            sheets_svc.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [format_req]}).execute()

        sheets_svc.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=f"'{tab_name}'!A1",
            valueInputOption="USER_ENTERED", body={"values": [row_data]}
        ).execute()
        return {"ok": True}
    except Exception as e:
        print(f"⚠️ [Quotation Sync Fallback] Sheet Sync Error: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        try:
            from google_drive_service import google_manager
            google_manager.clear_context()
        except:
            pass


@chat_bp.route("/api/quotation/create", methods=["POST"])
@login_required
def create_quotation():
    try:
        username = session.get("user")
        org_id = session.get("org_id")
        from google_drive_service import google_manager
        google_manager.set_context(username, org_id)

        quotation_data_str = request.form.get("quotation_data")
        pdf_file = request.files.get("quotation_pdf")
        
        if not quotation_data_str or not pdf_file:
            return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400
            
        quotation_data = json.loads(quotation_data_str)
        pdf_content = pdf_file.read()
        
        # 1. Upload to Drive
        original_filename = f"{quotation_data.get('quotation_no', 'QT')}_{quotation_data.get('customer_name', '')}.pdf".replace("/", "-")
        drive_link, err = google_drive_service.upload_to_date_folder(pdf_content, original_filename, "application/pdf")
        
        if err:
            return jsonify({"ok": False, "error": f"Drive Upload Error: {err}"}), 500
            
        # 2. Sync to Sheets in background via Celery serial queue
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [
            now_str,
            quotation_data.get('quotation_no', ''),
            quotation_data.get('customer_name', ''),
            quotation_data.get('customer_contact', ''),
            quotation_data.get('subtotal', 0),
            quotation_data.get('total_discount', 0),
            quotation_data.get('grand_total', 0),
            user,
            drive_link
        ]
        try:
            from tasks.sheets_queue import sheet_append_quotation
            sheet_append_quotation.delay(
                google_manager.spreadsheet_id,
                'ใบเสนอราคา (สร้างจากระบบ)',
                row_data,
                org_id=org_id,
                username=user
            )
        except (ImportError, ModuleNotFoundError):
            logger.info("Celery/Redis not available. Running sheet_append_quotation synchronously in background thread.")
            threading.Thread(
                target=_sync_sheet_append_quotation,
                args=(google_manager.spreadsheet_id, 'ใบเสนอราคา (สร้างจากระบบ)', row_data, org_id, user)
            ).start()
        
        database.log_event(f"สร้างใบเสนอราคา: {quotation_data.get('quotation_no')}", user=user, org_id=org_id)
        
        return jsonify({"ok": True, "link": drive_link})
        
    except Exception as e:
        return _err500(e)


@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        print(f"👤 User {session.get('user')} joined room: {room}")


@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)


@socketio.on('chat_message')
def handle_chat_message(data):
    # This is a real-time signal, actual DB save is still via REST for reliability
    # but we can broadcast it here to avoid polling lag
    room = data.get('room')
    if room:
        emit('new_message', data, room=room)


@socketio.on('user_online')
def handle_user_online(data):
    """Handle user coming online."""
    try:
        username = session.get("user")
        if not username:
            return emit('error', {'msg': 'Not logged in'})
        
        room = data.get('room', 'General')
        database.set_user_online(username, room)
        
        # User joins their own personal room for WebRTC signaling
        join_room(f"user_{username}")
        
        # Notify all users in the room about new Online status
        online_users = database.get_online_users()
        emit('user_status_updated', {
            'username': username,
            'status': 'online',
            'online_users': online_users
        }, room=room)
        
        print(f"[ONLINE] {username} joined room: {room}")
    except Exception as e:
        print(f"[ERROR] user_online: {e}")
        emit('error', {'msg': str(e)})


@socketio.on('user_offline')
def handle_user_offline():
    """Handle user going offline."""
    try:
        username = session.get("user")
        if not username:
            return
        
        database.set_user_offline(username)
        online_users = database.get_online_users()
        
        # Notify all connected clients about offline status
        emit('user_status_updated', {
            'username': username,
            'status': 'offline',
            'online_users': online_users
        }, broadcast=True)
        
        print(f"[OFFLINE] {username} went offline")
    except Exception as e:
        print(f"[ERROR] user_offline: {e}")


@socketio.on('user_typing')
def handle_user_typing(data):
    """Handle typing indicator."""
    try:
        username = session.get("user")
        if not username:
            return
        
        room_id = data.get('room_id', 1)
        database.set_user_typing(username, room_id)
        
        # Broadcast typing indicator to room
        emit('user_typing', {
            'username': username,
            'room_id': room_id,
            'display_name': data.get('display_name', username)
        }, room=f"room_{room_id}")
        
    except Exception as e:
        print(f"[ERROR] user_typing: {e}")


@socketio.on('user_stopped_typing')
def handle_user_stopped_typing(data):
    """Clear typing indicator."""
    try:
        username = session.get("user")
        if not username:
            return
        
        room_id = data.get('room_id', 1)
        database.clear_user_typing(username)
        
        # Broadcast to room
        emit('user_stopped_typing', {
            'username': username,
            'room_id': room_id
        }, room=f"room_{room_id}")
        
    except Exception as e:
        print(f"[ERROR] user_stopped_typing: {e}")


@socketio.on('message_read')
def handle_message_read(data):
    """Mark message as read (read receipt)."""
    try:
        username = session.get("user")
        if not username:
            return
        
        message_id = data.get('message_id')
        room_id = data.get('room_id')
        
        if message_id:
            database.mark_message_as_read(message_id, username, room_id)
            
            # Get read receipts for this message
            receipts = database.get_message_read_receipts(message_id)
            
            # Broadcast read receipts to room
            emit('message_read_receipt', {
                'message_id': message_id,
                'username': username,
                'read_by_count': len(receipts),
                'read_receipts': receipts
            }, room=f"room_{room_id}" if room_id else None)
            
            print(f"[READ] {username} read message {message_id}")
        
    except Exception as e:
        print(f"[ERROR] message_read: {e}")


@socketio.on('message_read_dm')
def handle_private_message_read(data):
    """Mark private message as read."""
    try:
        username = session.get("user")
        if not username:
            return
        
        message_id = data.get('message_id')
        if message_id:
            database.mark_private_message_as_read(message_id)
            
            # Emit read receipt to sender
            sender = data.get('sender')
            emit('dm_read_receipt', {
                'message_id': message_id,
                'read_by': username,
                'read_at': time.strftime("%Y-%m-%d %H:%M:%S")
            }, room=f"dm_{sender}_{username}" if sender else None)
            
            print(f"[DM_READ] {username} read DM {message_id}")
            
    except Exception as e:
        print(f"[ERROR] message_read_dm: {e}")


@socketio.on('join_room')
def on_join_room(data):
    """Join a room group for broadcasts."""
    try:
        room = data.get('room', '1')
        username = session.get("user")
        join_room(f"room_{room}")
        print(f"[JOIN] {username} joined room group: {room}")
        emit('message', {'text': f'{username} joined'}, room=f"room_{room}")
    except Exception as e:
        print(f"[ERROR] join_room: {e}")


@socketio.on('get_online_users')
def handle_get_online_users():
    """Get current list of online users."""
    try:
        online_users = database.get_online_users()
        emit('online_users_list', {
            'users': online_users,
            'count': len(online_users),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        print(f"[ERROR] get_online_users: {e}")
        emit('error', {'msg': str(e)})


@socketio.on('webrtc_signal')
def handle_webrtc_signal(data):
    """
    Signaling server for WebRTC Voice/Video Calls.
    """
    # Prefer sender from payload, fallback to session
    sender = data.get('sender') or session.get("user")
    if not sender:
        print(f"⚠️ [WebRTC] Signal dropped: No sender identified. Data={data}")
        return
        
    target = data.get('target')
    if not target:
        print(f"⚠️ [WebRTC] Signal dropped: No target for signal {data.get('type')} from {sender}")
        return
        
    target_room = f"user_{target}"
    data['sender'] = sender  # Ensure sender is attached
    
    print(f"📡 [WebRTC] {data.get('type').upper()} from {sender} -> {target}")
    
    # If it's a new call (offer), trigger a push notification to wake up the recipient
    if data.get('type') == 'offer':
        try:
            # Call the local function defined at the top of app.py
            call_type_th = "วิดีโอคอล" if data.get('callType') == 'video' else "สายโทรเข้า"
            send_push_notification(
                target, 
                f"📞 {sender}", 
                f"กำลังมี{call_type_th}จาก {sender}...", 
                tag="incoming_call"
            )
        except Exception as e:
            print(f"⚠️ [WebRTC] Push notification failed: {e}")

    emit('webrtc_signal', data, room=target_room)


def daily_morning_summary():
    """Daily job at 8:00 AM to summarize activities using Nong Pan persona."""
    print("🌟 Starting Daily Morning Summary Job (Nong Pan Persona)...", flush=True)
    try:
        # 1. Fetch activities
        activities = database.get_daily_activities()
        drive_stats = database.get_drive_stats()
        recent_files = database.get_drive_logs(limit=10)
        
        # 2. Prepare context
        context = "กิจกรรมของบริษัทในรอบ 24 ชม. ที่ผ่านมา:\n"
        if activities.get("posts"):
            context += "📢 ข่าวสารใหม่:\n" + "\n".join([f"- {p['title']}" for p in activities["posts"][:3]]) + "\n"
        if activities.get("schedules"):
            context += "📅 ตารางงานวันนี้:\n" + "\n".join([f"- {s['time']} {s['title']}" for s in activities["schedules"][:3]]) + "\n"
        if recent_files:
            context += "📂 เอกสารอัปโหลดใหม่:\n" + "\n".join([f"- {f['filename']} ({f['category']})" for f in recent_files[:5]]) + "\n"

        prompt = (
            "คุณคือ 'น้องพั้นซ์' (Punch) AI Assistant สาวออฟฟิศสุดน่ารักและเป็นกันเอง "
            "ช่วยสรุป Morning Brief ข้อมูลสำคัญประจำวันนี้ให้กับพี่ๆ ในทีม เพื่อเป็นกำลังใจและแนวทางในการทำงาน "
            "โดยใช้ภาษาที่เป็นกันเองและน่ารักมากๆ เหมือนมีเพื่อนร่วมงานที่คอยดูแลและให้ความใส่ใจพี่ๆ ทุกคนนะคะ\n\n"
            f"{context}\n\n"
            "สรุปในสไตล์น้องพั้นซ์:"
        )
        
        summary = ai_providers.generate_response(prompt)
        
        # 3. Broadcast to all users (or a specific group) via LINE
        if summary:
            broadcast_line_announcement("🌟 Morning Brief จากน้องพั้นซ์", summary)
            print("🌟 Daily Summary sent via LINE.")
            
    except Exception as e:
        print(f"❌ Daily Summary Job Error: {e}")


@chat_bp.route('/api/drive/contents', methods=['GET'])
@login_required
def get_drive_contents():
    folder_id = request.args.get('folder_id') or 'root'
    try:
        username = session.get("user")
        org_id = session.get("org_id")
        google_manager.set_context(username, org_id)
        
        if not google_manager.drive_service:
            return jsonify({
                "ok": False,
                "error": "Google Drive ขององค์กรยังไม่ได้เชื่อมต่อค่ะ กรุณาเชื่อมต่อในเมนูการตั้งค่า"
            }), 400
            
        contents = google_drive_service.list_folder_contents(folder_id)
        
        folder_name = "My Drive"
        if folder_id and folder_id != "root":
            try:
                folder_meta = google_manager.drive_service.files().get(
                    fileId=folder_id, fields="name", supportsAllDrives=True
                ).execute()
                folder_name = folder_meta.get("name", "Unknown Folder")
            except Exception:
                folder_name = "Folder"
                
        return jsonify({
            "ok": True,
            "items": contents,
            "folder_name": folder_name
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@chat_bp.route('/api/drive/rename', methods=['POST'])
@admin_required
def rename_drive_file():
    data = request.json or {}
    file_id = data.get('file_id')
    new_name = data.get('new_name')
    if not file_id or not new_name:
        return jsonify({"ok": False, "error": "Missing parameters"}), 400
    
    username = session.get("user")
    org_id = session.get("org_id")
    google_manager.set_context(username, org_id)
    if google_drive_service.rename_file(file_id, new_name):
        database.log_event(f"Renamed Drive file {file_id} to {new_name}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Failed to rename"}), 500


@chat_bp.route('/api/drive/delete', methods=['DELETE', 'POST'])
@admin_required
def delete_drive_file():
    data = request.json or {}
    file_id = data.get('file_id')
    if not file_id:
        return jsonify({"ok": False, "error": "Missing file_id"}), 400
    
    username = session.get("user")
    org_id = session.get("org_id")
    google_manager.set_context(username, org_id)
    if google_drive_service.delete_file(file_id):
        database.log_event(f"Deleted Drive file {file_id}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Failed to delete"}), 500


@chat_bp.route('/api/line/groups', methods=['GET'])
@login_required
def get_line_groups():
    username = session.get("user")
    mappings = database.list_group_mappings(username)
    return jsonify({"ok": True, "mappings": mappings})


@chat_bp.route('/api/line/groups/bind', methods=['POST'])
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


@chat_bp.route('/api/line/groups/unbind/<group_id>', methods=['DELETE'])
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


@chat_bp.route('/api/line/groups/<group_id>/settings', methods=['PUT', 'POST'])
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


@chat_bp.route('/api/google/folders', methods=['GET'])
@login_required
@billing.require_feature("google_sheets")
def get_google_folders():
    username = session.get("user")
    org_id = get_current_org_id()
    if not oauth2_service.is_org_connected(org_id):
        return jsonify({"ok": False, "error": "google_drive_not_connected"}), 400
        
    mgr = google_manager
    mgr.set_context(username, org_id)
    # Note: GoogleWorkspaceManager is a Singleton. Individual user manager is not supported in this version.
    folders = mgr.list_subfolders()
    return jsonify({"ok": True, "folders": folders})


@chat_bp.route('/api/drive/upload', methods=['POST'])
@login_required
def web_drive_upload():
    """Allows web users to upload billing/expense documents directly to Google Drive.
    It runs the same AI parsing, EMVCo QR code scanning, and Google Sheets logging as the LINE webhook.
    """
    files = request.files.getlist("files")
    folder_id = request.form.get("folder_id")
    folder_name = request.form.get("folder_name", "ทั่วไป")
    
    if not files or not files[0].filename:
        return jsonify({"ok": False, "error": "ไม่พบไฟล์ที่ต้องการอัปโหลดค่ะ"}), 400
        
    username = session.get("user")
    org_id = session.get("org_id")
    try:
        org_id = int(org_id) if org_id else 1
    except:
        org_id = 1
        
    google_manager.set_context(username=username, org_id=org_id)
    
    results = []
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Check billing limits before proceeding
    _ok, _used, _limit = billing.check_usage_allowed(org_id, "expense_count")
    if not _ok:
        return jsonify({"ok": False, "error": "limit_reached", "message": f"ใช้โควต้าบันทึกบิลครบ {_limit} รายการในเดือนนี้แล้วค่ะ"}), 403
        
    def process_file_item(f):
        original_name = f.filename or "web_upload"
        mimetype = f.mimetype or "application/octet-stream"
        
        # Verify file safety before processing
        is_safe, safety_err = validate_uploaded_file(f, original_name)
        if not is_safe:
            return {"status": "unsafe_file", "name": original_name, "error": safety_err}
            
        f.seek(0)
        content = f.read()
        if not content:
            return {"status": "empty_file", "name": original_name}
            
        # Check and increment billing limit
        _e_ok, _e_used, _e_limit = billing.check_and_increment(org_id, "expense_count")
        if not _e_ok:
            return {"status": "limit_reached", "name": original_name}
            
        # Run AI Smart Scan
        analysis = None
        f_type = "file"
        if mimetype.startswith("image/"): f_type = "image"
        elif mimetype.startswith("audio/"): f_type = "audio"
        
        if (f_type in ["image", "file"] and mimetype in ["image/jpeg", "image/png", "application/pdf"]) or f_type == "audio":
            try:
                analysis = ai_providers.analyze_media_contents(content, mimetype)
                if analysis and analysis.get("smart_name"):
                    ext = os.path.splitext(original_name)[1]
                    original_name = analysis["smart_name"]
                    if not original_name.endswith(ext): original_name += ext
            except Exception as e:
                logger.error(f"AI analysis failed in web upload: {e}")
                
        # Upload file to Drive
        link, upload_err = google_manager.upload_file(content, original_name, mimetype, folder_id=folder_id, org_id=org_id, username=username)
        if not link:
            return {"status": "upload_failed", "name": original_name, "error": str(upload_err)}
            
        # Sanitize data for Google Sheets
        raw_ext = analysis.get("extracted_data", {}) if analysis else {}
        sanitized_ext = raw_ext.copy()
        if "date" not in sanitized_ext or not sanitized_ext["date"]:
            sanitized_ext["date"] = datetime.now().strftime("%d/%m/%Y")
        sanitized_ext["category"] = folder_name
        for field in ["time", "sender", "receiver", "memo", "ref_number"]:
            if field not in sanitized_ext: sanitized_ext[field] = "-"
            
        # Scan QR Code
        verification_status = "-"
        if folder_name == "สลิปโอนเงิน" and content:
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
                        from tools.emvco_parser import EMVCoParser
                        parser = EMVCoParser()
                        decoded = parser.decode_slip_qr(val_qr)
                        is_valid_slip = False
                        if val_qr.startswith("000201") and ("A000000677" in val_qr):
                            is_valid_slip = True
                        elif decoded.get("is_valid_emvco"):
                            raw_tags = decoded.get("raw_tags", {})
                            if "00" in raw_tags:
                                inner = parser.parse_sub_tlv(raw_tags["00"])
                                if inner.get("00") == "000001":
                                    is_valid_slip = True
                        if is_valid_slip:
                            verification_status = "ผ่าน (คิวอาร์จริง)"
                        elif val_qr.startswith("https://") or "qr" in val_qr.lower():
                            verification_status = "ผ่าน (ลิงก์คิวอาร์)"
                        else:
                            verification_status = "ไม่ผ่าน (คิวอาร์ไม่ใช่สลิป)"
                    else:
                        verification_status = "ไม่ผ่าน (ไม่มี QR Code)"
            except Exception as qr_err:
                logger.error(f"Error scanning QR Code in web upload: {qr_err}")
                
        log_data = {
            "file_link": link,
            "summary": analysis.get("summary", f"Web upload: {original_name}") if analysis else f"Web upload: {original_name}",
            "original_filename": f.filename or "web_upload",
            "extracted_data": sanitized_ext,
            "line_sender_name": f"Web (พี่ {username})",
            "verification_status": verification_status
        }
        
        # Log to Sheets
        log_res = google_manager.log_expense(log_data, org_id=org_id, username=username)
        
        # Log to local DB
        amt = 0.0
        try:
            amt_raw = sanitized_ext.get("net_amount", 0)
            if not amt_raw or amt_raw == "-": amt_raw = 0
            if isinstance(amt_raw, str):
                amt = float(amt_raw.replace(',', '').replace('฿', '').strip())
            else:
                amt = float(amt_raw)
        except Exception:
            amt = 0.0
            
        try:
            database.add_drive_log(
                filename=f.filename or "web_upload",
                category=sanitized_ext.get("category", "General"),
                amount=amt,
                doc_date=sanitized_ext.get("date"),
                summary=analysis.get("summary") if analysis else f"Web upload: {f.filename}",
                file_link=link,
                user_id=f"web_{username}",
                org_id=org_id
            )
        except Exception as dbe:
            logger.error(f"Database Log Error in web upload: {dbe}")
            
        status = "success"
        if log_res and log_res.get("error") == "duplicate":
            status = "duplicate"
            
        return {
            "status": status,
            "name": original_name,
            "link": link,
            "sheet": log_res.get("sheet") if log_res else "ทั่วไป",
            "row": log_res.get("row") if log_res else 0,
            "amount": amt,
            "date": sanitized_ext.get("date"),
            "category": folder_name
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_file_item, file_obj) for file_obj in files]
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    # Run async reconciliation in background
    _has_success = any(r and r.get("status") in ("success", "duplicate") for r in results)
    if _has_success:
        def run_reconciliation_async(user, oid):
            try:
                google_manager.set_context(username=user, org_id=oid)
                google_manager.auto_reconcile_internal()
            except Exception as _rec_err:
                logger.warning(f"⚠️ Web upload reconciliation failed: {_rec_err}")
            finally:
                google_manager.clear_context()
        
        import threading
        threading.Thread(target=run_reconciliation_async, args=(username, org_id), daemon=True).start()
        
    google_manager.clear_context()
    return jsonify({"ok": True, "results": results})


@chat_bp.route("/api/dashboard/financial-insights")
@login_required
@_limiter.limit("10 per minute; 30 per hour")
def financial_insights():
    org_id = get_current_org_id()
    # Fetch all logs for this organization to get enough historical data
    logs = database.get_drive_logs(limit=2000, org_id=org_id)
    
    if not logs:
        return jsonify({
            "ok": True,
            "historic_months": [],
            "forecast_months": [],
            "categories": [],
            "insights": "ยังไม่มีประวัติการอัปโหลดบันทึกค่าใช้จ่ายในฐานข้อมูลสำหรับองค์กรนี้ค่ะ"
        })
        
    # Group by month (using YYYY-MM) and category
    monthly_data = {} # YYYY-MM -> total_amount
    category_data = {} # Category -> total_amount
    
    import re
    from datetime import datetime
    
    for log in logs:
        amount = log.get("amount") or 0.0
        try:
            amount = float(amount)
        except:
            amount = 0.0
            
        # Determine the month
        log_month = None
        # Try to parse doc_date first
        doc_date = log.get("doc_date")
        if doc_date and isinstance(doc_date, str):
            # Try DD/MM/YYYY
            m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", doc_date)
            if m:
                log_month = f"{m.group(3)}-{int(m.group(2)):02d}"
            else:
                # Try YYYY-MM-DD
                m2 = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", doc_date)
                if m2:
                    log_month = f"{m2.group(1)}-{int(m2.group(2)):02d}"
        
        # Fallback to created_at (format YYYY-MM-DD HH:MM:SS)
        if not log_month:
            created_at = log.get("created_at")
            if created_at and isinstance(created_at, str):
                m3 = re.match(r"(\d{4})-(\d{2})", created_at)
                if m3:
                    log_month = m3.group(0)
                    
        if not log_month:
            # Fallback to current month
            log_month = datetime.now().strftime("%Y-%m")
            
        monthly_data[log_month] = monthly_data.get(log_month, 0.0) + amount
        
        cat = log.get("category") or "ทั่วไป"
        category_data[cat] = category_data.get(cat, 0.0) + amount

    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())
    historic_list = [{"month": m, "total": monthly_data[m]} for m in sorted_months]
    
    # Calculate Forecasting: Linear Regression + 3-month Moving Average
    forecast_list = []
    if len(historic_list) >= 1:
        past_totals = [x["total"] for x in historic_list]
        avg_outflow = sum(past_totals) / len(past_totals)
        
        slope = 0.0
        if len(historic_list) >= 2:
            x_vals = list(range(len(historic_list)))
            y_vals = past_totals
            x_mean = sum(x_vals) / len(x_vals)
            y_mean = sum(y_vals) / len(y_vals)
            num = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(len(historic_list)))
            den = sum((x_vals[i] - x_mean) ** 2 for i in range(len(historic_list)))
            if den != 0:
                slope = num / den
                
        # Generate predictions for next 3 months
        last_m_str = sorted_months[-1]
        try:
            last_m_dt = datetime.strptime(last_m_str, "%Y-%m")
        except:
            last_m_dt = datetime.now()
            
        for i in range(1, 4):
            new_month = last_m_dt.month + i
            new_year = last_m_dt.year
            while new_month > 12:
                new_month -= 12
                new_year += 1
            f_month_str = f"{new_year}-{new_month:02d}"
            
            last_actual = past_totals[-1]
            pred_linear = last_actual + slope * i
            
            moving_avg = sum(past_totals[-3:]) / min(len(past_totals), 3)
            
            predicted_value = max(0.0, (pred_linear * 0.6) + (moving_avg * 0.4))
            
            forecast_list.append({
                "month": f_month_str,
                "total": round(predicted_value, 2)
            })
            
    # Prepare text summary for Gemini AI
    historic_text = "\n".join([f"- เดือน {x['month']}: ยอดรวม {x['total']:,.2f} บาท" for x in historic_list[-6:]])
    category_text = "\n".join([f"- หมวดหมู่ '{k}': ยอดสะสม {v:,.2f} บาท" for k, v in category_data.items()])
    forecast_text = "\n".join([f"- คาดการณ์เดือน {x['month']}: {x['total']:,.2f} บาท" for x in forecast_list])
    
    prompt = f"""คุณเป็น AI ผู้เชี่ยวชาญด้านการเงิน บัญชีองค์กร และการวางแผนภาษี (Financial Analyst)
วิเคราะห์ข้อมูลค่าใช้จ่ายและประเมินแนวโน้มทางการเงินขององค์กร เพื่อหาคำแนะนำเชิงลึก (Insights)

ข้อมูลค่าใช้จ่ายย้อนหลัง (สูงสุด 6 เดือน):
{historic_text}

สรุปยอดสะสมแยกตามหมวดหมู่:
{category_text}

การคาดการณ์รายจ่ายล่วงหน้า 3 เดือน:
{forecast_text}

โปรดสร้างสรุปรายงานวิเคราะห์ทางการเงินและข้อเสนอแนะเชิงลึก โดยระบุหัวข้อเหล่านี้เป็นภาษาไทยให้กระชับ ชัดเจน และดูเป็นมืออาชีพสำหรับระดับบริหาร:
1. 📈 สรุปภาพรวมและแนวโน้มการใช้จ่าย (วิเคราะห์ทิศทางและแนวโน้มหลัก)
2. 💡 โอกาสในการประหยัดและจุดที่ต้องควบคุม (ชี้เป้ากลุ่มรายจ่ายสูงผิดปกติหรือจุดรั่วไหล)
3. 🧾 คำแนะนำด้านการวางแผนภาษีองค์กร (การจัดการสิทธิ์ลดหย่อนหรือความถูกต้องของเอกสาร)
4. 🚀 การวางแผนสำรองเงินสดและ Runway (คำแนะนำในการเตรียมเงินสำรอง)

ใช้การจัดรูปแบบด้วย Markdown ที่สวยงาม (ใช้ตัวหนา, อิโมจิ, รายการสัญลักษณ์) ไม่ต้องมีเกริ่นนำหรือคำลงท้ายยาวๆ เริ่มสรุปได้ทันที:"""

    insights = "ไม่สามารถสร้างการวิเคราะห์ AI ได้ในขณะนี้ค่ะ"
    try:
        _allowed, _used, _limit = billing.check_and_increment(org_id, "ai_query_count")
        if _allowed:
            provider = ai_providers.get_provider()
            ai_res = ""
            for chunk in provider.chat_stream(prompt, [], "คุณคือ AI ผู้เชี่ยวชาญด้านบัญชีและการเงิน"):
                if chunk: ai_res += chunk
            insights = ai_res.strip()
        else:
            insights = f"⚠️ สิทธิ์ใช้งาน AI ของคุณสำหรับเดือนนี้เต็มแล้ว ({_limit} ครั้ง) กรุณาอัปเกรดสิทธิ์ของคุณเพื่อรับข้อมูลวิเคราะห์เชิงลึกจาก AI"
    except Exception as e:
        logger.error(f"AI insights generation error: {e}")
        insights = f"⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI: {e}"
        
    return jsonify({
        "ok": True,
        "historic_months": historic_list,
        "forecast_months": forecast_list,
        "categories": [{"category": k, "total": v} for k, v in category_data.items()],
        "insights": insights
    })

