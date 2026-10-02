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
import re
import random
import time
import threading
import logging
import secrets
import uuid
import hmac
import hashlib
import weakref
from pathlib import Path
from datetime import datetime, date, timedelta
from functools import wraps
from dotenv import load_dotenv

# Backward-compatible aliases used across the codebase
_j = json
_json = json
_re = re
_dt = datetime
_dt_mod = datetime
_time_mod = time
_t_mod = time

logger = logging.getLogger("OrgChatAI.Database")
load_dotenv(encoding="utf-8")

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
    _base_dir = Path(__file__).parent.absolute()
    if _base_dir.name == "db":
        _base_dir = _base_dir.parent
    DB_PATH = _base_dir / DB_PATH



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




