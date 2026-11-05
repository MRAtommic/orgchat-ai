# -*- coding: utf-8 -*-
"""
routes/quotation_crm.py — Quotation Generator, Financial Insights & AI Tools Blueprint
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

logger = logging.getLogger("OrgChatAI.Quotation_crm")

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
    logger.error(f"[{context or 'Quotation_crm'}] {type(e).__name__}: {e}", exc_info=True)
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง"}), 500

quotation_bp = Blueprint('quotation_crm', __name__)

@quotation_bp.route("/api/reconcile/save", methods=["POST"])
@login_required
def save_reconcile_entry():
    """Saves AI extracted receipt/slip data to Google Sheets."""
    try:
        from google_drive_service import google_manager
        data = request.json or {}
        username = session.get("user", "Admin")
        org_id = get_current_org_id()
        google_manager.set_context(username, org_id)
        res = google_manager.log_expense(data, org_id=org_id, username=username)
        return jsonify({"ok": True, "result": res})
    except Exception as e:
        logger.error(f"Error in /api/reconcile/save: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500


@quotation_bp.route("/api/export/pdf", methods=["POST"])
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
        logger.error(f"❌ PDF Export Error: {e}")
        return _err500(e)


@quotation_bp.route("/api/ai/extract-tasks", methods=["POST"])
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
        logger.error(f"[Quotation] Sheet Sync Error: {e}")
    finally:
        try:
            from google_drive_service import google_manager
            google_manager.clear_context()
        except Exception as e:
            logger.debug(f"[Quotation] clear_context notice: {e}")


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
        logger.error(f"[Quotation Sync Fallback] Sheet Sync Error: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        try:
            from google_drive_service import google_manager
            google_manager.clear_context()
        except Exception as e:
            logger.debug(f"[Quotation Sync Fallback] clear_context notice: {e}")


@quotation_bp.route("/api/quotation/create", methods=["POST"])
@login_required
def create_quotation():
    try:
        user = username = session.get("user")
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
        except Exception as _celery_err:
            logger.info(f"Celery/Redis unavailable ({_celery_err}). Running sheet_append_quotation synchronously in background thread.")
            threading.Thread(
                target=_sync_sheet_append_quotation,
                args=(google_manager.spreadsheet_id, 'ใบเสนอราคา (สร้างจากระบบ)', row_data, org_id, user)
            ).start()
        
        database.log_event(f"สร้างใบเสนอราคา: {quotation_data.get('quotation_no')}", user=user, org_id=org_id)
        
        return jsonify({"ok": True, "link": drive_link})
        
    except Exception as e:
        return _err500(e)


@quotation_bp.route("/api/dashboard/financial-insights")
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
        except (ValueError, TypeError):
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
        except (ValueError, TypeError):
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


# ═══════════════════════════════════════════════════════════════
# 🧠 Multi-Agent AI Debate & Decision Room (Executive Boardroom)
# ═══════════════════════════════════════════════════════════════
