# -*- coding: utf-8 -*-
"""
OrgChat AI — Modular Database Package
Backward-compatible re-exports from all domain modules.
"""

from .connection import *
from .connection import (
    _get_conn, _get_pg_pool, _pg_pool, _pg_pool_initialized, _pg_pool_lock,
    _db_url, _dt, _dt_mod, _j, _json, _re, _t_mod, _time_mod
)
from .schema import *
from .settings import *
from .settings import (
    _line_link_cleanup, _oauth_state_cleanup, _LINE_LINK_TTL, _OAUTH_STATE_TTL
)
from .users import *
from .users import (
    _ensure_reset_table, _ensure_otp_table, _ensure_login_attempts_table,
    _is_system_admin, _QR_TTL, _LOGIN_ATTEMPT_LIMIT, _LOGIN_ATTEMPT_WINDOW
)
from .orgs import *
from .chat import *
from .leave import *
from .finance import *
from .social import *
from .social import _kanban_seed_defaults
from .security import *
from .security import (
    _INJECTION_PATTERNS, _THAI_NATIONAL_ID_PATTERN, _CREDIT_CARD_PATTERN,
    _THAI_PHONE_PATTERN, _EMAIL_PATTERN
)
from .billing import *
from .migrations import run_migrations, get_migration_history, MIGRATIONS
