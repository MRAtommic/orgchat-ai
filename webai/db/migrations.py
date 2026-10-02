# -*- coding: utf-8 -*-
"""
webai/db/migrations.py — Simple Database Migration System
Tracks applied schema migrations in the `_migrations` table and applies
new incremental migrations automatically during database initialization.
"""

import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger("OrgChatAI.DB.Migrations")

# ══════════════════════════════════════════════════════════════════════
# Schema Migrations Registry
# Each migration is a tuple of:
# (version_id: str, description: str, sql_statements: list[str])
# ══════════════════════════════════════════════════════════════════════
MIGRATIONS = [
    (
        "001_initial_tracking",
        "Create _migrations tracking table",
        [
            """
            CREATE TABLE IF NOT EXISTS _migrations (
                version TEXT PRIMARY KEY,
                description TEXT,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    ),
    (
        "002_composite_indexes",
        "Add performance composite indexes for high-volume messaging and audit queries",
        [
            "CREATE INDEX IF NOT EXISTS idx_messages_org_user ON messages(organization_id, username, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_room_msg_time ON room_messages(room_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_org_ts ON audit_logs(org_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_expense_user_status ON expense_claims(username, status)",
        ]
    ),
    (
        "003_leave_requests_indexes",
        "Add indexing on leave requests for fast approval queries",
        [
            "CREATE INDEX IF NOT EXISTS idx_leave_org_user ON leave_requests(org_id, username)",
            "CREATE INDEX IF NOT EXISTS idx_leave_org_status ON leave_requests(org_id, status)",
        ]
    ),
    (
        "004_security_events_indexes",
        "Add indexing on security events and threat logs",
        [
            "CREATE INDEX IF NOT EXISTS idx_audit_user_action ON audit_logs(username, action)",
            "CREATE INDEX IF NOT EXISTS idx_blacklist_ip ON ip_blacklist(ip_address)",
        ]
    ),
]


def run_migrations(conn=None) -> list[str]:
    """
    Executes all pending migrations against the database.
    Returns the list of newly applied version IDs.
    """
    if conn is None:
        from .connection import _get_conn
        conn = _get_conn()

    cur = conn.cursor()

    # Step 1: Ensure _migrations table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Step 2: Fetch already applied versions
    cur.execute("SELECT version FROM _migrations")
    applied_versions = {row[0] for row in cur.fetchall()}

    newly_applied = []
    for version, description, stmts in MIGRATIONS:
        if version in applied_versions:
            continue

        logger.info(f"🔄 Applying migration: {version} — {description}...")
        try:
            for sql in stmts:
                sql_clean = sql.strip()
                if sql_clean:
                    cur.execute(sql_clean)

            cur.execute(
                "INSERT INTO _migrations (version, description, applied_at) VALUES (?, ?, ?)",
                (version, description, datetime.now().isoformat())
            )
            conn.commit()
            newly_applied.append(version)
            logger.info(f"✅ Migration applied: {version}")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Migration failed: {version} — {e}")
            raise

    if newly_applied:
        logger.info(f"🎉 Applied {len(newly_applied)} pending database migrations.")
    else:
        logger.debug("Database schema is fully up-to-date (0 pending migrations).")

    return newly_applied


def get_migration_history(conn=None) -> list[dict]:
    """Returns a list of all migrations applied to the database."""
    if conn is None:
        from .connection import _get_conn
        conn = _get_conn()

    cur = conn.cursor()
    try:
        cur.execute("SELECT version, description, applied_at FROM _migrations ORDER BY applied_at ASC")
        rows = cur.fetchall()
        return [
            {"version": r[0], "description": r[1], "applied_at": r[2]}
            for r in rows
        ]
    except Exception:
        return []
