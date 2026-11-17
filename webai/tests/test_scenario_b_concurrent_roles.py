# -*- coding: utf-8 -*-
"""
Scenario B: สถานการณ์ผู้ใช้ 3 บทบาทใช้พร้อมกัน
(admin อัปโหลด, member ถาม, owner เปลี่ยนสิทธิ์หมวดหมู่ ระหว่างนั้น ตรวจว่าสิทธิ์มีผลทันทีและไม่เห็นไฟล์ที่ไม่มีสิทธิ์)
"""
import io
import json
import os
import secrets
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

WEBAI = Path(__file__).resolve().parent.parent


@pytest.fixture
def concurrent_roles_env():
    tmpdir = tempfile.TemporaryDirectory()
    tmp_path = Path(tmpdir.name)
    db_file = tmp_path / "scenario_b.db"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    old_env = os.environ.copy()
    os.environ["DB_PATH"] = str(db_file)
    os.environ["DATA_DIR"] = str(data_dir)
    os.environ["VECTOR_BACKEND"] = "python"
    os.environ["FLASK_SECRET_KEY"] = secrets.token_hex(16)
    os.environ["BASE_URL"] = "http://localhost:5999"

    import app_server
    import database
    import rag_engine
    from db import org_features

    rag_engine.UPLOAD_DIR = uploads_dir
    rag_engine.META_FILE = data_dir / "file_meta.json"
    rag_engine.DOCS_FILE = data_dir / "processed_docs.json"

    app = app_server.app
    app.config["TESTING"] = True

    pw = "P@ssword123!"

    # 1. Create Organization & 3 Roles
    database.admin_create_user("owner_b", pw, role="user", email="owner@b.com")
    org_id, _ = database.create_organization("Concurrent Corp", "owner_b")

    database.admin_create_user("admin_b", pw, role="admin", email="admin@b.com")
    database.add_org_member(org_id, "admin_b", "admin", "owner_b")
    database.update_user_profile("admin_b", department="Finance")

    database.admin_create_user("member_b", pw, role="user", email="member@b.com")
    database.add_org_member(org_id, "member_b", "member", "owner_b")
    database.update_user_profile("member_b", department="Sales")
    conn = database._get_conn()
    conn.execute("UPDATE user_settings SET can_view_kb=1, can_edit_kb=1 WHERE username IN ('owner_b', 'admin_b', 'member_b')")
    conn.commit()
    conn.close()

    # Categories
    cat_fin = database.add_category("แผนกการเงิน", "ข้อมูลลับทางการเงิน", "owner_b", "confidential", org_id)
    org_features.set_category_departments(cat_fin, ["Finance"])

    cat_gen = database.add_category("ทั่วไป", "ข้อมูลทั่วไปสำหรับทุกคน", "owner_b", "public", org_id)

    ctx = {
        "app": app,
        "database": database,
        "rag_engine": rag_engine,
        "org_features": org_features,
        "org_id": org_id,
        "cat_fin": cat_fin,
        "cat_gen": cat_gen,
        "uploads_dir": uploads_dir,
        "pw": pw,
    }

    yield ctx

    os.environ.clear()
    os.environ.update(old_env)
    tmpdir.cleanup()


def _login(app, username, password):
    cl = app.test_client()
    res = cl.post("/api/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.get_json()}"
    csrf = cl.get("/api/csrf-token").get_json()["csrf_token"]
    return cl, csrf


def test_scenario_b_concurrent_roles_permissions(concurrent_roles_env):
    ctx = concurrent_roles_env
    app = ctx["app"]
    rag_engine = ctx["rag_engine"]
    org_id = ctx["org_id"]
    cat_fin = ctx["cat_fin"]
    cat_gen = ctx["cat_gen"]
    uploads_dir = ctx["uploads_dir"]

    client_owner, csrf_owner = _login(app, "owner_b", ctx["pw"])
    client_admin, csrf_admin = _login(app, "admin_b", ctx["pw"])
    client_member, csrf_member = _login(app, "member_b", ctx["pw"])

    # 1. Admin uploads 2 files
    fin_file = uploads_dir / "งบการเงิน_Q4.txt"
    fin_file.write_text("งบการเงินไตรมาส 4 กำไรสุทธิ 150 ล้านบาท แผนการลงทุนลับ", encoding="utf-8")
    rag_engine.ingest_file(fin_file, original_name="งบการเงิน_Q4.txt", department="Finance", category_id=cat_fin, org_id=org_id)

    gen_file = uploads_dir / "คู่มือการทำงานทั่วไป.txt"
    gen_file.write_text("เวลาทำงานปกติ 09:00 - 18:00 น. วันหยุดประจำปี 15 วัน", encoding="utf-8")
    rag_engine.ingest_file(gen_file, original_name="คู่มือการทำงานทั่วไป.txt", department="General", category_id=cat_gen, org_id=org_id)

    # 2. Member queries
    # Member belongs to Sales department -> should ONLY see General file in list_files
    res_member_files = client_member.get("/api/files", headers={"X-CSRF-Token": csrf_member})
    assert res_member_files.status_code == 200
    files = res_member_files.get_json().get("files", [])
    file_names = [f["name"] for f in files]
    assert "คู่มือการทำงานทั่วไป.txt" in file_names, "Member must see public files"
    assert "งบการเงิน_Q4.txt" not in file_names, "Member must NOT see restricted Finance files"

    # Admin and Owner should see both files
    res_admin_files = client_admin.get("/api/files", headers={"X-CSRF-Token": csrf_admin})
    admin_file_names = [f["name"] for f in res_admin_files.get_json().get("files", [])]
    assert "งบการเงิน_Q4.txt" in admin_file_names
    assert "คู่มือการทำงานทั่วไป.txt" in admin_file_names

    # 3. Member searches RAG
    # Retrieval filter for member should exclude finance file
    from routes.shared import get_rag_filter
    member_filter = get_rag_filter(org_id=org_id, username="member_b")
    member_results = rag_engine.query("งบการเงิน ไตรมาส 4", n_results=5, where=member_filter)
    matched_files = [c.get("source") or c.get("source_name") or c.get("metadata", {}).get("source_name") for c in member_results]
    assert "งบการเงิน_Q4.txt" not in matched_files, "Restricted chunks must NOT leak to member"

    # 4. Owner grants access: adds 'Sales' to Category 'แผนกการเงิน'
    res_grant = client_owner.post(
        f"/api/org/access/categories/{cat_fin}/departments",
        json={"departments": ["Finance", "Sales"]},
        headers={"X-CSRF-Token": csrf_owner}
    )
    assert res_grant.status_code == 200

    # 5. Immediate Effect Check: Member should IMMEDIATELY see the file without server restart
    res_member_files2 = client_member.get("/api/files", headers={"X-CSRF-Token": csrf_member})
    file_names2 = [f["name"] for f in res_member_files2.get_json().get("files", [])]
    assert "งบการเงิน_Q4.txt" in file_names2, "Permission change must take immediate effect"

    member_filter2 = get_rag_filter(org_id=org_id, username="member_b")
    member_results2 = rag_engine.query("งบการเงิน ไตรมาส 4", n_results=5, where=member_filter2)
    matched_files2 = [c.get("source") or c.get("source_name") or c.get("metadata", {}).get("source_name") for c in member_results2]
    assert "งบการเงิน_Q4.txt" in matched_files2, "Member must now retrieve the authorized file"

    # 6. Immediate Revocation Check: Owner removes 'Sales'
    res_revoke = client_owner.post(
        f"/api/org/access/categories/{cat_fin}/departments",
        json={"departments": ["Finance"]},
        headers={"X-CSRF-Token": csrf_owner}
    )
    assert res_revoke.status_code == 200

    member_filter3 = get_rag_filter(org_id=org_id, username="member_b")
    member_results3 = rag_engine.query("งบการเงิน ไตรมาส 4", n_results=5, where=member_filter3)
    matched_files3 = [c.get("source") or c.get("source_name") or c.get("metadata", {}).get("source_name") for c in member_results3]
    assert "งบการเงิน_Q4.txt" not in matched_files3, "Revocation must take immediate effect"
