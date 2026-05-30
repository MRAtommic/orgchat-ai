# -*- coding: utf-8 -*-
"""
Admin Blueprint — Admin Dashboard, User Management, Settings, Whitelist,
Superadmin Panel, Leave/Lunch, Schedules, Billing, LINE Group Management,
Expense Form, Reconciliation
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, send_from_directory, send_file, abort, redirect, session
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
import google_drive_service
from task_tracker import db_task_tracker
from reconciliation_service import ReconciliationService
import settings_manager

from routes.shared import (
    VERSION, socketio, _limiter, login_required, admin_required, superadmin_required, org_admin_required,
    PENDING_LINE_LINKS, _OAUTH_STATES, _store_oauth_state, _pop_oauth_state,
    send_push_notification, batch_send_push_notification,
    get_weather_context, THAI_HOLIDAYS_2026, get_current_time,
    _APP_START_TIME,
    VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS,
    OAUTH2_AVAILABLE, oauth2_service,
    _set_session_org, get_current_org_id,
    _get_gemini_api_key, _configure_gemini,
    can_edit_knowledge_base, can_view_knowledge_base, can_delete_knowledge_base,
    is_admin, get_rag_filter,
    safe_thread_target, validate_uploaded_file,
    ALLOWED_EXTENSIONS,
    USERS,
)

logger = logging.getLogger("OrgChatAI.Admin")

admin_bp = Blueprint('admin', __name__)

_recon_cache: dict = {}
_recon_lock = threading.Lock()

@admin_bp.route("/api/admin/line/settings", methods=["GET", "POST"])
@admin_required
def admin_line_settings():
    if request.method == "POST":
        data = request.json
        config = get_line_config()
        config.update(data)
        save_line_config(config)
        return jsonify({"ok": True, "message": "บันทึกการตั้งค่า LINE เรียบร้อยแล้วค่ะ"})
    return jsonify({"ok": True, "config": get_line_config()})


@admin_bp.route("/api/org/line/register-group", methods=["POST"])
@org_admin_required
def register_line_group_api():
    data = request.get_json(force=True) or {}
    group_id = (data.get("group_id") or "").strip()
    group_name = (data.get("group_name") or "").strip()
    if not group_id:
        return jsonify({"ok": False, "error": "กรุณาระบุ Group ID"}), 400
    org_id = get_current_org_id()
    username = session.get("user")
    database.register_line_group(group_id, org_id, username, group_name or None)
    return jsonify({"ok": True, "group_id": group_id, "org_id": org_id})


@admin_bp.route("/api/org/line/groups", methods=["GET"])
@org_admin_required
def list_line_groups_api():
    org_id = get_current_org_id()
    groups = database.get_line_groups_for_org(org_id)
    return jsonify({"ok": True, "groups": groups})


@admin_bp.route("/api/org/line/sync-group-names", methods=["POST"])
@org_admin_required
def sync_line_group_names():
    """Call LINE getGroupSummary API for each registered group and save real name + picture."""
    import requests as _req
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "ไม่พบองค์กร"}), 400
    config = database.get_line_config()
    token = config.get("channel_access_token", "")
    if not token:
        return jsonify({"ok": False, "error": "ยังไม่ได้ตั้งค่า LINE Channel Access Token ในแผงควบคุม"}), 400
    groups = database.get_line_groups_for_org(org_id)
    results = []
    for g in groups:
        gid = g["group_id"]
        try:
            r = _req.get(
                f"https://api.line.me/v2/bot/group/{gid}/summary",
                headers={"Authorization": f"Bearer {token}"},
                timeout=8
            )
            if r.status_code == 200:
                info = r.json()
                real_name = info.get("groupName", "")
                picture_url = info.get("pictureUrl", "")
                database.update_line_group_real_info(gid, real_name, picture_url)
                results.append({"group_id": gid, "real_name": real_name, "picture_url": picture_url, "ok": True})
            elif r.status_code == 404:
                results.append({"group_id": gid, "ok": False, "error": "ไม่พบกลุ่มนี้ใน LINE (บอทอาจถูกลบออกจากกลุ่มแล้ว)"})
            else:
                results.append({"group_id": gid, "ok": False, "error": f"LINE API ตอบกลับ {r.status_code}"})
        except Exception as e:
            logger.error(f"[LINE group sync] {gid}: {e}")
            results.append({"group_id": gid, "ok": False, "error": "เกิดข้อผิดพลาดในการติดต่อ LINE API"})
    return jsonify({"ok": True, "results": results})


@admin_bp.route("/api/org/line/groups/<group_id>", methods=["DELETE"])
@org_admin_required
def delete_line_group_api(group_id):
    org_id = get_current_org_id()
    conn = database._get_conn()
    try:
        conn.execute("DELETE FROM line_group_mappings WHERE group_id=? AND org_id=?", (group_id, org_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@admin_bp.route("/admin/line-groups")
@login_required
def admin_line_groups_page():
    user = session.get("user")
    org_id = get_current_org_id()
    settings = database.get_user_setting(user)
    
    is_global_admin = settings.get("role") == "admin"
    is_organization_admin = org_id and database.is_org_admin(org_id, user)
    
    if not is_global_admin and not is_organization_admin:
        return redirect("/?error=permission_denied"), 403
    line_bot_id = os.environ.get("LINE_BOT_BASIC_ID", "").strip()
    return render_template("admin_line_groups.html", line_bot_id=line_bot_id)


@admin_bp.route("/api/admin/line/broadcast-history")
@admin_required
def get_broadcast_history():
    """Retrieve filtered broadcast history for the current org."""
    try:
        org_id = get_current_org_id()
        if not org_id:
            return jsonify({"ok": False, "error": "ไม่พบข้อมูลองค์กร"}), 404
            
        history = database.get_line_broadcast_history(org_id, limit=50)
        return jsonify({"ok": True, "history": history})
    except Exception as e:
        logger.error(f"[LINE broadcast history] {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถดึงประวัติการประกาศได้"})


@admin_bp.route("/api/admin/line/broadcast", methods=["POST"])
@admin_required
def api_line_broadcast():
    data = request.json
    text = data.get("text", "").strip()
    user = session.get("user", "Unknown")
    org_id = get_current_org_id()
    
    if not text:
        return jsonify({"success": False, "error": "กรุณาระบุข้อความประกาศค่ะ"}), 400
    
    def run_broadcast():
        success = broadcast_line_announcement(title="ประกาศจากแอดมิน", text=text)
        status = "success" if success else "failed"
        database.save_line_broadcast(user, org_id, text, status)
        logger.info(f"Broadcast from {user} (Org: {org_id}): {text} - {status}")
        
    threading.Thread(target=run_broadcast).start()
    return jsonify({"success": True, "message": "กำลังส่งประกาศในพื้นหลังค่ะพี่!"})


@admin_bp.route("/billing")
@login_required
def billing_page():
    params = request.query_string.decode("utf-8")
    target = "/?view=plan"
    if params:
        target += f"&{params}"
    return redirect(target)


@admin_bp.route("/api/billing/status")
@login_required
def billing_status():
    org_id = get_current_org_id()
    status = billing.get_billing_status(org_id)

    # Enrich with actual live counts (not stored in billing module to avoid circular deps)
    kb_used = 0
    members_used = 0
    if org_id:
        try:
            kb_used = len([f for f in rag_engine.list_files() if f.get("organization_id", 1) == org_id])
        except Exception:
            pass
        try:
            members_used = len(database.get_org_members(org_id))
        except Exception:
            pass

    status["usage"]["kb_files"] = {
        "used":  kb_used,
        "limit": status["usage"]["kb_files"],
    }
    status["usage"]["max_users"] = {
        "used":  members_used,
        "limit": status["usage"]["max_users"],
    }

    # คำนวณ downgrade warnings — แจ้ง user ล่วงหน้าถ้า downgrade จะทำให้เกิน limit
    downgrade_warnings = []
    current_plan = status.get("plan", "free")
    if current_plan != "free":
        free_limits = billing.get_plan_config("free")["limits"]
        usage = status.get("usage", {})
        ai_used  = usage.get("ai_queries", {}).get("used", 0)
        exp_used = usage.get("expenses", {}).get("used", 0)
        if ai_used > free_limits["ai_queries_per_month"]:
            downgrade_warnings.append(f"AI queries: ใช้ไป {ai_used} ครั้ง (Free limit: {free_limits['ai_queries_per_month']})")
        if exp_used > free_limits["expenses_per_month"]:
            downgrade_warnings.append(f"รายจ่าย: บันทึกไป {exp_used} รายการ (Free limit: {free_limits['expenses_per_month']})")
        if members_used > free_limits["max_users"]:
            downgrade_warnings.append(f"สมาชิก: มี {members_used} คน (Free limit: {free_limits['max_users']} คน)")
        if kb_used > free_limits["kb_files"]:
            downgrade_warnings.append(f"ไฟล์ KB: มี {kb_used} ไฟล์ (Free limit: {free_limits['kb_files']} ไฟล์)")

    # is_paid — PromptPay polling ใน onboarding.html ใช้ field นี้
    return jsonify({
        "ok": True,
        "is_paid": status.get("plan", "free") != "free",
        "downgrade_warnings": downgrade_warnings,
        **status,
    })


@admin_bp.route("/plan")
@login_required
def plan_page():
    params = request.query_string.decode("utf-8")
    target = "/?view=plan"
    if params:
        target += f"&{params}"
    return redirect(target)


@admin_bp.route("/admin/customers")
@login_required
@superadmin_required
def admin_customers_page():
    return render_template("admin_customers.html")


@admin_bp.route("/api/admin/orgs")
@login_required
@superadmin_required
def admin_list_orgs():
    orgs = database.get_all_orgs_with_stats()
    for o in orgs:
        o["plan_config"] = billing.get_plan_config(o["plan"])
    return jsonify({"ok": True, "orgs": orgs})


@admin_bp.route("/api/admin/billing/set-plan", methods=["POST"])
@login_required
@superadmin_required
def admin_set_plan():
    data = request.get_json()
    org_id   = int(data.get("org_id", get_current_org_id()))
    plan     = data.get("plan", "free")
    expires  = data.get("expires_at")   # ISO string or null
    try:
        billing.set_org_plan(org_id, plan, expires)
        return jsonify({"ok": True, "plan": plan})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@admin_bp.route("/api/billing/checkout", methods=["POST"])
@admin_bp.route("/api/b/c", methods=["POST"])
@login_required
def billing_checkout():
    """Create a Stripe Checkout Session and return its URL."""
    if not payment.is_configured():
        return jsonify({"ok": False, "error": "ระบบชำระเงินยังไม่พร้อม กรุณาติดต่อทีมงาน"}), 503

    data = request.get_json()
    plan = data.get("plan", "pro")
    if plan not in ("pro", "business"):
        return jsonify({"ok": False, "error": "ไม่รู้จัก plan นี้"}), 400

    username = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        try:
            org_name = f"องค์กรของ {username}"
            org_id, slug = database.create_organization(org_name, username)
            session["org_id"] = org_id
            session["org_role"] = "admin"
            logger.info(f"[Checkout Auto-Org] Created org {org_name} (id={org_id}) for user {username}")
        except Exception as e:
            logger.error(f"[Checkout Auto-Org] Failed to create org: {e}")
            return jsonify({"ok": False, "error": "ไม่สามารถสร้างบัญชีองค์กรอัตโนมัติได้ กรุณาลองใหม่"}), 500

    stripe_info = database.get_org_stripe_info(org_id)

    # Double-payment guard — ถ้ามี active subscription อยู่แล้ว → เปิด portal แทน
    if stripe_info.get("subscription_id"):
        current_plan = billing.get_effective_plan(org_id)
        if current_plan != "free":
            return jsonify({
                "ok": False,
                "error": "คุณมี subscription ที่ active อยู่แล้ว กรุณาจัดการผ่านหน้า billing",
                "redirect": "/billing",
            }), 409

    base = os.environ.get("BASE_URL", "").rstrip("/") or request.host_url.rstrip("/")

    try:
        checkout_session = payment.create_checkout_session(
            org_id=org_id,
            plan=plan,
            customer_id=stripe_info.get("customer_id"),
            success_url=f"{base}/onboarding?plan={plan}&payment=success&org_id={org_id}&sid={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/pricing?cancelled=1",   # BS-3: หน้า public ไม่ต้อง login
        )
        return jsonify({"ok": True, "url": checkout_session.url})
    except Exception as e:
        logger.error(f"[Stripe] checkout error: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสร้างช่องทางชำระเงินได้ กรุณาลองใหม่"}), 500


@admin_bp.route("/api/billing/checkout-promptpay", methods=["POST"])
@admin_bp.route("/api/b/cp", methods=["POST"])
@login_required
def billing_checkout_promptpay():
    """Create a Stripe Checkout Session for PromptPay (one-time payment)."""
    if not payment.is_configured():
        return jsonify({"ok": False, "error": "ระบบชำระเงินยังไม่พร้อม กรุณาติดต่อทีมงาน"}), 503

    data = request.get_json() or {}
    plan = data.get("plan", "pro")
    if plan not in ("pro", "business"):
        return jsonify({"ok": False, "error": "ไม่รู้จัก plan นี้"}), 400

    username = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        try:
            org_name = f"องค์กรของ {username}"
            org_id, slug = database.create_organization(org_name, username)
            session["org_id"] = org_id
            session["org_role"] = "admin"
            logger.info(f"[Checkout Auto-Org] Created org {org_name} (id={org_id}) for user {username}")
        except Exception as e:
            logger.error(f"[Checkout Auto-Org] Failed to create org: {e}")
            return jsonify({"ok": False, "error": "ไม่สามารถสร้างบัญชีองค์กรอัตโนมัติได้ กรุณาลองใหม่"}), 500

    stripe_info = database.get_org_stripe_info(org_id)
    base = os.environ.get("BASE_URL", "").rstrip("/") or request.host_url.rstrip("/")

    try:
        checkout_session = payment.create_promptpay_checkout(
            org_id=org_id,
            plan=plan,
            customer_id=stripe_info.get("customer_id"),
            success_url=f"{base}/onboarding?plan={plan}&payment=success&method=promptpay&org_id={org_id}&sid={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/pricing",
        )
        return jsonify({"ok": True, "url": checkout_session.url})
    except Exception as e:
        logger.error(f"[Stripe PromptPay] checkout error: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสร้างช่องทางชำระเงินได้ กรุณาลองใหม่"}), 500


@admin_bp.route("/api/billing/portal", methods=["POST"])
@admin_bp.route("/api/b/p", methods=["POST"])
@login_required
def billing_portal():
    """Open Stripe Customer Portal to manage/cancel subscription."""
    org_id = get_current_org_id()
    stripe_info = database.get_org_stripe_info(org_id)
    customer_id = stripe_info.get("customer_id")

    if not customer_id:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูล Stripe — กรุณาสมัครแพลนก่อน"}), 404

    try:
        base = os.environ.get("BASE_URL", "").rstrip("/") or request.host_url.rstrip("/")
        portal = payment.create_portal_session(customer_id, f"{base}/billing")
        return jsonify({"ok": True, "url": portal.url})
    except Exception as e:
        logger.error(f"[Stripe] portal error: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถเปิดหน้าจัดการการชำระเงินได้ กรุณาลองใหม่"}), 500


@admin_bp.route("/api/billing/cancel-plan", methods=["POST"])
@login_required
def billing_cancel_plan():
    """
    ยกเลิก plan:
    - Stripe subscription → cancel_at_period_end=True (ยังใช้ได้ถึงสิ้นรอบ, webhook จัดการ)
    - PromptPay (ไม่มี sub_id) → ใช้ได้ถึง expires_at แล้วหมดเอง ไม่ต้องทำอะไร
    """
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id:
        return jsonify({"ok": False, "error": "ไม่พบองค์กร"}), 404
    if not database.is_org_admin(org_id, me) and not is_admin():
        return jsonify({"ok": False, "error": "เฉพาะ Admin องค์กรเท่านั้นที่ยกเลิกแผนได้"}), 403
    current_plan = billing.get_effective_plan(org_id)
    if current_plan == "free":
        return jsonify({"ok": False, "error": "แผนปัจจุบันเป็น Free อยู่แล้ว"}), 400

    stripe_info = database.get_org_stripe_info(org_id)
    sub_id = stripe_info.get("subscription_id")

    if sub_id and payment.is_configured():
        # ─── Stripe subscription: cancel at period end ───────────────
        # user ยังใช้ได้ถึงสิ้นรอบ, webhook จะ set free เมื่อ subscription deleted
        try:
            import stripe as _stripe
            _stripe.Subscription.modify(
                sub_id,
                cancel_at_period_end=True,
                api_key=os.environ.get("STRIPE_SECRET_KEY", "")
            )
            logger.info(f"[Billing] org {org_id} Stripe sub {sub_id} set cancel_at_period_end by {me}")
            return jsonify({
                "ok": True,
                "plan": current_plan,
                "message": "ยกเลิกแล้ว — คุณยังสามารถใช้งานได้จนถึงสิ้นรอบการเรียกเก็บเงิน",
                "cancel_at_period_end": True,
            })
        except Exception as _se:
            logger.error(f"[Billing] Stripe cancel error: {_se}")
            # Stripe ไม่ตอบ → ตัด access ทันทีเป็น fallback
            billing.set_org_plan(org_id, "free", None)
            logger.info(f"[Billing] org {org_id} force-free (Stripe cancel failed) by {me}")
            return jsonify({"ok": True, "plan": "free", "message": "ยกเลิกแผนแล้ว (force)"})
    else:
        # ─── PromptPay / no subscription: ใช้ได้ถึง expires_at เดิม ──
        # ไม่ต้องเปลี่ยน plan → ระบบจะ downgrade อัตโนมัติเมื่อ expires_at ถึง
        expires_at = stripe_info.get("plan_expires_at") or None
        logger.info(f"[Billing] org {org_id} PromptPay cancel noted by {me}, expires {expires_at}")
        return jsonify({
            "ok": True,
            "plan": current_plan,
            "message": "ยกเลิกแล้ว — คุณยังสามารถใช้งานได้จนถึงวันหมดอายุ ไม่มีการเรียกเก็บเงินเพิ่ม",
            "cancel_at_period_end": True,
        })


def _notify_plan_downgrade_line(org_id: int, reason: str) -> None:
    """ส่ง LINE notification ให้ org admin เมื่อ Stripe downgrade plan เป็น free"""
    try:
        import requests as _req
        tok  = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        base = os.environ.get("BASE_URL", "https://openchat.sbs")
        if not tok:
            return
        org_row  = database.get_org_by_id(org_id)
        org_name = org_row.get("name", f"Org #{org_id}") if org_row else f"Org #{org_id}"
        members  = database.get_org_members(org_id)
        reason_map = {
            "canceled":  "ยกเลิกการสมัครสมาชิก",
            "deleted":   "ยกเลิกการสมัครสมาชิก",
            "past_due":  "ชำระเงินไม่สำเร็จ",
            "unpaid":    "ค้างชำระ",
        }
        reason_th = reason_map.get(reason, reason)
        msg = (
            f"⚠️ แจ้งเตือนจาก OrgChat AI\n\n"
            f"แพลนขององค์กร '{org_name}' ถูกปรับลงเป็น Free\n"
            f"สาเหตุ: {reason_th}\n\n"
            f"กรุณาต่ออายุที่: {base}/billing"
        )
        for m in members:
            if m.get("role") != "admin":
                continue
            line_uid = database.get_line_user_id_for_username(m["username"])
            if not line_uid:
                continue
            try:
                _req.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                    json={"to": line_uid, "messages": [{"type": "text", "text": msg}]},
                    timeout=10,
                )
            except Exception:
                pass
    except Exception as _ne:
        logger.error(f"[notify_downgrade] org={org_id} reason={reason}: {_ne}")


@admin_bp.route("/api/billing/webhook", methods=["POST"])
def stripe_webhook():
    """Stripe webhook — updates org plan on subscription events."""
    payload   = request.get_data()
    sig       = request.headers.get("Stripe-Signature", "")

    try:
        event = payment.construct_webhook_event(payload, sig)
    except Exception as e:
        logger.warning(f"[Stripe webhook] invalid signature: {e}")
        return jsonify({"error": "Invalid webhook signature"}), 400

    event_id = event.get("id", "")

    # Atomic claim: only the first worker (or first delivery) processes this event.
    # stripe_try_claim_event uses INSERT OR IGNORE — concurrent duplicate deliveries
    # will get claimed=False and skip processing safely.
    if event_id:
        claimed = database.stripe_try_claim_event(event_id)
        if not claimed:
            logger.info(f"[Stripe webhook] duplicate event skipped: {event_id}")
            return jsonify({"ok": True})

    etype = event["type"]
    obj   = event["data"]["object"]
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()
    elif obj is not None:
        obj = dict(obj)

    try:
        if etype == "checkout.session.completed":
            meta            = obj.get("metadata", {})
            org_id          = int(meta.get("org_id", 0))
            plan            = meta.get("plan", "pro")
            customer_id     = obj.get("customer")
            subscription_id = obj.get("subscription")
            payment_type    = meta.get("payment_type", "")

            if not org_id:
                logger.error(f"[Stripe webhook] checkout.session.completed missing org_id — session {obj.get('id')}")
                return jsonify({"ok": True})  # bad metadata — retrying won't help

            if plan not in billing.PLANS or plan == "free":
                logger.error(f"[Stripe webhook] invalid plan in metadata: {plan!r}")
                return jsonify({"ok": True})  # bad metadata — retrying won't help

            if not database.get_org_by_id(org_id):
                logger.error(f"[Stripe webhook] org_id={org_id} does not exist — ignoring event")
                return jsonify({"ok": True})  # org deleted — retrying won't help

            if payment_type == "promptpay" or not subscription_id:
                from datetime import timedelta as _td, timezone as _tz
                days = int(meta.get("days", "30"))
                end_iso = (datetime.now(_tz.utc) + _td(days=days)).isoformat()
                billing.set_org_plan(org_id, plan, end_iso)
                if customer_id:
                    database.set_org_stripe_info(org_id, customer_id, None, end_iso)
                logger.info(f"[Stripe PromptPay] Org {org_id} → {plan} for {days} days (expires {end_iso})")
            else:
                end_iso = payment.get_subscription_period_end(subscription_id)
                if not end_iso:
                    # Stripe API ไม่ตอบ → fallback 35 วัน (monthly + 5-day buffer)
                    # Stripe จะส่ง invoice.payment_succeeded ครั้งถัดไปพร้อม end_iso จริง
                    from datetime import timedelta as _td2, timezone as _tz2
                    end_iso = (datetime.now(_tz2.utc) + _td2(days=35)).isoformat()
                    logger.warning(f"[Stripe] Could not get period_end for sub {subscription_id} — using 35d fallback")
                billing.set_org_plan(org_id, plan, end_iso)
                database.set_org_stripe_info(org_id, customer_id, subscription_id, end_iso)
                logger.info(f"[Stripe] Org {org_id} → {plan} (expires {end_iso})")

        elif etype in ("customer.subscription.updated", "invoice.payment_succeeded"):
            meta   = obj.get("metadata", {}) or {}
            org_id = int(meta.get("org_id", 0))

            # invoice.payment_succeeded: invoice object ไม่มี org_id ใน metadata
            # → fallback ดึง metadata จาก subscription object แทน
            if not org_id and etype == "invoice.payment_succeeded":
                _inv_sub_id = obj.get("subscription")
                if _inv_sub_id and payment.is_configured():
                    try:
                        import stripe as _stripe
                        _sub = _stripe.Subscription.retrieve(
                            _inv_sub_id,
                            api_key=os.environ.get("STRIPE_SECRET_KEY", "")
                        )
                        meta = (_sub.get("metadata") or {})
                        org_id = int(meta.get("org_id", 0))
                        logger.info(f"[Stripe webhook] invoice fallback: org_id={org_id} from sub {_inv_sub_id}")
                    except Exception as _inv_e:
                        logger.warning(f"[Stripe webhook] invoice sub lookup failed: {_inv_e}")

            if org_id:
                plan = meta.get("plan", "")
                if not plan or plan not in billing.PLANS or plan == "free":
                    logger.warning(f"[Stripe webhook] {etype} missing/invalid plan {plan!r} for org {org_id} — skipping")
                    return jsonify({"ok": True})
                sub_id = obj.get("id") if etype == "customer.subscription.updated" else obj.get("subscription")
                status = obj.get("status") if etype == "customer.subscription.updated" else "active"
                if status in ("active", "trialing"):
                    end_iso = payment.get_subscription_period_end(sub_id) if sub_id else None
                    if not end_iso:
                        from datetime import timedelta as _td3, timezone as _tz3
                        end_iso = (datetime.now(_tz3.utc) + _td3(days=35)).isoformat()
                        logger.warning(f"[Stripe] {etype} period_end missing — 35d fallback for org {org_id}")
                    billing.set_org_plan(org_id, plan, end_iso)
                    if sub_id:
                        database.set_org_stripe_info(org_id, obj.get("customer", ""), sub_id, end_iso)
                elif status in ("canceled", "unpaid", "past_due"):
                    billing.set_org_plan(org_id, "free")
                    logger.info(f"[Stripe] Org {org_id} → free (status={status})")
                    import threading
                    threading.Thread(
                        target=_notify_plan_downgrade_line, args=(org_id, status), daemon=True
                    ).start()

        elif etype == "customer.subscription.deleted":
            meta   = obj.get("metadata", {})
            org_id = int(meta.get("org_id", 0))
            if org_id:
                billing.set_org_plan(org_id, "free")
                logger.info(f"[Stripe] Org {org_id} → free (subscription deleted)")
                import threading
                threading.Thread(
                    target=_notify_plan_downgrade_line, args=(org_id, "deleted"), daemon=True
                ).start()

    except Exception as _wh_err:
        # Processing failed — un-claim so Stripe retries
        logger.error(f"[Stripe webhook] processing error for {event_id}: {_wh_err}", exc_info=True)
        if event_id:
            database.stripe_remove_event_claim(event_id)
        return jsonify({"error": "internal error"}), 500

    return jsonify({"ok": True})


@admin_bp.route("/api/dashboard/tax-expense-data")
@login_required
@billing.require_feature("financial_dashboard")
def tax_expense_data_api():
    """Aggregates tax and expense data from Google Sheets for the dashboard."""
    try:
        from google_drive_service import google_manager
        username = session.get("user")
        user_settings = database.get_user_setting(username)
        user_role = user_settings.get("role", "user")
        if user_role != "admin" and not user_settings.get("can_view_financial"):
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์เข้าถึงแดชบอร์ดรายจ่าย กรุณาติดต่อ Admin"}), 403
        org_id = get_current_org_id()
        google_manager.set_context(username, org_id)

        # Keep local SQLite logs fully aligned with current sheet content to avoid dashboard drift
        try:
            from google_drive_service import sync_drive_logs_from_sheets
            sync_drive_logs_from_sheets(org_id, username)
        except Exception as sync_err:
            logger.warning(f"Failed to sync drive logs from sheets: {sync_err}")

        if not google_manager.sheets_service:
            return jsonify({"ok": False, "error": "ยังไม่ได้เชื่อมต่อ Google Drive/Sheets — กรุณาให้ Admin ขององค์กรเชื่อมต่อ Google ในหน้า 'จัดการองค์กร'"}), 200
        
        def clean_float(val):
            if not val or str(val).strip() == '-':
                return 0.0
            try:
                s = str(val).replace(',', '').strip()
                is_negative = False
                if s.startswith('(') and s.endswith(')'):
                    is_negative = True
                    s = s[1:-1]
                elif s.startswith('-'):
                    is_negative = True
                    s = s[1:]
                # Remove any remaining non-numeric chars except dot
                import re
                clean_str = re.sub(r'[^\d.]', '', s)
                result = float(clean_str) if clean_str else 0.0
                return -result if is_negative else result
            except Exception:
                return 0.0

        spreadsheet = google_manager.sheets_service.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
        sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        total_expense = 0.0
        total_vat = 0.0
        total_wht = 0.0
        total_wht_3 = 0.0
        total_wht_53 = 0.0
        
        categories_map = {}
        unclear_scans = []
        
        # 1. Process Tax Invoices
        if "ใบเสร็จ/ใบกำกับภาษี" in sheet_titles:
            res_tax = google_manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=google_manager.spreadsheet_id, range="'ใบเสร็จ/ใบกำกับภาษี'!A1:Z"
            ).execute()
            vals = res_tax.get('values', [])
            if vals and len(vals) > 1:
                header = vals[0]
                idx_date = next((i for i, h in enumerate(header) if "วันที่" in h), 2)
                idx_amt = next((i for i, h in enumerate(header) if "สุทธิ" in h or "ยอดเงิน" in h), 9)
                idx_cat = next((i for i, h in enumerate(header) if "หมวดหมู่" in h), 1)
                idx_rec = next((i for i, h in enumerate(header) if "ผู้ส่ง" in h or "ร้านค้า" in h), 3)
                idx_vat = next((i for i, h in enumerate(header) if "VAT" in h), 12)
                idx_wht = next((i for i, h in enumerate(header) if "หัก ณ ที่จ่าย" in h or "WHT" in h), 13)
                idx_tax_id = next((i for i, h in enumerate(header) if "เลขผู้เสียภาษี" in h or "Tax" in h), 5)
                idx_ai_summary = next((i for i, h in enumerate(header) if "สรุปจาก AI" in h), 17)
                idx_link = next((i for i, h in enumerate(header) if "ลิงก์ไฟล์" in h or "ลิงก์ drive" in h), 19)
                
                for r_idx, row in enumerate(vals[1:], start=2):
                    if len(row) <= min(idx_date, idx_amt): continue
                    
                    amt = clean_float(row[idx_amt] if idx_amt < len(row) else 0.0)
                    total_expense += amt
                    
                    cat_val = str(row[idx_cat]).strip() if idx_cat < len(row) else ""
                    if not cat_val or cat_val == '-': cat_val = "ทั่วไป"
                    categories_map[cat_val] = categories_map.get(cat_val, 0.0) + amt
                    
                    vat = clean_float(row[idx_vat] if idx_vat < len(row) else 0.0)
                    total_vat += vat
                    
                    wht = clean_float(row[idx_wht] if idx_wht < len(row) else 0.0)
                    total_wht += wht
                    
                    tax_id = str(row[idx_tax_id]).strip() if idx_tax_id < len(row) else ""
                    if wht > 0:
                        # Improved WHT classification: 13 digits not starting with 0 is usually Personal (3), else Corporate (53)
                        if len(tax_id) == 13 and not tax_id.startswith("0"):
                            total_wht_3 += wht
                        else:
                            total_wht_53 += wht
                            
                    ai_summary = str(row[idx_ai_summary]).strip() if idx_ai_summary < len(row) else ""
                    vendor = str(row[idx_rec]).strip() if idx_rec < len(row) else "-"
                    date_val = str(row[idx_date]).strip() if idx_date < len(row) else "-"
                    link_val = str(row[idx_link]).strip() if idx_link < len(row) else ""
                    
                    is_unclear = False
                    issues = []
                    unclear_keywords = ["ไม่ชัด", "ชำรุด", "เบลอ", "ตรวจสอบไม่ได้", "อ่านไม่ได้", "ขาดชำรุด", "มืด"]
                    if any(k in ai_summary for k in unclear_keywords) or any(k in vendor for k in unclear_keywords):
                        is_unclear = True
                        issues.append("ภาพไม่ชัด")
                    if not amt:
                        is_unclear = True
                        issues.append("ไม่พบยอดเงิน")
                    if not date_val or date_val == "-":
                        is_unclear = True
                        issues.append("ไม่พบวันที่")
                        
                    if is_unclear:
                        unclear_scans.append({
                            "sheet": "ใบเสร็จ/ใบกำกับภาษี", "row": r_idx, "date": date_val,
                            "vendor": vendor, "amount": amt, "issues": ", ".join(issues), "link": link_val
                        })

        # 2. Process General Expenses (Voice recordings/others)
        if "บันทึกค่าใช้จ่าย" in sheet_titles:
            res_gen = google_manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=google_manager.spreadsheet_id, range="'บันทึกค่าใช้จ่าย'!A1:Z"
            ).execute()
            vals_gen = res_gen.get('values', [])
            if vals_gen and len(vals_gen) > 1:
                header = vals_gen[0]
                idx_amt = next((i for i, h in enumerate(header) if "จำนวนเงิน" in h), 4)
                idx_cat = next((i for i, h in enumerate(header) if "หมวดหมู่" in h), 1)
                idx_type = next((i for i, h in enumerate(header) if "ประเภท" in h), 3)
                
                for row in vals_gen[1:]:
                    amt = clean_float(row[idx_amt] if idx_amt < len(row) else 0.0)
                    total_expense += amt
                    
                    cat_val = str(row[idx_type]).strip() if idx_type < len(row) else (str(row[idx_cat]).strip() if idx_cat < len(row) else "ทั่วไป")
                    if not cat_val or cat_val == '-': cat_val = "ทั่วไป"
                    categories_map[cat_val] = categories_map.get(cat_val, 0.0) + amt

        # 3. Process Other Sheets (Transfer Slips, WHT, PEAK)
        other_sheets = ["สลิปโอนเงิน", "ใบหัก ณ ที่จ่าย", "peak"]
        for s_title in other_sheets:
            if s_title not in sheet_titles: continue
            res = google_manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=google_manager.spreadsheet_id, range=f"'{s_title}'!A1:Z"
            ).execute()
            vals = res.get('values', [])
            if not vals or len(vals) <= 1: continue
            
            header = vals[0]
            h_map = {h.strip().lower(): i for i, h in enumerate(header)}
            
            # Find common columns
            idx_amt = next((i for i, h in enumerate(header) if "สุทธิ" in h or "ยอดเงิน" in h or "จำนวนเงิน" in h or "มูลค่ารวมภาษี" in h), -1)
            idx_vat = next((i for i, h in enumerate(header) if "VAT" in h or "ภาษีมูลค่าเพิ่ม" in h), -1)
            idx_wht = next((i for i, h in enumerate(header) if "หัก ณ ที่จ่าย" in h or "WHT" in h or "ภาษีที่หัก" in h), -1)
            idx_cat = next((i for i, h in enumerate(header) if "หมวดหมู่" in h or "ประเภท" in h), -1)
            
            if idx_amt == -1: continue
            
            for row in vals[1:]:
                amt = clean_float(row[idx_amt] if idx_amt < len(row) else 0.0)
                if amt == 0: continue
                
                # For PEAK or similar, if amount is negative, it's a credit note, should reduce total expense
                total_expense += amt
                
                cat_val = str(row[idx_cat]).strip() if (idx_cat != -1 and idx_cat < len(row)) else s_title
                if not cat_val or cat_val == '-': cat_val = s_title
                categories_map[cat_val] = categories_map.get(cat_val, 0.0) + amt
                
                if idx_vat != -1:
                    total_vat += clean_float(row[idx_vat] if idx_vat < len(row) else 0.0)
                if idx_wht != -1:
                    wht_val = clean_float(row[idx_wht] if idx_wht < len(row) else 0.0)
                    total_wht += wht_val
                    # Simplified WHT split for these sheets as they often lack tax_id in the same row
                    if wht_val > 0:
                        total_wht_53 += wht_val 

        # Format categories for chart
        categories_list = [{"name": k, "value": v} for k, v in categories_map.items()]
        categories_list = sorted(categories_list, key=lambda x: x['value'], reverse=True)

        spreadsheet_id = google_manager.spreadsheet_id
        parent_folder_id = google_manager.parent_folder_id
        
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit" if spreadsheet_id else "https://docs.google.com/spreadsheets"
        drive_folder_url = f"https://drive.google.com/drive/folders/{parent_folder_id}" if parent_folder_id else "https://drive.google.com"

        biz_profile = database.get_org_profile(org_id) if org_id else None

        return jsonify({
            "ok": True,
            "total_expense": total_expense,
            "total_vat": total_vat,
            "total_wht": total_wht,
            "total_wht_3": total_wht_3,
            "total_wht_53": total_wht_53,
            "categories": categories_list,
            "unclear_scans": unclear_scans,
            "sheets_list": sheet_titles,
            "spreadsheet_url": spreadsheet_url,
            "drive_folder_url": drive_folder_url,
            "biz_profile": biz_profile
        })

    except Exception as e:
        import traceback
        from google.auth.exceptions import RefreshError
        logger.error(f"[Dashboard API] {e}\n{traceback.format_exc()}")
        if isinstance(e, RefreshError) or 'invalid_grant' in str(e):
            return jsonify({"ok": False, "error": "Token Google หมดอายุหรือถูก revoke — กรุณาเชื่อมต่อ Google ใหม่อีกครั้ง"}), 200
        return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการดึงข้อมูล Google Sheets"}), 500


@admin_bp.route("/api/set_key", methods=["POST"])
@admin_required
def set_key():
    data = request.get_json(force=True)
    key = data.get("api_key", "").strip()
    if not key:
        return jsonify({"ok": False, "error": "กรุณาใส่ API Key"}), 400
    os.environ["GEMINI_API_KEY"] = key
    # Persist to .env using absolute path from rag_engine
    env_path = rag_engine.BASE_DIR / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    lines = [l for l in lines if not l.startswith("GEMINI_API_KEY")]
    lines.append(f"GEMINI_API_KEY={key}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    # Refresh RAG engine with new key
    rag_engine._kb.update_api_key(key)
    
    return jsonify({"ok": True})


@admin_bp.route("/api/reconciliation/process", methods=["POST"])
@login_required
@billing.require_plan("pro")
def process_reconciliation():
    if not is_admin():
        return jsonify({"ok": False, "error": "Only admins can perform reconciliation"}), 403
    
    mp_files = request.files.getlist('marketplace')
    ship_files = request.files.getlist('shipnity')
    peak_files = request.files.getlist('peak')
    
    if not mp_files or not ship_files or not peak_files:
        return jsonify({"ok": False, "error": "กรุณาอัปโหลดไฟล์ให้ครบทุกหมวดหมู่ (Marketplace, Shipnity, PEAK)"}), 400
        
    try:
        df_result, financial = ReconciliationService.process_files(mp_files, ship_files, peak_files)
        
        # Fill NaN with safe defaults for JSON serialization
        df_clean = df_result.fillna('')
        
        for col in df_clean.columns:
            if df_clean[col].dtype in ['float64', 'int64']:
                df_clean[col] = df_clean[col].replace('', 0)
        
        records = df_clean.to_dict(orient='records')
        
        issue_count = sum(1 for r in records if r.get('issue', '') != '✅ ปกติ')
        
        summary = {
            "total": len(records),
            "issues": issue_count,
            "data": records,
            "financial": financial
        }
        
        # Cache data in memory for on-demand download (capped at 20 to prevent unbounded growth)
        report_id = uuid.uuid4().hex[:8]
        with _recon_lock:
            if len(_recon_cache) >= 20:
                oldest_key = next(iter(_recon_cache))
                del _recon_cache[oldest_key]
            _recon_cache[report_id] = df_result
        
        summary["report_url"] = f"/api/reconciliation/download/{report_id}"
        
        return jsonify({"ok": True, "summary": summary})
    except Exception as e:
        import traceback
        logger.error(f"[Reconciliation] {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการประมวลผลข้อมูล กรุณาลองใหม่"}), 500


@admin_bp.route("/api/reconciliation/download/<report_id>")
@login_required
def download_recon_report(report_id):
    with _recon_lock:
        df = _recon_cache.get(report_id)
    if df is None:
        return jsonify({"ok": False, "error": "รายงานหมดอายุ กรุณาประมวลผลใหม่"}), 404
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'reconciliation_report_{report_id}.xlsx'
    )


@admin_bp.route("/api/reconciliation/download-filtered", methods=["POST"])
@login_required
def download_filtered_recon():
    """Generate Excel from filtered data sent by client."""
    try:
        data = request.get_json()
        rows = data.get('rows', [])
        if not rows:
            return jsonify({"ok": False, "error": "ไม่มีข้อมูลสำหรับดาวน์โหลด"}), 400
        
        import pandas as pd
        df = pd.DataFrame(rows)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'reconciliation_filtered_{uuid.uuid4().hex[:6]}.xlsx'
        )
    except Exception as e:
        logger.error(f"[Reconciliation download-filtered] {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถสร้างไฟล์ Excel ได้ กรุณาลองใหม่"}), 500


@admin_bp.route("/api/reconciliation/move-row", methods=["POST"])
@login_required
@billing.require_plan("pro")
def move_row_between_sheets_api():
    """Move a row from one sheet to another in Google Sheets."""
    try:
        data = request.get_json()
        from_sheet = data.get("from_sheet", "").strip()
        row_index = int(data.get("row_index", 0))
        to_sheet = data.get("to_sheet", "").strip()

        if not from_sheet or not to_sheet or row_index <= 0:
            return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400

        ok, err = google_manager.move_row_between_sheets(from_sheet, row_index, to_sheet)
        if ok:
            return jsonify({"ok": True})
        else:
            return jsonify({"ok": False, "error": err or "ย้ายไม่สำเร็จ"}), 500
    except Exception as e:
        import traceback
        logger.error(f"[move-row] {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": "ไม่สามารถย้ายแถวได้ กรุณาลองใหม่"}), 500


@admin_bp.route("/api/schedules", methods=["GET", "POST"])
@login_required
def manage_schedules():
    user = session.get("user")
    if request.method == "POST":
        data = request.get_json(force=True)
        title = data.get("title")
        start_date = data.get("date") # Expected YYYY-MM-DD
        desc = data.get("desc", "")
        category = data.get("category", "General")
        start_time = data.get("time", "09:00")
        is_public = 1 if data.get("is_public") else 0
        target_depts = data.get("target_departments")
        target_users = data.get("target_users")
        status = data.get("status", "todo")
        
        if not title or not start_date:
            return jsonify({"ok": False, "error": "Missing title or date"}), 400

        org_id = get_current_org_id()

        # ตรวจว่าวันที่เลือกมีคำขอลาที่อนุมัติแล้วหรือไม่
        leave_warning = None
        try:
            _lconn = database._get_conn()
            try:
                _leave = _lconn.execute(
                    """SELECT 1 FROM leave_requests
                       WHERE username=? AND status='approved'
                       AND start_date <= ? AND end_date >= ?
                       LIMIT 1""",
                    (user, start_date, start_date),
                ).fetchone()
            finally:
                _lconn.close()
            if _leave:
                leave_warning = f"วันที่ {start_date} มีการลาที่อนุมัติแล้ว กรุณาตรวจสอบก่อนบันทึก"
        except Exception:
            pass

        database.add_schedule(user, title, start_date, desc, category, start_time, is_public, status, target_departments=target_depts, target_users=target_users, org_id=org_id)
        visibility_text = "Public" if is_public else "Private"
        database.log_event(f"Added {visibility_text} schedule: {title} on {start_date}", user=user, org_id=org_id)
        
        # --- New Public Event Broadcast ---
        profile = database.get_user_profile(user)
        display_name = profile.get("display_name", user)
        if is_public:
            notification_db.notify_all_except(
                user, 
                'calendar', 
                'กิจกรรมใหม่: ' + title, 
                f'โดย {display_name} | วันที่ {start_date} เวลา {start_time}',
                link='#calendar'
            )
            # --- LINE Broadcast for Public Events ---
            threading.Thread(target=broadcast_line_announcement, args=(
                "กิจกรรมใหม่", 
                f"-> กำหนดการใหม่!\nหัวข้อ: {title}\nวันที่: {start_date}\nเวลา: {start_time} น.\nโดย: {display_name}",
            ), kwargs={
                "fields": {
                    "หัวข้อ": title,
                    "วันที่": start_date,
                    "เวลา": f"{start_time} น.",
                    "โดย": display_name
                }
            }).start()
        else:
            # Notify specific users if specified
            if target_users:
                t_users = [u.strip() for u in target_users.split(',') if u.strip() and u.strip().lower() != user.lower()]
                if t_users:
                    notification_db.notify_users(
                        t_users, 'calendar', 'กำหนดการใหม่ที่แชร์กับคุณ: ' + title,
                        f'โดย {display_name} | วันที่ {start_date} เวลา {start_time}',
                        link='#calendar'
                    )
                    batch_send_push_notification(t_users, 'กำหนดการที่แชร์กับคุณ', f'{display_name}: {title}', url='#calendar')
                    
                    # --- LINE Push for Targeted Users ---
                    for target in t_users:
                        threading.Thread(target=send_line_push_notification, args=(
                            target, 
                            "กิจกรรมใหม่", 
                            f"-> กำหนดการใหม่สำหรับคุณ!\nหัวข้อ: {title}\nวันที่: {start_date}\nเวลา: {start_time} น.",
                        ), kwargs={
                            "fields": {
                                "หัวข้อ": title,
                                "วันที่": start_date,
                                "เวลา": f"{start_time} น.",
                                "โดย": display_name
                            }
                        }).start()
            
            # Notify specific departments
            if target_depts:
                t_depts = [d.strip() for d in target_depts.split(',') if d.strip()]
                # Get all users in these departments
                conn = database._get_conn()
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT username FROM user_profiles WHERE department IN ({','.join(['?']*len(t_depts))})", t_depts)
                    dept_users = [r[0] for r in cursor.fetchall() if r[0].lower() != user.lower()]
                finally:
                    conn.close()
                if dept_users:
                    notification_db.notify_users(
                        dept_users, 'calendar', 'กิจกรรมใหม่ในแผนก: ' + title,
                        f'โดย {display_name} | วันที่ {start_date} เวลา {start_time}',
                        link='#calendar'
                    )
                    batch_send_push_notification(dept_users, 'กิจกรรมใหม่ในแผนก', f'{display_name}: {title}', url='#calendar')
                        
        result = {"ok": True}
        if leave_warning:
            result["warning"] = leave_warning
        return jsonify(result)

    org_id = get_current_org_id()
    return jsonify({"schedules": database.get_schedules(user, org_id=org_id)})


@admin_bp.route("/api/schedules/<int:sid>", methods=["PUT", "DELETE"])
@login_required
def manage_schedule_item(sid):
    user = session.get("user")
    org_id = get_current_org_id()
    # Verify this schedule belongs to current org before any operation
    sched = database.get_schedule_by_id(sid)
    if not sched or sched.get("organization_id") != org_id:
        return jsonify({"ok": False, "error": "ไม่พบหรือไม่มีสิทธิ์"}), 404

    if request.method == "DELETE":
        ok = database.delete_schedule(sid, username=user, is_admin=is_admin())
        if ok:
            database.log_event(f"Schedule deleted: ID {sid}", user=user, org_id=org_id)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์ลบกำหนดการนี้"}), 403

    if request.method == "PUT":
        data = request.get_json(force=True)
        title = data.get("title")
        date = data.get("date")
        desc = data.get("desc", "")
        cat = data.get("category", "General")
        time_val = data.get("time", "09:00")
        is_public = 1 if data.get("is_public") else 0
        status = data.get("status", "todo")
        target_depts = data.get("target_departments")
        target_users = data.get("target_users")

        if not title or not date:
            return jsonify({"ok": False, "error": "Missing title or date"}), 400

        database.update_schedule(sid, title, date, desc, cat, time_val, is_public, status, target_departments=target_depts, target_users=target_users)
        user = session.get("user", "Admin")
        database.log_event(f"Updated schedule ID: {sid}", user=user, org_id=org_id)
        return jsonify({"ok": True})


@admin_bp.route("/api/schedules/<int:sid>/toggle", methods=["POST"])
@login_required
def toggle_schedule_route(sid):
    new_status = database.toggle_schedule_status(sid)
    if new_status is None:
        return jsonify({"ok": False, "error": "Schedule not found"}), 404
    user = session.get("user", "Admin")
    database.log_event(f"Toggled schedule status: {sid} to {new_status}", user=user, org_id=get_current_org_id())
    return jsonify({"ok": True, "new_status": new_status})


@admin_bp.route("/api/schedules/clear-past", methods=["DELETE"])
@login_required
def delete_past_schedules_route():
    user = session.get("user")
    database.delete_past_schedules(user)
    database.log_event(f"Cleared all past schedules", user=user, org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/schedules/archive-past", methods=["POST"])
@login_required
def archive_past_schedules_route():
    user = session.get("user")
    database.archive_past_schedules(user)
    database.log_event(f"Archived all past schedules", user=user, org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/lunch/random")
@login_required
def lunch_random():
    place = database.get_random_lunch()
    if place:
        return jsonify({"ok": True, "place": place})
    return jsonify({"ok": False, "error": "ยังไม่มีร้านอาหารในระบบ"})


@admin_bp.route("/api/lunch/all")
@login_required
def lunch_all():
    places = database.get_all_lunch_places()
    return jsonify({"ok": True, "places": places})


@admin_bp.route("/api/lunch/add", methods=["POST"])
@login_required
def lunch_add():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อร้าน"})
    
    database.add_lunch_place(
        name=name,
        type_str=data.get("type", ""),
        location=data.get("location", ""),
        added_by=session.get("user", "Admin")
    )
    return jsonify({"ok": True})


@admin_bp.route("/api/lunch/delete/<int:place_id>", methods=["DELETE"])
@login_required
@admin_required
def lunch_delete(place_id):
    conn = database._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lunch_places WHERE id = ?", (place_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/dashboard/stats")
@admin_required
def admin_dashboard_stats():
    """Provides system-wide statistics for the admin dashboard."""
    conn = database._get_conn()
    try:
        cursor = conn.cursor()
        
        # Total Queries (All users)
        cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'")
        total_queries = cursor.fetchone()[0]
        
        # Active Users (last 30 days)
        cursor.execute("SELECT COUNT(DISTINCT username) FROM user_profiles") # Simplified for now
        total_users = cursor.fetchone()[0]
        
        # Storage Stats
        uploads_size = sum(f.stat().st_size for f in rag_engine.UPLOAD_DIR.glob('*') if f.is_file())
        
        # Feedback counts
        cursor.execute("SELECT feedback, COUNT(*) FROM messages WHERE role = 'bot' GROUP BY feedback")
        feedback_stats = dict(cursor.fetchall())
    finally:
        conn.close()
    
    return jsonify({
        "ok": True,
        "total_queries": total_queries,
        "total_users": total_users,
        "uploads_size_mb": round(uploads_size / (1024 * 1024), 2),
        "feedback": feedback_stats,
        "kb_size": rag_engine.kb_stats().get("knowledge_base_size", 0)
    })


@admin_bp.route("/api/admin/system/diagnostics")
@admin_required
def admin_system_diagnostics():
    """Provides a detailed system diagnostic check for admins."""
    import sys
    import platform
    import sqlite3
    import time
    
    diagnostics = {}
    
    # 1. OS & Environment
    diagnostics["os"] = {
        "platform": platform.platform(),
        "python_version": sys.version,
        "current_time": shared.get_current_time()
    }
    
    # 2. Database Status
    db_path = database.DB_PATH
    db_exists = db_path.exists()
    db_size = db_path.stat().st_size if db_exists else 0
    db_writable = False
    if db_exists:
        try:
            with open(db_path, "a+b") as f:
                db_writable = True
        except Exception:
            pass
            
    diagnostics["database"] = {
        "engine": database.DB_TYPE,
        "sqlite_path": str(db_path.absolute()),
        "sqlite_exists": db_exists,
        "sqlite_size_mb": round(db_size / (1024 * 1024), 2),
        "sqlite_writable": db_writable,
    }
    
    # 3. Vector Database Status
    kb = rag_engine._get_kb()
    is_fallback = kb._ephemeral
    diagnostics["vector_db"] = {
        "engine": "PurePythonVectorStore (Fallback)" if is_fallback else "ChromaDB (Persistent)",
        "total_chunks": kb.total_chunks(),
        "total_files": len(rag_engine._load_meta()),
        "provider": kb.provider
    }
    
    # 4. AI Credentials & Quota
    diagnostics["ai"] = {
        "provider": os.environ.get("AI_PROVIDER", "groq").lower(),
        "embedding_provider": os.environ.get("AI_EMBEDDING_PROVIDER", "gemini").lower(),
        "gemini_api_key_set": bool(os.environ.get("GEMINI_API_KEY")),
        "groq_api_key_set": bool(os.environ.get("GROQ_API_KEY")),
        "quota_info": rag_engine.get_quota_status()
    }
    
    # 5. File System & Uploads
    upload_dir = rag_engine.UPLOAD_DIR
    upload_dir_exists = upload_dir.exists()
    upload_writable = False
    if upload_dir_exists:
        try:
            test_file = upload_dir / f"test_write_{int(time.time())}.tmp"
            test_file.write_text("write_test")
            test_file.unlink()
            upload_writable = True
        except Exception:
            pass
            
    diagnostics["filesystem"] = {
        "upload_dir": str(upload_dir.absolute()),
        "exists": upload_dir_exists,
        "writable": upload_writable
    }
    
    # 6. Google Drive & OAuth2 Services
    token_path = Path("token.json")
    google_drive_linked = token_path.exists()
    diagnostics["google_services"] = {
        "oauth2_enabled": shared.OAUTH2_AVAILABLE,
        "google_auth_available": shared.GOOGLE_AUTH_AVAILABLE,
        "drive_linked": google_drive_linked,
        "drive_parent_id_set": bool(os.environ.get("GOOGLE_DRIVE_PARENT_ID"))
    }
    
    return jsonify({
        "ok": True,
        "diagnostics": diagnostics
    })


# ─── AI Persona Management (Admin) ──────────────────────────
@admin_bp.route("/api/admin/personas", methods=["GET"])
@org_admin_required
def admin_get_personas():
    org_id = get_current_org_id()
    # Scoped by organization or created by 'System'
    conn = database._get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM ai_personas 
        WHERE organization_id = ? OR created_by = 'System'
        ORDER BY name ASC
    """, (org_id,))
    columns = [column[0] for column in cursor.description]
    personas = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"ok": True, "personas": personas})

@admin_bp.route("/api/admin/personas", methods=["POST"])
@org_admin_required
def admin_create_persona():
    org_id = get_current_org_id()
    data = request.json
    name = data.get("name")
    prompt = data.get("prompt")
    description = data.get("description")
    icon = data.get("icon")

    if not name or not prompt:
        return jsonify({"ok": False, "error": "Missing name or prompt"}), 400

    conn = database._get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ai_personas (name, system_prompt, description, avatar_url, created_by, organization_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, prompt, description, icon, session.get("user"), org_id))
    conn.commit()
    conn.close()
    
    database.log_event(f"Created AI Persona: {name}", user=session.get("user"), org_id=org_id)
    return jsonify({"ok": True})

@admin_bp.route("/api/admin/personas/<int:pid>", methods=["PUT"])
@org_admin_required
def admin_update_persona(pid):
    org_id = get_current_org_id()
    data = request.json
    name = data.get("name")
    prompt = data.get("prompt")
    description = data.get("description")
    icon = data.get("icon")

    # Security check: Ensure persona belongs to this org
    p = database.get_persona(pid)
    if not p or (p.get("organization_id") != org_id and p.get("created_by") != 'System' and not session.get("is_superadmin")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    database.update_persona(pid, name=name, system_prompt=prompt, description=description, avatar_url=icon)
    database.log_event(f"Updated AI Persona: {name} (ID: {pid})", user=session.get("user"), org_id=org_id)
    return jsonify({"ok": True})

@admin_bp.route("/api/admin/personas/<int:pid>", methods=["DELETE"])
@org_admin_required
def admin_delete_persona(pid):
    org_id = get_current_org_id()
    p = database.get_persona(pid)
    if not p or (p.get("organization_id") != org_id and not session.get("is_superadmin")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    database.delete_persona(pid)
    database.log_event(f"Deleted AI Persona (ID: {pid})", user=session.get("user"), org_id=org_id)
    return jsonify({"ok": True})

# ─── Activity Logs (Admin) ──────────────────────────────────
@admin_bp.route("/api/admin/logs", methods=["GET"])
@org_admin_required
def admin_get_logs():
    logs = database.get_events(limit=100)
    return jsonify({"ok": True, "logs": logs})


@admin_bp.route("/api/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings_route():
    if request.method == "GET":
        return jsonify({"ok": True, "settings": database.get_all_app_settings()})
    
    if request.method == "POST":
        data = request.json
        for key, value in data.items():
            database.set_app_setting(key, str(value))
        return jsonify({"ok": True})


@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_list_users():
    users = database.admin_get_all_users(org_id=get_current_org_id())
    return jsonify({"ok": True, "users": users})


@admin_bp.route("/api/users/list", methods=["GET"])
@login_required
def list_users_for_sharing():
    """Returns a simplified list of all users for selection in sharing UI."""
    users = database.admin_get_all_users(org_id=get_current_org_id()) # This returns profiles + settings
    # Filter only necessary fields for non-admin use
    safe_users = [{
        "username": u["username"],
        "display_name": u["display_name"] or u["username"].capitalize(),
        "avatar_url": u.get("avatar_url"),
        "department": u.get("department", "General")
    } for u in users if u.get("is_active", 1)]
    return jsonify({"ok": True, "users": safe_users})


@admin_bp.route("/api/admin/users", methods=["POST"])
@admin_required
def admin_create_user_route():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "user")
    display_name = data.get("display_name", "").strip()
    department = data.get("department", "General").strip()
    email = data.get("email", "").strip().lower()
    can_view_kb = data.get("can_view_kb", True)
    can_edit_kb = data.get("can_edit_kb", False)
    can_delete_kb = data.get("can_delete_kb", False)

    if not username or not password:
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"}), 400

    if database.admin_create_user(username, password, role, display_name=display_name, can_view_kb=can_view_kb, can_edit_kb=can_edit_kb, can_delete_kb=can_delete_kb, department=department, email=email or None):
        database.log_event(f"Created user: {username} (Role: {role})", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว"}), 400


@admin_bp.route("/api/admin/users/<username>", methods=["PUT"])
@admin_required
def admin_update_user_route(username):
    data = request.json
    display_name = data.get("display_name")
    role = data.get("role")
    is_active = data.get("is_active")
    can_view_kb = data.get("can_view_kb")
    can_edit_kb = data.get("can_edit_kb")
    can_delete_kb = data.get("can_delete_kb")
    can_view_financial = data.get("can_view_financial")
    department = data.get("department")
    notes = data.get("notes")
    password = data.get("password")

    database.admin_update_user(username, display_name, role, is_active, notes, can_view_kb, can_edit_kb, can_delete_kb, department=department, can_view_financial=can_view_financial)
    if password:
        database.admin_reset_user_password(username, password)
        
    database.log_event(f"Updated user details for: {username}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/users/<username>/reset-password", methods=["POST"])
@admin_required
def admin_reset_password_route(username):
    data = request.get_json() or {}
    password = data.get("password")
    if not password:
        return jsonify({"ok": False, "error": "กรุณากรอกรหัสผ่านใหม่"}), 400
    
    database.admin_reset_user_password(username, password)
    database.log_event(f"Reset password for: {username}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/users/<username>", methods=["DELETE"])
@admin_required
def admin_delete_user_route(username):
    if username == session.get("user"):
        return jsonify({"ok": False, "error": "ไม่สามารถลบตัวเองได้"}), 400

    # ป้องกัน orphan org — ถ้าเป็น admin คนเดียวของ org ใดก็ตาม → ห้ามลบ
    user_orgs = database.get_user_orgs(username) or []
    for org in user_orgs:
        if database.is_org_admin(org["id"], username) and database.count_org_admins(org["id"]) <= 1:
            return jsonify({
                "ok": False,
                "error": f"ไม่สามารถลบ '{username}' ได้ เนื่องจากเป็น Admin คนเดียวขององค์กร '{org.get('name', org['id'])}' "
                         f"กรุณาตั้งสมาชิกคนอื่นเป็น Admin ก่อน"
            }), 400

    if database.admin_delete_user_complete(username):
        database.log_event(f"Deleted user: {username}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่สามารถลบผู้ใช้นี้ได้"}), 400


@admin_bp.route("/api/admin/users/<username>/unbind-line", methods=["POST"])
@admin_required
def admin_unbind_user_line_route(username):
    """Unbind (disconnect) LINE account for a user profile by system administrator."""
    if database.unlink_line_user(username):
        database.log_event(f"Unbound LINE account for user: {username}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่สามารถยกเลิกการผูกบัญชี LINE ได้ หรือผู้ใช้นี้ยังไม่ได้ผูกบัญชี LINE"}), 400


@admin_bp.route("/api/org/members", methods=["POST"])
@login_required
def invite_org_member():
    me = session.get("user")
    org_id = get_current_org_id()
    if not org_id or not database.is_org_admin(org_id, me):
        return jsonify({"ok": False, "error": "เฉพาะผู้ดูแลองค์กรเท่านั้นที่สามารถเชิญสมาชิกได้"}), 403
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()   # ถ้าส่งมาด้วย = สร้าง user ใหม่
    role = data.get("role", "member")
    if role not in ("admin", "member"):
        role = "member"
    if not username:
        return jsonify({"ok": False, "error": "กรุณาระบุชื่อผู้ใช้"}), 400

    # ตรวจว่า user มีอยู่ในระบบแล้วไหม
    existing = database.get_user_setting(username)
    user_exists = bool(existing.get("custom_password"))

    # ตรวจว่าเป็นสมาชิกขององค์กรนี้อยู่แล้ว
    if user_exists and database.is_org_member(org_id, username.lower()):
        return jsonify({
            "ok": False,
            "error": f"'{username}' เป็นสมาชิกขององค์กรนี้อยู่แล้ว",
        }), 409

    if not user_exists:
        if not password:
            return jsonify({
                "ok": False,
                "error": "user_not_found",
                "message": f"ไม่พบ user '{username}' ในระบบ กรุณาระบุรหัสผ่านเพื่อสร้างบัญชีใหม่ให้เขาด้วย",
                "need_password": True,
            }), 404
        # สร้าง user ใหม่อัตโนมัติ
        created = database.admin_create_user(
            username=username.lower(),
            password=password,
            role=role,
            display_name=username,
        )
        if not created:
            return jsonify({"ok": False, "error": "ชื่อผู้ใช้นี้มีอยู่แล้ว (อาจเป็น case ต่างกัน)"}), 400

    # Atomic quota check + insert — ป้องกัน race condition เมื่อ 2 admin เชิญพร้อมกัน
    _mem_plan = billing.get_effective_plan(org_id)
    _max_users = billing.get_plan_config(_mem_plan)["limits"]["max_users"]
    try:
        ok, reason = database.add_org_member_with_quota(
            org_id, username.lower(), role=role,
            invited_by=session.get("user"), max_users=_max_users
        )
        if not ok:
            _cfg = billing.get_plan_config(_mem_plan)
            return jsonify({
                "ok": False,
                "error": "user_limit_reached",
                "message": f"Plan {_cfg['name']} อนุญาตสมาชิกได้สูงสุด {_max_users} คน กรุณาอัปเกรด Plan เพื่อเพิ่มสมาชิก",
                "current_plan": _mem_plan,
                "upgrade_url": "/billing",
            }), 403
        return jsonify({
            "ok": True,
            "created_new_user": not user_exists,
            "message": f"{'สร้างบัญชีและ' if not user_exists else ''}เพิ่ม {username} เข้าองค์กรสำเร็จ"
        })
    except Exception as e:
        logger.error(f"[add_org_member] {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถเพิ่มสมาชิกได้ กรุณาลองใหม่"}), 500





@admin_bp.route("/api/admin/analytics", methods=["GET"])
@admin_required
def get_admin_analytics():
    stats = database.get_analytics_data()
    return jsonify({"ok": True, "stats": stats})


@admin_bp.route("/api/schedules/<int:sched_id>/status", methods=["PATCH"])
@login_required
def patch_schedule_status(sched_id):
    data = request.json or {}
    status = data.get("status")
    if not status:
        return jsonify({"ok": False, "error": "Status required"}), 400
    
    user = session.get("user")
    if database.update_schedule_status(sched_id, status, user):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Could not update status"}), 403


@admin_bp.route("/api/schedules/reminders")
@login_required
def check_reminders():
    from datetime import datetime, timedelta
    user = session.get("user")
    schedules = database.get_schedules(user, org_id=get_current_org_id())
    now = datetime.now()
    reminders = []
    for s in schedules:
        try:
            dt_str = f"{s['date']} {s.get('time', '00:00')}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            diff = (dt - now).total_seconds() / 60
            if 0 < diff <= 15:
                reminders.append({
                    "id": s["id"],
                    "title": s["title"],
                    "minutes_left": int(diff),
                    "time": s.get("time", "")
                })
        except Exception:
            pass
    return jsonify({"reminders": reminders})


@admin_bp.route("/api/leave/request", methods=["POST"])
@login_required
def api_leave_request():
    user = session.get("user")
    data = request.get_json()
    l_type = data.get("type", "Sick")
    s_date = data.get("start_date")
    e_date = data.get("end_date")
    reason = data.get("reason", "")
    
    if not s_date or not e_date:
        return jsonify({"ok": False, "error": "กรุณากรอกวันที่เริ่มต้นและวันที่สิ้นสุดการลาให้ครบถ้วนค่ะ"}), 400

    # ตรวจ date logic
    if s_date > e_date:
        return jsonify({"ok": False, "error": "วันที่เริ่มต้นต้องไม่เกินวันที่สิ้นสุดค่ะ"}), 400

    # ตรวจ overlap กับใบลาที่มีอยู่
    overlap = database.check_leave_overlap(user, s_date, e_date)
    if overlap:
        return jsonify({
            "ok": False,
            "error": f"คุณมีใบลา {overlap['type']} ที่ทับซ้อนช่วง {overlap['start_date']} – {overlap['end_date']} อยู่แล้วค่ะ (สถานะ: {overlap.get('status','รอดำเนินการ')})"
        }), 400

    leave_id = database.create_leave_request(user, l_type, s_date, e_date, reason)
    if leave_id:
        # แจ้ง org admins เท่านั้น — ไม่ใช่ system admins ทั้งหมด
        org_id = get_current_org_id()
        if org_id:
            org_members = database.get_org_members(org_id)
            notify_targets = [m["username"] for m in org_members
                              if m.get("role") == "admin" and m["username"].lower() != user.lower()]
        else:
            # fallback: system admins ถ้าไม่มี org context
            notify_targets = [a for a in database.get_all_admins() if a.lower() != user.lower()]

        for admin in notify_targets:
            notification_db.add_notification(
                admin,
                "leave_request",
                "คำขอลาหยุดใหม่",
                f"คุณพี่ {user} ได้ส่งคำขอลาหยุด {l_type} ตั้งแต่วันที่ {s_date} ถึง {e_date}",
                "/#admin"
            )
        return jsonify({"ok": True, "id": leave_id})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการส่งคำขอลาหยุดค่ะ"}), 500


@admin_bp.route("/api/leave/my")
@login_required
def api_leave_my():
    user = session.get("user")
    leaves = database.get_user_leaves(user)
    return jsonify({"ok": True, "leaves": leaves})


@admin_bp.route("/api/admin/leave/all")
@admin_required
def api_admin_leave_all():
    leaves = database.get_all_leaves()
    return jsonify({"ok": True, "leaves": leaves})


@admin_bp.route("/api/admin/leave/status", methods=["POST"])
@admin_required
def api_admin_leave_status():
    admin_user = session.get("user")
    data = request.get_json()
    leave_id = data.get("id")
    status = data.get("status") # approved/rejected
    note = data.get("note", "")
    
    if not leave_id or status not in ["approved", "rejected"]:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ถูกต้องหรือครบถ้วนค่ะ"}), 400
        
    ok = database.update_leave_status(leave_id, status, admin_user, note)
    if ok:
        leave = database.get_leave_request(leave_id)
        if leave:
            status_text = "อนุมัติ" if status == "approved" else "ปฏิเสธ"
            notification_db.add_notification(
                leave["username"],
                "leave_status",
                f"คำขอลาของคุณได้รับการ{status_text}แล้วค่ะ",
                f"คำขอลาตั้งแต่วันที่ {leave['start_date']} ถึง {leave['end_date']} ได้รับการ{status_text} โดย {admin_user}",
                "/#leave"
            )
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบคำขอลาที่ระบุ"}), 404


@admin_bp.route("/api/leave/comment", methods=["POST"])
@login_required
def api_leave_add_comment():
    user = session.get("user")
    data = request.get_json()
    leave_id = data.get("leave_id")
    comment = data.get("comment", "").strip()
    
    if not leave_id or not comment:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วนค่ะ"}), 400
        
    database.add_leave_comment(leave_id, user, comment)
    
    # Notify other party
    leave = database.get_leave_request(leave_id)
    if leave:
        target = ""
        msg = f"มีข้อความแสดงความคิดเห็นใหม่ในคำขอลา: {comment[:50]}..."
        if user.lower() == leave["username"].lower():
            # User commented -> Notify admins
            admins = database.get_all_admins()
            for admin in admins:
                notification_db.add_notification(admin, "leave_comment", "มีข้อความใหม่เกี่ยวกับคำขอลา", msg, "/#admin")
        else:
            # Admin commented -> Notify user
            notification_db.add_notification(leave["username"], "leave_comment", "มีข้อความใหม่จากผู้ดูแลระบบเกี่ยวกับคำขอลา", msg, "/#leave")
            
    return jsonify({"ok": True})


@admin_bp.route("/api/leave/comments/<int:leave_id>")
@login_required
def api_leave_get_comments(leave_id):
    comments = database.get_leave_comments(leave_id)
    return jsonify({"ok": True, "comments": comments})


@admin_bp.route("/api/lunch/random")
@login_required
def api_lunch_random():
    return jsonify(database.get_random_lunch() or {"name": "ยังไม่มีรายชื่ออาหารในระบบ"})


@admin_bp.route("/api/lunch/all")
@login_required
def api_lunch_all():
    return jsonify(database.get_all_lunch_places())


@admin_bp.route("/api/lunch/add", methods=["POST"])
@login_required
def api_lunch_add():
    data = request.get_json() or {}
    name = data.get("name")
    if not name: return jsonify({"ok": False}), 400
    database.add_lunch_place(name, data.get("type", ""), data.get("location", ""), session.get("user"))
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/notifications/clear_all", methods=["POST"])
@admin_required
def admin_clear_all_notifications_route():
    count = notification_db.admin_clear_all_notifications()
    database.log_event(f"Admin cleared ALL notifications ({count} items)", user=session.get("user"))
    return jsonify({"status": "success", "count": count})


@admin_bp.route("/api/admin/chat/overview", methods=["GET"])
@admin_required
def admin_chat_overview():
    rooms = database.admin_get_all_rooms()
    dm_pairs = database.admin_get_all_dm_pairs()
    return jsonify({"ok": True, "rooms": rooms, "dm_pairs": dm_pairs})


@admin_bp.route("/api/admin/chat/ai", methods=["GET"])
@admin_required
def admin_ai_messages():
    username = request.args.get("username")
    msgs = database.admin_get_all_ai_messages(limit=200)
    if username:
        msgs = [m for m in msgs if m["username"] == username]
    return jsonify({"ok": True, "messages": msgs})


@admin_bp.route("/api/admin/chat/ai/delete/<int:mid>", methods=["DELETE", "POST"])
@admin_required
def admin_delete_ai_msg(mid):
    ok = database.delete_message(mid, username="Admin")
    return jsonify({"ok": ok})


@admin_bp.route("/api/admin/chat/ai/clear", methods=["POST"])
@admin_required
def admin_clear_ai():
    data = request.get_json(silent=True) or {}
    count = database.admin_clear_ai_chat(username=data.get("username"))
    return jsonify({"ok": True, "deleted": count})


@admin_bp.route("/api/admin/chat/room/<int:room_id>", methods=["GET"])
@admin_required
def admin_room_messages(room_id):
    msgs = database.admin_get_room_messages(room_id)
    return jsonify({"ok": True, "messages": msgs})


@admin_bp.route("/api/admin/chat/room/delete/<int:mid>", methods=["DELETE", "POST"])
@admin_required
def admin_delete_room_msg(mid):
    ok = database.admin_delete_room_message(mid)
    return jsonify({"ok": ok})


@admin_bp.route("/api/admin/chat/room/<int:room_id>/clear", methods=["POST"])
@admin_required
def admin_clear_room(room_id):
    count = database.admin_clear_room_messages(room_id)
    return jsonify({"ok": True, "deleted": count})


@admin_bp.route("/api/admin/chat/dm", methods=["GET"])
@admin_required
def admin_dm_messages():
    u1 = request.args.get("user1", "")
    u2 = request.args.get("user2", "")
    if not u1 or not u2:
        return jsonify({"ok": False, "error": "user1 and user2 required"}), 400
    msgs = database.admin_get_dm_messages(u1, u2)
    return jsonify({"ok": True, "messages": msgs})


@admin_bp.route("/api/admin/chat/dm/delete/<int:mid>", methods=["DELETE", "POST"])
@admin_required
def admin_delete_dm_msg(mid):
    ok = database.admin_delete_dm_message(mid)
    return jsonify({"ok": ok})


@admin_bp.route("/api/admin/chat/dm/clear", methods=["POST"])
@admin_required
def admin_clear_dm_route():
    data = request.get_json(silent=True) or {}
    u1 = data.get("user1", "")
    u2 = data.get("user2", "")
    if not u1 or not u2:
        return jsonify({"ok": False, "error": "user1 and user2 required"}), 400
    count = database.admin_clear_dm(u1, u2)
    return jsonify({"ok": True, "deleted": count})


@admin_bp.route("/api/admin/users/<username>/toggle-active", methods=["POST"])
@admin_required
def admin_toggle_active_route(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถปิดบัญชี Admin ได้"}), 400
    settings = database.get_user_setting(username)
    new_active = not settings.get("is_active", True)
    database.admin_update_user(username, is_active=new_active)
    admin_user = session.get("user", "Admin")
    status_th = "เปิด" if new_active else "ปิด"
    database.log_event(f"Admin {status_th}การใช้งาน user: {username}", user=admin_user)
    return jsonify({"ok": True, "is_active": new_active})


@admin_bp.route("/api/admin/settings", methods=["GET"])
@admin_required
def get_admin_settings():
    settings = settings_manager.get_settings()
    return jsonify({"ok": True, "settings": settings})


@admin_bp.route("/api/admin/settings", methods=["POST"])
@admin_required
def update_admin_settings():
    data = request.json or {}
    # Validate keys if necessary, but here we allow general .env updates
    success = settings_manager.update_settings(data)
    if success:
        database.log_event("อัปเดตการตั้งค่าระบบผ่านหน้าเว็บ", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่สามารถอัปเดตการตั้งค่าได้"}), 500


def superadmin_required(f):
    """Only master Admin user (or users listed in SUPERADMIN_USERS env) can access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อน"}), 401
        user = session.get("user")
        sa_users = set(filter(None, os.environ.get("SUPERADMIN_USERS", "Admin").split(",")))
        if user not in sa_users:
            return jsonify({"ok": False, "error": "Super Admin เท่านั้น"}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/admin/super")
@login_required
def superadmin_page():
    user = session.get("user")
    sa_users = set(filter(None, os.environ.get("SUPERADMIN_USERS", "Admin").split(",")))
    if user not in sa_users:
        return "403 — Super Admin Access Only", 403
    return render_template("superadmin.html")


@admin_bp.route("/api/superadmin/overview")
@superadmin_required
def superadmin_overview():
    stats = database.superadmin_get_system_stats()
    orgs = database.get_all_orgs_with_stats()
    plan_prices = {p: billing.PLANS[p]["price_thb"] for p in billing.PLANS}
    mrr = sum(plan_prices.get(o["plan"] or "free", 0) for o in orgs)
    paying = sum(1 for o in orgs if (o["plan"] or "free") != "free")
    uptime_sec = int(time.time() - _APP_START_TIME)
    return jsonify({
        "ok": True,
        "stats": stats,
        "mrr": mrr,
        "paying_orgs": paying,
        "total_orgs": len(orgs),
        "uptime_seconds": uptime_sec,
        "ai_provider": os.environ.get("AI_PROVIDER", "groq"),
        "version": VERSION,
    })


@admin_bp.route("/api/superadmin/orgs")
@superadmin_required
def superadmin_orgs():
    orgs = database.get_all_orgs_with_stats()
    for o in orgs:
        o["plan_config"] = billing.get_plan_config(o["plan"] or "free")
        o["effective_plan"] = billing.get_effective_plan(o["id"])
    return jsonify({"ok": True, "orgs": orgs})


@admin_bp.route("/api/superadmin/org/<int:org_id>/members")
@superadmin_required
def superadmin_org_members(org_id):
    members = database.get_org_members(org_id)
    return jsonify({"ok": True, "members": members})


@admin_bp.route("/api/superadmin/org/<int:org_id>/set-plan", methods=["POST"])
@superadmin_required
def superadmin_set_plan(org_id):
    data = request.get_json() or {}
    plan = data.get("plan", "free")
    expires = data.get("expires_at")
    try:
        billing.set_org_plan(org_id, plan, expires)
        database.log_event(f"[SuperAdmin] Set org {org_id} → plan={plan}", user=session.get("user"), org_id=org_id)
        return jsonify({"ok": True, "plan": plan})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@admin_bp.route("/api/superadmin/org/<int:org_id>", methods=["DELETE"])
@superadmin_required
def superadmin_delete_org(org_id):
    if org_id == 1:
        return jsonify({"ok": False, "error": "ไม่สามารถลบ org หลักได้"}), 400
    ok = database.superadmin_delete_org(org_id)
    if ok:
        database.log_event(f"[SuperAdmin] Deleted org {org_id}", user=session.get("user"), org_id=org_id)
    return jsonify({"ok": ok})


@admin_bp.route("/api/superadmin/users")
@superadmin_required
def superadmin_users():
    users = database.superadmin_get_all_users()
    return jsonify({"ok": True, "users": users})


@admin_bp.route("/api/superadmin/user/<username>/reset-password", methods=["POST"])
@superadmin_required
def superadmin_reset_password(username):
    data = request.get_json() or {}
    new_pw = data.get("password", "").strip()
    if len(new_pw) < 6:
        return jsonify({"ok": False, "error": "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"}), 400
    database.admin_reset_user_password(username, new_pw)
    database.log_event(f"[SuperAdmin] Reset password for {username}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/superadmin/user/<username>/toggle-active", methods=["POST"])
@superadmin_required
def superadmin_toggle_active(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถปิด Admin ได้"}), 400
    settings = database.get_user_setting(username)
    new_state = not settings.get("is_active", True)
    database.admin_update_user(username, is_active=new_state)
    database.log_event(f"[SuperAdmin] {'Activated' if new_state else 'Deactivated'} user {username}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True, "is_active": new_state})


@admin_bp.route("/api/superadmin/user/<username>/set-role", methods=["POST"])
@superadmin_required
def superadmin_set_role(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถเปลี่ยน role Admin ได้"}), 400
    data = request.get_json() or {}
    role = data.get("role", "user")
    if role not in ("user", "admin"):
        return jsonify({"ok": False, "error": "role ไม่ถูกต้อง"}), 400
    database.admin_update_user(username, role=role)
    database.log_event(f"[SuperAdmin] Set role {username} → {role}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True, "role": role})


@admin_bp.route("/api/superadmin/user/<username>", methods=["DELETE"])
@superadmin_required
def superadmin_delete_user(username):
    if username == "Admin":
        return jsonify({"ok": False, "error": "ไม่สามารถลบ Admin ได้"}), 400
    ok = database.admin_delete_user_complete(username)
    if ok:
        database.log_event(f"[SuperAdmin] Deleted user {username}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": ok})


@admin_bp.route("/api/superadmin/user/<username>/notes", methods=["POST"])
@superadmin_required
def superadmin_update_notes(username):
    data = request.get_json() or {}
    notes = data.get("notes", "")
    database.admin_update_user(username, notes=notes)
    return jsonify({"ok": True})


@admin_bp.route("/api/superadmin/system")
@superadmin_required
def superadmin_system():
    env_keys = ["AI_PROVIDER", "GROQ_API_KEY", "GEMINI_API_KEY", "STRIPE_SECRET_KEY",
                "LINE_CHANNEL_ACCESS_TOKEN", "FLASK_SECRET_KEY", "BASE_URL",
                "SUPERADMIN_USERS", "SENTRY_DSN", "REDIS_URL"]
    env_info = {}
    for k in env_keys:
        val = os.environ.get(k, "")
        if val:
            env_info[k] = val[:4] + "****" + val[-2:] if len(val) > 8 else "****"
        else:
            env_info[k] = "(ไม่ได้ตั้งค่า)"
    kb_files = rag_engine.list_files()
    return jsonify({
        "ok": True,
        "env": env_info,
        "kb_total_files": len(kb_files),
        "uptime_seconds": int(time.time() - _APP_START_TIME),
        "version": VERSION,
        "python_version": __import__("sys").version,
    })


@admin_bp.route("/api/superadmin/logs")
@superadmin_required
def superadmin_logs():
    limit = int(request.args.get("limit", 100))
    events = database.get_events(limit=limit)
    return jsonify({"ok": True, "events": events})


@admin_bp.route("/api/superadmin/org/create", methods=["POST"])
@superadmin_required
def superadmin_create_org():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    plan = data.get("plan", "free")
    if not name:
        return jsonify({"ok": False, "error": "กรุณากรอกชื่อองค์กร"}), 400
    try:
        result = database.create_organization(name=name, owner_username=session.get("user"))
        org_id = result[0] if isinstance(result, (tuple, list)) else result
        slug = result[1] if isinstance(result, (tuple, list)) and len(result) > 1 else ""
        if plan != "free":
            billing.set_org_plan(org_id, plan)
        database.log_event(f"[SuperAdmin] Created org '{name}' id={org_id}", user=session.get("user"), org_id=org_id)
        return jsonify({"ok": True, "org_id": org_id, "slug": slug})
    except Exception as e:
        logger.error(f"[SuperAdmin create org] {e}")
        return jsonify({"ok": False, "error": "ชื่อองค์กรนี้มีอยู่แล้ว หรือเกิดข้อผิดพลาด กรุณาลองใหม่"}), 400


@admin_bp.route("/api/superadmin/user/create", methods=["POST"])
@superadmin_required
def superadmin_create_user():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    display_name = (data.get("display_name") or username).strip()
    role = data.get("role", "user")
    if not username or not password:
        return jsonify({"ok": False, "error": "กรุณากรอก username และ password"}), 400
    if len(password) < 8:
        return jsonify({"ok": False, "error": "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"}), 400
    if role not in ("user", "admin"):
        role = "user"
    ok = database.admin_create_user(username=username, password=password, role=role, display_name=display_name)
    if not ok:
        return jsonify({"ok": False, "error": "Username นี้มีอยู่แล้ว"}), 400
    database.log_event(f"[SuperAdmin] Created user '{username}' role={role}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/superadmin/billing")
@superadmin_required
def superadmin_billing():
    orgs = database.get_all_orgs_with_stats()
    plan_prices = {p: billing.PLANS[p]["price_thb"] for p in billing.PLANS}
    revenue_by_plan = {}
    for p in billing.PLANS:
        count = sum(1 for o in orgs if (o.get("plan") or "free") == p)
        revenue_by_plan[p] = {
            "count": count,
            "price_thb": plan_prices.get(p, 0),
            "total": count * plan_prices.get(p, 0),
            "name": billing.PLANS[p].get("name", p),
        }
    paying_list = [
        {
            "id": o["id"], "name": o["name"],
            "plan": o.get("plan") or "free",
            "price_thb": plan_prices.get(o.get("plan") or "free", 0),
            "member_count": o.get("member_count", 0),
            "plan_expires_at": o.get("plan_expires_at"),
        }
        for o in orgs if (o.get("plan") or "free") != "free"
    ]
    mrr = sum(plan_prices.get(o.get("plan") or "free", 0) for o in orgs)
    return jsonify({"ok": True, "mrr": mrr, "revenue_by_plan": revenue_by_plan, "paying_orgs": paying_list})


@admin_bp.route("/api/superadmin/broadcast", methods=["POST"])
@superadmin_required
def superadmin_broadcast():
    data = request.get_json() or {}
    title = (data.get("title") or "ประกาศจากผู้ดูแลระบบ").strip()
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "กรุณากรอกข้อความ"}), 400
    database.log_event(f"[BROADCAST]{title}{message}", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/superadmin/broadcasts")
@superadmin_required
def superadmin_broadcasts():
    events = database.get_events(limit=500)
    broadcasts = []
    for e in events:
        text = e.get("event") or e.get("event_text") or ""
        if text.startswith("[BROADCAST]\x01"):
            parts = text[len("[BROADCAST]\x01"):].split("\x01", 1)
            broadcasts.append({
                "title": parts[0] if parts else "ประกาศ",
                "message": parts[1] if len(parts) > 1 else "",
                "user": e.get("user", "—"),
                "time": e.get("time") or e.get("timestamp", ""),
            })
    return jsonify({"ok": True, "broadcasts": broadcasts})


@admin_bp.route("/api/superadmin/system/clear-cache", methods=["POST"])
@superadmin_required
def superadmin_clear_cache():
    try:
        rag_engine.clear_cache()
    except Exception:
        pass
    database.log_event("[SuperAdmin] Cleared RAG/KB cache", user=session.get("user"), org_id=get_current_org_id())
    return jsonify({"ok": True})


@admin_bp.route("/api/superadmin/system/kb-cleanup", methods=["POST"])
@superadmin_required
def superadmin_kb_cleanup():
    """ล้างไฟล์ KB ที่ค้างสถานะ 'processing' นานเกิน threshold"""
    minutes = int(request.get_json(force=True).get("minutes", 30))
    cleaned = rag_engine.cleanup_stale_processing(max_age_minutes=minutes)
    database.log_event(f"[SuperAdmin] KB cleanup: {cleaned} stale files fixed", user=session.get("user"))
    return jsonify({"ok": True, "cleaned": cleaned})


@admin_bp.route("/api/superadmin/system/backup", methods=["POST"])
@superadmin_required
def superadmin_trigger_backup():
    """Trigger DB backup ทันที"""
    try:
        _backup_sqlite()
        database.log_event("[SuperAdmin] Manual DB backup triggered", user=session.get("user"))
        return jsonify({"ok": True, "message": "Backup สำเร็จ"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/superadmin/system/backups")
@superadmin_required
def superadmin_list_backups():
    """รายการไฟล์ backup ทั้งหมด"""
    import glob as _glob
    db_path = os.environ.get("DB_PATH", "chat_history.db")
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    files = sorted(_glob.glob(os.path.join(backup_dir, "chat_history_*.db")), reverse=True)
    result = []
    for f in files[:20]:
        try:
            stat = os.stat(f)
            result.append({
                "name": os.path.basename(f),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        except Exception:
            pass
    return jsonify({"ok": True, "backups": result, "backup_dir": backup_dir})


@admin_bp.route("/api/superadmin/system/scheduler")
@superadmin_required
def superadmin_scheduler_status():
    """ดูสถานะ APScheduler jobs ทั้งหมด"""
    try:
        from app_server import _scheduler
        jobs = []
        for job in _scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name or job.id,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
                "running": job.next_run_time is not None,
            })
        return jsonify({"ok": True, "jobs": jobs, "running": _scheduler.running})
    except Exception as e:
        return jsonify({"ok": True, "jobs": [], "error": str(e)})


@admin_bp.route("/api/superadmin/system/send-expiry-reminders", methods=["POST"])
@superadmin_required
def superadmin_send_expiry_reminders():
    """Force-trigger plan expiry reminders"""
    try:
        check_expiring_plans()
        database.log_event("[SuperAdmin] Force-sent expiry reminders", user=session.get("user"))
        return jsonify({"ok": True, "message": "ส่ง reminder เรียบร้อย"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/superadmin/system/health")
@superadmin_required
def superadmin_health():
    """System health: CPU, memory, disk"""
    import sys, shutil
    result = {"ok": True}
    try:
        import psutil
        result["cpu_pct"] = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        result["mem_total_mb"] = round(mem.total / 1024 / 1024)
        result["mem_used_mb"]  = round(mem.used  / 1024 / 1024)
        result["mem_pct"] = mem.percent
        disk = shutil.disk_usage("/")
        result["disk_total_gb"] = round(disk.total / 1024 / 1024 / 1024, 1)
        result["disk_used_gb"]  = round(disk.used  / 1024 / 1024 / 1024, 1)
        result["disk_pct"] = round(disk.used / disk.total * 100, 1)
    except ImportError:
        result["psutil"] = "not installed — pip install psutil"
    except Exception as e:
        result["error"] = str(e)
    return jsonify(result)


@admin_bp.route("/api/superadmin/impersonate/<username>", methods=["POST"])
@superadmin_required
def superadmin_impersonate(username):
    """Login as another user (for debugging). Logs the action."""
    me = session.get("user")
    settings = database.get_user_setting(username)
    if not settings:
        return jsonify({"ok": False, "error": "ไม่พบผู้ใช้"}), 404
    if not settings.get("is_active", 1):
        return jsonify({"ok": False, "error": "บัญชีนี้ถูกระงับ"}), 403
    database.log_event(f"[SuperAdmin] {me} impersonated user '{username}'", user=me)
    # Store original admin in session for "exit impersonation"
    original_admin = me
    session.clear()
    session.permanent = True
    session["user"] = username
    session["role"] = settings.get("role", "user")
    session["_impersonated_by"] = original_admin
    from routes.shared import _set_session_org
    _set_session_org(username)
    return jsonify({"ok": True, "message": f"กำลัง login เป็น @{username} — ปิดหน้าต่างนี้แล้วไปหน้าหลัก"})


@admin_bp.route("/api/superadmin/exit-impersonate", methods=["POST"])
@login_required
def superadmin_exit_impersonate():
    """ออกจาก impersonation และกลับเป็น superadmin เดิม"""
    original = session.get("_impersonated_by")
    if not original:
        return jsonify({"ok": False, "error": "ไม่ได้อยู่ใน impersonation mode"}), 400
    current = session.get("user")
    session.clear()
    session.permanent = True
    session["user"] = original
    _sa_settings = database.get_user_setting(original)
    session["role"] = _sa_settings.get("role", "admin") if _sa_settings else "admin"
    database.log_event(f"[SuperAdmin] Exited impersonation of '{current}', restored '{original}'", user=original)
    return jsonify({"ok": True, "message": f"กลับเป็น @{original} แล้ว"})


@admin_bp.route("/api/superadmin/broadcast-targeted", methods=["POST"])
@superadmin_required
def superadmin_broadcast_targeted():
    """ส่ง broadcast ไปเฉพาะ org หรือ plan ที่เลือก"""
    data = request.get_json(force=True) or {}
    title   = (data.get("title") or "ประกาศจากผู้ดูแลระบบ").strip()
    message = (data.get("message") or "").strip()
    target_org_id = data.get("org_id")    # int หรือ None
    target_plan   = data.get("plan")      # "free"/"pro"/"business" หรือ None
    if not message:
        return jsonify({"ok": False, "error": "กรุณากรอกข้อความ"}), 400

    orgs = database.get_all_orgs_with_stats()
    notify_count = 0
    for org in orgs:
        if target_org_id and org["id"] != int(target_org_id):
            continue
        if target_plan and (org.get("plan") or "free") != target_plan:
            continue
        usernames = database.get_all_usernames(org_id=org["id"])
        for uname in usernames:
            notification_db.add_notification(uname, "broadcast", title, message, "/")
        notify_count += len(usernames)

    target_desc = f"org_id={target_org_id}" if target_org_id else f"plan={target_plan}" if target_plan else "all"
    database.log_event(f"[SuperAdmin] Targeted broadcast to {target_desc}: {notify_count} users", user=session.get("user"))
    return jsonify({"ok": True, "notified": notify_count})


@admin_bp.route("/api/superadmin/db/tables")
@superadmin_required
def superadmin_db_tables():
    import sqlite3
    try:
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
        
        table_info = []
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{t}`")
            count = cursor.fetchone()[0]
            table_info.append({"name": t, "count": count})
            
        conn.close()
        return jsonify({"ok": True, "tables": table_info})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/superadmin/db/table/<table_name>")
@superadmin_required
def superadmin_db_table_data(table_name):
    import sqlite3
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    q = request.args.get("q", "").strip()
    
    try:
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get schema columns
        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
        cols = [{"name": r["name"], "type": r["type"], "pk": r["pk"]} for r in cursor.fetchall()]
        col_names = [c["name"] for c in cols]
        
        # Search query if specified
        where_clause = ""
        params = []
        if q and col_names:
            where_conditions = []
            for col in col_names:
                where_conditions.append(f"`{col}` LIKE ?")
                params.append(f"%{q}%")
            where_clause = " WHERE " + " OR ".join(where_conditions)
            
        # Count total rows
        count_query = f"SELECT COUNT(*) FROM `{table_name}`" + where_clause
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get rows
        select_query = f"SELECT * FROM `{table_name}`" + where_clause + " LIMIT ? OFFSET ?"
        cursor.execute(select_query, params + [limit, offset])
        rows = [dict(r) for r in cursor.fetchall()]
        
        conn.close()
        return jsonify({"ok": True, "columns": cols, "rows": rows, "total": total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/superadmin/db/table/<table_name>/row", methods=["POST"])
@superadmin_required
def superadmin_db_table_insert(table_name):
    import sqlite3
    data = request.get_json() or {}
    if not data:
        return jsonify({"ok": False, "error": "ไม่มีข้อมูลส่งมา"}), 400
        
    try:
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()
        
        cols = list(data.keys())
        placeholders = [f":" + c for c in cols]
        
        query = f"INSERT INTO `{table_name}` (" + ", ".join([f"`{c}`" for c in cols]) + ") VALUES (" + ", ".join(placeholders) + ")"
        cursor.execute(query, data)
        conn.commit()
        conn.close()
        database.log_event(f"[SuperAdmin] Inserted row into {table_name}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/superadmin/db/table/<table_name>/row/update", methods=["POST"])
@superadmin_required
def superadmin_db_table_update(table_name):
    import sqlite3
    data = request.get_json() or {}
    pk_cols = data.get("_pk_cols", {})  # e.g. {"id": 5} or {"username": "mex"}
    fields = data.get("_fields", {})    # New column values
    
    if not pk_cols or not fields:
        return jsonify({"ok": False, "error": "_pk_cols and _fields required"}), 400
        
    try:
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()
        
        # Build UPDATE query
        set_parts = []
        params = []
        for col, val in fields.items():
            set_parts.append(f"`{col}` = ?")
            params.append(val)
            
        where_parts = []
        for col, val in pk_cols.items():
            where_parts.append(f"`{col}` = ?")
            params.append(val)
            
        query = f"UPDATE `{table_name}` SET " + ", ".join(set_parts) + " WHERE " + " AND ".join(where_parts)
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        database.log_event(f"[SuperAdmin] Updated row in {table_name} where {pk_cols}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/superadmin/db/table/<table_name>/row/delete", methods=["POST"])
@superadmin_required
def superadmin_db_table_delete(table_name):
    import sqlite3
    pk_cols = request.get_json() or {} # e.g. {"id": 5}
    if not pk_cols:
        return jsonify({"ok": False, "error": "Primary key columns are required for deletion"}), 400
        
    try:
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()
        
        where_parts = []
        params = []
        for col, val in pk_cols.items():
            where_parts.append(f"`{col}` = ?")
            params.append(val)
            
        query = f"DELETE FROM `{table_name}` WHERE " + " AND ".join(where_parts)
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        database.log_event(f"[SuperAdmin] Deleted row from {table_name} where {pk_cols}", user=session.get("user"), org_id=get_current_org_id())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/superadmin/db/query", methods=["POST"])
@superadmin_required
def superadmin_db_query():
    import sqlite3
    data = request.get_json() or {}
    sql = (data.get("sql") or "").strip()
    if not sql:
        return jsonify({"ok": False, "error": "โปรดกรอก SQL query ที่ต้องการสั่งงาน"}), 400
        
    try:
        conn = sqlite3.connect(database.DB_PATH)
        # Safe limit for superadmin SELECT queries so they don't crash memory
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        # Check if query returns rows (like SELECT or PRAGMA)
        is_select = cursor.description is not None
        
        if is_select:
            cols = [desc[0] for desc in cursor.description]
            # Fetch up to 500 records max for safety
            rows = cursor.fetchmany(500)
            rows_dict = [dict(r) for r in rows]
            conn.close()
            database.log_event(f"[SuperAdmin] Executed SQL SELECT: {sql[:100]}...", user=session.get("user"), org_id=get_current_org_id())
            return jsonify({
                "ok": True, 
                "is_select": True, 
                "columns": cols, 
                "rows": rows_dict, 
                "total": len(rows_dict),
                "truncated": len(rows_dict) == 500
            })
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            database.log_event(f"[SuperAdmin] Executed SQL WRITE: {sql[:100]}...", user=session.get("user"), org_id=get_current_org_id())
            return jsonify({
                "ok": True, 
                "is_select": False, 
                "affected_rows": affected
            })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@admin_bp.route('/edit_expense_form', methods=['GET', 'POST'])
@login_required
def edit_expense_form():
    sheet = request.args.get('sheet')
    row_str = request.args.get('row')

    # Always use session context — never allow caller to override org/user via URL params
    org_id = session.get('org_id')
    username = session.get('user')

    if org_id or username:
        try:
            org_id_int = int(org_id) if org_id else None
        except (ValueError, TypeError):
            org_id_int = None
        google_manager.set_context(username=username, org_id=org_id_int)
    
    if not sheet or not row_str:
        return "❌ ข้อมูลไม่ครบถ้วน (กรุณาระบุ sheet และ row)", 400
        
    try:
        row = int(row_str)
    except ValueError:
        return "❌ เลขแถวไม่ถูกต้อง", 400
        
    if request.method == 'POST':
        # Handle form submission
        updated_data = {}
        for key, val in request.form.items():
            if key.startswith("field_"):
                col_name = key.replace("field_", "")
                
                # Format Date back to DD/MM/YYYY
                if "วันที่" in col_name and val:
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(val, "%Y-%m-%d")
                        val = dt.strftime("%d/%m/%Y")
                    except Exception:
                        pass
                
                updated_data[col_name] = val
                
        # Update each field in the spreadsheet
        for col_name, new_val in updated_data.items():
            google_manager.update_expense(sheet, row, col_name, new_val)
            
        # Re-run reconciliation
        google_manager.auto_reconcile_internal()
        
        # Breathtaking Success Page with Custom Canvas Confetti
        return """
        <!DOCTYPE html>
        <html lang="th" class="h-full">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>บันทึกสำเร็จ ✨</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://unpkg.com/lucide@latest"></script>
            <script>
                tailwind.config = {
                    theme: {
                        extend: {
                            colors: {
                                brand: { 50: '#f0f5ff', 600: '#2563eb', 700: '#1d4ed8' },
                                surface: { 900: '#0f172a', 950: '#020617' }
                            }
                        }
                    }
                }
            </script>
            <style>
                body {
                    font-family: 'Inter', 'Sarabun', sans-serif;
                }
            </style>
        </head>
        <body class="bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-white min-h-screen flex flex-col justify-center items-center overflow-hidden p-6 relative transition-colors duration-300">
            <script>
                const theme = localStorage.getItem('theme') || 'auto';
                const isDark = theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                document.documentElement.classList.toggle('dark', isDark);
            </script>
            <canvas id="confettiCanvas" class="absolute inset-0 w-full h-full pointer-events-none z-50"></canvas>

            <div class="max-w-md w-full bg-white dark:bg-surface-900 border border-surface-200 dark:border-white/10 p-10 rounded-[2.5rem] shadow-2xl text-center relative overflow-hidden transform scale-95 animate-[popIn_0.6s_cubic-bezier(0.16,1,0.3,1)_forwards] z-10">
                <div class="absolute -top-24 -left-24 w-48 h-48 bg-brand-600/10 rounded-full blur-3xl pointer-events-none"></div>
                
                <div class="w-24 h-24 bg-gradient-to-tr from-brand-600 to-blue-400 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-xl shadow-brand-600/20 relative animate-[bounceIn_0.8s_both]">
                    <i data-lucide="check" class="w-12 h-12 text-white relative z-10 stroke-[3]"></i>
                </div>

                <h1 class="text-3xl font-black tracking-tight text-white mb-4">บันทึกเรียบร้อย!</h1>
                <p class="text-slate-400 text-sm leading-relaxed mb-10 font-medium">
                    อัปเดตข้อมูลและประมวลผลการกระทบยอด<br/>บน Google Sheets เรียบร้อยแล้วค่ะ 💖
                </p>

                <div class="flex flex-col items-center justify-center mb-10 relative">
                    <svg class="w-14 h-14 transform -rotate-90">
                        <circle cx="28" cy="28" r="24" stroke="rgba(255,255,255,0.05)" stroke-width="4" fill="transparent" />
                        <circle id="countdownBar" cx="28" cy="28" r="24" stroke="#2563eb" stroke-width="4" fill="transparent" 
                                stroke-dasharray="150.8" stroke-dashoffset="0" class="transition-all duration-1000 ease-linear" />
                    </svg>
                    <span id="countdownText" class="absolute text-sm font-black text-brand-600">3</span>
                </div>

                <button class="w-full py-4 px-6 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 text-white font-bold transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2" onclick="window.close();">
                    <i data-lucide="x-circle" class="w-5 h-5"></i>
                    <span>ปิดหน้าต่างนี้</span>
                </button>
            </div>

            <script>
                lucide.createIcons();
                const canvas = document.getElementById('confettiCanvas');
                const ctx = canvas.getContext('2d');
                function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
                window.addEventListener('resize', resizeCanvas);
                resizeCanvas();
                let particles = [];
                const colors = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#ffffff'];
                class Particle {
                    constructor() {
                        this.x = canvas.width / 2; this.y = canvas.height / 2;
                        this.size = Math.random() * 8 + 4;
                        this.speedX = Math.random() * 12 - 6; this.speedY = Math.random() * -15 - 5;
                        this.color = colors[Math.floor(Math.random() * colors.length)];
                        this.gravity = 0.4; this.rotation = Math.random() * 360; this.rotationSpeed = Math.random() * 10 - 5;
                    }
                    update() { this.speedY += this.gravity; this.x += this.speedX; this.y += this.speedY; this.rotation += this.rotationSpeed; }
                    draw() {
                        ctx.save(); ctx.translate(this.x, this.y); ctx.rotate(this.rotation * Math.PI / 180);
                        ctx.fillStyle = this.color; ctx.fillRect(-this.size/2, -this.size/2, this.size, this.size); ctx.restore();
                    }
                }
                for (let i = 0; i < 100; i++) particles.push(new Particle());
                function animate() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    particles.forEach((p, idx) => { p.update(); p.draw(); if (p.y > canvas.height) particles.splice(idx, 1); });
                    if (particles.length > 0) requestAnimationFrame(animate);
                }
                animate();
                let timeLeft = 3; const totalBar = 150.8;
                const countdownBar = document.getElementById('countdownBar');
                const countdownText = document.getElementById('countdownText');
                const timer = setInterval(() => {
                    timeLeft--;
                    if (timeLeft >= 0) {
                        countdownText.innerText = timeLeft;
                        const offset = totalBar - (timeLeft / 3) * totalBar;
                        countdownBar.style.strokeDashoffset = offset;
                    }
                    if (timeLeft <= 0) { clearInterval(timer); window.close(); }
                }, 1000);
            </script>
            <style>
                @keyframes popIn { from { opacity: 0; transform: translateY(30px) scale(0.9); } to { opacity: 1; transform: translateY(0) scale(1); } }
                @keyframes bounceIn { 0% { transform: scale(0.3); opacity: 0; } 50% { transform: scale(1.05); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
            </style>
        </body>
        </html>
        """
        
    try:
        # Fetch current values and headers
        headers_res = google_manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=google_manager.spreadsheet_id, range=f"'{sheet}'!A1:Z1"
        ).execute()
        headers = headers_res.get('values', [[]])[0]
        
        row_res = google_manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=google_manager.spreadsheet_id, range=f"'{sheet}'!A{row}:Z{row}"
        ).execute()
        row_data = row_res.get('values', [[]])[0]
        
        # Prepare inputs list
        inputs_html = ""
        for i, header in enumerate(headers):
            if not header.strip():
                continue
                
            val = row_data[i] if i < len(row_data) else ""
            is_readonly = ""
            input_type = "text"
            label_suffix = ""
            icon_name = "edit-3"
            
            h_lower = header.lower()
            if "วันที่" in h_lower:
                input_type = "date"
                icon_name = "calendar"
                try:
                    parts = val.strip().split('/')
                    if len(parts) == 3:
                        day = int(parts[0])
                        month = int(parts[1])
                        year = int(parts[2])
                        if year < 100: year += 2000
                        val = f"{year:04d}-{month:02d}-{day:02d}"
                except Exception:
                    pass
            elif "จำนวน" in h_lower or "สุทธิ" in h_lower or "เงิน" in h_lower or "ยอด" in h_lower or "ภาษี" in h_lower or "ราคา" in h_lower:
                input_type = "number"
                icon_name = "banknote"
                val = str(val).replace(",", "").replace("฿", "").strip()
            elif "ผู้" in h_lower or "ร้าน" in h_lower or "คู่ค้า" in h_lower:
                icon_name = "store"
            elif "ลิงก์" in h_lower or "ไฟล์" in h_lower or "url" in h_lower or "id" in h_lower:
                icon_name = "lock"
                is_readonly = "readonly"
                label_suffix = " 🔒"
                
            if "บันทึก" in h_lower or "รายละเอียด" in h_lower or "หมายเหตุ" in h_lower:
                inputs_html += f'''
                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-500 px-1 flex items-center gap-2">
                        <i data-lucide="{icon_name}" class="w-3.5 h-3.5"></i> {header}{label_suffix}
                    </label>
                    <textarea name="field_{header}" rows="3" 
                        class="w-full bg-white dark:bg-surface-950 border border-surface-200 dark:border-surface-800 rounded-2xl p-4 text-sm focus:border-brand-600 focus:ring-4 focus:ring-brand-600/10 outline-none transition-all resize-none" 
                        placeholder="กรอกข้อมูล {header}...">{val}</textarea>
                </div>
                '''
            else:
                extra_attrs = ""
                helper_html = ""
                if input_type == "number":
                    extra_attrs = 'oninput="formatLiveCurrency(this)"'
                    helper_html = f'<div id="helper_field_{header}" class="text-[11px] text-brand-600 mt-1 font-bold h-4 opacity-0 transition-opacity"></div>'
                
                inputs_html += f'''
                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-500 px-1 flex items-center gap-2">
                        <i data-lucide="{icon_name}" class="w-3.5 h-3.5"></i> {header}{label_suffix}
                    </label>
                    <input type="{input_type}" name="field_{header}" value="{val}" {is_readonly} step="any" {extra_attrs}
                        class="w-full bg-white dark:bg-surface-950 border border-surface-200 dark:border-surface-800 rounded-2xl px-4 py-3 text-sm focus:border-brand-600 focus:ring-4 focus:ring-brand-600/10 outline-none transition-all" 
                        placeholder="กรอกข้อมูล {header}...">
                    {helper_html}
                </div>
                '''
            
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}", 500
        
    return f"""
    <!DOCTYPE html>
    <html lang="th" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📝 แก้ไขข้อมูลเอกสาร</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sarabun:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <script>
            tailwind.config = {{
                darkMode: 'class',
                theme: {{
                    extend: {{
                        colors: {{
                            brand: {{ 600: '#2563eb', 700: '#1d4ed8' }},
                            surface: {{ 50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 800: '#1e293b', 900: '#0f172a', 950: '#020617' }}
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            body {{ font-family: 'Inter', 'Sarabun', sans-serif; }}
            input[type="date"]::-webkit-calendar-picker-indicator {{ filter: invert(0.5); }}
            .dark input[type="date"]::-webkit-calendar-picker-indicator {{ filter: invert(1); }}
        </style>
    </head>
    <body class="bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 min-h-screen py-10 px-4 transition-colors duration-300">
        <div class="max-w-xl mx-auto bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 shadow-2xl rounded-[2.5rem] p-8 md:p-10 relative overflow-hidden">
            <!-- Theme Toggle -->
            <button id="themeToggle" class="absolute top-8 right-8 p-3 bg-surface-50 dark:bg-surface-800 rounded-2xl hover:scale-110 transition-all text-surface-600 dark:text-surface-400 border border-surface-100 dark:border-surface-700 z-10">
                <i data-lucide="moon" id="themeIcon" class="w-5 h-5"></i>
            </button>

            <header class="text-center mb-10">
                <div class="w-16 h-16 bg-brand-600 text-white rounded-2xl shadow-lg flex items-center justify-center mx-auto mb-6 transform -rotate-3">
                    <i data-lucide="file-edit" class="w-8 h-8"></i>
                </div>
                <h1 class="text-3xl font-black tracking-tight mb-2">แก้ไขข้อมูลเอกสาร</h1>
                <p class="text-sm text-slate-500 font-medium uppercase tracking-wider">
                    ชีต: <span class="text-brand-600 font-bold">{sheet}</span> • แถวที่: <span class="text-brand-600 font-bold">{row}</span>
                </p>
            </header>

            <form method="POST" id="editForm" class="space-y-6" onsubmit="return handleFormSubmit(this)">
                {inputs_html}
                
                <button type="submit" id="btnSubmit" class="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-4 px-6 rounded-2xl shadow-lg shadow-brand-600/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 mt-4">
                    <i data-lucide="save" class="w-5 h-5"></i>
                    <span>บันทึกและประมวลผล</span>
                </button>
            </form>
        </div>

        <script>
            lucide.createIcons();

            // Theme Toggle Logic
            const themeToggle = document.getElementById('themeToggle');
            const themeIcon = document.getElementById('themeIcon');
            
            function updateTheme() {{
                const theme = localStorage.getItem('theme') || 'auto';
                const isDark = theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                document.documentElement.classList.toggle('dark', isDark);
                if (themeIcon) themeIcon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }}

            if (themeToggle) {{
                themeToggle.onclick = () => {{
                    const current = localStorage.getItem('theme') || 'auto';
                    let next = 'dark';
                    if (current === 'dark') next = 'light';
                    else if (current === 'light') next = 'auto';
                    localStorage.setItem('theme', next);
                    updateTheme();
                }};
            }}
            updateTheme();

            function formatLiveCurrency(input) {{
                const helper = document.getElementById("helper_" + input.id) || document.getElementById("helper_field_" + input.name.replace('field_', ''));
                if (!helper) return;
                const val = parseFloat(input.value);
                if (isNaN(val)) {{ helper.classList.add('opacity-0'); return; }}
                helper.innerText = "฿ " + val.toLocaleString('th-TH', {{ minimumFractionDigits: 2 }});
                helper.classList.remove('opacity-0');
            }}
            function handleFormSubmit(form) {{
                const btn = document.getElementById('btnSubmit');
                btn.disabled = true;
                btn.classList.add('opacity-70', 'cursor-not-allowed');
                btn.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 animate-spin"></i> <span>กำลังบันทึก...</span>`;
                lucide.createIcons();
                return true;
            }}
            // Auto resize textareas
            document.querySelectorAll('textarea').forEach(t => {{
                t.addEventListener('input', () => {{ t.style.height = 'auto'; t.style.height = t.scrollHeight + 'px'; }});
                t.style.height = t.scrollHeight + 'px';
            }});
        </script>
    </body>
    </html>
    """


def check_expiring_plans():
    """Push LINE reminder to orgs whose PromptPay plan expires in 7 or 1 day."""
    from datetime import datetime, timedelta, timezone as _tz
    import sqlite3 as _sq

    now = datetime.now(_tz.utc)
    conn = _sq.connect(database.DB_PATH)
    conn.row_factory = _sq.Row
    rows = conn.execute(
        "SELECT id, name, plan, plan_expires_at FROM organizations "
        "WHERE plan != 'free' AND plan_expires_at IS NOT NULL"
    ).fetchall()
    conn.close()

    _base = os.environ.get("BASE_URL", "https://openchat.sbs")
    _token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    _headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_token}"}

    for row in rows:
        try:
            exp_dt = datetime.fromisoformat(row["plan_expires_at"])
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=_tz.utc)
            days_left = (exp_dt - now).days
            if days_left not in (7, 1):
                continue
            plan_label = {"pro": "Pro", "business": "Ultra"}.get(row["plan"], row["plan"].title())
            msg = (
                f"แจ้งเตือนค่ะพี่! แพลน {plan_label} ของ '{row['name']}' "
                f"จะหมดอายุใน {days_left} วัน\n\n"
                f"ต่ออายุได้เลยที่:\n{_base}/pricing\n\n"
                f"เพื่อให้น้องพั้นทำงานให้ต่อเนื่องนะคะ"
            )
            groups = database.get_line_groups_for_org(row["id"])
            for g in groups:
                try:
                    requests.post(
                        "https://api.line.me/v2/bot/message/push",
                        headers=_headers,
                        json={"to": g["group_id"], "messages": [{"type": "text", "text": msg}]},
                        timeout=10,
                    )
                    logger.info(f"[ExpiryReminder] Sent {days_left}d warning to group {g['group_id']} (org {row['id']})")
                except Exception as _e:
                    logger.warning(f"[ExpiryReminder] push failed: {_e}")
        except Exception as _e:
            logger.warning(f"[ExpiryReminder] row error: {_e}")


def _backup_sqlite():
    """Hot backup SQLite DB using the built-in backup API (safe during active writes)."""
    import glob as _glob
    db_path = os.environ.get("DB_PATH", "chat_history.db")
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"chat_history_{ts}.db")
    try:
        src = sqlite3.connect(db_path, timeout=10)
        dst = sqlite3.connect(dest)
        src.backup(dst)   # atomic hot backup — safe under concurrent writes
        src.close()
        dst.close()
        logger.info(f"[Backup] SQLite backed up → {dest}")
        # Keep only last 7 backups
        old = sorted(_glob.glob(os.path.join(backup_dir, "chat_history_*.db")))
        for f in old[:-7]:
            os.remove(f)
            logger.info(f"[Backup] Removed old backup: {f}")
    except Exception as _e:
        logger.error(f"[Backup] Failed: {_e}")


def _run_daily_reminders():
    import time as _t
    _t.sleep(3600)  # wait 1h after startup before first check
    while True:
        try:
            check_expiring_plans()
        except Exception as _e:
            logger.warning(f"[ExpiryReminder] check failed: {_e}")
        try:
            _backup_sqlite()
        except Exception as _e:
            logger.warning(f"[Backup] thread error: {_e}")
        _t.sleep(86400)  # every 24h


@admin_bp.route("/api/admin/whitelist", methods=["GET"])
@login_required
def api_admin_get_whitelist():
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    enabled = database.is_whitelist_enabled(org_id)
    emails = database.get_whitelist_emails(org_id)
    return jsonify({"ok": True, "enabled": enabled, "emails": emails})


@admin_bp.route("/api/admin/whitelist/toggle", methods=["POST"])
@login_required
def api_admin_toggle_whitelist():
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    data = request.json
    enabled = data.get("enabled", False)
    database.set_whitelist_status(org_id, enabled)
    return jsonify({"ok": True, "enabled": enabled})


@admin_bp.route("/api/admin/whitelist", methods=["POST"])
@login_required
def api_admin_add_whitelist():
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    data = request.json
    email = data.get("email", "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "อีเมลไม่ถูกต้อง"}), 400
        
    success = database.add_whitelist_email(org_id, email, session.get("user"))
    if success:
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": "อีเมลนี้มีอยู่ในระบบแล้ว"}), 400


@admin_bp.route("/api/admin/whitelist/<email>", methods=["DELETE"])
@login_required
def api_admin_remove_whitelist(email):
    org_id = get_current_org_id()
    if not database.is_org_admin(org_id, session.get("user")):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    
    database.remove_whitelist_email(org_id, email)
    return jsonify({"ok": True})


@admin_bp.route("/api/dashboard/all-expenses", methods=["GET"])
@login_required
@billing.require_feature("financial_dashboard")
def api_dashboard_all_expenses():
    """Fetches and standardizes all expense records from Google Sheets."""
    try:
        _username = session.get("user")
        _us = database.get_user_setting(_username)
        if _us.get("role") != "admin" and not _us.get("can_view_financial"):
            return jsonify({"ok": False, "error": "คุณไม่มีสิทธิ์เข้าถึงแดชบอร์ดรายจ่าย กรุณาติดต่อ Admin"}), 403
        from google_drive_service import google_manager
        username = session.get("user")
        org_id = get_current_org_id()
        google_manager.set_context(username, org_id)

        if not google_manager.sheets_service:
            return jsonify({"ok": False, "error": "ยังไม่ได้เชื่อมต่อ Google Drive/Sheets — กรุณาให้ Admin ขององค์กรเชื่อมต่อ Google ในหน้า 'จัดการองค์กร'"}), 200

        spreadsheet = google_manager.sheets_service.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
        sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]

        all_expenses = []
        target_sheets = ["ใบเสร็จ/ใบกำกับภาษี", "สลิปโอนเงิน", "ใบหัก ณ ที่จ่าย", "บันทึกค่าใช้จ่าย", "peak"]

        def clean_float_val(v):
            if not v or str(v).strip() == '-': return 0.0
            try: return float(str(v).replace(',', '').replace('฿', '').strip())
            except Exception: return 0.0

        for sheet_name in target_sheets:
            if sheet_name not in sheet_titles:
                continue

            try:
                res = google_manager.sheets_service.spreadsheets().values().get(
                    spreadsheetId=google_manager.spreadsheet_id, range=f"'{sheet_name}'!A1:Z"
                ).execute()
                vals = res.get('values', [])
                if not vals or len(vals) <= 1:
                    continue

                header = vals[0]
                h_map = {h.strip().lower(): i for i, h in enumerate(header)}

                def get_col_val(row, name_keys, default=''):
                    for k in name_keys:
                        idx = h_map.get(k.lower())
                        if idx is not None and idx < len(row):
                            val = str(row[idx]).strip()
                            if val != '-':
                                return val
                    return default

                for r_idx, row in enumerate(vals[1:], start=2):
                    date_val = get_col_val(row, ["วันที่ในเอกสาร", "วันที่", "วันที่เอกสาร", "วันที่ใบกำกับฯ (ถ้ามี)", "วันที่บันทึกภาษีซื้อ (ถ้ามี)"], default='-')
                    net_amt = get_col_val(row, ["จำนวนเงินสุทธิ", "จำนวนเงิน", "ยอดชำระ", "ยอดรวมสุทธิ", "สุทธิ", "ยอดรวม", "จำนวนเงินที่ชำระ"], default='0')
                    gross_amt = get_col_val(row, ["ยอดก่อนภาษี", "ก่อนภาษี", "ยอดก่อน vat", "gross_amount", "ราคาต่อหน่วย"], default='0')
                    vat_amt = get_col_val(row, ["VAT", "ภาษีมูลค่าเพิ่ม", "vat_amount", "อัตราภาษี"], default='0')
                    wht_amt = get_col_val(row, ["หัก ณ ที่จ่าย", "ภาษีหัก ณ ที่จ่าย", "จำนวนภาษีที่หัก", "wht_amount", "หัก ณ ที่จ่าย (ถ้ามี)"], default='0')
                    wht_type = get_col_val(row, ["ประเภท หัก ณ ที่จ่าย", "ประเภทเงินได้", "wht_type", "income_type", "ภ.ง.ด. (ถ้ามี)"], default='-')
                    ref_num = get_col_val(row, ["เลขที่อ้างอิง", "อ้างอิงถึง", "ref_number", "เลขที่ใบกำกับฯ (ถ้ามี)"], default='-')
                    merchant = get_col_val(row, ["ผู้ส่ง/ร้านค้า", "ผู้รับเงิน", "ผู้มีหน้าที่หักภาษี (ผู้จ่ายเงิน)", "ผู้ส่ง", "ร้านค้า", "คู่ค้า", "ผู้รับเงิน/คู่ค้า"], default='-')
                    receiver = get_col_val(row, ["ผู้รับ", "ผู้ถูกหักภาษี (ผู้รับเงิน)", "ลูกค้า", "payee"], default='-')
                    details = get_col_val(row, ["รายละเอียด/บันทึกช่วยจำ", "คำอธิบาย", "บันทึกช่วยจำ", "รายละเอียด", "หมายเหตุ", "สรุปจาก AI", "สรุปข้อมูล", "สรุป"], default='-')
                    tax_id = get_col_val(row, ["เลขผู้เสียภาษี", "เลขประจำตัวผู้เสียภาษี", "tax_id", "เลขทะเบียน 13 หลัก"], default='-')
                    address = get_col_val(row, ["ที่อยู่คู่ค้า", "ที่อยู่", "ที่อยู่ผู้ขาย", "address"], default='-')
                    branch = get_col_val(row, ["รหัสสาขา", "สาขา", "branch", "เลขสาขา 5 หลัก"], default='-')
                    link_val = get_col_val(row, ["ลิงก์ไฟล์", "ลิงก์ drive", "file_link"], default='')
                    original_file = get_col_val(row, ["ไฟล์ต้นฉบับ", "ไฟล์อ้างอิง", "original_filename"], default='-')
                    sender_name = get_col_val(row, ["ผู้ส่ง (LINE User)", "line_sender_name"], default='-')
                    status = get_col_val(row, ["สถานะการจ่าย", "สถานะการจ่ายเงิน", "สถานะ", "status"], default='จ่ายแล้ว')
                    batch_id = get_col_val(row, ["รหัสกลุ่ม (batch id)", "batch_id", "รหัสกลุ่ม"], default='-')
                    verification_status = get_col_val(row, ["การตรวจสอบ (wht/qr)", "verification_status", "การตรวจสอบ"], default='-')

                    all_expenses.append({
                        "sheet_name": sheet_name,
                        "row_index": r_idx,
                        "date": date_val,
                        "doc_type": sheet_name,
                        "merchant": merchant,
                        "receiver": receiver,
                        "net_amount": clean_float_val(net_amt),
                        "gross_amount": clean_float_val(gross_amt),
                        "vat_amount": clean_float_val(vat_amt),
                        "wht_amount": clean_float_val(wht_amt),
                        "wht_type": wht_type,
                        "ref_number": ref_num,
                        "details": details,
                        "tax_id": tax_id,
                        "address": address,
                        "branch": branch,
                        "link": link_val,
                        "original_filename": original_file,
                        "line_sender_name": sender_name,
                        "status": status,
                        "batch_id": batch_id,
                        "verification_status": verification_status
                    })
            except Exception as se:
                logger.error(f"Error parsing sheet {sheet_name}: {se}")

        return jsonify({"ok": True, "expenses": all_expenses})
    except Exception as e:
        from google.auth.exceptions import RefreshError
        logger.error(f"Error listing all expenses: {e}")
        if isinstance(e, RefreshError) or 'invalid_grant' in str(e):
            return jsonify({"ok": False, "error": "Token Google หมดอายุ — กรุณาเชื่อมต่อ Google ใหม่"}), 200
        return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการดึงข้อมูล"}), 500


@admin_bp.route("/api/dashboard/update-expense", methods=["POST"])
@login_required
@billing.require_feature("financial_dashboard")
def api_dashboard_update_expense():
    """Updates a set of fields in a specific Google Sheet row dynamically."""
    try:
        from google_drive_service import google_manager
        username = session.get("user")
        org_id = session.get("org_id")
        google_manager.set_context(username, org_id)

        data = request.get_json() or {}
        sheet_name = data.get("sheet_name", "").strip()
        row_index = int(data.get("row_index", 0))
        fields_to_update = data.get("fields", {})

        if not sheet_name or not row_index or not fields_to_update:
            return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400

        # Get current sheet headers
        res = google_manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=google_manager.spreadsheet_id, range=f"'{sheet_name}'!A1:Z1"
        ).execute()
        headers = res.get('values', [[]])[0]

        # Field key to sheet header possibilities mapping
        mapping = {
            "date": ["วันที่ในเอกสาร", "วันที่", "วันที่เอกสาร", "วันที่ใบกำกับฯ (ถ้ามี)", "วันที่บันทึกภาษีซื้อ (ถ้ามี)"],
            "merchant": ["ผู้ส่ง/ร้านค้า", "ผู้รับเงิน", "ผู้มีหน้าที่หักภาษี (ผู้จ่ายเงิน)", "ผู้ส่ง", "ร้านค้า", "คู่ค้า", "ผู้รับเงิน/คู่ค้า"],
            "details": ["รายละเอียด/บันทึกช่วยจำ", "คำอธิบาย", "บันทึกช่วยจำ", "รายละเอียด", "หมายเหตุ", "สรุปจาก AI", "สรุปข้อมูล", "สรุป"],
            "net_amount": ["จำนวนเงินสุทธิ", "จำนวนเงิน", "ยอดชำระ", "ยอดรวมสุทธิ", "สุทธิ", "ยอดรวม", "จำนวนเงินที่ชำระ"],
            "gross_amount": ["ยอดก่อนภาษี", "ก่อนภาษี", "ยอดก่อน vat", "gross_amount", "ราคาต่อหน่วย"],
            "vat_amount": ["VAT", "ภาษีมูลค่าเพิ่ม", "vat_amount", "อัตราภาษี"],
            "wht_amount": ["หัก ณ ที่จ่าย", "ภาษีหัก ณ ที่จ่าย", "จำนวนภาษีที่หัก", "wht_amount", "หัก ณ ที่จ่าย (ถ้ามี)"],
            "wht_type": ["ประเภท หัก ณ ที่จ่าย", "ประเภทเงินได้", "wht_type", "income_type", "ภ.ง.ด. (ถ้ามี)"],
            "ref_number": ["เลขที่อ้างอิง", "อ้างอิงถึง", "ref_number", "เลขที่ใบกำกับฯ (ถ้ามี)"],
            "tax_id": ["เลขผู้เสียภาษี", "เลขประจำตัวผู้เสียภาษี", "tax_id", "เลขทะเบียน 13 หลัก"],
            "address": ["ที่อยู่คู่ค้า", "ที่อยู่", "ที่อยู่ผู้ขาย", "address"],
            "branch": ["รหัสสาขา", "สาขา", "branch", "เลขสาขา 5 หลัก"],
            "line_sender_name": ["ผู้ส่ง (LINE User)", "line_sender_name"],
            "status": ["สถานะการจ่าย", "สถานะการจ่ายเงิน", "สถานะ", "status"]
        }

        # Build cells to update
        data_to_update = []
        for key, new_val in fields_to_update.items():
            candidates = mapping.get(key, [])
            matched_header_idx = -1
            
            for c in candidates:
                for idx, h in enumerate(headers):
                    if c.strip().lower() in h.strip().lower() or h.strip().lower() in c.strip().lower():
                        matched_header_idx = idx
                        break
                if matched_header_idx != -1:
                    break

            if matched_header_idx != -1:
                col_letter = chr(65 + matched_header_idx) if matched_header_idx < 26 else f"A{chr(65 + (matched_header_idx - 26))}"
                cell_range = f"'{sheet_name}'!{col_letter}{row_index}"
                data_to_update.append({
                    'range': cell_range,
                    'values': [[new_val]]
                })

        if not data_to_update:
            return jsonify({"ok": False, "error": "ไม่พบฟิลด์ที่ตรงกับคอลัมน์ของชีตนี้"}), 400

        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data_to_update
        }
        google_manager.sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=google_manager.spreadsheet_id,
            body=body
        ).execute()

        # Re-run reconciliation
        google_manager.auto_reconcile_internal()

        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Error in api_dashboard_update_expense: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถอัปเดตข้อมูลได้ กรุณาลองใหม่"}), 500


@admin_bp.route("/api/dashboard/delete-expense", methods=["POST"])
@login_required
@billing.require_feature("financial_dashboard")
def api_dashboard_delete_expense():
    """Deletes a specific row in Google Sheets."""
    try:
        from google_drive_service import google_manager
        username = session.get("user")
        org_id = session.get("org_id")
        google_manager.set_context(username, org_id)

        data = request.get_json() or {}
        sheet_name = data.get("sheet_name", "").strip()
        row_index = int(data.get("row_index", 0))

        if not sheet_name or not row_index:
            return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400

        # Get sheetId
        spreadsheet = google_manager.sheets_service.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
        
        # If sheet_name is "ใบเสร็จ/ใบกำกับภาษี", try to find matching row in "peak" and delete it
        if sheet_name == "ใบเสร็จ/ใบกำกับภาษี":
            try:
                # 1. Get the row values from "ใบเสร็จ/ใบกำกับภาษี" to extract the file link
                res_row = google_manager.sheets_service.spreadsheets().values().get(
                    spreadsheetId=google_manager.spreadsheet_id,
                    range=f"'{sheet_name}'!A{row_index}:Z{row_index}"
                ).execute()
                row_vals = res_row.get('values', [[]])[0]
                
                # Column T (index 19) is "ลิงก์ไฟล์"
                file_link = None
                if len(row_vals) > 19:
                    file_link = str(row_vals[19]).strip()
                
                if file_link and file_link != '-' and file_link.startswith('http'):
                    # 2. Get all rows in "peak" to find the match
                    res_peak = google_manager.sheets_service.spreadsheets().values().get(
                        spreadsheetId=google_manager.spreadsheet_id,
                        range="'peak'!A1:Z"
                    ).execute()
                    peak_vals = res_peak.get('values', [])
                    
                    if peak_vals and len(peak_vals) > 1:
                        peak_header = peak_vals[0]
                        link_col_idx = -1
                        for idx, h in enumerate(peak_header):
                            if "ลิงก์" in h or "link" in h.lower():
                                link_col_idx = idx
                                break
                        
                        if link_col_idx != -1:
                            peak_row_to_delete = -1
                            for p_r_idx, p_row in enumerate(peak_vals[1:], start=2):
                                if len(p_row) > link_col_idx:
                                    p_link = str(p_row[link_col_idx]).strip()
                                    if p_link == file_link:
                                        peak_row_to_delete = p_r_idx
                                        break
                            
                            # 3. If matching row is found in peak, delete it!
                            if peak_row_to_delete != -1:
                                peak_sheet_id = None
                                for s in spreadsheet.get('sheets', []):
                                    if s['properties']['title'] == 'peak':
                                        peak_sheet_id = s['properties']['sheetId']
                                        break
                                
                                if peak_sheet_id is not None:
                                    peak_delete_body = {
                                        "requests": [
                                            {
                                                "deleteDimension": {
                                                    "range": {
                                                        "sheetId": peak_sheet_id,
                                                        "dimension": "ROWS",
                                                        "startIndex": peak_row_to_delete - 1,
                                                        "endIndex": peak_row_to_delete
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                    google_manager.sheets_service.spreadsheets().batchUpdate(
                                        spreadsheetId=google_manager.spreadsheet_id,
                                        body=peak_delete_body
                                    ).execute()
                                    logger.info(f"✅ Automatically deleted corresponding row {peak_row_to_delete} in 'peak' sheet.")
            except Exception as pe:
                logger.error(f"⚠️ Failed to delete corresponding row in peak: {pe}")

        sheet_id = None
        for s in spreadsheet.get('sheets', []):
            if s['properties']['title'] == sheet_name:
                sheet_id = s['properties']['sheetId']
                break

        if sheet_id is None:
            return jsonify({"ok": False, "error": f"ไม่พบชีต '{sheet_name}'"}), 404

        # Delete row using batchUpdate deleteDimension
        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": row_index - 1,
                            "endIndex": row_index
                        }
                    }
                }
            ]
        }
        google_manager.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=google_manager.spreadsheet_id,
            body=body
        ).execute()

        # Re-run reconciliation
        google_manager.auto_reconcile_internal()

        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Error in api_dashboard_delete_expense: {e}")
        return jsonify({"ok": False, "error": "ไม่สามารถลบข้อมูลได้ กรุณาลองใหม่"}), 500


