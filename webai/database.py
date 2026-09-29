import sys, io
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
if hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8')
    except Exception: pass

import sqlite3
import json
import os
from pathlib import Path
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    import sys
    print("❌ FATAL: bcrypt not installed — cannot start safely. Run: pip install bcrypt", file=sys.stderr)
    sys.exit(1)

DB_PATH = Path(os.environ.get("DB_PATH", "chat_history.db"))
if not DB_PATH.is_absolute():
    DB_PATH = Path(__file__).parent.absolute() / DB_PATH



def hash_password(password: str) -> str:
    """Hash a password with bcrypt. Falls back to plaintext if bcrypt unavailable."""
    if not password:
        return ""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return password


def check_password(password: str, stored: str) -> bool:
    """Verify a password against stored hash. Plaintext fallback is disabled for security."""
    if not password or not stored:
        return False
    if BCRYPT_AVAILABLE and (stored.startswith("$2b$") or stored.startswith("$2a$")):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    # For security, we only allow bcrypt hashes for database accounts.
    return False

import os
import re
import random
import time
from functools import wraps

import os
import re
import random
import time
import threading
import logging
from functools import wraps

logger = logging.getLogger("OrgChatAI.Database")

from dotenv import load_dotenv
load_dotenv(encoding="utf-8")

# Determine DB_TYPE dynamically based on environment
_db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
DB_TYPE = "postgres" if (_db_url or os.environ.get("DB_TYPE") == "postgres") else "sqlite"

_pg_pool = None
_pg_pool_initialized = False
_pg_pool_lock = threading.Lock()

def _get_pg_pool():
    global _pg_pool, _pg_pool_initialized
    if not _pg_pool_initialized:
        with _pg_pool_lock:
            if not _pg_pool_initialized:
                db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
                if db_url:
                    try:
                        import psycopg2.pool
                        # Initialize ThreadedConnectionPool: 1 min connection, 20 max connections
                        _pg_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, dsn=db_url)
                        print("✅ Postgres connection pool initialized successfully")
                    except Exception as e:
                        print(f"❌ Failed to initialize Postgres connection pool: {e}")
                        _pg_pool = None
                _pg_pool_initialized = True
    return _pg_pool

class PostgresRow:
    """Emulates sqlite3.Row for PostgreSQL query results."""
    def __init__(self, description, values):
        self._keys = [d[0] for d in description] if description else []
        self._values = tuple(values) if values is not None else ()
        self._mapping = {k: v for k, v in zip(self._keys, self._values)}

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._values[item]
        if isinstance(item, str):
            if item in self._mapping:
                return self._mapping[item]
            # Case-insensitive fallback
            item_lower = item.lower()
            for k, v in self._mapping.items():
                if k.lower() == item_lower:
                    return v
            raise KeyError(item)
        raise TypeError(f"Row indices must be integers or strings, not {type(item).__name__}")

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def keys(self):
        return list(self._keys)

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError):
            return default

    def __contains__(self, key):
        if isinstance(key, str):
            return key in self._mapping or any(k.lower() == key.lower() for k in self._mapping)
        return False

    def __repr__(self):
        return f"<PostgresRow {self._mapping}>"


class DynamicCursorWrapper:
    def __init__(self, cursor, is_postgres=False, connection_wrapper=None):
        self._cursor = cursor
        self._is_postgres = is_postgres
        import weakref
        self._connection_wrapper_ref = weakref.ref(connection_wrapper) if connection_wrapper else None
        self._lastrowid = None

    @property
    def _connection_wrapper(self):
        return self._connection_wrapper_ref() if self._connection_wrapper_ref else None

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
        self._closed = False

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
        if self._closed:
            return
        self._closed = True
        if self._is_postgres and self._pool:
            try:
                self._pool.putconn(self._conn)
            except Exception:
                pass
        else:
            try:
                return self._conn.close()
            except Exception:
                pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
        finally:
            self.close()


def _get_conn(timeout: int = 30):
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if db_url:
        pool = _get_pg_pool()
        if pool:
            try:
                conn = pool.getconn()
                # Set autocommit to False for transaction support (default in sqlite)
                conn.autocommit = False
                return DynamicConnectionWrapper(conn, is_postgres=True, pool=pool)
            except Exception as e:
                import logging
                logger = logging.getLogger("database")
                logger.warning(f"⚠️ Failed to get connection from Postgres pool: {e}. Falling back to SQLite...")
                
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
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
                    logger.warning(f"⚠️ [DB Retry] Database error (SQLite) in {func.__name__} (attempt {attempt+1}/{max_retries}). Retrying in {backoff:.3f}s... Error: {e}")
                    time.sleep(backoff)
                    continue
                except Exception as e:
                    mod_name = type(e).__module__
                    err_name = type(e).__name__
                    if mod_name.startswith('psycopg2') and err_name in ['OperationalError', 'TransactionRollbackError', 'InterfaceError']:
                        last_err = e
                        backoff = (initial_backoff * (2 ** attempt)) + random.uniform(0, 0.05)
                        import logging
                        logger = logging.getLogger("database_retry")
                        logger.warning(f"⚠️ [DB Retry] Database error (Postgres {err_name}) in {func.__name__} (attempt {attempt+1}/{max_retries}). Retrying in {backoff:.3f}s... Error: {e}")
                        time.sleep(backoff)
                        continue
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
        CREATE TABLE IF NOT EXISTS line_broadcast_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            org_id INTEGER DEFAULT 1,
            text TEXT NOT NULL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            username TEXT DEFAULT 'System',
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            hash_signature TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN org_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN hash_signature TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_integrity_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            sha256_hash TEXT NOT NULL,
            file_size INTEGER,
            category TEXT DEFAULT 'uploads',
            last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL DEFAULT 1,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            created_by TEXT DEFAULT 'Admin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE line_broadcast_history ADD COLUMN org_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE line_broadcast_history ADD COLUMN scheduled_at TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            org_id INTEGER DEFAULT 1,
            check_date TEXT NOT NULL,
            check_time TEXT NOT NULL,
            check_type TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            address TEXT,
            distance_meters REAL,
            status TEXT DEFAULT 'on_time',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN reminder_sent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass


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
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
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
            organization_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try: cursor.execute("ALTER TABLE private_messages ADD COLUMN reply_to_id INTEGER")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE private_messages ADD COLUMN organization_id INTEGER")
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
        CREATE TABLE IF NOT EXISTS user_leave_quotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            org_id INTEGER NOT NULL DEFAULT 1,
            year INTEGER NOT NULL,
            sick_leave INTEGER NOT NULL DEFAULT 30,
            personal_leave INTEGER NOT NULL DEFAULT 6,
            vacation_leave INTEGER NOT NULL DEFAULT 6,
            other_leave INTEGER NOT NULL DEFAULT 30,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, org_id, year)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            username TEXT,
            event_type TEXT NOT NULL,
            action_detail TEXT,
            ip_address TEXT,
            user_agent TEXT,
            ai_model TEXT,
            tokens_used INTEGER DEFAULT 0,
            department TEXT DEFAULT 'General',
            status TEXT DEFAULT 'success',
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
    # Migration: Add visibility & access_level to kb_categories if not exists
    try:
        cursor.execute("ALTER TABLE kb_categories ADD COLUMN visibility TEXT DEFAULT 'public'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE kb_categories ADD COLUMN access_level TEXT DEFAULT 'public'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN clearance_level TEXT DEFAULT 'employee'")
    except sqlite3.OperationalError: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            organization_id INTEGER DEFAULT 1,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_ts ON audit_logs(timestamp)")

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
            organization_id INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(scope_category_id) REFERENCES kb_categories(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wiki_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT,
            content TEXT,
            author TEXT,
            category_id INTEGER,
            org_id INTEGER DEFAULT 1,
            views INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            org_id INTEGER DEFAULT 1,
            position INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            column_id INTEGER DEFAULT 1,
            position INTEGER DEFAULT 0,
            assignee TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'normal',
            is_done INTEGER DEFAULT 0,
            created_by TEXT,
            org_id INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: Add missing columns to wiki_pages and kanban_cards if tables existed previously
    for alter_sql in [
        "ALTER TABLE wiki_pages ADD COLUMN org_id INTEGER DEFAULT 1",
        "ALTER TABLE wiki_pages ADD COLUMN category_id INTEGER",
        "ALTER TABLE wiki_pages ADD COLUMN views INTEGER DEFAULT 0",
        "ALTER TABLE kanban_cards ADD COLUMN org_id INTEGER DEFAULT 1",
        "ALTER TABLE kanban_cards ADD COLUMN created_by TEXT",
        "ALTER TABLE kanban_columns ADD COLUMN org_id INTEGER DEFAULT 1",
    ]:
        try:
            cursor.execute(alter_sql)
        except sqlite3.OperationalError:
            pass

    # Migration: Add organization_id to ai_personas if not exists
    try:
        cursor.execute("ALTER TABLE ai_personas ADD COLUMN organization_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError: pass
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
            line_permissions TEXT DEFAULT 'report,links,reconcile,search,folder,leave',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col, col_type in [
        ("totp_secret", "TEXT"), 
        ("totp_backup_codes", "TEXT"), 
        ("totp_enabled", "INTEGER DEFAULT 0"), 
        ("totp_type", "TEXT DEFAULT 'authenticator'"), 
        ("session_version", "INTEGER DEFAULT 1"),
        ("can_broadcast_line", "INTEGER DEFAULT 0"),
        ("can_manage_peak", "INTEGER DEFAULT 0")
    ]:
        try: cursor.execute(f"ALTER TABLE user_settings ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE organizations ADD COLUMN owner_username TEXT")
    except sqlite3.OperationalError: pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_invite_tokens (
            token TEXT PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            created_by TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            department TEXT,
            max_uses INTEGER DEFAULT 0,
            used_count INTEGER DEFAULT 0,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
        CREATE TABLE IF NOT EXISTS ip_blacklist (
            ip_address TEXT PRIMARY KEY,
            reason TEXT,
            blocked_until DATETIME,
            violation_count INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_view_financial INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_manage_leave INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN line_permissions TEXT DEFAULT 'report,links,reconcile,search,folder,leave'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN locked_until DATETIME")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN totp_enabled INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN totp_secret TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN totp_backup_codes TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_use_ai INTEGER DEFAULT 1")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_claim_expense INTEGER DEFAULT 1")
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
            status TEXT DEFAULT 'published',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES kb_categories(id) ON DELETE SET NULL
        )
    """)
    # Migration: add status column to existing wiki_pages tables
    try:
        cursor.execute("ALTER TABLE wiki_pages ADD COLUMN status TEXT DEFAULT 'published'")
    except Exception:
        pass

    # --- Performance Optimization: Indexes ---
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_username ON messages(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_room_messages_room_id ON room_messages(room_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_private_messages_participants ON private_messages(sender, recipient)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_private_messages_org_id ON private_messages(organization_id)")
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
            event_text TEXT,
            user TEXT,
            organization_id INTEGER DEFAULT 1,
            time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN organization_id INTEGER DEFAULT 1")
    except Exception:
        pass

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
            org_id INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: add org_id, sync_status, local_filepath to drive_logs if missing
    try:
        cursor.execute("ALTER TABLE drive_logs ADD COLUMN org_id INTEGER DEFAULT 1")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE drive_logs ADD COLUMN sync_status TEXT DEFAULT 'synced'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE drive_logs ADD COLUMN local_filepath TEXT")
    except Exception:
        pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_created_at ON drive_logs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_filename ON drive_logs(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_org_id ON drive_logs(org_id)")

    # --- Offline-First Resilient Upload Queue ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offline_upload_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            username TEXT,
            user_id TEXT,
            original_filename TEXT NOT NULL,
            local_filepath TEXT NOT NULL,
            mimetype TEXT,
            folder_id TEXT,
            folder_name TEXT,
            analysis_json TEXT,
            extracted_data_json TEXT,
            verification_status TEXT,
            line_sender_name TEXT,
            sync_status TEXT DEFAULT 'pending',
            drive_link TEXT,
            sheets_row INTEGER,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            synced_at DATETIME
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_offline_queue_sync_status ON offline_upload_queue(sync_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_offline_queue_org_id ON offline_upload_queue(org_id)")

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
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
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
            manager_username TEXT,
            PRIMARY KEY (organization_id, username),
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_profiles (
            org_id INTEGER PRIMARY KEY,
            business_type TEXT,
            vat_status TEXT,
            branch_type TEXT,
            business_name_th TEXT,
            business_name_en TEXT,
            tax_id TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            district TEXT,
            province TEXT,
            zipcode TEXT,
            phone TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    # --- Per-Org LINE Bot Channel Key Integration ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_line_configs (
            org_id INTEGER PRIMARY KEY,
            channel_access_token TEXT,
            channel_secret TEXT,
            bot_basic_id TEXT,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_login_tokens (
            token      TEXT PRIMARY KEY,
            status     TEXT DEFAULT 'pending',
            username   TEXT,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stripe_processed_events (
            event_id     TEXT PRIMARY KEY,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # DB-backed LINE link tokens (แทน in-memory PENDING_LINE_LINKS)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_line_links (
            token        TEXT PRIMARY KEY,
            line_user_id TEXT NOT NULL,
            expires_at   REAL NOT NULL
        )
    """)
    # DB-backed OAuth2 states (แทน in-memory _OAUTH_STATES)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_states (
            state       TEXT PRIMARY KEY,
            data_json   TEXT NOT NULL,
            expires_at  REAL NOT NULL
        )
    """)

    # Custom Categories & AI Auto-Categorization Rules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_expense_categories (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id        INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            account_code  TEXT DEFAULT '',
            parent_id     INTEGER DEFAULT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_category_rules (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id        INTEGER NOT NULL,
            keyword       TEXT NOT NULL,
            category_name TEXT NOT NULL,
            rule_type     TEXT DEFAULT 'contains',
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_members_username ON organization_members(username)")
    # Migration: plan_expires_at, Stripe fields on organizations
    for col_sql in [
        "ALTER TABLE organizations ADD COLUMN plan_expires_at DATETIME",
        "ALTER TABLE organizations ADD COLUMN stripe_customer_id TEXT",
        "ALTER TABLE organizations ADD COLUMN stripe_subscription_id TEXT",
        "ALTER TABLE organizations ADD COLUMN whitelist_enabled INTEGER DEFAULT 0",
        "ALTER TABLE organization_members ADD COLUMN manager_username TEXT",
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER DEFAULT 1,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            created_by TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            color TEXT DEFAULT '#3b82f6',
            icon TEXT DEFAULT 'building',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(organization_id, name COLLATE NOCASE),
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_departments_org ON organization_departments(organization_id)")
    try:
        cursor.execute("ALTER TABLE organization_allowed_emails ADD COLUMN role TEXT DEFAULT 'member'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE organization_departments ADD COLUMN head_username TEXT DEFAULT ''")
    except Exception:
        pass

    # Migration: add org_id to line_group_mappings for multi-tenant support
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN org_id INTEGER")
    except Exception:
        pass
    # Migration: store real LINE group name and picture fetched from LINE API
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN line_real_name TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN line_picture_url TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN bot_enabled INTEGER DEFAULT 1")
    except Exception:
        pass

    # Seed default organization
    cursor.execute("INSERT OR IGNORE INTO organizations (id, name, slug, plan) VALUES (1, 'Default Organization', 'default', 'free')")
    # Ensure system admin accounts are in default org if needed
    for uname in ("Admin", "admin"):
        cursor.execute("SELECT 1 FROM organization_members WHERE username = ? COLLATE NOCASE AND organization_id = 1", (uname,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO organization_members (organization_id, username, role)
                VALUES (1, ?, 'admin')
            """, (uname,))

    # Database Consistency: Clean orphan records to maintain PRAGMA foreign_key_check = 0
    try:
        cursor.execute("DELETE FROM comments WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM post_views WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM likes WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM polls WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM poll_votes WHERE poll_id NOT IN (SELECT id FROM polls)")
        cursor.execute("DELETE FROM poll_options WHERE poll_id NOT IN (SELECT id FROM polls)")
        cursor.execute("DELETE FROM room_members WHERE room_id NOT IN (SELECT id FROM chat_rooms)")
    except Exception:
        pass


    # ══════════════════════════════════════════════════════
    # Feature: Quotation / Invoice
    # ══════════════════════════════════════════════════════
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id          INTEGER NOT NULL,
            quotation_no    TEXT NOT NULL,
            type            TEXT DEFAULT 'quotation',   -- quotation | invoice
            customer_name   TEXT NOT NULL,
            customer_company TEXT DEFAULT '',
            customer_address TEXT DEFAULT '',
            customer_tax_id  TEXT DEFAULT '',
            customer_email   TEXT DEFAULT '',
            customer_phone   TEXT DEFAULT '',
            items           TEXT DEFAULT '[]',           -- JSON [{name,qty,unit,price}]
            subtotal        REAL DEFAULT 0,
            discount        REAL DEFAULT 0,
            vat_rate        REAL DEFAULT 7,
            vat_amount      REAL DEFAULT 0,
            wht_rate        REAL DEFAULT 0,
            wht_amount      REAL DEFAULT 0,
            total           REAL DEFAULT 0,
            status          TEXT DEFAULT 'draft',        -- draft|sent|approved|rejected|paid
            notes           TEXT DEFAULT '',
            valid_until     TEXT DEFAULT '',
            created_by      TEXT NOT NULL,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotations_org ON quotations(org_id, created_at)")

    # ══════════════════════════════════════════════════════
    # Feature: CRM — Customers & Deals
    # ══════════════════════════════════════════════════════
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id      INTEGER NOT NULL,
            name        TEXT NOT NULL,
            company     TEXT DEFAULT '',
            email       TEXT DEFAULT '',
            phone       TEXT DEFAULT '',
            address     TEXT DEFAULT '',
            tax_id      TEXT DEFAULT '',
            tags        TEXT DEFAULT '[]',
            notes       TEXT DEFAULT '',
            created_by  TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_customers_org ON crm_customers(org_id)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_deals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id          INTEGER NOT NULL,
            customer_id     INTEGER,
            title           TEXT NOT NULL,
            value           REAL DEFAULT 0,
            stage           TEXT DEFAULT 'lead',  -- lead|qualified|proposal|negotiation|won|lost
            probability     INTEGER DEFAULT 50,
            expected_close  TEXT DEFAULT '',
            assigned_to     TEXT DEFAULT '',
            notes           TEXT DEFAULT '',
            created_by      TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES crm_customers(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_deals_org ON crm_deals(org_id, stage)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_activities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id      INTEGER NOT NULL,
            deal_id     INTEGER,
            customer_id INTEGER,
            type        TEXT DEFAULT 'note',   -- note|call|email|meeting
            content     TEXT NOT NULL,
            created_by  TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(deal_id) REFERENCES crm_deals(id) ON DELETE CASCADE
        )
    """)

    # ══════════════════════════════════════════════════════
    # Feature: Meeting Notes
    # ══════════════════════════════════════════════════════
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_notes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id          INTEGER NOT NULL,
            title           TEXT NOT NULL,
            audio_filename  TEXT DEFAULT '',
            transcript      TEXT DEFAULT '',
            summary         TEXT DEFAULT '',
            action_items    TEXT DEFAULT '[]',   -- JSON [{task, assignee, due}]
            participants    TEXT DEFAULT '',
            meeting_date    TEXT DEFAULT '',
            wiki_page_id    INTEGER DEFAULT NULL,
            created_by      TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_notes_org ON meeting_notes(org_id, created_at)")

    # ══════════════════════════════════════════════════════
    # High-Performance Composite Indexes
    # ══════════════════════════════════════════════════════
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_org_user_time ON messages(organization_id, username, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_room_messages_room_time ON room_messages(room_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(username, is_read, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_org_date ON schedules(organization_id, start_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(username, organization_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_tracking_org_ym ON usage_tracking(org_id, year_month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotations_org_created ON quotations(org_id, created_at)")

    conn.commit()
    conn.close()


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
    """Transfers the Owner status of an organization to another existing member."""
    if not is_org_owner(org_id, current_owner):
        return False, "เฉพาะ Owner ปัจจุบันเท่านั้นที่สามารถโอนสิทธิ์ความเป็นเจ้าของได้"
    if current_owner.lower() == new_owner.lower():
        return False, "ไม่สามารถโอนสิทธิ์ให้ตัวเองได้"
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT role FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE", (org_id, new_owner))
        target_row = cur.fetchone()
        if not target_row:
            return False, f"ไม่พบผู้ใช้ '{new_owner}' ในองค์กรนี้"
        
        cur.execute("UPDATE organization_members SET role = 'admin' WHERE organization_id = ? AND username = ? COLLATE NOCASE", (org_id, new_owner))
        cur.execute("UPDATE organizations SET owner_username = ? WHERE id = ?", (new_owner, org_id))
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
        from . import billing
    except (ImportError, ValueError):
        import billing
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

        active_plan = billing.get_effective_plan(org_id)
        plan_config = billing.get_plan_config(active_plan)
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


def transfer_org_ownership(org_id: int, current_owner: str, new_owner: str) -> tuple[bool, str]:
    """Transfers the ownership / Super Admin status of an organization to another member."""
    if not current_owner or not new_owner:
        return False, "ระบุชื่อผู้ใช้ไม่ถูกต้อง"
    if current_owner.lower() == new_owner.lower():
        return False, "ไม่สามารถโอนสิทธิ์ให้ตนเองได้"
    if not is_org_owner(org_id, current_owner):
        return False, "เฉพาะ Admin ใหญ่ (Owner) ปัจจุบันเท่านั้นที่มีสิทธิ์โอนความเป็นเจ้าขององค์กร"
    
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # 1. Verify target is a member of the organization
        cursor.execute("SELECT role, joined_at FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE", (org_id, new_owner))
        target_row = cursor.fetchone()
        if not target_row:
            return False, "ผู้รับสิทธิ์ไม่ได้เป็นสมาชิกในองค์กรนี้"
        
        # 2. Get current earliest admin joined_at to shift target earlier
        cursor.execute("""
            SELECT joined_at FROM organization_members 
            WHERE organization_id = ? AND username = ? COLLATE NOCASE
        """, (org_id, current_owner))
        curr_row = cursor.fetchone()
        curr_joined = curr_row[0] if curr_row else "2020-01-01 00:00:00"

        # 3. Promote target to admin and set joined_at 1 second earlier than current owner
        import datetime
        try:
            from datetime import datetime as dt, timedelta
            base_dt = dt.fromisoformat(curr_joined)
            new_joined = (base_dt - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            new_joined = "2019-01-01 00:00:00"

        cursor.execute("""
            UPDATE organization_members 
            SET role = 'admin', joined_at = ? 
            WHERE organization_id = ? AND username = ? COLLATE NOCASE
        """, (new_joined, org_id, new_owner))

        # 4. Ensure current owner remains an admin
        cursor.execute("""
            UPDATE organization_members 
            SET role = 'admin' 
            WHERE organization_id = ? AND username = ? COLLATE NOCASE
        """, (org_id, current_owner))

        conn.commit()
        return True, "โอนสิทธิ์ความเป็นเจ้าขององค์กรสำเร็จเรียบร้อยแล้ว"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


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
    try:
        cursor.execute("SELECT email, added_by, created_at, role FROM organization_allowed_emails WHERE organization_id = ? ORDER BY created_at DESC", (org_id,))
        rows = cursor.fetchall()
        emails = [{"email": r[0], "added_by": r[1], "created_at": r[2], "role": r[3] or "member"} for r in rows]
    except Exception:
        cursor.execute("SELECT email, added_by, created_at FROM organization_allowed_emails WHERE organization_id = ? ORDER BY created_at DESC", (org_id,))
        rows = cursor.fetchall()
        emails = [{"email": r[0], "added_by": r[1], "created_at": r[2], "role": "member"} for r in rows]
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

def get_email_whitelisted_organizations(email: str) -> list:
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT organization_id, added_by, created_at, role FROM organization_allowed_emails WHERE email = ? COLLATE NOCASE", (email,))
        rows = cursor.fetchall()
        orgs = [{"organization_id": r[0], "added_by": r[1], "created_at": r[2], "role": r[3] or "member"} for r in rows]
    except Exception:
        # Fallback if role doesn't exist
        cursor.execute("SELECT organization_id, added_by, created_at FROM organization_allowed_emails WHERE email = ? COLLATE NOCASE", (email,))
        rows = cursor.fetchall()
        orgs = [{"organization_id": r[0], "added_by": r[1], "created_at": r[2], "role": "member"} for r in rows]
    conn.close()
    return orgs

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


def add_drive_log(filename, category=None, amount=None, doc_date=None, summary=None, file_link=None, user_id=None, org_id=1, sync_status="synced", local_filepath=None):
    """Log a file upload/analysis event to the database with connection safety."""
    try:
        with _get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drive_logs (filename, category, amount, doc_date, summary, file_link, user_id, org_id, sync_status, local_filepath)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, category, amount, doc_date, summary, file_link, user_id, org_id or 1, sync_status, local_filepath))
            log_id = cursor.lastrowid
            return log_id
    except Exception as e:
        print(f"❌ Error adding drive log: {e}")
        return None

def add_offline_upload(org_id=1, username=None, user_id=None, original_filename="", local_filepath="",
                       mimetype=None, folder_id=None, folder_name=None, analysis=None,
                       extracted_data=None, verification_status="-", line_sender_name=None):
    """Register an offline or local receipt upload for subsequent cloud sync."""
    try:
        import json
        analysis_json = json.dumps(analysis, ensure_ascii=False) if analysis else None
        extracted_data_json = json.dumps(extracted_data, ensure_ascii=False) if extracted_data else None
        with _get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO offline_upload_queue (
                    org_id, username, user_id, original_filename, local_filepath,
                    mimetype, folder_id, folder_name, analysis_json, extracted_data_json,
                    verification_status, line_sender_name, sync_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                org_id or 1, username, user_id, original_filename, local_filepath,
                mimetype, folder_id, folder_name, analysis_json, extracted_data_json,
                verification_status, line_sender_name
            ))
            return cursor.lastrowid
    except Exception as e:
        print(f"❌ Error adding offline upload queue item: {e}")
        return None

def get_pending_offline_uploads(limit=20):
    """Retrieve pending offline uploads that need syncing to Google Drive/Sheets."""
    try:
        import json
        with _get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM offline_upload_queue
                WHERE sync_status = 'pending' OR (sync_status = 'failed' AND retry_count < 10)
                ORDER BY id ASC LIMIT ?
            """, (limit,))
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            items = []
            for row in rows:
                d = dict(zip(columns, row))
                if d.get("analysis_json"):
                    try: d["analysis"] = json.loads(d["analysis_json"])
                    except: d["analysis"] = None
                else:
                    d["analysis"] = None
                if d.get("extracted_data_json"):
                    try: d["extracted_data"] = json.loads(d["extracted_data_json"])
                    except: d["extracted_data"] = None
                else:
                    d["extracted_data"] = None
                items.append(d)
            return items
    except Exception as e:
        print(f"❌ Error retrieving pending offline uploads: {e}")
        return []

def update_offline_upload_status(upload_id: int, sync_status: str, drive_link: str = None, sheets_row: int = None, error_message: str = None):
    """Update sync status of an item in the offline upload queue, and update drive_logs if synced."""
    try:
        with _get_conn() as conn:
            cursor = conn.cursor()
            if sync_status == 'synced':
                cursor.execute("""
                    UPDATE offline_upload_queue
                    SET sync_status = ?, drive_link = COALESCE(?, drive_link),
                        sheets_row = COALESCE(?, sheets_row), error_message = NULL,
                        synced_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (sync_status, drive_link, sheets_row, upload_id))
                if drive_link:
                    cursor.execute("""
                        SELECT local_filepath FROM offline_upload_queue WHERE id = ?
                    """, (upload_id,))
                    lfp_row = cursor.fetchone()
                    if lfp_row and lfp_row[0]:
                        cursor.execute("""
                            UPDATE drive_logs
                            SET file_link = ?, sync_status = 'synced'
                            WHERE local_filepath = ?
                        """, (drive_link, lfp_row[0]))
            elif sync_status == 'failed':
                cursor.execute("""
                    UPDATE offline_upload_queue
                    SET sync_status = ?, error_message = ?, retry_count = retry_count + 1
                    WHERE id = ?
                """, (sync_status, str(error_message)[:500] if error_message else None, upload_id))
            else:
                cursor.execute("""
                    UPDATE offline_upload_queue
                    SET sync_status = ?
                    WHERE id = ?
                """, (sync_status, upload_id))
            return True
    except Exception as e:
        print(f"❌ Error updating offline upload status: {e}")
        return False

def get_offline_queue_stats(org_id=None):
    """Get counts of pending, synced, and failed items in offline upload queue."""
    try:
        with _get_conn() as conn:
            cursor = conn.cursor()
            if org_id is not None:
                cursor.execute("""
                    SELECT sync_status, COUNT(*) FROM offline_upload_queue
                    WHERE org_id = ? GROUP BY sync_status
                """, (org_id,))
            else:
                cursor.execute("SELECT sync_status, COUNT(*) FROM offline_upload_queue GROUP BY sync_status")
            rows = cursor.fetchall()
            counts = {"pending": 0, "synced": 0, "failed": 0, "total": 0}
            for status, cnt in rows:
                if status in counts:
                    counts[status] = cnt
                counts["total"] += cnt
            return counts
    except Exception as e:
        print(f"❌ Error getting offline queue stats: {e}")
        return {"pending": 0, "synced": 0, "failed": 0, "total": 0}


def optimize_and_checkpoint_db():
    """Performs WAL checkpoint (TRUNCATE), PRAGMA optimize, and incremental vacuum to maintain SQLite health."""
    try:
        with _get_conn() as conn:
            # Commit pending WAL frames back to main database file and truncate WAL to 0 bytes
            res = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            res_row = res.fetchone() if res else None
            # Analyze query planner stats
            conn.execute("PRAGMA optimize")
            # Free unused pages
            try:
                conn.execute("PRAGMA incremental_vacuum(500)")
            except Exception:
                pass
            import logging
            logger = logging.getLogger("database")
            logger.info(f"🧹 [DB Maintenance] SQLite WAL Checkpoint (TRUNCATE) & Optimize completed. Status: {res_row}")
            return {"ok": True, "wal_checkpoint": list(res_row) if res_row else None}
    except Exception as e:
        import logging
        logger = logging.getLogger("database")
        logger.warning(f"⚠️ [DB Maintenance] Optimization error: {e}")
        return {"ok": False, "error": str(e)}


def get_drive_logs(limit=50, offset=0, user_id=None, org_id=None):
    """Retrieve recent drive logs filtered by org."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        where_clauses = []
        params = []
        if org_id is not None:
            where_clauses.append("org_id = ?")
            params.append(org_id)
        if user_id:
            where_clauses.append("user_id = ?")
            params.append(user_id)
        query = "SELECT * FROM drive_logs"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
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

def get_drive_stats(org_id=None):
    """Get statistics for the dashboard, scoped to a specific org."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        where = "WHERE org_id = ?" if org_id is not None else ""
        base_params = (org_id,) if org_id is not None else ()

        cursor.execute(f"SELECT COUNT(*) FROM drive_logs {where}", base_params)
        total_files = cursor.fetchone()[0]

        amt_where = "WHERE org_id = ? AND amount IS NOT NULL" if org_id is not None else "WHERE amount IS NOT NULL"
        amt_params = (org_id,) if org_id is not None else ()
        cursor.execute(f"SELECT SUM(amount) FROM drive_logs {amt_where}", amt_params)
        total_amount = cursor.fetchone()[0] or 0

        cat_where = "WHERE org_id = ?" if org_id is not None else ""
        cursor.execute(f"SELECT category, COUNT(*) as count FROM drive_logs {cat_where} GROUP BY category", base_params)
        categories = dict(cursor.fetchall())

        recent_where = "WHERE org_id = ? AND created_at > datetime('now', '-1 day')" if org_id is not None else "WHERE created_at > datetime('now', '-1 day')"
        cursor.execute(f"SELECT COUNT(*) FROM drive_logs {recent_where}", base_params)
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


def get_cash_flow_projection(org_id=1):
    """
    Analyzes last 3 months of expenses and predicts next month's spending.
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get last 4 months of data (including current)
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as total
        FROM drive_logs
        WHERE org_id = ? AND created_at >= date('now', '-4 months')
        GROUP BY month
        ORDER BY month DESC
    """, (org_id,))
    history = cursor.fetchall()
    
    # Get top 3 expense categories
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM drive_logs
        WHERE org_id = ? AND created_at >= date('now', '-1 month')
        GROUP BY category
        ORDER BY total DESC LIMIT 3
    """, (org_id,))
    top_categories = cursor.fetchall()
    
    conn.close()
    
    totals = [r['total'] for r in history if r['total']]
    avg_projection = sum(totals) / len(totals) if totals else 0
    
    return {
        "history": [dict(r) for r in history],
        "projection": avg_projection,
        "top_categories": [dict(r) for r in top_categories]
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


# ─── Time Attendance & GPS Clock-in Functions ──────────────────────

def record_attendance(username, org_id, check_type, latitude, longitude, address, distance_meters, status):
    """Records a time attendance event (check-in / check-out)."""
    from datetime import datetime
    now = datetime.now()
    check_date = now.strftime("%Y-%m-%d")
    check_time = now.strftime("%H:%M:%S")
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO time_attendance (username, org_id, check_date, check_time, check_type, latitude, longitude, address, distance_meters, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, org_id or 1, check_date, check_time, check_type, latitude, longitude, address, distance_meters, status))
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
        "status": status
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

def get_line_config(org_id: int = None):
    """Returns LINE integration configuration from org_line_configs or app_settings with os.environ fallback."""
    from database import get_app_setting
    import os
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

def stripe_is_event_processed(event_id: str) -> bool:
    conn = _get_conn()
    row = conn.execute(
        "SELECT 1 FROM stripe_processed_events WHERE event_id = ?", (event_id,)
    ).fetchone()
    conn.close()
    return row is not None


def stripe_mark_event_processed(event_id: str) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO stripe_processed_events (event_id) VALUES (?)", (event_id,)
    )
    conn.commit()
    conn.close()


def stripe_try_claim_event(event_id: str) -> bool:
    """Atomically insert event_id. Returns True only if this call claimed it
    (i.e. no concurrent worker already did). Prevents duplicate processing."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO stripe_processed_events (event_id) VALUES (?)", (event_id,)
        )
        claimed = cur.rowcount > 0
        conn.commit()
        return claimed
    finally:
        conn.close()


def stripe_remove_event_claim(event_id: str) -> None:
    """Remove a previously claimed event so Stripe can retry on processing failure."""
    conn = _get_conn()
    conn.execute("DELETE FROM stripe_processed_events WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()


# ─── Org Membership Check (for session re-validation) ────────────────────────

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


# ══════════════════════════════════════════════════════════════
# QUOTATION / INVOICE CRUD
# ══════════════════════════════════════════════════════════════

def quotation_create(org_id: int, data: dict) -> int:
    conn = _get_conn()
    cur = conn.cursor()
    # auto-generate quotation number
    ym = __import__('datetime').date.today().strftime('%Y%m')
    prefix = 'INV' if data.get('type') == 'invoice' else 'QT'
    cur.execute("SELECT COUNT(*) FROM quotations WHERE org_id=? AND strftime('%Y%m', created_at)=?", (org_id, ym))
    seq = (cur.fetchone()[0] or 0) + 1
    qno = data.get('quotation_no') or f"{prefix}{ym}{seq:03d}"
    cur.execute("""
        INSERT INTO quotations (org_id, quotation_no, type, customer_name, customer_company,
            customer_address, customer_tax_id, customer_email, customer_phone,
            items, subtotal, discount, vat_rate, vat_amount, wht_rate, wht_amount, total,
            status, notes, valid_until, created_by)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (org_id, qno, data.get('type','quotation'), data.get('customer_name',''),
         data.get('customer_company',''), data.get('customer_address',''),
         data.get('customer_tax_id',''), data.get('customer_email',''), data.get('customer_phone',''),
         __import__('json').dumps(data.get('items',[])),
         data.get('subtotal',0), data.get('discount',0), data.get('vat_rate',7),
         data.get('vat_amount',0), data.get('wht_rate',0), data.get('wht_amount',0),
         data.get('total',0), data.get('status','draft'), data.get('notes',''),
         data.get('valid_until',''), data.get('created_by',''))
    )
    qid = cur.lastrowid
    conn.commit(); conn.close()
    return qid

def quotation_list(org_id: int, status: str = None, type_: str = None) -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    q = "SELECT * FROM quotations WHERE org_id=?"
    params = [org_id]
    if status: q += " AND status=?"; params.append(status)
    if type_:  q += " AND type=?";   params.append(type_)
    q += " ORDER BY created_at DESC"
    rows = [dict(r) for r in cur.execute(q, params).fetchall()]
    conn.close()
    import json
    for r in rows:
        try: r['items'] = json.loads(r.get('items') or '[]')
        except: r['items'] = []
    return rows

def quotation_get(qid: int, org_id: int) -> dict | None:
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM quotations WHERE id=? AND org_id=?", (qid, org_id)).fetchone()
    conn.close()
    if not row: return None
    import json
    r = dict(row)
    try: r['items'] = json.loads(r.get('items') or '[]')
    except: r['items'] = []
    return r

def quotation_update(qid: int, org_id: int, data: dict) -> bool:
    import json as _json
    conn = _get_conn(); cur = conn.cursor()
    items = data.get('items', [])
    cur.execute("""UPDATE quotations SET
        customer_name=?, customer_company=?, customer_address=?, customer_tax_id=?,
        customer_email=?, customer_phone=?, items=?, subtotal=?, discount=?,
        vat_rate=?, vat_amount=?, wht_rate=?, wht_amount=?, total=?,
        status=?, notes=?, valid_until=?, type=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=? AND org_id=?""",
        (data.get('customer_name',''), data.get('customer_company',''),
         data.get('customer_address',''), data.get('customer_tax_id',''),
         data.get('customer_email',''), data.get('customer_phone',''),
         _json.dumps(items), data.get('subtotal',0), data.get('discount',0),
         data.get('vat_rate',7), data.get('vat_amount',0), data.get('wht_rate',0),
         data.get('wht_amount',0), data.get('total',0),
         data.get('status','draft'), data.get('notes',''), data.get('valid_until',''),
         data.get('type','quotation'), qid, org_id)
    )
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def quotation_delete(qid: int, org_id: int) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM quotations WHERE id=? AND org_id=?", (qid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def quotation_set_status(qid: int, org_id: int, status: str) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("UPDATE quotations SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND org_id=?",
                (status, qid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok


# ══════════════════════════════════════════════════════════════
# CRM CRUD
# ══════════════════════════════════════════════════════════════

def crm_customer_list(org_id: int, q: str = '') -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    if q:
        rows = cur.execute("SELECT * FROM crm_customers WHERE org_id=? AND (name LIKE ? OR company LIKE ? OR email LIKE ? OR phone LIKE ?) ORDER BY name",
                           (org_id, f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()
    else:
        rows = cur.execute("SELECT * FROM crm_customers WHERE org_id=? ORDER BY name", (org_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crm_customer_get(cid: int, org_id: int) -> dict | None:
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM crm_customers WHERE id=? AND org_id=?", (cid, org_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def crm_customer_create(org_id: int, data: dict) -> int:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO crm_customers (org_id, name, company, email, phone, address, tax_id, tags, notes, created_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (org_id, data.get('name',''), data.get('company',''), data.get('email',''),
                 data.get('phone',''), data.get('address',''), data.get('tax_id',''),
                 __import__('json').dumps(data.get('tags',[])), data.get('notes',''), data.get('created_by','')))
    cid = cur.lastrowid; conn.commit(); conn.close(); return cid

def crm_customer_update(cid: int, org_id: int, data: dict) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""UPDATE crm_customers SET name=?, company=?, email=?, phone=?, address=?, tax_id=?, tags=?, notes=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=? AND org_id=?""",
                (data.get('name',''), data.get('company',''), data.get('email',''),
                 data.get('phone',''), data.get('address',''), data.get('tax_id',''),
                 __import__('json').dumps(data.get('tags',[])), data.get('notes',''), cid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_customer_delete(cid: int, org_id: int) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM crm_customers WHERE id=? AND org_id=?", (cid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_deal_list(org_id: int, customer_id: int = None, stage: str = None) -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    q = """SELECT d.*, c.name as customer_name, c.company as customer_company
           FROM crm_deals d LEFT JOIN crm_customers c ON d.customer_id=c.id
           WHERE d.org_id=?"""
    params = [org_id]
    if customer_id: q += " AND d.customer_id=?"; params.append(customer_id)
    if stage: q += " AND d.stage=?"; params.append(stage)
    q += " ORDER BY d.created_at DESC"
    rows = cur.execute(q, params).fetchall()
    conn.close(); return [dict(r) for r in rows]

def crm_deal_create(org_id: int, data: dict) -> int:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO crm_deals (org_id, customer_id, title, value, stage, probability, expected_close, assigned_to, notes, created_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (org_id, data.get('customer_id'), data.get('title',''), data.get('value',0),
                 data.get('stage','lead'), data.get('probability',50), data.get('expected_close',''),
                 data.get('assigned_to',''), data.get('notes',''), data.get('created_by','')))
    did = cur.lastrowid; conn.commit(); conn.close(); return did

def crm_deal_update(did: int, org_id: int, data: dict) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""UPDATE crm_deals SET customer_id=?, title=?, value=?, stage=?, probability=?, expected_close=?, assigned_to=?, notes=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=? AND org_id=?""",
                (data.get('customer_id'), data.get('title',''), data.get('value',0),
                 data.get('stage','lead'), data.get('probability',50), data.get('expected_close',''),
                 data.get('assigned_to',''), data.get('notes',''), did, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_deal_delete(did: int, org_id: int) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM crm_deals WHERE id=? AND org_id=?", (did, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_activity_add(org_id: int, data: dict) -> int:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO crm_activities (org_id, deal_id, customer_id, type, content, created_by) VALUES (?,?,?,?,?,?)",
                (org_id, data.get('deal_id'), data.get('customer_id'), data.get('type','note'),
                 data.get('content',''), data.get('created_by','')))
    aid = cur.lastrowid; conn.commit(); conn.close(); return aid

def crm_activities_get(org_id: int, deal_id: int = None, customer_id: int = None) -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    q = "SELECT * FROM crm_activities WHERE org_id=?"
    params = [org_id]
    if deal_id: q += " AND deal_id=?"; params.append(deal_id)
    if customer_id: q += " AND customer_id=?"; params.append(customer_id)
    q += " ORDER BY created_at DESC LIMIT 50"
    rows = cur.execute(q, params).fetchall()
    conn.close(); return [dict(r) for r in rows]


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
        except: d['action_items'] = []
        result.append(d)
    return result

def meeting_note_get(mid: int, org_id: int) -> dict | None:
    import json as _j
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM meeting_notes WHERE id=? AND org_id=?", (mid, org_id)).fetchone()
    conn.close()
    if not row: return None
    d = dict(row)
    try: d['action_items'] = _j.loads(d.get('action_items') or '[]')
    except: d['action_items'] = []
    return d

def meeting_note_update(mid: int, org_id: int, data: dict) -> bool:
    import json as _j
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


def _oauth_state_cleanup():
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM oauth_states WHERE expires_at < ?", (time.time(),))
        conn.commit()
        conn.close()
    except Exception:
        pass


def log_audit_event(username: str, org_id: int, action: str, details: str = "", ip_address: str = ""):
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (username, organization_id, action, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
        """, (username or 'System', org_id or 1, action, details or '', ip_address or ''))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error logging audit event: {e}")

# Old duplicate get_audit_logs removed - consolidated definition at bottom of file

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
def get_custom_categories(org_id: int) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category_name, account_code, parent_id, created_at
            FROM custom_expense_categories
            WHERE org_id = ?
            ORDER BY category_name ASC
        """, (str(org_id),))
        return [
            {
                "id": r[0],
                "category_name": r[1],
                "account_code": r[2] or "",
                "parent_id": r[3],
                "created_at": str(r[4])
            }
            for r in cursor.fetchall()
        ]
    finally:
        conn.close()

def add_custom_category(org_id: int, category_name: str, account_code: str = "", parent_id: int = None) -> int:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO custom_expense_categories (org_id, category_name, account_code, parent_id)
            VALUES (?, ?, ?, ?)
        """, (str(org_id), category_name.strip(), account_code.strip(), parent_id))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def delete_custom_category(org_id: int, category_id: int) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM custom_expense_categories WHERE id = ? AND org_id = ?", (category_id, str(org_id)))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_ai_category_rules(org_id: int) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, keyword, category_name, rule_type, created_at
            FROM ai_category_rules
            WHERE org_id = ?
            ORDER BY id DESC
        """, (str(org_id),))
        return [
            {
                "id": r[0],
                "keyword": r[1],
                "category_name": r[2],
                "rule_type": r[3] or "contains",
                "created_at": str(r[4])
            }
            for r in cursor.fetchall()
        ]
    finally:
        conn.close()

def add_ai_category_rule(org_id: int, keyword: str, category_name: str, rule_type: str = "contains") -> int:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_category_rules (org_id, keyword, category_name, rule_type)
            VALUES (?, ?, ?, ?)
        """, (str(org_id), keyword.strip().lower(), category_name.strip(), rule_type))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def delete_ai_category_rule(org_id: int, rule_id: int) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ai_category_rules WHERE id = ? AND org_id = ?", (rule_id, str(org_id)))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# Account Lockout & Brute-Force Protection Functions
# ═══════════════════════════════════════════════════════════════

def is_account_locked(username: str) -> tuple[bool, int]:
    """
    Checks if account is currently locked out due to excessive failed logins.
    Returns (is_locked, seconds_remaining).
    """
    if not username:
        return False, 0
    from datetime import datetime
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
        except Exception:
            pass
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
    from datetime import datetime, timedelta
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


def log_audit_event(username: str, event_type: str, action_detail: str = "", ip_address: str = "", user_agent: str = "", ai_model: str = "", tokens_used: int = 0, status: str = "success", org_id: int = 1, department: str = None) -> bool:
    """Logs security, authentication, AI usage, and admin audit events."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # If department is not supplied, fetch from user_profiles
        if not department and username:
            try:
                cursor.execute("SELECT department FROM user_profiles WHERE username = ? COLLATE NOCASE", (username.strip(),))
                row = cursor.fetchone()
                if row and row[0]:
                    department = row[0]
            except Exception: pass
            
        if not department:
            department = "General"
            
        cursor.execute("""
            INSERT INTO audit_logs (org_id, username, event_type, action_detail, ip_address, user_agent, ai_model, tokens_used, department, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (org_id, username or "Anonymous", event_type, action_detail, ip_address, user_agent, ai_model, tokens_used, department, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.getLogger("OrgChatAI").error(f"[log_audit_event] Error: {e}")
        return False


class AuditLogList(list):
    """List subclass that also supports dictionary-style access for total and logs."""
    def __init__(self, items, total=None):
        super().__init__(items)
        self.total = len(items) if total is None else total
        self.logs = list(items)

    def __getitem__(self, item):
        if item == "total":
            return self.total
        elif item == "logs":
            return self.logs
        return super().__getitem__(item)

    def get(self, key, default=None):
        if key == "total":
            return self.total
        elif key == "logs":
            return self.logs
        return default


def get_audit_logs(org_id: int = 1, limit: int = 100, offset: int = 0, event_type: str = None, username: str = None, search: str = None, action: str = None, username_filter: str = None, action_filter: str = None):
    """Fetches paginated, searchable audit log entries with HMAC verification."""
    import hmac
    import hashlib
    username = username or username_filter
    search = search or action or action_filter
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(audit_logs)")
        cols = [c[1] for c in cursor.fetchall()]
        org_col = "org_id" if "org_id" in cols else "organization_id" if "organization_id" in cols else "org_id"
        
        query = f"SELECT * FROM audit_logs WHERE {org_col} = ?"
        params = [org_id]
        
        if event_type and "event_type" in cols:
            query += " AND event_type = ?"
            params.append(event_type)
        if username and "username" in cols:
            query += " AND username LIKE ? COLLATE NOCASE"
            params.append(f"%{username.strip()}%")
        if search:
            search_conditions = []
            s = f"%{search.strip()}%"
            for candidate in ["username", "action", "action_detail", "details", "ip_address", "ai_model", "department"]:
                if candidate in cols:
                    search_conditions.append(f"{candidate} LIKE ?")
                    params.append(s)
            if search_conditions:
                query += " AND (" + " OR ".join(search_conditions) + ")"
            
        # Count total matches
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total_row = cursor.fetchone()
        total = total_row[0] if total_row else 0
        
        order_col = "id" if "id" in cols else "timestamp"
        query += f" ORDER BY {order_col} DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        
        secret_salt = os.environ.get("SECRET_KEY", "orgchat_secret_audit_salt")
        for row_dict in rows:
            oid = row_dict.get("org_id") or row_dict.get("organization_id") or 1
            uname = row_dict.get("username") or ""
            act = row_dict.get("action") or row_dict.get("event_type") or ""
            det = row_dict.get("details") or row_dict.get("action_detail") or ""
            ip = row_dict.get("ip_address") or ""
            sig = row_dict.get("hash_signature")
            payload = f"{oid}:{uname}:{act}:{det}:{ip}"
            expected_sig = hmac.new(secret_salt.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
            row_dict["is_verified"] = (sig == expected_sig) if sig else True
        
        return AuditLogList(rows, total=total)
    except Exception as e:
        logging.getLogger("OrgChatAI").error(f"[get_audit_logs error] {e}")
        return AuditLogList([], total=0)
    finally:
        conn.close()


def get_security_audit_metrics(org_id: int = 1, days: int = 30) -> dict:
    """Calculates security, login, AI usage, and department statistics for IT Security Audit Dashboard."""
    from datetime import datetime, timedelta
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
    
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # 1. High-level totals
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN event_type IN ('login_success', 'login_failed', 'account_lockout') THEN 1 END) as total_logins,
                COUNT(CASE WHEN event_type = 'login_success' THEN 1 END) as successful_logins,
                COUNT(CASE WHEN event_type = 'login_failed' THEN 1 END) as failed_logins,
                COUNT(CASE WHEN event_type = 'account_lockout' THEN 1 END) as lockout_incidents,
                COUNT(CASE WHEN event_type IN ('ai_chat', 'ai_rag_query') THEN 1 END) as total_ai_requests,
                COALESCE(SUM(CASE WHEN event_type IN ('ai_chat', 'ai_rag_query') THEN tokens_used ELSE 0 END), 0) as total_tokens
            FROM audit_logs
            WHERE org_id = ? AND timestamp >= ?
        """, (org_id, since_date))
        totals_row = cursor.fetchone()
        totals = dict(totals_row) if totals_row else {}
        
        # 2. Department AI Usage Breakdown
        cursor.execute("""
            SELECT department, COUNT(*) as count, COALESCE(SUM(tokens_used), 0) as tokens
            FROM audit_logs
            WHERE org_id = ? AND event_type IN ('ai_chat', 'ai_rag_query') AND timestamp >= ?
            GROUP BY department
            ORDER BY count DESC
        """, (org_id, since_date))
        dept_usage = [dict(r) for r in cursor.fetchall()]
        
        # 3. AI Model Distribution
        cursor.execute("""
            SELECT COALESCE(NULLIF(ai_model, ''), 'Gemini-3.6-Flash') as model, COUNT(*) as count
            FROM audit_logs
            WHERE org_id = ? AND event_type IN ('ai_chat', 'ai_rag_query') AND timestamp >= ?
            GROUP BY model
            ORDER BY count DESC
        """, (org_id, since_date))
        model_dist = [dict(r) for r in cursor.fetchall()]
        
        # 4. Daily Timeline (past 14 days)
        timeline_since = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d 00:00:00")
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date_str,
                COUNT(CASE WHEN event_type = 'login_success' THEN 1 END) as logins,
                COUNT(CASE WHEN event_type = 'login_failed' THEN 1 END) as failed_logins,
                COUNT(CASE WHEN event_type IN ('ai_chat', 'ai_rag_query') THEN 1 END) as ai_requests
            FROM audit_logs
            WHERE org_id = ? AND timestamp >= ?
            GROUP BY date_str
            ORDER BY date_str ASC
        """, (org_id, timeline_since))
        timeline = [dict(r) for r in cursor.fetchall()]
        
        # 5. Top IP Addresses
        cursor.execute("""
            SELECT ip_address, COUNT(*) as activity_count, username, MAX(timestamp) as last_seen
            FROM audit_logs
            WHERE org_id = ? AND ip_address IS NOT NULL AND ip_address != '' AND timestamp >= ?
            GROUP BY ip_address
            ORDER BY activity_count DESC
            LIMIT 10
        """, (org_id, since_date))
        ip_dist = [dict(r) for r in cursor.fetchall()]

        return {
            "totals": totals,
            "department_usage": dept_usage,
            "model_distribution": model_dist,
            "timeline": timeline,
            "ip_distribution": ip_dist
        }
    finally:
        conn.close()


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


# ═══════════════════════════════════════════════════════════════
# 🛡️ Infosec & Cryptographic Integrity Helpers (Chapter 1 & 4)
# ═══════════════════════════════════════════════════════════════

def compute_sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file for File Integrity Monitoring (FIM)."""
    import hashlib
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def register_file_integrity(filepath: str, category: str = "uploads") -> bool:
    """Store baseline SHA-256 hash of a file for FIM detection."""
    p = Path(filepath)
    if not p.exists() or not p.is_file():
        return False
    
    sha = compute_sha256_file(str(p))
    if not sha:
        return False
        
    size = p.stat().st_size
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO file_integrity_records (file_path, file_name, sha256_hash, file_size, category, last_checked)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) DO UPDATE SET
                sha256_hash = excluded.sha256_hash,
                file_size = excluded.file_size,
                last_checked = CURRENT_TIMESTAMP
        """, (str(p), p.name, sha, size, category))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to register FIM for {filepath}: {e}")
        return False
    finally:
        conn.close()


def verify_file_integrity(filepath: str) -> tuple[bool, str]:
    """Verify if a file has been modified/tampered with against its baseline hash."""
    p = Path(filepath)
    if not p.exists() or not p.is_file():
        return False, "File does not exist on disk"
        
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT sha256_hash FROM file_integrity_records WHERE file_path = ?", (str(p),))
        row = cur.fetchone()
        if not row:
            # Register new baseline if never seen
            register_file_integrity(str(p))
            return True, "Baseline created"
            
        expected_hash = row[0]
        current_hash = compute_sha256_file(str(p))
        if current_hash == expected_hash:
            cur.execute("UPDATE file_integrity_records SET last_checked = CURRENT_TIMESTAMP WHERE file_path = ?", (str(p),))
            conn.commit()
            return True, "Integrity verified (OK)"
        else:
            logger.warning(f"🚨 [FIM ALERT] File {p.name} TAMPERED! Expected={expected_hash} Got={current_hash}")
            return False, f"Tampered! Expected {expected_hash[:8]}... got {current_hash[:8]}..."
    finally:
        conn.close()


def log_audit_event(username: str = "System", action: str = "GENERAL", details: str = "", ip_address: str = "", org_id: int = 1, **kwargs) -> bool:
    """
    Log an audit event with HMAC-SHA256 signature for tamper-evident accounting.
    Supports flexible positional arguments and legacy kwargs (event_type, action_detail, etc.).
    """
    import hmac
    import hashlib

    # Handle legacy positional ordering: log_audit_event(user, org_id, action, details, ip)
    if isinstance(action, int) or (isinstance(action, str) and action.isdigit()):
        # swap org_id and action
        actual_org_id = int(action)
        actual_action = details if details else "GENERAL"
        actual_details = ip_address if ip_address else ""
        actual_ip = kwargs.get("ip_address", "127.0.0.1")
        action = actual_action
        details = actual_details
        ip_address = actual_ip
        org_id = actual_org_id

    # Handle legacy kwargs
    if "event_type" in kwargs and (not action or action == "GENERAL"):
        action = kwargs.get("event_type", "GENERAL")
    if "action_detail" in kwargs and not details:
        details = kwargs.get("action_detail", "")
    if "org_id" in kwargs:
        try:
            org_id = int(kwargs.get("org_id", 1))
        except (ValueError, TypeError):
            org_id = 1
    
    secret_salt = os.environ.get("SECRET_KEY", "orgchat_secret_audit_salt")
    payload = f"{org_id}:{username}:{action}:{details}:{ip_address}"
    sig = hmac.new(secret_salt.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO audit_logs (org_id, username, action, details, ip_address, hash_signature)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (org_id, username or 'System', action, details, ip_address, sig))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to insert audit log: {e}")
        return False
    finally:
        conn.close()





# ═══════════════════════════════════════════════════════════════
# 🛑 Anti-Prompt Injection & Jailbreak Guardrail (Chapter 2)
# ═══════════════════════════════════════════════════════════════

_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)system\s+prompt",
    r"(?i)you\s+are\s+now\s+(DAN|unrestricted|jailbroken|an\s+evil|a\s+hacker)",
    r"(?i)reveal\s+(your\s+)?(instructions|secret|internal\s+prompt|api\s*key)",
    r"(?i)show\s+me\s+your\s+(initial|system)\s+instructions",
    r"(?i)bypass\s+(content\s+filter|safety\s+filter|guardrail)",
    r"(?i)print\s+the\s+system\s+message",
    r"(?i)ลืมคำสั่ง(ก่อนหน้า|ทั้งหมด|เดิม)",
    r"(?i)แสดง\s*(system\s*prompt|คำสั่งระบบ|ความลับของระบบ|api\s*key)",
    r"(?i)ปลดล็อกกฎเกณฑ์ทั้งหมด",
]


def detect_prompt_injection(text: str) -> tuple[bool, str]:
    """Detect prompt injection and jailbreak attempts in user query."""
    if not text:
        return False, ""
    import re
    for pattern in _INJECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            matched_phrase = match.group(0)
            logger.warning(f"🚨 [PROMPT INJECTION DETECTED] Triggered by: '{matched_phrase}' in text: '{text[:80]}...'")
            return True, matched_phrase
    return False, ""


def get_security_health_status(org_id: int = 1) -> dict:
    """Generate a real-time security health score and defense metrics report."""
    import datetime as _dt_mod
    import time as _time_mod
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # 1. Total audit logs and integrity score
        logs = get_audit_logs(org_id=org_id, limit=100)
        total_logs = len(logs)
        verified_logs = sum(1 for l in logs if l.get('is_verified'))
        log_integrity_pct = int((verified_logs / total_logs) * 100) if total_logs > 0 else 100

        # 2. File Integrity Monitoring (FIM) stats
        cur.execute("SELECT COUNT(*), COUNT(CASE WHEN datetime(last_checked) >= datetime('now', '-24 hours') THEN 1 END) FROM file_integrity_records")
        fim_row = cur.fetchone()
        total_tracked_files = fim_row[0] if fim_row else 0
        recent_scanned_files = fim_row[1] if fim_row else 0

        # 3. Failed login attempts in last 24h
        cur.execute("SELECT COUNT(*) FROM login_attempts WHERE success = 0 AND ts >= ?", (int(_time_mod.time()) - 86400,))
        failed_attempts_24h = cur.fetchone()[0]

        # 4. MFA / 2FA Adoption Stats
        cur.execute("SELECT COUNT(*), COUNT(CASE WHEN totp_enabled = 1 THEN 1 END) FROM user_settings")
        user_row = cur.fetchone()
        total_users = user_row[0] if user_row else 1
        mfa_users = user_row[1] if user_row else 0
        mfa_pct = int((mfa_users / total_users) * 100) if total_users > 0 else 0

        # 5. Calculate overall security score (0 - 100)
        score = 100
        if log_integrity_pct < 100:
            score -= (100 - log_integrity_pct)
        if failed_attempts_24h > 10:
            score = max(50, score - 15)

        return {
            "overall_health_score": score,
            "status": "EXCELLENT" if score >= 90 else "GOOD" if score >= 75 else "ATTENTION_REQUIRED",
            "log_integrity_percent": log_integrity_pct,
            "total_audit_logs": total_logs,
            "verified_audit_logs": verified_logs,
            "fim_tracked_files": total_tracked_files,
            "fim_recent_scans": recent_scanned_files,
            "failed_logins_24h": failed_attempts_24h,
            "mfa_enabled_users": mfa_users,
            "total_users": total_users,
            "mfa_adoption_percent": mfa_pct,
            "timestamp": _dt_mod.datetime.now().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# 🛑 Automated IP Blacklist & Threat Defense Guard (Enterprise)
# ═══════════════════════════════════════════════════════════════

def is_ip_blacklisted(ip_address: str) -> tuple[bool, str]:
    """Check if an IP address is currently blocked in the blacklist."""
    if not ip_address or ip_address in ("127.0.0.1", "localhost", "::1"):
        return False, ""
    
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT reason, blocked_until FROM ip_blacklist 
            WHERE ip_address = ? AND (blocked_until IS NULL OR datetime(blocked_until) > datetime('now'))
        """, (ip_address,))
        row = cur.fetchone()
        if row:
            return True, row[0] or "Threat defense security lockout"
        return False, ""
    finally:
        conn.close()


def block_ip(ip_address: str, reason: str = "Automated threat lockout", duration_minutes: int = 60):
    """Add or increment violation for an IP address and lock it out."""
    if not ip_address or ip_address in ("127.0.0.1", "localhost", "::1"):
        return

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ip_blacklist (ip_address, reason, blocked_until, violation_count, created_at)
            VALUES (?, ?, datetime('now', '+' || ? || ' minutes'), 1, datetime('now'))
            ON CONFLICT(ip_address) DO UPDATE SET
                reason = excluded.reason,
                blocked_until = datetime('now', '+' || ? || ' minutes'),
                violation_count = ip_blacklist.violation_count + 1
        """, (ip_address, reason, duration_minutes, duration_minutes))
        conn.commit()
    finally:
        conn.close()


def unblock_ip(ip_address: str) -> bool:
    """Remove an IP address from blacklist (Admin Unban)."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ip_blacklist WHERE ip_address = ?", (ip_address,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_blacklisted_ips() -> list[dict]:
    """Retrieve all actively blocked IPs with violation history."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ip_address, reason, blocked_until, violation_count, created_at
            FROM ip_blacklist
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        return [
            {
                "ip_address": r[0],
                "reason": r[1],
                "blocked_until": r[2],
                "violation_count": r[3],
                "created_at": r[4]
            }
            for r in rows
        ]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# 🛡️ Automated PII Data Masking & Anonymizer Guard (PDPA Compliance)
# ═══════════════════════════════════════════════════════════════

# Pre-compiled Regex patterns for Sensitive PII data
_THAI_NATIONAL_ID_PATTERN = re.compile(r'\b[1-9]\d{12}\b|\b[1-9]\s?\d{4}\s?\d{5}\s?\d{2}\s?\d\b|\b[1-9]-\d{4}-\d{5}-\d{2}-\d\b')
_CREDIT_CARD_PATTERN = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})\b|\b(?:\d{4}[-\s]){3}\d{4}\b')
_THAI_PHONE_PATTERN = re.compile(r'\b(?:0[689]\d{8}|0[2-57]\d{7})\b|\b(?:0[689]\d{1}-\d{3}-\d{4}|0[689]\d{2}-\d{3}-\d{3}|0[2-57]-\d{3}-\d{4})\b')
_EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')


def mask_pii_data(text: str) -> tuple[str, list[dict]]:
    """
    Scans and anonymizes sensitive Personally Identifiable Information (PII)
    in compliance with Thailand's PDPA and GDPR.
    
    Returns:
      (masked_text, detected_pii_items)
    """
    if not text or not isinstance(text, str):
        return text, []

    detected_items = []
    masked = text

    # 1. Thai National ID (13 digits)
    def _mask_national_id(match):
        raw = match.group(0)
        clean = re.sub(r'[-\s]', '', raw)
        if len(clean) == 13:
            detected_items.append({"type": "THAI_NATIONAL_ID", "original": raw})
            return f"[ID: {clean[:1]}-XXXX-XXXXX-XX-{clean[-1:]}]"
        return raw
    masked = _THAI_NATIONAL_ID_PATTERN.sub(_mask_national_id, masked)

    # 2. Credit Card Numbers (15-16 digits)
    def _mask_credit_card(match):
        raw = match.group(0)
        clean = re.sub(r'[-\s]', '', raw)
        if len(clean) in (15, 16):
            detected_items.append({"type": "CREDIT_CARD", "original": raw})
            return f"[CARD: ****-****-****-{clean[-4:]}]"
        return raw
    masked = _CREDIT_CARD_PATTERN.sub(_mask_credit_card, masked)

    # 3. Thai Phone Numbers (9-10 digits)
    def _mask_phone(match):
        raw = match.group(0)
        clean = re.sub(r'[-\s]', '', raw)
        if len(clean) in (9, 10):
            detected_items.append({"type": "PHONE_NUMBER", "original": raw})
            return f"[PHONE: {clean[:3]}-***-{clean[-3:]}]"
        return raw
    masked = _THAI_PHONE_PATTERN.sub(_mask_phone, masked)

    # 4. Email Addresses
    def _mask_email(match):
        raw = match.group(0)
        parts = raw.split('@')
        if len(parts) == 2:
            uname, domain = parts
            detected_items.append({"type": "EMAIL", "original": raw})
            masked_uname = uname[:2] + "***" if len(uname) > 2 else uname[:1] + "***"
            return f"[EMAIL: {masked_uname}@{domain}]"
        return raw
    masked = _EMAIL_PATTERN.sub(_mask_email, masked)
    return masked, detected_items


# ═══════════════════════════════════════════════════════════════
# 🤖 AI Security Threat Intelligence Sentinel (UEBA & DLP Guard)
# ═══════════════════════════════════════════════════════════════

def analyze_user_threat_behavior(username: str, client_ip: str, action: str, details: str = "", org_id: int = 1) -> dict:
    """
    User & Entity Behavior Analytics (UEBA):
    Detects abnormal activity spikes, data exfiltration patterns,
    and rapid query harvesting attempts.
    """
    import time as _t_mod
    conn = _get_conn()
    cur = conn.cursor()
    try:
        now_ts = int(_t_mod.time())
        one_hour_ago = now_ts - 3600
        five_min_ago = now_ts - 300

        # 1. Query rate analysis (Burst Detection in last 5 min)
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE username = ? AND datetime(timestamp) >= datetime('now', '-5 minutes')
        """, (username,))
        burst_count = cur.fetchone()[0]

        # 2. Total security alerts triggered in last 24h
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE (username = ? OR ip_address = ?) 
              AND action LIKE 'SECURITY_%' 
              AND datetime(timestamp) >= datetime('now', '-24 hours')
        """, (username, client_ip))
        alert_count = cur.fetchone()[0]

        # 3. Assess Threat Level & Anomaly Flags
        threat_level = "LOW"
        risk_score = 10
        anomalies = []

        if burst_count > 30:
            threat_level = "HIGH"
            risk_score += 40
            anomalies.append(f"High-frequency request burst ({burst_count} actions in 5 min) - Possible scraping/exfiltration")
        elif burst_count > 15:
            threat_level = "MEDIUM"
            risk_score += 20
            anomalies.append(f"Moderate activity surge ({burst_count} actions in 5 min)")

        if alert_count >= 5:
            threat_level = "CRITICAL"
            risk_score += 50
            anomalies.append(f"Repeated security violations ({alert_count} alerts in 24h) - Auto containment recommended")
        elif alert_count >= 2:
            if threat_level != "CRITICAL":
                threat_level = "HIGH"
            risk_score += 25
            anomalies.append(f"Multiple security violations ({alert_count} alerts in 24h)")

        risk_score = min(100, risk_score)

        return {
            "username": username,
            "ip_address": client_ip,
            "threat_level": threat_level,
            "risk_score": risk_score,
            "burst_count_5m": burst_count,
            "security_alerts_24h": alert_count,
            "anomalies": anomalies,
            "recommended_action": "BLOCK_IP" if threat_level == "CRITICAL" else "MONITOR_CLOSELY" if threat_level == "HIGH" else "NORMAL"
        }
    finally:
        conn.close()


def get_security_threat_intel(org_id: int = 1) -> dict:
    """Aggregates enterprise-wide threat telemetry for the SOC Security Dashboard."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # Top active threat IPs
        cur.execute("""
            SELECT ip_address, COUNT(*) as cnt 
            FROM audit_logs 
            WHERE action LIKE 'SECURITY_%' AND datetime(timestamp) >= datetime('now', '-24 hours')
            GROUP BY ip_address 
            ORDER BY cnt DESC LIMIT 5
        """)
        threat_ips = [{"ip": r[0], "incidents": r[1]} for r in cur.fetchall()]

        # Top flagged actions
        cur.execute("""
            SELECT action, COUNT(*) as cnt 
            FROM audit_logs 
            WHERE action LIKE 'SECURITY_%' AND datetime(timestamp) >= datetime('now', '-24 hours')
            GROUP BY action 
            ORDER BY cnt DESC LIMIT 5
        """)
        flagged_actions = [{"action": r[0], "count": r[1]} for r in cur.fetchall()]

        return {
            "ok": True,
            "active_threat_ips": threat_ips,
            "top_flagged_actions": flagged_actions,
            "intel_engine_status": "ONLINE (Sentinel v3.4 Active)"
        }
    finally:
        conn.close()








