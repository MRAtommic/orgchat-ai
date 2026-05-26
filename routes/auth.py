# -*- coding: utf-8 -*-
"""
Authentication Blueprint — Login, Logout, OAuth2, QR Login, LINE Magic Link, Password Reset, Org Signup
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, send_from_directory, send_file, abort, redirect, session
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
        if user_role != "admin":
            return jsonify({"ok": False, "error": "เฉพาะ Admin เท่านั้นที่เชื่อมต่อ Google ระดับบริษัทได้"}), 403
        org_id = session.get("org_id", 1)
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
        return jsonify({"ok": False, "error": str(e)}), 500


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
        return f"<h1>Google ปฏิเสธการเชื่อมต่อ</h1><p>{error}</p><p><a href='/'>กลับหน้าหลัก</a></p>", 400

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
            <style>{_CSS}</style></head>
            <body style="background:linear-gradient(135deg,#667eea,#764ba2)">
            <div class="card">
              <div style="font-size:48px">✅</div>
              <h1 style="color:#059669">เชื่อมต่อ Google สำเร็จ!</h1>
              <span class="badge">ระดับ: {{{{ scope }}}}</span>
              <br><div class="email">{{{{ email }}}}</div>
              <p style="color:#475569">ระบบสร้าง Google Sheets และโฟลเดอร์ Drive เรียบร้อยแล้ว</p>
              <a href="/" class="btn">กลับหน้าหลัก</a>
            </div></body></html>""", email=google_email, scope=scope_label)
        else:
            return render_template_string(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>เชื่อมต่อ (บางส่วน)</title>
            <style>{_CSS}</style></head>
            <body style="background:linear-gradient(135deg,#f59e0b,#ef4444)">
            <div class="card">
              <h1 style="color:#D97706">⚠️ เชื่อมต่อสำเร็จ แต่สร้าง Workspace ไม่สมบูรณ์</h1>
              <span class="badge">ระดับ: {{{{ scope }}}}</span>
              <p style="color:#475569">บัญชีเชื่อมต่อแล้ว แต่สร้าง Sheets/Drive ไม่สำเร็จ ลองยกเลิกแล้วเชื่อมต่อใหม่</p>
              <a href="/" class="btn">กลับหน้าหลัก</a>
            </div></body></html>""", scope=scope_label)

    except Exception as e:
        logger.error(f"OAuth2 callback error: {e}")
        return f"<h1>เกิดข้อผิดพลาด</h1><p>{e}</p><p><a href='/'>กลับหน้าหลัก</a></p>", 500


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
    if not token or token not in PENDING_LINE_LINKS:
        return render_link_error("โทเค็นสำหรับผูกบัญชีไม่ถูกต้องหรือหมดอายุแล้วค่ะ"), 400
        
    link_data = PENDING_LINE_LINKS[token]
    # Check expiry (10 minutes = 600 seconds)
    if time.time() - link_data.get("timestamp", 0) > 600:
        del PENDING_LINE_LINKS[token]
        return render_link_error("โทเค็นสำหรับผูกบัญชีหมดอายุแล้วค่ะ กรุณาขอลิงก์ใหม่ใน LINE Bot อีกครั้งนะคะ"), 400
        
    line_user_id = link_data["line_user_id"]
    
    if request.method == 'GET':
        # If user is already logged in, auto-link
        username = session.get("user")
        if username:
            database.link_line_user(username, line_user_id)
            del PENDING_LINE_LINKS[token]
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
        elif username_lower in USERS and USERS[username_lower] == password:
            if not settings.get("is_active", 1):
                return render_login_page(token, error="บัญชีผู้ใช้ของคุณถูกระงับการใช้งานชั่วคราวค่ะ")
            resolved_username = username_raw.capitalize()
            authenticated = True
            
        if authenticated:
            session.permanent = True
            session["user"] = resolved_username
            database.link_line_user(resolved_username, line_user_id)
            del PENDING_LINE_LINKS[token]
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
    
    # 1. Check Database first (Dynamic Users) — supports bcrypt hashed passwords
    settings = database.get_user_setting(username_raw)
    
    if settings.get("custom_password") and database.check_password(password, settings["custom_password"]):
        if not settings.get("is_active", 1):
            return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403
        session.permanent = True
        session["user"] = settings.get("username_original", username_raw)
        session["role"] = settings.get("role", "user")  # ← ใช้สำหรับ feature gate ระดับ system
        _set_session_org(session["user"])
        return jsonify({"ok": True, "user": session["user"], "role": session["role"], "org_role": session.get("org_role", "member")})

    # 2. Fallback to Hardcoded (plain text)
    if username_lower in USERS and USERS[username_lower] == password:
        user_to_session = username_raw.capitalize()
        if not settings.get("is_active", 1):
             return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับโดยผู้ดูแลระบบ"}), 403
        session.permanent = True
        session["user"] = user_to_session
        session["role"] = settings.get("role", "admin") if username_lower == "admin" else settings.get("role", "user")
        _set_session_org(user_to_session)
        return jsonify({"ok": True, "user": user_to_session, "role": session["role"], "org_role": session.get("org_role", "member")})

    return jsonify({"ok": False, "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"})


@auth_bp.route("/api/qr/generate", methods=["POST"])
@_limiter.limit("10 per minute; 30 per hour")
def qr_generate():
    """Generate a unique QR login token for desktop."""
    token = str(uuid.uuid4())
    _qr_tokens[token] = {
        "status": "pending",
        "user": None,
        "created": time.time()
    }
    # Cleanup old tokens (> 5 min) — snapshot first to avoid dict-changed-during-iteration
    cutoff = time.time() - 300
    live = {k: v for k, v in list(_qr_tokens.items()) if v["created"] >= cutoff}
    _qr_tokens.clear()
    _qr_tokens.update(live)
    
    return jsonify({"ok": True, "token": token})


@auth_bp.route("/api/qr/poll/<token>")
@_limiter.limit("60 per minute")
def qr_poll(token):
    """Desktop polls this to check if QR was scanned and approved."""
    entry = _qr_tokens.get(token)
    if not entry:
        return jsonify({"ok": False, "error": "Token expired or invalid"}), 404
    
    # Check expiry (5 min)
    if time.time() - entry["created"] > 300:
        del _qr_tokens[token]
        return jsonify({"ok": False, "error": "Token expired"}), 410
    
    if entry["status"] == "approved" and entry["user"]:
        user = entry["user"]
        del _qr_tokens[token]
        # Log user in
        session.permanent = True
        session["user"] = user
        _u_settings = database.get_user_setting(user)
        session["role"] = _u_settings.get("role", "user")
        _set_session_org(user)
        return jsonify({"ok": True, "status": "approved", "user": user, "role": session["role"], "org_role": session.get("org_role", "member")})
    
    return jsonify({"ok": True, "status": "pending"})


@auth_bp.route("/api/qr/approve/<token>", methods=["POST"])
@login_required
def qr_approve(token):
    """Mobile user (already logged in) approves a QR login token."""
    entry = _qr_tokens.get(token)
    if not entry:
        return jsonify({"ok": False, "error": "Token ไม่ถูกต้องหรือหมดอายุ"}), 404
    
    if time.time() - entry["created"] > 300:
        del _qr_tokens[token]
        return jsonify({"ok": False, "error": "Token หมดอายุแล้ว"}), 410
    
    user = session.get("user")
    entry["status"] = "approved"
    entry["user"] = user
    return jsonify({"ok": True, "message": f"อนุมัติเข้าสู่ระบบสำหรับ {user} เรียบร้อย"})


@auth_bp.route("/qr-login/<token>")
def qr_login_page(token):
    """Page that mobile opens after scanning QR code."""
    entry = _qr_tokens.get(token)
    if not entry:
        return render_template_string(QR_APPROVE_HTML, token=token, error="Token ไม่ถูกต้องหรือหมดอายุ", valid=False)
    if time.time() - entry["created"] > 300:
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
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)

        # Token is valid, get the user's email
        email = idinfo.get("email")
        if not email:
            return jsonify({"ok": False, "error": "ไม่พบอีเมลจาก Google Account"}), 400
            
        username = email.split('@')[0]
        
        # --- Whitelist Check ---
        user_orgs = database.get_user_orgs(username)
        target_org_id = user_orgs[0]["id"] if user_orgs else 1
        
        if database.is_whitelist_enabled(target_org_id):
            if not database.is_org_admin(target_org_id, username) and not database.is_email_allowed(target_org_id, email):
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

        session.permanent = True
        session["user"] = username
        _set_session_org(username)
        return jsonify({"ok": True, "user": username, "org_role": session.get("org_role", "member")})

    except Exception as e:
        print(f"Google Login Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


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
            import sqlite3
            conn = sqlite3.connect("chat_history.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
            org_row = cursor.fetchone()
            if org_row:
                org_name = org_row["name"]
            conn.close()
        except Exception:
            pass

        return jsonify({
            "ok": True, 
            "user": user, 
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


@auth_bp.route("/api/profile/update", methods=["POST"])
@login_required
def api_update_profile():
    user = session.get("user")
    display_name = request.form.get("display_name")
    background_url = request.form.get("background_url")
    department = request.form.get("department")
    
    avatar_url = None
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename:
            ext = Path(secure_filename(file.filename)).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                return jsonify({"ok": False, "error": "รองรับเฉพาะไฟล์รูป (.jpg, .png, .webp, .gif)"}), 400
            prof_dir = Path("uploads/profiles")
            prof_dir.mkdir(parents=True, exist_ok=True)
            filename = secure_filename(f"{user}_{file.filename}")
            save_path = prof_dir / filename
            file.save(str(save_path))
            avatar_url = f"/uploads/profiles/{filename}"
            
    database.update_user_profile(user, display_name=display_name, avatar_url=avatar_url, background_url=background_url, department=department)
    database.log_event(f"Profile updated for {user}", user=user)
    return jsonify({"ok": True, "profile": database.get_user_profile(user)})


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
    else:
        logger.info(f"[ForgotPassword] No LINE for user '{username}' — reset URL logged server-side only.")
        return jsonify({"ok": True, "message": "บัญชีนี้ยังไม่ได้เชื่อม LINE ค่ะ กรุณาติดต่อ Admin เพื่อรีเซ็ตรหัสผ่านให้ค่ะ"})


@auth_bp.route("/api/auth/reset-password", methods=["POST"])
@_limiter.limit("5 per minute")
def api_reset_password():
    data = request.get_json(force=True)
    token    = (data.get("token") or "").strip()
    password = data.get("password") or ""
    if not token or len(password) < 6:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบหรือรหัสผ่านสั้นเกินไป"})
    ok = database.consume_reset_token(token, password)
    if not ok:
        return jsonify({"ok": False, "error": "ลิ้งค์ไม่ถูกต้องหรือหมดอายุแล้วค่ะ"})
    return jsonify({"ok": True})


@auth_bp.route("/signup")
def signup_page():
    return render_template("signup.html")


@auth_bp.route("/onboarding")
def onboarding_page():
    payment_status = request.args.get("payment")
    plan = request.args.get("plan")
    if payment_status == "success" and plan:
        org_id_param = request.args.get("org_id")
        org_id = None
        _ob_username = session.get("user")
        if org_id_param and _ob_username:
            try:
                _candidate = int(org_id_param)
                _user_orgs = database.get_user_orgs(_ob_username)
                if any(o["id"] == _candidate for o in (_user_orgs or [])):
                    org_id = _candidate
            except Exception:
                pass
        if not org_id:
            org_id = session.get("org_id")
        if not org_id:
            username = session.get("user")
            if username:
                try:
                    orgs = database.get_user_orgs(username)
                    if orgs:
                        org_id = orgs[0]["id"]
                except Exception:
                    pass
        if org_id:
            try:
                target_plan = "pro" if plan == "pro" else plan
                if target_plan in ("pro", "business"):
                    from datetime import datetime, timedelta, timezone
                    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                    billing.set_org_plan(org_id, target_plan, expires_at)
                    logger.info(f"[Local Sync] Successfully updated Org {org_id} to plan {target_plan} via redirect fallback.")
            except Exception as e:
                logger.error(f"[Local Sync] Failed to update plan via redirect fallback: {e}")
    org_id = get_current_org_id()
    active_plan = billing.get_effective_plan(org_id)
    plan_config = billing.get_plan_config(active_plan)
    plan_name = plan_config.get("name", "Free")
    return render_template("onboarding.html", active_plan=active_plan, plan_name=plan_name)


@auth_bp.route("/api/org/signup", methods=["POST"])
@_limiter.limit("5 per minute; 20 per hour")
def org_signup():
    data = request.get_json(force=True)
    org_name = data.get("org_name", "").strip()
    display_name = data.get("display_name", "").strip()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not org_name or not username or not password:
        return jsonify({"ok": False, "error": "กรุณากรอกข้อมูลให้ครบถ้วน"}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "error": "รหัสผ่านไม่ตรงกัน"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"}), 400

    # Create admin user first (org needs owner_username)
    try:
        success = database.admin_create_user(
            username=username,
            password=password,
            role="admin",
            display_name=display_name or username.capitalize(),
            can_view_kb=True,
            can_edit_kb=True,
            can_delete_kb=True
        )
        if not success:
            return jsonify({"ok": False, "error": "ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"ไม่สามารถสร้างบัญชีผู้ใช้: {e}"}), 500

    # Create organization (returns tuple: org_id, slug)
    try:
        org_id, _ = database.create_organization(org_name, username)
    except Exception as e:
        return jsonify({"ok": False, "error": f"ชื่อองค์กรนี้มีอยู่แล้ว: {e}"}), 409

    # Auto-login
    session.permanent = True
    session["user"] = username
    session["role"] = "admin"
    session["org_id"] = org_id
    session["org_role"] = "admin"

    return jsonify({"ok": True, "user": username, "role": "admin", "org_id": org_id})


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
            import sqlite3
            conn = sqlite3.connect("chat_history.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
            org_row = cursor.fetchone()
            if org_row:
                org_name = org_row["name"]
            conn.close()
        except Exception:
            pass
            
        profile["active_plan"] = active_plan
        profile["plan_name"] = plan_name
        profile["org_name"] = org_name
        
    return jsonify({"ok": True, "profile": profile})


@auth_bp.route("/api/profile/update", methods=["POST"])
@login_required
def update_my_profile():
    username = session.get("user")
    
    # Handle multipart form (avatar file upload) or JSON
    display_name = None
    avatar_url = None
    department = None
    
    if request.content_type and 'multipart/form-data' in request.content_type:
        display_name = request.form.get("display_name")
        department = request.form.get("department")
        
        # Handle avatar file upload
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
            avatar_filename = f"avatar_{username}_{int(time.time())}.{ext}"
            upload_dir = os.path.join("static", "uploads", "avatars")
            os.makedirs(upload_dir, exist_ok=True)
            avatar_path = os.path.join(upload_dir, avatar_filename)
            avatar_file.save(avatar_path)
            avatar_url = f"/static/uploads/avatars/{avatar_filename}"
    else:
        data = request.get_json(force=True)
        display_name = data.get("display_name")
        avatar_url = data.get("avatar_url") 
        department = data.get("department")
    
    database.update_user_profile(username, display_name=display_name, avatar_url=avatar_url, department=department)
    profile = database.get_user_profile(username)
    database.log_event(f"Profile updated by {username}", username)
    return jsonify({"ok": True, "profile": profile})

