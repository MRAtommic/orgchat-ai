# -*- coding: utf-8 -*-
"""
Authentication Blueprint — Login, Logout, OAuth2, QR Login, LINE Magic Link, Password Reset, Org Signup
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, send_from_directory, send_file, abort, redirect, session
from markupsafe import escape as _html_escape
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
import secrets as _sec
from datetime import datetime, timedelta
from functools import wraps
import logging

import database
import billing
import payment
from google_drive_service import google_manager, GoogleWorkspaceManager

from routes.shared import (
    VERSION, socketio, _limiter, login_required, admin_required,
    PENDING_LINE_LINKS, _OAUTH_STATES, _store_oauth_state, _pop_oauth_state,
    send_push_notification, batch_send_push_notification,
    get_weather_context, THAI_HOLIDAYS_2026, get_current_time,
    VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS,
    OAUTH2_AVAILABLE, oauth2_service,
    GOOGLE_AUTH_AVAILABLE, id_token, google_requests,
    _set_session_org, get_current_org_id,
    _get_gemini_api_key, _configure_gemini,
    USERS,
)

logger = logging.getLogger("OrgChatAI.Auth")

auth_bp = Blueprint('auth', __name__)

_qr_tokens = {}  # legacy — superseded by DB-backed qr_* functions in database.py

QR_APPROVE_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>อนุมัติเข้าสู่ระบบ - OrgChat AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --brand: #2563eb;
            --brand-dark: #1d4ed8;
            --success: #10b981;
            --error: #ef4444;
            --bg: #0b0f19;
            --card-bg: rgba(17, 24, 39, 0.7);
            --card-border: rgba(255, 255, 255, 0.08);
            --text: #f3f4f6;
            --text-muted: #9ca3af;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Outfit', 'Sarabun', sans-serif;
            background: radial-gradient(circle at 50% 50%, #111827 0%, #030712 100%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow: hidden;
        }
        .glass-card {
            width: 100%;
            max-width: 420px;
            background: var(--card-bg);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--card-border);
            border-radius: 28px;
            padding: 40px 32px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
            text-align: center;
            animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .icon-box {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px auto;
            font-size: 36px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .icon-success {
            background: rgba(16, 185, 129, 0.1);
            border: 2px solid var(--success);
            color: var(--success);
        }
        .icon-error {
            background: rgba(239, 68, 68, 0.1);
            border: 2px solid var(--error);
            color: var(--error);
        }
        .icon-pending {
            background: rgba(37, 99, 235, 0.1);
            border: 2px solid var(--brand);
            color: var(--brand);
        }
        h1 {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #ffffff;
            letter-spacing: -0.5px;
        }
        p {
            font-size: 14px;
            color: var(--text-muted);
            line-height: 1.6;
            margin-bottom: 30px;
        }
        .user-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 8px 20px;
            border-radius: 99px;
            font-weight: 600;
            color: #fbbf24;
            font-size: 15px;
            margin-bottom: 24px;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 16px;
            border-radius: 16px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            font-family: inherit;
            border: none;
            outline: none;
            margin-bottom: 12px;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%);
            color: white;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.4);
            filter: brightness(1.1);
        }
        .btn-primary:active {
            transform: translateY(0);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text);
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .footer {
            margin-top: 24px;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.25);
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="glass-card">
        {% if error %}
            <div class="icon-box icon-error">✕</div>
            <h1>ไม่สามารถเข้าสู่ระบบได้</h1>
            <p>{{ error }}</p>
            <button class="btn btn-secondary" onclick="window.close()">ปิดหน้าจอนี้</button>
        {% elif valid %}
            <div id="approveContainer">
                <div class="icon-box icon-pending">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 17V7h5a3 3 0 0 1 0 6H9"/></svg>
                </div>
                <h1>อนุมัติเข้าสู่ระบบเครื่องคอมพิวเตอร์</h1>
                <p>คุณกำลังทำการเข้าสู่ระบบบนหน้าจอคอมพิวเตอร์ด้วยชื่อบัญชี:</p>
                <div class="user-badge">{{ user }}</div>
                <button class="btn btn-primary" id="btnApprove" onclick="approveLogin()">
                    อนุมัติการเข้าสู่ระบบ
                </button>
                <button class="btn btn-secondary" onclick="cancelLogin()">ยกเลิก</button>
            </div>
            
            <div id="statusContainer" class="hidden">
                <div class="icon-box icon-success">✓</div>
                <h1 style="color: var(--success)">อนุมัติสำเร็จ!</h1>
                <p>หน้าจอคอมพิวเตอร์ของคุณจะเข้าสู่ระบบในสักครู่ คุณสามารถปิดหน้าต่างนี้ได้เลยค่ะ</p>
                <button class="btn btn-primary" onclick="window.close()">เสร็จสิ้น</button>
            </div>
        {% else %}
            <div class="icon-box icon-error">✕</div>
            <h1>ข้อมูลไม่ถูกต้อง</h1>
            <p>ไม่พบข้อมูลคำขอ หรือคำขอเข้าสู่ระบบของคุณไม่ถูกต้อง</p>
            <button class="btn btn-secondary" onclick="window.close()">ปิดหน้าจอนี้</button>
        {% endif %}
        
        <div class="footer">
            OrgChat AI &bull; Secure Authentication
        </div>
    </div>

    <script>
        async function approveLogin() {
            const btn = document.getElementById('btnApprove');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>กำลังอนุมัติ...';

            try {
                const res = await fetch('/api/qr/approve/' + {{ token | tojson }}, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (data.ok) {
                    document.getElementById('approveContainer').classList.add('hidden');
                    document.getElementById('statusContainer').classList.remove('hidden');
                } else {
                    alert('ไม่สามารถอนุมัติได้: ' + (data.error || 'เกิดข้อผิดพลาด'));
                    btn.disabled = false;
                    btn.textContent = 'อนุมัติการเข้าสู่ระบบ';
                }
            } catch (err) {
                alert('เกิดข้อผิดพลาดในการเชื่อมต่อ กรุณาลองใหม่อีกครั้ง');
                btn.disabled = false;
                btn.textContent = 'อนุมัติการเข้าสู่ระบบ';
            }
        }
        
        function cancelLogin() {
            if (confirm('คุณต้องการยกเลิกคำขอเข้าสู่ระบบนี้หรือไม่?')) {
                window.close();
            }
        }
    </script>
</body>
</html>"""

@auth_bp.route("/api/auth/google/debug-uri")
def auth_google_debug_uri():
    """แสดง redirect_uri ที่ app จะส่งไปให้ Google — ใช้ตรวจสอบว่าตรงกับ Console ไหม"""
    return jsonify({
        "redirect_uri_in_use": oauth2_service.redirect_uri if OAUTH2_AVAILABLE else "OAuth2 not available",
        "env_OAUTH2_REDIRECT_URI": os.environ.get("OAUTH2_REDIRECT_URI", "(ไม่ได้ตั้งค่า — ใช้ default localhost)"),
    })


@auth_bp.route("/api/auth/google/start")
def auth_google_start():
    """
    Initiate Google OAuth2 login flow.
    ?mode=org  → เชื่อมต่อระดับบริษัท (เฉพาะ admin) ทุกคนในบริษัทใช้ร่วมกัน
    ?mode=personal (default) → เชื่อมต่อส่วนตัว
    """
    if not OAUTH2_AVAILABLE or not oauth2_service.is_configured:
        return jsonify({"ok": False, "error": "ระบบ Google OAuth2 ยังไม่ได้ตั้งค่า กรุณาติดต่อผู้ดูแลระบบ"}), 503

    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อนเชื่อมต่อ Google"}), 401

    mode = request.args.get("mode", "personal")  # 'org' or 'personal'

    if mode == "org":
        user_role = session.get("role", "user")
        org_role = session.get("org_role", "member")
        if user_role != "admin" and org_role != "admin":
            return jsonify({"ok": False, "error": "เฉพาะ Admin เท่านั้นที่เชื่อมต่อ Google ระดับองค์กรได้"}), 403
        org_id = get_current_org_id() or session.get("org_id", 1)
        if not billing.has_feature(org_id, "google_sheets"):
            plan = billing.get_effective_plan(org_id)
            return jsonify({
                "ok": False,
                "error": "upgrade_required",
                "message": "การเชื่อมต่อ Google Sheets ต้องการ Plan Pro ขึ้นไป",
                "current_plan": plan,
            }), 403
    else:
        org_id = None

    try:
        redirect_uri = oauth2_service.redirect_uri
        import secrets as _sec
        state_token = _sec.token_urlsafe(32)

        authorization_url, _, code_verifier = oauth2_service.get_authorization_url(
            redirect_uri=redirect_uri,
            state=state_token
        )

        # เก็บ state บน server (ไม่พึ่ง session cookie — แก้ปัญหา Cloudflare Tunnel)
        _store_oauth_state(state_token, {
            "username": username,
            "mode": mode,
            "org_id": org_id,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        })

        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"OAuth2 start error: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถเชื่อมต่อ Google ได้ กรุณาลองใหม่"}), 500


@auth_bp.route("/api/auth/google/callback")
def auth_google_callback():
    """Handle Google OAuth2 callback — exchange code for tokens."""
    if not OAUTH2_AVAILABLE:
        return "<h1>OAuth2 ไม่พร้อมใช้งาน</h1>", 503

    # Verify state — อ่านจาก server-side store ไม่พึ่ง session cookie
    state = request.args.get('state')
    state_data = _pop_oauth_state(state) if state else None
    if not state_data:
        return "<h1>Invalid state — กรุณาลองใหม่</h1><p><a href='/'>กลับหน้าหลัก</a></p>", 400

    username = state_data.get("username") or session.get("user")
    if not username:
        return "<h1>กรุณาเข้าสู่ระบบก่อน</h1><p><a href='/'>กลับหน้าหลัก</a></p>", 401

    # Check for error from Google
    error = request.args.get('error')
    if error:
        if error == 'access_denied':
            # User pressed cancel — redirect back, previously connected email is still saved
            return redirect('/?google_cancelled=1')
        return redirect(f'/?google_error=1')

    authorization_code = request.args.get('code')
    if not authorization_code:
        return "<h1>ไม่พบ authorization code</h1><p><a href='/'>กลับหน้าหลัก</a></p>", 400

    try:
        redirect_uri = state_data.get("redirect_uri", oauth2_service.redirect_uri)
        mode = state_data.get("mode", "personal")
        org_id = state_data.get("org_id")

        # Exchange the code for tokens
        token_result = oauth2_service.exchange_code_for_token(
            authorization_code,
            redirect_uri=redirect_uri,
            code_verifier=state_data.get("code_verifier")
        )

        google_email = token_result.get('email', '')
        google_name  = token_result.get('name', '')

        if mode == 'org' and org_id:
            # บันทึกโทเค็นระดับบริษัท — ทุกคนในบริษัทใช้ร่วมกัน
            database.save_org_google_token(
                org_id=org_id,
                google_email=google_email,
                access_token=token_result.get('access_token'),
                refresh_token=token_result.get('refresh_token'),
                token_expiry=token_result.get('token_expiry'),
                connected_by=username
            )
            setup_ok = oauth2_service.setup_org_workspace(org_id, google_email, connected_by=username)
            scope_label = "บริษัท (ทุกคนในองค์กรใช้ร่วมกัน)"
        else:
            # บันทึกโทเค็นส่วนตัว
            database.save_google_token(
                username=username,
                google_email=google_email,
                access_token=token_result.get('access_token'),
                refresh_token=token_result.get('refresh_token'),
                token_expiry=token_result.get('token_expiry')
            )
            # Update profile with Google avatar if not set
            profile = database.get_user_profile(username)
            if not profile.get('avatar_url'):
                database.update_user_profile(username, display_name=google_name,
                                             avatar_url=token_result.get('picture'))
            setup_ok = oauth2_service.setup_user_workspace(username, google_email)
            scope_label = "ส่วนตัว"

        GoogleWorkspaceManager.invalidate_user_cache(username)

        _CSS = """body{font-family:'Inter','Sarabun',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
        .card{background:white;border-radius:20px;padding:40px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.3);max-width:460px}
        .email{background:#F0FDF4;color:#059669;padding:8px 16px;border-radius:10px;font-weight:600;display:inline-block;margin:10px 0}
        .badge{background:#EFF6FF;color:#1D4ED8;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600}
        .btn{display:inline-block;background:#1D4ED8;color:white;padding:12px 30px;border-radius:12px;text-decoration:none;font-weight:600;margin-top:20px}"""

        if setup_ok:
            return render_template_string(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>เชื่อมต่อสำเร็จ!</title>
            <style>{_CSS}</style>
            <script>setTimeout(()=>{{window.location.href='/?google_connected=1';}},3000);</script>
            </head>
            <body style="background:linear-gradient(135deg,#667eea,#764ba2)">
            <div class="card">
              <div style="font-size:48px">✅</div>
              <h1 style="color:#059669">เชื่อมต่อ Google สำเร็จ!</h1>
              <span class="badge">ระดับ: {{{{ scope }}}}</span>
              <br><div class="email">{{{{ email }}}}</div>
              <p style="color:#475569">ระบบสร้าง Google Sheets และโฟลเดอร์ Drive เรียบร้อยแล้ว</p>
              <p style="color:#94a3b8;font-size:13px">กำลังกลับหน้าหลักใน 3 วินาที...</p>
              <a href="/?google_connected=1" class="btn">กลับหน้าหลัก</a>
            </div></body></html>""", email=google_email, scope=scope_label)
        else:
            return render_template_string(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>เชื่อมต่อ (บางส่วน)</title>
            <style>{_CSS}</style>
            <script>setTimeout(()=>{{window.location.href='/?google_connected=1';}},4000);</script>
            </head>
            <body style="background:linear-gradient(135deg,#f59e0b,#ef4444)">
            <div class="card">
              <h1 style="color:#D97706">⚠️ เชื่อมต่อสำเร็จ แต่สร้าง Workspace ไม่สมบูรณ์</h1>
              <span class="badge">ระดับ: {{{{ scope }}}}</span>
              <p style="color:#475569">บัญชีเชื่อมต่อแล้ว แต่สร้าง Sheets/Drive ไม่สำเร็จ ลองยกเลิกแล้วเชื่อมต่อใหม่</p>
              <a href="/?google_connected=1" class="btn">กลับหน้าหลัก</a>
            </div></body></html>""", scope=scope_label)

    except Exception as e:
        logger.error(f"OAuth2 callback error: {e}")
        return f"<h1>เกิดข้อผิดพลาด</h1><p>{_html_escape(str(e))}</p><p><a href='/'>กลับหน้าหลัก</a></p>", 500


@auth_bp.route("/api/auth/google/status")
def auth_google_status():
    """Check if the current user has connected their Google account."""
    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    if not OAUTH2_AVAILABLE:
        return jsonify({
            "ok": True,
            "oauth2_available": False,
            "connected": False,
            "message": "ระบบ OAuth2 ไม่พร้อมใช้งาน"
        })

    org_id   = session.get("org_id", 1)
    user_role = session.get("role", "user")

    # Org-level status
    org_info = oauth2_service.get_org_connection_info(org_id)
    # Personal status
    personal_info = oauth2_service.get_user_connection_info(username)

    # Effective connection = org first, then personal
    effective = org_info if org_info['connected'] else personal_info
    effective_source = 'org' if org_info['connected'] else ('personal' if personal_info['connected'] else 'none')

    def _sheet_url(sid):
        return f"https://docs.google.com/spreadsheets/d/{sid}/edit" if sid else None
    def _drive_url(fid):
        return f"https://drive.google.com/drive/folders/{fid}" if fid else None

    return jsonify({
        "ok": True,
        "oauth2_available": oauth2_service.is_configured,
        "is_admin": user_role == "admin",
        "effective_source": effective_source,
        "connected": effective['connected'],
        "email": effective.get('email'),
        "spreadsheet_id": effective.get('spreadsheet_id'),
        "spreadsheet_url": _sheet_url(effective.get('spreadsheet_id')),
        "drive_folder_url": _drive_url(effective.get('drive_folder_id')),
        "org": {
            "connected": org_info['connected'],
            "email": org_info.get('email'),
            "connected_by": org_info.get('connected_by'),
            "spreadsheet_url": _sheet_url(org_info.get('spreadsheet_id')),
            "drive_folder_url": _drive_url(org_info.get('drive_folder_id')),
        },
        "personal": {
            "connected": personal_info['connected'],
            "email": personal_info.get('email'),
            "spreadsheet_url": _sheet_url(personal_info.get('spreadsheet_id')),
            "drive_folder_url": _drive_url(personal_info.get('drive_folder_id')),
        }
    })


@auth_bp.route("/api/auth/google/disconnect", methods=["POST"])
def auth_google_disconnect():
    """
    Disconnect Google account.
    ?scope=org  → ยกเลิกระดับบริษัท (admin only)
    ?scope=personal → ยกเลิกส่วนตัว (default)
    """
    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    if not OAUTH2_AVAILABLE:
        return jsonify({"ok": False, "error": "OAuth2 not available"}), 503

    scope = request.args.get("scope", "personal")

    if scope == "org":
        user_role = session.get("role", "user")
        if user_role != "admin":
            return jsonify({"ok": False, "error": "เฉพาะ Admin เท่านั้นที่ยกเลิกการเชื่อมต่อระดับบริษัทได้"}), 403
        org_id = session.get("org_id", 1)
        oauth2_service.disconnect_org(org_id)
        google_manager.set_context(username=None, org_id=org_id)
        return jsonify({"ok": True, "message": "ยกเลิกการเชื่อมต่อ Google ระดับบริษัทสำเร็จ"})

    oauth2_service.disconnect_user(username)
    GoogleWorkspaceManager.invalidate_user_cache(username)
    return jsonify({"ok": True, "message": "ยกเลิกการเชื่อมต่อ Google ส่วนตัวสำเร็จ"})


def render_link_error(error):
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>เกิดข้อผิดพลาด - OrgChat AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --error: #EF4444;
                --bg: #0D0D0D;
                --card-bg: rgba(25, 25, 25, 0.65);
                --card-border: rgba(239, 68, 68, 0.2);
                --text: #F3F4F6;
                --text-muted: #9CA3AF;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', 'Sarabun', sans-serif;
                background: radial-gradient(circle at 50% 50%, #1c1515 0%, #0d0d0d 100%);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                overflow-x: hidden;
            }}
            .container {{
                width: 100%;
                max-width: 440px;
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 48px 32px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
                text-align: center;
                animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .error-icon {{
                width: 72px;
                height: 72px;
                background: rgba(239, 68, 68, 0.1);
                border: 2px solid var(--error);
                color: var(--error);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                margin: 0 auto 28px auto;
                box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
                animation: scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
            }}
            @keyframes scaleIn {{
                from {{ transform: scale(0); opacity: 0; }}
                to {{ transform: scale(1); opacity: 1; }}
            }}
            h1 {{
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 16px;
                color: #FFFFFF;
            }}
            p {{
                font-size: 15px;
                color: var(--text-muted);
                line-height: 1.6;
                margin-bottom: 32px;
            }}
            .btn {{
                display: inline-block;
                width: 100%;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: var(--text);
                font-weight: 600;
                font-size: 15px;
                padding: 14px;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                margin-top: 10px;
                font-family: inherit;
            }}
            .btn:hover {{
                background: rgba(255, 255, 255, 0.1);
                border-color: rgba(255, 255, 255, 0.2);
            }}
            .footer-info {{
                margin-top: 40px;
                font-size: 11px;
                color: rgba(255, 255, 255, 0.2);
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">!</div>
            <h1>เกิดข้อผิดพลาดในการผูกบัญชีค่ะ</h1>
            <p>{error}</p>
            
            <a href="javascript:window.close();" class="btn">ปิดหน้าต่างนี้</a>
            
            <div class="footer-info">
                ORGCHAT AI SYSTEM &bull; ERROR ENCOUNTERED
            </div>
        </div>
    </body>
    </html>
    """


def render_success_page(username):
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ผูกบัญชีสำเร็จ - OrgChat AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --success: #10B981;
                --bg: #0D0D0D;
                --card-bg: rgba(25, 25, 25, 0.65);
                --card-border: rgba(16, 185, 129, 0.2);
                --text: #F3F4F6;
                --text-muted: #9CA3AF;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', 'Sarabun', sans-serif;
                background: radial-gradient(circle at 50% 50%, #151a18 0%, #0d0d0d 100%);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                overflow-x: hidden;
            }}
            .container {{
                width: 100%;
                max-width: 440px;
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 48px 32px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
                text-align: center;
                animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .success-icon {{
                width: 72px;
                height: 72px;
                background: rgba(16, 185, 129, 0.1);
                border: 2px solid var(--success);
                color: var(--success);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                margin: 0 auto 28px auto;
                box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
                animation: scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
            }}
            @keyframes scaleIn {{
                from {{ transform: scale(0); opacity: 0; }}
                to {{ transform: scale(1); opacity: 1; }}
            }}
            h1 {{
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 12px;
                color: #FFFFFF;
            }}
            .username-badge {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #D4AF37;
                padding: 6px 16px;
                border-radius: 99px;
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            p {{
                font-size: 15px;
                color: var(--text-muted);
                line-height: 1.6;
                margin-bottom: 32px;
            }}
            .info-box {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 16px;
                text-align: left;
                font-size: 13px;
                color: var(--text-muted);
                line-height: 1.5;
            }}
            .info-item {{
                display: flex;
                margin-bottom: 8px;
            }}
            .info-item:last-child {{
                margin-bottom: 0;
            }}
            .info-label {{
                font-weight: bold;
                color: var(--text);
                width: 24px;
                flex-shrink: 0;
            }}
            .footer-info {{
                margin-top: 40px;
                font-size: 11px;
                color: rgba(255, 255, 255, 0.2);
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">&#10003;</div>
            <h1>ผูกบัญชีสำเร็จเรียบร้อยค่ะ!</h1>
            <div class="username-badge">{username}</div>
            <p>ยินดีด้วยค่ะ บัญชี LINE ของคุณได้รับการผูกกับระบบ OrgChat AI เรียบร้อยแล้ว ต่อจากนี้ สลิปและไฟล์ที่คุณส่งใน LINE จะถูกบันทึกเข้า Drive และ Sheet ส่วนตัวของคุณโดยตรงโดยอัตโนมัติค่ะ</p>
            
            <div class="info-box">
                <div class="info-item">
                    <span class="info-label">&#128161;</span>
                    <span>ตอนนี้คุณสามารถกลับไปใช้งานที่แชท LINE Bot ได้ตามปกติเลยนะคะ</span>
                </div>
            </div>
            
            <div class="footer-info">
                ORGCHAT AI SYSTEM &bull; SECURE CONNECTION
            </div>
        </div>
    </body>
    </html>
    """


def render_login_page(token, error=None):
    error_html = f'<div class="error-msg">&#9888; {error}</div>' if error else ''
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ผูกบัญชี LINE - OrgChat AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #cda252;
                --primary-hover: #b88d3d;
                --bg: #0D0D0D;
                --card-bg: rgba(25, 25, 25, 0.65);
                --card-border: rgba(205, 170, 82, 0.15);
                --text: #F3F4F6;
                --text-muted: #9CA3AF;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', 'Sarabun', sans-serif;
                background: radial-gradient(circle at 50% 50%, #1c1a17 0%, #0d0d0d 100%);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                overflow-x: hidden;
            }}
            .container {{
                width: 100%;
                max-width: 440px;
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 40px 32px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
                text-align: center;
                position: relative;
                animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .logo-container {{
                margin-bottom: 24px;
            }}
            .logo {{
                font-size: 28px;
                font-weight: 700;
                letter-spacing: 2px;
                background: linear-gradient(135deg, #FFF 30%, var(--primary) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            h1 {{
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 8px;
                color: var(--text);
            }}
            p {{
                font-size: 14px;
                color: var(--text-muted);
                line-height: 1.6;
                margin-bottom: 28px;
            }}
            .form-group {{
                margin-bottom: 20px;
                text-align: left;
            }}
            label {{
                display: block;
                font-size: 13px;
                font-weight: 600;
                color: var(--text-muted);
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            input {{
                width: 100%;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 14px 16px;
                font-size: 15px;
                color: var(--text);
                outline: none;
                transition: all 0.3s;
                font-family: inherit;
            }}
            input:focus {{
                border-color: var(--primary);
                background: rgba(255, 255, 255, 0.06);
                box-shadow: 0 0 0 4px rgba(205, 170, 82, 0.1);
            }}
            .error-msg {{
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.25);
                color: #F87171;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                text-align: left;
                margin-bottom: 20px;
                line-height: 1.5;
            }}
            .btn {{
                width: 100%;
                background: linear-gradient(135deg, var(--primary) 0%, #b88d3d 100%);
                color: #0D0D0D;
                font-weight: 700;
                font-size: 15px;
                padding: 14px;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                margin-top: 10px;
                font-family: inherit;
                box-shadow: 0 4px 12px rgba(205, 170, 82, 0.2);
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(205, 170, 82, 0.35);
                background: linear-gradient(135deg, #e3b865 0%, var(--primary) 100%);
            }}
            .btn:active {{
                transform: translateY(0);
            }}
            .footer-info {{
                margin-top: 32px;
                font-size: 11px;
                color: rgba(255, 255, 255, 0.3);
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-container">
                <span class="logo">ORGCHAT AI</span>
            </div>
            <h1>เชื่อมต่อ LINE Bot ของคุณ</h1>
            <p>กรุณาลงชื่อเข้าใช้ด้วยบัญชี OrgChat AI ของคุณเพื่อผูกบัญชี LINE Bot และเข้าถึงระบบจัดเก็บเอกสารอัตโนมัติค่ะ</p>
            
            {error_html}
            
            <form method="POST" action="/line/link_magic?token={token}">
                <div class="form-group">
                    <label for="username">ชื่อผู้ใช้ (Username)</label>
                    <input type="text" id="username" name="username" placeholder="ระบุชื่อผู้ใช้ของคุณ" required autocomplete="username">
                </div>
                <div class="form-group">
                    <label for="password">รหัสผ่าน (Password)</label>
                    <input type="password" id="password" name="password" placeholder="ระบุรหัสผ่านของคุณ" required autocomplete="current-password">
                </div>
                <button type="submit" class="btn">ผูกบัญชีใช้งาน</button>
            </form>
            
            <div class="footer-info">
                SECURE AUTHENTICATION &bull; ORGCHAT SYSTEM
            </div>
        </div>
    </body>
    </html>
    """


@auth_bp.route("/line/link_magic", methods=['GET', 'POST'])
def line_link_magic():
    token = request.args.get('token')
    if not token:
        return render_link_error("โทเค็นสำหรับผูกบัญชีไม่ถูกต้องหรือหมดอายุแล้วค่ะ"), 400

    # อ่านจาก DB (multi-worker safe) พร้อม fallback memory เผื่อ migration
    link_data = database.line_link_get(token)
    if not link_data:
        # Fallback: เช็ค in-memory dict เผื่อมี token ที่สร้างก่อน migration
        _mem = PENDING_LINE_LINKS.get(token)
        if _mem:
            link_data = {"line_user_id": _mem["line_user_id"],
                         "expires_at": _mem.get("timestamp", 0) + 600}
        else:
            return render_link_error("โทเค็นสำหรับผูกบัญชีไม่ถูกต้องหรือหมดอายุแล้วค่ะ"), 400

    if time.time() > link_data.get("expires_at", 0):
        database.line_link_delete(token)
        PENDING_LINE_LINKS.pop(token, None)
        return render_link_error("โทเค็นสำหรับผูกบัญชีหมดอายุแล้วค่ะ กรุณาขอลิงก์ใหม่ใน LINE Bot อีกครั้งนะคะ"), 400

    line_user_id = link_data["line_user_id"]

    if request.method == 'GET':
        username = session.get("user")
        if username:
            database.link_line_user(username, line_user_id)
            database.line_link_delete(token)
            PENDING_LINE_LINKS.pop(token, None)
            return render_success_page(username)
        return render_login_page(token)

    elif request.method == 'POST':
        username_raw = request.form.get("username", "").strip()
        username_lower = username_raw.lower()
        password = request.form.get("password", "")

        settings = database.get_user_setting(username_raw)
        authenticated = False
        resolved_username = username_raw

        if settings.get("custom_password") and database.check_password(password, settings["custom_password"]):
            if not settings.get("is_active", 1):
                return render_login_page(token, error="บัญชีผู้ใช้ของคุณถูกระงับการใช้งานชั่วคราวค่ะ")
            resolved_username = settings.get("username_original", username_raw)
            authenticated = True
        elif username_lower in USERS and hmac.compare_digest(USERS[username_lower], password):
            if not settings.get("is_active", 1):
                return render_login_page(token, error="บัญชีผู้ใช้ของคุณถูกระงับการใช้งานชั่วคราวค่ะ")
            resolved_username = username_raw.capitalize()
            authenticated = True

        if authenticated:
            session.clear()  # ป้องกัน session fixation
            session.permanent = True
            session["user"] = resolved_username
            resolved_settings = database.get_user_setting(resolved_username)
            session["role"] = resolved_settings.get("role", "user")
            database.link_line_user(resolved_username, line_user_id)
            database.line_link_delete(token)
            PENDING_LINE_LINKS.pop(token, None)
            return render_success_page(resolved_username)
        else:
            return render_login_page(token, error="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้องค่ะ")


@auth_bp.route("/api/login", methods=["POST"])
@_limiter.limit("10 per minute; 50 per hour")
def api_login():
    data = request.json
    username_raw = data.get("username", "").strip()
    username_lower = username_raw.lower()
    password = data.get("password", "")

    # ตรวจสอบ IP จาก SQLite (persist ข้าม restart — ป้องกัน brute-force)
    client_ip = request.remote_addr or "unknown"
    if database.count_failed_attempts(client_ip) >= database._LOGIN_ATTEMPT_LIMIT:
        return jsonify({"ok": False, "error": "IP นี้ถูกล็อคชั่วคราวเนื่องจากพยายามเข้าสู่ระบบผิดพลาดหลายครั้ง กรุณาลองใหม่ใน 1 ชั่วโมง"}), 429
    
    # 1. Check Database first (Dynamic Users) — supports bcrypt hashed passwords
    settings = database.get_user_setting(username_raw)

    def _check_whitelist(uname):
        """Return error string if whitelist blocks this user, else None."""
        user_orgs = database.get_user_orgs(uname)
        if not user_orgs:
            return None  # ยังไม่ได้อยู่ org ไหน → ไม่มี whitelist ที่ต้องตรวจ
        org_id = user_orgs[0]["id"]
        if not database.is_whitelist_enabled(org_id):
            return None
        # สมาชิกที่มีอยู่แล้วในองค์กรผ่านได้เสมอ — whitelist กันแค่คนใหม่
        if database.is_org_member(org_id, uname):
            return None
        email = settings.get("email", "")
        if not email or not database.is_email_allowed(org_id, email):
            return "อีเมลนี้ไม่อยู่ในรายชื่อที่ได้รับอนุญาต (Whitelist)"
        return None

    if settings.get("custom_password") and database.check_password(password, settings["custom_password"]):
        if not settings.get("is_active", 1):
            return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403
        wl_err = _check_whitelist(username_raw)
        if wl_err:
            return jsonify({"ok": False, "error": wl_err}), 403
        session.clear()  # ป้องกัน session fixation
        session.permanent = True
        session["user"] = settings.get("username_original", username_raw)
        session["role"] = settings.get("role", "user")
        _set_session_org(session["user"])
        database.record_login_attempt(client_ip, username_raw, success=True)
        return jsonify({"ok": True, "user": session["user"], "role": session["role"], "org_role": session.get("org_role"), "has_org": session.get("org_id") is not None})

    # 2. Fallback to Hardcoded (plain text)
    if username_lower in USERS and hmac.compare_digest(USERS[username_lower], password):
        user_to_session = username_raw.capitalize()
        if not settings.get("is_active", 1):
             return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403
        session.clear()  # ป้องกัน session fixation
        session.permanent = True
        session["user"] = user_to_session
        session["role"] = settings.get("role", "user")
        _set_session_org(user_to_session)
        database.record_login_attempt(client_ip, username_raw, success=True)
        return jsonify({"ok": True, "user": user_to_session, "role": session["role"], "org_role": session.get("org_role"), "has_org": session.get("org_id") is not None})

    database.record_login_attempt(client_ip, username_raw, success=False)
    return jsonify({"ok": False, "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"})


@auth_bp.route("/api/qr/generate", methods=["POST"])
@_limiter.limit("10 per minute; 30 per hour")
def qr_generate():
    """Generate a unique QR login token stored in DB (safe for multi-worker)."""
    token = str(uuid.uuid4())
    database.qr_create_token(token)
    return jsonify({"ok": True, "token": token})


@auth_bp.route("/api/qr/poll/<token>")
@_limiter.limit("60 per minute")
def qr_poll(token):
    """Desktop polls this to check if QR was scanned and approved."""
    entry = database.qr_get_token(token)
    if not entry:
        return jsonify({"ok": False, "error": "Token expired or invalid"}), 404

    if time.time() > entry["expires_at"]:
        return jsonify({"ok": False, "error": "Token expired"}), 410

    if entry["status"] == "approved":
        user = database.qr_consume_token(token)
        if not user:
            return jsonify({"ok": False, "error": "Token expired or already used"}), 410
        session.clear()  # ป้องกัน session fixation
        session.permanent = True
        session["user"] = user
        _u_settings = database.get_user_setting(user)
        session["role"] = _u_settings.get("role", "user")
        _set_session_org(user)
        return jsonify({"ok": True, "status": "approved", "user": user, "role": session["role"], "org_role": session.get("org_role")})

    return jsonify({"ok": True, "status": "pending"})


@auth_bp.route("/api/qr/approve/<token>", methods=["POST"])
@login_required
def qr_approve(token):
    """Mobile user (already logged in) approves a QR login token."""
    user = session.get("user")
    ok = database.qr_approve_token(token, user)
    if not ok:
        entry = database.qr_get_token(token)
        if not entry:
            return jsonify({"ok": False, "error": "Token ไม่ถูกต้องหรือหมดอายุ"}), 404
        return jsonify({"ok": False, "error": "Token หมดอายุแล้ว"}), 410
    return jsonify({"ok": True, "message": f"อนุมัติเข้าสู่ระบบสำหรับ {user} เรียบร้อย"})


@auth_bp.route("/qr-login/<token>")
def qr_login_page(token):
    """Page that mobile opens after scanning QR code."""
    entry = database.qr_get_token(token)
    if not entry:
        return render_template_string(QR_APPROVE_HTML, token=token, error="Token ไม่ถูกต้องหรือหมดอายุ", valid=False)
    if time.time() > entry["expires_at"]:
        return render_template_string(QR_APPROVE_HTML, token=token, error="Token หมดอายุแล้ว กรุณาสร้าง QR Code ใหม่", valid=False)
    user = session.get("user")
    if not user:
        return render_template_string(QR_APPROVE_HTML, token=token, error="กรุณาเข้าสู่ระบบบนมือถือก่อน แล้วสแกนอีกครั้ง", valid=False)
    return render_template_string(QR_APPROVE_HTML, token=token, error=None, valid=True, user=user)


@auth_bp.route("/api/login/google", methods=["POST"])
def api_login_google():
    data = request.json
    token = data.get("credential")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    
    if not token or not client_id:
        return jsonify({"ok": False, "error": "ไม่สามารถตรวจสอบสิทธิ์ด้วย Google ได้ (ไม่มี Token หรือ Client ID)"}), 400

    if not GOOGLE_AUTH_AVAILABLE:
        return jsonify({"ok": False, "error": "Google Auth library not installed on server"}), 500

    try:
        # Verify the token with clock skew tolerance to handle system clock desyncs
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            client_id, 
            clock_skew_in_seconds=60
        )

        # Token is valid, get the user's email
        email = idinfo.get("email")
        if not email:
            return jsonify({"ok": False, "error": "ไม่พบอีเมลจาก Google Account"}), 400

        # ── Resolve username (ป้องกัน collision ระหว่าง email จาก domain ต่างกัน) ──
        # ขั้นแรก: ลองใช้ email prefix เหมือนเดิมเพื่อ backward compat
        _GOOGLE_RESERVED = frozenset({
            "admin", "root", "system", "support", "api", "null", "undefined",
            "test", "guest", "owner", "superadmin", "staff", "bot", "service",
            "help", "info", "mail", "billing", "account", "security",
        })
        base_uname = re.sub(r'[^a-z0-9_]', '_', email.split('@')[0].lower())[:28]
        # ถ้าชนกับ reserved word → เพิ่ม _g ต่อท้าย
        if base_uname in _GOOGLE_RESERVED:
            base_uname = f"{base_uname}_g"[:30]
            logger.info(f"[GoogleLogin] reserved username '{base_uname}' from {email} — using '{base_uname}'")
        username = base_uname
        # ตรวจสอบว่า username มีอยู่แล้วและเป็นคนละ email หรือไม่
        existing_settings = database.get_user_setting(username)
        if existing_settings:
            stored_email = (existing_settings.get("email") or "").lower()
            if stored_email and stored_email != email.lower():
                # collision! ใช้ suffix จาก domain เพื่อทำให้ unique
                domain_tag = re.sub(r'[^a-z0-9]', '', email.split('@')[1].split('.')[0].lower())[:8]
                username = f"{base_uname}_{domain_tag}"[:30]
                logger.info(f"[GoogleLogin] username collision on {base_uname!r} — using {username!r} for {email}")

        # --- Whitelist Check & Auto-Binding ---
        user_orgs = database.get_user_orgs(username)

        # Check if the user has no organization yet (or only belongs to the Default Organization), but their email is whitelisted in any organization
        has_real_org = any(o["id"] != 1 for o in user_orgs)
        if not has_real_org:
            allowed_orgs = []
            try:
                allowed_orgs = database.get_email_whitelisted_organizations(email)
            except Exception as e:
                logger.error(f"Error checking email whitelisted organizations: {e}")

            if allowed_orgs:
                first_org = allowed_orgs[0]
                first_org_id = first_org["organization_id"]
                first_org_role = first_org.get("role", "member")
                first_org_invited_by = first_org.get("added_by", "system")

                # Ensure user_settings and user_profiles entries exist for this username
                try:
                    conn = database._get_conn()
                    cur = conn.cursor()
                    cur.execute("INSERT OR IGNORE INTO user_settings (username, role, is_active, email) VALUES (?, 'user', 1, ?)", (username, email))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"Error seeding user_settings for Gmail login: {e}")

                # Add as member — ตรวจ quota ก่อนเสมอ (ป้องกัน free plan เกิน 1 คน)
                try:
                    _gplan = billing.get_effective_plan(first_org_id)
                    _gmax  = billing.get_plan_config(_gplan)["limits"]["max_users"]
                    _ok, _reason = database.add_org_member_with_quota(
                        first_org_id, username,
                        role=first_org_role,
                        invited_by=first_org_invited_by,
                        max_users=_gmax,
                    )
                    if not _ok:
                        logger.warning(f"[GoogleLogin] auto-join blocked for {username} org={first_org_id}: {_reason}")
                        return jsonify({"ok": False, "error": "องค์กรนี้มีสมาชิกเต็มโควต้าแล้ว กรุณาติดต่อผู้ดูแลองค์กรเพื่อขอสิทธิ์"}), 403
                    else:
                        # Auto-joined whitelisted org! Now clean up by removing them from Default Organization (ID 1) if they were in it
                        try:
                            database.remove_org_member(1, username)
                        except Exception as e:
                            logger.error(f"Failed to remove user from Default Org after auto-join: {e}")
                except Exception as e:
                    logger.error(f"Error binding user to organization: {e}")

                # Refresh user_orgs so the login session logic knows about this organization
                user_orgs = database.get_user_orgs(username)

        target_org_id = user_orgs[0]["id"] if user_orgs else None

        if target_org_id and database.is_whitelist_enabled(target_org_id):
            # สมาชิกที่มีอยู่แล้วผ่านได้เสมอ
            if not database.is_org_member(target_org_id, username) and not database.is_email_allowed(target_org_id, email):
                return jsonify({"ok": False, "error": "อีเมลนี้ไม่อยู่ในรายชื่อที่ได้รับอนุญาตให้เข้าสู่ระบบ (Whitelist)"}), 403

        # Check if user exists or is active
        settings = database.get_user_setting(username)
        if settings and not settings.get("is_active", 1):
             return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403

        # Update user profile with Google info if they have no avatar/display name
        profile = database.get_user_profile(username)
        display_name = profile.get("display_name") if profile.get("display_name") else idinfo.get("name")
        avatar_url = profile.get("avatar_url") if profile.get("avatar_url") else idinfo.get("picture")
        database.update_user_profile(username, display_name=display_name, avatar_url=avatar_url)

        # ── บันทึก email ลง user_settings เพื่อใช้ตรวจ collision ในอนาคต ──
        try:
            conn = database._get_conn()
            conn.execute("UPDATE user_settings SET email=? WHERE username=? AND (email IS NULL OR email='')", (email, username))
            conn.commit()
            conn.close()
        except Exception:
            pass

        session.clear()
        session.permanent = True
        session["user"] = username
        session["role"] = settings.get("role", "user") if settings else "user"
        _set_session_org(username)
        return jsonify({"ok": True, "user": username, "role": session["role"], "org_role": session.get("org_role")})

    except Exception as e:
        logger.error(f"Google Login Error: {e}")
        return jsonify({"ok": False, "error": "เข้าสู่ระบบด้วย Google ไม่สำเร็จ กรุณาลองใหม่"}), 500


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()  # Clear entire session securely on logout
    return jsonify({"ok": True})


@auth_bp.route("/api/me")
def api_me():
    user = session.get("user")
    if user:
        profile = database.get_user_profile(user)
        user_settings = database.get_user_setting(user)
        
        # Determine current active organization and plan
        org_id = get_current_org_id()
        active_plan = billing.get_effective_plan(org_id)
        plan_config = billing.get_plan_config(active_plan)
        plan_name = plan_config.get("name_th", plan_config.get("name", "Free"))
        
        org_name = "Default Organization"
        try:
            conn = database._get_conn()
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
                org_row = cursor.fetchone()
                if org_row:
                    org_name = org_row["name"]
            finally:
                conn.close()
        except Exception:
            pass

        org_role = session.get("org_role")
        return jsonify({
            "ok": True,
            "user": user,
            "has_org": org_id is not None,
            "org_id": org_id,
            "org_role": org_role,
            "profile": {
                **profile,
                "role": user_settings.get("role"),
                "can_edit_kb": user_settings.get("can_edit_kb", False),
                "is_active": user_settings.get("is_active", 1),
                "active_plan": active_plan,
                "plan_name": plan_name,
                "org_name": org_name
            }
        })
    return jsonify({"ok": False, "error": "Unauthorized"}), 401




@auth_bp.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>")
def reset_password_page(token):
    username = database.validate_reset_token(token)
    return render_template("reset_password.html", valid=bool(username), username=username or "", token=token)


@auth_bp.route("/api/auth/forgot-password", methods=["POST"])
@_limiter.limit("3 per minute; 10 per hour")
def api_forgot_password():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip().lower()
    if not username:
        return jsonify({"ok": False, "error": "กรุณากรอก username"})

    token = database.create_reset_token(username)
    if not token:
        # Don't reveal whether user exists
        return jsonify({"ok": True, "message": "ถ้า username นี้มีในระบบ เราจะส่งลิ้งค์รีเซ็ตไปทาง LINE ค่ะ"})

    base = os.environ.get("BASE_URL", "https://openchat.sbs")
    reset_url = f"{base}/reset-password/{token}"

    # Try to send via LINE DM
    line_user_id = database.get_line_user_id_for_username(username)
    line_sent = False
    if line_user_id:
        try:
            _tok = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
            msg = (
                f"สวัสดีค่ะ คุณได้ขอรีเซ็ตรหัสผ่านสำหรับบัญชี OrgChat AI\n\n"
                f"คลิกลิ้งค์ด้านล่างเพื่อตั้งรหัสผ่านใหม่ (หมดอายุใน 1 ชั่วโมง):\n{reset_url}\n\n"
                f"ถ้าไม่ได้ขอรีเซ็ต ไม่ต้องทำอะไรค่ะ"
            )
            import requests as _req
            _req.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {_tok}"},
                json={"to": line_user_id, "messages": [{"type": "text", "text": msg}]},
                timeout=10,
            )
            line_sent = True
        except Exception as _e:
            logger.warning(f"[ForgotPassword] LINE push failed: {_e}")

    if line_sent:
        return jsonify({"ok": True, "message": "ส่งลิ้งค์รีเซ็ตไปทาง LINE ของคุณแล้วค่ะ กรุณาตรวจสอบข้อความจาก OrgChat AI"})

    # ไม่มี LINE — แจ้ง org admins ของ user ผ่าน LINE แทน เพื่อให้ช่วย reset
    logger.warning(f"[ForgotPassword] No LINE for user '{username}' — notifying org admins. reset_url={reset_url}")
    try:
        _tok = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        user_orgs = database.get_user_orgs(username) or []
        admin_notified = False
        if _tok and user_orgs:
            org_id = user_orgs[0]["id"]
            org_members = database.get_org_members(org_id)
            admin_msg = (
                f"แจ้งเตือนจาก OrgChat AI\n\n"
                f"ผู้ใช้ '{username}' ขอรีเซ็ตรหัสผ่าน แต่ยังไม่ได้ผูก LINE\n\n"
                f"ลิ้งค์รีเซ็ต (ส่งให้ผู้ใช้โดยตรง — หมดอายุ 1 ชม.):\n{reset_url}"
            )
            import requests as _req2
            for m in org_members:
                if m.get("role") == "admin" and m["username"].lower() != username:
                    _lid = database.get_line_user_id_for_username(m["username"])
                    if _lid:
                        try:
                            _req2.post(
                                "https://api.line.me/v2/bot/message/push",
                                headers={"Content-Type": "application/json",
                                         "Authorization": f"Bearer {_tok}"},
                                json={"to": _lid, "messages": [{"type": "text", "text": admin_msg}]},
                                timeout=10,
                            )
                            admin_notified = True
                        except Exception:
                            pass
    except Exception as _e:
        logger.error(f"[ForgotPassword] admin notify failed: {_e}")

    if admin_notified:
        return jsonify({"ok": True, "message": "บัญชีนี้ยังไม่ได้เชื่อม LINE ค่ะ ระบบได้แจ้ง Admin องค์กรของคุณให้ส่งลิ้งค์รีเซ็ตให้แล้ว"})
    return jsonify({"ok": True, "message": "บัญชีนี้ยังไม่ได้เชื่อม LINE ค่ะ กรุณาติดต่อผู้ดูแลระบบเพื่อขอลิ้งค์รีเซ็ตรหัสผ่านค่ะ"})


@auth_bp.route("/api/auth/reset-password", methods=["POST"])
@_limiter.limit("5 per minute")
def api_reset_password():
    data = request.get_json(force=True)
    token    = (data.get("token") or "").strip()
    password = data.get("password") or ""
    if not token or len(password) < 8:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบหรือรหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"})
    ok = database.consume_reset_token(token, password)
    if not ok:
        return jsonify({"ok": False, "error": "ลิ้งค์ไม่ถูกต้องหรือหมดอายุแล้วค่ะ"})
    return jsonify({"ok": True})


@auth_bp.route("/signup")
def signup_page():
    return render_template("signup.html")


@auth_bp.route("/onboarding")
def onboarding_page():
    from datetime import datetime, timedelta, timezone as _tz

    payment_status  = request.args.get("payment")
    plan            = request.args.get("plan")
    sid             = request.args.get("sid", "").strip()
    payment_method  = request.args.get("method", "")   # "promptpay" or ""
    prompt_login    = False   # บอก template ให้แสดง "กรุณา login ใหม่"
    stripe_cs       = None    # เก็บ checkout.Session object ไว้ใช้ซ้ำ

    if payment_status == "success" and plan:
        # ── ตรวจก่อนว่า plan ถูก set แล้วหรือยัง (ลด Stripe API call ซ้ำ) ──────
        _quick_org = session.get("org_id") or _resolve_org_from_url()
        if _quick_org and billing.get_effective_plan(_quick_org) != "free":
            # Webhook set plan แล้ว → ไม่ต้องเรียก Stripe API ซ้ำ
            logger.info(f"[Onboarding] org {_quick_org} plan already active — skipping Stripe verify")
        elif sid and payment.is_configured():
            # ──────────────────────────────────────────────────────────
            # Security: verify กับ Stripe ป้องกัน URL exploit
            # ──────────────────────────────────────────────────────────
            try:
                import stripe as _stripe
                stripe_cs = _stripe.checkout.Session.retrieve(
                    sid, api_key=os.environ.get("STRIPE_SECRET_KEY", "")
                )
                cs_status  = stripe_cs.status
                cs_payment = stripe_cs.payment_status

                if cs_status == "expired":
                    # QR/session หมดอายุ — redirect ไปหน้า billing พร้อม reason
                    return redirect("/billing?reason=session_expired")

                stripe_verified = (cs_payment == "paid" and cs_status == "complete")

                if stripe_verified:
                    # ── หา org_id: session → URL param → Stripe metadata (fallback session หาย) ──
                    org_id = _resolve_org_from_session_or_stripe(stripe_cs)

                    if org_id:
                        # ── ใช้ plan จาก Stripe metadata เท่านั้น — ห้ามเชื่อ URL param ──
                        meta = stripe_cs.metadata or {}
                        target_plan = meta.get("plan", "")
                        if target_plan not in ("pro", "business"):
                            target_plan = None
                        if target_plan:
                            # subscription → ดึง period_end จริงจาก Stripe, PromptPay → 30 วัน
                            subscription_id = getattr(stripe_cs, "subscription", None)
                            expires_at = None
                            if subscription_id:
                                expires_at = payment.get_subscription_period_end(subscription_id)
                            if not expires_at:
                                expires_at = (datetime.now(_tz.utc) + timedelta(days=30)).isoformat()
                            billing.set_org_plan(org_id, target_plan, expires_at)
                            logger.info(f"[Local Sync] Org {org_id} → {target_plan} expires={expires_at} (Stripe-verified redirect fallback)")
                            # restore session org ถ้าหาย
                            if not session.get("org_id"):
                                session["org_id"] = org_id
                                prompt_login = True   # แจ้งให้ login ใหม่เพื่อ refresh context
                    else:
                        logger.warning(f"[Onboarding] Stripe verified but could not resolve org_id (session may have expired)")
                        prompt_login = True
                else:
                    logger.info(f"[Stripe verify] {sid} status={cs_status} payment_status={cs_payment} — webhook will handle")
            except Exception as _se:
                logger.warning(f"[Stripe verify] could not verify session {sid}: {_se}")

    org_id     = get_current_org_id()
    has_org    = org_id is not None
    active_plan = billing.get_effective_plan(org_id)
    plan_config = billing.get_plan_config(active_plan)
    plan_name   = plan_config.get("name", "Free")
    line_bot_id = os.environ.get("LINE_BOT_BASIC_ID", "").strip()
    is_promptpay = (payment_method == "promptpay")
    return render_template(
        "onboarding.html",
        active_plan=active_plan, plan_name=plan_name,
        has_org=has_org, line_bot_id=line_bot_id,
        is_promptpay=is_promptpay,
        prompt_login=prompt_login,
    )


def _resolve_org_from_url():
    """ดึง org_id จาก URL param org_id ถ้ายืนยันได้จาก session user"""
    org_id_param = request.args.get("org_id", "")
    username = session.get("user")
    if not org_id_param or not username:
        return None
    try:
        candidate = int(org_id_param)
        if any(o["id"] == candidate for o in (database.get_user_orgs(username) or [])):
            return candidate
    except Exception:
        pass
    return None


def _resolve_org_from_session_or_stripe(stripe_cs):
    """หา org_id จาก session ก่อน ถ้าไม่มี (session หาย) → fallback Stripe metadata"""
    # 1. session → URL param (มี session)
    username = session.get("user")
    org_id_param = request.args.get("org_id", "")
    if username and org_id_param:
        try:
            candidate = int(org_id_param)
            if any(o["id"] == candidate for o in (database.get_user_orgs(username) or [])):
                return candidate
        except Exception:
            pass

    if session.get("org_id"):
        return session.get("org_id")

    if username:
        orgs = database.get_user_orgs(username)
        if orgs:
            return orgs[0]["id"]

    # 2. Stripe metadata fallback (session หาย — ไม่มี username ใน session)
    try:
        meta_org_id = int(stripe_cs.metadata.get("org_id", 0))
        if meta_org_id and database.get_org_by_id(meta_org_id):
            return meta_org_id
    except Exception:
        pass

    return None


@auth_bp.route("/api/org/create-for-user", methods=["POST"])
@login_required
@_limiter.limit("5 per minute; 10 per hour")
def create_org_for_user():
    """สร้าง org สำหรับ user ที่ login แล้ว (เช่น Google login ที่ยังไม่มี org)"""
    username = session.get("user")
    data = request.get_json(force=True)
    org_name = (data.get("org_name") or "").strip()
    if not org_name:
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อองค์กร"}), 400

    existing = database.get_user_orgs(username)
    if existing:
        session["org_id"] = existing[0]["id"]
        session["org_role"] = existing[0]["role"]
        return jsonify({"ok": True, "org_id": existing[0]["id"], "already_exists": True})

    try:
        org_id, _ = database.create_organization(org_name, username)
    except Exception:
        return jsonify({"ok": False, "error": "ชื่อองค์กรนี้มีอยู่แล้ว กรุณาเปลี่ยนชื่อ"}), 409

    session["org_id"] = org_id
    session["org_role"] = "admin"
    logger.info(f"[OrgCreate] user={username} created org={org_id} name={org_name!r}")
    return jsonify({"ok": True, "org_id": org_id})


@auth_bp.route("/api/org/signup", methods=["POST"])
@_limiter.limit("5 per minute; 20 per hour")
def org_signup():
    data = request.get_json(force=True)
    org_name = data.get("org_name", "").strip()
    display_name = data.get("display_name", "").strip()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    # Reserved usernames — ห้ามใช้เพื่อป้องกันความสับสนกับ system accounts
    _RESERVED = frozenset({
        "admin", "root", "system", "support", "api", "null", "undefined",
        "test", "guest", "owner", "superadmin", "staff", "bot", "service",
        "help", "info", "mail", "billing", "account", "security",
    })

    if not org_name or not username or not password:
        return jsonify({"ok": False, "error": "กรุณากรอกข้อมูลให้ครบถ้วน"}), 400
    if not re.match(r'^[a-z0-9_]{3,30}$', username):
        return jsonify({"ok": False, "error": "username ใช้ได้เฉพาะ a-z, 0-9, _ และต้องมี 3-30 ตัวอักษร"}), 400
    if username in _RESERVED:
        return jsonify({"ok": False, "error": f"ชื่อผู้ใช้ '{username}' ไม่สามารถใช้งานได้ กรุณาเลือกชื่ออื่น"}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "error": "รหัสผ่านไม่ตรงกัน"}), 400
    if len(password) < 8:
        return jsonify({"ok": False, "error": "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"}), 400

    # สร้าง user + org ใน single transaction — ป้องกัน orphan user กรณี DB error
    try:
        org_id, _ = database.signup_create_user_and_org(
            username=username,
            password=password,
            display_name=display_name or username.capitalize(),
            org_name=org_name,
        )
    except ValueError as e:
        if "username_exists" in str(e):
            return jsonify({"ok": False, "error": "ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว"}), 400
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"[Signup] atomic create failed for '{username}': {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสร้างบัญชีได้ กรุณาลองใหม่อีกครั้ง"}), 500

    # Auto-login (session.clear ก่อนเสมอ — ป้องกัน session fixation)
    session.clear()
    session.permanent = True
    session["user"] = username
    session["role"] = "user"
    session["org_id"] = org_id
    session["org_role"] = "admin"

    return jsonify({"ok": True, "user": username, "role": "user", "org_id": org_id})


@auth_bp.route("/api/org/me")
@login_required
def get_current_org():
    user = session.get("user")
    org_id = get_current_org_id()
    org = database.get_org(org_id)
    members = database.get_org_members(org_id)
    return jsonify({
        "ok": True,
        "org": org,
        "members": members,
        "org_role": session.get("org_role", "member")
    })


@auth_bp.route("/api/org/switch/<int:target_org_id>", methods=["POST"])
@login_required
def switch_org(target_org_id):
    user = session.get("user")
    orgs = database.get_user_orgs(user)
    match = next((o for o in orgs if o["id"] == target_org_id), None)
    if not match:
        return jsonify({"ok": False, "error": "คุณไม่ได้เป็นสมาชิกขององค์กรนี้"}), 403
    session["org_id"] = target_org_id
    session["org_role"] = match["role"]
    return jsonify({"ok": True, "org_id": target_org_id, "org_role": match["role"]})


@auth_bp.route("/api/org/members/<username>/role", methods=["POST"])
@login_required
def update_org_member_role(username):
    """Org admin changes another member's role (admin ↔ member)."""
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
    if not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่เปลี่ยนตำแหน่งได้"}), 403
    data = request.get_json(force=True)
    new_role = data.get("role", "").strip()
    if new_role not in ("admin", "member"):
        return jsonify({"ok": False, "error": "ตำแหน่งต้องเป็น admin หรือ member เท่านั้น"}), 400
    if username == me and new_role == "member":
        if database.count_org_admins(org_id) <= 1:
            return jsonify({"ok": False, "error": "ไม่สามารถลดตำแหน่งตัวเองได้ เนื่องจากคุณเป็น Admin คนเดียวในองค์กร"}), 400
    if not database.update_org_member_role(org_id, username, new_role):
        return jsonify({"ok": False, "error": "ไม่พบสมาชิกคนนี้ในองค์กร"}), 404
    if username == me:
        session["org_role"] = new_role
    return jsonify({"ok": True, "username": username, "role": new_role})


@auth_bp.route("/api/org/invite", methods=["POST"])
@login_required
def invite_org_member():
    """Org admin invites an existing user into the organization."""
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
    if not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่เชิญสมาชิกได้"}), 403
    data = request.get_json(force=True)
    invite_username = data.get("username", "").strip().lower()
    role = data.get("role", "member")
    if not invite_username:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อผู้ใช้ที่ต้องการเชิญ"}), 400
    if role not in ("admin", "member"):
        role = "member"
    # Check max_users limit for current plan
    active_plan = billing.get_effective_plan(org_id)
    plan_config = billing.get_plan_config(active_plan)
    max_users = plan_config.get("limits", {}).get("max_users", 1)
    current_count = database.get_org_member_count(org_id)
    if max_users != -1 and current_count >= max_users:
        return jsonify({
            "ok": False,
            "error": f"แผน {active_plan.capitalize()} รองรับสูงสุด {max_users} คน กรุณาอัปเกรดแผนเพื่อเพิ่มสมาชิก"
        }), 403
    # Verify target user exists
    target_settings = database.get_user_setting(invite_username)
    if not target_settings:
        return jsonify({"ok": False, "error": f"ไม่พบผู้ใช้ '{invite_username}' ในระบบ"}), 404
    database.add_org_member(org_id, invite_username, role=role, invited_by=me)
    return jsonify({"ok": True, "username": invite_username, "role": role})


def send_invitation_email(to_email: str, org_name: str, invited_by: str) -> tuple[bool, str]:
    import smtplib
    import os
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    smtp_server = os.environ.get("SMTP_SERVER", "").strip()
    smtp_port = os.environ.get("SMTP_PORT", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    smtp_sender = os.environ.get("SMTP_SENDER", smtp_user).strip()
    base_url = os.environ.get("BASE_URL", "https://openchat.sbs").strip()
    
    if not smtp_server or not smtp_user or not smtp_password:
        logger.warning("SMTP credentials are not configured in environment. Skipping email dispatch.")
        return False, "smtp_not_configured"
        
    try:
        port = int(smtp_port) if smtp_port else 587
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"คุณได้รับเชิญเข้าร่วมองค์กร {org_name} บน OrgChat AI"
        msg["From"] = f"OrgChat AI <{smtp_sender}>"
        msg["To"] = to_email
        
        html_content = f"""
        <html>
        <body style="font-family: 'Sarabun', 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f8fafc; padding: 40px 20px; margin: 0; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #e2e8f0;">
                <div style="background-color: #4f46e5; padding: 30px 40px; text-align: center; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.025em;">OrgChat AI</h2>
                </div>
                <div style="padding: 40px; line-height: 1.6;">
                    <p style="font-size: 16px; margin-top: 0;">สวัสดีครับ,</p>
                    <p style="font-size: 16px;">คุณได้รับเชิญเข้าร่วมองค์กร <strong>{org_name}</strong> โดยคุณ <strong>{invited_by}</strong></p>
                    <p style="font-size: 16px; margin-bottom: 30px;">คุณสามารถเข้าสู่ระบบและเริ่มใช้งานร่วมกับทีมได้ทันทีโดยการลงชื่อเข้าใช้ด้วยบัญชี Google (Gmail) ของคุณผ่านลิงก์ด้านล่างนี้:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{base_url}" style="background-color: #4f46e5; color: #ffffff; padding: 14px 30px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);">
                            เข้าสู่ระบบ OrgChat AI
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #64748b; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                        หากปุ่มด้านบนใช้งานไม่ได้ สามารถคัดลอกลิงก์นี้ไปวางที่เบราว์เซอร์ได้ครับ: <br>
                        <a href="{base_url}" style="color: #4f46e5;">{base_url}</a>
                    </p>
                </div>
                <div style="background-color: #f1f5f9; padding: 20px 40px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                    นี่คืออีเมลอัตโนมัติจากระบบ กรุณาอย่าตอบกลับอีเมลนี้
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))
        
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_server, port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, port, timeout=10)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender, [to_email], msg.as_string())
        server.quit()
        return True, ""
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False, str(e)


@auth_bp.route("/api/org/invite-email", methods=["POST"])
@login_required
def invite_email_org_member():
    """Org admin whitelists a Gmail address and marks it as invited."""
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
    if not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่เชิญสมาชิกได้"}), 403
        
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    role = data.get("role", "member")
    if role not in ("admin", "member"):
        role = "member"
        
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "รูปแบบอีเมลไม่ถูกต้อง"}), 400
        
    # Check max_users limit for current plan
    active_plan = billing.get_effective_plan(org_id)
    plan_config = billing.get_plan_config(active_plan)
    max_users = plan_config.get("limits", {}).get("max_users", 1)
    current_count = database.get_org_member_count(org_id)
    if max_users != -1 and current_count >= max_users:
        return jsonify({
            "ok": False,
            "error": f"แผน {active_plan.capitalize()} รองรับสูงสุด {max_users} คน กรุณาอัปเกรดแผนเพื่อเพิ่มสมาชิก"
        }), 403
        
    # Add to allowed emails (whitelist) with role
    success = database.add_whitelist_email(org_id, email, me, role=role)
    already_exists = False
    if not success:
        # Check if already whitelisted in this organization
        if database.is_email_allowed(org_id, email):
            already_exists = True
            # Gracefully update the role to the newly requested role
            try:
                import sqlite3
                conn = database._get_conn()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE organization_allowed_emails SET role = ?, added_by = ? WHERE organization_id = ? AND email = ?",
                    (role, me, org_id, email)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to update existing whitelist role: {e}")
        else:
            return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการตรวจสอบสถานะ Whitelist ของอีเมลนี้"}), 400
        
    # Automatically ensure whitelist is enabled for this organization
    database.set_whitelist_status(org_id, True)
    
    # Get organization name
    org_name = "Default Organization"
    try:
        import sqlite3
        conn = database._get_conn()
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
            org_row = cursor.fetchone()
            if org_row:
                org_name = org_row["name"]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to resolve org name for org_id={org_id}: {e}")
        
    # Send actual email
    email_sent, email_err = send_invitation_email(email, org_name, me)
    
    if email_sent:
        if already_exists:
            message = f"อีเมล {email} ได้รับอนุมัติสิทธิ์อยู่แล้ว! ระบบทำการอัปเดตบทบาทสิทธิ์เป็น {role} และส่งอีเมลเชิญซ้ำให้เรียบร้อยแล้วครับ! 📧✨"
        else:
            message = f"เพิ่ม {email} เข้า Whitelist และส่งอีเมลเชิญไปยัง Gmail ของเขาเรียบร้อยแล้ว! 📧✨"
    else:
        if email_err == "smtp_not_configured":
            message = f"เพิ่ม {email} เข้า Whitelist สำเร็จ! 🟢 (หมายเหตุ: ระบบไม่ได้ส่งอีเมลจริงเนื่องจากยังไม่ได้ตั้งค่า SMTP ในไฟล์ .env ของเซิร์ฟเวอร์)"
        else:
            message = f"เพิ่ม {email} เข้า Whitelist สำเร็จ! 🟢 (แต่การส่งอีเมลล้มเหลวเนื่องจาก: {email_err})"
            
    return jsonify({
        "ok": True, 
        "email": email, 
        "role": role, 
        "message": message
    })


@auth_bp.route("/api/org/members/<username>/permissions", methods=["PUT"])
@login_required
def update_org_member_permissions(username):
    """Org admin updates feature permissions and profile settings for a member."""
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
    if not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่แก้ไขสิทธิ์ได้"}), 403
    if not database.is_org_member(org_id, username):
        return jsonify({"ok": False, "error": "ไม่พบสมาชิกคนนี้ในองค์กร"}), 404
    data = request.get_json(force=True)
    
    update_kwargs = {}
    if "display_name" in data:
        update_kwargs["display_name"] = data["display_name"]
    if "is_active" in data:
        update_kwargs["is_active"] = bool(data["is_active"])
    if "can_view_kb" in data:
        update_kwargs["can_view_kb"] = bool(data["can_view_kb"])
    if "can_edit_kb" in data:
        update_kwargs["can_edit_kb"] = bool(data["can_edit_kb"])
    if "can_delete_kb" in data:
        update_kwargs["can_delete_kb"] = bool(data["can_delete_kb"])
    if "can_view_financial" in data:
        update_kwargs["can_view_financial"] = bool(data["can_view_financial"])
    if "notes" in data:
        update_kwargs["notes"] = data["notes"]
        
    database.admin_update_user(username, **update_kwargs)
    return jsonify({"ok": True})


@auth_bp.route("/api/org/members/<username>/reset-password", methods=["POST"])
@login_required
def org_member_reset_password(username):
    """Org admin resets a member's password."""
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
    if not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่รีเซ็ตรหัสผ่านได้"}), 403
    if not database.is_org_member(org_id, username):
        return jsonify({"ok": False, "error": "ไม่พบสมาชิกคนนี้ในองค์กร"}), 404
    
    data = request.get_json(force=True)
    password = data.get("password")
    if not password:
        return jsonify({"ok": False, "error": "กรุณากรอกรหัสผ่านใหม่"}), 400
        
    database.admin_reset_user_password(username, password)
    database.log_event(f"Org admin reset password for member: {username}", user=me, org_id=org_id)
    return jsonify({"ok": True})


@auth_bp.route("/api/org/members/<username>", methods=["DELETE"])
@login_required
def remove_org_member(username):
    """Org admin removes a member from the organization and completely purges their account."""
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
    if not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่ลบสมาชิกได้"}), 403
    if username.lower() == me.lower():
        return jsonify({"ok": False, "error": "ไม่สามารถลบตัวเองออกจากองค์กรได้"}), 400
    
    # Security check: Ensure user is a member of the admin's organization
    if not database.is_org_member(org_id, username):
        return jsonify({"ok": False, "error": "ไม่พบสมาชิกคนนี้ในองค์กร"}), 404
        
    # Purge user account across all tables
    if not database.admin_delete_user_complete(username):
        return jsonify({"ok": False, "error": "ไม่สามารถลบสมาชิกคนนี้ได้"}), 500
        
    database.log_event(f"Org admin completely deleted member account: {username}", user=me, org_id=org_id)
    return jsonify({"ok": True, "username": username})


@auth_bp.route("/api/org/profile", methods=["GET"])
@login_required
def get_org_profile_api():
    """Retrieve the business profile details for the current organization."""
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
        
    profile = database.get_org_profile(org_id)
    if not profile:
        profile = {}
    return jsonify({"ok": True, "profile": profile})


@auth_bp.route("/api/org/profile", methods=["POST"])
@login_required
def update_org_profile_api():
    """Update the business profile details for the current organization."""
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "คุณยังไม่ได้อยู่ในองค์กร"}), 403
    if not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่สามารถแก้ไขข้อมูลธุรกิจได้"}), 403
        
    data = request.get_json() or {}
    # Validation: some fields are required according to screenshots: ประเภทธุรกิจ, สถานะการจด VAT, ประเภทสาขา, ชื่อธุรกิจภาษาไทย, เบอร์โทรติดต่อ
    required_fields = ["business_type", "vat_status", "branch_type", "business_name_th", "phone"]
    for f in required_fields:
        if not data.get(f):
            return jsonify({"ok": False, "error": "กรุณากรอกข้อมูลในช่องที่จำเป็น (*) ให้ครบถ้วน"}), 400
            
    if database.update_org_profile(org_id, data):
        database.log_event(f"Updated business profile for org_id: {org_id}", user=me, org_id=org_id)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่สามารถบันทึกข้อมูลธุรกิจได้ กรุณาลองใหม่"}), 500


@auth_bp.route("/api/profile", methods=["GET"])
@login_required
def get_my_profile():
    username = session.get("user")
    profile = database.get_user_profile(username)
    if profile:
        org_id = get_current_org_id()
        active_plan = billing.get_effective_plan(org_id)
        plan_config = billing.get_plan_config(active_plan)
        plan_name = plan_config.get("name_th", plan_config.get("name", "Free"))
        
        org_name = "Default Organization"
        try:
            conn = database._get_conn()
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
                org_row = cursor.fetchone()
                if org_row:
                    org_name = org_row["name"]
            finally:
                conn.close()
        except Exception:
            pass
            
        profile["active_plan"] = active_plan
        profile["plan_name"] = plan_name
        profile["org_name"] = org_name
        profile["org_role"] = session.get("org_role", "member")
        
        # Dynamic database verification to guarantee correct role
        if org_id:
            is_admin_check = database.is_org_admin(org_id, username)
            profile["org_role"] = "admin" if is_admin_check else "member"
            
        settings = database.get_user_setting(username)
        profile["role"] = settings.get("role", "user")
        
    return jsonify({"ok": True, "profile": profile})


@auth_bp.route("/api/profile/update", methods=["POST"])
@login_required
def update_my_profile():
    username = session.get("user")
    
    # Handle multipart form (avatar file upload) or JSON
    display_name = None
    avatar_url = None
    background_url = None
    department = None

    if request.content_type and 'multipart/form-data' in request.content_type:
        display_name = request.form.get("display_name")
        background_url = request.form.get("background_url")
        department = request.form.get("department")

        # Handle avatar file upload
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            ext = Path(secure_filename(avatar_file.filename)).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                return jsonify({"ok": False, "error": "รองรับเฉพาะไฟล์รูป (.jpg, .png, .webp, .gif)"}), 400
            avatar_filename = f"avatar_{username}_{int(time.time())}{ext}"
            upload_dir = Path("uploads") / "profiles"
            upload_dir.mkdir(parents=True, exist_ok=True)
            avatar_file.save(str(upload_dir / avatar_filename))
            avatar_url = f"/uploads/profiles/{avatar_filename}"
    else:
        data = request.get_json(force=True)
        display_name = data.get("display_name")
        avatar_url = data.get("avatar_url")
        background_url = data.get("background_url")
        department = data.get("department")

    database.update_user_profile(username, display_name=display_name, avatar_url=avatar_url, background_url=background_url, department=department)
    profile = database.get_user_profile(username)
    database.log_event(f"Profile updated by {username}", user=username, org_id=get_current_org_id())
    return jsonify({"ok": True, "profile": profile})


@auth_bp.route("/api/user/my-settings", methods=["GET"])
@login_required
def get_my_settings():
    """Return current user's settings (role, permissions, notes) — read for self."""
    username = session.get("user")
    settings = database.get_user_setting(username)
    profile = database.get_user_profile(username) or {}
    return jsonify({
        "ok": True,
        "username": username,
        "display_name": profile.get("display_name") or username,
        "avatar_url": profile.get("avatar_url") or "",
        "department": profile.get("department") or "",
        "position": profile.get("position") or "",
        "role": settings.get("role", "user"),
        "is_active": bool(settings.get("is_active", 1)),
        "notes": settings.get("notes") or "",
        "can_view_kb": bool(settings.get("can_view_kb")),
        "can_edit_kb": bool(settings.get("can_edit_kb")),
        "can_delete_kb": bool(settings.get("can_delete_kb")),
        "can_view_financial": bool(settings.get("can_view_financial")),
    })


@auth_bp.route("/api/user/update-notes", methods=["POST"])
@login_required
def update_my_notes():
    """User updates their own notes field."""
    username = session.get("user")
    data = request.get_json(force=True)
    notes = data.get("notes", "")
    database.admin_update_user(username, notes=notes)
    return jsonify({"ok": True})


@auth_bp.route("/api/user/change-password", methods=["POST"])
@login_required
def change_my_password():
    """User changes their own password. Requires current password to verify."""
    username = session.get("user")
    data = request.get_json(force=True)
    current_pw = (data.get("current_password") or "").strip()
    new_pw = (data.get("new_password") or "").strip()
    if not new_pw or len(new_pw) < 4:
        return jsonify({"ok": False, "error": "รหัสผ่านใหม่ต้องมีอย่างน้อย 4 ตัวอักษร"}), 400
    # Verify current password
    settings = database.get_user_setting(username)
    stored_hash = settings.get("custom_password") or ""
    import bcrypt
    if stored_hash:
        try:
            ok = bcrypt.checkpw(current_pw.encode(), stored_hash.encode() if isinstance(stored_hash, str) else stored_hash)
        except Exception:
            ok = False
        if not ok:
            return jsonify({"ok": False, "error": "รหัสผ่านปัจจุบันไม่ถูกต้อง"}), 400
    else:
        # No custom password set yet — allow if user provides their Google/default login (skip verify)
        pass
    database.admin_reset_user_password(username, new_pw)
    database.log_event(f"Password changed by user {username}", user=username, org_id=get_current_org_id())
    return jsonify({"ok": True})

