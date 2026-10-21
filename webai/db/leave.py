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

from .orgs import get_org_members
def add_schedule(username, title, start_date, description="", category="General", start_time="09:00", is_public=0, status="todo", target_departments=None, target_users=None, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO schedules (username, title, start_date, start_time, description, category, is_public, status, target_departments, target_users, organization_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, title, start_date, start_time, description, category, is_public, status, target_departments, target_users, org_id))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def get_schedules(username="Admin", org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    # Get user's department for filtering
    cursor.execute("SELECT department FROM user_profiles WHERE username = ?", (username,))
    dept_row = cursor.fetchone()
    user_dept = dept_row[0] if dept_row else "General"

    # Fetch all public events + private events owned by the user + events for user's department + events specifically for user
    # ONLY NON-ARCHIVED items
    cursor.execute("""
        SELECT s.id, s.title, s.start_date, s.start_time, s.description, s.category, s.is_public, s.username,
               p.display_name, p.avatar_url, s.status, s.target_departments, s.target_users
        FROM schedules s
        LEFT JOIN user_profiles p ON s.username = p.username
        WHERE (s.is_public = 1
           OR s.username = ?
           OR (s.target_departments IS NOT NULL AND (',' || s.target_departments || ',') LIKE ?)
           OR (s.target_users IS NOT NULL AND (',' || s.target_users || ',') LIKE ?))
           AND (s.is_archived = 0 OR s.is_archived IS NULL)
           AND (s.organization_id = ? OR s.organization_id IS NULL)
        ORDER BY s.start_date ASC, s.start_time ASC
    """, (username, f'%,{user_dept},%', f'%,{username},%', org_id))

    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r[0], "title": r[1], "date": r[2], "time": r[3],
        "desc": r[4], "category": r[5], "is_public": bool(r[6]),
        "owner": r[7], "display_name": r[8] or r[7].capitalize(), "avatar_url": r[9],
        "status": r[10] or "todo",
        "target_departments": r[11],
        "target_users": r[12]
    } for r in rows]

def get_schedule_by_id(sid: int) -> dict | None:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules WHERE id = ?", (sid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_upcoming_schedules(window_minutes=30):
    """
    Finds schedules that are starting within the next `window_minutes` (and not yet passed),
    and have reminder_sent = 0 (or NULL).
    """
    from datetime import datetime, timedelta
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    now_time = now.strftime("%H:%M")
    end_window = now + timedelta(minutes=window_minutes)
    end_time = end_window.strftime("%H:%M")
    end_date_str = end_window.strftime("%Y-%m-%d")

    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    rows = []
    try:
        cursor.execute("""
            SELECT s.*, p.display_name, p.line_user_id
            FROM schedules s
            LEFT JOIN user_profiles p ON s.username = p.username
            WHERE (s.is_archived = 0 OR s.is_archived IS NULL)
              AND (s.reminder_sent = 0 OR s.reminder_sent IS NULL)
              AND (
                (s.start_date = ? AND s.start_time >= ? AND s.start_time <= ?)
                OR (s.start_date = ? AND s.start_time <= ? AND ? != ?)
              )
            ORDER BY s.start_date ASC, s.start_time ASC
        """, (today_str, now_time, end_time, end_date_str, end_time, today_str, end_date_str))
        rows = [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        logger.error(f"[get_upcoming_schedules] error: {e}")
        rows = []
    finally:
        conn.close()
    return rows


def mark_schedule_reminder_sent(schedule_id):
    """Marks schedule reminder as sent so duplicate notifications are not dispatched."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE schedules SET reminder_sent = 1 WHERE id = ?", (schedule_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"[mark_schedule_reminder_sent] error: {e}")
    finally:
        conn.close()



def update_schedule(sid, title, start_date, description="", category="General", start_time="09:00", is_public=0, status="todo", target_departments=None, target_users=None):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE schedules 
        SET title = ?, start_date = ?, start_time = ?, description = ?, category = ?, is_public = ?, status = ?, target_departments = ?, target_users = ?
        WHERE id = ?
    """, (title, start_date, start_time, description, category, is_public, status, target_departments, target_users, sid))
    conn.commit()
    conn.close()

def delete_schedule(schedule_id, username=None, is_admin=False):
    """Delete a schedule, verifying ownership or admin status."""
    conn = _get_conn()
    cursor = conn.cursor()
    if is_admin:
        cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    else:
        cursor.execute("DELETE FROM schedules WHERE id = ? AND username = ?", (schedule_id, username))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def toggle_schedule_status(sid):
    """Toggle status between 'todo'/'in_progress' and 'done'."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM schedules WHERE id = ?", (sid,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    current_status = row[0] or "todo"
    new_status = "done" if current_status != "done" else "todo"
    
    cursor.execute("UPDATE schedules SET status = ? WHERE id = ?", (new_status, sid))
    conn.commit()
    conn.close()
    return new_status

def delete_past_schedules(username):
    """Delete all schedules older than today for this user."""
    from datetime import date
    today = date.today().isoformat()
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE username = ? AND start_date < ?", (username, today))
    conn.commit()
    conn.close()

def archive_past_schedules(username):
    """Archive (hide) all schedules older than today for this user."""
    from datetime import date
    today = date.today().isoformat()
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE schedules SET is_archived = 1 WHERE username = ? AND start_date < ?", (username, today))
        conn.commit()
    finally:
        conn.close()

def auto_archive_old_schedules(days=90):
    """Automatically archives schedules older than 'days' for everyone."""
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE schedules SET is_archived = 1 WHERE start_date < ? AND is_archived = 0", (cutoff,))
        count = cursor.rowcount
        conn.commit()
        return count
    finally:
        conn.close()




def check_leave_overlap(username: str, start_date: str, end_date: str) -> dict | None:
    """
    ตรวจว่า user มีใบลาที่ overlap กับช่วงวันที่ที่ขอไหม (status ≠ rejected)
    คืน dict ของ leave ที่ทับซ้อน หรือ None ถ้าไม่มี
    """
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT id, type, start_date, end_date, status FROM leave_requests
               WHERE username = ?
                 AND status != 'rejected'
                 AND start_date <= ? AND end_date >= ?
               LIMIT 1""",
            (username, end_date, start_date),
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def create_leave_request(username, leave_type, start_date, end_date, reason, org_id=None):
    """Submit a new leave request, scoped to org."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        # Add org_id column if it doesn't exist (safe migration)
        try:
            cursor.execute("ALTER TABLE leave_requests ADD COLUMN org_id INTEGER")
            conn.commit()
        except Exception:
            pass  # Column already exists
        cursor.execute(
            "INSERT INTO leave_requests (username, type, start_date, end_date, reason, org_id) VALUES (?, ?, ?, ?, ?, ?)",
            (username, leave_type, start_date, end_date, reason, org_id)
        )
        leave_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return leave_id
    except Exception as e:
        print(f"[ERROR] create_leave_request: {e}")
        return None

def get_user_leaves(username):
    """Fetch all leave requests for a specific user."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leave_requests WHERE username = ? ORDER BY timestamp DESC", (username,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] get_user_leaves: {e}")
        return []

def get_all_leaves(limit=200, org_id=None):
    """Fetch all leave requests for admins, filtered by org."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Check if org_id column exists
        cursor.execute("PRAGMA table_info(leave_requests)")
        cols = [r[1] for r in cursor.fetchall()]
        has_org_col = 'org_id' in cols
        if has_org_col and org_id is not None:
            # Get members of this org and filter by them
            members_conn = _get_conn()
            members = [r[0] for r in members_conn.execute(
                "SELECT username FROM organization_members WHERE organization_id = ?", (org_id,)
            ).fetchall()]
            members_conn.close()
            if members:
                placeholders = ','.join('?' * len(members))
                cursor.execute(
                    f"SELECT * FROM leave_requests WHERE (org_id = ? OR username IN ({placeholders})) ORDER BY timestamp DESC LIMIT ?",
                    [org_id] + members + [limit]
                )
            else:
                cursor.execute(
                    "SELECT * FROM leave_requests WHERE org_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (org_id, limit)
                )
        else:
            cursor.execute("SELECT * FROM leave_requests ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] get_all_leaves: {e}")
        return []

def update_leave_status(leave_id, status, approver, note=""):
    """Approve or reject a leave request. Only transitions from 'pending' to prevent double-approval."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE leave_requests SET status = ?, approved_by = ?, approver_note = ? WHERE id = ? AND status = 'pending'",
            (status, approver, note, leave_id)
        )
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except Exception as e:
        logging.getLogger("OrgChatAI").error(f"[update_leave_status] {e}")
        return False

def get_user_leave_balance(username: str, org_id: int = 1, year: int = None) -> dict:
    """
    Calculates current year's used leave days from approved requests and returns quota balance.
    Default yearly quotas: Sick=30, Personal=6, Vacation=6, Other=30.
    """
    from datetime import datetime
    if not year:
        year = datetime.now().year
    username_clean = username.strip() if username else ""
    
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sick_leave, personal_leave, vacation_leave, other_leave 
            FROM user_leave_quotas 
            WHERE username = ? COLLATE NOCASE AND org_id = ? AND year = ?
        """, (username_clean, org_id, year))
        q_row = cursor.fetchone()
        
        if q_row:
            sick_max = q_row["sick_leave"]
            pers_max = q_row["personal_leave"]
            vac_max = q_row["vacation_leave"]
            oth_max = q_row["other_leave"]
        else:
            sick_max, pers_max, vac_max, oth_max = 30, 6, 6, 30
            cursor.execute("""
                INSERT OR IGNORE INTO user_leave_quotas 
                (username, org_id, year, sick_leave, personal_leave, vacation_leave, other_leave)
                VALUES (?, ?, ?, 30, 6, 6, 30)
            """, (username_clean, org_id, year))
            conn.commit()
            
        cursor.execute("""
            SELECT type, leave_type, start_date, end_date 
            FROM leave_requests 
            WHERE (username = ? COLLATE NOCASE OR line_user_id = ?) 
              AND status = 'approved'
              AND (start_date LIKE ? OR end_date LIKE ?)
        """, (username_clean, username_clean, f"{year}-%", f"{year}-%"))
        
        rows = cursor.fetchall()
        
        sick_used, pers_used, vac_used, oth_used = 0, 0, 0, 0
        for r in rows:
            l_type = (r["type"] or r["leave_type"] or "Other").lower()
            try:
                s_dt = datetime.strptime(r["start_date"], "%Y-%m-%d")
                e_dt = datetime.strptime(r["end_date"], "%Y-%m-%d")
                days_count = max(1, (e_dt - s_dt).days + 1)
            except Exception:
                days_count = 1
                
            if any(k in l_type for k in ["sick", "ป่วย"]):
                sick_used += days_count
            elif any(k in l_type for k in ["personal", "กิจ"]):
                pers_used += days_count
            elif any(k in l_type for k in ["vacation", "พักร้อน"]):
                vac_used += days_count
            else:
                oth_used += days_count

        return {
            "username": username_clean,
            "org_id": org_id,
            "year": year,
            "quotas": {
                "sick": {"name": "ลาป่วย", "code": "Sick", "max": sick_max, "used": sick_used, "remaining": max(0, sick_max - sick_used), "color": "emerald"},
                "personal": {"name": "ลากิจ", "code": "Personal", "max": pers_max, "used": pers_used, "remaining": max(0, pers_max - pers_used), "color": "amber"},
                "vacation": {"name": "ลาพักร้อน", "code": "Vacation", "max": vac_max, "used": vac_used, "remaining": max(0, vac_max - vac_used), "color": "blue"},
                "other": {"name": "ลาอื่นๆ", "code": "Other", "max": oth_max, "used": oth_used, "remaining": max(0, oth_max - oth_used), "color": "purple"}
            },
            "total_max": sick_max + pers_max + vac_max + oth_max,
            "total_used": sick_used + pers_used + vac_used + oth_used,
            "total_remaining": max(0, (sick_max + pers_max + vac_max + oth_max) - (sick_used + pers_used + vac_used + oth_used))
        }
    finally:
        conn.close()

def update_user_leave_quota(username: str, org_id: int, year: int, sick: int, personal: int, vacation: int, other: int) -> bool:
    """Inserts or updates yearly custom leave quotas for a user."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_leave_quotas (username, org_id, year, sick_leave, personal_leave, vacation_leave, other_leave, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(username, org_id, year) DO UPDATE SET
                sick_leave = excluded.sick_leave,
                personal_leave = excluded.personal_leave,
                vacation_leave = excluded.vacation_leave,
                other_leave = excluded.other_leave,
                updated_at = CURRENT_TIMESTAMP
        """, (username.strip(), org_id, year, sick, personal, vacation, other))
        conn.commit()
        return True
    except Exception as e:
        logging.getLogger("OrgChatAI").error(f"[update_user_leave_quota] {e}")
        return False
    finally:
        conn.close()

def get_org_leave_balances(org_id: int, year: int = None) -> list:
    """Fetches leave balances for all members of an organization."""
    members = get_org_members(org_id)
    results = []
    for m in members:
        uname = m.get("username")
        if uname:
            balance = get_user_leave_balance(uname, org_id=org_id, year=year)
            balance["display_name"] = m.get("display_name", uname)
            balance["role"] = m.get("role", "member")
            results.append(balance)
    return results



def get_leave_request(leave_id):
    """Retrieves a single leave request by ID."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leave_requests WHERE id = ?", (leave_id,))
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

def get_all_admins():
    """Returns a list of usernames that have 'admin' role."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user_settings WHERE role = 'admin'")
    admins = [r[0] for r in cursor.fetchall()]
    conn.close()
    return admins

def add_leave_comment(leave_id, username, comment):
    """Adds a comment to a leave request."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leave_comments (leave_id, username, comment) VALUES (?, ?, ?)",
        (leave_id, username, comment)
    )
    conn.commit()
    conn.close()
    return True

def get_leave_comments(leave_id):
    """Retrieves all comments for a leave request."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM leave_comments WHERE leave_id = ? ORDER BY timestamp ASC",
        (leave_id,)
    )
    comments = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return comments


# ─── Time Attendance & GPS Clock-in Functions ──────────────────────

def record_attendance(username, org_id, check_type, latitude=None, longitude=None, address=None, distance_meters=0.0, status='on_time', note='', custom_date=None, custom_time=None):
    """Records a time attendance event (check-in / check-out). Supports custom_date/custom_time and note."""
    from datetime import datetime
    now = datetime.now()
    check_date = custom_date or now.strftime("%Y-%m-%d")
    check_time = custom_time or now.strftime("%H:%M:%S")
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO time_attendance (username, org_id, check_date, check_time, check_type, latitude, longitude, address, distance_meters, status, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, org_id or 1, check_date, check_time, check_type, latitude, longitude, address, distance_meters, status, note or ''))
    rec_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": rec_id,
        "username": username,
        "org_id": org_id or 1,
        "check_date": check_date,
        "check_time": check_time,
        "check_type": check_type,
        "latitude": latitude,
        "longitude": longitude,
        "address": address,
        "distance_meters": distance_meters,
        "status": status,
        "note": note or ''
    }


def update_attendance_checkout(attendance_id, check_time=None, latitude=None, longitude=None, address=None, distance_meters=None, status=None):
    """Updates an existing checkout attendance record with the latest timestamp and GPS coordinates."""
    from datetime import datetime
    if not check_time:
        check_time = datetime.now().strftime("%H:%M:%S")
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE time_attendance 
        SET check_time = ?, latitude = COALESCE(?, latitude), longitude = COALESCE(?, longitude),
            address = COALESCE(?, address), distance_meters = COALESCE(?, distance_meters),
            status = COALESCE(?, status)
        WHERE id = ?
    """, (check_time, latitude, longitude, address, distance_meters, status, attendance_id))
    conn.commit()
    conn.close()
    return True


def get_today_attendance(username, org_id=None, date_str=None):
    """Gets today's attendance records for a user."""
    from datetime import datetime
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if org_id:
        cursor.execute(
            "SELECT * FROM time_attendance WHERE username = ? AND org_id = ? AND check_date = ? ORDER BY id ASC",
            (username, org_id, date_str)
        )
    else:
        cursor.execute(
            "SELECT * FROM time_attendance WHERE username = ? AND check_date = ? ORDER BY id ASC",
            (username, date_str)
        )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_org_attendance(org_id, date_from=None, date_to=None, username=None, limit=100):
    """Retrieves attendance records for an organization with optional date and user filters."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM time_attendance WHERE org_id = ?"
    params = [org_id]
    if username:
        query += " AND username = ?"
        params.append(username)
    if date_from:
        query += " AND check_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND check_date <= ?"
        params.append(date_to)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_daily_org_attendance(org_id: int, target_date: str = None, department: str = None, search: str = None):
    """
    Retrieves full daily attendance status for ALL active members in the organization on a given date.
    Returns summary counts (total, present, absent, late, manual) and per-user details.
    """
    from datetime import datetime
    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")

    all_members = get_org_members(org_id) or []
    
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM time_attendance 
        WHERE org_id = ? AND check_date = ? 
        ORDER BY id ASC
    """, (org_id, target_date))
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()

    records_by_user = {}
    for r in records:
        u = r.get("username")
        if u not in records_by_user:
            records_by_user[u] = {"check_in": None, "check_out": None, "all": []}
        records_by_user[u]["all"].append(r)
        if r.get("check_type") == "check_in" and not records_by_user[u]["check_in"]:
            records_by_user[u]["check_in"] = r
        elif r.get("check_type") == "check_out":
            records_by_user[u]["check_out"] = r

    processed_members = []
    for m in all_members:
        u = m.get("username")
        u_records = records_by_user.get(u, {"check_in": None, "check_out": None, "all": []})
        cin = u_records["check_in"]
        cout = u_records["check_out"]

        attended = cin is not None
        if attended:
            st = cin.get("status") or "on_time"
            if st not in ["on_time", "late", "manual_admin", "outside_geofence"]:
                st = "on_time"
        else:
            st = "absent"

        duration_hours = 0.0
        if cin and cout and cin.get("check_time") and cout.get("check_time"):
            try:
                t1 = datetime.strptime(cin["check_time"][:8], "%H:%M:%S")
                t2 = datetime.strptime(cout["check_time"][:8], "%H:%M:%S")
                diff_sec = max(0, (t2 - t1).total_seconds())
                duration_hours = round(diff_sec / 3600.0, 2)
            except Exception:
                duration_hours = 0.0

        raw_note = ""
        if cin:
            raw_note = cin.get("note") or (cin.get("address") if cin.get("status") == "manual_admin" else "") or ""

        item = {
            "username": u,
            "display_name": m.get("display_name") or u,
            "avatar_url": m.get("avatar_url") or "",
            "role": m.get("role") or "member",
            "department": m.get("department") or "ทั่วไป",
            "position": m.get("position") or "",
            "email": m.get("email") or "",
            "attended": attended,
            "status": st,
            "check_in": cin,
            "check_out": cout,
            "work_duration_hours": duration_hours,
            "note": raw_note
        }

        if department and department.strip() and item["department"] != department.strip():
            continue

        if search and search.strip():
            q = search.strip().lower()
            if (q not in item["username"].lower() and 
                q not in item["display_name"].lower() and 
                q not in item["department"].lower() and 
                q not in item["email"].lower()):
                continue

        processed_members.append(item)

    def _sort_key(item):
        if item["attended"] and item["check_in"]:
            return (0, item["check_in"].get("check_time", "99:99"))
        return (1, item["display_name"].lower())

    processed_members.sort(key=_sort_key)

    total_m = len(processed_members)
    present_cnt = sum(1 for x in processed_members if x["attended"])
    absent_cnt = total_m - present_cnt
    late_cnt = sum(1 for x in processed_members if x["status"] == "late")
    manual_cnt = sum(1 for x in processed_members if x["status"] == "manual_admin")
    pct = round((present_cnt / total_m * 100), 1) if total_m > 0 else 0

    return {
        "date": target_date,
        "summary": {
            "total_members": total_m,
            "present_count": present_cnt,
            "absent_count": absent_cnt,
            "late_count": late_cnt,
            "manual_count": manual_cnt,
            "present_percentage": pct
        },
        "members": processed_members
    }


def set_manual_attendance(org_id: int, username: str, check_date: str, check_in_time: str, check_out_time: str = None, status: str = 'manual_admin', note: str = None, updated_by: str = None):
    """
    Inserts or updates an attendance record manually for an employee by Admin.
    Allows marking employee as present ('มา'), setting custom time, or correcting status.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    note_val = note.strip() if note else "บันทึกเวลาแทนโดย Admin"
    updated_by_val = updated_by or "Admin"
    
    if check_in_time and len(check_in_time) == 5:
        check_in_time = f"{check_in_time}:00"
    if check_out_time and len(check_out_time) == 5:
        check_out_time = f"{check_out_time}:00"

    cursor.execute("""
        SELECT id FROM time_attendance 
        WHERE org_id = ? AND username = ? AND check_date = ? AND check_type = 'check_in' 
        LIMIT 1
    """, (org_id, username, check_date))
    cin_row = cursor.fetchone()

    if cin_row:
        cursor.execute("""
            UPDATE time_attendance 
            SET check_time = ?, status = ?, note = ?, updated_by = ?
            WHERE id = ?
        """, (check_in_time, status, note_val, updated_by_val, cin_row[0]))
        cin_id = cin_row[0]
    else:
        cursor.execute("""
            INSERT INTO time_attendance (username, org_id, check_date, check_time, check_type, latitude, longitude, address, distance_meters, status, note, updated_by)
            VALUES (?, ?, ?, ?, 'check_in', NULL, NULL, ?, 0, ?, ?, ?)
        """, (username, org_id, check_date, check_in_time, note_val, status, note_val, updated_by_val))
        cin_id = cursor.lastrowid

    cout_id = None
    if check_out_time:
        cursor.execute("""
            SELECT id FROM time_attendance 
            WHERE org_id = ? AND username = ? AND check_date = ? AND check_type = 'check_out' 
            LIMIT 1
        """, (org_id, username, check_date))
        cout_row = cursor.fetchone()

        if cout_row:
            cursor.execute("""
                UPDATE time_attendance 
                SET check_time = ?, status = 'on_time', note = ?, updated_by = ?
                WHERE id = ?
            """, (check_out_time, note_val, updated_by_val, cout_row[0]))
            cout_id = cout_row[0]
        else:
            cursor.execute("""
                INSERT INTO time_attendance (username, org_id, check_date, check_time, check_type, latitude, longitude, address, distance_meters, status, note, updated_by)
                VALUES (?, ?, ?, ?, 'check_out', NULL, NULL, ?, 0, 'on_time', ?, ?)
            """, (username, org_id, check_date, check_out_time, note_val, note_val, updated_by_val))
            cout_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return {
        "ok": True,
        "check_in_id": cin_id,
        "check_out_id": cout_id,
        "username": username,
        "check_date": check_date
    }


def delete_attendance_record(org_id: int, username: str, check_date: str):
    """
    Deletes all attendance records (check-in and check-out) for a user on a given date.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM time_attendance 
        WHERE org_id = ? AND username = ? AND check_date = ?
    """, (org_id, username, check_date))
    cnt = cursor.rowcount
    conn.commit()
    conn.close()
    return cnt


def add_leave_request(line_user_id, username, leave_type, start_date, end_date, reason, org_id=None):
    conn = _get_conn()
    cursor = conn.cursor()
    # Safe migration check for org_id column
    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN org_id INTEGER")
        conn.commit()
    except Exception:
        pass
    # If org_id is not supplied, lookup from line_group_mappings or organization_members
    if not org_id:
        try:
            r = cursor.execute("SELECT organization_id FROM line_group_mappings WHERE line_group_id = ? LIMIT 1", (line_user_id,)).fetchone()
            if r and r[0]:
                org_id = r[0]
            else:
                r2 = cursor.execute("SELECT organization_id FROM organization_members WHERE username = ? LIMIT 1", (username,)).fetchone()
                if r2 and r2[0]:
                    org_id = r2[0]
        except Exception:
            pass
    if not org_id:
        org_id = 1  # Fallback default org

    cursor.execute("""
        INSERT INTO leave_requests (line_user_id, username, type, leave_type, start_date, end_date, reason, org_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (line_user_id, username, leave_type, leave_type, start_date, end_date, reason, org_id))
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return req_id

def update_leave_request_file(req_id, file_link):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE leave_requests SET file_link = ? WHERE id = ?", (file_link, req_id))
    conn.commit()
    conn.close()

def get_recent_leave_request(line_user_id):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leave_requests WHERE line_user_id = ? ORDER BY id DESC LIMIT 1", (line_user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None



