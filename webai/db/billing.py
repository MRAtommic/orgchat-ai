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



