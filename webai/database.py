# -*- coding: utf-8 -*-
"""
database.py — Backward-compatible Facade for OrgChat AI Database Layer
All database functions are now modularized into the `webai/db/` package:
  - db.connection: Connection pool, DB_PATH, dynamic wrappers, password hashing
  - db.schema: Database initialization, schema creation, migrations
  - db.users: User authentication, profiles, permissions, lockouts, tokens
  - db.orgs: Organizations, memberships, departments, quotas, invites
  - db.chat: Messaging, chat history, rooms, DMs, read receipts, polls
  - db.leave: Leave requests, approvals, quotas, attendance tracking
  - db.finance: Drive logs, offline queue, expenses, quotations, CRM
  - db.social: Social feed, posts, comments, wiki, kanban, meeting notes
  - db.security: Audit logs, threat detection, PII masking, IP blocking
  - db.settings: Global app settings, user settings, LINE & Google configs
  - db.billing: Stripe webhook processing & quota checks

This file re-exports everything from `db` so that all existing code remains 100% functional.
"""

from db import *
from db import (
    _get_conn, _get_pg_pool, _pg_pool, _pg_pool_initialized, _pg_pool_lock,
    _db_url, _dt, _dt_mod, _j, _json, _re, _t_mod, _time_mod,
    _ensure_reset_table, _ensure_otp_table, _ensure_login_attempts_table,
    _is_system_admin, _QR_TTL, _LOGIN_ATTEMPT_LIMIT, _LOGIN_ATTEMPT_WINDOW,
    _kanban_seed_defaults, _line_link_cleanup, _oauth_state_cleanup,
    _LINE_LINK_TTL, _OAUTH_STATE_TTL,
    _INJECTION_PATTERNS, _THAI_NATIONAL_ID_PATTERN, _CREDIT_CARD_PATTERN,
    _THAI_PHONE_PATTERN, _EMAIL_PATTERN
)
