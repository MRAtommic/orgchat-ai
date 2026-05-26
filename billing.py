"""
OrgChat AI — Billing & Subscription module
Defines plan limits, feature gates, and monthly usage tracking.
"""
import sqlite3
import os
from datetime import datetime, date
from functools import wraps
from flask import session, jsonify

from pathlib import Path
DB_PATH = Path(os.environ.get("DB_PATH", "chat_history.db"))

# ─── Plan Configuration ───────────────────────────────────────────────────────

PLAN_HIERARCHY = ["free", "pro", "business"]

PLANS = {
    "free": {
        "name": "Free",
        "name_th": "ฟรี",
        "price_thb": 0,
        "limits": {
            "expenses_per_month": 10,
            "ai_queries_per_month": 35,
            "kb_files": 5,
            "max_users": 1,
        },
        "features": {
            "google_sheets": False,
            "financial_dashboard": False,
            "line_bot": False,
            "export": False,
            "priority_support": False,
        },
    },
    "pro": {
        "name": "Pro",
        "name_th": "โปร",
        "price_thb": 299,
        "limits": {
            "expenses_per_month": -1,       # -1 = unlimited
            "ai_queries_per_month": -1,
            "kb_files": 100,
            "max_users": 3,
        },
        "features": {
            "google_sheets": True,
            "financial_dashboard": True,
            "line_bot": True,
            "export": False,
            "priority_support": False,
        },
    },
    "business": {
        "name": "Ultra",
        "name_th": "อัลตร้า",
        "price_thb": 599,
        "limits": {
            "expenses_per_month": -1,
            "ai_queries_per_month": -1,
            "kb_files": -1,
            "max_users": 10,
        },
        "features": {
            "google_sheets": True,
            "financial_dashboard": True,
            "line_bot": True,
            "export": True,
            "priority_support": True,
        },
    },
}


# ─── DB helpers ──────────────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_billing_tables():
    """Run once at startup to ensure billing tables exist."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usage_tracking (
            org_id      INTEGER NOT NULL,
            year_month  TEXT    NOT NULL,
            expense_count    INTEGER DEFAULT 0,
            ai_query_count   INTEGER DEFAULT 0,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (org_id, year_month)
        )
    """)

    # Migration: add plan_expires_at to organizations if not exists
    try:
        cur.execute("ALTER TABLE organizations ADD COLUMN plan_expires_at DATETIME")
    except Exception:
        pass

    conn.commit()
    conn.close()


# ─── Plan resolution ─────────────────────────────────────────────────────────

def get_effective_plan(org_id: int) -> str:
    """
    Returns the active plan name for an org.
    Falls back to 'free' if plan_expires_at has passed.
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT plan, plan_expires_at FROM organizations WHERE id = ?", (org_id,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return "free"

    plan = row["plan"] or "free"
    if plan == "free":
        return "free"

    expires = row["plan_expires_at"]
    if expires:
        try:
            from datetime import timezone
            exp_dt = datetime.fromisoformat(expires)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if exp_dt < datetime.now(timezone.utc):
                return "free"
        except Exception:
            pass

    return plan if plan in PLANS else "free"


def get_plan_config(plan_name: str) -> dict:
    return PLANS.get(plan_name, PLANS["free"])


def plan_rank(plan_name: str) -> int:
    try:
        return PLAN_HIERARCHY.index(plan_name)
    except ValueError:
        return 0


def meets_plan(org_plan: str, required_plan: str) -> bool:
    return plan_rank(org_plan) >= plan_rank(required_plan)


# ─── Usage tracking ──────────────────────────────────────────────────────────

def _current_ym() -> str:
    return date.today().strftime("%Y-%m")


def get_usage(org_id: int, year_month: str = None) -> dict:
    ym = year_month or _current_ym()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT expense_count, ai_query_count FROM usage_tracking WHERE org_id=? AND year_month=?",
        (org_id, ym),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"expense_count": row["expense_count"], "ai_query_count": row["ai_query_count"]}
    return {"expense_count": 0, "ai_query_count": 0}


def increment_usage(org_id: int, metric: str) -> int:
    """
    Increments a usage counter for the current month.
    metric: 'expense_count' or 'ai_query_count'
    Returns the new count.
    """
    if metric not in _ALLOWED_METRICS:
        raise ValueError(f"Invalid metric: {metric!r}")
    ym = _current_ym()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usage_tracking (org_id, year_month, {col})
        VALUES (?, ?, 1)
        ON CONFLICT(org_id, year_month) DO UPDATE SET
            {col} = {col} + 1,
            updated_at = CURRENT_TIMESTAMP
    """.format(col=metric), (org_id, ym))
    conn.commit()
    cur.execute(
        f"SELECT {metric} FROM usage_tracking WHERE org_id=? AND year_month=?",
        (org_id, ym),
    )
    new_count = (cur.fetchone() or {metric: 0})[metric]
    conn.close()
    return new_count


_METRIC_TO_LIMIT_KEY = {
    "expense_count":  "expenses_per_month",
    "ai_query_count": "ai_queries_per_month",
}

# Allowlist — only these column names may be passed to increment_usage
_ALLOWED_METRICS = frozenset(_METRIC_TO_LIMIT_KEY.keys())


def check_usage_allowed(org_id: int, metric: str) -> tuple[bool, int, int]:
    """
    Returns (allowed, current_count, limit).
    limit = -1 means unlimited.
    metric: DB column name ('expense_count' or 'ai_query_count')
    """
    plan = get_effective_plan(org_id)
    config = get_plan_config(plan)
    limit_key = _METRIC_TO_LIMIT_KEY.get(metric, metric)
    limit = config["limits"].get(limit_key, 0)
    usage = get_usage(org_id)
    current = usage.get(metric, 0)

    if limit == -1:
        return True, current, -1
    return current < limit, current, limit


def has_feature(org_id: int, feature: str) -> bool:
    plan = get_effective_plan(org_id)
    config = get_plan_config(plan)
    return config["features"].get(feature, False)


# ─── Admin helpers ───────────────────────────────────────────────────────────

def set_org_plan(org_id: int, plan: str, expires_at: str = None):
    """Set org plan. expires_at is an ISO datetime string or None (= forever)."""
    if plan not in PLANS:
        raise ValueError(f"Unknown plan: {plan}")
    conn = _get_conn()
    conn.execute(
        "UPDATE organizations SET plan=?, plan_expires_at=? WHERE id=?",
        (plan, expires_at, org_id),
    )
    conn.commit()
    conn.close()


def get_billing_status(org_id: int) -> dict:
    """Full billing status dict for an org — used by the API and UI."""
    plan_name = get_effective_plan(org_id)
    config = get_plan_config(plan_name)
    usage = get_usage(org_id)

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT plan, plan_expires_at FROM organizations WHERE id=?", (org_id,)
    )
    row = cur.fetchone()
    conn.close()

    raw_plan = (row["plan"] if row else "free") or "free"
    expires_at = row["plan_expires_at"] if row else None

    limits = config["limits"]
    features = config["features"]

    def pct(used, limit):
        if limit <= 0:
            return 0
        return round((used / limit) * 100)

    return {
        "plan": plan_name,
        "plan_name_th": config["name_th"],
        "price_thb": config["price_thb"],
        "plan_expires_at": expires_at,
        "is_expired": raw_plan != "free" and plan_name == "free",
        "usage": {
            "expenses": {
                "used": usage["expense_count"],
                "limit": limits["expenses_per_month"],
                "pct": pct(usage["expense_count"], limits["expenses_per_month"]),
            },
            "ai_queries": {
                "used": usage["ai_query_count"],
                "limit": limits["ai_queries_per_month"],
                "pct": pct(usage["ai_query_count"], limits["ai_queries_per_month"]),
            },
            "max_users": limits["max_users"],
            "kb_files": limits["kb_files"],
        },
        "features": features,
    }


# ─── Flask decorators ────────────────────────────────────────────────────────

def require_plan(min_plan: str):
    """Route decorator: requires the org to be on min_plan or higher."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            org_id = session.get("org_id", 1)
            plan = get_effective_plan(org_id)
            if not meets_plan(plan, min_plan):
                required_cfg = get_plan_config(min_plan)
                return jsonify({
                    "ok": False,
                    "error": "upgrade_required",
                    "message": f"ฟีเจอร์นี้ต้องการ Plan {required_cfg['name']} ขึ้นไป",
                    "required_plan": min_plan,
                    "current_plan": plan,
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_feature(feature: str):
    """Route decorator: requires a specific feature to be enabled on the org's plan."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            org_id = session.get("org_id", 1)
            if not has_feature(org_id, feature):
                plan = get_effective_plan(org_id)
                return jsonify({
                    "ok": False,
                    "error": "feature_not_available",
                    "message": f"ฟีเจอร์ '{feature}' ไม่รวมอยู่ใน Plan {get_plan_config(plan)['name']}",
                    "current_plan": plan,
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def check_and_increment(org_id: int, metric: str) -> tuple:
    """
    Atomically checks limit then increments. Returns (allowed, current, limit).
    Uses BEGIN IMMEDIATE to prevent double-spend race conditions.
    """
    if metric not in _ALLOWED_METRICS:
        raise ValueError(f"Invalid metric: {metric!r}")

    plan = get_effective_plan(org_id)
    config = get_plan_config(plan)
    limit_key = _METRIC_TO_LIMIT_KEY[metric]
    limit = config["limits"].get(limit_key, 0)

    if limit == -1:  # unlimited plan — skip atomic check
        new_count = increment_usage(org_id, metric)
        return True, new_count - 1, -1

    ym = _current_ym()
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            f"SELECT {metric} FROM usage_tracking WHERE org_id=? AND year_month=?",
            (org_id, ym),
        )
        row = cur.fetchone()
        current = row[metric] if row else 0

        if current < limit:
            cur.execute(
                """INSERT INTO usage_tracking (org_id, year_month, {col})
                   VALUES (?, ?, 1)
                   ON CONFLICT(org_id, year_month) DO UPDATE SET
                       {col} = {col} + 1,
                       updated_at = CURRENT_TIMESTAMP
                """.format(col=metric),
                (org_id, ym),
            )
            cur.execute("COMMIT")
            return True, current, limit
        else:
            cur.execute("COMMIT")
            return False, current, limit
    except Exception:
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()
