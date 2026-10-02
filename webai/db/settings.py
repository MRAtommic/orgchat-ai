import sqlite3
import json
import os
import re
import random
import time
import threading
import logging
import secrets
import uuid
import hmac
import hashlib
from pathlib import Path
from datetime import datetime, date, timedelta
from functools import wraps

from .connection import *
from .connection import (
    _get_conn, _get_pg_pool, _pg_pool, _pg_pool_initialized, _pg_pool_lock,
    _db_url, _dt, _dt_mod, _j, _json, _re, _t_mod, _time_mod
)


def get_stats(username="Admin", org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user' AND username = ? AND organization_id = ?", (username, org_id))
    total_queries = cursor.fetchone()[0]

    cursor.execute("SELECT feedback, COUNT(*) FROM messages WHERE role = 'bot' AND username = ? AND organization_id = ? GROUP BY feedback", (username, org_id))
    feedback_stats = cursor.fetchall() # List of (val, count)

    conn.close()
    return {
        "total_queries": total_queries,
        "feedback": dict(feedback_stats)
    }


def add_push_subscription(username, subscription_json):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO push_subscriptions (username, subscription_json) VALUES (?, ?)", (username, subscription_json))
    conn.commit()
    conn.close()

def get_push_subscriptions(username):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT subscription_json FROM push_subscriptions WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def remove_push_subscription(username, subscription_json):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM push_subscriptions WHERE username = ? AND subscription_json = ?", (username, subscription_json))
    conn.commit()
    conn.close()

def log_event(event_text, user="System", org_id=1):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (event_text, user, organization_id) VALUES (?, ?, ?)", (event_text, user, org_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log event: {e}")

def get_events(limit=20, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT datetime(time, 'localtime'), event_text, user FROM events WHERE organization_id = ? ORDER BY time DESC LIMIT ?", (org_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"time": r[0], "event": r[1], "user": r[2]} for r in rows]



def get_daily_activities(org_id=1):
    """Fetch posts and schedules from the last 24 hours."""
    conn = _get_conn()
    cursor = conn.cursor()

    # Get posts from last 24h
    cursor.execute("""
        SELECT p.content, p.author, p.category, p.timestamp, up.display_name
        FROM posts p
        LEFT JOIN user_profiles up ON p.author = up.username
        WHERE p.timestamp >= datetime('now', '-1 day')
          AND (p.organization_id = ? OR p.organization_id IS NULL)
        ORDER BY p.timestamp DESC
    """, (org_id,))
    posts = cursor.fetchall()

    # Get upcoming schedules
    cursor.execute("""
        SELECT title, start_date, start_time, category
        FROM schedules
        WHERE start_date >= date('now')
          AND (organization_id = ? OR organization_id IS NULL)
        ORDER BY start_date ASC, start_time ASC
        LIMIT 10
    """, (org_id,))
    schedules = cursor.fetchall()

    conn.close()

    posts_data = [{
        "content": r[0],
        "author": r[4] or r[1],
        "category": r[2],
        "time": r[3]
    } for r in posts]

    schedules_data = [{
        "title": r[0],
        "date": r[1],
        "time": r[2],
        "category": r[3]
    } for r in schedules]

    return {"posts": posts_data, "schedules": schedules_data}

def get_executive_summary_data(org_id=1):
    """
    Aggregates comprehensive data for the Executive Daily Brief.
    Includes: Expenses, Leave Requests, Pending Approvals, Scheduled Meetings, and New Feed Posts.
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Financial Summary (Last 24h)
    cursor.execute("""
        SELECT SUM(amount) as total, COUNT(*) as count 
        FROM drive_logs 
        WHERE org_id = ? AND created_at >= datetime('now', '-1 day')
    """, (org_id,))
    finance = cursor.fetchone()
    
    # 2. HR Summary (Leaves today or starting today)
    cursor.execute("""
        SELECT l.username, up.display_name, l.leave_type, l.type, l.reason
        FROM leave_requests l
        LEFT JOIN user_profiles up ON l.username = up.username
        WHERE (l.org_id = ? OR l.org_id IS NULL)
          AND l.status = 'approved' 
          AND date('now') BETWEEN l.start_date AND l.end_date
    """, (org_id,))
    leaves = cursor.fetchall()
    
    # 3. Pending Leave Requests Count
    cursor.execute("""
        SELECT COUNT(*) as pending_count
        FROM leave_requests
        WHERE (org_id = ? OR org_id IS NULL) AND status = 'pending'
    """, (org_id,))
    pending_row = cursor.fetchone()
    pending_count = pending_row['pending_count'] if pending_row else 0

    # 4. Tasks/Schedules Summary (Due today)
    cursor.execute("""
        SELECT title, start_time, category 
        FROM schedules 
        WHERE organization_id = ? AND start_date = date('now')
        ORDER BY start_time ASC
    """, (org_id,))
    tasks = cursor.fetchall()
    
    # 5. Social Feed (Last 24h)
    cursor.execute("""
        SELECT p.content, up.display_name
        FROM posts p
        LEFT JOIN user_profiles up ON p.author = up.username
        WHERE p.organization_id = ? AND p.timestamp >= datetime('now', '-1 day')
        ORDER BY p.timestamp DESC LIMIT 5
    """, (org_id,))
    posts = cursor.fetchall()
    
    conn.close()
    
    return {
        "finance": {"total_amount": finance['total'] or 0, "count": finance['count'] if finance else 0},
        "leaves": [dict(r) for r in leaves],
        "pending_leaves_count": pending_count,
        "tasks": [dict(r) for r in tasks],
        "posts": [dict(r) for r in posts]
    }




def get_user_setting(username):
    """Get user_settings for a user, returns defaults if not set. Case-insensitive."""
    if not username:
        return {"username_original": "", "role": "user", "is_active": 1, "custom_password": None, "notes": "", "can_view_kb": False, "can_edit_kb": False, "can_delete_kb": False, "can_view_financial": False, "totp_enabled": False, "totp_secret": "", "totp_backup_codes": "", "can_manage_leave": False, "can_broadcast_line": False, "can_manage_peak": False, "can_use_ai": True, "can_claim_expense": True}
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, role, is_active, custom_password, notes, 
               can_view_kb, can_edit_kb, can_delete_kb, email, can_view_financial, 
               totp_enabled, totp_secret, totp_backup_codes, can_manage_leave,
               can_broadcast_line, can_manage_peak, can_use_ai, can_claim_expense
        FROM user_settings WHERE username = ? COLLATE NOCASE
    """, (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "username_original": row[0],
            "role": row[1],
            "is_active": row[2],
            "custom_password": row[3],
            "notes": row[4],
            "can_view_kb": bool(row[5]),
            "can_edit_kb": bool(row[6]),
            "can_delete_kb": bool(row[7]),
            "email": row[8] or "",
            "can_view_financial": bool(row[9]) if row[9] is not None else False,
            "totp_enabled": bool(row[10]),
            "totp_secret": row[11] or "",
            "totp_backup_codes": row[12] or "",
            "can_manage_leave": bool(row[13]) if row[13] is not None else False,
            "can_broadcast_line": bool(row[14]) if row[14] is not None else False,
            "can_manage_peak": bool(row[15]) if row[15] is not None else False,
            "can_use_ai": bool(row[16]) if row[16] is not None else True,
            "can_claim_expense": bool(row[17]) if row[17] is not None else True,
        }

    # Defaults
    if username.lower() == "admin":
        return {
            "username_original": "Admin", "role": "admin", "is_active": 1, "custom_password": None, "notes": "Default Admin",
            "can_view_kb": True, "can_edit_kb": True, "can_delete_kb": True, "can_view_financial": True,
            "totp_enabled": False, "totp_secret": "", "totp_backup_codes": "", "can_manage_leave": True,
            "can_broadcast_line": True, "can_manage_peak": True, "can_use_ai": True, "can_claim_expense": True
        }
    return {
        "username_original": username, "role": "user", "is_active": 1, "custom_password": None, "notes": "",
        "can_view_kb": False, "can_edit_kb": False, "can_delete_kb": False, "can_view_financial": False,
        "totp_enabled": False, "totp_secret": "", "totp_backup_codes": "", "can_manage_leave": False,
        "can_broadcast_line": False, "can_manage_peak": False, "can_use_ai": True, "can_claim_expense": True
    }





# --- Global App Settings ---
def get_app_setting(key, default=None):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

get_setting = get_app_setting

def set_app_setting(key, value):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (key, value))
    conn.commit()
    conn.close()

set_setting = set_app_setting

def get_all_app_settings():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_settings")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def get_line_permissions(username: str) -> str:
    """Retrieve the LINE permissions string for a user."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT line_permissions FROM user_settings WHERE username = ? COLLATE NOCASE", (username,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] is not None:
            return row[0]
    except Exception as e:
        print(f"Error getting LINE permissions for {username}: {e}")
    return 'report,links,reconcile,search,folder,leave'



    conn.commit()
    conn.close()
    return claim_id

def get_line_config(org_id: int = None):
    """Returns LINE integration configuration from org_line_configs or app_settings with os.environ fallback."""
    if org_id:
        org_cfg = get_org_line_config(org_id)
        if org_cfg and org_cfg.get("channel_access_token") and org_cfg.get("is_active"):
            return {
                "channel_access_token": (org_cfg.get("channel_access_token") or "").strip(),
                "channel_secret": (org_cfg.get("channel_secret") or "").strip(),
                "bot_basic_id": (org_cfg.get("bot_basic_id") or "").strip(),
                "webhook_url": get_app_setting("LINE_WEBHOOK_URL", "") or os.environ.get("LINE_WEBHOOK_URL", ""),
                "is_custom_org": True
            }
    token = get_app_setting("LINE_CHANNEL_ACCESS_TOKEN", "") or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    secret = get_app_setting("LINE_CHANNEL_SECRET", "") or os.environ.get("LINE_CHANNEL_SECRET", "")
    webhook = get_app_setting("LINE_WEBHOOK_URL", "") or os.environ.get("LINE_WEBHOOK_URL", "")
    bot_id = get_app_setting("LINE_BOT_BASIC_ID", "") or os.environ.get("LINE_BOT_BASIC_ID", "")
    return {
        "channel_access_token": token.strip() if token else "",
        "channel_secret": secret.strip() if secret else "",
        "bot_basic_id": bot_id.strip() if bot_id else "",
        "webhook_url": webhook.strip() if webhook else "",
        "is_custom_org": False
    }

def get_org_line_config(org_id: int) -> dict | None:
    """Retrieve custom LINE Bot credentials for an organization."""
    if not org_id:
        return None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM org_line_configs WHERE org_id = ?", (org_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"[get_org_line_config] error for org {org_id}: {e}")
        return None

def save_org_line_config(org_id: int, channel_access_token: str, channel_secret: str, bot_basic_id: str = "", is_active: int = 1) -> bool:
    """Save or update custom LINE Bot credentials for an organization."""
    if not org_id:
        return False
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO org_line_configs (org_id, channel_access_token, channel_secret, bot_basic_id, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(org_id) DO UPDATE SET
                channel_access_token = excluded.channel_access_token,
                channel_secret = excluded.channel_secret,
                bot_basic_id = excluded.bot_basic_id,
                is_active = excluded.is_active,
                updated_at = CURRENT_TIMESTAMP
        """, (org_id, channel_access_token.strip(), channel_secret.strip(), bot_basic_id.strip(), 1 if is_active else 0))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"[save_org_line_config] error for org {org_id}: {e}")
        return False

def delete_org_line_config(org_id: int) -> bool:
    """Remove custom LINE Bot credentials for an organization (reverts to system bot)."""
    if not org_id:
        return False
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM org_line_configs WHERE org_id = ?", (org_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"[delete_org_line_config] error for org {org_id}: {e}")
        return False



# =========================================================================
# Per-User Google OAuth2 Token Management (Multi-Tenant Drive & Sheets)
# =========================================================================

def save_google_token(username, google_email, access_token, refresh_token, token_expiry, spreadsheet_id=None, drive_folder_id=None):
    """Save or update a user's Google OAuth2 tokens."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_google_tokens 
                (username, google_email, access_token, refresh_token, token_expiry, spreadsheet_id, drive_folder_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(username) DO UPDATE SET
                google_email = excluded.google_email,
                access_token = excluded.access_token,
                refresh_token = COALESCE(excluded.refresh_token, user_google_tokens.refresh_token),
                token_expiry = excluded.token_expiry,
                spreadsheet_id = COALESCE(excluded.spreadsheet_id, user_google_tokens.spreadsheet_id),
                drive_folder_id = COALESCE(excluded.drive_folder_id, user_google_tokens.drive_folder_id),
                updated_at = CURRENT_TIMESTAMP
        """, (username, google_email, access_token, refresh_token, token_expiry, spreadsheet_id, drive_folder_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving Google token for {username}: {e}")
        return False


def get_google_token(username):
    """Retrieve a user's Google OAuth2 token data."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_google_tokens WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"❌ Error getting Google token for {username}: {e}")
        return None


def delete_google_token(username):
    """Remove a user's Google OAuth2 tokens (disconnect)."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_google_tokens WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error deleting Google token for {username}: {e}")
        return False


def get_user_spreadsheet_id(username):
    """Get the user's personal spreadsheet ID."""
    token_data = get_google_token(username)
    if token_data:
        return token_data.get("spreadsheet_id")
    return None


def set_user_spreadsheet_id(username, spreadsheet_id):
    """Set the user's personal spreadsheet ID."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_google_tokens SET spreadsheet_id = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
            (spreadsheet_id, username)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error setting spreadsheet_id for {username}: {e}")
        return False


def set_user_drive_folder_id(username, drive_folder_id):
    """Set the user's personal Drive folder ID."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_google_tokens SET drive_folder_id = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
            (drive_folder_id, username)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error setting drive_folder_id for {username}: {e}")
        return False


def get_all_google_connected_users():
    """Get all users who have connected their Google accounts."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT username, google_email, spreadsheet_id, drive_folder_id, updated_at FROM user_google_tokens")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error getting connected users: {e}")
        return []


# =========================================================================
# Org-Level Google OAuth2 Token Management (1 Google account per org)
# =========================================================================

def save_org_google_token(org_id: int, google_email: str, access_token: str,
                          refresh_token: str, token_expiry: str,
                          spreadsheet_id: str = None, drive_folder_id: str = None,
                          connected_by: str = None) -> bool:
    """Save or update an org's shared Google OAuth2 tokens."""
    try:
        conn = _get_conn()
        
        # Check if email is changing
        cursor = conn.cursor()
        cursor.execute("SELECT google_email FROM org_google_tokens WHERE org_id = ?", (org_id,))
        existing_row = cursor.fetchone()
        
        # If there was an existing email and it is different from the new one, clear old logs
        if existing_row and existing_row[0] != google_email:
            print(f"🔄 Google email changed from {existing_row[0]} to {google_email} for org {org_id}. Clearing old drive logs.")
            conn.execute("DELETE FROM drive_logs WHERE org_id = ?", (org_id,))
            
        conn.execute("""
            INSERT INTO org_google_tokens
                (org_id, google_email, access_token, refresh_token, token_expiry,
                 spreadsheet_id, drive_folder_id, connected_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(org_id) DO UPDATE SET
                google_email    = excluded.google_email,
                access_token    = excluded.access_token,
                refresh_token   = COALESCE(excluded.refresh_token, org_google_tokens.refresh_token),
                token_expiry    = excluded.token_expiry,
                spreadsheet_id  = COALESCE(excluded.spreadsheet_id, org_google_tokens.spreadsheet_id),
                drive_folder_id = COALESCE(excluded.drive_folder_id, org_google_tokens.drive_folder_id),
                connected_by    = excluded.connected_by,
                updated_at      = CURRENT_TIMESTAMP
        """, (org_id, google_email, access_token, refresh_token, token_expiry,
              spreadsheet_id, drive_folder_id, connected_by))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving org Google token for org {org_id}: {e}")
        return False


def get_org_google_token(org_id: int) -> dict | None:
    """Retrieve an org's shared Google OAuth2 token data."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM org_google_tokens WHERE org_id = ?", (org_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ Error getting org Google token for org {org_id}: {e}")
        return None


def delete_org_google_token(org_id: int) -> bool:
    """Remove an org's shared Google OAuth2 tokens (disconnect) and clear old cached drive logs."""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM org_google_tokens WHERE org_id = ?", (org_id,))
        conn.execute("DELETE FROM drive_logs WHERE org_id = ?", (org_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error deleting org Google token for org {org_id}: {e}")
        return False


def set_org_spreadsheet_id(org_id: int, spreadsheet_id: str) -> bool:
    try:
        conn = _get_conn()
        conn.execute(
            "UPDATE org_google_tokens SET spreadsheet_id = ?, updated_at = CURRENT_TIMESTAMP WHERE org_id = ?",
            (spreadsheet_id, org_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error setting org spreadsheet_id for org {org_id}: {e}")
        return False


def set_org_drive_folder_id(org_id: int, drive_folder_id: str) -> bool:
    try:
        conn = _get_conn()
        conn.execute(
            "UPDATE org_google_tokens SET drive_folder_id = ?, updated_at = CURRENT_TIMESTAMP WHERE org_id = ?",
            (drive_folder_id, org_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error setting org drive_folder_id for org {org_id}: {e}")
        return False


def get_org_admin_google_token(org_id: int) -> dict | None:
    """
    Get the Google token of the first admin member in an org.
    Used as fallback when LINE bot background threads have no username context.
    """
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ugt.*
            FROM user_google_tokens ugt
            JOIN organization_members om ON om.username = ugt.username
            WHERE om.organization_id = ? AND om.role = 'admin'
              AND ugt.refresh_token IS NOT NULL
            ORDER BY om.joined_at
            LIMIT 1
        """, (org_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ Error getting org admin Google token for org {org_id}: {e}")
        return None


def resolve_google_token(username: str, org_id: int = None) -> tuple[dict | None, str]:
    """
    Resolve the correct Google token for a context.
    Returns (token_dict, source) where source is 'org', 'personal', or 'org_admin_personal'.
    Priority: org-level token → personal user token → org admin's personal token → None.
    """
    if org_id:
        org_token = get_org_google_token(org_id)
        if org_token and org_token.get("refresh_token"):
            return org_token, "org"
    user_token = get_google_token(username)
    if user_token and user_token.get("refresh_token"):
        return user_token, "personal"
    # Fallback: background threads (LINE bot) run with user=None — use org admin's personal token
    if org_id and not username:
        admin_token = get_org_admin_google_token(org_id)
        if admin_token and admin_token.get("refresh_token"):
            return admin_token, "org_admin_personal"
    return None, "none"


@db_transaction_retry()


def save_line_broadcast(username: str, org_id: int, text: str, status: str = "success", scheduled_at: str = None):
    """Log a LINE broadcast event to history."""
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO line_broadcast_history (username, org_id, text, status, scheduled_at) VALUES (?, ?, ?, ?, ?)",
            (username, org_id, text, status, scheduled_at)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving broadcast history: {e}")
        return False


def get_line_broadcast_history(org_id: int, limit: int = 50):
    """Retrieve broadcast history for a specific organization."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM line_broadcast_history WHERE org_id = ? ORDER BY timestamp DESC LIMIT ?",
            (org_id, limit)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"❌ Error fetching broadcast history: {e}")
        return []


def get_pending_broadcasts(now_str: str):
    """Retrieve pending broadcasts that should be run."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM line_broadcast_history WHERE status = 'Pending' AND scheduled_at <= ?",
            (now_str,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"❌ Error fetching pending broadcasts: {e}")
        return []


def update_line_broadcast_status(broadcast_id: int, status: str):
    """Update status of a broadcast."""
    try:
        conn = _get_conn()
        conn.execute(
            "UPDATE line_broadcast_history SET status = ? WHERE id = ?",
            (status, broadcast_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error updating broadcast status: {e}")
        return False


# ─── DB-backed LINE link tokens ─────────────────────────────────────────────

_LINE_LINK_TTL = 600  # 10 นาที


def line_link_create(token: str, line_user_id: str):
    """สร้าง LINE link token ใน DB (แทน in-memory dict)."""
    expires_at = time.time() + _LINE_LINK_TTL
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO pending_line_links (token, line_user_id, expires_at) VALUES (?, ?, ?)",
        (token, line_user_id, expires_at),
    )
    conn.commit()
    conn.close()
    # ล้าง expired tokens ในโอกาสเดียวกัน
    _line_link_cleanup()


def line_link_get(token: str) -> dict | None:
    """คืน {'line_user_id': ..., 'timestamp': ...} หรือ None ถ้าไม่มี/หมดอายุ"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT line_user_id, expires_at FROM pending_line_links WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {"line_user_id": row[0], "timestamp": row[1] - _LINE_LINK_TTL, "expires_at": row[1]}


def line_link_delete(token: str):
    conn = _get_conn()
    conn.execute("DELETE FROM pending_line_links WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def _line_link_cleanup():
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM pending_line_links WHERE expires_at < ?", (time.time(),))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ─── DB-backed OAuth2 states ────────────────────────────────────────────────

_OAUTH_STATE_TTL = 600  # 10 นาที


def oauth_state_store(state: str, data: dict):
    """บันทึก OAuth state ลง DB (แทน in-memory _OAUTH_STATES)."""
    import json as _json
    expires_at = time.time() + _OAUTH_STATE_TTL
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO oauth_states (state, data_json, expires_at) VALUES (?, ?, ?)",
        (state, _json.dumps(data, ensure_ascii=False), expires_at),
    )
    conn.commit()
    conn.close()
    # ล้าง expired
    _oauth_state_cleanup()


def oauth_state_pop(state: str) -> dict | None:
    """ดึงและลบ state — คืน data dict หรือ None ถ้าหมดอายุ/ไม่มี"""
    import json as _json
    conn = _get_conn()
    row = conn.execute(
        "SELECT data_json, expires_at FROM oauth_states WHERE state = ?", (state,)
    ).fetchone()
    if row:
        conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
        conn.commit()
    conn.close()
    if not row:
        return None
    if time.time() > row[1]:
        return None
    return _json.loads(row[0])




def _oauth_state_cleanup():
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM oauth_states WHERE expires_at < ?", (time.time(),))
        conn.commit()
        conn.close()
    except Exception:
        pass




def get_user_clearance_level(username: str) -> str:
    if not username:
        return 'employee'
    if username == 'Admin':
        return 'admin'
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT clearance_level, role FROM user_settings WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        if row[1] in ['admin', 'superadmin']:
            return 'admin'
        return row[0] or 'employee'
    return 'employee'

def update_user_clearance_level(username: str, clearance_level: str) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE user_settings SET clearance_level = ? WHERE username = ?", (clearance_level, username))
    ok = cur.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def get_kb_category_access_level(category_id: int) -> str:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT access_level FROM kb_categories WHERE id = ?", (category_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else 'public'



def update_kb_category_access_level(category_id: int, access_level: str) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE kb_categories SET access_level = ? WHERE id = ?", (access_level, category_id))
    ok = cur.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def log_event(action, user="System", org_id=1, details="", ip_address="127.0.0.1"):
    """Log an audit trail event for organization compliance and activity history."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(audit_logs)")
        cols = [c[1] for c in cursor.fetchall()]
        org_col = "org_id" if "org_id" in cols else "organization_id" if "organization_id" in cols else "org_id"
        action_col = "action" if "action" in cols else "event_type"
        details_col = "details" if "details" in cols else "action_detail"
        
        cursor.execute(
            f"INSERT INTO audit_logs ({org_col}, username, {action_col}, {details_col}, ip_address) VALUES (?, ?, ?, ?, ?)",
            (org_id, user or "System", str(action), str(details or ""), ip_address or "127.0.0.1")
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[log_event error] {e}")

# Old duplicate get_audit_logs removed - robust definition maintained at end of file.


# ══════════════════════════════════════════════════════
# Custom Expense Categories & AI Rules CRUD
# ══════════════════════════════════════════════════════


