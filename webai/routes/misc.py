# -*- coding: utf-8 -*-
"""
Misc Blueprint — Health Check, Version, Manifest, Service Worker, Uploads,
Pages (index, dashboard, pricing, privacy, terms), Notifications, Debug Routes
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, send_from_directory, send_file, abort, redirect, session, current_app
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
import logging

import database
import rag_engine
import notification_db
import billing

from routes.shared import (
    VERSION, socketio, _limiter, login_required, admin_required,
    send_push_notification, batch_send_push_notification,
    get_weather_context, THAI_HOLIDAYS_2026, get_current_time,
    VAPID_PUBLIC_KEY,
    get_current_org_id, _get_gemini_api_key,
)

logger = logging.getLogger("OrgChatAI.Misc")

misc_bp = Blueprint('misc', __name__)

@misc_bp.route("/api/debug/routes")
@login_required
@admin_required
def list_routes():
    import urllib.parse
    output = []
    for rule in current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:25} {methods:20} {rule}")
        output.append(line)
    return "<pre>" + "\n".join(sorted(output)) + "</pre>"


@misc_bp.route("/api/version")
def get_version():
    return jsonify({"version": VERSION, "status": "online"})


@misc_bp.route('/uploads/social_feed/<path:filename>')
def serve_social_uploads(filename):
    return send_from_directory('uploads/social_feed', filename)


@misc_bp.route('/uploads/profiles/<path:filename>')
def serve_profile_uploads(filename):
    return send_from_directory('uploads/profiles', filename)


@misc_bp.route('/uploads/group_chat/<path:filename>')
@login_required
def serve_group_chat_uploads(filename):
    return send_from_directory('uploads/group_chat', filename)


@misc_bp.route('/uploads/dm_chat/<path:filename>')
@login_required
def serve_dm_chat_uploads(filename):
    return send_from_directory('uploads/dm_chat', filename)


@misc_bp.route('/uploads/group_profiles/<path:filename>')
def serve_group_profile_uploads(filename):
    return send_from_directory('uploads/group_profiles', filename)


@misc_bp.route("/")
def index():
    from flask import make_response
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    user = session.get("user")
    is_admin = False
    is_superadmin = False
    is_org_admin = False
    if user:
        settings = database.get_user_setting(user)
        is_admin = settings.get("role") == "admin"
        sa_users_str = os.environ.get("SUPERADMIN_USERS", "Admin")
        sa_users = [u.strip().lower() for u in sa_users_str.split(",") if u.strip()]
        is_superadmin = user.lower() in sa_users
        # Check org_role from session first, fallback to DB check
        is_org_admin = session.get("org_role") == "admin"
        if not is_org_admin:
            org_id_check = session.get("org_id") or get_current_org_id()
            if org_id_check:
                try:
                    is_org_admin = database.is_org_admin(org_id_check, user)
                    # Sync session if DB says admin but session didn't know
                    if is_org_admin and session.get("org_role") != "admin":
                        session["org_role"] = "admin"
                except Exception:
                    pass
    line_bot_id = os.environ.get("LINE_BOT_BASIC_ID", "").strip()
    
    org_id = get_current_org_id()
    biz_profile = database.get_org_profile(org_id) if org_id else None
    org_info = database.get_org(org_id) if org_id else None

    org_plan = billing.get_effective_plan(org_id) if org_id else "free"
    resp = make_response(render_template("index.html", google_client_id=google_client_id,
                           vapid_public_key=VAPID_PUBLIC_KEY, is_admin=is_admin, is_superadmin=is_superadmin,
                           is_org_admin=is_org_admin, line_bot_id=line_bot_id, biz_profile=biz_profile,
                           org_info=org_info, org_plan=org_plan))
    # Prevent browser caching so sidebar renders correctly after login
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@misc_bp.route("/dashboard")
@login_required
def tax_expense_dashboard():
    org_id = get_current_org_id()
    if not billing.has_feature(org_id, "financial_dashboard"):
        return redirect("/pricing?upgrade=financial_dashboard")
    biz_profile = database.get_org_profile(org_id) if org_id else None
    org_info = database.get_org(org_id) if org_id else None
    return render_template("tax_expense_dashboard.html", biz_profile=biz_profile, org_info=org_info)


@misc_bp.route("/pricing")
def pricing_page():
    if session.get("user"):
        return redirect("/?view=plan")
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    is_test_mode = stripe_key.startswith("sk_test_")
    return render_template("pricing.html", plans=billing.PLANS, plan_hierarchy=billing.PLAN_HIERARCHY, is_test_mode=is_test_mode)


@misc_bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")


@misc_bp.route("/terms")
def terms_page():
    return render_template("terms.html")


@misc_bp.route("/api/status")
@login_required
def status():
    provider = os.environ.get("AI_PROVIDER", "groq").lower()
    has_key = False
    if provider == "gemini":
        from routes.shared import _get_gemini_api_key
        has_key = bool(_get_gemini_api_key())
    elif provider == "groq":
        has_key = bool(os.environ.get("GROQ_API_KEY"))
    elif provider == "ollama":
        has_key = True # Local
        
    stats = rag_engine.kb_stats()
    quota_info = rag_engine.get_quota_status()
    
    user_settings = database.get_user_setting(session.get("user"))
    
    user = session.get("user")
    sa_users_str = os.environ.get("SUPERADMIN_USERS", "Admin")
    sa_users = [u.strip().lower() for u in sa_users_str.split(",") if u.strip()]
    is_superadmin = (user.lower() in sa_users) if user else False
    
    org_id = session.get("org_id")
    org_role = session.get("org_role")

    response = jsonify({
        "api_key_set": has_key,
        "quota_info": quota_info,
        "provider": provider,
        "is_admin": user_settings.get("role") == "admin",
        "is_superadmin": is_superadmin,
        "can_view_kb": bool(user_settings.get("can_view_kb")),
        "can_edit_kb": bool(user_settings.get("can_edit_kb")),
        "can_delete_kb": bool(user_settings.get("can_delete_kb")),
        "user": session.get("user"),
        "app_settings": database.get_all_app_settings(),
        "server_time": get_current_time(),
        "org_id": org_id,
        "org_role": org_role,
        "has_org": org_id is not None,
        "org_plan": billing.get_effective_plan(org_id) if org_id else None,
        "org_features": billing.get_plan_config(billing.get_effective_plan(org_id)).get("features", {}) if org_id else {},
        **stats
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@misc_bp.route("/api/ping")
def ping():
    return jsonify({"ok": True, "version": VERSION})


@misc_bp.route("/api/feedback", methods=["POST"])
@login_required
@_limiter.limit("10 per minute; 30 per hour")
def feedback():
    user = session.get("user")
    data = request.get_json(force=True)
    val = data.get("value", 0)
    database.save_feedback(user, val)
    return jsonify({"ok": True})


@misc_bp.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications_route():
    user = session.get("user")
    notifs = notification_db.get_notifications(user)
    unread_count = sum(1 for n in notifs if not n.get('is_read'))
    return jsonify({"notifications": notifs, "unread_count": unread_count})


@misc_bp.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_notif_read_route(notif_id):
    user = session.get("user")
    notification_db.mark_notification_read(notif_id, user)
    return jsonify({"ok": True})


@misc_bp.route("/api/notifications/read_all", methods=["POST"])
@login_required
def mark_all_read_route():
    user = session.get("user")
    notification_db.mark_all_notifications_read(user)
    return jsonify({"ok": True})


@misc_bp.route("/api/notifications/<int:notif_id>", methods=["DELETE"])
@login_required
def delete_notif_route(notif_id):
    user = session.get("user")
    notification_db.delete_notification(notif_id, user)
    return jsonify({"ok": True})


@misc_bp.route("/api/notifications/delete_all", methods=["DELETE"])
@login_required
def delete_all_notifs_route():
    user = session.get("user")
    notification_db.delete_all_notifications(user)
    return jsonify({"ok": True})


@misc_bp.route("/manifest.json")
def serve_manifest():
    return send_from_directory("static", "manifest.json")


@misc_bp.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


@misc_bp.route("/health")
def health_check():
    """Used by uptime monitors (UptimeRobot, etc.) — returns 200 if server is alive."""
    import sqlite3 as _sq
    db_ok = False
    try:
        _c = _sq.connect(os.environ.get("DB_PATH", "chat_history.db"), timeout=2)
        _c.execute("SELECT 1")
        _c.close()
        db_ok = True
    except Exception:
        pass
    status = "ok" if db_ok else "degraded"
    return jsonify({
        "status": status,
        "db": db_ok,
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
    }), 200 if db_ok else 503

