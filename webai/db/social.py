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

from .chat import get_poll_for_post
# --- Wiki Functions ---

def create_wiki_page(title, content, author, category_id=None, org_id=1):
    import re
    slug = re.sub(r'[^\w\s-]', '', title.lower()).strip().replace(' ', '-')
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO wiki_pages (slug, title, content, author, category_id, organization_id) VALUES (?, ?, ?, ?, ?, ?)",
            (slug, title, content, author, category_id, org_id)
        )
        page_id = cursor.lastrowid
        conn.commit()
        return page_id, slug
    except sqlite3.IntegrityError:
        # Slug collision, append random chars
        import uuid
        slug = f"{slug}-{str(uuid.uuid4())[:4]}"
        cursor.execute(
            "INSERT INTO wiki_pages (slug, title, content, author, category_id, organization_id) VALUES (?, ?, ?, ?, ?, ?)",
            (slug, title, content, author, category_id, org_id)
        )
        page_id = cursor.lastrowid
        conn.commit()
        return page_id, slug
    finally:
        conn.close()

def update_wiki_page(slug, title, content, category_id=None, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE wiki_pages SET title = ?, content = ?, category_id = ?, updated_at = CURRENT_TIMESTAMP WHERE slug = ? AND organization_id = ?",
        (title, content, category_id, slug, org_id)
    )
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def get_wiki_pages(org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT slug, title, author, updated_at FROM wiki_pages WHERE organization_id = ? ORDER BY updated_at DESC", (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"slug": r[0], "title": r[1], "author": r[2], "updated_at": r[3]} for r in rows]

def get_wiki_page(slug, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT title, content, author, category_id, updated_at FROM wiki_pages WHERE slug = ? AND organization_id = ?", (slug, org_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"title": row[0], "content": row[1], "author": row[2], "category_id": row[3], "updated_at": row[4]}
    return None

def delete_wiki_page(slug, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wiki_pages WHERE slug = ? AND organization_id = ?", (slug, org_id))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok



# --- Social Feed ---
@db_transaction_retry()
def add_post(content, author="Anonymous", category="General", link=None, attachments=None, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (content, author, category, link, attachments, organization_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (content, author, category, link, json.dumps(attachments) if attachments else None, org_id))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id

def get_posts(category=None, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    base_query = """
        SELECT p.id, p.content, p.author, p.category, p.summary, p.timestamp, p.link, p.attachments, p.is_pinned,
               up.display_name, up.avatar_url,
               (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) as like_count,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) as comment_count
        FROM posts p
        LEFT JOIN user_profiles up ON p.author = up.username
        WHERE (p.organization_id = ? OR p.organization_id IS NULL)
    """
    cat_clean = str(category).strip() if category else ""
    if cat_clean and cat_clean.lower() not in ["all", "ทั้งหมด", "ทุกหมวดหมู่", "none", ""]:
        if cat_clean.lower() in ["general", "ทั่วไป"]:
            cursor.execute(base_query + " AND (p.category = 'General' OR p.category = 'ทั่วไป' OR p.category IS NULL OR p.category = '') ORDER BY p.is_pinned DESC, p.timestamp DESC", (org_id,))
        else:
            cursor.execute(base_query + " AND p.category = ? ORDER BY p.is_pinned DESC, p.timestamp DESC", (org_id, category))
    else:
        cursor.execute(base_query + " ORDER BY p.is_pinned DESC, p.timestamp DESC", (org_id,))

    rows = cursor.fetchall()
    conn.close()

    posts = []
    for r in rows:
        p = {
            "id": r[0], "content": r[1], "author": r[2], "category": r[3],
            "summary": r[4], "timestamp": r[5], "link": r[6],
            "attachments": json.loads(r[7]) if r[7] else [],
            "is_pinned": bool(r[8]),
            "display_name": r[9] or r[2].capitalize(),
            "avatar_url": r[10],
            "likes": r[11], "comments": r[12]
        }
        p["poll"] = get_poll_for_post(p["id"])
        posts.append(p)
    return posts

def get_post(post_id: int) -> dict | None:
    """ดึงโพสต์เดียว — ใช้ตรวจ ownership ก่อน update/delete"""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT id, author, content, category FROM posts WHERE id=?", (post_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def check_post_access(post_id: int, org_id: int = 1) -> bool:
    """Fast indexed check if a post belongs to the organization (or public/unscoped)."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT 1 FROM posts WHERE id = ? AND (organization_id = ? OR organization_id IS NULL) LIMIT 1",
        (post_id, org_id)
    ).fetchone()
    conn.close()
    return row is not None


def update_post(post_id, content, category, link=None):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE posts SET content = ?, category = ?, link = ? WHERE id = ?
    """, (content, category, link, post_id))
    conn.commit()
    conn.close()

def delete_post(post_id, username=None, is_admin=False):
    """Delete a post, verifying ownership or admin status."""
    conn = _get_conn()
    cursor = conn.cursor()
    if is_admin:
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    else:
        cursor.execute("DELETE FROM posts WHERE id = ? AND author = ?", (post_id, username))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def toggle_pin(post_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT is_pinned FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    if row:
        # Pinned logic: 1 if not previously pinned (0 or None), else 0
        new_val = 1 if not row[0] else 0
        cursor.execute("UPDATE posts SET is_pinned = ? WHERE id = ?", (new_val, post_id))
        conn.commit()
    conn.close()

def update_post_summary(post_id, summary):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET summary = ? WHERE id = ?", (summary, post_id))
    conn.commit()
    conn.close()

@db_transaction_retry()
def add_comment(post_id, content, author="Anonymous"):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (post_id, content, author) VALUES (?, ?, ?)", (post_id, content, author))
    cid = cursor.lastrowid
    conn.commit()
    conn.close()
    return cid

def delete_comment(comment_id, username=None, is_admin=False):
    """Delete a comment, verifying ownership or admin status."""
    conn = _get_conn()
    cursor = conn.cursor()
    if is_admin:
        cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    else:
        cursor.execute("DELETE FROM comments WHERE id = ? AND author = ?", (comment_id, username))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def get_comments(post_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.content, c.author, c.timestamp, p.display_name, p.avatar_url
        FROM comments c
        LEFT JOIN user_profiles p ON c.author = p.username
        WHERE c.post_id = ? 
        ORDER BY c.timestamp ASC
    """, (post_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "content": r[1], 
        "author": r[2], 
        "timestamp": r[3],
        "display_name": r[4] or r[2].capitalize(),
        "avatar_url": r[5]
    } for r in rows]

@db_transaction_retry()


def record_post_view(post_id, username):
    """Record that a user has viewed a post."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO post_views (post_id, username) VALUES (?, ?)", (post_id, username))
        conn.commit()
    finally:
        conn.close()

def get_post_views(post_id):
    """Get list of users who viewed a post with their avatars."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.username, COALESCE(p.display_name, v.username), p.avatar_url, v.timestamp
        FROM post_views v
        LEFT JOIN user_profiles p ON v.username = p.username COLLATE NOCASE
        WHERE v.post_id = ?
        ORDER BY v.timestamp DESC
    """, (post_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"username": r[0], "display_name": r[1], "avatar": r[2], "time": r[3]} for r in rows]

# ─── Admin Dashboard Stats ─────────────────────


def kanban_init_db():
    """Ensure kanban tables exist (idempotent)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL DEFAULT 1,
            title TEXT NOT NULL,
            position INTEGER DEFAULT 0,
            color TEXT DEFAULT '#6366f1',
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            assignee TEXT,
            due_date TEXT,
            position INTEGER DEFAULT 0,
            color TEXT,
            labels TEXT,
            is_done INTEGER DEFAULT 0,
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(column_id) REFERENCES kanban_columns(id) ON DELETE CASCADE
        )
    """)
    # Migrations
    try: cursor.execute("ALTER TABLE kanban_cards ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE kanban_cards ADD COLUMN is_done INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE kanban_columns ADD COLUMN org_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError: pass

    conn.commit()
    conn.close()

def _kanban_seed_defaults(cursor, org_id: int):
    """Seed 3 default columns for an org that has none."""
    defaults = [
        ("To Do", 0, "#6366f1"),
        ("In Progress", 1, "#f59e0b"),
        ("Done", 2, "#10b981"),
    ]
    for title, pos, color in defaults:
        cursor.execute(
            "INSERT INTO kanban_columns (org_id, title, position, color, created_by) VALUES (?, ?, ?, ?, ?)",
            (org_id, title, pos, color, "System")
        )

def kanban_get_board(org_id: int):
    """Return all columns with their cards for a specific org."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kanban_columns WHERE org_id=? ORDER BY position ASC, id ASC", (org_id,))
    columns = [dict(row) for row in cursor.fetchall()]
    if not columns:
        _kanban_seed_defaults(cursor, org_id)
        conn.commit()
        cursor.execute("SELECT * FROM kanban_columns WHERE org_id=? ORDER BY position ASC, id ASC", (org_id,))
        columns = [dict(row) for row in cursor.fetchall()]
    for col in columns:
        cursor.execute(
            "SELECT * FROM kanban_cards WHERE column_id=? ORDER BY position ASC, id ASC",
            (col["id"],)
        )
        col["cards"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return columns

def kanban_add_column(title, color="#6366f1", created_by="System", org_id: int = 1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(position),0)+1 FROM kanban_columns WHERE org_id=?", (org_id,))
    pos = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO kanban_columns (org_id, title, position, color, created_by) VALUES (?, ?, ?, ?, ?)",
        (org_id, title, pos, color, created_by)
    )
    col_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return col_id

def kanban_get_column(col_id: int, org_id: int = None) -> dict | None:
    """ดึงข้อมูล column เดียว — ถ้าระบุ org_id จะตรวจ ownership ด้วย"""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    if org_id is not None:
        row = conn.execute("SELECT * FROM kanban_columns WHERE id=? AND org_id=?", (col_id, org_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM kanban_columns WHERE id=?", (col_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def kanban_update_column(col_id, title=None, color=None):
    conn = _get_conn()
    cursor = conn.cursor()
    if title is not None:
        cursor.execute("UPDATE kanban_columns SET title=? WHERE id=?", (title, col_id))
    if color is not None:
        cursor.execute("UPDATE kanban_columns SET color=? WHERE id=?", (color, col_id))
    conn.commit()
    conn.close()

def kanban_delete_column(col_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM kanban_columns WHERE id=?", (col_id,))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def kanban_add_card(column_id, title, description="", priority="medium", assignee="", due_date="", labels="", color="", created_by="System", is_done=0):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(position),0)+1 FROM kanban_cards WHERE column_id=?", (column_id,))
    pos = cursor.fetchone()[0]
    cursor.execute(
        """INSERT INTO kanban_cards (column_id, title, description, priority, assignee, due_date, position, labels, color, created_by, is_done)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (column_id, title, description, priority, assignee, due_date, pos, labels, color, created_by, int(is_done))
    )
    card_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return card_id

def kanban_update_card(card_id, **kwargs):
    allowed = {"title", "description", "priority", "assignee", "due_date", "labels", "color", "column_id", "position", "is_done"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    conn = _get_conn()
    cursor = conn.cursor()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [card_id]
    cursor.execute(f"UPDATE kanban_cards SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def kanban_delete_card(card_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kanban_cards WHERE id=?", (card_id,))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def kanban_get_card(card_id):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kanban_cards WHERE id=?", (card_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def kanban_move_card(card_id, new_column_id, new_position):
    """Move card and perform full re-index of affected columns to prevent gaps/duplicates."""
    conn = _get_conn()
    cursor = conn.cursor()
    
    # 1. Get current card info
    cursor.execute("SELECT column_id FROM kanban_cards WHERE id=?", (card_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    old_column_id = row[0]

    # 2. Extract the card from everywhere & temporarily set its position to a safe virtual spot
    cursor.execute("UPDATE kanban_cards SET column_id = ?, position = -1 WHERE id = ?", (new_column_id, card_id))

    # 3. Helper to re-index a column
    def reindex_column(col_id, target_card_id=None, target_pos=None):
        cursor.execute("SELECT id FROM kanban_cards WHERE column_id = ? AND id != ? ORDER BY position ASC, id ASC", 
                       (col_id, target_card_id if target_card_id else -1))
        cards = [r[0] for r in cursor.fetchall()]
        
        # Insert target card at target position if this is the new column
        if target_card_id and target_pos is not None:
            cards.insert(max(0, min(len(cards), target_pos)), target_card_id)
            
        # Write back new positions
        for idx, cid in enumerate(cards):
            cursor.execute("UPDATE kanban_cards SET position = ? WHERE id = ?", (idx, cid))

    # 4. Re-index affected columns
    reindex_column(old_column_id)
    if old_column_id != new_column_id:
        reindex_column(new_column_id, card_id, new_position)
    else:
        # If same column, we need to re-index differently because the card is still there
        # but with position -1. The first reindex_column call already ignored it.
        # So we just re-run with the target insertion.
        reindex_column(new_column_id, card_id, new_position)

    conn.commit()
    conn.close()
    return True

def kanban_reorder_columns(order_list, org_id=None):
    """order_list: list of {id, position}"""
    conn = _get_conn()
    cursor = conn.cursor()
    for item in order_list:
        if org_id is not None:
            cursor.execute("UPDATE kanban_columns SET position=? WHERE id=? AND org_id=?", (item["position"], item["id"], org_id))
        else:
            cursor.execute("UPDATE kanban_columns SET position=? WHERE id=?", (item["position"], item["id"]))
    conn.commit()
    conn.close()

# ─── Wiki CRUD ────────────────────────────────────────

def wiki_get_all_pages(org_id=1):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, slug, title, author, category_id, created_at, updated_at FROM wiki_pages WHERE organization_id = ? ORDER BY updated_at DESC",
        (org_id,)
    )
    pages = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return pages

def wiki_get_page(page_id=None, slug=None, org_id=1):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if page_id:
        cursor.execute("SELECT * FROM wiki_pages WHERE id=? AND organization_id=?", (page_id, org_id))
    elif slug:
        cursor.execute("SELECT * FROM wiki_pages WHERE slug=? AND organization_id=?", (slug, org_id))
    else:
        conn.close()
        return None
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def wiki_create_page(title, content, author="System", category_id=None, org_id=1):
    import re, datetime
    slug = re.sub(r"[^a-z0-9-]", "-", title.lower())
    slug = re.sub(r"-+", "-", slug).strip("-") or f"page-{int(datetime.datetime.now().timestamp())}"
    conn = _get_conn()
    cursor = conn.cursor()
    # Ensure slug uniqueness
    base_slug = slug
    i = 1
    while True:
        cursor.execute("SELECT id FROM wiki_pages WHERE slug=? AND organization_id=?", (slug, org_id))
        if not cursor.fetchone():
            break
        slug = f"{base_slug}-{i}"
        i += 1
    cursor.execute(
        "INSERT INTO wiki_pages (slug, title, content, author, category_id, organization_id) VALUES (?, ?, ?, ?, ?, ?)",
        (slug, title, content, author, category_id, org_id)
    )
    page_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return page_id, slug

def wiki_update_page(page_id, title=None, content=None, category_id=None, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    updates = []
    values = []
    if title is not None:
        updates.append("title=?")
        values.append(title)
    if content is not None:
        updates.append("content=?")
        values.append(content)
    if category_id is not None:
        updates.append("category_id=?")
        values.append(category_id)
    if not updates:
        conn.close()
        return False
    updates.append("updated_at=CURRENT_TIMESTAMP")
    values.append(page_id)
    values.append(org_id)
    cursor.execute(f"UPDATE wiki_pages SET {', '.join(updates)} WHERE id=? AND organization_id=?", values)
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def wiki_delete_page(page_id, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wiki_pages WHERE id=? AND organization_id=?", (page_id, org_id))
    ok = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def wiki_search(query, org_id=1):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    q = f"%{query}%"
    cursor.execute(
        "SELECT id, slug, title, author, updated_at FROM wiki_pages WHERE (title LIKE ? OR content LIKE ?) AND organization_id = ? ORDER BY updated_at DESC LIMIT 20",
        (q, q, org_id)
    )
    results = [dict(r) for r in cursor.fetchall()]


def get_all_lunch_places():
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lunch_places ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_random_lunch():
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lunch_places ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_lunch_place(name, type_str="", location="", added_by="Admin"):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lunch_places (name, type, location, added_by) VALUES (?,?,?,?)", (name, type_str, location, added_by))
    conn.commit()
    conn.close()



# ══════════════════════════════════════════════════════════════
# MEETING NOTES CRUD
# ══════════════════════════════════════════════════════════════

def meeting_note_create(org_id: int, data: dict) -> int:
    import json as _j
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO meeting_notes (org_id, title, audio_filename, transcript, summary, action_items, participants, meeting_date, created_by)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (org_id, data.get('title',''), data.get('audio_filename',''),
                 data.get('transcript',''), data.get('summary',''),
                 _j.dumps(data.get('action_items',[])),
                 data.get('participants',''), data.get('meeting_date',''), data.get('created_by','')))
    mid = cur.lastrowid; conn.commit(); conn.close(); return mid

def meeting_note_list(org_id: int) -> list:
    import json as _j
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM meeting_notes WHERE org_id=? ORDER BY created_at DESC", (org_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try: d['action_items'] = _j.loads(d.get('action_items') or '[]')
        except (ValueError, TypeError): d['action_items'] = []
        result.append(d)
    return result

def meeting_note_get(mid: int, org_id: int) -> dict | None:
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM meeting_notes WHERE id=? AND org_id=?", (mid, org_id)).fetchone()
    conn.close()
    if not row: return None
    d = dict(row)
    try: d['action_items'] = _j.loads(d.get('action_items') or '[]')
    except (ValueError, TypeError): d['action_items'] = []
    return d

def meeting_note_update(mid: int, org_id: int, data: dict) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""UPDATE meeting_notes SET title=?, transcript=?, summary=?, action_items=?, participants=?, meeting_date=?, wiki_page_id=?
                   WHERE id=? AND org_id=?""",
                (data.get('title',''), data.get('transcript',''), data.get('summary',''),
                 _j.dumps(data.get('action_items',[])), data.get('participants',''),
                 data.get('meeting_date',''), data.get('wiki_page_id'), mid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def meeting_note_delete(mid: int, org_id: int) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM meeting_notes WHERE id=? AND org_id=?", (mid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok




# ══════════════════════════════════════════════════════
# Wiki & Kanban & Posts Database Helpers
# ══════════════════════════════════════════════════════

def get_all_posts(org_id: int = 1) -> list[dict]:
    """Retrieve social posts for an organization."""
    return get_posts(category=None, org_id=org_id)

def get_post_by_id(pid: int) -> dict | None:
    return get_post(pid)

def wiki_get_all_pages(org_id: int = 1) -> list[dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM wiki_pages WHERE org_id = ? ORDER BY updated_at DESC", (org_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def wiki_search(q: str, org_id: int = 1) -> list[dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    pattern = f"%{q}%"
    rows = conn.execute("SELECT * FROM wiki_pages WHERE org_id = ? AND (title LIKE ? OR content LIKE ?) ORDER BY updated_at DESC", (org_id, pattern, pattern)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def wiki_create_page(title: str, content: str = "", author: str = "Anonymous", category_id: int = None, org_id: int = 1) -> tuple[int, str]:
    import re
    slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', title.lower()).strip('_') or f"page_{int(time.time())}"
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO wiki_pages (title, slug, content, author, category_id, org_id) VALUES (?, ?, ?, ?, ?, ?)",
        (title, slug, content, author, category_id, org_id)
    )
    page_id = cur.lastrowid
    conn.commit()
    conn.close()
    return page_id, slug

def wiki_get_page(page_id: int = None, slug: str = None, org_id: int = 1) -> dict | None:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    if page_id:
        row = conn.execute("SELECT * FROM wiki_pages WHERE id = ? AND org_id = ?", (page_id, org_id)).fetchone()
    elif slug:
        row = conn.execute("SELECT * FROM wiki_pages WHERE slug = ? AND org_id = ?", (slug, org_id)).fetchone()
    else:
        row = None
    if row:
        conn.execute("UPDATE wiki_pages SET views = views + 1 WHERE id = ?", (row["id"],))
        conn.commit()
    conn.close()
    return dict(row) if row else None

def wiki_update_page(page_id: int, title: str = None, content: str = None, category_id: int = None, org_id: int = 1) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    fields = []
    params = []
    if title is not None:
        fields.append("title = ?"); params.append(title)
    if content is not None:
        fields.append("content = ?"); params.append(content)
    if category_id is not None:
        fields.append("category_id = ?"); params.append(category_id)
    fields.append("updated_at = CURRENT_TIMESTAMP")
    if not fields:
        conn.close()
        return False
    params.extend([page_id, org_id])
    cur.execute(f"UPDATE wiki_pages SET {', '.join(fields)} WHERE id = ? AND org_id = ?", params)
    ok = cur.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def wiki_delete_page(page_id: int, org_id: int = 1) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM wiki_pages WHERE id = ? AND org_id = ?", (page_id, org_id))
    ok = cur.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def kanban_get_card(card_id: int) -> dict | None:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM kanban_cards WHERE id = ?", (card_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def kanban_get_column(column_id: int, org_id: int = 1) -> dict | None:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM kanban_columns WHERE id = ? AND org_id = ?", (column_id, org_id)).fetchone()
    conn.close()
    if not row:
        # Fallback dummy column for standard Kanban 1/2/3/4 board setup
        return {"id": column_id, "name": f"Column {column_id}", "org_id": org_id, "position": column_id}
    return dict(row)

def kanban_update_card(card_id: int, **kwargs) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    allowed_cols = {"title", "description", "column_id", "position", "assignee", "due_date", "priority", "is_done"}
    fields = []
    params = []
    for k, v in kwargs.items():
        if k in allowed_cols:
            fields.append(f"{k} = ?")
            params.append(v)
    if not fields:
        conn.close()
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(card_id)
    cur.execute(f"UPDATE kanban_cards SET {', '.join(fields)} WHERE id = ?", params)
    ok = cur.rowcount > 0
    conn.commit()
    conn.close()
    return ok




