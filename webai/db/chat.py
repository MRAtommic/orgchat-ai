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

from .users import get_user_profile
# --- WebSocket Status Management Functions ---

def set_user_online(username, room=None):
    """Mark user as online."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO user_status (username, is_online, current_room, last_activity, updated_at) 
               VALUES (?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (username, room)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] set_user_online: {e}")
        return False

def set_user_offline(username):
    """Mark user as offline."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_status SET is_online = 0, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
            (username,)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] set_user_offline: {e}")
        return False

def set_user_typing(username, room_id):
    """Mark user as typing in a room."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_status SET typing_in_room = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
            (room_id, username)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] set_user_typing: {e}")
        return False

def clear_user_typing(username):
    """Clear typing indicator for user."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_status SET typing_in_room = NULL, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
            (username,)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] clear_user_typing: {e}")
        return False

def get_user_status(username):
    """Get user's current status."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_online, current_room, typing_in_room, last_activity FROM user_status WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "username": username,
                "is_online": bool(row[0]),
                "current_room": row[1],
                "typing_in_room": row[2],
                "last_activity": row[3]
            }
        return {"username": username, "is_online": False}
    except Exception as e:
        print(f"[ERROR] get_user_status: {e}")
        return {"username": username, "is_online": False}

def get_online_users():
    """Get list of all online users."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT username, current_room, typing_in_room FROM user_status WHERE is_online = 1")
        rows = cursor.fetchall()
        conn.close()
        
        return [{"username": r[0], "current_room": r[1], "typing_in_room": r[2]} for r in rows]
    except Exception as e:
        print(f"[ERROR] get_online_users: {e}")
        return []

def mark_message_as_read(message_id, username, room_id=None):
    """Mark message as read by a user (Read receipt)."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO message_read_receipts (message_id, username, room_id, read_at) 
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            (message_id, username, room_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] mark_message_as_read: {e}")
        return False

def get_message_read_receipts(message_id):
    """Get list of users who read a message."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.username, r.read_at, p.avatar_url 
            FROM message_read_receipts r
            LEFT JOIN user_profiles p ON r.username = p.username
            WHERE r.message_id = ? 
            ORDER BY r.read_at
        """, (message_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{"username": r[0], "read_at": r[1], "avatar_url": r[2]} for r in rows]
    except Exception as e:
        print(f"[ERROR] get_message_read_receipts: {e}")
        return []

def mark_room_read(room_id, username, max_id):
    """Mark all messages in a room up to max_id as read by user."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # 1. Update message-specific read receipts (for avatars)
        cursor.execute("""
            SELECT id FROM room_messages 
            WHERE room_id = ? AND id <= ?
        """, (room_id, max_id))
        msg_ids = [r[0] for r in cursor.fetchall()]
        
        for mid in msg_ids:
            cursor.execute("INSERT OR IGNORE INTO message_read_receipts (message_id, username, room_id) VALUES (?, ?, ?)", (mid, username, room_id))
        
        # 2. Update room_members (for unread count badge)
        cursor.execute("""
            UPDATE room_members 
            SET last_read_id = MAX(last_read_id, ?) 
            WHERE room_id = ? AND username = ? COLLATE NOCASE
        """, (max_id, room_id, username))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error marking room messages read: {e}")
        return False

def get_room_reader_avatars(room_id):
    """Get latest message_id read by each user in room with their avatars."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.username, MAX(r.message_id), p.avatar_url, p.display_name
            FROM message_read_receipts r
            LEFT JOIN user_profiles p ON r.username = p.username
            WHERE r.room_id = ?
            GROUP BY r.username
        """, (room_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{"username": r[0], "max_id": r[1], "avatar_url": r[2], "display_name": r[3]} for r in rows]
    except Exception as e:
        print(f"Error get_room_reader_avatars: {e}")
        return []

def mark_dm_read(user_me, user_them, max_id):
    """Mark all incoming messages from user_them to user_me up to max_id as read."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # 1. Update per-message read status table
        cursor.execute("""
            SELECT id FROM private_messages 
            WHERE sender = ? AND recipient = ? AND id <= ?
        """, (user_them, user_me, max_id))
        msg_ids = [r[0] for r in cursor.fetchall()]
        
        for mid in msg_ids:
            cursor.execute("SELECT is_read FROM private_message_read_status WHERE message_id = ?", (mid,))
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO private_message_read_status (message_id, is_read, read_at) VALUES (?, 1, CURRENT_TIMESTAMP)", (mid,))
            elif not row[0]:
                cursor.execute("UPDATE private_message_read_status SET is_read = 1, read_at = CURRENT_TIMESTAMP WHERE message_id = ?", (mid,))
        
        # 2. Update is_read column in private_messages (for unread counts)
        cursor.execute("""
            UPDATE private_messages 
            SET is_read = 1 
            WHERE sender = ? AND recipient = ? AND id <= ?
        """, (user_them, user_me, max_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error marking DM read: {e}")
        return False

def mark_private_message_as_read(message_id):
    """Mark a single private message as read."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM private_message_read_status WHERE message_id = ?", (message_id,))
        if cursor.fetchone():
            cursor.execute("UPDATE private_message_read_status SET is_read = 1, read_at = CURRENT_TIMESTAMP WHERE message_id = ?", (message_id,))
        else:
            cursor.execute("INSERT INTO private_message_read_status (message_id, is_read, read_at) VALUES (?, 1, CURRENT_TIMESTAMP)", (message_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] mark_private_message_as_read: {e}")
        return False


@db_transaction_retry()
def save_message(role, text, sources=None, username="Admin", org_id=1):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        sources_json = json.dumps(sources) if sources else None
        cursor.execute("INSERT INTO messages (role, text, sources, username, organization_id) VALUES (?, ?, ?, ?, ?)", (role, text, sources_json, username, org_id))
        msg_id = cursor.lastrowid
        conn.commit()
        return msg_id
    finally:
        conn.close()

def get_history(username="Admin", limit=50, org_id=1):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, role, text, sources FROM messages WHERE username = ? AND organization_id = ? ORDER BY timestamp DESC LIMIT ?", (username, org_id, limit))
        rows = cursor.fetchall()
    finally:
        conn.close()

    history = []
    for r in rows:
        history.append({
            "id": r[0],
            "role": r[1],
            "text": r[2],
            "sources": json.loads(r[3]) if r[3] else []
        })
    history.reverse()
    return history

def clear_history(username="Admin", org_id=1):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE username = ? AND organization_id = ?", (username, org_id))
        conn.commit()
    finally:
        conn.close()

def delete_message(msg_id, username="Admin"):
    """Delete a specific message by its ID, verifying ownership."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if username == "Admin":
            cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        else:
            cursor.execute("DELETE FROM messages WHERE id = ? AND username = ?", (msg_id, username))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()
    return deleted

# ─── Admin Chat Management ─────────────────────────────

def admin_get_all_ai_messages(limit=200, org_id=None):
    conn = _get_conn()
    cursor = conn.cursor()
    if org_id is not None:
        cursor.execute(
            "SELECT id, username, role, text, timestamp FROM messages WHERE organization_id = ? ORDER BY timestamp DESC LIMIT ?",
            (org_id, limit)
        )
    else:
        cursor.execute("SELECT id, username, role, text, timestamp FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "role": r[2], "text": r[3][:120], "timestamp": r[4]} for r in rows]

def admin_clear_ai_chat(username=None):
    conn = _get_conn()
    cursor = conn.cursor()
    if username:
        cursor.execute("DELETE FROM messages WHERE username = ?", (username,))
    else:
        cursor.execute("DELETE FROM messages")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def admin_get_room_messages(room_id, limit=200):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, text, timestamp FROM room_messages WHERE room_id = ? ORDER BY timestamp DESC LIMIT ?", (room_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "text": r[2][:120], "timestamp": r[3]} for r in rows]

def admin_delete_room_message(msg_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM room_messages WHERE id = ?", (msg_id,))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def delete_room_message(msg_id, username=None, is_admin=False):
    """Delete a room message, verifying ownership or admin status."""
    conn = _get_conn()
    cursor = conn.cursor()
    if is_admin or username == "Admin":
        cursor.execute("DELETE FROM room_messages WHERE id = ?", (msg_id,))
    else:
        # Note: In room_messages, even if user is not Admin, let them delete if they ARE the sender.
        cursor.execute("DELETE FROM room_messages WHERE id = ? AND username = ?", (msg_id, username))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def admin_clear_room_messages(room_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM room_messages WHERE room_id = ?", (room_id,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def admin_get_dm_messages(user1, user2, limit=200):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sender, recipient, text, timestamp
        FROM private_messages
        WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?)
        ORDER BY timestamp DESC LIMIT ?
    """, (user1, user2, user2, user1, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "recipient": r[2], "text": r[3][:120], "timestamp": r[4]} for r in rows]

def admin_delete_dm_message(msg_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM private_messages WHERE id = ?", (msg_id,))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def delete_private_message(msg_id, username=None, is_admin=False, org_id=None):
    """Delete a private message, verifying ownership or admin status and organization."""
    conn = _get_conn()
    cursor = conn.cursor()
    if org_id is not None:
        if is_admin or username == "Admin":
            cursor.execute("DELETE FROM private_messages WHERE id = ? AND organization_id = ?", (msg_id, org_id))
        else:
            cursor.execute("DELETE FROM private_messages WHERE id = ? AND sender = ? AND organization_id = ?", (msg_id, username, org_id))
    else:
        if is_admin or username == "Admin":
            cursor.execute("DELETE FROM private_messages WHERE id = ?", (msg_id,))
        else:
            cursor.execute("DELETE FROM private_messages WHERE id = ? AND sender = ?", (msg_id, username))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def admin_clear_dm(user1, user2):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM private_messages WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?)", (user1, user2, user2, user1))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def admin_get_all_rooms():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, owner FROM chat_rooms ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "owner": r[2]} for r in rows]

def delete_room(room_id):
    """Delete a chat room and all its messages/members (cascade)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM chat_rooms WHERE id = ?", (room_id,))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok


def admin_get_all_dm_pairs():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
          CASE WHEN sender < recipient THEN sender ELSE recipient END AS u1,
          CASE WHEN sender < recipient THEN recipient ELSE sender END AS u2,
          COUNT(*) as msg_count
        FROM private_messages
        GROUP BY u1, u2
        ORDER BY u1, u2
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"user1": r[0], "user2": r[1], "count": r[2]} for r in rows]

@db_transaction_retry()
def save_feedback(username="Admin", feedback_val=0):
    """Save feedback for a specific message."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE messages SET feedback = ? 
        WHERE id = (SELECT id FROM messages WHERE role = 'bot' AND username = ? ORDER BY timestamp DESC LIMIT 1)
    """, (feedback_val, username))
    conn.commit()
    conn.close()

def update_schedule_status(sched_id, status, username="Admin"):
    """Update the status of a schedule item for Kanban."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE schedules SET status = ? WHERE id = ? AND (username = ? OR is_public = 1)", (status, sched_id, username))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok



def toggle_like(post_id, user):
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # Check if already liked
        cursor.execute("SELECT 1 FROM likes WHERE post_id = ? AND user = ?", (post_id, user))
        if cursor.fetchone():
            cursor.execute("DELETE FROM likes WHERE post_id = ? AND user = ?", (post_id, user))
            liked = False
        else:
            cursor.execute("INSERT INTO likes (post_id, user, reaction) VALUES (?, ?, 'like')", (post_id, user))
            liked = True
        conn.commit()
    finally:
        conn.close()
    return liked

@db_transaction_retry()
def set_reaction(post_id, user, reaction):
    """Set or update a specific emoji reaction for a user on a post. Returns (reacted, reaction_type)."""
    VALID_REACTIONS = {
        'like', 'celebrate', 'support', 'insightful', 'target', 'rocket', 'love', 'thankyou',
        'haha', 'wow', 'sad', 'angry'
    }
    if reaction not in VALID_REACTIONS:
        reaction = 'like'
    
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT reaction FROM likes WHERE post_id = ? AND user = ?", (post_id, user))
        row = cursor.fetchone()
        if row:
            if row[0] == reaction:
                # Same reaction → remove (toggle off)
                cursor.execute("DELETE FROM likes WHERE post_id = ? AND user = ?", (post_id, user))
                conn.commit()
                return False, None
            else:
                # Different reaction → update
                cursor.execute("UPDATE likes SET reaction = ? WHERE post_id = ? AND user = ?", (reaction, post_id, user))
                conn.commit()
                return True, reaction
        else:
            cursor.execute("INSERT INTO likes (post_id, user, reaction) VALUES (?, ?, ?)", (post_id, user, reaction))
            conn.commit()
            return True, reaction
    finally:
        conn.close()

def get_post_reactions(post_id):
    """Get all reactions for a post with user info."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.user, l.reaction, p.display_name, p.avatar_url
        FROM likes l
        LEFT JOIN user_profiles p ON l.user = p.username
        WHERE l.post_id = ?
        ORDER BY l.rowid ASC
    """, (post_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "user": r[0],
        "reaction": r[1] or 'like',
        "display_name": r[2] or r[0].capitalize(),
        "avatar_url": r[3]
    } for r in rows]

# --- Poll Functions ---
def add_poll(post_id, question, options):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO polls (post_id, question) VALUES (?, ?)", (post_id, question))
    poll_id = cursor.lastrowid
    for opt in options:
        cursor.execute("INSERT INTO poll_options (poll_id, option_text) VALUES (?, ?)", (poll_id, opt))
    conn.commit()
    conn.close()
    return poll_id

def vote_poll(poll_id, option_id, username):
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO poll_votes (poll_id, option_id, username) VALUES (?, ?, ?)", (poll_id, option_id, username))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error voting: {e}")
        return False
    finally:
        conn.close()

def get_poll_for_post(post_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question FROM polls WHERE post_id = ?", (post_id,))
    poll_row = cursor.fetchone()
    if not poll_row:
        conn.close()
        return None
    
    poll_id = poll_row[0]
    question = poll_row[1]
    
    cursor.execute("SELECT id, option_text FROM poll_options WHERE poll_id = ?", (poll_id,))
    option_rows = cursor.fetchall()
    
    options = []
    for opt_id, opt_text in option_rows:
        # Get users who voted for this option with their avatars
        cursor.execute("""
            SELECT COALESCE(p.display_name, v.username), p.avatar_url
            FROM poll_votes v
            LEFT JOIN user_profiles p ON v.username = p.username COLLATE NOCASE
            WHERE v.option_id = ?
        """, (opt_id,))
        voter_rows = cursor.fetchall()
        voters = [{"name": r[0], "avatar": r[1]} for r in voter_rows]
        options.append({
            "id": opt_id,
            "text": opt_text,
            "votes": len(voters),
            "voters": voters
        })
    
    total_votes = sum(o["votes"] for o in options)
    
    conn.close()
    return {
        "id": poll_id,
        "question": question,
        "options": options,
        "total_votes": total_votes
    }

def get_user_vote(poll_id, username):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT option_id FROM poll_votes WHERE poll_id = ? AND username = ?", (poll_id, username))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None



# --- Unified & Private Chat ---
@db_transaction_retry()
def save_dm(sender, recipient, text, attachments=None, reply_to_id=None, org_id=None):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        attach_json = json.dumps(attachments) if attachments else None
        cursor.execute("""
            INSERT INTO private_messages (sender, recipient, text, attachments, reply_to_id, organization_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sender, recipient, text, attach_json, reply_to_id, org_id))
        msg_id = cursor.lastrowid
        conn.commit()
        return msg_id
    finally:
        conn.close()

def get_dm_history(user1, user2, limit=50, org_id=None):
    conn = _get_conn()
    cursor = conn.cursor()
    # If org_id is provided, enforce org isolation in SQL query
    if org_id is not None:
        cursor.execute("""
            SELECT m.id, m.sender, m.text, m.timestamp, p.display_name, p.avatar_url, m.attachments, m.is_pinned,
                   m.reply_to_id, rm.text as reply_text, rm.sender as reply_sender,
                   COALESCE(rs.is_read, 0) as is_read
            FROM private_messages m
            LEFT JOIN user_profiles p ON m.sender = p.username COLLATE NOCASE
            LEFT JOIN private_messages rm ON m.reply_to_id = rm.id
            LEFT JOIN private_message_read_status rs ON m.id = rs.message_id
            WHERE 
                m.organization_id = ? AND (
                    (m.sender = ? COLLATE NOCASE AND m.recipient = ? COLLATE NOCASE) OR 
                    (m.sender = ? COLLATE NOCASE AND m.recipient = ? COLLATE NOCASE) OR
                    (m.sender = 'AI-Assistant' AND m.recipient = ? COLLATE NOCASE AND 
                     EXISTS (SELECT 1 FROM private_messages pm2 WHERE pm2.sender = ? COLLATE NOCASE AND pm2.recipient = ? COLLATE NOCASE AND pm2.organization_id = ? LIMIT 1))
                )
            ORDER BY m.timestamp DESC LIMIT ?
        """, (org_id, user1, user2, user2, user1, user1, user1, user2, org_id, limit))
    else:
        cursor.execute("""
            SELECT m.id, m.sender, m.text, m.timestamp, p.display_name, p.avatar_url, m.attachments, m.is_pinned,
                   m.reply_to_id, rm.text as reply_text, rm.sender as reply_sender,
                   COALESCE(rs.is_read, 0) as is_read
            FROM private_messages m
            LEFT JOIN user_profiles p ON m.sender = p.username COLLATE NOCASE
            LEFT JOIN private_messages rm ON m.reply_to_id = rm.id
            LEFT JOIN private_message_read_status rs ON m.id = rs.message_id
            WHERE 
                (m.sender = ? COLLATE NOCASE AND m.recipient = ? COLLATE NOCASE) OR 
                (m.sender = ? COLLATE NOCASE AND m.recipient = ? COLLATE NOCASE) OR
                (m.sender = 'AI-Assistant' AND m.recipient = ? COLLATE NOCASE AND 
                 EXISTS (SELECT 1 FROM private_messages pm2 WHERE pm2.sender = ? COLLATE NOCASE AND pm2.recipient = ? COLLATE NOCASE LIMIT 1))
            ORDER BY m.timestamp DESC LIMIT ?
        """, (user1, user2, user2, user1, user1, user1, user2, limit))
        
    rows = cursor.fetchall()
    conn.close()
    rows.reverse()

    return [{
        "id": r[0], "username": r[1], "text": r[2], "timestamp": r[3],
        "display_name": r[4] or r[1].capitalize(), "avatar_url": r[5],
        "attachments": json.loads(r[6]) if r[6] else None,
        "is_pinned": bool(r[7]),
        "reply_to_id": r[8],
        "reply_text": r[9],
        "reply_sender": r[10],
        "is_read": bool(r[11])
    } for r in rows]

def create_room(name, owner, members=None, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_rooms (name, owner, organization_id) VALUES (?, ?, ?)", (name, owner, org_id))
    room_id = cursor.lastrowid

    # Add owner as member
    cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (?, ?)", (room_id, owner))

    # Add other members
    if members:
        for m in members:
            if m != owner:
                cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (?, ?)", (room_id, m))

    conn.commit()
    conn.close()

    return room_id

def add_room_members(room_id, usernames):
    """Add multiple members to an existing room."""
    conn = _get_conn()
    cursor = conn.cursor()
    for u in usernames:
        cursor.execute("INSERT OR IGNORE INTO room_members (room_id, username) VALUES (?, ?)", (room_id, u))
    conn.commit()
    conn.close()
    return True

def remove_room_member(room_id, username):
    """Remove a single member from a room."""
    conn = _get_conn()
    cursor = conn.cursor()
    # Don't remove the owner
    cursor.execute("SELECT owner FROM chat_rooms WHERE id = ?", (room_id,))
    row = cursor.fetchone()
    if row and row[0].lower() == username.lower():
        conn.close()
        return False, "ไม่สามารถลบเจ้าของห้องได้"
    cursor.execute(
        "DELETE FROM room_members WHERE room_id = ? AND username = ? COLLATE NOCASE",
        (room_id, username)
    )
    conn.commit()
    conn.close()
    return True, "ok"

def link_line_user(username, line_user_id):
    """Link a LINE user ID to an OrgChat username. Creates profile if missing."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # 1. Check if user profile exists
        cursor.execute("SELECT 1 FROM user_profiles WHERE username = ? COLLATE NOCASE", (username,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create a basic profile if it doesn't exist
            cursor.execute("INSERT INTO user_profiles (username, display_name) VALUES (?, ?)", (username, username.capitalize()))
            
        # 2. Remove any existing link for this LINE user ID (ensure 1-to-1)
        cursor.execute("UPDATE user_profiles SET line_user_id = NULL WHERE line_user_id = ?", (line_user_id,))
        
        # 3. Set new link
        cursor.execute("UPDATE user_profiles SET line_user_id = ? WHERE username = ? COLLATE NOCASE", (line_user_id, username))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error linking LINE user: {e}")
        return False

def unlink_line_user(username):
    """Unlink a LINE user ID from an OrgChat username by setting line_user_id to NULL."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE user_profiles SET line_user_id = NULL WHERE username = ? COLLATE NOCASE", (username,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error unlinking LINE user {username}: {e}")
        return False

def get_line_id_by_username(username):
    """Get the linked LINE ID for a specific OrgChat user."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT up.line_user_id 
            FROM user_profiles up
            LEFT JOIN user_settings s ON up.username = s.username
            WHERE up.username = ? COLLATE NOCASE AND COALESCE(s.is_active, 1) = 1
        """, (username,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception as e:
        print(f"Error getting LINE ID for {username}: {e}")
        return None

def get_username_by_line_id(line_user_id):
    """Get the OrgChat username for a specific LINE user ID."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT up.username 
            FROM user_profiles up
            LEFT JOIN user_settings s ON up.username = s.username
            WHERE up.line_user_id = ? AND COALESCE(s.is_active, 1) = 1
        """, (line_user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error getting username for LINE ID {line_user_id}: {e}")
        return None

def set_pending_edit(line_user_id, sheet_name, row_index, data=None, state=None):
    """Store the last record added by a user for potential editing."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        data_json = json.dumps(data) if data else "{}"
        cursor.execute("""
            INSERT OR REPLACE INTO pending_edits (line_user_id, sheet_name, row_index, data_json, state, timestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (line_user_id, sheet_name, row_index, data_json, state))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error setting pending edit: {e}")
        return False

def get_pending_edit(line_user_id):
    """Retrieve the last record info for a user."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT sheet_name, row_index, data_json, state FROM pending_edits WHERE line_user_id = ?", (line_user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"sheet_name": row[0], "row_index": row[1], "data": json.loads(row[2]), "state": row[3]}
        return None
    except Exception as e:
        print(f"Error getting pending edit: {e}")
        return None

def update_pending_edit_state(line_user_id, state):
    """Update the state of a pending edit interaction."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE pending_edits SET state = ? WHERE line_user_id = ?", (state, line_user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating pending edit state: {e}")
        return False

def update_group_profile(room_id, name=None, avatar_url=None):
    """Updates group profile name and/or avatar."""
    conn = _get_conn()
    cursor = conn.cursor()
    if name:
        cursor.execute("UPDATE chat_rooms SET name = ? WHERE id = ?", (name, room_id))
    if avatar_url:
        cursor.execute("UPDATE chat_rooms SET avatar_url = ? WHERE id = ?", (avatar_url, room_id))
    conn.commit()
    conn.close()
    return True

@db_transaction_retry()
def add_room_message(room_id, username, text, attachments=None, reply_to_id=None):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        attach_json = json.dumps(attachments) if attachments else None
        cursor.execute("""
            INSERT INTO room_messages (room_id, username, text, attachments, reply_to_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (room_id, username, text, attach_json, reply_to_id))
        msg_id = cursor.lastrowid
        conn.commit()
        return msg_id
    finally:
        conn.close()

def toggle_room_message_pin(msg_id):
    """Toggles the pinned status of a room message."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT is_pinned FROM room_messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if row:
        new_val = 1 if not row[0] else 0
        cursor.execute("UPDATE room_messages SET is_pinned = ? WHERE id = ?", (new_val, msg_id))
        conn.commit()
    conn.close()

def toggle_private_message_pin(msg_id, org_id=None):
    """Toggles the pinned status of a private message within the given organization."""
    conn = _get_conn()
    cursor = conn.cursor()
    if org_id is not None:
        cursor.execute("SELECT is_pinned FROM private_messages WHERE id = ? AND organization_id = ?", (msg_id, org_id))
    else:
        cursor.execute("SELECT is_pinned FROM private_messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if row:
        new_val = 1 if not row[0] else 0
        if org_id is not None:
            cursor.execute("UPDATE private_messages SET is_pinned = ? WHERE id = ? AND organization_id = ?", (new_val, msg_id, org_id))
        else:
            cursor.execute("UPDATE private_messages SET is_pinned = ? WHERE id = ?", (new_val, msg_id))
        conn.commit()
    conn.close()

def get_room_messages(room_id, limit=100):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.username, m.text, m.timestamp, p.display_name, p.avatar_url, m.attachments, m.is_pinned,
               m.reply_to_id, rm.text as reply_text, rm.username as reply_sender,
               (SELECT COUNT(*) FROM message_read_receipts WHERE message_id = m.id) as read_count
        FROM room_messages m
        LEFT JOIN user_profiles p ON m.username = p.username
        LEFT JOIN room_messages rm ON m.reply_to_id = rm.id
        WHERE m.room_id = ?
        ORDER BY m.timestamp DESC LIMIT ?
    """, (room_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    # Reverse rows to return them in chronological order (Oldest first)
    rows.reverse()

    return [{
        "id": r[0], "username": r[1], "text": r[2], "timestamp": r[3],
        "display_name": r[4] or r[1].capitalize(), "avatar_url": r[5],
        "attachments": json.loads(r[6]) if r[6] else None,
        "is_pinned": bool(r[7]),
        "reply_to_id": r[8],
        "reply_text": r[9],
        "reply_sender": r[10],
        "read_count": r[11]
    } for r in rows]

def format_chat_message_preview(text: str, attachments_raw=None) -> str:
    """Format the preview text of a message (handles text, audio, images, files)."""
    text_clean = (text or "").strip()
    if text_clean:
        return text_clean
        
    if attachments_raw:
        try:
            import json
            atts = json.loads(attachments_raw) if isinstance(attachments_raw, str) else attachments_raw
            if isinstance(atts, list) and len(atts) > 0:
                first = atts[0]
                att_type = (first.get("type") or "").lower()
                att_name = first.get("name") or ""
                url = (first.get("url") or "").lower()
                
                if att_type == "audio" or "voice_" in url or url.endswith((".webm", ".mp3", ".wav", ".m4a", ".ogg")):
                    return "🎤 ข้อความเสียง"
                elif att_type == "image" or url.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")):
                    return "📷 รูปภาพ"
                elif att_type == "video" or url.endswith((".mp4", ".mov", ".avi", ".mkv")):
                    return "🎥 วิดีโอ"
                elif att_name:
                    return f"📎 {att_name}"
                else:
                    return "📎 ไฟล์แนบ"
        except Exception:
            pass
            
    return ""

def get_rooms_for_user(username, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()

    # Get rooms with their last message
    cursor.execute("""
        SELECT r.id, r.name, r.avatar_url, r.owner,
               m.text as last_msg, m.timestamp as last_time, m.username as last_sender,
               m.attachments as last_attachments
        FROM chat_rooms r
        JOIN room_members rm ON r.id = rm.room_id
        LEFT JOIN (
            SELECT room_id, text, attachments, timestamp, username,
                   ROW_NUMBER() OVER (PARTITION BY room_id ORDER BY id DESC) as rn
            FROM room_messages
        ) m ON r.id = m.room_id AND m.rn = 1
        WHERE rm.username = ? COLLATE NOCASE
          AND (r.organization_id = ? OR r.organization_id IS NULL)
        ORDER BY COALESCE(m.timestamp, '1970-01-01') DESC
    """, (username, org_id))
    
    rooms = []
    for r in cursor.fetchall():
        last_msg = format_chat_message_preview(r[4], r[7])
        rooms.append({
            "id": r[0], "name": r[1], "avatar_url": r[2], "owner": r[3], "type": "room",
            "last_msg": last_msg, "last_time": r[5], "last_sender": r[6], "last_attachments": r[7]
        })
    
    # Recent DM contacts with their last message
    cursor.execute("""
        SELECT contact, text as last_msg, timestamp as last_time, sender as last_sender, attachments as last_attachments
        FROM (
            SELECT CASE WHEN sender = ? COLLATE NOCASE THEN recipient ELSE sender END as contact,
                   text, attachments, timestamp, sender,
                   ROW_NUMBER() OVER (PARTITION BY CASE WHEN sender = ? COLLATE NOCASE THEN recipient ELSE sender END ORDER BY id DESC) as rn
            FROM private_messages
            WHERE sender = ? COLLATE NOCASE OR recipient = ? COLLATE NOCASE
        ) pm
        WHERE rn = 1
          AND (
              pm.contact = 'AI-Assistant'
              OR EXISTS (
                  SELECT 1 FROM organization_members om1
                  JOIN organization_members om2 ON om1.organization_id = om2.organization_id
                  WHERE om1.username = ? COLLATE NOCASE 
                    AND om2.username = pm.contact COLLATE NOCASE
                    AND om1.organization_id = ?
              )
          )
        ORDER BY timestamp DESC
    """, (username, username, username, username, username, org_id))
    
    contacts = []
    for c in cursor.fetchall():
        contact_name = c[0]
        p = get_user_profile(contact_name)
        last_msg = format_chat_message_preview(c[1], c[4])
        contacts.append({
            "id": contact_name, "name": p["display_name"], 
            "avatar_url": p["avatar_url"], "type": "dm",
            "last_msg": last_msg, "last_time": c[2], "last_sender": c[3], "last_attachments": c[4]
        })
    
    conn.close()
    return {"rooms": rooms, "contacts": contacts}

def update_room_last_read(room_id, username):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM room_messages WHERE room_id = ?", (room_id,))
    last_id = cursor.fetchone()[0] or 0
    cursor.execute("UPDATE room_members SET last_read_id = ? WHERE room_id = ? AND username = ? COLLATE NOCASE", (last_id, room_id, username))
    conn.commit()
    conn.close()

def mark_dm_as_read(sender, recipient):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE private_messages SET is_read = 1 WHERE sender = ? COLLATE NOCASE AND recipient = ? COLLATE NOCASE AND is_read = 0", (sender, recipient))
    conn.commit()
    conn.close()

def get_unread_counts(username):
    conn = _get_conn()
    cursor = conn.cursor()
    counts = {"rooms": {}, "dms": {}}
    
    # Room unreads
    cursor.execute("""
        SELECT rm.room_id, COUNT(m.id)
        FROM room_members rm
        JOIN room_messages m ON rm.room_id = m.room_id
        WHERE rm.username = ? COLLATE NOCASE AND m.id > rm.last_read_id
        GROUP BY rm.room_id
    """, (username,))
    for rid, count in cursor.fetchall():
        counts["rooms"][rid] = count
        
    # DM unreads
    cursor.execute("""
        SELECT sender, COUNT(*)
        FROM private_messages
        WHERE recipient = ? COLLATE NOCASE AND is_read = 0
        GROUP BY sender
    """, (username,))
    for sender, count in cursor.fetchall():
        counts["dms"][sender] = count
        
    conn.close()
    return counts

def get_all_usernames(org_id=1):
    """Fetch all unique usernames registered in user_profiles, filtered by org."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.username FROM user_profiles p
        JOIN organization_members om ON p.username = om.username COLLATE NOCASE
        WHERE om.organization_id = ?
    """, (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]



def edit_room_message(msg_id, new_text, username, is_admin_user=False):
    """Edit a group chat message. Returns True on success."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM room_messages WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        if not row:
            return False
        if not is_admin_user and row[0].lower() != username.lower():
            return False
        cursor.execute(
            "UPDATE room_messages SET text = ?, edited_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_text, msg_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def edit_private_message(msg_id, new_text, username, is_admin_user=False, org_id=None):
    """Edit a DM message within the specific organization. Returns True on success."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        if org_id is not None:
            cursor.execute("SELECT sender FROM private_messages WHERE id = ? AND organization_id = ?", (msg_id, org_id))
        else:
            cursor.execute("SELECT sender FROM private_messages WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        if not row:
            return False
        if not is_admin_user and row[0].lower() != username.lower():
            return False
            
        if org_id is not None:
            cursor.execute(
                "UPDATE private_messages SET text = ?, edited_at = CURRENT_TIMESTAMP WHERE id = ? AND organization_id = ?",
                (new_text, msg_id, org_id)
            )
        else:
            cursor.execute(
                "UPDATE private_messages SET text = ?, edited_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_text, msg_id)
            )
        conn.commit()
        return True
    finally:
        conn.close()


# ─── Global Search ─────────────────────────────


