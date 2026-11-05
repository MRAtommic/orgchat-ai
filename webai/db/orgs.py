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


def get_user_orgs(username: str) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.name, o.slug, o.plan, om.role
        FROM organizations o
        JOIN organization_members om ON o.id = om.organization_id
        WHERE om.username = ? COLLATE NOCASE
        ORDER BY o.id
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "slug": r[2], "plan": r[3], "role": r[4]} for r in rows]


def get_org(org_id: int) -> dict | None:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, slug, plan, max_users, trial_ends_at, created_at FROM organizations WHERE id = ?", (org_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "slug": row[2], "plan": row[3],
            "max_users": row[4], "trial_ends_at": row[5], "created_at": row[6]}


def get_org_stripe_info(org_id: int) -> dict:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT stripe_customer_id, stripe_subscription_id FROM organizations WHERE id=?",
        (org_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"customer_id": row[0], "subscription_id": row[1]}
    return {"customer_id": None, "subscription_id": None}


def set_org_stripe_info(org_id: int, customer_id: str, subscription_id: str = None,
                         plan_expires_at: str = None):
    conn = _get_conn()
    conn.execute(
        """UPDATE organizations
           SET stripe_customer_id=?, stripe_subscription_id=?,
               plan_expires_at=COALESCE(?, plan_expires_at)
           WHERE id=?""",
        (customer_id, subscription_id, plan_expires_at, org_id),
    )
    conn.commit()
    conn.close()


def get_org_member_count(org_id: int) -> int:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM organization_members WHERE organization_id = ?", (org_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_orgs_with_stats() -> list:
    """Admin view: all orgs with plan, member count, and this-month usage."""
    from datetime import date
    ym = date.today().strftime("%Y-%m")
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT
            o.id, o.name, o.slug,
            COALESCE(o.plan, 'free')       AS plan,
            o.plan_expires_at,
            o.stripe_customer_id,
            o.created_at,
            COUNT(DISTINCT om.username)    AS member_count,
            COALESCE(ut.expense_count, 0)  AS expense_count,
            COALESCE(ut.ai_query_count, 0) AS ai_query_count
        FROM organizations o
        LEFT JOIN organization_members om ON om.organization_id = o.id
        LEFT JOIN usage_tracking ut ON ut.org_id = o.id AND ut.year_month = ?
        GROUP BY o.id
        ORDER BY o.id
    """, (ym,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_org_id_by_line_group(group_id: str) -> int | None:
    """Multi-tenant: map LINE group_id → org_id"""
    conn = _get_conn()
    cur = conn.cursor()
    # First check direct org_id mapping
    cur.execute("SELECT org_id, owner_username FROM line_group_mappings WHERE group_id = ?", (group_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if row[0]:  # has explicit org_id
        return int(row[0])
    # Fallback: derive from owner's primary org
    return get_user_primary_org_id(row[1])


def get_org_id_by_line_user(line_user_id: str) -> int | None:
    """Multi-tenant: map LINE user_id → org_id via linked username (checks bot ID or login ID)"""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM user_profiles WHERE line_user_id = ? OR line_login_id = ?", (line_user_id, line_user_id))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return get_user_primary_org_id(row[0])


def get_user_primary_org_id(username: str) -> int | None:
    """Get the first (primary) org_id a user belongs to."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT organization_id FROM organization_members WHERE username = ? COLLATE NOCASE ORDER BY organization_id LIMIT 1",
        (username,)
    )
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row else None


@db_transaction_retry()
def register_line_group(group_id: str, org_id: int, owner_username: str, group_name: str = None):
    """Register or update a LINE group → org mapping."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO line_group_mappings (group_id, org_id, owner_username, group_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(group_id) DO UPDATE SET
            org_id = excluded.org_id,
            owner_username = excluded.owner_username,
            group_name = COALESCE(excluded.group_name, group_name)
    """, (group_id, org_id, owner_username, group_name))
    conn.commit()
    conn.close()


def get_line_groups_for_org(org_id: int, only_enabled: bool = True) -> list:
    """List all LINE groups registered to an org."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT group_id, group_name, owner_username, created_at, line_real_name, line_picture_url, bot_enabled FROM line_group_mappings WHERE org_id = ?"
    if only_enabled:
        query += " AND COALESCE(bot_enabled, 1) = 1"
    query += " ORDER BY created_at DESC"
    cur.execute(query, (org_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_linked_line_users_for_org(org_id: int = None) -> list:
    """Returns a list of unique line_user_id strings that are linked to active users in the given org (or all orgs if org_id is None)."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if org_id is not None:
            cur.execute("""
                SELECT DISTINCT up.line_user_id
                FROM organization_members om
                JOIN user_profiles up ON om.username = up.username
                LEFT JOIN user_settings s ON om.username = s.username
                WHERE om.organization_id = ?
                  AND up.line_user_id IS NOT NULL
                  AND up.line_user_id != ''
                  AND COALESCE(s.is_active, 1) = 1
            """, (org_id,))
        else:
            cur.execute("""
                SELECT DISTINCT up.line_user_id
                FROM user_profiles up
                LEFT JOIN user_settings s ON up.username = s.username
                WHERE up.line_user_id IS NOT NULL
                  AND up.line_user_id != ''
                  AND COALESCE(s.is_active, 1) = 1
            """)
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows if r and r[0]]
    except Exception as e:
        logger.error(f"Error fetching linked line users for org {org_id}: {e}")
        return []



def update_line_group_real_info(group_id: str, real_name: str, picture_url: str = None):
    """Update the real LINE group name and picture fetched from LINE API."""
    conn = _get_conn()
    conn.execute(
        "UPDATE line_group_mappings SET line_real_name=?, line_picture_url=? WHERE group_id=?",
        (real_name, picture_url, group_id)
    )
    conn.commit()
    conn.close()


def signup_create_user_and_org(username: str, password: str, display_name: str, org_name: str) -> tuple:
    """
    Atomically creates user + org in a single transaction.
    Returns (org_id, slug). Raises ValueError("username_exists") or other exceptions on failure.
    """
    import re as _re
    hashed_pw = hash_password(password)
    slug = _re.sub(r'[^a-z0-9]+', '-', org_name.lower()).strip('-') or 'org'

    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM user_profiles WHERE username = ? COLLATE NOCASE", (username,))
        if cursor.fetchone():
            raise ValueError("username_exists")

        base_slug = slug
        suffix = 1
        while True:
            cursor.execute("SELECT id FROM organizations WHERE slug = ?", (slug,))
            if not cursor.fetchone():
                break
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        cursor.execute(
            "INSERT INTO user_profiles (username, display_name, department) VALUES (?, ?, 'General')",
            (username, display_name),
        )
        cursor.execute(
            "INSERT INTO user_settings (username, role, custom_password, can_view_kb, can_edit_kb, can_delete_kb, is_active) VALUES (?, 'user', ?, 1, 1, 1, 1)",
            (username, hashed_pw),
        )
        cursor.execute("INSERT INTO organizations (name, slug) VALUES (?, ?)", (org_name, slug))
        org_id = cursor.lastrowid
        cursor.execute(
            "INSERT OR IGNORE INTO organization_members (organization_id, username, role) VALUES (?, ?, 'admin')",
            (org_id, username),
        )
        # Create organization default room and add the user
        cursor.execute(
            "INSERT INTO chat_rooms (name, owner, organization_id) VALUES ('กลุ่มทั่วไป (General)', 'system', ?)",
            (org_id,)
        )
        default_room_id = cursor.lastrowid
        cursor.execute(
            "INSERT OR IGNORE INTO room_members (room_id, username) VALUES (?, ?)",
            (default_room_id, username)
        )
        conn.commit()
        return org_id, slug
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def signup_create_user_and_join_org(
    username: str, password: str, display_name: str,
    org_id: int, role: str = "member", email: str = "", invited_by: str = "system"
) -> None:
    """Creates a user account and adds them to an existing org (no new org created).
    Raises ValueError('username_exists') if taken, or other exceptions on failure.
    """
    hashed_pw = hash_password(password)
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM user_profiles WHERE username = ? COLLATE NOCASE", (username,))
        if cursor.fetchone():
            raise ValueError("username_exists")
        cursor.execute(
            "INSERT INTO user_profiles (username, display_name, department) VALUES (?, ?, 'General')",
            (username, display_name),
        )
        cursor.execute(
            "INSERT INTO user_settings (username, role, custom_password, email, can_view_kb, can_edit_kb, can_delete_kb, is_active) VALUES (?, 'user', ?, ?, 1, 1, 1, 1)",
            (username, hashed_pw, email),
        )
        cursor.execute(
            "INSERT OR IGNORE INTO organization_members (organization_id, username, role) VALUES (?, ?, ?)",
            (org_id, username, role),
        )
        
        # Get default room for this organization or create one if missing
        cursor.execute(
            "SELECT id FROM chat_rooms WHERE organization_id = ? ORDER BY id ASC LIMIT 1",
            (org_id,)
        )
        room_row = cursor.fetchone()
        if room_row:
            default_room_id = room_row[0]
        else:
            cursor.execute(
                "INSERT INTO chat_rooms (name, owner, organization_id) VALUES ('กลุ่มทั่วไป (General)', 'system', ?)",
                (org_id,)
            )
            default_room_id = cursor.lastrowid

        cursor.execute(
            "INSERT OR IGNORE INTO room_members (room_id, username) VALUES (?, ?)",
            (default_room_id, username)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_organization(name: str, owner_username: str) -> tuple:
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'org'
    conn = _get_conn()
    cursor = conn.cursor()
    base_slug = slug
    suffix = 1
    while True:
        cursor.execute("SELECT id FROM organizations WHERE slug = ?", (slug,))
        if not cursor.fetchone():
            break
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    cursor.execute("INSERT INTO organizations (name, slug) VALUES (?, ?)", (name, slug))
    org_id = cursor.lastrowid
    cursor.execute("""
        INSERT OR IGNORE INTO organization_members (organization_id, username, role)
        VALUES (?, ?, 'admin')
    """, (org_id, owner_username))
    cursor.execute("""
        INSERT OR IGNORE INTO user_settings (username, role, is_active)
        VALUES (?, 'admin', 1)
    """, (owner_username,))
    cursor.execute("""
        UPDATE user_settings SET role = 'admin' WHERE username = ?
    """, (owner_username,))
    
    # Create default room for this organization and add the owner
    cursor.execute(
        "INSERT INTO chat_rooms (name, owner, organization_id) VALUES ('กลุ่มทั่วไป (General)', 'system', ?)",
        (org_id,)
    )
    default_room_id = cursor.lastrowid
    cursor.execute(
        "INSERT OR IGNORE INTO room_members (room_id, username) VALUES (?, ?)",
        (default_room_id, owner_username)
    )
    
    conn.commit()
    conn.close()
    return org_id, slug


def add_org_member(org_id: int, username: str, role: str = 'member', invited_by: str = None):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO organization_members (organization_id, username, role, invited_by)
        VALUES (?, ?, ?, ?)
    """, (org_id, username, role, invited_by))
    cursor.execute("""
        INSERT OR IGNORE INTO user_settings (username, role, is_active)
        VALUES (?, 'user', 1)
    """, (username,))
    conn.commit()
    conn.close()


def add_org_member_with_quota(org_id: int, username: str, role: str,
                               invited_by: str, max_users: int) -> tuple[bool, str]:
    """Atomically check member quota then insert.
    Returns (True, "") on success, (False, reason) if quota exceeded or already member.
    Uses BEGIN IMMEDIATE so concurrent invites can't both slip past the limit.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        if max_users != -1:
            count = cur.execute(
                "SELECT COUNT(*) FROM organization_members WHERE organization_id = ?", (org_id,)
            ).fetchone()[0]
            if count >= max_users:
                cur.execute("ROLLBACK")
                return False, "quota_exceeded"
        cur.execute(
            "INSERT OR IGNORE INTO organization_members (organization_id, username, role, invited_by) VALUES (?, ?, ?, ?)",
            (org_id, username, role, invited_by),
        )
        cur.execute(
            "INSERT OR IGNORE INTO user_settings (username, role, is_active) VALUES (?, 'user', 1)",
            (username,),
        )
        # Auto-add to the org's default chat room (matches signup_create_user_and_join_org behavior)
        default_room = cur.execute(
            "SELECT id FROM chat_rooms WHERE organization_id = ? ORDER BY id ASC LIMIT 1",
            (org_id,)
        ).fetchone()
        if default_room:
            cur.execute(
                "INSERT OR IGNORE INTO room_members (room_id, username) VALUES (?, ?)",
                (default_room[0], username)
            )
        cur.execute("COMMIT")
        return True, ""
    except Exception:
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def get_org_members(org_id: int) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT om.username, om.role, om.joined_at,
               COALESCE(up.display_name, om.username) as display_name,
               up.avatar_url, up.department, up.position, om.invited_by,
               COALESCE(s.is_active, 1) as is_active,
               COALESCE(s.can_view_financial, 0) as can_view_financial,
               s.email,
               COALESCE(s.can_view_kb, 0) as can_view_kb,
               COALESCE(s.can_edit_kb, 0) as can_edit_kb,
               COALESCE(s.can_delete_kb, 0) as can_delete_kb,
               s.notes,
               CASE WHEN gt.username IS NOT NULL THEN 1 ELSE 0 END as google_connected,
               gt.google_email,
               om.manager_username,
               COALESCE(s.can_manage_leave, 0) as can_manage_leave,
               COALESCE(s.can_broadcast_line, 0) as can_broadcast_line,
               COALESCE(s.can_manage_peak, 0) as can_manage_peak
        FROM organization_members om
        LEFT JOIN user_profiles up ON om.username = up.username
        LEFT JOIN user_settings s ON om.username = s.username
        LEFT JOIN user_google_tokens gt ON om.username = gt.username
        WHERE om.organization_id = ?
        ORDER BY CASE om.role WHEN 'admin' THEN 0 ELSE 1 END, om.joined_at
    """, (org_id,))
    rows = cursor.fetchall()

    cursor.execute("SELECT owner_username FROM organizations WHERE id = ?", (org_id,))
    org_row = cursor.fetchone()
    owner_username = org_row[0] if (org_row and org_row[0]) else None
    if not owner_username:
        for r in sorted(rows, key=lambda x: x[2] or ""):
            if r[1] == "admin":
                owner_username = r[0]
                break

    conn.close()

    return [{"username": r[0], "role": r[1], "joined_at": r[2],
             "display_name": r[3], "avatar_url": r[4],
             "department": r[5] or "", "position": r[6] or "", "invited_by": r[7],
             "is_active": bool(r[8]), "can_view_financial": bool(r[9]),
             "email": r[10] or "",
             "can_view_kb": bool(r[11]), "can_edit_kb": bool(r[12]), "can_delete_kb": bool(r[13]),
             "notes": r[14] or "",
             "google_connected": bool(r[15]),
             "google_email": r[16] or "",
             "manager_username": r[17] or "",
             "can_manage_leave": bool(r[18]),
             "can_broadcast_line": bool(r[19]),
             "can_manage_peak": bool(r[20]),
             "is_owner": (r[0].lower() == (owner_username or "").lower())} for r in rows]



def is_org_owner(org_id: int, username: str) -> bool:
    """Checks if the user is the owner of the organization."""
    if not username:
        return False
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT owner_username FROM organizations WHERE id = ?", (org_id,))
    org_row = cursor.fetchone()
    if org_row and org_row[0]:
        conn.close()
        return org_row[0].lower() == username.lower()

    # Creator is the earliest admin who joined the organization
    cursor.execute("""
        SELECT username FROM organization_members 
        WHERE organization_id = ? AND role = 'admin' 
        ORDER BY joined_at ASC LIMIT 1
    """, (org_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None and row[0].lower() == username.lower()


def get_org_owner(org_id: int) -> str | None:
    """Returns the username of the organization's founder / Super Admin."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT owner_username FROM organizations WHERE id = ?", (org_id,))
    org_row = cursor.fetchone()
    if org_row and org_row[0]:
        conn.close()
        return org_row[0]

    cursor.execute("""
        SELECT username FROM organization_members 
        WHERE organization_id = ? AND role = 'admin' 
        ORDER BY joined_at ASC LIMIT 1
    """, (org_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def transfer_org_ownership(org_id: int, current_owner: str, new_owner: str) -> tuple[bool, str]:
    """Transfers the Owner / Super Admin status of an organization to another existing member."""
    if not current_owner or not new_owner:
        return False, "ระบุชื่อผู้ใช้ไม่ถูกต้อง"
    if current_owner.lower() == new_owner.lower():
        return False, "ไม่สามารถโอนสิทธิ์ให้ตนเองได้"
    if not is_org_owner(org_id, current_owner):
        return False, "เฉพาะ Owner ปัจจุบันเท่านั้นที่มีสิทธิ์โอนความเป็นเจ้าขององค์กร"
    
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # 1. Verify target is a member of the organization
        cursor.execute("SELECT role, joined_at FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE", (org_id, new_owner))
        target_row = cursor.fetchone()
        if not target_row:
            return False, f"ไม่พบผู้ใช้ '{new_owner}' ในองค์กรนี้"
        
        # 2. Get current earliest admin joined_at to shift target earlier for legacy fallback
        cursor.execute("""
            SELECT joined_at FROM organization_members 
            WHERE organization_id = ? AND username = ? COLLATE NOCASE
        """, (org_id, current_owner))
        curr_row = cursor.fetchone()
        curr_joined = curr_row[0] if curr_row else "2020-01-01 00:00:00"

        from datetime import datetime as dt, timedelta
        try:
            base_dt = dt.fromisoformat(curr_joined)
            new_joined = (base_dt - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            new_joined = "2019-01-01 00:00:00"

        # 3. Promote target to admin and update joined_at
        cursor.execute("""
            UPDATE organization_members 
            SET role = 'admin', joined_at = ? 
            WHERE organization_id = ? AND username = ? COLLATE NOCASE
        """, (new_joined, org_id, new_owner))

        # 4. Update owner_username in organizations table
        cursor.execute("UPDATE organizations SET owner_username = ? WHERE id = ?", (new_owner, org_id))

        # 5. Ensure current owner remains an admin
        cursor.execute("""
            UPDATE organization_members 
            SET role = 'admin' 
            WHERE organization_id = ? AND username = ? COLLATE NOCASE
        """, (org_id, current_owner))

        conn.commit()
        return True, f"โอนสิทธิ์ความเป็นเจ้าขององค์กรให้คุณ {new_owner} สำเร็จเรียบร้อยแล้ว"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def get_org_quota_info(org_id: int) -> dict:
    """Returns organizational quota usage (members, storage, plan)."""
    try:
        import billing as app_billing
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import billing as app_billing

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name, plan, max_users, plan_expires_at FROM organizations WHERE id = ?", (org_id,))
        org_row = cur.fetchone()
        if not org_row:
            return {}
        org_name, plan_name, org_max_users, expires_at = org_row
        
        cur.execute("SELECT COUNT(*) FROM organization_members WHERE organization_id = ?", (org_id,))
        member_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM organization_members WHERE organization_id = ? AND role = 'admin'", (org_id,))
        admin_count = cur.fetchone()[0]

        active_plan = app_billing.get_effective_plan(org_id)
        plan_config = app_billing.get_plan_config(active_plan)
        limit_users = plan_config.get("limits", {}).get("max_users", org_max_users or 5)
        
        user_percent = 100 if limit_users == -1 else min(100, int((member_count / max(1, limit_users)) * 100))

        return {
            "ok": True,
            "org_name": org_name,
            "plan": active_plan,
            "plan_display": plan_config.get("name", active_plan.capitalize()),
            "member_count": member_count,
            "admin_count": admin_count,
            "max_users": limit_users,
            "is_unlimited": limit_users == -1,
            "usage_percent": user_percent,
            "expires_at": expires_at or "ไม่มีวันหมดอายุ"
        }
    finally:
        conn.close()


def create_org_invite_token(org_id: int, created_by: str, role: str = "member", department: str = None, expires_days: int = 7, max_uses: int = 0) -> str:
    import secrets
    from datetime import datetime, timedelta
    token = "inv_" + secrets.token_urlsafe(16)
    expires_at = (datetime.now() + timedelta(days=expires_days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO org_invite_tokens (token, organization_id, created_by, role, department, max_uses, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (token, org_id, created_by, role, department, max_uses, expires_at))
        conn.commit()
        return token
    finally:
        conn.close()


def get_org_invite_token_info(token: str) -> dict | None:
    from datetime import datetime
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.token, t.organization_id, t.created_by, t.role, t.department, t.expires_at, o.name as org_name
            FROM org_invite_tokens t
            JOIN organizations o ON t.organization_id = o.id
            WHERE t.token = ?
        """, (token,))
        row = cur.fetchone()
        if not row:
            return None
        tok, oid, cby, role, dept, exp, org_name = row
        if exp and exp < datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
            return None
        return {
            "token": tok,
            "org_id": oid,
            "org_name": org_name,
            "created_by": cby,
            "role": role,
            "department": dept,
            "expires_at": exp
        }
    finally:
        conn.close()


def update_org_member_permissions(org_id: int, username: str, perms: dict) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        fields = []
        values = []
        for key in ["can_view_financial", "can_manage_leave", "can_view_kb", "can_edit_kb", "can_delete_kb", "can_broadcast_line", "can_manage_peak"]:
            if key in perms:
                fields.append(f"{key} = ?")
                values.append(1 if perms[key] else 0)
        if fields:
            values.append(username)
            cur.execute(f"UPDATE user_settings SET {', '.join(fields)} WHERE username = ? COLLATE NOCASE", values)
        
        if "manager_username" in perms:
            cur.execute("UPDATE organization_members SET manager_username = ? WHERE organization_id = ? AND username = ? COLLATE NOCASE",
                        (perms["manager_username"] or None, org_id, username))
        
        prof_fields = []
        prof_values = []
        for pkey in ["department", "position", "display_name"]:
            if pkey in perms and perms[pkey] is not None:
                prof_fields.append(f"{pkey} = ?")
                prof_values.append(perms[pkey])
        if prof_fields:
            prof_values.append(username)
            cur.execute(f"UPDATE user_profiles SET {', '.join(prof_fields)} WHERE username = ? COLLATE NOCASE", prof_values)
            
        conn.commit()
        return True
    finally:
        conn.close()


def is_org_admin(org_id: int, username: str) -> bool:
    if not username:
        return False
    # Org Owner always has full admin authority
    if is_org_owner(org_id, username):
        return True
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE", (org_id, username))
    row = cursor.fetchone()
    conn.close()
    return row is not None and row[0] == 'admin'





def is_org_member(org_id: int, username: str) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE", (org_id, username))
    row = cursor.fetchone()
    conn.close()
    return row is not None



def remove_org_member(org_id: int, username: str) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # 1. Look up user email to remove from whitelist of this org
        u_email = cursor.execute("SELECT email FROM user_settings WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if u_email and u_email[0]:
            cursor.execute("DELETE FROM organization_allowed_emails WHERE organization_id = ? AND email = ? COLLATE NOCASE", (org_id, u_email[0].strip().lower()))
        g_email = cursor.execute("SELECT google_email FROM user_google_tokens WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if g_email and g_email[0]:
            cursor.execute("DELETE FROM organization_allowed_emails WHERE organization_id = ? AND email = ? COLLATE NOCASE", (org_id, g_email[0].strip().lower()))

        # 2. Remove from room_members of chat rooms belonging to this organization
        cursor.execute("""
            DELETE FROM room_members WHERE username = ? COLLATE NOCASE AND room_id IN (
                SELECT id FROM chat_rooms WHERE organization_id = ?
            )
        """, (username, org_id))

        # 3. Delete from organization_members
        cursor.execute("DELETE FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE", (org_id, username))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()


def update_org_member_role(org_id: int, username: str, new_role: str) -> bool:
    """Change a member's role within an organization. Returns True if a row was updated."""
    if new_role not in ('admin', 'member'):
        return False
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE organization_members SET role = ? WHERE organization_id = ? AND username = ? COLLATE NOCASE",
        (new_role, org_id, username)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def update_org_member_manager(org_id: int, username: str, manager_username: str) -> bool:
    """Update reports-to manager for a member in an organization."""
    if username.lower() == (manager_username or "").lower():
        return False
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE organization_members SET manager_username = ? WHERE organization_id = ? AND username = ? COLLATE NOCASE",
        (manager_username if manager_username else None, org_id, username)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_org_profile(org_id: int) -> dict | None:
    """Get business profile for a specific organization."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(organization_profiles)")
        cols = [r[1] for r in cursor.fetchall()]
        if cols:
            if "logo_url" not in cols:
                conn.execute("ALTER TABLE organization_profiles ADD COLUMN logo_url TEXT")
            if "signature_url" not in cols:
                conn.execute("ALTER TABLE organization_profiles ADD COLUMN signature_url TEXT")
            conn.commit()
    except Exception as e:
        print(f"Migration error for organization_profiles: {e}")
        
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organization_profiles WHERE org_id = ?", (org_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_org_profile(org_id: int, data: dict) -> bool:
    """Insert or update business profile for a specific organization."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM organization_profiles WHERE org_id = ?", (org_id,))
        exists = cursor.fetchone()
        
        fields = [
            "business_type", "vat_status", "branch_type", "business_name_th",
            "business_name_en", "tax_id", "address_line1", "address_line2",
            "district", "province", "zipcode", "phone", "logo_url", "signature_url"
        ]
        
        if not exists:
            query = f"INSERT INTO organization_profiles (org_id, {', '.join(fields)}) VALUES (?, {', '.join(['?'] * len(fields))})"
            values = [org_id] + [data.get(f, "") for f in fields]
            cursor.execute(query, values)
        else:
            set_clause = ", ".join([f"{f} = ?" for f in fields])
            query = f"UPDATE organization_profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE org_id = ?"
            values = [data.get(f, "") for f in fields] + [org_id]
            cursor.execute(query, values)
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating org profile: {e}")
        return False
    finally:
        conn.close()


def count_org_admins(org_id: int) -> int:
    """Count how many admins are in an organization."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM organization_members WHERE organization_id = ? AND role = 'admin'",
        (org_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count


# --- Organization Departments Management ---

def get_org_departments(org_id: int) -> list:
    """Returns list of departments for an organization, with member counts and member previews."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # Check if table exists
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='organization_departments'")
        if not cur.fetchone():
            return []

        cur.execute("""
            SELECT id, organization_id, name, description, color, icon, created_at,
                   COALESCE(head_username, '')
            FROM organization_departments
            WHERE organization_id = ?
            ORDER BY name COLLATE NOCASE ASC
        """, (org_id,))
        dept_rows = cur.fetchall()

        # If no departments defined yet in table, discover from existing members
        if not dept_rows:
            cur.execute("""
                SELECT DISTINCT up.department
                FROM organization_members om
                JOIN user_profiles up ON om.username = up.username
                WHERE om.organization_id = ? AND up.department IS NOT NULL AND TRIM(up.department) != ''
            """, (org_id,))
            found_depts = [r[0].strip() for r in cur.fetchall() if r[0] and r[0].strip()]
            
            # Default palette
            palette = ["#8b5cf6", "#0284c7", "#f43f5e", "#10b981", "#f59e0b", "#06b6d4", "#6366f1", "#ec4899"]
            for idx, dname in enumerate(found_depts):
                color = palette[idx % len(palette)]
                try:
                    cur.execute("""
                        INSERT OR IGNORE INTO organization_departments (organization_id, name, color)
                        VALUES (?, ?, ?)
                    """, (org_id, dname, color))
                except Exception:
                    pass
            conn.commit()

            # Re-fetch
            cur.execute("""
                SELECT id, organization_id, name, description, color, icon, created_at,
                       COALESCE(head_username, '')
                FROM organization_departments
                WHERE organization_id = ?
                ORDER BY name COLLATE NOCASE ASC
            """, (org_id,))
            dept_rows = cur.fetchall()

        # Fetch all members of this org with profile info
        cur.execute("""
            SELECT om.username, COALESCE(up.display_name, om.username) as display_name,
                   up.avatar_url, up.department, up.position, om.role
            FROM organization_members om
            LEFT JOIN user_profiles up ON om.username = up.username
            WHERE om.organization_id = ?
        """, (org_id,))
        member_rows = cur.fetchall()

        user_display_map = {m[0]: (m[1] or m[0]) for m in member_rows}

        # Group members by department (case-insensitive)
        dept_members_map = {}
        unassigned_members = []
        for m in member_rows:
            m_data = {
                "username": m[0],
                "display_name": m[1] or m[0],
                "avatar_url": m[2] or "",
                "department": m[3] or "",
                "position": m[4] or "",
                "role": m[5] or "member"
            }
            d_clean = (m[3] or "").strip().lower()
            if d_clean:
                dept_members_map.setdefault(d_clean, []).append(m_data)
            else:
                unassigned_members.append(m_data)

        result = []
        for r in dept_rows:
            dept_id, oid, name, desc, color, icon, created_at, head_user = r
            m_list = dept_members_map.get(name.strip().lower(), [])
            head_dname = user_display_map.get(head_user, head_user) if head_user else ""
            result.append({
                "id": dept_id,
                "organization_id": oid,
                "name": name,
                "department_name": name,
                "description": desc or "",
                "color": color or "#3b82f6",
                "icon": icon or "building",
                "head_username": head_user or "",
                "head_display_name": head_dname,
                "created_at": created_at,
                "member_count": len(m_list),
                "members": m_list
            })

        return result
    finally:
        conn.close()


def create_org_department(org_id: int, name: str, description: str = "", color: str = "#3b82f6", icon: str = "building", head_username: str = "") -> tuple:
    name = (name or "").strip()
    if not name:
        return None, "กรุณาระบุชื่อแผนก"
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM organization_departments WHERE organization_id = ? AND name = ? COLLATE NOCASE", (org_id, name))
        if cur.fetchone():
            return None, f"แผนก '{name}' มีอยู่แล้วในองค์กร"
        
        cur.execute("""
            INSERT INTO organization_departments (organization_id, name, description, color, icon, head_username)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (org_id, name, (description or "").strip(), color or "#3b82f6", icon or "building", (head_username or "").strip()))
        dept_id = cur.lastrowid
        conn.commit()
        return dept_id, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()


def update_org_department(dept_id: int, org_id: int, name: str, description: str = None, color: str = None, icon: str = None, head_username: str = None) -> tuple:
    name = (name or "").strip()
    if not name:
        return False, "กรุณาระบุชื่อแผนก"
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM organization_departments WHERE id = ? AND organization_id = ?", (dept_id, org_id))
        row = cur.fetchone()
        if not row:
            return False, "ไม่พบแผนกที่ระบุ"
        old_name = row[0]

        # Check duplicate if name changed
        if name.lower() != old_name.lower():
            cur.execute("SELECT id FROM organization_departments WHERE organization_id = ? AND name = ? COLLATE NOCASE AND id != ?", (org_id, name, dept_id))
            if cur.fetchone():
                return False, f"แผนกชื่อ '{name}' มีอยู่แล้วในองค์กร"

        cur.execute("""
            UPDATE organization_departments
            SET name = ?,
                description = COALESCE(?, description),
                color = COALESCE(?, color),
                icon = COALESCE(?, icon),
                head_username = COALESCE(?, head_username)
            WHERE id = ? AND organization_id = ?
        """, (name, description, color, icon, head_username, dept_id, org_id))

        # If name changed, update user_profiles of members in this org
        if name.lower() != old_name.lower():
            cur.execute("""
                UPDATE user_profiles
                SET department = ?
                WHERE username IN (
                    SELECT username FROM organization_members WHERE organization_id = ?
                ) AND department = ? COLLATE NOCASE
            """, (name, org_id, old_name))

        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def delete_org_department(dept_id: int, org_id: int, fallback_dept: str = "") -> tuple:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM organization_departments WHERE id = ? AND organization_id = ?", (dept_id, org_id))
        row = cur.fetchone()
        if not row:
            return False, "ไม่พบแผนกที่ระบุ"
        old_name = row[0]

        # Migrate members with this department in this org
        cur.execute("""
            UPDATE user_profiles
            SET department = ?
            WHERE username IN (
                SELECT username FROM organization_members WHERE organization_id = ?
            ) AND department = ? COLLATE NOCASE
        """, (fallback_dept, org_id, old_name))

        cur.execute("DELETE FROM organization_departments WHERE id = ? AND organization_id = ?", (dept_id, org_id))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


# --- Whitelist Feature ---

def get_whitelist_emails(org_id: int) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    from datetime import datetime
    now_utc = datetime.utcnow()
    try:
        cursor.execute("SELECT email, added_by, created_at, role FROM organization_allowed_emails WHERE organization_id = ? ORDER BY created_at DESC", (org_id,))
        rows = cursor.fetchall()
        emails = []
        for r in rows:
            created_at = r[2]
            is_expired = False
            if created_at:
                try:
                    dt = datetime.fromisoformat(str(created_at).replace('Z', ''))
                    if (now_utc - dt).total_seconds() > 7 * 86400:
                        is_expired = True
                except Exception:
                    pass
            emails.append({"email": r[0], "added_by": r[1], "created_at": r[2], "role": r[3] or "member", "is_expired": is_expired})
    except Exception:
        cursor.execute("SELECT email, added_by, created_at FROM organization_allowed_emails WHERE organization_id = ? ORDER BY created_at DESC", (org_id,))
        rows = cursor.fetchall()
        emails = []
        for r in rows:
            created_at = r[2]
            is_expired = False
            if created_at:
                try:
                    dt = datetime.fromisoformat(str(created_at).replace('Z', ''))
                    if (now_utc - dt).total_seconds() > 7 * 86400:
                        is_expired = True
                except Exception:
                    pass
            emails.append({"email": r[0], "added_by": r[1], "created_at": r[2], "role": "member", "is_expired": is_expired})
    conn.close()
    return emails

def add_whitelist_email(org_id: int, email: str, added_by: str, role: str = "member") -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute("INSERT INTO organization_allowed_emails (organization_id, email, added_by, role) VALUES (?, ?, ?, ?)", (org_id, email, added_by, role))
        except sqlite3.OperationalError:
            # Fallback if role column doesn't exist yet
            cursor.execute("INSERT INTO organization_allowed_emails (organization_id, email, added_by) VALUES (?, ?, ?)", (org_id, email, added_by))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False # Already exists
    conn.close()
    return success

def remove_whitelist_email(org_id: int, email: str) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM organization_allowed_emails WHERE organization_id = ? AND email = ?", (org_id, email))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_email_whitelisted_organizations(email: str, max_age_days: int = 7) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT organization_id, added_by, created_at, role 
            FROM organization_allowed_emails 
            WHERE email = ? COLLATE NOCASE 
              AND (created_at IS NOT NULL AND datetime(created_at, '+' || ? || ' days') >= datetime('now'))
        """, (email, max_age_days))
        rows = cursor.fetchall()
        orgs = [{"organization_id": r[0], "added_by": r[1], "created_at": r[2], "role": r[3] or "member"} for r in rows]
    except Exception:
        # Fallback if role doesn't exist
        cursor.execute("""
            SELECT organization_id, added_by, created_at 
            FROM organization_allowed_emails 
            WHERE email = ? COLLATE NOCASE
              AND (created_at IS NOT NULL AND datetime(created_at, '+' || ? || ' days') >= datetime('now'))
        """, (email, max_age_days))
        rows = cursor.fetchall()
        orgs = [{"organization_id": r[0], "added_by": r[1], "created_at": r[2], "role": "member"} for r in rows]
    conn.close()
    return orgs

def is_email_allowed(org_id: int, email: str, max_age_days: int = 7) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM organization_allowed_emails 
        WHERE organization_id = ? AND email = ? COLLATE NOCASE
          AND (created_at IS NOT NULL AND datetime(created_at, '+' || ? || ' days') >= datetime('now'))
    """, (org_id, email, max_age_days))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def is_whitelist_enabled(org_id: int) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT whitelist_enabled FROM organizations WHERE id = ?", (org_id,))
        row = cursor.fetchone()
        conn.close()
        return bool(row[0]) if row and row[0] else False
    except sqlite3.OperationalError:
        # Fallback if column doesn't exist yet
        conn.close()
        return False

def set_whitelist_status(org_id: int, enabled: bool):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE organizations SET whitelist_enabled = ? WHERE id = ?", (1 if enabled else 0, org_id))
    conn.commit()
    conn.close()




def superadmin_delete_org(org_id: int) -> bool:
    """Super admin: delete an org and all its associated data."""
    conn = _get_conn()
    try:
        # ลบข้อมูลทั้งหมดที่เชื่อมกับ org นี้ก่อน แล้วค่อยลบ org
        tables_with_org_id = [
            ("messages", "organization_id"),
            ("schedules", "organization_id"),
            ("posts", "organization_id"),
            ("chat_rooms", "organization_id"),
            ("wiki_pages", "organization_id"),
            ("org_google_tokens", "org_id"),
            ("organization_allowed_emails", "organization_id"),
            ("organization_members", "organization_id"),
            ("usage_tracking", "org_id"),
            ("leave_requests", "org_id"),
            ("subscriptions", "org_id"),
            ("invoices", "org_id"),
            ("ai_personas", "org_id"),
        ]
        for table, col in tables_with_org_id:
            try:
                # Security: check table and column names (though hardcoded above)
                if not re.match(r'^[a-zA-Z0-9_]+$', table) or not re.match(r'^[a-zA-Z0-9_]+$', col):
                    continue
                conn.execute(f"DELETE FROM {table} WHERE {col}=?", (org_id,))
            except sqlite3.OperationalError:
                pass  # ตารางอาจไม่มีอยู่ใน schema เก่า (เช่น wiki_pages)
            except Exception as e:
                logger.error(f"[superadmin_delete_org] Error deleting from {table}: {e}")
        
        conn.execute("DELETE FROM organizations WHERE id=?", (org_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"[superadmin_delete_org] fatal error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()




def save_group_mapping(group_id, owner_username, group_name, default_folder_id=None, default_folder_name=None):
    """Save or update a LINE Group mapping for a corporate owner."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO line_group_mappings (group_id, owner_username, group_name, default_folder_id, default_folder_name)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(group_id) DO UPDATE SET
                owner_username = excluded.owner_username,
                group_name = excluded.group_name,
                default_folder_id = excluded.default_folder_id,
                default_folder_name = excluded.default_folder_name
        """, (group_id, owner_username, group_name, default_folder_id, default_folder_name))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving group mapping: {e}")
        return False


def get_group_mapping(group_id):
    """Retrieve details for a specific group mapping."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM line_group_mappings WHERE group_id = ?", (group_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"❌ Error getting group mapping: {e}")
        return None


def get_group_owner(group_id):
    """Retrieve the owner username associated with a LINE group ID."""
    mapping = get_group_mapping(group_id)
    if mapping:
        return mapping.get("owner_username")
    return None


def delete_group_mapping(group_id):
    """Delete a group mapping by group_id."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM line_group_mappings WHERE group_id = ?", (group_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error deleting group mapping: {e}")
        return False


def list_group_mappings(owner_username):
    """List all group mappings owned by a specific user."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM line_group_mappings WHERE owner_username = ? ORDER BY created_at DESC", (owner_username,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error listing group mappings: {e}")
        return []


def update_group_mapping_settings(group_id, group_name=None, default_folder_id=None, default_folder_name=None, bot_enabled=None):
    """Update settings for a specific LINE group mapping."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        updates = []
        params = []
        if group_name is not None:
            updates.append("group_name = ?")
            params.append(group_name)
        if default_folder_id is not None:
            updates.append("default_folder_id = ?")
            params.append(default_folder_id)
        if default_folder_name is not None:
            updates.append("default_folder_name = ?")
            params.append(default_folder_name)
        if bot_enabled is not None:
            updates.append("bot_enabled = ?")
            params.append(1 if bot_enabled else 0)
            
        if not updates:
            conn.close()
            return True
            
        params.append(group_id)
        cursor.execute(f"UPDATE line_group_mappings SET {', '.join(updates)} WHERE group_id = ?", params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error updating group mapping settings: {e}")
        return False


# ─── Password Reset ───────────────────────────────────────────────────────────



def get_org_by_id(org_id: int) -> dict | None:
    """Return org row or None if not found."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, name, slug, plan FROM organizations WHERE id=?", (org_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def is_org_member_active(org_id: int, username: str) -> bool:
    """Fast check: is username still a member of org_id?"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT 1 FROM organization_members WHERE organization_id=? AND username=? COLLATE NOCASE",
        (org_id, username),
    ).fetchone()
    conn.close()
    return row is not None


# ─── LINE Broadcast History ──────────────────────────────────────────────────



def create_org_announcement(org_id, title, content, priority, created_by):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO org_announcements (organization_id, title, content, priority, created_by)
        VALUES (?, ?, ?, ?, ?)
    """, (org_id, title, content, priority, created_by))
    ann_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ann_id

def get_org_announcements(org_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, content, priority, created_by, datetime(created_at, 'localtime')
        FROM org_announcements
        WHERE organization_id = ?
        ORDER BY id DESC LIMIT 50
    """, (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2], "priority": r[3], "created_by": r[4], "created_at": r[5]} for r in rows]

def delete_org_announcement(ann_id, org_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM org_announcements WHERE id = ? AND organization_id = ?", (ann_id, org_id))
    conn.commit()
    conn.close()
    return True





# ═════════════════════════════════════════════════════════════════════
# Org LINE Flex Card Customization
# ═════════════════════════════════════════════════════════════════════

DEFAULT_ORG_FLEX_SETTINGS = {
    "primary_color": "#2563EB",
    "header_bg": "#1B2838",
    "header_text_color": "#FFFFFF",
    "header_icon": "📢",
    "header_title": "ประกาศใหม่",
    "header_sub": "NEW ANNOUNCEMENT",
    "badge_text": "GENERAL",
    "badge_bg": "#EFF6FF",
    "badge_color": "#2563EB",
    "button_style": "primary",
    "button_color": "#2563EB",
    "portal_button_text": "💬 ดูในระบบ OrgChat",
    "feed_primary_color": "#7C3AED",
    "feed_header_bg": "#7C3AED",
    "feed_header_icon": "✨",
    "feed_header_title": "โพสต์ใหม่ใน Feed",
    "feed_header_sub": "NEW FEED POST",
    "card_style": "modern",
    "show_avatar": 1,
    "custom_json_template": ""
}

def get_org_flex_settings(org_id: int) -> dict:
    """Retrieve custom LINE Flex Card settings for the specified organization.
    Returns standard enterprise defaults if not customized."""
    if not org_id:
        return DEFAULT_ORG_FLEX_SETTINGS.copy()
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT org_id, primary_color, header_bg, header_text_color, header_icon,
                   header_title, header_sub, badge_text, badge_bg, badge_color,
                   button_style, button_color, portal_button_text, feed_primary_color,
                   feed_header_bg, feed_header_icon, feed_header_title, feed_header_sub,
                   card_style, show_avatar, custom_json_template
            FROM org_flex_settings
            WHERE org_id = ?
        """, (org_id,))
        row = cursor.fetchone()
        conn.close()
        
        cfg = DEFAULT_ORG_FLEX_SETTINGS.copy()
        cfg["org_id"] = int(org_id)
        if row:
            cfg.update({
                "org_id": row[0],
                "primary_color": row[1] or cfg["primary_color"],
                "header_bg": row[2] or cfg["header_bg"],
                "header_text_color": row[3] or cfg["header_text_color"],
                "header_icon": row[4] or cfg["header_icon"],
                "header_title": row[5] or cfg["header_title"],
                "header_sub": row[6] or cfg["header_sub"],
                "badge_text": row[7] or cfg["badge_text"],
                "badge_bg": row[8] or cfg["badge_bg"],
                "badge_color": row[9] or cfg["badge_color"],
                "button_style": row[10] or cfg["button_style"],
                "button_color": row[11] or cfg["button_color"],
                "portal_button_text": row[12] or cfg["portal_button_text"],
                "feed_primary_color": row[13] or cfg["feed_primary_color"],
                "feed_header_bg": row[14] or cfg["feed_header_bg"],
                "feed_header_icon": row[15] or cfg["feed_header_icon"],
                "feed_header_title": row[16] or cfg["feed_header_title"],
                "feed_header_sub": row[17] or cfg["feed_header_sub"],
                "card_style": row[18] or cfg["card_style"],
                "show_avatar": int(row[19] if row[19] is not None else 1),
                "custom_json_template": row[20] or ""
            })
        return cfg
    except Exception as e:
        logger.error(f"Error fetching org_flex_settings for org {org_id}: {e}")
        return DEFAULT_ORG_FLEX_SETTINGS.copy()

def save_org_flex_settings(org_id: int, settings: dict) -> bool:
    """Save or update custom LINE Flex Card settings for an organization."""
    if not org_id:
        return False
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS org_flex_settings (
                org_id INTEGER PRIMARY KEY,
                primary_color TEXT DEFAULT '#2563EB',
                header_bg TEXT DEFAULT '#1B2838',
                header_text_color TEXT DEFAULT '#FFFFFF',
                header_icon TEXT DEFAULT '📢',
                header_title TEXT DEFAULT 'ประกาศใหม่',
                header_sub TEXT DEFAULT 'NEW ANNOUNCEMENT',
                badge_text TEXT DEFAULT 'GENERAL',
                badge_bg TEXT DEFAULT '#EFF6FF',
                badge_color TEXT DEFAULT '#2563EB',
                button_style TEXT DEFAULT 'primary',
                button_color TEXT DEFAULT '#2563EB',
                portal_button_text TEXT DEFAULT '💬 ดูในระบบ OrgChat',
                feed_primary_color TEXT DEFAULT '#7C3AED',
                feed_header_bg TEXT DEFAULT '#7C3AED',
                feed_header_icon TEXT DEFAULT '✨',
                feed_header_title TEXT DEFAULT 'โพสต์ใหม่ใน Feed',
                feed_header_sub TEXT DEFAULT 'NEW FEED POST',
                card_style TEXT DEFAULT 'modern',
                show_avatar INTEGER DEFAULT 1,
                custom_json_template TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT INTO org_flex_settings (
                org_id, primary_color, header_bg, header_text_color, header_icon,
                header_title, header_sub, badge_text, badge_bg, badge_color,
                button_style, button_color, portal_button_text, feed_primary_color,
                feed_header_bg, feed_header_icon, feed_header_title, feed_header_sub,
                card_style, show_avatar, custom_json_template, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(org_id) DO UPDATE SET
                primary_color = excluded.primary_color,
                header_bg = excluded.header_bg,
                header_text_color = excluded.header_text_color,
                header_icon = excluded.header_icon,
                header_title = excluded.header_title,
                header_sub = excluded.header_sub,
                badge_text = excluded.badge_text,
                badge_bg = excluded.badge_bg,
                badge_color = excluded.badge_color,
                button_style = excluded.button_style,
                button_color = excluded.button_color,
                portal_button_text = excluded.portal_button_text,
                feed_primary_color = excluded.feed_primary_color,
                feed_header_bg = excluded.feed_header_bg,
                feed_header_icon = excluded.feed_header_icon,
                feed_header_title = excluded.feed_header_title,
                feed_header_sub = excluded.feed_header_sub,
                card_style = excluded.card_style,
                show_avatar = excluded.show_avatar,
                custom_json_template = excluded.custom_json_template,
                updated_at = CURRENT_TIMESTAMP
        """, (
            org_id,
            settings.get("primary_color", "#2563EB"),
            settings.get("header_bg", "#1B2838"),
            settings.get("header_text_color", "#FFFFFF"),
            settings.get("header_icon", "📢"),
            settings.get("header_title", "ประกาศใหม่"),
            settings.get("header_sub", "NEW ANNOUNCEMENT"),
            settings.get("badge_text", "GENERAL"),
            settings.get("badge_bg", "#EFF6FF"),
            settings.get("badge_color", "#2563EB"),
            settings.get("button_style", "primary"),
            settings.get("button_color", "#2563EB"),
            settings.get("portal_button_text", "💬 ดูในระบบ OrgChat"),
            settings.get("feed_primary_color", "#7C3AED"),
            settings.get("feed_header_bg", "#7C3AED"),
            settings.get("feed_header_icon", "✨"),
            settings.get("feed_header_title", "โพสต์ใหม่ใน Feed"),
            settings.get("feed_header_sub", "NEW FEED POST"),
            settings.get("card_style", "modern"),
            int(settings.get("show_avatar", 1)),
            settings.get("custom_json_template", "")
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving org_flex_settings for org {org_id}: {e}")
        return False

def reset_org_flex_settings(org_id: int) -> bool:
    """Reset organization's LINE Flex Card settings to standard defaults."""
    if not org_id:
        return False
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM org_flex_settings WHERE org_id = ?", (org_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error resetting org_flex_settings for org {org_id}: {e}")
        return False
