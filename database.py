import sys, io
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
if hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8')
    except Exception: pass

import sqlite3
import json
from pathlib import Path
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    import sys
    print("❌ FATAL: bcrypt not installed — cannot start safely. Run: pip install bcrypt", file=sys.stderr)
    sys.exit(1)

DB_PATH = Path("chat_history.db")


def hash_password(password: str) -> str:
    """Hash a password with bcrypt. Falls back to plaintext if bcrypt unavailable."""
    if not password:
        return ""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return password


def check_password(password: str, stored: str) -> bool:
    """Verify a password against stored hash (or plaintext fallback)."""
    if not password or not stored:
        return False
    if BCRYPT_AVAILABLE and stored.startswith("$2b$"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    # Fallback: plaintext comparison (for legacy or non-bcrypt installs)
    return password == stored

import os
import re
import random
import time
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

DB_TYPE = "sqlite"


class DynamicCursorWrapper:
    def __init__(self, cursor, is_postgres=False, connection_wrapper=None):
        self._cursor = cursor
        self._is_postgres = is_postgres
        self._connection_wrapper = connection_wrapper
        self._lastrowid = None

    def translate_sql(self, sql):
        if not self._is_postgres or not sql:
            return sql
        
        # Translate SQLite AUTOINCREMENT to Postgres SERIAL
        sql_translated = re.sub(r'(?i)\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b', 'SERIAL PRIMARY KEY', sql)
        sql_translated = re.sub(r'(?i)\bINTEGER\s+PRIMARY\s+KEY\b', 'SERIAL PRIMARY KEY', sql_translated)
        
        # Translate SQLite placeholder '?' to PostgreSQL '%s'
        sql_translated = sql_translated.replace("?", "%s")
        
        upper_sql = sql_translated.upper().strip()
        
        # Translate SQLite DATETIME to Postgres TIMESTAMP
        sql_translated = re.sub(r'(?i)\bDATETIME\b', 'TIMESTAMP', sql_translated)
            
        # Translate SQLite GROUP_CONCAT to Postgres STRING_AGG
        sql_translated = re.sub(r'(?i)\bGROUP_CONCAT\b', 'STRING_AGG', sql_translated)
            
        # Translate INSERT OR IGNORE / INSERT OR REPLACE to PostgreSQL syntax
        if "INSERT OR IGNORE" in upper_sql:
            sql_translated = sql_translated.replace("INSERT OR IGNORE INTO", "INSERT INTO")
            sql_translated = sql_translated.replace("INSERT OR IGNORE", "INSERT")
            if "ON CONFLICT" not in upper_sql:
                sql_translated += " ON CONFLICT DO NOTHING"
        elif "INSERT OR REPLACE" in upper_sql:
            sql_translated = sql_translated.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            sql_translated = sql_translated.replace("INSERT OR REPLACE", "INSERT")
            if "ON CONFLICT" not in upper_sql:
                if "USER_SETTINGS" in upper_sql:
                    sql_translated += " ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP"
                elif "APP_SETTINGS" in upper_sql:
                    sql_translated += " ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP"
                elif "USER_PROFILES" in upper_sql:
                    sql_translated += " ON CONFLICT (username) DO UPDATE SET display_name = EXCLUDED.display_name, avatar_url = EXCLUDED.avatar_url, background_url = EXCLUDED.background_url, department = EXCLUDED.department, position = EXCLUDED.position, line_user_id = EXCLUDED.line_user_id"
                elif "PENDING_EDITS" in upper_sql:
                    sql_translated += " ON CONFLICT (line_user_id) DO UPDATE SET sheet_name = EXCLUDED.sheet_name, row_index = EXCLUDED.row_index, data_json = EXCLUDED.data_json, state = EXCLUDED.state, timestamp = CURRENT_TIMESTAMP"

        # Append RETURNING id to get lastrowid on Postgres
        if upper_sql.startswith("INSERT INTO") and "RETURNING" not in upper_sql:
            no_id_tables = ["LIKES", "POST_VIEWS", "PUSH_SUBSCRIPTIONS", "USER_PROFILES", "USER_SETTINGS", "APP_SETTINGS", "PENDING_EDITS", "LINE_GROUP_MAPPINGS"]
            if not any(t in upper_sql for t in no_id_tables):
                sql_translated += " RETURNING id"

        # Quote reserved word 'user' outside of single-quoted strings
        def quote_user(match):
            if match.group(1):
                return '"user"'
            return match.group(0)
        sql_translated = re.sub(r"'[^']*'|(\buser\b)", quote_user, sql_translated)

        return sql_translated

    def execute(self, sql, params=None):
        sql_translated = self.translate_sql(sql)
        if self._is_postgres and sql_translated.upper().strip().startswith("PRAGMA"):
            return None  # Ignore SQLite PRAGMAs on Postgres
            
        use_savepoint = self._is_postgres and self._connection_wrapper and not sql_translated.upper().strip().startswith(("BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE"))
        
        if use_savepoint:
            try:
                with self._connection_wrapper._conn.cursor() as sp_cur:
                    sp_cur.execute("SAVEPOINT dynamic_sp")
            except Exception:
                pass

        try:
            if params is None:
                self._cursor.execute(sql_translated)
            else:
                self._cursor.execute(sql_translated, params)
                
            if self._is_postgres and "RETURNING" in sql_translated.upper():
                try:
                    if self._cursor.description:
                        rows = self._cursor.fetchall()
                        if rows:
                            self._lastrowid = rows[0][0]
                except Exception:
                    pass
            
            if use_savepoint:
                try:
                    with self._connection_wrapper._conn.cursor() as sp_cur:
                        sp_cur.execute("RELEASE SAVEPOINT dynamic_sp")
                except Exception:
                    pass
        except Exception as e:
            if use_savepoint:
                try:
                    with self._connection_wrapper._conn.cursor() as sp_cur:
                        sp_cur.execute("ROLLBACK TO SAVEPOINT dynamic_sp")
                except Exception:
                    pass
            if self._is_postgres:
                err_msg = str(e).lower()
                # Map Postgres UniqueViolation/IntegrityError to sqlite3.IntegrityError
                if "unique" in err_msg or "duplicate" in err_msg or "integrity" in err_msg:
                    raise sqlite3.IntegrityError(str(e)) from e
                # Map all other exceptions to sqlite3.OperationalError
                raise sqlite3.OperationalError(str(e)) from e
            raise
        return self

    def executemany(self, sql, seq_of_params):
        sql_translated = self.translate_sql(sql)
        use_savepoint = self._is_postgres and self._connection_wrapper and not sql_translated.upper().strip().startswith(("BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE"))
        
        if use_savepoint:
            try:
                with self._connection_wrapper._conn.cursor() as sp_cur:
                    sp_cur.execute("SAVEPOINT dynamic_sp")
            except Exception:
                pass
                
        try:
            res = self._cursor.executemany(sql_translated, seq_of_params)
            if use_savepoint:
                try:
                    with self._connection_wrapper._conn.cursor() as sp_cur:
                        sp_cur.execute("RELEASE SAVEPOINT dynamic_sp")
                except Exception:
                    pass
            return res
        except Exception as e:
            if use_savepoint:
                try:
                    with self._connection_wrapper._conn.cursor() as sp_cur:
                        sp_cur.execute("ROLLBACK TO SAVEPOINT dynamic_sp")
                except Exception:
                    pass
            if self._is_postgres:
                err_msg = str(e).lower()
                if "unique" in err_msg or "duplicate" in err_msg or "integrity" in err_msg:
                    raise sqlite3.IntegrityError(str(e)) from e
                raise sqlite3.OperationalError(str(e)) from e
            raise

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._is_postgres and self._connection_wrapper and self._connection_wrapper.row_factory:
            return PostgresRow(self._cursor.description, row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        if self._is_postgres and self._connection_wrapper and self._connection_wrapper.row_factory:
            return [PostgresRow(self._cursor.description, r) for r in rows]
        return rows

    def fetchmany(self, size=None):
        if size is None:
            rows = self._cursor.fetchmany()
        else:
            rows = self._cursor.fetchmany(size)
        if not rows:
            return []
        if self._is_postgres and self._connection_wrapper and self._connection_wrapper.row_factory:
            return [PostgresRow(self._cursor.description, r) for r in rows]
        return rows

    @property
    def lastrowid(self):
        if self._is_postgres:
            return self._lastrowid
        return getattr(self._cursor, "lastrowid", None)

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return getattr(self._cursor, "rowcount", -1)

    def close(self):
        self._cursor.close()

    def __iter__(self):
        for row in self._cursor:
            if self._is_postgres and self._connection_wrapper and self._connection_wrapper.row_factory:
                yield PostgresRow(self._cursor.description, row)
            else:
                yield row


class DynamicConnectionWrapper:
    def __init__(self, conn, is_postgres=False, pool=None):
        self._conn = conn
        self._is_postgres = is_postgres
        self._row_factory = None
        self._pool = pool

    @property
    def row_factory(self):
        if self._is_postgres:
            return self._row_factory
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, val):
        if self._is_postgres:
            self._row_factory = val
        else:
            self._conn.row_factory = val

    def cursor(self, *args, **kwargs):
        raw_cursor = self._conn.cursor(*args, **kwargs)
        return DynamicCursorWrapper(raw_cursor, self._is_postgres, connection_wrapper=self)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        if self._is_postgres and self._pool:
            self._pool.putconn(self._conn)
        else:
            return self._conn.close()

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:
                pass
        else:
            try:
                self.commit()
            except Exception:
                pass


def _get_conn(timeout: int = 30):
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-16000")
    return DynamicConnectionWrapper(conn, is_postgres=False)



def db_transaction_retry(max_retries=5, initial_backoff=0.05):
    """Decorator to automatically retry database write operations if they encounter sqlite3.OperationalError (locks) or Postgres equivalent errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_err = e
                    backoff = (initial_backoff * (2 ** attempt)) + random.uniform(0, 0.05)
                    import logging
                    logger = logging.getLogger("database_retry")
                    logger.warning(f"⚠️ [DB Retry] Database error in {func.__name__} (attempt {attempt+1}/{max_retries}). Retrying in {backoff:.3f}s... Error: {e}")
                    time.sleep(backoff)
                    continue
                except Exception as e:
                    raise
            raise last_err
        return wrapper
    return decorator




def init_db():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT DEFAULT 'Admin',
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            sources TEXT,
            feedback INTEGER DEFAULT 0, -- 1 for up, -1 for down, 0 for none
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT DEFAULT 'Admin',
            title TEXT NOT NULL,
            description TEXT,
            start_date TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            start_time TEXT DEFAULT '09:00',
            is_public INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            author TEXT DEFAULT 'Anonymous',
            category TEXT DEFAULT 'General',
            summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            link TEXT,
            attachments TEXT,
            is_pinned INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_views (
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(post_id, username),
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    # Migration: Add new columns if they don't exist
    try: cursor.execute("ALTER TABLE posts ADD COLUMN link TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE posts ADD COLUMN attachments TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE posts ADD COLUMN is_pinned INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    # Ensure no NULLs in is_pinned for old rows
    cursor.execute("UPDATE posts SET is_pinned = 0 WHERE is_pinned IS NULL")

    # NEW Migration for schedules
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN is_public INTEGER DEFAULT 0")
        print("✅ Database migrated: Added is_public column to schedules.")
    except sqlite3.OperationalError:
        pass
    
    cursor.execute("UPDATE schedules SET is_public = 0 WHERE is_public IS NULL")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            author TEXT DEFAULT 'Anonymous',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            post_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            PRIMARY KEY(post_id, user),
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            avatar_url TEXT,
            background_url TEXT,
            department TEXT DEFAULT 'General',
            position TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            attachments TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: Add feedback column if it doesn't exist for older databases
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN feedback INTEGER DEFAULT 0")
        print("✅ Database migrated: Added feedback column.")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN start_time TEXT DEFAULT '09:00'")
        print("✅ Database migrated: Added start_time column to schedules.")
    except sqlite3.OperationalError:
        pass

    # NEW: Add username column to messages and schedules if not exists
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN username TEXT DEFAULT 'Admin'")
    except sqlite3.OperationalError: pass
    
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN username TEXT DEFAULT 'Admin'")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN department TEXT DEFAULT 'General'")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN position TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN line_user_id TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN target_departments TEXT") # Comma separated depts
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN target_users TEXT") # Comma separated usernames
    except sqlite3.OperationalError: pass

    # Migrations for leave_requests to sync duplicate schemas
    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN line_user_id TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN leave_type TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN type TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN file_link TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN approved_by TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN approver_note TEXT")
    except sqlite3.OperationalError: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            text TEXT NOT NULL,
            attachments TEXT,
            is_read INTEGER DEFAULT 0,
            is_pinned INTEGER DEFAULT 0,
            reply_to_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try: cursor.execute("ALTER TABLE private_messages ADD COLUMN reply_to_id INTEGER")
    except sqlite3.OperationalError: pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            avatar_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_user_id TEXT,
            username TEXT,
            leave_type TEXT,
            start_date TEXT,
            end_date TEXT,
            reason TEXT,
            file_link TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_user_id TEXT,
            username TEXT,
            vendor TEXT,
            amount REAL,
            expense_date TEXT,
            file_link TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_members (
            room_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            last_read_id INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(room_id, username),
            FOREIGN KEY(room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            attachments TEXT,
            is_pinned INTEGER DEFAULT 0,
            reply_to_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE
        )
    """)
    try: cursor.execute("ALTER TABLE room_messages ADD COLUMN reply_to_id INTEGER")
    except sqlite3.OperationalError: pass
    # Migration: Add is_pinned to room_messages if not exists
    try:
        cursor.execute("ALTER TABLE room_messages ADD COLUMN is_pinned INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kb_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            avatar_url TEXT,
            visibility TEXT DEFAULT 'public', -- public, private, restricted
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: Add visibility to kb_categories if not exists
    try:
        cursor.execute("ALTER TABLE kb_categories ADD COLUMN visibility TEXT DEFAULT 'public'")
    except sqlite3.OperationalError: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_category_access (
            username TEXT,
            category_id INTEGER,
            PRIMARY KEY (username, category_id),
            FOREIGN KEY(category_id) REFERENCES kb_categories(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            system_prompt TEXT NOT NULL,
            scope_category_id INTEGER,
            avatar_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(scope_category_id) REFERENCES kb_categories(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            username TEXT PRIMARY KEY,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            can_view_kb INTEGER DEFAULT 0,
            can_edit_kb INTEGER DEFAULT 0,
            can_delete_kb INTEGER DEFAULT 0,
            custom_password TEXT,
            notes TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_edits (
            line_user_id TEXT PRIMARY KEY,
            sheet_name TEXT,
            row_index INTEGER,
            data_json TEXT,
            state TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Default settings
    cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('allow_user_edit', '0')")

    # Default Personas
    cursor.execute("SELECT COUNT(*) FROM ai_personas")
    if cursor.fetchone()[0] == 0:
        personas = [
            ("ผู้ช่วยมืออาชีพ (Professional)", "คุณเป็นเลขานุการผู้บริหารที่สุขุม รอบคอบ และเป็นทางการมาก ตอบคำถามด้วยสำนวนภาษาธุรกิจที่ไพเราะและชัดเจน", "เน้นความเป็นทางการ ข้อมูลแม่นยำ และภาษาสวยงาม", None, "https://cdn-icons-png.flaticon.com/512/1077/1077114.png", "System"),
            ("พี่ใจดี (Kind Assistant)", "คุณเป็นรุ่นพี่ในที่ทำงานที่ใจดี เข้าถึงง่าย และพร้อมช่วยเหลือน้องๆ เสมอ ตอบแบบเป็นกันเอง ใช้ภาษาที่เป็นมิตรและให้กำลังใจ", "เน้นความเป็นกันเอง สไตล์พี่สอนน้อง เข้าใจง่าย", None, "https://cdn-icons-png.flaticon.com/512/4140/4140048.png", "System"),
            ("สรุปสาระสำคัญ (Concise Specialist)", "คุณเป็นผู้เชี่ยวชาญด้านการสรุปข้อมูลที่เน้นความเร็วและเนื้อหาสำคัญเท่านั้น ตอบเป็นข้อๆ (Bullet points) สั้นที่สุดเท่าที่จะทำได้", "เน้นความรวดเร็ว สรุปเนื้อๆ ไม่เน้นน้ำ", None, "https://cdn-icons-png.flaticon.com/512/9131/9131546.png", "System")
        ]
        cursor.executemany("INSERT INTO ai_personas (name, system_prompt, description, scope_category_id, avatar_url, created_by) VALUES (?, ?, ?, ?, ?, ?)", personas)

    # Migrations for existing user_settings
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_view_kb INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_edit_kb INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_delete_kb INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN email TEXT")
    except sqlite3.OperationalError: pass

    # Migration: Add category_id to knowledge_base
    try:
        cursor.execute("ALTER TABLE knowledge_base ADD COLUMN category_id INTEGER")
    except sqlite3.OperationalError:
        pass

    # Migration: Add status to schedules for Kanban
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN status TEXT DEFAULT 'todo'")
        print("✅ Database migrated: Added status column to schedules (Kanban).")
    except sqlite3.OperationalError:
        pass

    # Migration: Add is_archived to schedules
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN is_archived INTEGER DEFAULT 0")
        print("✅ Database migrated: Added is_archived column.")
    except sqlite3.OperationalError:
        pass

    # Migration: Add reaction column to likes table
    try:
        cursor.execute("ALTER TABLE likes ADD COLUMN reaction TEXT DEFAULT 'like'")
        print("✅ Database migrated: Added reaction column to likes.")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            username TEXT NOT NULL,
            subscription_json TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(username, subscription_json)
        )
    """)
    
    # --- Notifications Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT,
            is_read INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # --- Interactive Polls ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_votes (
            poll_id INTEGER NOT NULL,
            option_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            PRIMARY KEY(poll_id, username),
            FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE,
            FOREIGN KEY(option_id) REFERENCES poll_options(id) ON DELETE CASCADE
        )
    """)

    # Migration: Add edited_at to room_messages and private_messages for message edit feature
    try:
        cursor.execute("ALTER TABLE room_messages ADD COLUMN edited_at DATETIME")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE private_messages ADD COLUMN edited_at DATETIME")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE private_messages ADD COLUMN is_pinned INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass

    # Search History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            username TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- User Status Tracking (Online/Offline) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_status (
            username TEXT PRIMARY KEY,
            is_online INTEGER DEFAULT 0,
            current_room TEXT,
            typing_in_room TEXT,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Message Read Receipts ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_read_receipts (
            message_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            room_id INTEGER,
            read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(message_id, username),
            FOREIGN KEY(message_id) REFERENCES room_messages(id) ON DELETE CASCADE
        )
    """)

    # --- Private Message Read Status ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS private_message_read_status (
            message_id INTEGER NOT NULL,
            is_read INTEGER DEFAULT 0,
            read_at DATETIME,
            PRIMARY KEY(message_id),
            FOREIGN KEY(message_id) REFERENCES private_messages(id) ON DELETE CASCADE
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wiki_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            category_id INTEGER,
            organization_id INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES kb_categories(id) ON DELETE SET NULL
        )
    """)
    
    # --- Performance Optimization: Indexes ---
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_username ON messages(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_room_messages_room_id ON room_messages(room_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_private_messages_participants ON private_messages(sender, recipient)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(start_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_status_online ON user_status(is_online)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_read_receipts ON message_read_receipts(message_id, username)")
    
    # --- Leave Requests Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            approved_by TEXT,
            approver_note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leave_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            comment TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(leave_id) REFERENCES leave_requests(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_text TEXT NOT NULL,
            user TEXT DEFAULT 'System',
            time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(time)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lunch_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT, -- เช่น ตามสั่ง, ส้มตำ, ญี่ปุ่น
            location TEXT,
            added_by TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add initial data if empty
    cursor.execute("SELECT COUNT(*) FROM lunch_places")
    if cursor.fetchone()[0] == 0:
        places = [
            ("ข้าวมันไก่หน้าปากซอย", "ไก่ตอน", "หน้าปากซอย"),
            ("ส้มตำแซ่บเวอร์", "อีสาน", "ข้างออฟฟิศ"),
            ("ราเมนเด็ด", "ญี่ปุ่น", "ในห้าง"),
            ("ตามสั่งป้าดาว", "อาหารตามสั่ง", "ตึกแถวตรงข้าม"),
            ("ผัดไทยโบราณ", "เส้น", "ทางเดินรถเมล์")
        ]
        cursor.executemany("INSERT INTO lunch_places (name, type, location) VALUES (?,?,?)", places)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drive_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT,
            amount REAL,
            doc_date TEXT,
            summary TEXT,
            file_link TEXT,
            user_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_created_at ON drive_logs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_filename ON drive_logs(filename)")

    # --- Per-User Google OAuth2 Token Storage (personal / no-org users) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_google_tokens (
            username TEXT PRIMARY KEY,
            google_email TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TEXT,
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Multi-Tenancy: Organizations ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT UNIQUE,
            plan TEXT DEFAULT 'free',
            max_users INTEGER DEFAULT 10,
            trial_ends_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Per-Org Google OAuth2 Token Storage (1 Google account shared by entire org) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_google_tokens (
            org_id INTEGER PRIMARY KEY,
            google_email TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TEXT,
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
            connected_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)

    # --- B2B LINE Group Mapping Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_group_mappings (
            group_id TEXT PRIMARY KEY,
            owner_username TEXT NOT NULL,
            group_name TEXT,
            default_folder_id TEXT,
            default_folder_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner_username) REFERENCES user_profiles(username) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_members (
            organization_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            invited_by TEXT,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (organization_id, username),
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    # Add organization_id columns to key tables (migrations)
    for tbl in ("messages", "schedules", "posts", "chat_rooms", "wiki_pages"):
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN organization_id INTEGER DEFAULT 1")
        except Exception:
            pass
    # Billing: usage tracking per org per month
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_tracking (
            org_id      INTEGER NOT NULL,
            year_month  TEXT    NOT NULL,
            expense_count    INTEGER DEFAULT 0,
            ai_query_count   INTEGER DEFAULT 0,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (org_id, year_month)
        )
    """)
    # Migration: plan_expires_at, Stripe fields on organizations
    for col_sql in [
        "ALTER TABLE organizations ADD COLUMN plan_expires_at DATETIME",
        "ALTER TABLE organizations ADD COLUMN stripe_customer_id TEXT",
        "ALTER TABLE organizations ADD COLUMN stripe_subscription_id TEXT",
        "ALTER TABLE organizations ADD COLUMN whitelist_enabled INTEGER DEFAULT 0",
    ]:
        try:
            cursor.execute(col_sql)
        except Exception:
            pass

    # --- Whitelist Emails ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_allowed_emails (
            organization_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            added_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (organization_id, email),
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)

    # Migration: add org_id to line_group_mappings for multi-tenant support
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN org_id INTEGER")
    except Exception:
        pass

    # Seed default organization
    cursor.execute("INSERT OR IGNORE INTO organizations (id, name, slug, plan) VALUES (1, 'Default Organization', 'default', 'free')")
    # Add all existing users to default org
    cursor.execute("SELECT username FROM user_profiles")
    for (uname,) in cursor.fetchall():
        cursor.execute("""
            INSERT OR IGNORE INTO organization_members (organization_id, username, role)
            VALUES (1, ?, CASE WHEN lower(?) = 'admin' THEN 'admin' ELSE 'member' END)
        """, (uname, uname))
    # Also seed from user_settings
    cursor.execute("SELECT username FROM user_settings")
    for (uname,) in cursor.fetchall():
        cursor.execute("""
            INSERT OR IGNORE INTO organization_members (organization_id, username, role)
            VALUES (1, ?, CASE WHEN lower(?) = 'admin' THEN 'admin' ELSE 'member' END)
        """, (uname, uname))

    conn.commit()
    conn.close()


def get_user_orgs(username: str) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.name, o.slug, o.plan, om.role
        FROM organizations o
        JOIN organization_members om ON o.id = om.organization_id
        WHERE om.username = ?
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
    """Multi-tenant: map LINE user_id → org_id via linked username"""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM user_profiles WHERE line_user_id = ?", (line_user_id,))
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
        "SELECT organization_id FROM organization_members WHERE username = ? ORDER BY organization_id LIMIT 1",
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


def get_line_groups_for_org(org_id: int) -> list:
    """List all LINE groups registered to an org."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT group_id, group_name, owner_username, created_at FROM line_group_mappings WHERE org_id = ? ORDER BY created_at DESC",
        (org_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


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
        VALUES (?, 'user', 1)
    """, (owner_username,))
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


def get_org_members(org_id: int) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT om.username, om.role, om.joined_at,
               COALESCE(up.display_name, om.username) as display_name,
               up.avatar_url, up.department, up.position
        FROM organization_members om
        LEFT JOIN user_profiles up ON om.username = up.username
        WHERE om.organization_id = ?
        ORDER BY CASE om.role WHEN 'admin' THEN 0 ELSE 1 END, om.joined_at
    """, (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"username": r[0], "role": r[1], "joined_at": r[2],
             "display_name": r[3], "avatar_url": r[4],
             "department": r[5], "position": r[6]} for r in rows]


def is_org_admin(org_id: int, username: str) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM organization_members WHERE organization_id = ? AND username = ?", (org_id, username))
    row = cursor.fetchone()
    conn.close()
    return row is not None and row[0] == 'admin'


def remove_org_member(org_id: int, username: str) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM organization_members WHERE organization_id = ? AND username = ?", (org_id, username))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# --- Whitelist Feature ---

def get_whitelist_emails(org_id: int) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT email, added_by, created_at FROM organization_allowed_emails WHERE organization_id = ? ORDER BY created_at DESC", (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"email": r[0], "added_by": r[1], "created_at": r[2]} for r in rows]

def add_whitelist_email(org_id: int, email: str, added_by: str) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    try:
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

def is_email_allowed(org_id: int, email: str) -> bool:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM organization_allowed_emails WHERE organization_id = ? AND email = ?", (org_id, email))
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


def add_drive_log(filename, category=None, amount=None, doc_date=None, summary=None, file_link=None, user_id=None):
    """Log a file upload/analysis event to the database."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO drive_logs (filename, category, amount, doc_date, summary, file_link, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (filename, category, amount, doc_date, summary, file_link, user_id))
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id
    except Exception as e:
        print(f"❌ Error adding drive log: {e}")
        return None

def get_drive_logs(limit=50, offset=0, user_id=None):
    """Retrieve recent drive logs."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        query = "SELECT * FROM drive_logs"
        params = []
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Error fetching drive logs: {e}")
        return []

def search_drive_logs(search_query, limit=20):
    """Search drive logs by filename or summary."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        query = """
            SELECT * FROM drive_logs 
            WHERE filename LIKE ? OR summary LIKE ? OR category LIKE ?
            ORDER BY created_at DESC LIMIT ?
        """
        like_query = f"%{search_query}%"
        cursor.execute(query, (like_query, like_query, like_query, limit))
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Error searching drive logs: {e}")
        return []

def get_drive_stats():
    """Get statistics for the dashboard."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # Total files
        cursor.execute("SELECT COUNT(*) FROM drive_logs")
        total_files = cursor.fetchone()[0]
        
        # Total amount (if available)
        cursor.execute("SELECT SUM(amount) FROM drive_logs WHERE amount IS NOT NULL")
        total_amount = cursor.fetchone()[0] or 0
        
        # Files by category
        cursor.execute("SELECT category, COUNT(*) as count FROM drive_logs GROUP BY category")
        categories = dict(cursor.fetchall())
        
        # Recent activity (last 24h)
        cursor.execute("SELECT COUNT(*) FROM drive_logs WHERE created_at > datetime('now', '-1 day')")
        recent_count = cursor.fetchone()[0]
        
        conn.close()
        return {
            "total_files": total_files,
            "total_amount": total_amount,
            "categories": categories,
            "recent_count": recent_count
        }
    except Exception as e:
        print(f"❌ Error fetching drive stats: {e}")
        return {}



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


def save_message(role, text, sources=None, username="Admin", org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    sources_json = json.dumps(sources) if sources else None
    cursor.execute("INSERT INTO messages (role, text, sources, username, organization_id) VALUES (?, ?, ?, ?, ?)", (role, text, sources_json, username, org_id))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def get_history(username="Admin", limit=50, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, text, sources FROM messages WHERE username = ? AND organization_id = ? ORDER BY timestamp ASC LIMIT ?", (username, org_id, limit))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        history.append({
            "id": r[0],
            "role": r[1],
            "text": r[2],
            "sources": json.loads(r[3]) if r[3] else []
        })
    return history

def clear_history(username="Admin", org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE username = ? AND organization_id = ?", (username, org_id))
    conn.commit()
    conn.close()

def delete_message(msg_id, username="Admin"):
    """Delete a specific message by its ID, verifying ownership."""
    conn = _get_conn()
    cursor = conn.cursor()
    if username == "Admin":
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
    else:
        cursor.execute("DELETE FROM messages WHERE id = ? AND username = ?", (msg_id, username))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ─── Admin Chat Management ─────────────────────────────

def admin_get_all_ai_messages(limit=200):
    conn = _get_conn()
    cursor = conn.cursor()
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

def delete_private_message(msg_id, username=None, is_admin=False):
    """Delete a private message, verifying ownership or admin status."""
    conn = _get_conn()
    cursor = conn.cursor()
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

def get_stats(username="Admin"):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user' AND username = ?", (username,))
    total_queries = cursor.fetchone()[0]
    
    cursor.execute("SELECT feedback, COUNT(*) FROM messages WHERE role = 'bot' AND username = ? GROUP BY feedback", (username,))
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

def log_event(event_text, user="System"):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (event_text, user) VALUES (?, ?)", (event_text, user))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log event: {e}")

def get_events(limit=20):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT datetime(time, 'localtime'), event_text, user FROM events ORDER BY time DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"time": r[0], "event": r[1], "user": r[2]} for r in rows]

def add_schedule(username, title, start_date, description="", category="General", start_time="09:00", is_public=0, status="todo", target_departments=None, target_users=None, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO schedules (username, title, start_date, start_time, description, category, is_public, status, target_departments, target_users, organization_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, title, start_date, start_time, description, category, is_public, status, target_departments, target_users, org_id))
    conn.commit()
    conn.close()

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
    if category and category != "All":
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
    VALID_REACTIONS = {'like', 'love', 'haha', 'wow', 'sad', 'angry'}
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

# --- User Profile ---
def get_user_profile(username):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT username, display_name, avatar_url, background_url, department FROM user_profiles WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "display_name": row[1], "avatar_url": row[2], "background_url": row[3], "department": row[4] or "General"}
    return {"username": username, "display_name": username.capitalize(), "avatar_url": None, "background_url": None, "department": "General"}

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

# --- Unified & Private Chat ---
@db_transaction_retry()
def save_dm(sender, recipient, text, attachments=None, reply_to_id=None):
    conn = _get_conn()
    cursor = conn.cursor()
    attach_json = json.dumps(attachments) if attachments else None
    cursor.execute("""
        INSERT INTO private_messages (sender, recipient, text, attachments, reply_to_id) 
        VALUES (?, ?, ?, ?, ?)
    """, (sender, recipient, text, attach_json, reply_to_id))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def get_dm_history(user1, user2, limit=50):
    conn = _get_conn()
    cursor = conn.cursor()
    # Updated query to include reply_to_id and fetch replied message info
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

def get_line_id_by_username(username):
    """Get the linked LINE ID for a specific OrgChat user."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT line_user_id FROM user_profiles WHERE username = ? COLLATE NOCASE", (username,))
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
        cursor.execute("SELECT username FROM user_profiles WHERE line_user_id = ?", (line_user_id,))
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
    cursor = conn.cursor()
    attach_json = json.dumps(attachments) if attachments else None
    cursor.execute("""
        INSERT INTO room_messages (room_id, username, text, attachments, reply_to_id) 
        VALUES (?, ?, ?, ?, ?)
    """, (room_id, username, text, attach_json, reply_to_id))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

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

def toggle_private_message_pin(msg_id):
    """Toggles the pinned status of a private message."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT is_pinned FROM private_messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if row:
        new_val = 1 if not row[0] else 0
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

def get_rooms_for_user(username, org_id=1):
    conn = _get_conn()
    cursor = conn.cursor()

    # Get rooms with their last message
    cursor.execute("""
        SELECT r.id, r.name, r.avatar_url, r.owner,
               m.text as last_msg, m.timestamp as last_time, m.username as last_sender
        FROM chat_rooms r
        JOIN room_members rm ON r.id = rm.room_id
        LEFT JOIN (
            SELECT room_id, text, timestamp, username,
                   ROW_NUMBER() OVER (PARTITION BY room_id ORDER BY id DESC) as rn
            FROM room_messages
        ) m ON r.id = m.room_id AND m.rn = 1
        WHERE rm.username = ? COLLATE NOCASE
          AND (r.organization_id = ? OR r.organization_id IS NULL)
        ORDER BY COALESCE(m.timestamp, '1970-01-01') DESC
    """, (username, org_id))
    
    rooms = []
    for r in cursor.fetchall():
        rooms.append({
            "id": r[0], "name": r[1], "avatar_url": r[2], "owner": r[3], "type": "room",
            "last_msg": r[4], "last_time": r[5], "last_sender": r[6]
        })
    
    # Recent DM contacts with their last message
    cursor.execute("""
        SELECT contact, text as last_msg, timestamp as last_time, sender as last_sender
        FROM (
            SELECT CASE WHEN sender = ? COLLATE NOCASE THEN recipient ELSE sender END as contact,
                   text, timestamp, sender,
                   ROW_NUMBER() OVER (PARTITION BY CASE WHEN sender = ? COLLATE NOCASE THEN recipient ELSE sender END ORDER BY id DESC) as rn
            FROM private_messages
            WHERE sender = ? COLLATE NOCASE OR recipient = ? COLLATE NOCASE
        )
        WHERE rn = 1
        ORDER BY timestamp DESC
    """, (username, username, username, username))
    
    contacts = []
    for c in cursor.fetchall():
        contact_name = c[0]
        p = get_user_profile(contact_name)
        contacts.append({
            "id": contact_name, "name": p["display_name"], 
            "avatar_url": p["avatar_url"], "type": "dm",
            "last_msg": c[1], "last_time": c[2], "last_sender": c[3]
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

def get_user_setting(username):
    """Get user_settings for a user, returns defaults if not set. Case-insensitive."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role, is_active, custom_password, notes, can_view_kb, can_edit_kb, can_delete_kb, email FROM user_settings WHERE username = ? COLLATE NOCASE", (username,))
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
            "email": row[8] or ""
        }
    
    # Defaults
    if username.lower() == "admin":
        return {"username_original": "Admin", "role": "admin", "is_active": 1, "custom_password": None, "notes": "Default Admin", "can_view_kb": True, "can_edit_kb": True, "can_delete_kb": True}
    return {"username_original": username, "role": "user", "is_active": 1, "custom_password": None, "notes": "", "can_view_kb": False, "can_edit_kb": False, "can_delete_kb": False}

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
               om.role as org_role
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
        "org_role": r[10]
    } for r in rows]

# --- Global App Settings ---
def get_app_setting(key, default=None):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_app_setting(key, value):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (key, value))
    conn.commit()
    conn.close()

def get_all_app_settings():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_settings")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def admin_update_user(username, display_name=None, role=None, is_active=None, notes=None, can_view_kb=None, can_edit_kb=None, can_delete_kb=None, department=None):
    """Admin updates a user's profile and settings."""
    conn = _get_conn()
    cursor = conn.cursor()

    # Prevent admin from disabling their own account or changing role
    if username == "Admin":
        if is_active is not None and not is_active: # If trying to set is_active to False
            # This function doesn't return jsonify, it should raise an exception or return a status
            # For a database function, returning a boolean or raising an error is more appropriate.
            # For now, we'll just prevent the action silently or log it.
            print(f"Attempted to disable Admin account by {username}. Action prevented.")
            is_active = True # Force active
        if role is not None and role != "admin": # If trying to change role from admin
            print(f"Attempted to change Admin role by {username}. Action prevented.")
            role = "admin" # Force admin role

    # Update profile
    if display_name is not None or department is not None:
        if display_name is not None and department is not None:
            cursor.execute("""
                INSERT INTO user_profiles (username, display_name, department) VALUES (?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET display_name = excluded.display_name, department = excluded.department
            """, (username, display_name, department))
        elif display_name is not None:
            cursor.execute("""
                INSERT INTO user_profiles (username, display_name) VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET display_name = excluded.display_name
            """, (username, display_name))
        else: # department is not None
            cursor.execute("""
                INSERT INTO user_profiles (username, department) VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET department = excluded.department
            """, (username, department))
    # Upsert settings
    if role is not None or is_active is not None or notes is not None or can_view_kb is not None or can_edit_kb is not None or can_delete_kb is not None:
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
        if notes is not None:
            cursor.execute("UPDATE user_settings SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?", (notes, username))
    conn.commit()
    conn.close()

def admin_reset_user_password(username, new_password):
    """Admin sets a custom password override for a user (hashed with bcrypt)."""
    conn = _get_conn()
    cursor = conn.cursor()
    hashed = hash_password(new_password)
    cursor.execute("INSERT OR IGNORE INTO user_settings (username) VALUES (?)", (username,))
    cursor.execute("UPDATE user_settings SET custom_password = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?", (hashed, username))
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
        
        # 2. Create Settings & Password (hashed)
        cursor.execute("""
            INSERT INTO user_settings (username, role, custom_password, can_view_kb, can_edit_kb, can_delete_kb, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
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
            "posts", "comments", "private_messages"
        ]
        
        for table in tables:
            # Handle special column names if necessary
            col = "username"
            if table == "private_messages":
                cursor.execute("DELETE FROM private_messages WHERE sender = ? OR recipient = ?", (username, username))
                continue
            if table == "likes":
                col = "user"
            if table == "comments":
                col = "author"
            if table == "posts":
                col = "author"
            
            cursor.execute(f"DELETE FROM {table} WHERE {col} = ?", (username,))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user {username}: {e}")
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
    cur.execute("SELECT COUNT(*) AS cnt FROM messages WHERE role='user'")
    total_ai_queries = (cur.fetchone() or {"cnt": 0})["cnt"]
    cur.execute("SELECT SUM(ai_query_count) AS cnt FROM usage_tracking WHERE year_month=?", (ym,))
    ai_queries_this_month = (cur.fetchone() or {"cnt": 0})["cnt"] or 0
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


def superadmin_delete_org(org_id: int) -> bool:
    """Super admin: delete an org and remove all its members from it."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM organization_members WHERE organization_id=?", (org_id,))
        conn.execute("DELETE FROM usage_tracking WHERE org_id=?", (org_id,))
        conn.execute("DELETE FROM organizations WHERE id=?", (org_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[superadmin_delete_org] error: {e}")
        return False
    finally:
        conn.close()


def add_category(name, description=None, created_by="Admin", visibility="public"):
    """Adds a new KB category with visibility settings."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO kb_categories (name, description, created_by, visibility) VALUES (?, ?, ?, ?)", 
                       (name, description, created_by, visibility))
        cat_id = cursor.lastrowid
        conn.commit()
        return cat_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_categories(username=None):
    """
    Returns KB categories filtered by user access.
    Logic:
    - Admin sees all.
    - Owner sees all their categories.
    - Public categories are visible to all.
    - Restricted categories are visible to authorized users.
    - Private categories are only visible to the owner.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    
    if username == "Admin":
        cursor.execute("SELECT id, name, description, created_by, visibility, created_at FROM kb_categories ORDER BY name ASC")
    elif username:
        cursor.execute("""
            SELECT DISTINCT c.id, c.name, c.description, c.created_by, c.visibility, c.created_at
            FROM kb_categories c
            LEFT JOIN user_category_access uca ON c.id = uca.category_id
            WHERE c.visibility = 'public'
               OR c.created_by = ?
               OR (c.visibility = 'restricted' AND uca.username = ?)
            ORDER BY c.name ASC
        """, (username, username))
    else:
        cursor.execute("SELECT id, name, description, created_by, visibility, created_at FROM kb_categories WHERE visibility = 'public' ORDER BY name ASC")
        
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2], "created_by": r[3], "visibility": r[4], "created_at": r[5]} for r in rows]

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

def create_leave_request(username, leave_type, start_date, end_date, reason):
    """Submit a new leave request."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leave_requests (username, type, start_date, end_date, reason) VALUES (?, ?, ?, ?, ?)",
            (username, leave_type, start_date, end_date, reason)
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

def get_all_leaves(limit=200):
    """Fetch all leave requests (for admins)."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leave_requests ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] get_all_leaves: {e}")
        return []

def update_leave_status(leave_id, status, approver, note=""):
    """Approve or reject a leave request."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE leave_requests SET status = ?, approved_by = ?, approver_note = ? WHERE id = ?",
            (status, approver, note, leave_id)
        )
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except Exception as e:
        print(f"[ERROR] update_leave_status: {e}")
        return False

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
    """Updates persona fields."""
    if not kwargs: return False
    conn = _get_conn()
    cursor = conn.cursor()
    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [persona_id]
    try:
        cursor.execute(f"UPDATE ai_personas SET {fields} WHERE id = ?", values)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating persona: {e}")
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
def get_admin_dashboard_stats():
    """Returns analytics for the admin dashboard."""
    conn = _get_conn()
    cursor = conn.cursor()
    
    # User growth (total users)
    cursor.execute("SELECT COUNT(*) FROM user_profiles")
    total_users = cursor.fetchone()[0]
    
    # Message stats (Queries to AI)
    cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'")
    total_ai_queries = cursor.fetchone()[0]
    
    # Top AI Personas used (simulated através de mensagens se persona_id estava em mensagens, mas não está. 
    # Por enquanto, vamos contar posts totais por usuário)
    cursor.execute("SELECT author, COUNT(*) as c FROM posts GROUP BY author ORDER BY c DESC LIMIT 5")
    top_posters = [{"user": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Poll participation
    cursor.execute("SELECT COUNT(*) FROM poll_votes")
    total_votes = cursor.fetchone()[0]
    
    # File count in knowledge_base (assumindo nome da tabela como 'knowledge_base')
    total_files = 0
    try:
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        total_files = cursor.fetchone()[0]
    except:
        pass
        
    conn.close()
    return {
        "total_users": total_users,
        "total_ai_queries": total_ai_queries,
        "top_posters": top_posters,
        "total_votes": total_votes,
        "total_files": total_files
    }

def get_analytics_data():
    """Returns rich analytics: daily activity (last 7 days), top posters, message counts."""
    conn = _get_conn()
    cursor = conn.cursor()
    
    # Daily AI queries last 7 days
    cursor.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM messages
        WHERE role = 'user'
          AND timestamp >= DATE('now', '-7 days')
        GROUP BY day
        ORDER BY day ASC
    """)
    daily_queries = [{"day": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Daily posts last 7 days
    cursor.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM posts
        WHERE timestamp >= DATE('now', '-7 days')
        GROUP BY day
        ORDER BY day ASC
    """)
    daily_posts = [{"day": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Top 5 posters
    cursor.execute("""
        SELECT author, COUNT(*) as c FROM posts
        GROUP BY author ORDER BY c DESC LIMIT 5
    """)
    top_posters = [{"user": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Daily DMs + room messages (combined chat activity)
    cursor.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM room_messages
        WHERE timestamp >= DATE('now', '-7 days')
        GROUP BY day ORDER BY day ASC
    """)
    daily_chat = [{"day": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Total counts
    cursor.execute("SELECT COUNT(*) FROM messages WHERE role='user'")
    total_queries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]
    
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

def get_all_personas_v2():
    """Returns all personas including their scope category names."""
    conn = _get_conn()
    cursor = conn.cursor()
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


def edit_private_message(msg_id, new_text, username, is_admin_user=False):
    """Edit a DM message. Returns True on success."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sender FROM private_messages WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        if not row:
            return False
        if not is_admin_user and row[0].lower() != username.lower():
            return False
        cursor.execute(
            "UPDATE private_messages SET text = ?, edited_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_text, msg_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ─── Global Search ─────────────────────────────
def global_search(query: str, username: str, limit: int = 30):
    """Search across posts, schedules, and DMs for a given user."""
    conn = _get_conn()
    cursor = conn.cursor()
    results = []
    q = f"%{query}%"

    # --- Posts ---
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

    # --- Schedules ---
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

    # --- Room Messages ---
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

    # --- DMs (only own) ---
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
    # Sort by timestamp descending
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

def kanban_init_db():
    """Ensure kanban tables exist (idempotent)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    # Seed default columns if empty
    cursor.execute("SELECT COUNT(*) FROM kanban_columns")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("To Do", 0, "#6366f1", "System"),
            ("In Progress", 1, "#f59e0b", "System"),
            ("Done", 2, "#10b981", "System"),
        ]
        cursor.executemany(
            "INSERT INTO kanban_columns (title, position, color, created_by) VALUES (?, ?, ?, ?)",
            defaults
        )
    
    # Migrations: Add updated_at and is_done if not exists
    try: cursor.execute("ALTER TABLE kanban_cards ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE kanban_cards ADD COLUMN is_done INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    conn.commit()
    conn.close()

def kanban_get_board():
    """Return all columns with their cards, ordered by position."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kanban_columns ORDER BY position ASC, id ASC")
    columns = [dict(row) for row in cursor.fetchall()]
    for col in columns:
        cursor.execute(
            "SELECT * FROM kanban_cards WHERE column_id = ? ORDER BY position ASC, id ASC",
            (col["id"],)
        )
        col["cards"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return columns

def kanban_add_column(title, color="#6366f1", created_by="System"):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(position),0)+1 FROM kanban_columns")
    pos = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO kanban_columns (title, position, color, created_by) VALUES (?, ?, ?, ?)",
        (title, pos, color, created_by)
    )
    col_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return col_id

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

def kanban_reorder_columns(order_list):
    """order_list: list of {id, position}"""
    conn = _get_conn()
    cursor = conn.cursor()
    for item in order_list:
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
    conn.close()
    return results


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
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

# --- New Features: Leave and Expense ---

def add_leave_request(line_user_id, username, leave_type, start_date, end_date, reason):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leave_requests (line_user_id, username, leave_type, start_date, end_date, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (line_user_id, username, leave_type, start_date, end_date, reason))
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

def add_expense_claim(line_user_id, username, vendor, amount, expense_date, file_link):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expense_claims (line_user_id, username, vendor, amount, expense_date, file_link)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (line_user_id, username, vendor, amount, expense_date, file_link))
    claim_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return claim_id

def get_line_config():
    """Returns LINE integration configuration from app_settings."""
    from database import get_app_setting
    return {
        "channel_access_token": get_app_setting("LINE_CHANNEL_ACCESS_TOKEN", ""),
        "channel_secret": get_app_setting("LINE_CHANNEL_SECRET", ""),
        "webhook_url": get_app_setting("LINE_WEBHOOK_URL", "")
    }

def search_drive_logs(query, limit=5):
    """Search for logs related to Google Drive activities."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    q = f"%{query}%"
    cursor.execute("SELECT * FROM drive_logs WHERE filename LIKE ? OR summary LIKE ? ORDER BY created_at DESC LIMIT ?", (q, q, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


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
    """Remove an org's shared Google OAuth2 tokens (disconnect)."""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM org_google_tokens WHERE org_id = ?", (org_id,))
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


# ─── Password Reset ───────────────────────────────────────────────────────────

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
    """Returns username if token is valid and unused, else None."""
    _ensure_reset_table()
    import datetime
    conn = _get_conn()
    row = conn.execute(
        "SELECT username, expires_at, used FROM password_reset_tokens WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    if not row or row[2]:
        return None
    try:
        if datetime.datetime.fromisoformat(row[1]) < datetime.datetime.utcnow():
            return None
    except Exception:
        return None
    return row[0]


def consume_reset_token(token: str, new_password: str) -> bool:
    """Validate token, update password, mark token used. Returns True on success."""
    username = validate_reset_token(token)
    if not username:
        return False
    new_hash = hash_password(new_password)
    conn = _get_conn()
    # Reject if user was deactivated after the token was issued
    active = conn.execute(
        "SELECT 1 FROM user_settings WHERE username = ? AND is_active = 1", (username,)
    ).fetchone()
    if not active:
        conn.close()
        return False
    conn.execute(
        "UPDATE user_settings SET custom_password = ? WHERE username = ?", (new_hash, username)
    )
    conn.execute(
        "UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,)
    )
    conn.commit()
    conn.close()
    return True


def get_line_user_id_for_username(username: str) -> str | None:
    """Return LINE user ID linked to this username, or None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT line_user_id FROM user_profiles WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row[0] if row and row[0] else None
