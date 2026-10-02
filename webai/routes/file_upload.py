# -*- coding: utf-8 -*-
"""
routes/file_upload.py — File Upload, Knowledge Files & Google Drive Blueprint
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

logger = logging.getLogger("OrgChatAI.File_upload")

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
    logger.error(f"[{context or 'File_upload'}] {type(e).__name__}: {e}", exc_info=True)
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง"}), 500

file_bp = Blueprint('file_upload', __name__)

from routes.line_webhook import get_channel_access_token

@file_bp.route("/api/upload", methods=["POST"])
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


@file_bp.route("/api/files")
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


@file_bp.route("/api/files/<file_id>", methods=["DELETE"])
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


@file_bp.route("/api/files/<file_id>/category", methods=["PUT"])
@login_required
def update_file_category_route(file_id):
    """Updates category for a specific file in Knowledge Base."""
    data = request.json or {}
    category_id = data.get("category_id")
    if category_id is not None and str(category_id).isdigit():
        category_id = int(category_id)
    elif category_id == "unassigned" or not category_id:
        category_id = None
    
    ok = rag_engine.update_file_category(file_id, category_id)
    if ok:
        database.update_file_category(file_id, category_id)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบไฟล์ที่ระบุ"}), 404


@file_bp.route("/api/files/<file_id>/rename", methods=["PUT", "POST"])
@login_required
def rename_file_route(file_id):
    """Renames a file in Knowledge Base."""
    if not can_edit_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการแก้ไขไฟล์ในคลังข้อมูล (ติดต่อผู้ดูแลระบบเพื่อขอสิทธิ์)"}), 403

    data = request.json or {}
    new_name = (data.get("name") or data.get("new_name") or "").strip()
    if not new_name:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อไฟล์ใหม่"}), 400

    org_id = get_current_org_id()
    res = rag_engine.rename_file(file_id, new_name, org_id=org_id)
    if res.get("ok"):
        user = session.get("user", "Admin")
        database.log_event(f"Renamed file ID {file_id} to '{res.get('name')}'", user=user, org_id=org_id)
        return jsonify(res)
    return jsonify(res), 400



@file_bp.route("/api/files/download/<filename>")
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


@file_bp.route('/api/drive/contents', methods=['GET'])
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


@file_bp.route('/api/drive/rename', methods=['POST'])
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


@file_bp.route('/api/drive/delete', methods=['DELETE', 'POST'])
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


@file_bp.route('/api/google/folders', methods=['GET'])
@login_required
def get_google_folders():
    try:
        username = session.get("user")
        org_id = get_current_org_id()
        if not oauth2_service.is_org_connected(org_id):
            return jsonify({"ok": False, "error": "google_drive_not_connected", "folders": []}), 200
            
        mgr = google_manager
        mgr.set_context(username, org_id)
        folders = mgr.list_subfolders() or []
        return jsonify({"ok": True, "folders": folders})
    except Exception as e:
        logger.warning(f"Failed to fetch Google Drive folders: {e}")
        return jsonify({"ok": False, "error": str(e), "folders": []}), 200



@file_bp.route('/api/drive/upload', methods=['POST'])
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
    except (ValueError, TypeError):
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
                
        # --- Offline-First: Always save local backup first to prevent any data loss ---
        from tools.offline_storage import save_local_receipt_backup
        rel_backup_path, abs_backup_path, local_backup_url = save_local_receipt_backup(content, original_name)

        # Upload file to Drive (with graceful offline fallback)
        link, upload_err = google_manager.upload_file(content, original_name, mimetype, folder_id=folder_id, org_id=org_id, username=username)
        is_offline_backup = False
        if not link:
            logger.warning(f"⚠️ Drive upload unavailable in web upload for '{original_name}': {upload_err}. Using resilient local backup.")
            link = local_backup_url
            is_offline_backup = True
            
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
        
        if is_offline_backup:
            database.add_offline_upload(
                org_id=org_id,
                username=username,
                user_id=f"web_{username}",
                original_filename=f.filename or "web_upload",
                local_filepath=abs_backup_path,
                mimetype=mimetype,
                folder_id=folder_id,
                folder_name=folder_name,
                analysis=analysis,
                extracted_data=sanitized_ext,
                verification_status=verification_status,
                line_sender_name=f"Web (พี่ {username})"
            )
            log_res = {"ok": True, "sheet": folder_name, "row": 0}
        else:
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
                org_id=org_id,
                sync_status="pending_cloud_sync" if is_offline_backup else "synced",
                local_filepath=abs_backup_path
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
            "sheet": log_res.get("sheet") if log_res else (folder_name or "ทั่วไป"),
            "row": log_res.get("row") if log_res else 0,
            "amount": amt,
            "date": sanitized_ext.get("date"),
            "category": folder_name,
            "is_offline_backup": is_offline_backup,
            "message": "บันทึกในเครื่องเรียบร้อยแล้ว (สำรองข้อมูลปลอดภัย รอซิงค์ Cloud)" if is_offline_backup else "บันทึกสำเร็จ"
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


