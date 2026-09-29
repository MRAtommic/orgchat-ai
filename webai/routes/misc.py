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
    get_current_org_id, _get_gemini_api_key, is_superadmin_user,
    get_or_create_csrf_token,
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


def _safe_filename(filename: str) -> bool:
    """Block path traversal: reject filenames containing '..' or absolute path components."""
    if not filename:
        return False
    # Normalize path separators and check for traversal
    normalized = filename.replace('\\', '/')
    if '..' in normalized or normalized.startswith('/') or ':' in normalized:
        return False
    return True


@misc_bp.route('/uploads/social_feed/<path:filename>')
def serve_social_uploads(filename):
    if not _safe_filename(filename):
        abort(403)
    return send_from_directory('uploads/social_feed', filename)


@misc_bp.route('/uploads/receipts_backup/<path:filename>')
def serve_receipts_backup(filename):
    if not _safe_filename(filename):
        abort(403)
    return send_from_directory('uploads/receipts_backup', filename)


@misc_bp.route('/uploads/profiles/<path:filename>')
@login_required
def serve_profile_uploads(filename):
    if not _safe_filename(filename):
        abort(403)
    return send_from_directory('uploads/profiles', filename)


@misc_bp.route('/uploads/group_chat/<path:filename>')
@login_required
def serve_group_chat_uploads(filename):
    if not _safe_filename(filename):
        abort(403)
    return send_from_directory('uploads/group_chat', filename)


@misc_bp.route('/uploads/dm_chat/<path:filename>')
@login_required
def serve_dm_chat_uploads(filename):
    if not _safe_filename(filename):
        abort(403)
    return send_from_directory('uploads/dm_chat', filename)


@misc_bp.route('/uploads/group_profiles/<path:filename>')
@login_required
def serve_group_profile_uploads(filename):
    if not _safe_filename(filename):
        abort(403)
    return send_from_directory('uploads/group_profiles', filename)


@misc_bp.route("/")
@misc_bp.route("/login")
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
        is_superadmin = is_superadmin_user(user)
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
    csrf_token = get_or_create_csrf_token()
    resp = make_response(render_template("index.html", google_client_id=google_client_id,
                           vapid_public_key=VAPID_PUBLIC_KEY, is_admin=is_admin, is_superadmin=is_superadmin,
                           is_org_admin=is_org_admin, line_bot_id=line_bot_id, biz_profile=biz_profile,
                           org_info=org_info, org_plan=org_plan, csrf_token=csrf_token))
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
    is_superadmin = is_superadmin_user(user) if user else False
    
    org_id = get_current_org_id()
    org_role = session.get("org_role")
    if user and org_id:
        try:
            if database.is_org_admin(org_id, user):
                org_role = "admin"
                session["org_role"] = "admin"
            elif database.is_org_member(org_id, user):
                org_role = "member"
                session["org_role"] = "member"
            else:
                org_role = None
                session["org_role"] = None
        except Exception:
            pass

    response = jsonify({
        "api_key_set": has_key,
        "quota_info": quota_info,
        "provider": provider,
        "is_admin": user_settings.get("role") == "admin",
        "is_superadmin": is_superadmin,
        "can_view_kb": bool(user_settings.get("can_view_kb")),
        "can_edit_kb": bool(user_settings.get("can_edit_kb")),
        "can_delete_kb": bool(user_settings.get("can_delete_kb")),
        "can_view_financial": bool(user_settings.get("can_view_financial")),
        "can_manage_leave": bool(user_settings.get("can_manage_leave")),
        "can_broadcast_line": bool(user_settings.get("can_broadcast_line")),
        "can_manage_peak": bool(user_settings.get("can_manage_peak")),
        "can_use_ai": bool(user_settings.get("can_use_ai", True)),
        "can_claim_expense": bool(user_settings.get("can_claim_expense", True)),
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


@misc_bp.route('/favicon.ico')
def serve_favicon():
    """Serve favicon.ico to prevent 404 console errors."""
    static_dir = os.path.join(current_app.root_path, 'static')
    if os.path.exists(os.path.join(static_dir, 'favicon.ico')):
        return send_from_directory('static', 'favicon.ico')
    # Fallback to app icon if exists
    for icon_name in ['icon-192.png', 'icon.png', 'logo.png']:
        if os.path.exists(os.path.join(static_dir, icon_name)):
            return send_from_directory('static', icon_name, mimetype='image/png')
    return ('', 204)


# ═══════════════════════════════════════════════════════════════
# 🛡️ Security, Audit & FIM Routes (Chapter 1, 3, 4)
# ═══════════════════════════════════════════════════════════════

@misc_bp.route("/api/security/audit-logs")
@login_required
def get_security_audit_logs():
    org_id = get_current_org_id() or 1
    logs = database.get_audit_logs(org_id=org_id, limit=60)
    return jsonify({"ok": True, "logs": logs})


@misc_bp.route("/api/security/health-status")
@login_required
def get_security_health():
    """Retrieve system security health score and defensive telemetry."""
    org_id = get_current_org_id() or 1
    health_data = database.get_security_health_status(org_id=org_id)
    return jsonify({"ok": True, "health": health_data})


@misc_bp.route("/api/security/export-report")
@login_required
def export_security_report():
    """Generate and send downloadable Security Audit & Compliance PDF Report."""
    from flask import send_file
    from pathlib import Path
    import export_service

    org_id = get_current_org_id() or 1
    user_orgs = database.get_user_orgs(session.get("user", "Admin"))
    org_name = user_orgs[0]["name"] if user_orgs else "Enterprise Workspace"

    health_data = database.get_security_health_status(org_id=org_id)
    audit_logs = database.get_audit_logs(org_id=org_id, limit=50)

    export_folder = Path("exports").resolve()
    pdf_path = export_service.export_security_audit_report_pdf(
        health_data=health_data,
        audit_logs=audit_logs,
        folder=export_folder,
        org_name=org_name
    )

    return send_file(
        str(pdf_path.resolve()),
        as_attachment=True,
        download_name=f"Security_Audit_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype="application/pdf"
    )


@misc_bp.route("/api/security/verify-integrity", methods=["POST"])
@login_required
def verify_system_file_integrity():
    """Verify integrity of uploaded files and KB documents."""
    from pathlib import Path
    uploads_dir = Path("uploads")
    results = []
    if uploads_dir.exists():
        for f in uploads_dir.rglob("*"):
            if f.is_file():
                valid, msg = database.verify_file_integrity(str(f))
                results.append({
                    "file": f.name,
                    "valid": valid,
                    "status": msg
                })
    return jsonify({"ok": True, "files": results, "total_scanned": len(results)})


@misc_bp.route("/api/kb/anomalies")
@login_required
def get_kb_anomalies():
    """Scan and detect duplicate documents, hash collisions, and file anomalies in knowledge base."""
    import rag_engine
    org_id = get_current_org_id() or 1
    scan_report = rag_engine.detect_kb_duplicates_and_anomalies(org_id=org_id)
    return jsonify(scan_report)


@misc_bp.route("/api/security/blacklist")
@admin_required
def get_security_blacklist():
    """Retrieve list of blacklisted IP addresses and reasons."""
    blacklisted = database.get_blacklisted_ips()
    return jsonify({"ok": True, "blacklist": blacklisted})


@misc_bp.route("/api/security/unblock-ip", methods=["POST"])
@admin_required
def unblock_security_ip():
    """Admin endpoint to unban an IP address."""
    user = session.get("user", "Admin")
    data = request.json or {}
    ip_to_unblock = data.get("ip_address", "").strip()
    if not ip_to_unblock:
        return jsonify({"ok": False, "error": "missing_ip"}), 400

    success = database.unblock_ip(ip_to_unblock)
    if success:
        database.log_audit_event(user, "SECURITY_IP_UNBLOCKED", f"Unblocked IP: {ip_to_unblock}", request.remote_addr or "unknown", get_current_org_id() or 1)
        return jsonify({"ok": True, "message": f"ปลดบล็อค IP {ip_to_unblock} เรียบร้อยแล้ว"})
    return jsonify({"ok": False, "error": "not_found", "message": "ไม่พบ IP นี้ในรายการที่ถูกบล็อค"}), 404


@misc_bp.route("/api/security/mask-pii", methods=["POST"])
@login_required
def test_mask_pii():
    """Test and preview PII data masking & anonymization on arbitrary text."""
    data = request.json or {}
    raw_text = data.get("text", "")
    masked_text, detected_items = database.mask_pii_data(raw_text)
    return jsonify({
        "ok": True,
        "original_text": raw_text,
        "masked_text": masked_text,
        "detected_items": detected_items,
        "count": len(detected_items)
    })


@misc_bp.route("/api/security/threat-intel")
@admin_required
def get_security_threat_intel():
    """Retrieve SOC threat intelligence and live incident aggregation."""
    org_id = get_current_org_id() or 1
    intel = database.get_security_threat_intel(org_id=org_id)
    return jsonify(intel)


@misc_bp.route("/api/security/analyze-behavior", methods=["POST"])
@admin_required
def analyze_user_behavior_endpoint():
    """Analyze behavioral risk score for a specific user and IP."""
    data = request.json or {}
    target_user = data.get("username", session.get("user", "Anonymous"))
    target_ip = data.get("ip_address", request.remote_addr or "127.0.0.1")
    analysis = database.analyze_user_threat_behavior(
        username=target_user,
        client_ip=target_ip,
        action="UEBA_AUDIT_QUERY",
        org_id=get_current_org_id() or 1
    )
    return jsonify({"ok": True, "analysis": analysis})


@misc_bp.route("/health")
def health_check():
    """Used by uptime monitors (UptimeRobot, etc.) — returns 200 if server is alive."""
    db_ok = False
    try:
        conn = database._get_conn(timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        db_ok = True
    except Exception as e:
        logger.error(f"[HealthCheck] DB check failed ({database.DB_TYPE}): {e}")

    status = "ok" if db_ok else "degraded"
    return jsonify({
        "status": status,
        "db": db_ok,
        "db_type": database.DB_TYPE,
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
    }), 200 if db_ok else 503

