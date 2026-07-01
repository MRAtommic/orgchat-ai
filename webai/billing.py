"""
OrgChat AI — Billing & Subscription module
Defines plan limits, feature gates, and monthly usage tracking.
"""
import sqlite3
import os
import logging
from datetime import datetime, date
from functools import wraps
from flask import session, jsonify

logger = logging.getLogger("OrgChatAI.Billing")

from pathlib import Path
DB_PATH = Path(os.environ.get("DB_PATH", "chat_history.db"))


def _get_line_token() -> str:
    """Resolve LINE Channel Access Token: config file first, then env fallback."""
    try:
        import json as _json
        _cfg_path = os.path.join(os.path.dirname(__file__), "line_config.json")
        if os.path.exists(_cfg_path):
            with open(_cfg_path, 'r', encoding='utf-8') as f:
                _cfg = _json.load(f)
            tok = (_cfg.get("channel_access_token") or "").strip()
            if tok:
                return tok
    except Exception:
        pass
    return os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()

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
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                org_id      INTEGER NOT NULL,
                year_month  TEXT    NOT NULL,
                expense_count    INTEGER DEFAULT 0,
                ai_query_count   INTEGER DEFAULT 0,
                alert_flags      TEXT    DEFAULT NULL,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (org_id, year_month)
            )
        """)
        try:
            cur.execute("ALTER TABLE usage_tracking ADD COLUMN alert_flags TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            pass # Column likely already exists

        # Migrations: add columns to organizations if not exists
        for _col_sql in [
            "ALTER TABLE organizations ADD COLUMN plan_expires_at DATETIME",
            "ALTER TABLE organizations ADD COLUMN plan_expiry_notified INTEGER DEFAULT 0",
        ]:
            try:
                cur.execute(_col_sql)
            except sqlite3.OperationalError:
                pass # Column likely already exists
            except Exception as e:
                logger.error(f"Migration error ({_col_sql}): {e}")

        conn.commit()
    finally:
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
                # Downgrade DB — check flag ก่อนเพื่อ notify แค่ครั้งเดียว
                try:
                    _sync = _get_conn()
                    _flag = _sync.execute(
                        "SELECT plan_expiry_notified FROM organizations WHERE id=?", (org_id,)
                    ).fetchone()
                    already_notified = bool(_flag and _flag["plan_expiry_notified"])
                    _sync.execute(
                        "UPDATE organizations SET plan='free', plan_expires_at=NULL, plan_expiry_notified=1 WHERE id=?",
                        (org_id,)
                    )
                    _sync.commit()
                    _sync.close()
                    if not already_notified:
                        import threading
                        threading.Thread(
                            target=_send_expiry_notification, args=(org_id,), daemon=True
                        ).start()
                except Exception as e:
                    logger.error(f"Error handling expired plan for org {org_id}: {e}")
                return "free"
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid plan_expires_at format for org {org_id}: {expires}")
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
    if plan != "free" and expires_at:
        # ใช้ MAX เพื่อป้องกัน redirect fallback ทับ expires_at ที่ webhook ตั้งไว้ถูกต้องแล้ว
        # รีเซ็ต plan_expiry_notified เมื่อ upgrade ใหม่ เพื่อให้แจ้งเตือนได้อีกครั้งถ้าหมดอายุ
        conn.execute(
            """UPDATE organizations
               SET plan=?,
                   plan_expires_at=CASE
                       WHEN plan_expires_at IS NULL OR plan_expires_at < ? THEN ?
                       ELSE plan_expires_at
                   END,
                   plan_expiry_notified=0
               WHERE id=?""",
            (plan, expires_at, expires_at, org_id),
        )
    else:
        conn.execute(
            "UPDATE organizations SET plan=?, plan_expires_at=? WHERE id=?",
            (plan, expires_at, org_id),
        )
    conn.commit()
    conn.close()


def _send_expiry_notification(org_id: int) -> None:
    """ส่ง LINE notification ให้ org admin เมื่อ plan หมดอายุ (PromptPay/time-based)."""
    try:
        import requests as _req
        tok = _get_line_token()
        base = os.environ.get("BASE_URL", "https://openchat.sbs")
        if not tok:
            return
        conn = _get_conn()
        org_row = conn.execute("SELECT name FROM organizations WHERE id=?", (org_id,)).fetchone()
        org_name = org_row["name"] if org_row else f"Org #{org_id}"
        admins = conn.execute(
            "SELECT om.username, up.line_user_id FROM organization_members om "
            "LEFT JOIN user_profiles up ON om.username = up.username "
            "WHERE om.organization_id=? AND om.role='admin'",
            (org_id,)
        ).fetchall()
        conn.close()
        msg = (
            f"⚠️ แจ้งเตือนจาก OrgChat AI\n\n"
            f"แพลนขององค์กร '{org_name}' หมดอายุแล้ว\n"
            f"ฟีเจอร์พรีเมียมถูกระงับชั่วคราว\n\n"
            f"กรุณาต่ออายุที่: {base}/billing"
        )
        for row in admins:
            line_uid = row["line_user_id"] if row["line_user_id"] else None
            if not line_uid:
                continue
            try:
                _req.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                    json={"to": line_uid, "messages": [{"type": "text", "text": msg}]},
                    timeout=10,
                )
            except Exception as e:
                logger.error(f"Failed to send expiry notification to {row['username']}: {e}")
    except Exception as e:
        logger.error(f"Error in _send_expiry_notification for org {org_id}: {e}")


def _push_line_to_org_groups(org_id: int, message: str) -> int:
    """ส่ง LINE push message ไปทุก group ของ org. Returns จำนวน group ที่ส่งสำเร็จ."""
    try:
        import requests as _req
        tok = _get_line_token()
        if not tok:
            return 0
        # import database inline เพื่อหลีกเลี่ยง circular import
        import database as _db
        groups = _db.get_line_groups_for_org(org_id)
        sent = 0
        for g in groups:
            gid = g.get("group_id") or g.get("line_group_id")
            if not gid:
                continue
            try:
                resp = _req.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                    json={"to": gid, "messages": [{"type": "text", "text": message}]},
                    timeout=10,
                )
                if resp.status_code == 200:
                    sent += 1
            except Exception as e:
                logger.error(f"Failed to push LINE message to group {gid}: {e}")
        return sent
    except Exception as e:
        logger.error(f"Error in _push_line_to_org_groups for org {org_id}: {e}")
        return 0


def send_usage_alert_if_needed(org_id: int, metric: str, current: int, limit: int) -> None:
    """ส่ง LINE alert เมื่อ usage ถึง 80% หรือ 100% ของ limit (ส่งครั้งเดียวต่อ threshold ต่อเดือน)."""
    if limit <= 0 or org_id is None:
        return
    pct = (current / limit) * 100
    if pct < 80:
        return

    threshold = 100 if pct >= 100 else 80
    ym = _current_ym()
    flag_key = f"usage_alert_{metric}_{threshold}_{ym}"

    conn = _get_conn()
    try:
        # ตรวจว่าส่งแล้วหรือยัง
        row = conn.execute(
            "SELECT 1 FROM usage_tracking WHERE org_id=? AND year_month=?", (org_id, ym)
        ).fetchone()
        # ใช้ updated_at เพื่อเก็บ flag (เพิ่ม column alert_sent แทนการ add table ใหม่)
        # ใช้ JSON blob ใน column สำหรับ flags
        flag_row = conn.execute(
            "SELECT alert_flags FROM usage_tracking WHERE org_id=? AND year_month=?", (org_id, ym)
        ).fetchone()
        flags = {}
        if flag_row and flag_row["alert_flags"]:
            try:
                import json as _json
                flags = _json.loads(flag_row["alert_flags"])
            except Exception:
                flags = {}
        if flags.get(flag_key):
            return  # ส่งแล้ว
        # set flag
        flags[flag_key] = True
        import json as _json
        conn.execute(
            "UPDATE usage_tracking SET alert_flags=? WHERE org_id=? AND year_month=?",
            (_json.dumps(flags), org_id, ym)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error in send_usage_alert_if_needed for org {org_id}: {e}")
    finally:
        conn.close()

    metric_name = {"expense_count": "รายการค่าใช้จ่าย", "ai_query_count": "การถาม AI"}.get(metric, metric)
    if threshold == 100:
        msg = (
            f"🚫 OrgChat AI: โควต้า {metric_name} หมดแล้วค่ะ\n"
            f"ใช้ครบ {current}/{limit} ครั้งสำหรับเดือนนี้แล้ว\n\n"
            f"อัปเกรด Plan เพื่อใช้งานต่อได้ที่:\nhttps://openchat.sbs/pricing"
        )
    else:
        msg = (
            f"⚠️ OrgChat AI: ใกล้ถึงโควต้า {metric_name} แล้วค่ะ\n"
            f"ใช้ไป {current}/{limit} ครั้ง ({threshold}%) สำหรับเดือนนี้\n\n"
            f"อัปเกรด Plan เพื่อใช้งานไม่จำกัดได้ที่:\nhttps://openchat.sbs/pricing"
        )
    import threading
    threading.Thread(target=_push_line_to_org_groups, args=(org_id, msg), daemon=True).start()


def send_monthly_summary_to_org(org_id: int) -> None:
    """ส่งสรุปการใช้งานรายเดือนผ่าน LINE ให้ org."""
    try:
        ym = _current_ym()
        usage = get_usage(org_id)
        plan = get_effective_plan(org_id)
        config = get_plan_config(plan)
        plan_name = config.get("name_th", plan)

        exp_limit = config["limits"]["expenses_per_month"]
        ai_limit  = config["limits"]["ai_queries_per_month"]

        def limit_str(limit):
            return "ไม่จำกัด" if limit == -1 else str(limit)

        msg = (
            f"📊 สรุปการใช้งาน OrgChat AI เดือน {ym}\n"
            f"แพลน: {plan_name}\n\n"
            f"📋 รายการค่าใช้จ่าย: {usage['expense_count']}/{limit_str(exp_limit)} ครั้ง\n"
            f"🤖 ถาม AI: {usage['ai_query_count']}/{limit_str(ai_limit)} ครั้ง\n\n"
            f"ดูรายละเอียดเพิ่มเติม: https://openchat.sbs/billing"
        )
        _push_line_to_org_groups(org_id, msg)
    except Exception as e:
        logger.error(f"Error in send_monthly_summary_to_org for org {org_id}: {e}")


def send_monthly_summary_all_orgs() -> None:
    """ส่งสรุปรายเดือนให้ทุก org ที่มี LINE groups — เรียกจาก scheduler สิ้นเดือน."""
    try:
        conn = _get_conn()
        org_ids = [r["id"] for r in conn.execute(
            "SELECT DISTINCT o.id FROM organizations o "
            "JOIN line_group_mappings lg ON lg.org_id = o.id"
        ).fetchall()]
        conn.close()
        import threading
        for oid in org_ids:
            threading.Thread(target=send_monthly_summary_to_org, args=(oid,), daemon=True).start()
    except Exception as e:
        logger.error(f"Error in send_monthly_summary_all_orgs: {e}")


def get_billing_status(org_id: int) -> dict:
    """Full billing status dict for an org — used by the API and UI."""
    plan_name = get_effective_plan(org_id)
    config = get_plan_config(plan_name)
    usage = get_usage(org_id)

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT plan, plan_expires_at, stripe_subscription_id FROM organizations WHERE id=?", (org_id,)
    )
    row = cur.fetchone()
    conn.close()

    raw_plan = (row["plan"] if row else "free") or "free"
    expires_at = row["plan_expires_at"] if row else None
    sub_id = row["stripe_subscription_id"] if row else None

    # Check Stripe for cancellation status
    cancel_at_period_end = False
    if sub_id:
        try:
            import stripe as _stripe
            _stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
            sub = _stripe.Subscription.retrieve(sub_id)
            cancel_at_period_end = bool(getattr(sub, "cancel_at_period_end", False))
        except Exception:
            pass

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
        "cancel_at_period_end": cancel_at_period_end,
        "has_stripe_subscription": bool(sub_id),
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
            from routes.shared import get_current_org_id
            org_id = get_current_org_id()
            plan = get_effective_plan(org_id) if org_id else "free"
            if not meets_plan(plan, min_plan):
                required_cfg = get_plan_config(min_plan)
                return jsonify({
                    "ok": False,
                    "error": "upgrade_required",
                    "message": f"ฟีเจอร์นี้ต้องการ Plan {required_cfg['name']} ขึ้นไป กรุณาอัปเกรดเพื่อใช้งาน",
                    "required_plan": min_plan,
                    "current_plan": plan,
                    "upgrade_url": "/billing",
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_feature(feature: str):
    """Route decorator: requires a specific feature to be enabled on the org's plan."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from routes.shared import get_current_org_id
            org_id = get_current_org_id()
            if not org_id or not has_feature(org_id, feature):
                plan = get_effective_plan(org_id) if org_id else "free"
                return jsonify({
                    "ok": False,
                    "error": "feature_not_available",
                    "message": f"ฟีเจอร์นี้ไม่รวมอยู่ใน Plan {get_plan_config(plan)['name']} กรุณาอัปเกรด Plan เพื่อใช้งาน",
                    "current_plan": plan,
                    "upgrade_url": "/billing",
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
            new_count = current + 1
            # ส่ง alert ที่ 80% และ 100% แบบ background (ไม่ block response)
            import threading
            threading.Thread(
                target=send_usage_alert_if_needed,
                args=(org_id, metric, new_count, limit),
                daemon=True,
            ).start()
            return True, current, limit
        else:
            cur.execute("COMMIT")
            # ส่ง 100% alert ถ้ายังไม่เคยส่ง
            import threading
            threading.Thread(
                target=send_usage_alert_if_needed,
                args=(org_id, metric, current, limit),
                daemon=True,
            ).start()
            return False, current, limit
    except Exception as e:
        logger.error(f"Fatal error in check_and_increment for org {org_id}: {e}")
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()
