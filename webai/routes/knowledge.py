# -*- coding: utf-8 -*-
"""
routes/knowledge.py — Knowledge Base, RAG, Web Ingestion & Document Blueprint
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

logger = logging.getLogger("OrgChatAI.Knowledge")

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
    logger.error(f"[{context or 'Knowledge'}] {type(e).__name__}: {e}", exc_info=True)
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง"}), 500

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route("/api/kb/cleanup-stale", methods=["POST"])
@login_required
def cleanup_stale_kb():
    """ล้างไฟล์ KB ที่ค้างอยู่ที่ status='processing' นานเกิน 30 นาที"""
    cleaned = rag_engine.cleanup_stale_processing(max_age_minutes=30)
    return jsonify({"ok": True, "cleaned": cleaned,
                    "message": f"ล้างไฟล์ค้าง {cleaned} ไฟล์"})


# ═══════════════════════════════════════════════════════════════
# 🌐 Smart Web Crawler & URL Ingestion Endpoints
# ═══════════════════════════════════════════════════════════════

@knowledge_bp.route("/api/kb/crawl-preview", methods=["POST"])
@login_required
def kb_crawl_preview():
    """Extract and preview content from a web URL before ingesting."""
    data = request.json or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "กรุณาระบุ URL เว็บไซต์ที่ต้องการตรวจสอบ"}), 400

    crawler = web_crawler.WebCrawler(timeout=12, max_pages=1)
    page_data = crawler.extract_page_content(url)

    if not page_data.get("success"):
        return jsonify({"ok": False, "error": f"ไม่สามารถดึงข้อมูลได้: {page_data.get('error', 'Unknown error')}"}), 400

    return jsonify({
        "ok": True,
        "data": {
            "url": page_data["url"],
            "title": page_data["title"],
            "description": page_data.get("description", ""),
            "word_count": page_data["word_count"],
            "char_count": page_data["char_count"],
            "preview_text": page_data["text"][:1200] + ("..." if len(page_data["text"]) > 1200 else ""),
            "internal_links_count": len(page_data.get("internal_links", [])),
            "internal_links": page_data.get("internal_links", [])[:10]
        }
    })


@knowledge_bp.route("/api/kb/crawl-ingest", methods=["POST"])
@login_required
def kb_crawl_ingest():
    """Crawl web page(s), chunk text, and index into ChromaDB Knowledge Base."""
    if not can_edit_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการเพิ่มข้อมูลลงคลังความรู้"}), 403

    data = request.json or {}
    url = (data.get("url") or "").strip()
    crawl_subpages = bool(data.get("crawl_subpages", False))
    max_pages = min(int(data.get("max_pages", 5)), 20)
    dept = data.get("department", "General")
    category_id = data.get("category_id")
    if category_id is not None:
        try: category_id = int(category_id)
        except (ValueError, TypeError): category_id = None
        
    org_id = get_current_org_id()

    if not url:
        return jsonify({"ok": False, "error": "กรุณาระบุ URL เว็บไซต์ที่ต้องการเรียนรู้"}), 400

    try:
        result = web_crawler.ingest_website_url(
            url=url,
            crawl_subpages=crawl_subpages,
            max_pages=max_pages,
            department=dept,
            category_id=category_id,
            org_id=org_id
        )

        if not result.get("success"):
            return jsonify({"ok": False, "error": result.get("error", "การดึงข้อมูลล้มเหลว")}), 400

        user = session.get("user", "Admin")
        database.log_event(
            f"Crawled website: {url} ({result.get('pages_crawled', 1)} pages, {result.get('total_chunks', 0)} chunks)",
            user=user,
            org_id=org_id
        )

        return jsonify({
            "ok": True,
            "message": f"เรียนรู้ข้อมูลจากเว็บไซต์สำเร็จ! ({result.get('pages_crawled', 1)} หน้า, {result.get('total_chunks', 0)} ชิ้นส่วน)",
            "result": result
        })
    except Exception as e:
        logger.error(f"Crawl ingestion error: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500


@knowledge_bp.route("/api/kb/crawl-refresh", methods=["POST"])
@login_required
def kb_crawl_refresh():
    """Re-crawl an existing indexed web URL to update its Knowledge Base chunks."""
    if not can_edit_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการอัปเดตข้อมูล"}), 403

    data = request.json or {}
    file_id = data.get("file_id")
    url = data.get("url")

    meta = rag_engine._load_meta()
    if file_id and file_id in meta:
        url = meta[file_id].get("url") or meta[file_id].get("path")
        dept = meta[file_id].get("department", "General")
        cat_id = meta[file_id].get("category_id")
    elif not url:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูล URL ที่ต้องการรีเฟรช"}), 400
    else:
        dept = data.get("department", "General")
        cat_id = data.get("category_id")

    org_id = get_current_org_id()

    try:
        result = web_crawler.ingest_website_url(
            url=url,
            crawl_subpages=False,
            max_pages=1,
            department=dept,
            category_id=cat_id,
            org_id=org_id
        )
        if not result.get("success"):
            return jsonify({"ok": False, "error": result.get("error", "การรีเฟรชข้อมูลล้มเหลว")}), 400

        return jsonify({
            "ok": True,
            "message": f"อัปเดตข้อมูลจากเว็บไซต์เรียบร้อยแล้ว ({result.get('total_chunks', 0)} ชิ้นส่วน)",
            "result": result
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@knowledge_bp.route("/api/departments")
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


@knowledge_bp.route("/api/kb/categories", methods=["GET"])
@login_required
def list_categories():
    user = session.get("user", "Admin")
    categories = database.get_categories(user, org_id=get_current_org_id())
    return jsonify({"ok": True, "categories": categories})


@knowledge_bp.route("/api/kb/categories", methods=["POST"])
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


@knowledge_bp.route("/api/kb/categories/settings", methods=["POST"])
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


@knowledge_bp.route("/api/kb/categories/<int:cat_id>", methods=["DELETE"])
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


@knowledge_bp.route("/api/kb/categories/access/<int:cat_id>", methods=["GET"])
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


@knowledge_bp.route("/api/kb/search")
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


@knowledge_bp.route("/api/kb/files/assign", methods=["POST"])
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


@knowledge_bp.route("/api/personas", methods=["GET"])
@login_required
def get_personas():
    try:
        org_id = get_current_org_id()
        personas = database.get_all_personas_v2(org_id)
        return jsonify({"ok": True, "personas": personas})
    except Exception as e:
        logger.error(f"[personas] {e}", exc_info=True)
        return jsonify({"ok": True, "personas": []})


@knowledge_bp.route("/api/kb/files/view/<file_id>")
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
        
    import mimetypes
    guessed_mime, _ = mimetypes.guess_type(path.name)
    mime = guessed_mime or ('application/pdf' if file_info.get('type') == 'pdf' else 'application/octet-stream')
    return send_file(path, mimetype=mime, download_name=path.name)


@knowledge_bp.route("/api/kb/page-preview", methods=["GET"])
@login_required
def get_kb_page_preview():
    """
    Renders a specific page of a PDF file as PNG or returns page text with highlight snippet.
    Query params: file_id or filename, page (1-based), render_image (1 or 0)
    """
    if not can_view_knowledge_base():
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์เข้าถึง"}), 403
    org_id = get_current_org_id()
    file_id = request.args.get("file_id")
    filename = request.args.get("filename")
    try:
        page_num = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page_num = 1
    render_img = request.args.get("render_image", "0") == "1"

    files = rag_engine.list_files(org_id=org_id)
    file_info = None
    if file_id:
        file_info = next((f for f in files if f["file_id"] == file_id), None)
    elif filename:
        file_info = next((f for f in files if f.get("filename") == filename or f.get("name") == filename), None)

    if not file_info:
        return jsonify({"ok": False, "error": "ไม่พบไฟล์เอกสารในคลังความรู้"}), 404

    path = Path(file_info["path"])
    if not path.exists():
        return jsonify({"ok": False, "error": "ไม่พบไฟล์เอกสารบนดิสก์"}), 404

    # If it's a PDF:
    if path.suffix.lower() == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            total_pages = len(doc)
            target_idx = max(0, min(page_num - 1, total_pages - 1))
            page = doc[target_idx]
            page_text = page.get_text()

            if render_img:
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                doc.close()
                return send_file(io.BytesIO(img_bytes), mimetype="image/png")

            doc.close()
            return jsonify({
                "ok": True,
                "filename": file_info.get("filename") or file_info.get("name") or path.name,
                "file_id": file_info["file_id"],
                "total_pages": total_pages,
                "current_page": target_idx + 1,
                "page_text": page_text,
                "is_pdf": True,
                "image_preview_url": f"/api/kb/page-preview?file_id={file_info['file_id']}&page={target_idx + 1}&render_image=1"
            })
        except Exception as e:
            logger.error(f"Error rendering PDF page: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    # If it's another file type (.pptx, .docx, .txt, .csv)
    return jsonify({
        "ok": True,
        "filename": file_info.get("filename") or file_info.get("name") or path.name,
        "file_id": file_info["file_id"],
        "is_pdf": False,
        "total_pages": 1,
        "current_page": 1,
        "view_url": f"/api/kb/files/view/{file_info['file_id']}"
    })


@knowledge_bp.route("/api/kb/compare", methods=["POST"])
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


@knowledge_bp.route("/api/csv/<file_id>", methods=["GET", "POST"])
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


@knowledge_bp.route("/api/txt/<file_id>", methods=["GET", "POST"])
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


@knowledge_bp.route("/api/sync", methods=["POST"])
@admin_required
def sync_kb():
    results = rag_engine.sync_uploads()
    return jsonify({"ok": True, "results": results})


@knowledge_bp.route("/api/kb/reprocess/<file_id>", methods=["POST"])
@login_required
def kb_reprocess_route(file_id):
    """Re-chunks and re-embeds a specific file in the Knowledge Base."""
    if not can_edit_knowledge_base():
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ในการจัดการไฟล์ในคลังข้อมูล"}), 403
    org_id = get_current_org_id()
    res = rag_engine.reprocess_file(file_id, org_id=org_id)
    if res.get("ok"):
        user = session.get("user", "Admin")
        database.log_event(f"Reprocessed file ID {file_id}", user=user, org_id=org_id)
        return jsonify(res)
    return jsonify(res), 400


@knowledge_bp.route("/api/prune", methods=["POST"])
@admin_required
def prune_kb_route():
    count = rag_engine.prune_kb()
    return jsonify({"ok": True, "pruned": count})


@knowledge_bp.route("/api/wipe", methods=["POST"])
@admin_required
def wipe():
    ok = rag_engine.wipe_knowledge_base()
    return jsonify({"ok": ok})


