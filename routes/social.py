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
)

logger = logging.getLogger("OrgChatAI.Social")

social_bp = Blueprint('social', __name__)

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
        link = request.form.get("link")
        
        if not content:
            return jsonify({"ok": False, "error": "Content required"}), 400
            
        attachments = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file.filename:
                    is_valid, err_msg = validate_uploaded_file(file, file.filename)
                    if not is_valid:
                        return jsonify({"ok": False, "error": f"ไฟล์ {file.filename} ไม่ปลอดภัย: {err_msg}"}), 400
                    filename = secure_filename(file.filename)

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
        
        notification_db.notify_all_except(
            author, 
            'post', 
            'โพสต์ใหม่จาก ' + display_name, 
            f'หัวข้อ: {category} - "{content[:30]}..."',
            link='#feed'
        )
        # --- LINE Broadcast for Announcements & General Updates ---
        if category and category.lower() in ["announcement", "ประกาศ", "news", "ทั่วไป", "general", "it help"]:
            threading.Thread(target=broadcast_line_announcement, args=(
                "อัปเดตข่าวสารสำคัญ", 
                f"📢 มีประกาศใหม่ล่าสุด!\nหัวข้อ: {category}\nเนื้อหา: {content[:100]}...\nโดย: {display_name}"
            )).start()
        else:
            # Fallback broadcast for any other category
            threading.Thread(target=broadcast_line_announcement, args=(
                "โพสต์ใหม่ใน Feed", 
                f"✨ มีรายการใหม่น่าสนใจใน Feed!\nหมวดหมู่: {category}\nผู้โพสต์: {display_name}\nลองเข้าไปอ่านและแสดงความคิดเห็นได้ที่แอปนะครับ"
            )).start()
        
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
    if request.method == "DELETE":
        ok = database.delete_post(pid, username=user, is_admin=is_admin())
        if ok:
            database.log_event(f"Post deleted: ID {pid}", user=user, org_id=get_current_org_id())
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
    database.log_event(f"Post updated: ID {pid}", user=user, org_id=get_current_org_id())
    return jsonify({"ok": True})


@social_bp.route("/api/posts/<int:pid>/pin", methods=["POST"])
@admin_required
def pin_post_route(pid):
    database.toggle_pin(pid)
    return jsonify({"ok": True})


@social_bp.route("/api/posts/<int:pid>/comments", methods=["GET", "POST"])
def manage_comments(pid):
    if request.method == "POST":
        if "user" not in session:
            return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อนแสดงความคิดเห็น"}), 401
        data = request.get_json(force=True)
        content = data.get("content")
        author = session.get("user")  # Always use session user
        
        if not content:
            return jsonify({"ok": False, "error": "Comment content required"}), 400
            
        database.add_comment(pid, content, author)
        
        # --- Comment Notification ---
        profile = database.get_user_profile(author)
        display_name = profile.get("display_name", author)
        posts = database.get_posts(org_id=get_current_org_id())
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != author:
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
    user = session.get("user")
    database.record_post_view(pid, user)
    return jsonify({"ok": True})


@social_bp.route("/api/posts/<int:pid>/views", methods=["GET"])
@login_required
def get_post_views_route(pid):
    views = database.get_post_views(pid)
    return jsonify({"ok": True, "views": views})


@social_bp.route("/api/posts/<int:pid>/comments/<int:cid>", methods=["DELETE"])
@login_required
def delete_comment_route(pid, cid):
    user = session.get("user")
    ok = database.delete_comment(cid, username=user, is_admin=is_admin())
    if ok:
        database.log_event(f"Comment deleted: ID {cid} from post {pid}", user=user, org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ลบคอมเม้นนี้"}), 403


@social_bp.route("/api/posts/<int:pid>/like", methods=["POST"])
@login_required
def post_like(pid):
    user = session.get("user", "Current User")
    liked = database.toggle_like(pid, user)
    
    # --- Reaction Notification ---
    if liked:
        posts = database.get_posts(org_id=get_current_org_id())
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != user:
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
        posts = database.get_posts(org_id=get_current_org_id())
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != user:
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
def summarize_post_route(pid):
    posts = database.get_posts(org_id=get_current_org_id())
    post = next((p for p in posts if p["id"] == pid), None)
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
    return jsonify({"ok": True, "columns": database.kanban_get_board()})


@social_bp.route("/api/kanban/columns", methods=["POST"])
@login_required
def kanban_add_column():
    data = request.json or {}
    title = data.get("title", "").strip()
    color = data.get("color", "#6366f1")
    if not title:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อคอลัมน์"}), 400
    col_id = database.kanban_add_column(title, color, created_by=session.get("user", "System"))
    return jsonify({"ok": True, "id": col_id})


@social_bp.route("/api/kanban/columns/<int:col_id>", methods=["PUT"])
@login_required
def kanban_update_column(col_id):
    # ตรวจสอบ ownership — เฉพาะผู้สร้างหรือ admin ของ org เท่านั้น
    user = session.get("user")
    col = database.kanban_get_column(col_id)
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
    user = session.get("user")
    col = database.kanban_get_column(col_id)
    if not col:
        return jsonify({"ok": False, "error": "ไม่พบ column"}), 404
    if col.get("created_by") != user and not is_admin():
        return jsonify({"ok": False, "error": "ไม่มีสิทธิ์ลบ column นี้"}), 403
    ok = database.kanban_delete_column(col_id)
    return jsonify({"ok": ok})


@social_bp.route("/api/kanban/columns/reorder", methods=["POST"])
@login_required
def kanban_reorder_columns():
    data = request.json or {}
    order = data.get("order", [])
    database.kanban_reorder_columns(order)
    return jsonify({"ok": True})


@social_bp.route("/api/kanban/cards", methods=["POST"])
@login_required
@_limiter.limit("30 per minute")
def kanban_add_card():
    data = request.json or {}
    column_id = data.get("column_id")
    title = data.get("title", "").strip()
    if not column_id or not title:
        return jsonify({"ok": False, "error": "Missing column_id or title"}), 400
    
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

    import wiki_manager
    file_path, download_name, error = wiki_manager.export_page_to_file(
        page_id=page_id,
        title=title,
        content=content,
        author=author,
        updated_at=updated_at,
        export_format=export_format
    )

    if error:
        return jsonify({"ok": False, "error": error}), 400

    return send_file(file_path, as_attachment=True, download_name=download_name)

