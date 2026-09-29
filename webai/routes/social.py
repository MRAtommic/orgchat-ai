# -*- coding: utf-8 -*-
"""
Social Blueprint — Feed Posts, Comments, Likes, Reactions, Polls,
Wiki Pages, Kanban Board, Link Preview
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, send_from_directory, send_file, abort, redirect, session
from werkzeug.utils import secure_filename
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
from functools import wraps
from bs4 import BeautifulSoup
import requests as http_requests
import logging

from fpdf import FPDF

import database
import rag_engine
import export_service
import ai_providers
import notification_db
import billing
import payment
from google_drive_service import google_manager, GoogleWorkspaceManager
from task_tracker import db_task_tracker

from routes.shared import (
    VERSION, socketio, _limiter, login_required, admin_required,
    PENDING_LINE_LINKS, _OAUTH_STATES, _store_oauth_state, _pop_oauth_state,
    send_push_notification, batch_send_push_notification,
    get_weather_context, THAI_HOLIDAYS_2026, get_current_time,
    VAPID_PUBLIC_KEY,
    get_current_org_id, is_admin,
    _is_safe_url, _get_gemini_api_key,
    validate_uploaded_file,
)
from routes.chat import send_line_push_notification

logger = logging.getLogger("OrgChatAI.Social")

social_bp = Blueprint('social', __name__)
def check_post_access(pid, org_id):
    """Verify if a post belongs to the current user's organization with fast indexed lookup."""
    return database.check_post_access(pid, org_id=org_id)

def check_card_access(card_id, org_id):
    """Verify if a Kanban card belongs to the current organization."""
    card = database.kanban_get_card(card_id)
    if not card:
        return False
    column_id = card.get("column_id")
    if not column_id:
        return False
    col = database.kanban_get_column(column_id, org_id=org_id)
    return col is not None

@social_bp.route("/api/link-preview")
@login_required
def get_link_preview():
    url = request.args.get("url")
    if not url:
        return jsonify({"ok": False}), 400
    if not url.startswith("http"):
        url = "http://" + url
    if not _is_safe_url(url):
        return jsonify({"ok": False, "error": "URL ไม่อนุญาต"}), 400

    # YouTube oEmbed fallback
    if "youtube.com" in url or "youtu.be" in url:
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            response = http_requests.get(oembed_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    "ok": True,
                    "title": data.get("title", "")[:100],
                    "description": f"วิดีโอ YouTube โดย {data.get('author_name', '')}"[:200],
                    "image": data.get("thumbnail_url", ""),
                    "url": url
                })
        except Exception as yt_err:
            logger.error(f"[youtube-oembed] {yt_err}")

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = http_requests.get(url, timeout=5, headers=headers, allow_redirects=True, stream=True)
        raw = b""
        for chunk in response.iter_content(chunk_size=8192):
            raw += chunk
            if len(raw) > 512 * 1024:  # หยุดที่ 512 KB
                break
        response.close()
        soup = BeautifulSoup(raw.decode("utf-8", errors="replace"), 'html.parser')
        
        title = soup.find("title").text if soup.find("title") else url
        description = ""
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            description = og_desc["content"]
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc["content"]
                
        image = ""
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image = og_image["content"]
            
        return jsonify({
            "ok": True,
            "title": title[:100],
            "description": description[:200],
            "image": image,
            "url": url
        })
    except Exception as e:
        logger.error(f"[link-preview] {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถดึงข้อมูล URL ได้"}), 500


@social_bp.route("/api/kanban/auto-generate", methods=["POST"])
@login_required
@_limiter.limit("10 per minute; 30 per hour")
def auto_generate_kanban():
    user = session.get("user", "Admin")
    data = request.get_json(force=True)
    goal = data.get("goal")
    if not goal:
        return jsonify({"ok": False, "error": "กรุณากรอกเป้าหมาย"}), 400

    prompt = (
        f"จากเป้าหมายดังนี้: '{goal}' "
        "ช่วยแตกเป็นรายการงานย่อยๆ (Tasks) สำหรับระบบ Kanban "
        "ตอบในรูปแบบ JSON เป็นรายการดั้งนี้ "
        '{"tasks": [{"title": "ชื่อสั้นๆ", "desc": "รายละเอียดงาน", "category": "General|Task|Meeting", "date": "YYYY-MM-DD", "time": "HH:MM"}]} '
        f"กำหนดวันที่เริ่มจากวันนี้ ({get_current_time().split(' ')[0]}) เป็นต้นไป "
        "ข้อสำคัญ: ตอบเฉพาะ JSON เท่านั้น ห้ามมีข้อความอื่นเด็ดขาด"
    )

    try:
        provider = ai_providers.get_provider()
        response_text = provider.chat(prompt, [], "")
        
        # Clean potential markdown backticks
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        
        org_id = get_current_org_id()
        tasks_added = 0
        for t in result.get("tasks", []):
            database.add_schedule(
                user,
                t.get("title"),
                t.get("date"),
                description=t.get("desc", ""),
                category=t.get("category", "Task"),
                start_time=t.get("time", "09:00"),
                status="todo",
                org_id=org_id
            )
            tasks_added += 1
            
        database.log_event(f"AI Auto-generated {tasks_added} tasks for goal: {goal[:50]}", user=user, org_id=org_id)
        return jsonify({"ok": True, "count": tasks_added})
    except Exception as e:
        logger.error(f"[AI Kanban] {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสร้างงานอัตโนมัติได้ กรุณาลองใหม่"}), 500


@social_bp.route("/api/posts", methods=["GET", "POST"])
@login_required
@_limiter.limit("20 per minute; 100 per hour", methods=["POST"])
def manage_posts():
    if request.method == "POST":
        # Handle multipart form data for file uploads
        content = request.form.get("content")
        author = session.get("user", request.form.get("author", "Anonymous"))  # Always use session user
        category = request.form.get("category", "General")
        link = (request.form.get("link") or "").strip()
        if not link and content:
            import re
            url_match = re.search(r'https?://[^\s<>"]+', content)
            if url_match:
                link = url_match.group(0)
        
        has_attachments = 'files' in request.files and any(f.filename for f in request.files.getlist('files'))
        poll_question = request.form.get("poll_question")

        if not content and not link and not has_attachments and not poll_question:
            return jsonify({"ok": False, "error": "กรุณาใส่ข้อความ ลิงก์ โพลล์ หรือแนบไฟล์อย่างใดอย่างหนึ่งค่ะ"}), 400

        if not content:
            content = ""
            
        attachments = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file.filename:
                    is_valid, err_msg = validate_uploaded_file(file, file.filename)
                    if not is_valid:
                        return jsonify({"ok": False, "error": f"ไฟล์ {file.filename} ไม่ปลอดภัย: {err_msg}"}), 400
                    from pathlib import Path
                    orig_suffix = Path(file.filename).suffix.lower()
                    orig_stem = Path(file.filename).stem
                    safe_stem = secure_filename(orig_stem)
                    if not safe_stem:
                        safe_stem = "file"
                    filename = f"{safe_stem}{orig_suffix}"

                    # Add timestamp to avoid collisions
                    ts = int(time.time())
                    unique_filename = f"{ts}_{filename}"
                    save_path = os.path.join("uploads/social_feed", unique_filename)
                    file.save(save_path)
                    attachments.append({
                        "name": filename,
                        "path": f"/uploads/social_feed/{unique_filename}",
                        "type": file.content_type
                    })
            
        # Handle poll data
        poll_question = request.form.get("poll_question")
        poll_options_raw = request.form.get("poll_options")
        
        # Debounce / Idempotency Guard (4-second duplicate post prevention)
        if content:
            recent_posts = database.get_posts(org_id=get_current_org_id())
            if recent_posts:
                for rp in recent_posts[:3]:
                    if rp.get("author") == author and rp.get("content") == content:
                        try:
                            from datetime import datetime as _dt
                            p_ts = rp.get("timestamp") or ""
                            if p_ts:
                                p_dt = _dt.strptime(str(p_ts)[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                                if abs((_dt.now() - p_dt).total_seconds()) < 4:
                                    return jsonify({"ok": True, "id": rp.get("id"), "debounced": True, "message": "โพสต์สำเร็จแล้วค่ะ"})
                        except Exception:
                            pass

        pid = database.add_post(content, author, category, link, attachments, org_id=get_current_org_id())

        if poll_question and poll_options_raw:
            try:
                import json
                poll_options = json.loads(poll_options_raw)
                if isinstance(poll_options, list) and len(poll_options) >= 2:
                    database.add_poll(pid, poll_question, poll_options)
                    database.log_event(f"Poll added to post: ID {pid}", user=author, org_id=get_current_org_id())
            except Exception as e:
                print(f"Error adding poll: {e}")

        database.log_event(f"New post created: ID {pid} by {author}", user=author, org_id=get_current_org_id())
        
        # --- New Post Broadcast ---
        profile = database.get_user_profile(author)
        display_name = profile.get("display_name", author)
        _oid = get_current_org_id()
        
        notification_db.notify_org_members_except(
            _oid,
            author, 
            'post', 
            'โพสต์ใหม่จาก ' + display_name, 
            f'หัวข้อ: {category} - "{content[:30]}..."',
            link='#feed'
        )
        # --- LINE Push for Announcements & Feed Updates to Mapped Groups + Personal LINE ---
        if _oid:
            def run_social_line_push():
                try:
                    from routes.chat import get_channel_access_token
                    _tok = get_channel_access_token()
                    if _tok:
                        import requests as _req
                        _groups = database.get_line_groups_for_org(_oid) or []
                        _base_url = (os.environ.get("BASE_URL") or os.environ.get("PUBLIC_URL") or "https://openchat.sbs").rstrip('/')
                        portal_url = f"{_base_url}/#feed"

                        is_announcement = category and category.lower() in ["announcement", "ประกาศ", "news", "ทั่วไป", "general", "it help"]
                        if is_announcement:
                            primary_color = "#2563EB"
                            badge_bg = "#EFF6FF"
                            header_bg = "#1B2838"
                            header_icon = "📢"
                            header_title = "ประกาศใหม่"
                            header_sub = "NEW ANNOUNCEMENT"
                            alt_prefix = "📢 ประกาศใหม่"
                        else:
                            primary_color = "#7C3AED"
                            badge_bg = "#F5F3FF"
                            header_bg = "#7C3AED"
                            header_icon = "✨"
                            header_title = "โพสต์ใหม่ใน Feed"
                            header_sub = "NEW FEED POST"
                            alt_prefix = "✨ โพสต์ใหม่"

                        # 1) Parse Image Attachments
                        image_urls = []
                        if attachments:
                            for att in attachments:
                                att_path = att.get("path", "")
                                att_type = (att.get("type") or "").lower()
                                att_name = (att.get("name") or "").lower()
                                is_img = (
                                    att_type.startswith("image/") or
                                    att_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"))
                                )
                                if is_img and att_path:
                                    full_img_url = att_path if att_path.startswith("http") else f"{_base_url}{att_path}"
                                    image_urls.append(full_img_url)

                        # 2) Parse Attached Link & Preview Metadata
                        clean_link = None
                        link_domain = None
                        link_title = None
                        link_image = None
                        if link and link.strip():
                            clean_link = link.strip()
                        elif content:
                            import re as _re
                            _m = _re.search(r'https?://[^\s<>"]+', content)
                            if _m:
                                clean_link = _m.group(0)

                        if clean_link:
                            if not clean_link.startswith(("http://", "https://")):
                                clean_link = "https://" + clean_link
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(clean_link)
                                link_domain = (parsed.netloc or "LINK").upper()
                                # Fast fetch link title & illustration image for preview
                                try:
                                    if "youtube.com" in clean_link or "youtu.be" in clean_link:
                                        yt_res = _req.get(f"https://www.youtube.com/oembed?url={clean_link}&format=json", timeout=2.0)
                                        if yt_res.status_code == 200:
                                            yt_data = yt_res.json()
                                            link_title = yt_data.get("title")
                                            link_image = yt_data.get("thumbnail_url")
                                    if not link_title or not link_image:
                                        h_resp = _req.get(clean_link, timeout=1.5, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                                        if h_resp.status_code == 200:
                                            from bs4 import BeautifulSoup
                                            _soup = BeautifulSoup(h_resp.content[:32768], 'html.parser')
                                            if not link_title:
                                                og_t = _soup.find("meta", property="og:title")
                                                if og_t and og_t.get("content"):
                                                    link_title = og_t["content"].strip()
                                                elif _soup.title and _soup.title.string:
                                                    link_title = _soup.title.string.strip()
                                            if not link_image:
                                                og_img = _soup.find("meta", property="og:image") or _soup.find("meta", attrs={"name": "twitter:image"})
                                                if og_img and og_img.get("content"):
                                                    link_image = og_img["content"].strip()
                                except Exception:
                                    pass
                            except Exception:
                                link_domain = "LINK"
                            if not link_title:
                                link_title = clean_link

                        # If post has NO image attachments, but the link HAS a preview image:
                        # Automatically use the link preview image as the illustration image!
                        if not image_urls and link_image:
                            image_urls.append(link_image)

                        # 3) Build Body Contents
                        body_contents = [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": category.upper() if category else ("GENERAL" if is_announcement else "FEED"),
                                        "size": "xxs",
                                        "color": primary_color,
                                        "weight": "bold"
                                    }
                                ],
                                "backgroundColor": badge_bg,
                                "cornerRadius": "20px",
                                "paddingAll": "6px",
                                "paddingStart": "12px",
                                "paddingEnd": "12px",
                                "width": "120px",
                                "justifyContent": "center"
                            },
                            {
                                "type": "text",
                                "text": (content or "ไม่มีเนื้อหา")[:300],
                                "wrap": True,
                                "size": "sm",
                                "color": "#374151",
                                "margin": "lg"
                            }
                        ]

                        # Add Image Box if images exist (NOTE: cornerRadius is on box, NOT on image for LINE Flex compliance)
                        if image_urls:
                            primary_img = image_urls[0]
                            img_box_contents = [
                                {
                                    "type": "image",
                                    "url": primary_img,
                                    "size": "full",
                                    "aspectRatio": "16:9",
                                    "aspectMode": "cover",
                                    "action": {
                                        "type": "uri",
                                        "label": "ดูรูปภาพเต็ม",
                                        "uri": primary_img
                                    }
                                }
                            ]
                            if len(image_urls) > 1:
                                img_box_contents.append({
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": f"📷 แนบทั้งหมด {len(image_urls)} รูป (แตะเพื่อดูรูปภาพ)",
                                            "size": "xxs",
                                            "color": "#6B7280",
                                            "align": "center"
                                        }
                                    ],
                                    "paddingTop": "6px",
                                    "justifyContent": "center"
                                })
                            body_contents.append({
                                "type": "box",
                                "layout": "vertical",
                                "contents": img_box_contents,
                                "cornerRadius": "12px",
                                "margin": "lg"
                            })

                        # Add Link Preview Card Box if link exists
                        if clean_link:
                            body_contents.append({
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {"type": "text", "text": "🔗", "size": "xs", "flex": 0},
                                            {
                                                "type": "text",
                                                "text": link_domain or "LINK",
                                                "size": "xxs",
                                                "weight": "bold",
                                                "color": primary_color,
                                                "margin": "xs",
                                                "flex": 1
                                            }
                                        ],
                                        "alignItems": "center"
                                    },
                                    {
                                        "type": "text",
                                        "text": (link_title or "เปิดดูเนื้อหาตามลิงก์ที่แนบ")[:80],
                                        "size": "xs",
                                        "weight": "bold",
                                        "color": "#1E293B",
                                        "wrap": True,
                                        "maxLines": 2,
                                        "margin": "xs"
                                    }
                                ],
                                "backgroundColor": "#F8FAFC",
                                "cornerRadius": "10px",
                                "paddingAll": "10px",
                                "margin": "lg",
                                "borderWidth": "1px",
                                "borderColor": "#E2E8F0",
                                "action": {
                                    "type": "uri",
                                    "label": "เปิดลิงก์",
                                    "uri": clean_link
                                }
                            })

                        # Separator and Author Info
                        body_contents.append({"type": "separator", "margin": "lg", "color": "#F3F4F6"})
                        body_contents.append({
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {"type": "text", "text": display_name[:1].upper(), "color": "#ffffff", "size": "xs", "align": "center"}
                                    ],
                                    "width": "28px",
                                    "height": "28px",
                                    "backgroundColor": primary_color,
                                    "cornerRadius": "14px",
                                    "justifyContent": "center",
                                    "alignItems": "center"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {"type": "text", "text": display_name, "size": "xs", "color": "#111827", "weight": "bold"},
                                        {"type": "text", "text": "เมื่อสักครู่", "size": "xxs", "color": "#9CA3AF"}
                                    ],
                                    "paddingStart": "10px"
                                }
                            ],
                            "alignItems": "center",
                            "margin": "lg"
                        })

                        # 4) Build Footer Buttons
                        footer_contents = []
                        if clean_link:
                            # Primary button: Open attached link directly in LINE In-App Browser
                            footer_contents.append({
                                "type": "button",
                                "action": {"type": "uri", "label": "🌐 เปิดลิงก์ที่แนบ", "uri": clean_link},
                                "style": "primary",
                                "color": primary_color,
                                "height": "sm"
                            })
                            # Secondary button: View in OrgChat
                            footer_contents.append({
                                "type": "button",
                                "action": {"type": "uri", "label": "💬 ดูในระบบ OrgChat", "uri": portal_url},
                                "style": "secondary",
                                "height": "sm",
                                "margin": "sm"
                            })
                        elif image_urls:
                            # Primary button: View full size image
                            footer_contents.append({
                                "type": "button",
                                "action": {"type": "uri", "label": "🔍 ดูรูปภาพขนาดเต็ม", "uri": image_urls[0]},
                                "style": "primary",
                                "color": primary_color,
                                "height": "sm"
                            })
                            # Secondary button: View in OrgChat
                            footer_contents.append({
                                "type": "button",
                                "action": {"type": "uri", "label": "💬 ดูในระบบ OrgChat", "uri": portal_url},
                                "style": "secondary",
                                "height": "sm",
                                "margin": "sm"
                            })
                        else:
                            # Single button: View post in OrgChat
                            btn_label = "อ่านเพิ่มเติม" if is_announcement else "💬 เข้าดูโพสต์"
                            footer_contents.append({
                                "type": "button",
                                "action": {"type": "uri", "label": btn_label, "uri": portal_url},
                                "style": "primary",
                                "color": primary_color,
                                "height": "sm"
                            })

                        # 5) Alt Text summary
                        extras = []
                        if image_urls:
                            extras.append("รูปภาพ")
                        if clean_link:
                            extras.append("ลิงก์")
                        extra_str = f" [แนบ{'+'.join(extras)}]" if extras else ""
                        alt_text = f"{alt_prefix}: {category} — โดย {display_name}{extra_str}"

                        flex_msg = {
                            "type": "flex",
                            "altText": alt_text,
                            "contents": {
                                "type": "bubble",
                                "size": "mega",
                                "header": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "box",
                                            "layout": "horizontal",
                                            "contents": [
                                                {
                                                    "type": "box",
                                                    "layout": "vertical",
                                                    "contents": [
                                                        {"type": "text", "text": header_icon, "size": "xl", "align": "center"}
                                                    ],
                                                    "width": "40px",
                                                    "height": "40px",
                                                    "backgroundColor": "#ffffff20",
                                                    "cornerRadius": "12px",
                                                    "justifyContent": "center",
                                                    "alignItems": "center"
                                                },
                                                {
                                                    "type": "box",
                                                    "layout": "vertical",
                                                    "contents": [
                                                        {"type": "text", "text": header_title, "color": "#ffffff", "size": "lg", "weight": "bold"},
                                                        {"type": "text", "text": header_sub, "color": "#ffffff90", "size": "xxs"}
                                                    ],
                                                    "paddingStart": "12px"
                                                }
                                            ],
                                            "alignItems": "center"
                                        }
                                    ],
                                    "backgroundColor": header_bg,
                                    "paddingAll": "16px"
                                },
                                "body": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": body_contents,
                                    "paddingAll": "20px",
                                    "backgroundColor": "#ffffff"
                                },
                                "footer": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": footer_contents,
                                    "paddingAll": "12px",
                                    "backgroundColor": "#F9FAFB"
                                },
                                "styles": {
                                    "footer": {"separator": False}
                                }
                            }
                        }
                        
                        # 1) Push to LINE Groups immediately
                        for _g in _groups:
                            _gid = _g.get("group_id")
                            if _gid:
                                try:
                                    _resp = _req.post(
                                        "https://api.line.me/v2/bot/message/push",
                                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                                        json={"to": _gid, "messages": [flex_msg]},
                                        timeout=4
                                    )
                                    if _resp.status_code == 200:
                                        logger.info(f"🚀 [LINE Group Push] Sent successfully to group {_gid}")
                                    else:
                                        logger.error(f"❌ [LINE Group Push Error] Target: {_gid} - Status: {_resp.status_code} - Body: {_resp.text}")
                                except Exception as _ge:
                                    logger.error(f"❌ [LINE Group Push Exception] {_ge}")
                        
                        # 2) Push to individual LINE users in this org (personal DM) using Multicast
                        try:
                            org_members = database.get_org_members(_oid) or []
                            _target_lids = []
                            for member in org_members:
                                _uname = member.get("username", "")
                                if _uname.lower() == author.lower():
                                    continue
                                if not member.get("is_active", True):
                                    continue
                                _lid = database.get_line_id_by_username(_uname)
                                if _lid and _lid not in _target_lids:
                                    _target_lids.append(_lid)

                            if _target_lids:
                                _m_resp = _req.post(
                                    "https://api.line.me/v2/bot/message/multicast",
                                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                                    json={"to": _target_lids, "messages": [flex_msg]},
                                    timeout=4
                                )
                                if _m_resp.status_code == 200:
                                    logger.info(f"🚀 [LINE Multicast Push] Sent to {len(_target_lids)} users")
                                else:
                                    logger.error(f"❌ [LINE Multicast Error] Status: {_m_resp.status_code} - Body: {_m_resp.text}")
                        except Exception as _member_err:
                            logger.warning(f"Failed to push announcement to individual LINE users: {_member_err}")

                except Exception as _e:
                    logger.error(f"Failed to send social post LINE push: {_e}")
            threading.Thread(target=run_social_line_push, daemon=True).start()
        
        # --- @Mentions in post ---
        import re
        mentions = re.findall(r'@(\w+)', content or '')
        mention_targets = [m for m in set(mentions) if m.lower() != author.lower()]
        if mention_targets:
            notification_db.notify_users(
                mention_targets,
                'mention',
                f'{display_name} แท็กคุณในโพสต์',
                f'"{(content or "")[:60]}..."',
                link='#feed'
            )
            # Push to LINE for mentions
            for target in mention_targets:
                threading.Thread(target=send_line_push_notification, args=(target, f'{display_name} แท็กคุณในโพสต์', f'"{(content or "")[:60]}..."')).start()
            batch_send_push_notification(mention_targets, f'{display_name} แท็กคุณในโพสต์', f'"{(content or "")[:40]}..."', url='#feed')
        
        return jsonify({"ok": True, "id": pid})
    
    cat = request.args.get("category", "All")
    posts = database.get_posts(cat, org_id=get_current_org_id())
    return jsonify({"posts": posts})


@social_bp.route("/api/posts/<int:pid>", methods=["PUT", "DELETE"])
@login_required
def update_delete_post(pid):
    user = session.get("user")
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404

    if request.method == "DELETE":
        ok = database.delete_post(pid, username=user, is_admin=is_admin())
        if ok:
            database.log_event(f"Post deleted: ID {pid}", user=user, org_id=org_id)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ลบโพสต์นี้"}), 403
    
    data = request.get_json(force=True)
    content = data.get("content")
    category = data.get("category")
    link = data.get("link")

    # ตรวจ ownership — เฉพาะเจ้าของหรือ admin
    post = database.get_post(pid)
    if not post:
        return jsonify({"ok": False, "error": "ไม่พบโพสต์"}), 404
    if post.get("author") != user and not is_admin():
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์แก้ไขโพสต์นี้"}), 403

    database.update_post(pid, content, category, link)
    database.log_event(f"Post updated: ID {pid}", user=user, org_id=org_id)
    return jsonify({"ok": True})


@social_bp.route("/api/posts/<int:pid>/pin", methods=["POST"])
@admin_required
def pin_post_route(pid):
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404
    database.toggle_pin(pid)
    return jsonify({"ok": True})


@social_bp.route("/api/posts/<int:pid>/comments", methods=["GET", "POST"])
@login_required
def manage_comments(pid):
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404

    if request.method == "POST":
        if "user" not in session:
            return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อนแสดงความคิดเห็น"}), 401
        data = request.get_json(force=True)
        content = data.get("content")
        author = session.get("user")  # Always use session user
        
        if not content:
            return jsonify({"ok": False, "error": "Comment content required"}), 400

        # Debounce / Idempotency Guard (3-second duplicate comment prevention)
        existing_comments = database.get_comments(pid)
        if existing_comments:
            for ec in existing_comments[-3:]:
                if ec.get("author") == author and ec.get("content") == content:
                    try:
                        from datetime import datetime as _dt
                        c_ts = ec.get("timestamp") or ""
                        if c_ts:
                            c_dt = _dt.strptime(str(c_ts)[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                            if abs((_dt.now() - c_dt).total_seconds()) < 3:
                                return jsonify({"ok": True, "id": ec.get("id"), "debounced": True})
                    except Exception:
                        pass
            
        database.add_comment(pid, content, author)
        
        # --- Comment Notification ---
        profile = database.get_user_profile(author)
        display_name = profile.get("display_name", author)
        post = database.get_post_by_id(pid)
        if post and post.get("author") != author:
            notification_db.add_notification(
                post["author"],
                'comment',
                'มีคนแสดงความคิดเห็น',
                f'{display_name} แสดงความคิดเห็นในโพสต์ของคุณ: "{content[:30]}..."',
                link=f'#post-{pid}'
            )
            # Push to LINE
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'มีคนแสดงความคิดเห็น', f'{display_name} แสดงความคิดเห็นในโพสต์: "{content[:30]}..."')).start()
            send_push_notification(post["author"], 'มีคนแสดงความคิดเห็น', f'{display_name} แสดงความคิดเห็นในโพสต์ของคุณ', url='#feed')
        
        # --- @Mentions in comment ---
        import re
        mentions = re.findall(r'@(\w+)', content or '')
        mention_targets = [m for m in set(mentions) if m.lower() != author.lower()]
        if mention_targets:
            notification_db.notify_users(
                mention_targets,
                'mention',
                f'{display_name} แท็กคุณในคอมเมนต์',
                f'"{(content or "")[:60]}..."',
                link=f'#post-{pid}'
            )
            batch_send_push_notification(mention_targets, f'{display_name} แท็กคุณในคอมเมนต์', f'"{(content or "")[:40]}..."', url=f'#feed')
            
            # --- LINE Push for Mentions in Comment ---
            for target in mention_targets:
                threading.Thread(target=send_line_push_notification, args=(target, f'{display_name} แท็กคุณในคอมเมนต์', f'"{(content or "")[:60]}..."')).start()
        
        return jsonify({"ok": True})
    
    return jsonify({"comments": database.get_comments(pid)})


@social_bp.route("/api/posts/<int:pid>/view", methods=["POST"])
@login_required
def record_post_view_route(pid):
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404
    user = session.get("user")
    database.record_post_view(pid, user)
    return jsonify({"ok": True})


@social_bp.route("/api/posts/<int:pid>/views", methods=["GET"])
@login_required
def get_post_views_route(pid):
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404
    views = database.get_post_views(pid)
    return jsonify({"ok": True, "views": views})


@social_bp.route("/api/posts/<int:pid>/comments/<int:cid>", methods=["DELETE"])
@login_required
def delete_comment_route(pid, cid):
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404
    user = session.get("user")
    ok = database.delete_comment(cid, username=user, is_admin=is_admin())
    if ok:
        database.log_event(f"Comment deleted: ID {cid} from post {pid}", user=user, org_id=org_id)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ลบคอมเม้นนี้"}), 403


@social_bp.route("/api/posts/<int:pid>/like", methods=["POST"])
@login_required
def post_like(pid):
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404
    user = session.get("user", "Current User")
    liked = database.toggle_like(pid, user)
    
    # --- Reaction Notification ---
    if liked:
        post = database.get_post_by_id(pid)
        if post and post.get("author") != user:
            notification_db.add_notification(
                post["author"],
                'like',
                'มีคนถูกใจโพสต์ของคุณ',
                f'{user} ถูกใจโพสต์ของคุณ',
                link=f'#post-{pid}'
            )
            send_push_notification(post["author"], 'มีคนถูกใจโพสต์ของคุณ', f'{user} ถูกใจโพสต์ของคุณ', url='#feed')
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'มีคนถูกใจโพสต์ของคุณ', f'{user} ถูกใจโพสต์ของคุณ')).start()
    return jsonify({"ok": True, "liked": liked})


@social_bp.route("/api/posts/<int:pid>/react", methods=["POST"])
@login_required
def post_react(pid):
    """Set/toggle an emoji reaction on a post."""
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404
    user = session.get("user", "Anonymous")
    data = request.get_json(force=True)
    reaction = data.get("reaction", "like")
    
    reacted, reaction_type = database.set_reaction(pid, user, reaction)

    if reacted:
        REACTION_LABELS = {
            'like': '👍 ถูกใจ', 'love': '❤️ รักเลย',
            'haha': '😆 ฮาเลย', 'wow': '😲 ทึ่งเลย',
            'sad': '😢 เศร้า', 'angry': '😡 โกรธ'
        }
        post = database.get_post_by_id(pid)
        if post and post.get("author") != user:
            notification_db.add_notification(
                post["author"],
                'like',
                'มีการแสดงความรู้สึกต่อโพสต์ของคุณ',
                f'{user} ได้ {REACTION_LABELS.get(reaction_type, reaction_type)} ต่อโพสต์ของคุณ',
                link=f'#post-{pid}'
            )
            label = REACTION_LABELS.get(reaction_type, reaction_type)
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'ความเคลื่อนไหวต่อโพสต์', f'{user} ได้ {label} ต่อโพสต์ของคุณ')).start()

    reactions = database.get_post_reactions(pid)
    counts = {}
    for r in reactions:
        rtype = r['reaction']
        counts[rtype] = counts.get(rtype, 0) + 1
    
    return jsonify({
        "ok": True, "reacted": reacted, "reaction": reaction_type,
        "counts": counts, "total": len(reactions)
    })


@social_bp.route("/api/posts/<int:pid>/reactions", methods=["GET"])
@login_required
def get_reactions(pid):
    """Get all reactions for a post with user info."""
    org_id = get_current_org_id()
    if not check_post_access(pid, org_id):
        return jsonify({"ok": False, "error": "ไม่พบโพสต์นี้ในองค์กรของคุณ"}), 404
    user = session.get("user")
    reactions = database.get_post_reactions(pid)
    
    # Find current user's reaction
    my_reaction = None
    for r in reactions:
        if r['user'] == user:
            my_reaction = r['reaction']
            break
    
    # Group by reaction type
    counts = {}
    for r in reactions:
        rtype = r['reaction']
        counts[rtype] = counts.get(rtype, 0) + 1
    
    return jsonify({
        "ok": True, "reactions": reactions, "counts": counts,
        "total": len(reactions), "my_reaction": my_reaction
    })


@social_bp.route("/api/posts/<int:pid>/summarize", methods=["POST"])
@login_required
@_limiter.limit("20 per minute; 60 per hour")
def summarize_post_route(pid):
    post = database.get_post_by_id(pid)
    if not post:
        return jsonify({"ok": False, "error": "Post not found"}), 404
    
    content = post["content"]
    system_prompt = "ช่วยสรุปเนื้อหาสำคัญของโพสต์นี้ให้เป็นข้อความสั้นๆ ประมาณ 1-2 ประโยค ด้วยภาษาไทยที่กระชับและเข้าใจง่ายที่สุดค่ะ"
    
    try:
        provider = ai_providers.get_provider()
        full_summary = ""
        for chunk in provider.chat_stream(content, [], system_prompt):
            if chunk:
                full_summary += chunk
        
        database.update_post_summary(pid, full_summary)
        return jsonify({"ok": True, "summary": full_summary})
    except Exception as e:
        logger.error(f"[Summarization] {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสรุปเนื้อหาได้ กรุณาลองใหม่"}), 500


@social_bp.route("/api/polls/<int:poll_id>/vote", methods=["POST"])
@login_required
def vote_poll_route(poll_id):
    data = request.get_json(force=True)
    option_id = data.get("option_id")
    user = session.get("user")
    
    if option_id is None:
        return jsonify({"ok": False, "error": "Missing option_id"}), 400
        
    ok = database.vote_poll(poll_id, option_id, user)
    if ok:
        database.log_event(f"User {user} voted on poll {poll_id}", user=user, org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "คุณได้ลงคะแนนโหวตแล้ว หรือมีข้อผิดพลาดเกิดขึ้นค่ะ"}), 500


@social_bp.route("/api/polls/<int:poll_id>/user_vote")
@login_required
def get_user_vote_route(poll_id):
    user = session.get("user")
    vote = database.get_user_vote(poll_id, user)
    return jsonify({"option_id": vote})


@social_bp.route("/api/feed/summarize", methods=["POST"])
@login_required
@_limiter.limit("10 per minute; 30 per hour")
def feed_daily_summary():
    user = session.get("user", "Admin")
    data = database.get_daily_activities(org_id=get_current_org_id())
    
    posts = data.get("posts", [])
    schedules = data.get("schedules", [])
    
    if not posts and not schedules:
        return jsonify({"ok": True, "summary": "สวัสดีค่ะพี่ๆ วันนี้ยังไม่มีข่าวสารหรือกิจกรรมใหม่บนฟีดเลยนะคะ น้องพั้นซ์แนะนำให้พี่ๆ ลองอัปโหลดหรือโพสต์แบ่งปันกิจกรรมใหม่ๆ กันได้เลยค่ะ 😊"})
    
    # Prepare prompt
    posts_text = "\n".join([f"- {p['author']} โพสต์ในหมวดหมู่ {p['category']}: {p['content'][:100]}" for p in posts])
    schedules_text = "\n".join([f"- {s['title']} ({s['category']}) วันที่ {s['date']} เวลา {s['time']}" for s in schedules])
    
    prompt = f"""คุณคือผู้ช่วยอัจฉริยะที่คอยสรุป 'Morning Brief' หรือภาพรวมกิจกรรมล่าสุดบน Feed ให้พี่ๆ ในทีมเข้าใจง่ายและเป็นกันเอง
    
    ข้อมูลกิจกรรมในรอบ 24 ชม. ที่ผ่านมา:
    {posts_text}
    
    ตารางงานและกิจกรรมที่กำลังจะเกิดขึ้น:
    {schedules_text}
    
    ช่วยสรุปข้อมูลเหล่านี้ให้น่าอ่านและกระชับในสไตล์น้องพั้นซ์ (ไม่เกิน 4-5 ประโยค) เพื่อให้พี่ๆ ในทีมเตรียมตัวทำงานในวันนี้อย่างมีความสุขและราบรื่นนะคะ
    """
    
    try:
        provider = ai_providers.get_provider()
        full_summary = ""
        system_prompt = "คุณคือ 'น้องพั้นซ์' AI Assistant สาวออฟฟิศผู้น่ารัก สดใส สุภาพ และเป็นกันเอง คอยช่วยเหลือพี่ๆ ในทีมเสมอ ตอบเป็นภาษาไทยค่ะ"
        
        for chunk in provider.chat_stream(prompt, [], system_prompt):
            if chunk:
                full_summary += chunk
        
        return jsonify({"ok": True, "summary": full_summary})
    except Exception as e:
        logger.error(f"[Daily Summary] {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสรุปข้อมูลวันนี้ได้ กรุณาลองใหม่"}), 500


@social_bp.route("/api/wiki", methods=["GET"])
@login_required
def list_wiki_pages():
    org_id = get_current_org_id()
    pages = database.get_wiki_pages(org_id=org_id)
    return jsonify({"pages": pages})


@social_bp.route("/api/wiki", methods=["POST"])
@login_required
def create_wiki_page_route():
    data = request.json or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    category_id = data.get("category_id")
    
    if not title or not content:
        return jsonify({"ok": False, "error": "Title and content required"}), 400
        
    user = session.get("user")
    org_id = get_current_org_id()
    page_id, slug = database.create_wiki_page(title, content, user, category_id, org_id=org_id)

    # Ingest into RAG engine
    rag_engine.ingest_text(content, source_name=f"Wiki: {title}", category_id=category_id, org_id=org_id)

    database.log_event(f"Created Wiki page: {title}", user=user, org_id=org_id)
    return jsonify({"ok": True, "slug": slug})


@social_bp.route("/api/wiki/<slug>", methods=["GET"])
@login_required
def get_wiki_page_route(slug):
    org_id = get_current_org_id()
    page = database.get_wiki_page(slug, org_id=org_id)
    if not page:
        return jsonify({"ok": False, "error": "Page not found"}), 404
    return jsonify({"ok": True, "page": page})


@social_bp.route("/api/wiki/<slug>", methods=["PUT"])
@login_required
def update_wiki_page_route(slug):
    data = request.json or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    category_id = data.get("category_id")
    
    if not title or not content:
        return jsonify({"ok": False, "error": "Title and content required"}), 400
        
    org_id = get_current_org_id()
    if database.update_wiki_page(slug, title, content, category_id, org_id=org_id):
        # Update RAG engine
        rag_engine.ingest_text(content, source_name=f"Wiki: {title}", category_id=category_id, org_id=org_id)
        
        database.log_event(f"Updated Wiki page: {title}", user=session.get("user"), org_id=org_id)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Update failed"}), 404


@social_bp.route("/api/wiki/<slug>", methods=["DELETE"])
@login_required
def delete_wiki_page_route(slug):
    org_id = get_current_org_id()
    page = database.get_wiki_page(slug, org_id=org_id)
    if not page:
        return jsonify({"ok": False}), 404
        
    if database.delete_wiki_page(slug, org_id=org_id):
        # Remove from RAG
        rag_engine._kb.delete_by_source(f"Wiki: {page['title']}")
        database.log_event(f"Deleted Wiki page: {slug}", user=session.get("user"), org_id=org_id)
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500


@social_bp.route("/api/kanban/board", methods=["GET"])
@login_required
def kanban_get_board():
    org_id = get_current_org_id()
    return jsonify({"ok": True, "columns": database.kanban_get_board(org_id)})


@social_bp.route("/api/kanban/columns", methods=["POST"])
@login_required
def kanban_add_column():
    org_id = get_current_org_id()
    data = request.json or {}
    title = data.get("title", "").strip()
    color = data.get("color", "#6366f1")
    if not title:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อคอลัมน์"}), 400
    col_id = database.kanban_add_column(title, color, created_by=session.get("user", "System"), org_id=org_id)
    return jsonify({"ok": True, "id": col_id})


@social_bp.route("/api/kanban/columns/<int:col_id>", methods=["PUT"])
@login_required
def kanban_update_column(col_id):
    org_id = get_current_org_id()
    user = session.get("user")
    col = database.kanban_get_column(col_id, org_id=org_id)
    if not col:
        return jsonify({"ok": False, "error": "ไม่พบ column"}), 404
    if col.get("created_by") != user and not is_admin():
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์แก้ไข column นี้"}), 403
    data = request.json or {}
    database.kanban_update_column(col_id, title=data.get("title"), color=data.get("color"))
    return jsonify({"ok": True})


@social_bp.route("/api/kanban/columns/<int:col_id>", methods=["DELETE"])
@login_required
def kanban_delete_column(col_id):
    org_id = get_current_org_id()
    user = session.get("user")
    col = database.kanban_get_column(col_id, org_id=org_id)
    if not col:
        return jsonify({"ok": False, "error": "ไม่พบ column"}), 404
    if col.get("created_by") != user and not is_admin():
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์ลบ column นี้"}), 403
    ok = database.kanban_delete_column(col_id)
    return jsonify({"ok": ok})


@social_bp.route("/api/kanban/columns/reorder", methods=["POST"])
@login_required
def kanban_reorder_columns():
    org_id = get_current_org_id()
    data = request.json or {}
    order = data.get("order", [])
    database.kanban_reorder_columns(order, org_id=org_id)
    return jsonify({"ok": True})


@social_bp.route("/api/kanban/cards", methods=["POST"])
@login_required
@_limiter.limit("30 per minute")
def kanban_add_card():
    org_id = get_current_org_id()
    data = request.json or {}
    column_id = data.get("column_id")
    title = data.get("title", "").strip()
    if not column_id or not title:
        return jsonify({"ok": False, "error": "Missing column_id or title"}), 400
    # ตรวจว่า column นั้นเป็นของ org นี้
    if not database.kanban_get_column(int(column_id), org_id=org_id):
        return jsonify({"ok": False, "error": "ไม่พบ column หรือไม่มีสิทธิ์"}), 403
    
    current_user = session.get("user", "System")
    assignees_raw = data.get("assignee", "")
    if assignees_raw and isinstance(assignees_raw, str):
        assignee_list = [a.strip() for a in assignees_raw.split(',') if a.strip()]
    else:
        assignee_list = []
        
    card_id = database.kanban_add_card(
        column_id=int(column_id),
        title=title,
        description=data.get("description", ""),
        priority=data.get("priority", "medium"),
        assignee=",".join(assignee_list) if assignee_list else "",
        due_date=data.get("due_date", ""),
        labels=data.get("labels", ""),
        color=data.get("color", ""),
        created_by=current_user,
        is_done=int(data.get("is_done", 0))
    )
    
    if assignee_list:
        for a in assignee_list:
            if a != current_user:
                try:
                    notification_db.add_notification(
                        a,
                        "kanban",
                        "มอบหมายงานใหม่ / Kanban",
                        f"{current_user} ได้มอบหมายงาน '{title}' ให้กับคุณ",
                        link="#view=kanban"
                    )
                    batch_send_push_notification([a], "มอบหมายงานใหม่ / Kanban", f"{current_user}: {title}", url="#view=kanban")
                    # --- Send to LINE ---
                    threading.Thread(target=send_line_push_notification, args=(
                        a, 
                        "งานใหม่ (Kanban)", 
                        f"{current_user} ได้มอบหมายงาน '{title}' ให้กับคุณ"
                    ), kwargs={
                        "fields": {
                            "งาน": title,
                            "ผู้มอบหมาย": current_user,
                            "สถานะ": "รอดำเนินการ (To Do)"
                        }
                    }).start()
                except Exception as e:
                    print(f"Error sending kanban notification to {a}: {e}")
            
    return jsonify({"ok": True, "id": card_id})


@social_bp.route("/api/kanban/cards/<int:card_id>", methods=["PUT"])
@login_required
def kanban_update_card(card_id):
    org_id = get_current_org_id()
    if not check_card_access(card_id, org_id):
        return jsonify({"ok": False, "error": "ไม่พบการ์ดนี้ในองค์กรของคุณ"}), 404
        
    data = request.json or {}
    old_card = database.kanban_get_card(card_id)
    if not old_card:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404
        
    database.kanban_update_card(card_id, **data)
    
    current_user = session.get("user", "System")
    assignees_raw = data.get("assignee", "")
    if isinstance(assignees_raw, str):
        new_assignee_list = [a.strip() for a in assignees_raw.split(',') if a.strip()]
    else:
        new_assignee_list = []
        
    old_assignee_list = (old_card.get("assignee") or "").split(',')
    old_assignee_list = [a.strip() for a in old_assignee_list if a.strip()]
    
    # Notify ONLY newly added assignees
    added_assignees = [a for a in new_assignee_list if a not in old_assignee_list and a != current_user]
    
    for a in added_assignees:
        try:
            notification_db.add_notification(
                a,
                "kanban",
                "มอบหมายงาน / Kanban",
                f"{current_user} ได้มอบหมายงาน '{data.get('title', old_card['title'])}' ให้กับคุณ",
                link="#view=kanban"
            )
            batch_send_push_notification([a], "มอบหมายงาน / Kanban", f"{current_user}: {data.get('title', old_card['title'])}", url="#view=kanban")
            # --- Send to LINE ---
            threading.Thread(target=send_line_push_notification, args=(
                a, 
                "อัปเดตงาน (Kanban)", 
                f"{current_user} ได้เพิ่มคุณในงาน '{data.get('title', old_card['title'])}'"
            ), kwargs={
                "fields": {
                    "งาน": data.get('title', old_card['title']),
                    "แจ้งเตือน": f"{current_user} มอบหมายงานให้คุณ",
                    "ดูที่หน้าเว็บ": "เมนู Kanban"
                }
            }).start()
        except Exception as e:
            print(f"Error sending kanban update notification to {a}: {e}")
            
    return jsonify({"ok": True})


@social_bp.route("/api/kanban/cards/<int:card_id>", methods=["DELETE"])
@login_required
def kanban_delete_card(card_id):
    org_id = get_current_org_id()
    if not check_card_access(card_id, org_id):
        return jsonify({"ok": False, "error": "ไม่พบการ์ดนี้ในองค์กรของคุณ"}), 404

    user = session.get("user")
    card = database.kanban_get_card(card_id)
    if not card:
        return jsonify({"ok": False, "error": "ไม่พบ card"}), 404
    if card.get("created_by") != user and not is_admin():
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์ลบ card นี้"}), 403
    ok = database.kanban_delete_card(card_id)
    return jsonify({"ok": ok})


@social_bp.route("/api/kanban/cards/<int:card_id>/move", methods=["POST"])
@login_required
def kanban_move_card(card_id):
    org_id = get_current_org_id()
    if not check_card_access(card_id, org_id):
        return jsonify({"ok": False, "error": "ไม่พบการ์ดนี้ในองค์กรของคุณ"}), 404

    data = request.json or {}
    new_column_id = data.get("column_id")
    new_position = data.get("position", 0)
    if new_column_id is None:
        return jsonify({"ok": False, "error": "Missing column_id"}), 400
    ok = database.kanban_move_card(card_id, int(new_column_id), int(new_position))
    
    # Also update 'is_done' if passed (for automatic status on move to Done column)
    is_done = data.get("is_done")
    if is_done is not None:
        database.kanban_update_card(card_id, is_done=int(is_done))
        
    # Broadcast board update via socketio
    socketio.emit("kanban_update", {}, room="kanban_board")
    return jsonify({"ok": ok})


@social_bp.route("/api/wiki/pages", methods=["GET"])
@login_required
def wiki_list_pages():
    q = request.args.get("q", "").strip()
    org_id = get_current_org_id()
    if q:
        pages = database.wiki_search(q, org_id=org_id)
    else:
        pages = database.wiki_get_all_pages(org_id=org_id)
    return jsonify({"ok": True, "pages": pages})


@social_bp.route("/api/wiki/pages", methods=["POST"])
@login_required
def wiki_create_page():
    data = request.json or {}
    title = data.get("title", "").strip()
    content = data.get("content", "")
    if not title:
        return jsonify({"ok": False, "error": "กรุณาระบุหัวข้อบทความ"}), 400
    org_id = get_current_org_id()
    page_id, slug = database.wiki_create_page(
        title=title,
        content=content,
        author=session.get("user", "Anonymous"),
        category_id=data.get("category_id"),
        org_id=org_id
    )
    return jsonify({"ok": True, "id": page_id, "slug": slug})


@social_bp.route("/api/wiki/pages/<int:page_id>", methods=["GET"])
@login_required
def wiki_get_page(page_id):
    org_id = get_current_org_id()
    page = database.wiki_get_page(page_id=page_id, org_id=org_id)
    if not page:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404
    return jsonify({"ok": True, "page": page})


@social_bp.route("/api/wiki/pages/<int:page_id>", methods=["PUT"])
@login_required
def wiki_update_page(page_id):
    data = request.json or {}
    org_id = get_current_org_id()
    database.wiki_update_page(page_id, title=data.get("title"), content=data.get("content"), category_id=data.get("category_id"), org_id=org_id)
    return jsonify({"ok": True})


@social_bp.route("/api/wiki/pages/<int:page_id>", methods=["DELETE"])
@login_required
def wiki_delete_page(page_id):
    org_id = get_current_org_id()
    ok = database.wiki_delete_page(page_id, org_id=org_id)
    return jsonify({"ok": ok})


@social_bp.route("/api/wiki/pages/<int:page_id>/export", methods=["GET"])
@login_required
def export_wiki_page(page_id):
    export_format = request.args.get("format", "txt").lower()
    org_id = get_current_org_id()
    page = database.wiki_get_page(page_id=page_id, org_id=org_id)
    if not page:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404

    title = page.get("title", "wiki_export")
    content = page.get("content", "")
    author = page.get("author", "Unknown")
    updated_at = page.get("updated_at", "")

    import tempfile
    ext = "md" if export_format == "md" else "txt"
    download_name = f"{title}_{page_id}.{ext}"
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, download_name)
    
    export_text = f"# {title}\nAuthor: {author}\nUpdated: {updated_at}\n\n{content}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(export_text)

    return send_file(file_path, as_attachment=True, download_name=download_name)

