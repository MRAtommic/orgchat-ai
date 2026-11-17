# -*- coding: utf-8 -*-
"""
Scenario E: สถานการณ์ restart ขณะอัปโหลดค้าง
- อัปโหลดค้างตอนปิดเซิร์ฟเวอร์ แล้วเปิดใหม่
- สถานะต้องไม่ค้าง INDEXING / processing
- Vector store กับ meta ต้องสอดคล้องกัน (จำนวน chunk เท่ากัน)
- ไฟล์ที่พร้อมใช้งานเดิมยังค้นหาได้ปกติ และผู้ใช้สามารถอัปโหลดไฟล์ที่เคยล้มเหลวซ้ำจนสำเร็จได้
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
def restart_recovery_env():
    tmpdir = tempfile.TemporaryDirectory()
    tmp_path = Path(tmpdir.name)
    db_file = tmp_path / "scenario_e.db"
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

    rag_engine.UPLOAD_DIR = uploads_dir
    rag_engine.META_FILE = data_dir / "file_meta.json"
    rag_engine.DOCS_FILE = data_dir / "processed_docs.json"

    # Reset in-memory / file vector store
    kb = rag_engine._get_kb()
    if hasattr(kb.collection, "data"):
        kb.collection.data = []
        kb.collection.save()
    with rag_engine._META_LOCK:
        rag_engine._save_meta({})

    app = app_server.app
    app.config["TESTING"] = True

    pw = "P@ssword123!"
    database.admin_create_user("admin_e", pw, role="admin", email="admin@e.com")
    org_id, _ = database.create_organization("Restart Corp", "admin_e")

    ctx = {
        "app": app,
        "database": database,
        "rag_engine": rag_engine,
        "org_id": org_id,
        "uploads_dir": uploads_dir,
        "data_dir": data_dir,
        "pw": pw,
    }

    yield ctx

    os.environ.clear()
    os.environ.update(old_env)
    tmpdir.cleanup()


def test_scenario_e_restart_recovery_and_chunk_consistency(restart_recovery_env):
    ctx = restart_recovery_env
    rag_engine = ctx["rag_engine"]
    uploads_dir = ctx["uploads_dir"]
    org_id = ctx["org_id"]

    # 1. Ingest a healthy file
    healthy_file = uploads_dir / "นโยบายบริษัท.txt"
    healthy_file.write_text("นโยบายบริษัท รีสตาร์ท คอร์ปอเรชั่น ประจำปี 2026 วันลาพักร้อน 15 วัน", encoding="utf-8")
    res_healthy = rag_engine.ingest_file(healthy_file, original_name="นโยบายบริษัท.txt", org_id=org_id)
    assert res_healthy["status"] == "ok"
    healthy_fid = res_healthy["file_id"]

    meta_before = rag_engine._load_meta()
    assert healthy_fid in meta_before
    assert meta_before[healthy_fid]["status"] == "ready"
    healthy_chunks = meta_before[healthy_fid]["chunks"]
    assert healthy_chunks > 0

    # Verify initial chunk consistency
    kb = rag_engine._get_kb()
    assert kb.collection.count() == healthy_chunks, "Initial vector store count must equal healthy chunk count"

    # 2. Simulate server shutdown during file upload (crash / kill while status='processing')
    # File A: Crashed before embedding any chunks
    crashed_fid_a = "file_crashed_aaa"
    crashed_file_a = uploads_dir / "เอกสารที่ค้างA.txt"
    crashed_file_a.write_text("เนื้อหาเอกสาร A ที่กำลังประมวลผลอยู่ขณะดับ", encoding="utf-8")

    # File B: Crashed halfway through (inserted 1 orphan chunk in vector store before dying)
    crashed_fid_b = "file_crashed_bbb"
    crashed_file_b = uploads_dir / "เอกสารที่ค้างB.txt"
    crashed_file_b.write_text("เนื้อหาเอกสาร B ที่มี chunk หลงเหลือในเวกเตอร์สโตร์", encoding="utf-8")

    # Inject orphan chunk for File B into vector store
    kb.add_chunks(
        chunks=["เนื้อหาเอกสาร B chunk หลงเหลือ"],
        source_name="เอกสารที่ค้างB.txt",
        file_id=crashed_fid_b,
        metadatas=[{"source": "เอกสารที่ค้างB.txt", "file_id": crashed_fid_b, "organization_id": org_id, "category_id": ""}]
    )

    with rag_engine._META_LOCK:
        meta = rag_engine._load_meta()
        meta[crashed_fid_a] = {
            "name": "เอกสารที่ค้างA.txt",
            "path": str(crashed_file_a),
            "size": crashed_file_a.stat().st_size,
            "category_id": None,
            "category_name": "ไม่มีหมวดหมู่",
            "department": "General",
            "organization_id": org_id,
            "chunks": 0,
            "status": "processing",  # Stuck in INDEXING
            "timestamp": "2026-11-10T12:00:00"
        }
        meta[crashed_fid_b] = {
            "name": "เอกสารที่ค้างB.txt",
            "path": str(crashed_file_b),
            "size": crashed_file_b.stat().st_size,
            "category_id": None,
            "category_name": "ไม่มีหมวดหมู่",
            "department": "General",
            "organization_id": org_id,
            "chunks": 1,
            "status": "processing",  # Stuck in INDEXING
            "timestamp": "2026-11-10T12:00:05"
        }
        rag_engine._save_meta(meta)

    # 3. Simulate Server Restart Startup Sequence
    # On startup, app_server executes:
    #   1. rag_engine.cleanup_stale_processing(max_age_minutes=0)
    #   2. kb_cleanup.cleanup()
    cleaned_count = rag_engine.cleanup_stale_processing(max_age_minutes=0)
    assert cleaned_count == 2, f"Startup cleanup must clean both stuck files, got {cleaned_count}"

    import kb_cleanup
    kb_cleanup.cleanup()

    # 4. Verify Post-Restart Health & Consistency
    meta_after = rag_engine._load_meta()

    # Neither file should be stuck in 'processing' or 'INDEXING'
    for fid in (crashed_fid_a, crashed_fid_b):
        assert meta_after[fid]["status"] == "error", f"File {fid} must be marked as error, got {meta_after[fid]['status']}"
        assert meta_after[fid]["chunks"] == 0, f"File {fid} chunk count in meta must be reset to 0"
        assert "รีสตาร์ต" in meta_after[fid]["error"] or "timeout" in meta_after[fid]["error"]

    # Verify vector store chunk count EXACTLY equals meta chunk count sum
    total_meta_chunks = sum(info.get("chunks", 0) for info in meta_after.values() if info.get("status") == "ready")
    total_vector_chunks = kb.collection.count()
    assert total_vector_chunks == total_meta_chunks, (
        f"Vector store chunk count ({total_vector_chunks}) must match meta chunk count ({total_meta_chunks})"
    )

    # 5. Verify healthy file remains queryable
    results = rag_engine.query("วันลาพักร้อน", n_results=3, where={"organization_id": org_id})
    sources = [c.get("source") or c.get("source_name") for c in results]
    assert "นโยบายบริษัท.txt" in sources, "Healthy file must remain queryable after restart cleanup"

    # 6. Verify user can re-upload the crashed file cleanly
    res_reupload = rag_engine.ingest_file(crashed_file_b, original_name="เอกสารที่ค้างB.txt", org_id=org_id, force=True)
    assert res_reupload["status"] == "ok"
    reupload_fid = res_reupload["file_id"]
    meta_final = rag_engine._load_meta()
    assert meta_final[reupload_fid]["status"] == "ready"
    assert meta_final[reupload_fid]["chunks"] > 0

    final_meta_chunks = sum(info.get("chunks", 0) for info in meta_final.values() if info.get("status") == "ready")
    assert kb.collection.count() == final_meta_chunks, "After re-upload, vector store and meta chunks must remain consistent"

