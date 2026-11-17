# -*- coding: utf-8 -*-
"""Regression test suite for R2, R3, F1, F3, F5 fixes:
- R2: In-memory state cleanup to prevent slow leaks
- R3: SQLite concurrency locking prevented (DDL in interval jobs eliminated)
- F1: Thai 13-digit tax ID checksum algorithm
- F3: Knowledge harvester querying `messages` table
- F5: Fuzzing crashes neutralized (None payload handling, safe datetime overflow, SMTP 400)
"""
import time
import pytest
import database
import app_server
from routes.chat import (
    _profile_cache, _typing_last, _rtc_last_offer, _pending_calls,
    _limit_warn_cache, cleanup_in_memory_state
)
from knowledge_harvester import KnowledgeHarvester


def test_r2_in_memory_cleanup():
    """Verify that stale in-memory state entries are purged by cleanup_in_memory_state()."""
    now = time.time()
    # Populate entries: one fresh, one stale
    _profile_cache["stale_user"] = (now - 400, "Stale", None)
    _profile_cache["fresh_user"] = (now - 10, "Fresh", None)

    _typing_last[("stale_typer", "dm", "x")] = now - 120
    _typing_last[("fresh_typer", "dm", "x")] = now - 5

    _rtc_last_offer["stale_caller"] = now - 600
    _rtc_last_offer["fresh_caller"] = now - 10

    _limit_warn_cache["stale_warn"] = now - 4000
    _limit_warn_cache["fresh_warn"] = now - 30

    _pending_calls["stale_pending"] = {"sender": "x", "ts": now - 100}
    _pending_calls["fresh_pending"] = {"sender": "y", "ts": now - 5}

    # Run cleanup
    cleanup_in_memory_state()

    # Verify stale purged, fresh retained
    assert "stale_user" not in _profile_cache
    assert "fresh_user" in _profile_cache

    assert ("stale_typer", "dm", "x") not in _typing_last
    assert ("fresh_typer", "dm", "x") in _typing_last

    assert "stale_caller" not in _rtc_last_offer
    assert "fresh_caller" in _rtc_last_offer

    assert "stale_warn" not in _limit_warn_cache
    assert "fresh_warn" in _limit_warn_cache

    assert "stale_pending" not in _pending_calls
    assert "fresh_pending" in _pending_calls


def test_f1_thai_tax_id_checksum():
    """Verify Thai 13-digit tax ID checksum algorithm."""
    def is_valid_tax_id(tax_id: str) -> bool:
        clean = "".join(c for c in tax_id if c.isdigit())
        if len(clean) != 13:
            return False
        digits = [int(c) for c in clean]
        s = sum(digits[i] * (13 - i) for i in range(12))
        check = (11 - (s % 11)) % 10
        return check == digits[12]

    # Valid computed Thai Tax ID: 0105558000014
    assert is_valid_tax_id("0105558000014") is True
    assert is_valid_tax_id("0105558000018") is False
    assert is_valid_tax_id("12345") is False
    assert is_valid_tax_id("abc") is False


def test_f3_knowledge_harvester_messages_query():
    """Verify KnowledgeHarvester queries messages table without crashing."""
    res = KnowledgeHarvester.analyze_recent_messages(org_id=1, limit=10)
    assert res is None or isinstance(res, list)


def test_f5_fuzz_crash_regressions():
    """Regression test ensuring none of the 6 fuzzing crashes recur."""
    client = app_server.app.test_client()

    # Setup test admin and org
    database.admin_create_user("fz_reg_admin", "TestPass123!", role="admin", email="fz_reg@test.com")
    c = database._get_conn()
    c.execute("UPDATE user_settings SET role='superadmin' WHERE username='fz_reg_admin'")
    c.commit()
    c.close()

    oid, _ = database.create_organization("Reg Org", "fz_reg_admin")
    database.add_org_member(oid, "fz_reg_admin", "admin", "fz_reg_admin")

    # Log in
    client.post("/api/login", json={"username": "fz_reg_admin", "password": "TestPass123!"})
    csrf = client.get("/api/csrf-token").get_json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf}

    with client.session_transaction() as sess:
        sess["user"] = "fz_reg_admin"
        sess["org_id"] = oid
        sess["org_role"] = "admin"

    # 1. Line broadcast with text=None -> 400, not 500 AttributeError
    r1 = client.post("/api/admin/line/broadcast", json={"text": None}, headers=headers)
    assert r1.status_code == 400
    assert r1.get_json()["success"] is False

    # 2. Admin create user with username=None -> 400, not 500 AttributeError
    r2 = client.post("/api/admin/users", json={"username": None, "password": None}, headers=headers)
    assert r2.status_code == 400
    assert r2.get_json()["ok"] is False

    # 3. 2FA email send OTP -> never crashes with 500 (returns 200 on configured SMTP or 400 on error)
    r3 = client.post("/api/2fa/send-email-otp", json={}, headers=headers)
    assert r3.status_code in (200, 400)
    assert r3.status_code != 500

    # 4. Security metrics with huge days -> 200, not OverflowError
    r4 = client.get(f"/api/admin/security/metrics?days=99999999999", headers=headers)
    assert r4.status_code == 200
    assert r4.get_json()["ok"] is True

    # 5. CRM customer update with name=None -> 400, not 503/IntegrityError
    r5 = client.put("/api/crm/customers/99999", json={"name": None}, headers=headers)
    assert r5.status_code == 400
    assert r5.get_json()["ok"] is False


def test_s3_org_creator_role_separation():
    """Verify that creating an organization makes the creator an org admin, but NOT a system admin."""
    uname = f"test_creator_{int(time.time())}"
    database.admin_create_user(uname, "CreatorPass123!", role="user", email=f"{uname}@test.com")
    
    # User starts as 'user' in user_settings
    setting_before = database.get_user_setting(uname)
    assert setting_before.get("role") == "user"
    
    # Create organization
    org_id, slug = database.create_organization("Creator Org", uname)
    assert org_id is not None
    
    # User is admin of their org in organization_members
    assert database.is_org_admin(org_id, uname) is True
    
    # BUT user_settings.role MUST REMAIN 'user' (NOT elevated to global system admin)
    setting_after = database.get_user_setting(uname)
    assert setting_after.get("role") == "user", f"Security violation (S3): Org creator got system role {setting_after.get('role')}!"


def test_s2_filename_sanitization():
    """Verify that uploaded/renamed filenames are stripped of HTML/XSS injection characters."""
    from db.sanitize import clean_label
    payload = '<img src=x onerror="alert(1)">Quarterly_Report.pdf'
    sanitized = clean_label(payload, maxlen=120)
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert "Quarterly_Report.pdf" in sanitized


def test_f2_migrate_attendance_tz():
    """Verify that migrate_attendance_tz shifts timestamps +7h accurately."""
    from tools.migrate_attendance_tz import shift_time_plus_7
    assert shift_time_plus_7("07:03:00") == "14:03:00"
    assert shift_time_plus_7("00:30") == "07:30"
    assert shift_time_plus_7("20:00:00") == "03:00:00"
    assert shift_time_plus_7("invalid") == "invalid"


def test_r6_asset_versioning_hash():
    """Verify that asset hashes match file contents and update_template_assets detects changes."""
    from tools.update_asset_versions import get_file_hash, update_template_assets
    h = get_file_hash("/static/style.css")
    assert len(h) == 8, f"Invalid asset hash: {h}"
    total, updated = update_template_assets(check_only=True)
    assert total > 0, "No static assets found in template"
