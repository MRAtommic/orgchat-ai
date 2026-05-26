import sqlite3
import json
import time
import threading
import logging
import uuid
from functools import wraps
from pathlib import Path

DB_PATH = Path("chat_history.db")
logger = logging.getLogger(__name__)

def _get_conn():
    import database
    return database._get_conn()

def init_task_table():
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_tasks (
                id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                args TEXT,
                status TEXT DEFAULT 'pending', -- pending, running, success, failed
                error_message TEXT,
                org_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

# Initialize on import
try:
    init_task_table()
except Exception as e:
    logger.error(f"Error initializing db_tasks table: {e}")


def track_task_start(task_id, task_name, args_dict, org_id):
    try:
        conn = _get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO db_tasks (id, task_name, args, status, org_id, created_at, updated_at)
                VALUES (?, ?, ?, 'running', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (task_id, task_name, json.dumps(args_dict), org_id))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to track task start: {e}")

def track_task_success(task_id):
    try:
        conn = _get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE db_tasks
                SET status = 'success', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (task_id,))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to track task success: {e}")

def track_task_failure(task_id, error_msg):
    try:
        conn = _get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE db_tasks
                SET status = 'failed', error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (str(error_msg), task_id))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to track task failure: {e}")

def get_failed_tasks(org_id):
    try:
        conn = _get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, task_name, args, error_message, created_at
                FROM db_tasks
                WHERE status = 'failed' AND org_id = ?
                ORDER BY created_at DESC
            """, (org_id,))
            rows = cursor.fetchall()
            return [{"id": r[0], "task_name": r[1], "args": json.loads(r[2]), "error": r[3], "created_at": r[4]} for r in rows]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to get failed tasks: {e}")
        return []

def db_task_tracker(task_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve org_id dynamically based on typical target arguments
            org_id = kwargs.get('org_id')
            if not org_id:
                # If it's process_pending_uploads(b_key, did, folder_id, folder_name, reply_tok)
                # We can extract did and query it from DB, or extract org_id if passed
                if task_name == "process_pending_uploads" and len(args) > 1:
                    try:
                        import database
                        did = args[1]
                        org_id = database.get_org_id_by_line_group(did) if (did.startswith("C") or did.startswith("R")) else database.get_org_id_by_line_user(did)
                    except Exception:
                        pass
                elif len(args) > 4:
                    org_id = args[4]
                elif len(args) > 3:
                    org_id = args[3]
            
            task_id = str(uuid.uuid4())
            args_serialized = {
                "args": [str(a) for a in args],
                "kwargs": {k: str(v) for k, v in kwargs.items()}
            }
            
            track_task_start(task_id, task_name, args_serialized, org_id)
            try:
                result = func(*args, **kwargs)
                track_task_success(task_id)
                return result
            except Exception as e:
                track_task_failure(task_id, e)
                raise e
        return wrapper
    return decorator
