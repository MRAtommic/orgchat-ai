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

from .settings import get_user_clearance_level
# --- User Profile ---
def get_user_profile(username):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT username, display_name, avatar_url, background_url, department, line_user_id FROM user_profiles WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "username": row[0],
            "display_name": row[1],
            "avatar_url": row[2],
            "background_url": row[3],
            "department": row[4] or "General",
            "line_user_id": row[5] or ""
        }
    return {
        "username": username,
        "display_name": username.capitalize(),
        "avatar_url": None,
        "background_url": None,
        "department": "General",
        "line_user_id": ""
    }

def update_user_profile(username, display_name=None, avatar_url=None, background_url=None, department=None):
    conn = _get_conn()
    cursor = conn.cursor()
    # Check if exists
    cursor.execute("SELECT 1 FROM user_profiles WHERE username = ?", (username,))
    if cursor.fetchone():
        if display_name:
            cursor.execute("UPDATE user_profiles SET display_name = ? WHERE username = ?", (display_name, username))
        if avatar_url:
            cursor.execute("UPDATE user_profiles SET avatar_url = ? WHERE username = ?", (avatar_url, username))
        if background_url:
            cursor.execute("UPDATE user_profiles SET background_url = ? WHERE username = ?", (background_url, username))
        if department:
            cursor.execute("UPDATE user_profiles SET department = ? WHERE username = ?", (department, username))
    else:
        cursor.execute("""
            INSERT INTO user_profiles (username, display_name, avatar_url, background_url, department)
            VALUES (?, ?, ?, ?, ?)
        """, (username, display_name or username.capitalize(), avatar_url, background_url, department or "General"))
    conn.commit()
    conn.close()



def get_user_by_email(email: str) -> dict | None:
    """Find user settings/profile by email address. Case-insensitive."""
    if not email:
        return None
    email_clean = email.strip().lower()
    conn = _get_conn()
    cursor = conn.cursor()
    # 1. Check user_settings table
    cursor.execute("""
        SELECT username, role, is_active, email 
        FROM user_settings 
        WHERE email = ? COLLATE NOCASE AND is_active = 1
    """, (email_clean,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return {"username": row[0], "role": row[1], "is_active": row[2], "email": row[3]}

    # 2. Check user_google_tokens
    cursor.execute("""
        SELECT username, google_email 
        FROM user_google_tokens 
        WHERE google_email = ? COLLATE NOCASE
    """, (email_clean,))
    row_g = cursor.fetchone()
    if row_g:
        conn.close()
        return {"username": row_g[0], "role": "user", "is_active": 1, "email": row_g[1]}

    # 3. Check organization_allowed_emails
    cursor.execute("""
        SELECT email FROM organization_allowed_emails 
        WHERE email = ? COLLATE NOCASE
    """, (email_clean,))
    row_wl = cursor.fetchone()
    conn.close()
    if row_wl:
        return {"username": email_clean.split("@")[0], "role": "user", "is_active": 1, "email": row_wl[0]}

    return None

def admin_get_all_users(org_id=1):
    """Get all users with their profiles and settings, filtered by org."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.username, p.display_name, p.avatar_url,
               COALESCE(s.role, 'user') as role,
               COALESCE(s.is_active, 1) as is_active,
               COALESCE(s.notes, '') as notes,
               COALESCE(s.can_view_kb, 0) as can_view_kb,
               COALESCE(s.can_edit_kb, 0) as can_edit_kb,
               COALESCE(s.can_delete_kb, 0) as can_delete_kb,
               p.department,
               om.role as org_role,
               COALESCE(s.can_view_financial, 0) as can_view_financial,
               p.line_user_id,
               COALESCE(s.line_permissions, 'report,links,reconcile,search,folder,leave') as line_permissions,
               COALESCE(s.can_manage_leave, 0) as can_manage_leave
        FROM user_profiles p
        JOIN organization_members om ON p.username = om.username COLLATE NOCASE
        LEFT JOIN user_settings s ON p.username = s.username COLLATE NOCASE
        WHERE om.organization_id = ?
        ORDER BY role DESC, p.username ASC
    """, (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "username": r[0],
        "display_name": r[1],
        "avatar_url": r[2],
        "role": r[3],
        "is_active": bool(r[4]),
        "notes": r[5],
        "can_view_kb": bool(r[6]),
        "can_edit_kb": bool(r[7]),
        "can_delete_kb": bool(r[8]),
        "department": r[9],
        "org_role": r[10],
        "can_view_financial": bool(r[11]),
        "line_user_id": r[12],
        "line_permissions": r[13],
        "can_manage_leave": bool(r[14]),
    } for r in rows]

def update_user_totp(username, secret, backup_codes_json="", enabled=False):
    """Update TOTP 2FA secret and backup codes for a user."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_settings (username, totp_secret, totp_backup_codes, totp_enabled)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            totp_secret = EXCLUDED.totp_secret,
            totp_backup_codes = EXCLUDED.totp_backup_codes,
            totp_enabled = EXCLUDED.totp_enabled
    """, (username, secret, backup_codes_json, 1 if enabled else 0))
    conn.commit()
    conn.close()

def set_totp_status(username, enabled):
    """Enable or disable TOTP 2FA for a user."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_settings SET totp_enabled = ? WHERE username = ? COLLATE NOCASE
    """, (1 if enabled else 0, username))
    conn.commit()
    conn.close()



def admin_update_user(username, display_name=None, role=None, is_active=None, notes=None, can_view_kb=None, can_edit_kb=None, can_delete_kb=None, department=None, can_view_financial=None, position=None, line_permissions=None, can_manage_leave=None, can_use_ai=None, can_claim_expense=None, can_broadcast_line=None, can_manage_peak=None):
    """Admin updates a user's profile and settings."""
    conn = _get_conn()
    cursor = conn.cursor()

    # Prevent admin from disabling their own account or changing role
    if username == "Admin":
        if is_active is not None and not is_active:
            is_active = True
        if role is not None and role != "admin":
            role = "admin"

    # Update profile
    profile_updates = {}
    if display_name is not None:
        profile_updates["display_name"] = display_name
    if department is not None:
        profile_updates["department"] = department
    if position is not None:
        profile_updates["position"] = position

    if profile_updates:
        cursor.execute("INSERT OR IGNORE INTO user_profiles (username) VALUES (?)", (username,))
        for col, val in profile_updates.items():
            cursor.execute(f"UPDATE user_profiles SET {col} = ? WHERE username = ?", (val, username))
    # Upsert settings
    if any(v is not None for v in [role, is_active, notes, can_view_kb, can_edit_kb, can_delete_kb, can_view_financial, line_permissions, can_manage_leave, can_use_ai, can_claim_expense, can_broadcast_line, can_manage_peak]):
        cursor.execute("INSERT OR IGNORE INTO user_settings (username) VALUES (?)", (username,))
        if role is not None:
            cursor.execute("UPDATE user_settings SET role = ? WHERE username = ?", (role, username))
        if is_active is not None:
            cursor.execute("UPDATE user_settings SET is_active = ? WHERE username = ?", (1 if is_active else 0, username))
        if can_view_kb is not None:
            cursor.execute("UPDATE user_settings SET can_view_kb = ? WHERE username = ?", (1 if can_view_kb else 0, username))
        if can_edit_kb is not None:
            cursor.execute("UPDATE user_settings SET can_edit_kb = ? WHERE username = ?", (1 if can_edit_kb else 0, username))
        if can_delete_kb is not None:
            cursor.execute("UPDATE user_settings SET can_delete_kb = ? WHERE username = ?", (1 if can_delete_kb else 0, username))
        if can_view_financial is not None:
            cursor.execute("UPDATE user_settings SET can_view_financial = ? WHERE username = ?", (1 if can_view_financial else 0, username))
        if line_permissions is not None:
            cursor.execute("UPDATE user_settings SET line_permissions = ? WHERE username = ?", (line_permissions, username))
        if can_manage_leave is not None:
            cursor.execute("UPDATE user_settings SET can_manage_leave = ? WHERE username = ?", (1 if can_manage_leave else 0, username))
        if can_use_ai is not None:
            cursor.execute("UPDATE user_settings SET can_use_ai = ? WHERE username = ?", (1 if can_use_ai else 0, username))
        if can_claim_expense is not None:
            cursor.execute("UPDATE user_settings SET can_claim_expense = ? WHERE username = ?", (1 if can_claim_expense else 0, username))
        if can_broadcast_line is not None:
            cursor.execute("UPDATE user_settings SET can_broadcast_line = ? WHERE username = ?", (1 if can_broadcast_line else 0, username))
        if can_manage_peak is not None:
            cursor.execute("UPDATE user_settings SET can_manage_peak = ? WHERE username = ?", (1 if can_manage_peak else 0, username))
        if notes is not None:
            cursor.execute("UPDATE user_settings SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?", (notes, username))
    conn.commit()
    conn.close()


def get_user_session_version(username: str) -> int:
    """Get the current session version for a user. Defaults to 1."""
    if not username:
        return 1
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT session_version FROM user_settings WHERE username = ? COLLATE NOCASE", (username,))
        row = cur.fetchone()
        return int(row[0]) if (row and row[0] is not None) else 1
    except Exception:
        return 1
    finally:
        conn.close()


def increment_user_session_version(username: str) -> int:
    """Increment session version to immediately invalidate active sessions across all other devices."""
    if not username:
        return 1
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE user_settings SET session_version = COALESCE(session_version, 1) + 1 WHERE username = ? COLLATE NOCASE", (username,))
        conn.commit()
        cur.execute("SELECT session_version FROM user_settings WHERE username = ? COLLATE NOCASE", (username,))
        row = cur.fetchone()
        new_ver = int(row[0]) if (row and row[0] is not None) else 1
        return new_ver
    except Exception as e:
        logger.warning(f"Error incrementing session_version for {username}: {e}")
        return 1
    finally:
        conn.close()


def admin_reset_user_password(username, new_password):
    """Admin sets a custom password override for a user (hashed with bcrypt) and invalidates old sessions."""
    conn = _get_conn()
    cursor = conn.cursor()
    hashed = hash_password(new_password)
    cursor.execute("INSERT OR IGNORE INTO user_settings (username) VALUES (?)", (username,))
    cursor.execute("UPDATE user_settings SET custom_password = ?, session_version = COALESCE(session_version, 1) + 1, updated_at = CURRENT_TIMESTAMP WHERE username = ? COLLATE NOCASE", (hashed, username))
    conn.commit()
    conn.close()

def admin_create_user(username, password, role="user", display_name=None, can_view_kb=False, can_edit_kb=False, can_delete_kb=False, department="General", email=None):
    """Admin creates a new user account with profile and settings (password hashed)."""
    conn = _get_conn()
    cursor = conn.cursor()
    # First, check if user already exists case-insensitively
    cursor.execute("SELECT username FROM user_profiles WHERE username = ? COLLATE NOCASE", (username,))
    if cursor.fetchone():
        conn.close()
        print(f"User {username} already exists (case-insensitive check)")
        return False

    try:
        if not display_name:
            display_name = username.capitalize()

        # Hash password before storing
        hashed_pw = hash_password(password)

        # 1. Create Profile
        cursor.execute("""
            INSERT INTO user_profiles (username, display_name, department) 
            VALUES (?, ?, ?)
        """, (username, display_name, department))
        
        # 2. Create Settings & Password (hashed) — is_active=1 set explicitly for clarity
        cursor.execute("""
            INSERT INTO user_settings (username, role, custom_password, can_view_kb, can_edit_kb, can_delete_kb, email, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (username, role, hashed_pw, 1 if can_view_kb else 0, 1 if can_edit_kb else 0, 1 if can_delete_kb else 0, email or ""))
        
        # 3. Add to General Group (Room ID: 1)
        cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (1, ?)", (username,))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Error creating user {username}: {e}")
        return False
    finally:
        conn.close()

def admin_delete_user_complete(username):
    """Admin deletes a user and all their related data across all tables."""
    if username == "Admin":
        return False # Protect main admin
        
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # List of tables where user data resides
        tables = [
            "user_profiles", "user_settings", "user_category_access", 
            "room_members", "likes", "messages", "schedules", 
            "posts", "comments", "private_messages", "organization_members",
            "room_messages", "group_messages", "push_subscriptions",
            "user_google_tokens", "user_status", "search_history",
            "message_read_receipts",
            "leave_requests", "leave_comments", "expense_claims", "wiki_pages"
        ]
        
        # Clean up private_message_read_status based on message IDs
        cursor.execute("""
            DELETE FROM private_message_read_status 
            WHERE message_id IN (
                SELECT id FROM private_messages 
                WHERE sender = ? COLLATE NOCASE OR recipient = ? COLLATE NOCASE
            )
        """, (username, username))
        
        # 0. Look up user email before deletion to clean up from whitelists
        emails = []
        cur_email = cursor.execute("SELECT email FROM user_settings WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if cur_email and cur_email[0]:
            emails.append(cur_email[0].strip().lower())
        g_email = cursor.execute("SELECT google_email FROM user_google_tokens WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if g_email and g_email[0]:
            emails.append(g_email[0].strip().lower())
            
        for em in set(emails):
            cursor.execute("DELETE FROM organization_allowed_emails WHERE email = ? COLLATE NOCASE", (em,))

        for table in tables:
            # Basic whitelist check for safety (even though the list is hardcoded above)
            if not re.match(r'^[a-zA-Z0-9_]+$', table):
                continue

            col = "username"
            if table == "private_messages":
                cursor.execute("DELETE FROM private_messages WHERE sender = ? COLLATE NOCASE OR recipient = ? COLLATE NOCASE", (username, username))
                continue
            if table == "likes":
                col = "user"
            if table == "comments" or table == "posts" or table == "wiki_pages":
                col = "author"
            
            cursor.execute(f"DELETE FROM {table} WHERE {col} = ? COLLATE NOCASE", (username,))
            
        # Clean up kanban_cards
        cursor.execute("DELETE FROM kanban_cards WHERE assignee = ? COLLATE NOCASE OR created_by = ? COLLATE NOCASE", (username, username))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting user {username}: {e}")
        return False
    finally:
        conn.close()

def superadmin_get_all_users() -> list:
    """Super admin: all users across ALL orgs with their org memberships."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.username,
                COALESCE(p.display_name, p.username) AS display_name,
                p.avatar_url,
                COALESCE(p.department, 'General') AS department,
                p.timestamp AS profile_created,
                COALESCE(s.role, 'user') AS role,
                COALESCE(s.is_active, 1) AS is_active,
                COALESCE(s.notes, '') AS notes,
                COALESCE(s.can_edit_kb, 0) AS can_edit_kb,
                GROUP_CONCAT(
                    CAST(o.id AS TEXT) || ':' || o.name || ':' || om.role || ':' || COALESCE(o.plan, 'free'),
                    '|'
                ) AS org_memberships
            FROM user_profiles p
            LEFT JOIN user_settings s ON p.username = s.username COLLATE NOCASE
            LEFT JOIN organization_members om ON p.username = om.username COLLATE NOCASE
            LEFT JOIN organizations o ON om.organization_id = o.id
            GROUP BY p.username
            ORDER BY p.timestamp DESC
        """)
        rows = cur.fetchall()
    finally:
        conn.close()
    result = []
    for r in rows:
        d = dict(r)
        orgs = []
        if d.get("org_memberships"):
            for part in d["org_memberships"].split("|"):
                bits = part.split(":", 3)
                if len(bits) == 4:
                    orgs.append({"id": int(bits[0]), "name": bits[1], "role": bits[2], "plan": bits[3]})
        d["orgs"] = orgs
        del d["org_memberships"]
        result.append(d)
    return result


def superadmin_get_system_stats() -> dict:
    """Super admin: system-wide aggregate stats."""
    from datetime import date
    ym = date.today().strftime("%Y-%m")
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM organizations")
    total_orgs = (cur.fetchone() or {"cnt": 0})["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM user_profiles")
    total_users = (cur.fetchone() or {"cnt": 0})["cnt"]
    cur.execute("SELECT SUM(ai_query_count) AS cnt FROM usage_tracking WHERE year_month=?", (ym,))
    ai_queries_this_month = (cur.fetchone() or {"cnt": 0})["cnt"] or 0
    cur.execute("SELECT SUM(ai_query_count) AS cnt FROM usage_tracking")
    tracked_total = (cur.fetchone() or {"cnt": 0})["cnt"] or 0
    cur.execute("SELECT COUNT(*) AS cnt FROM messages WHERE role='user'")
    msg_total = (cur.fetchone() or {"cnt": 0})["cnt"] or 0
    total_ai_queries = max(tracked_total, msg_total, ai_queries_this_month)
    cur.execute("SELECT COUNT(*) AS cnt FROM organizations WHERE COALESCE(plan,'free') != 'free'")
    paying_orgs = (cur.fetchone() or {"cnt": 0})["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM messages")
    total_messages = (cur.fetchone() or {"cnt": 0})["cnt"]
    conn.close()
    db_size_bytes = 0
    try:
        db_size_bytes = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    except Exception:
        pass
    return {
        "total_orgs": total_orgs,
        "total_users": total_users,
        "total_ai_queries": total_ai_queries,
        "ai_queries_this_month": ai_queries_this_month,
        "paying_orgs": paying_orgs,
        "total_messages": total_messages,
        "db_size_bytes": db_size_bytes,
    }




def add_category(name, description=None, created_by="Admin", visibility="public", org_id=None):
    """Adds a new KB category with visibility settings, scoped to org."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # Add organization_id column if it doesn't exist (safe migration)
        try:
            cursor.execute("ALTER TABLE kb_categories ADD COLUMN organization_id INTEGER")
            conn.commit()
        except Exception:
            pass  # Column already exists
        cursor.execute(
            "INSERT INTO kb_categories (name, description, created_by, visibility, organization_id) VALUES (?, ?, ?, ?, ?)",
            (name, description, created_by, visibility, org_id)
        )
        cat_id = cursor.lastrowid
        conn.commit()
        return cat_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_categories(username=None, org_id=None):
    """
    Returns KB categories filtered by user access AND organization.
    Logic:
    - Admin sees all categories in their org.
    - Owner sees all their categories in their org.
    - Public categories in the org are visible to all members.
    - Restricted categories are visible to authorized users.
    - Private categories are only visible to the owner.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    # Check if organization_id column exists
    cursor.execute("PRAGMA table_info(kb_categories)")
    cols = [r[1] for r in cursor.fetchall()]
    has_org_col = 'organization_id' in cols

    # Build org filter clause
    if has_org_col and org_id is not None:
        # Show org-specific categories OR legacy categories without org (org_id IS NULL)
        org_clause = " AND (c.organization_id = ? OR c.organization_id IS NULL)"
        org_params_single = (org_id,)
    else:
        org_clause = ""
        org_params_single = ()

    # Access & Clearance rank mapping
    CLEARANCE_MAP = {'employee': 1, 'manager': 2, 'executive': 3, 'admin': 99}
    ACCESS_MAP = {'public': 0, 'internal': 1, 'confidential': 2, 'executives': 3}

    user_clearance = get_user_clearance_level(username)
    max_rank = CLEARANCE_MAP.get(user_clearance, 1)

    if username == "Admin" or (username and _is_system_admin(username)):
        if has_org_col and org_id is not None:
            cursor.execute(
                "SELECT id, name, description, created_by, visibility, created_at, access_level FROM kb_categories "
                "WHERE (organization_id = ? OR organization_id IS NULL) ORDER BY name ASC",
                (org_id,)
            )
        else:
            cursor.execute("SELECT id, name, description, created_by, visibility, created_at, access_level FROM kb_categories ORDER BY name ASC")
    elif username:
        if has_org_col and org_id is not None:
            cursor.execute("""
                SELECT DISTINCT c.id, c.name, c.description, c.created_by, c.visibility, c.created_at, c.access_level
                FROM kb_categories c
                LEFT JOIN user_category_access uca ON c.id = uca.category_id
                WHERE (c.visibility = 'public' OR c.created_by = ? OR (c.visibility = 'restricted' AND uca.username = ?))
                  AND (c.organization_id = ? OR c.organization_id IS NULL)
                ORDER BY c.name ASC
            """, (username, username, org_id))
        else:
            cursor.execute("""
                SELECT DISTINCT c.id, c.name, c.description, c.created_by, c.visibility, c.created_at, c.access_level
                FROM kb_categories c
                LEFT JOIN user_category_access uca ON c.id = uca.category_id
                WHERE c.visibility = 'public'
                   OR c.created_by = ?
                   OR (c.visibility = 'restricted' AND uca.username = ?)
                ORDER BY c.name ASC
            """, (username, username))
    else:
        if has_org_col and org_id is not None:
            cursor.execute(
                "SELECT id, name, description, created_by, visibility, created_at, access_level FROM kb_categories "
                "WHERE visibility = 'public' AND (organization_id = ? OR organization_id IS NULL) ORDER BY name ASC",
                (org_id,)
            )
        else:
            cursor.execute("SELECT id, name, description, created_by, visibility, created_at, access_level FROM kb_categories WHERE visibility = 'public' ORDER BY name ASC")

    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        acc = r[6] if len(r) > 6 and r[6] else 'public'
        req_rank = ACCESS_MAP.get(acc, 0)
        # Filter out categories that require higher clearance than user rank
        if max_rank >= req_rank:
            result.append({
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "created_by": r[3],
                "visibility": r[4],
                "created_at": r[5],
                "access_level": acc
            })
    return result

def _is_system_admin(username):
    """Quick check if username is system admin (role=admin in user_settings)."""
    try:
        conn = _get_conn()
        row = conn.execute("SELECT role FROM user_settings WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        conn.close()
        return row and row[0] == 'admin'
    except Exception:
        return False

def update_category_settings(cat_id, visibility, authorized_users=None):
    """
    Updates visibility of a category and manages authorized users if restricted.
    authorized_users: List of usernames
    """
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE kb_categories SET visibility = ? WHERE id = ?", (visibility, cat_id))
        
        # If restricted, update authorized users
        if visibility == 'restricted' and authorized_users is not None:
            cursor.execute("DELETE FROM user_category_access WHERE category_id = ?", (cat_id,))
            for user in authorized_users:
                if user.strip():
                    cursor.execute("INSERT OR IGNORE INTO user_category_access (username, category_id) VALUES (?, ?)", 
                                   (user.strip(), cat_id))
        elif visibility != 'restricted':
            # Optionally clear access list if no longer restricted
            cursor.execute("DELETE FROM user_category_access WHERE category_id = ?", (cat_id,))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating category settings: {e}")
        return False
    finally:
        conn.close()

def delete_category(cat_id):
    """Deletes a KB category."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kb_categories WHERE id = ?", (cat_id,))
    # Clear associations in user_category_access
    cursor.execute("DELETE FROM user_category_access WHERE category_id = ?", (cat_id,))
    # Reset category_id in knowledge_base
    cursor.execute("UPDATE knowledge_base SET category_id = NULL WHERE category_id = ?", (cat_id,))
    conn.commit()
    conn.close()

def update_file_category(file_id, category_id):
    """Assigns a file to a category."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE knowledge_base SET category_id = ? WHERE file_id = ?", (category_id, file_id))
    conn.commit()
    conn.close()

def get_files_by_category(category_id=None):
    """Returns files filtered by category_id. If None, returns unassigned files."""
    conn = _get_conn()
    cursor = conn.cursor()
    if category_id:
        cursor.execute("SELECT * FROM knowledge_base WHERE category_id = ?", (category_id,))
    else:
        cursor.execute("SELECT * FROM knowledge_base WHERE category_id IS NULL")
    rows = cursor.fetchall()
    conn.close()
    # Note: Need to match knowledge_base schema for return dict
    return rows

# ─── Leave Management Functions ───────────────────────────



def get_user_category_access(username):
    """Returns category IDs the user has access to."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id FROM user_category_access WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def set_user_category_access(username, category_ids):
    """Sets which categories a user can access."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_category_access WHERE username = ?", (username,))
    for cat_id in category_ids:
        cursor.execute("INSERT INTO user_category_access (username, category_id) VALUES (?, ?)", (username, cat_id))
    conn.commit()
    conn.close()

# ─── AI Personas ──────────────────────────────
def add_persona(name, system_prompt, description=None, scope_category_id=None, avatar_url=None, created_by=None):
    """Adds a new AI persona."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ai_personas (name, system_prompt, description, scope_category_id, avatar_url, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, system_prompt, description, scope_category_id, avatar_url, created_by))
        persona_id = cursor.lastrowid
        conn.commit()
        return persona_id
    except Exception as e:
        print(f"Error adding persona: {e}")
        return None
    finally:
        conn.close()

def get_personas(only_active=True):
    """Returns all AI personas."""
    conn = _get_conn()
    cursor = conn.cursor()
    query = "SELECT * FROM ai_personas"
    if only_active:
        query += " WHERE is_active = 1"
    query += " ORDER BY name ASC"
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    conn.close()
    return results

def get_persona(persona_id):
    """Returns a specific persona."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_personas WHERE id = ?", (persona_id,))
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    conn.close()
    return dict(zip(columns, row)) if row else None

def update_persona(persona_id, **kwargs):
    """Updates persona fields with whitelist validation."""
    allowed = {"name", "description", "system_prompt", "scope_category_id", "avatar_url", "is_active", "organization_id"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates: 
        return False
        
    conn = _get_conn()
    cursor = conn.cursor()
    fields = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [persona_id]
    try:
        cursor.execute(f"UPDATE ai_personas SET {fields} WHERE id = ?", values)
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating persona {persona_id}: {e}")
        return False
    finally:
        conn.close()

def delete_persona(persona_id):
    """Deletes a persona."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_personas WHERE id = ?", (persona_id,))
    conn.commit()
    conn.close()

# ─── Seen Receipts ────────────────────────────


def get_admin_dashboard_stats(org_id=None):
    """Returns analytics for the admin dashboard, filtered by org."""
    conn = _get_conn()
    cursor = conn.cursor()

    if org_id is not None:
        # Get org member usernames for filtering
        members = [r[0] for r in conn.execute(
            "SELECT username FROM organization_members WHERE organization_id = ?", (org_id,)
        ).fetchall()]
        placeholders = ','.join('?' * len(members)) if members else "''"
        member_params = members if members else []

        # User count (org members only)
        total_users = len(members)

        # AI queries (org members only)
        if members:
            cursor.execute(
                f"SELECT COUNT(*) FROM messages WHERE role = 'user' AND username IN ({placeholders})",
                member_params
            )
        else:
            cursor.execute("SELECT 0")
        total_ai_queries = cursor.fetchone()[0]

        # Top posters (org only)
        if members:
            cursor.execute(
                f"SELECT author, COUNT(*) as c FROM posts WHERE organization_id = ? GROUP BY author ORDER BY c DESC LIMIT 5",
                (org_id,)
            )
        else:
            cursor.execute("SELECT NULL, 0 WHERE 1=0")
        top_posters = [{"user": r[0], "count": r[1]} for r in cursor.fetchall()]
    else:
        cursor.execute("SELECT COUNT(*) FROM user_profiles")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'")
        total_ai_queries = cursor.fetchone()[0]
        cursor.execute("SELECT author, COUNT(*) as c FROM posts GROUP BY author ORDER BY c DESC LIMIT 5")
        top_posters = [{"user": r[0], "count": r[1]} for r in cursor.fetchall()]

    # Poll participation
    cursor.execute("SELECT COUNT(*) FROM poll_votes")
    total_votes = cursor.fetchone()[0]

    # File count
    total_files = 0
    try:
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        total_files = cursor.fetchone()[0]
    except Exception:
        pass

    conn.close()
    return {
        "total_users": total_users,
        "total_ai_queries": total_ai_queries,
        "top_posters": top_posters,
        "total_votes": total_votes,
        "total_files": total_files
    }

def get_analytics_data(org_id=None):
    """Returns rich analytics: daily activity (last 7 days), top posters, message counts — filtered by org."""
    conn = _get_conn()
    cursor = conn.cursor()

    # Build member filter if org_id is given
    if org_id is not None:
        members = [r[0] for r in conn.execute(
            "SELECT username FROM organization_members WHERE organization_id = ?", (org_id,)
        ).fetchall()]
        if members:
            placeholders = ','.join('?' * len(members))
            msg_filter = f"AND username IN ({placeholders})"
            post_filter = f"AND organization_id = {org_id}"
            msg_params_7d = members
            msg_params_total = members
        else:
            msg_filter = "AND 1=0"
            post_filter = "AND 1=0"
            msg_params_7d = []
            msg_params_total = []
    else:
        msg_filter = ""
        post_filter = ""
        msg_params_7d = []
        msg_params_total = []

    # Daily AI queries last 7 days
    cursor.execute(
        f"""SELECT DATE(timestamp) as day, COUNT(*) as cnt FROM messages
            WHERE role = 'user' AND timestamp >= DATE('now', '-7 days') {msg_filter}
            GROUP BY day ORDER BY day ASC""",
        msg_params_7d
    )
    daily_queries = [{"day": r[0], "count": r[1]} for r in cursor.fetchall()]

    # Daily posts last 7 days
    cursor.execute(
        f"""SELECT DATE(timestamp) as day, COUNT(*) as cnt FROM posts
            WHERE timestamp >= DATE('now', '-7 days') {post_filter}
            GROUP BY day ORDER BY day ASC"""
    )
    daily_posts = [{"day": r[0], "count": r[1]} for r in cursor.fetchall()]

    # Top 5 posters
    cursor.execute(
        f"SELECT author, COUNT(*) as c FROM posts {('WHERE ' + post_filter[4:]) if post_filter else ''} GROUP BY author ORDER BY c DESC LIMIT 5"
    )
    top_posters = [{"user": r[0], "count": r[1]} for r in cursor.fetchall()]

    # Daily chat activity
    cursor.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM room_messages
        WHERE timestamp >= DATE('now', '-7 days')
        GROUP BY day ORDER BY day ASC
    """)
    daily_chat = [{"day": r[0], "count": r[1]} for r in cursor.fetchall()]

    # Total counts
    cursor.execute(f"SELECT COUNT(*) FROM messages WHERE role='user' {msg_filter}", msg_params_total)
    total_queries = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM posts {('WHERE ' + post_filter[4:]) if post_filter else ''}")
    total_posts = cursor.fetchone()[0]

    if org_id is not None:
        total_users = len(members)
    else:
        cursor.execute("SELECT COUNT(*) FROM user_profiles")
        total_users = cursor.fetchone()[0]

    conn.close()
    return {
        "daily_queries": daily_queries,
        "daily_posts": daily_posts,
        "daily_chat": daily_chat,
        "top_posters": top_posters,
        "total_queries": total_queries,
        "total_posts": total_posts,
        "total_users": total_users,
    }

def get_all_personas_v2(org_id=None):
    """Returns all personas including their scope category names, filtered by organization."""
    conn = _get_conn()
    cursor = conn.cursor()
    if org_id is not None:
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM ai_personas p
            LEFT JOIN kb_categories c ON p.scope_category_id = c.id
            WHERE p.organization_id = ? OR p.created_by = 'System'
            ORDER BY p.name ASC
        """, (org_id,))
    else:
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM ai_personas p
            LEFT JOIN kb_categories c ON p.scope_category_id = c.id
            ORDER BY p.name ASC
        """)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    conn.close()
    return results

def get_persona(pid):
    """Retrieves a single persona by ID."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_personas WHERE id = ?", (pid,))
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

# ─── Message Edit Functions ───────────────────


def global_search(query: str, username: str, limit: int = 30, org_id=None):
    """Search across posts, schedules, and DMs for a given user — filtered by org."""
    conn = _get_conn()
    cursor = conn.cursor()
    results = []
    q = f"%{query}%"

    # --- Posts (filtered by org) ---
    if org_id is not None:
        cursor.execute("""
            SELECT p.id, p.content, p.author, p.category, p.timestamp,
                   COALESCE(up.display_name, p.author) as display_name
            FROM posts p
            LEFT JOIN user_profiles up ON p.author = up.username COLLATE NOCASE
            WHERE (p.content LIKE ? OR p.author LIKE ?) AND p.organization_id = ?
            ORDER BY p.timestamp DESC LIMIT ?
        """, (q, q, org_id, limit))
    else:
        cursor.execute("""
            SELECT p.id, p.content, p.author, p.category, p.timestamp,
                   COALESCE(up.display_name, p.author) as display_name
            FROM posts p
            LEFT JOIN user_profiles up ON p.author = up.username COLLATE NOCASE
            WHERE p.content LIKE ? OR p.author LIKE ?
            ORDER BY p.timestamp DESC LIMIT ?
        """, (q, q, limit))
    for r in cursor.fetchall():
        results.append({
            "type": "post", "id": r[0],
            "text": r[1][:200], "author": r[5],
            "category": r[3], "timestamp": r[4],
            "link": "#feed"
        })

    # --- Schedules (filtered by org membership) ---
    if org_id is not None:
        cursor.execute("""
            SELECT s.id, s.title, s.description, s.start_date, s.start_time, s.category, s.username
            FROM schedules s
            JOIN organization_members om ON om.username = s.username COLLATE NOCASE AND om.organization_id = ?
            WHERE (s.title LIKE ? OR s.description LIKE ?) AND (s.username = ? COLLATE NOCASE OR s.is_public = 1)
            ORDER BY s.start_date ASC LIMIT ?
        """, (org_id, q, q, username, limit))
    else:
        cursor.execute("""
            SELECT id, title, description, start_date, start_time, category, username
            FROM schedules
            WHERE (title LIKE ? OR description LIKE ?) AND (username = ? COLLATE NOCASE OR is_public = 1)
            ORDER BY start_date ASC LIMIT ?
        """, (q, q, username, limit))
    for r in cursor.fetchall():
        results.append({
            "type": "schedule", "id": r[0],
            "text": r[1], "author": r[6],
            "category": r[5],
            "timestamp": f"{r[3]} {r[4]}",
            "link": "#calendar"
        })

    # --- Room Messages (only rooms user is member of, in same org) ---
    if org_id is not None:
        cursor.execute("""
            SELECT m.id, m.text, m.username, m.timestamp, r.name
            FROM room_messages m
            JOIN chat_rooms r ON m.room_id = r.id AND r.organization_id = ?
            JOIN room_members rm ON rm.room_id = m.room_id AND rm.username = ? COLLATE NOCASE
            WHERE m.text LIKE ?
            ORDER BY m.timestamp DESC LIMIT ?
        """, (org_id, username, q, limit))
    else:
        cursor.execute("""
            SELECT m.id, m.text, m.username, m.timestamp, r.name
            FROM room_messages m
            JOIN chat_rooms r ON m.room_id = r.id
            JOIN room_members rm ON rm.room_id = m.room_id AND rm.username = ? COLLATE NOCASE
            WHERE m.text LIKE ?
            ORDER BY m.timestamp DESC LIMIT ?
        """, (username, q, limit))
    for r in cursor.fetchall():
        results.append({
            "type": "message", "id": r[0],
            "text": r[1][:200], "author": r[2],
            "category": r[4],
            "timestamp": r[3],
            "link": "#chat"
        })

    # --- DMs (only own — DMs are personal, no org filter needed) ---
    cursor.execute("""
        SELECT id, text, sender, recipient, timestamp
        FROM private_messages
        WHERE (sender = ? COLLATE NOCASE OR recipient = ? COLLATE NOCASE)
          AND text LIKE ?
        ORDER BY timestamp DESC LIMIT ?
    """, (username, username, q, limit))
    for r in cursor.fetchall():
        other = r[3] if r[2].lower() == username.lower() else r[2]
        results.append({
            "type": "dm", "id": r[0],
            "text": r[1][:200], "author": r[2],
            "category": f"DM กับ {other}",
            "timestamp": r[4],
            "link": "#chat"
        })

    conn.close()
    results.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return results[:limit]


# ─── Search Insights ─────────────────────────────
def log_search(query: str, username: str):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO search_history (query, username) VALUES (?, ?)", (query, username))
    conn.commit()
    conn.close()

def get_search_insights(limit: int = 20):
    conn = _get_conn()
    cursor = conn.cursor()
    # Top searches
    cursor.execute("""
        SELECT query, COUNT(*) as count 
        FROM search_history 
        WHERE query != ''
        GROUP BY query 
        ORDER BY count DESC 
        LIMIT ?
    """, (limit,))
    tops = [{"query": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Recent searches
    cursor.execute("SELECT query, username, timestamp FROM search_history ORDER BY timestamp DESC LIMIT ?", (limit,))
    recents = [{"query": r[0], "username": r[1], "timestamp": r[2]} for r in cursor.fetchall()]
    
    conn.close()
    return {"top_searches": tops, "recent_searches": recents}


# ─── Kanban CRUD ─────────────────────────────────────



def _ensure_reset_table():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token       TEXT PRIMARY KEY,
            username    TEXT NOT NULL,
            expires_at  DATETIME NOT NULL,
            used        INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def create_reset_token(username: str) -> str | None:
    """Generate a 1-hour reset token for username. Returns token or None if user not found."""
    _ensure_reset_table()
    conn = _get_conn()
    row = conn.execute(
        "SELECT username FROM user_settings WHERE username = ? AND is_active = 1", (username,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    import secrets, datetime
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
    # Delete old tokens for this user
    conn.execute("DELETE FROM password_reset_tokens WHERE username = ?", (username,))
    conn.execute(
        "INSERT INTO password_reset_tokens (token, username, expires_at) VALUES (?, ?, ?)",
        (token, username, expires),
    )
    conn.commit()
    conn.close()
    return token


def validate_reset_token(token: str) -> str | None:
    """Returns username if token is valid and not yet used, else None."""
    _ensure_reset_table()
    import datetime
    conn = _get_conn()
    # Opportunistically clean up expired tokens on each check
    try:
        conn.execute(
            "DELETE FROM password_reset_tokens WHERE expires_at < ?",
            (datetime.datetime.utcnow().isoformat(),),
        )
        conn.commit()
    except Exception:
        pass
    row = conn.execute(
        "SELECT username, expires_at FROM password_reset_tokens WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    try:
        if datetime.datetime.fromisoformat(row[1]) < datetime.datetime.utcnow():
            return None
    except Exception:
        return None
    return row[0]


def consume_reset_token(token: str, new_password: str) -> bool:
    """Validate + consume token atomically, then update password.
    Uses BEGIN IMMEDIATE so concurrent requests with the same token
    are serialized — only the first call succeeds.
    """
    import datetime as _dt
    _ensure_reset_table()
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        now_iso = _dt.datetime.utcnow().isoformat()
        row = cur.execute(
            "SELECT username FROM password_reset_tokens WHERE token = ? AND expires_at > ?",
            (token, now_iso),
        ).fetchone()
        if not row:
            cur.execute("ROLLBACK")
            return False
        username = row[0]
        active = cur.execute(
            "SELECT 1 FROM user_settings WHERE username = ? AND is_active = 1", (username,)
        ).fetchone()
        if not active:
            cur.execute("ROLLBACK")
            return False
        new_hash = hash_password(new_password)
        cur.execute("UPDATE user_settings SET custom_password = ? WHERE username = ?", (new_hash, username))
        cur.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))
        cur.execute("COMMIT")
        return True
    except Exception:
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _ensure_otp_table():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_otps (
            email       TEXT PRIMARY KEY,
            username    TEXT NOT NULL,
            otp_code    TEXT NOT NULL,
            expires_at  REAL NOT NULL,
            created_at  REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_reset_otp(email: str, username: str) -> str:
    """Generate a random 6-digit OTP for email/username, expiring in 10 minutes (600s)."""
    _ensure_otp_table()
    import random, time
    otp_code = f"{random.randint(100000, 999999)}"
    now = time.time()
    expires_at = now + 600  # 10 mins
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO password_reset_otps (email, username, otp_code, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
        (email.lower().strip(), username, otp_code, expires_at, now)
    )
    conn.commit()
    conn.close()
    return otp_code


def verify_and_consume_reset_otp(email_or_username: str, otp_code: str, new_password: str) -> tuple[bool, str]:
    """Verify 6-digit OTP code and update user's password if valid."""
    _ensure_otp_table()
    import time
    conn = _get_conn()
    now = time.time()
    clean_target = (email_or_username or "").strip().lower()
    clean_otp = (otp_code or "").strip()

    row = conn.execute(
        "SELECT email, username, otp_code, expires_at FROM password_reset_otps WHERE (email = ? COLLATE NOCASE OR username = ? COLLATE NOCASE)",
        (clean_target, clean_target)
    ).fetchone()

    if not row:
        conn.close()
        return False, "ไม่พบรหัส OTP สำหรับอีเมลหรือบัญชีนี้ กรุณาขอรหัส OTP ใหม่"

    db_email, db_username, db_otp, expires_at = row[0], row[1], row[2], row[3]
    if now > expires_at:
        conn.execute("DELETE FROM password_reset_otps WHERE email = ?", (db_email,))
        conn.commit()
        conn.close()
        return False, "รหัส OTP หมดอายุแล้ว (อายุ 10 นาที) กรุณากดขอรหัส OTP ใหม่"

    if not hmac.compare_digest(str(db_otp), str(clean_otp)):
        conn.close()
        return False, "รหัส OTP 6 หลักไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง"

    # Valid OTP! Hash password and update database
    new_hash = hash_password(new_password)
    conn.execute(
        "UPDATE user_settings SET custom_password = ?, session_version = COALESCE(session_version, 1) + 1 WHERE username = ? COLLATE NOCASE",
        (new_hash, db_username)
    )
    conn.execute("DELETE FROM password_reset_otps WHERE email = ?", (db_email,))
    conn.commit()
    conn.close()
    return True, f"ตั้งรหัสผ่านใหม่สำหรับบัญชี {db_username} เรียบร้อยแล้ว"


def get_line_user_id_for_username(username: str) -> str | None:
    """Return LINE user ID linked to this username, or None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT line_user_id FROM user_profiles WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row[0] if row and row[0] else None


# ─── Login Attempt Tracking (SQLite-backed, persists across restarts) ─────────

import time as _time_mod

_LOGIN_ATTEMPT_WINDOW = 3600  # 1 ชั่วโมง
_LOGIN_ATTEMPT_LIMIT  = 20    # max ครั้งต่อ IP ต่อชั่วโมง


def _ensure_login_attempts_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ip         TEXT    NOT NULL,
            username   TEXT,
            success    INTEGER NOT NULL DEFAULT 0,
            ts         INTEGER NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_ts ON login_attempts(ip, ts)")


def record_login_attempt(ip: str, username: str, success: bool) -> None:
    conn = _get_conn()
    try:
        _ensure_login_attempts_table(conn)
        conn.execute(
            "INSERT INTO login_attempts (ip, username, success, ts) VALUES (?, ?, ?, ?)",
            (ip, username, 1 if success else 0, int(_time_mod.time())),
        )
        # prune old rows ทุกครั้งที่บันทึก (เก็บแค่ 24 ชม.)
        conn.execute("DELETE FROM login_attempts WHERE ts < ?", (int(_time_mod.time()) - 86400,))
        conn.commit()
    finally:
        conn.close()


def count_failed_attempts(ip: str, window_seconds: int = _LOGIN_ATTEMPT_WINDOW) -> int:
    """นับจำนวน login ผิดพลาดจาก IP นี้ในช่วงเวลาที่กำหนด"""
    conn = _get_conn()
    try:
        _ensure_login_attempts_table(conn)
        cutoff = int(_time_mod.time()) - window_seconds
        row = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE ip=? AND success=0 AND ts>?",
            (ip, cutoff),
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def is_known_user_ip(username: str, ip: str) -> bool:
    """Check if this IP has previously logged in successfully for this user."""
    conn = _get_conn()
    try:
        _ensure_login_attempts_table(conn)
        row = conn.execute(
            "SELECT 1 FROM login_attempts WHERE username = ? AND ip = ? AND success = 1 LIMIT 1",
            (username, ip)
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


# ─── QR Login Token (DB-backed, safe for multi-worker) ───────────────────────

_QR_TTL = 300  # 5 minutes


def qr_create_token(token: str) -> None:
    now = _time_mod.time()
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS qr_login_tokens (
            token      TEXT PRIMARY KEY,
            status     TEXT DEFAULT 'pending',
            username   TEXT,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.execute(
        "INSERT OR REPLACE INTO qr_login_tokens (token, status, username, created_at, expires_at) VALUES (?, 'pending', NULL, ?, ?)",
        (token, now, now + _QR_TTL),
    )
    conn.execute("DELETE FROM qr_login_tokens WHERE expires_at < ?", (now,))
    conn.commit()
    conn.close()


def qr_get_token(token: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT token, status, username, created_at, expires_at FROM qr_login_tokens WHERE token = ?",
        (token,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {"token": row[0], "status": row[1], "username": row[2],
            "created_at": row[3], "expires_at": row[4]}


def qr_approve_token(token: str, username: str) -> bool:
    conn = _get_conn()
    cur = conn.execute(
        "UPDATE qr_login_tokens SET status='approved', username=? WHERE token=? AND status='pending' AND expires_at > ?",
        (username, token, _time_mod.time()),
    )
    conn.commit()
    conn.close()
    return cur.rowcount == 1


def qr_consume_token(token: str) -> str | None:
    """Returns username and deletes token atomically. Returns None if invalid/expired."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT username FROM qr_login_tokens WHERE token=? AND status='approved' AND expires_at > ?",
        (token, _time_mod.time()),
    ).fetchone()
    if row:
        conn.execute("DELETE FROM qr_login_tokens WHERE token=?", (token,))
        conn.commit()
    conn.close()
    return row[0] if row else None


# ─── Stripe Event Idempotency ─────────────────────────────────────────────────



def is_account_locked(username: str) -> tuple[bool, int]:
    """
    Checks if account is currently locked out due to excessive failed logins.
    Returns (is_locked, seconds_remaining).
    """
    if not username:
        return False, 0
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT locked_until FROM user_settings WHERE username = ? COLLATE NOCASE", (username.strip(),))
        row = cursor.fetchone()
        if not row or not row[0]:
            return False, 0
        locked_until_str = str(row[0])
        try:
            locked_dt = datetime.strptime(locked_until_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
            now_dt = datetime.now()
            if locked_dt > now_dt:
                remaining = int((locked_dt - now_dt).total_seconds())
                return True, max(1, remaining)
        except Exception as e:
            logger.warning(f"[is_account_locked] Date parse error for user '{username}': {e}")
        return False, 0
    finally:
        conn.close()

def record_failed_login(username: str, max_attempts: int = 5, lock_minutes: int = 15) -> dict:
    """
    Increments failed login counter and locks account if threshold exceeded.
    Returns status dict with attempts and whether account became locked.
    """
    if not username:
        return {"locked": False, "attempts": 0}
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT failed_login_attempts FROM user_settings WHERE username = ? COLLATE NOCASE", (username.strip(),))
        row = cursor.fetchone()
        if not row:
            current_attempts = 0
            cursor.execute("INSERT OR IGNORE INTO user_settings (username, failed_login_attempts) VALUES (?, 0)", (username.strip(),))
        else:
            current_attempts = (row[0] or 0)

        new_attempts = current_attempts + 1
        
        locked = False
        locked_until = None
        if new_attempts >= max_attempts:
            locked = True
            locked_until = (datetime.now() + timedelta(minutes=lock_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            UPDATE user_settings 
            SET failed_login_attempts = ?, locked_until = ?
            WHERE username = ? COLLATE NOCASE
        """, (new_attempts, locked_until, username.strip()))
        conn.commit()
        return {"locked": locked, "attempts": new_attempts, "lock_minutes": lock_minutes}
    finally:
        conn.close()

def reset_failed_login(username: str) -> None:
    """Resets failed login attempt counter and clears lock status on successful auth."""
    if not username:
        return
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_settings 
            SET failed_login_attempts = 0, locked_until = NULL
            WHERE username = ? COLLATE NOCASE
        """, (username.strip(),))
        conn.commit()
    finally:
        conn.close()




