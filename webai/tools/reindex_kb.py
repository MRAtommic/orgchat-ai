# -*- coding: utf-8 -*-
"""
tools/reindex_kb.py — Re-index Knowledge Base Files into Vector Store
Re-processes all files in uploads/ to ensure every single chunk is properly
embedded and stored with unique sequential IDs (fixing the batch overwrite bug).
"""
import io
import json
import os
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import rag_engine


def reindex_all():
    meta_path = rag_engine.META_FILE
    if not meta_path.exists():
        print(f"❌ ไม่พบไฟล์ {meta_path}")
        return

    meta = rag_engine._load_meta()
    if not meta:
        print("ℹ️ ไม่มีไฟล์ในคลังความรู้")
        return

    print("=" * 70)
    print("🚀 เริ่มต้นกระบวนการ Re-index เอกสารทั้งหมดในคลังความรู้")
    print(f"📁 จำนวนไฟล์ทั้งหมด: {len(meta)} ไฟล์")
    print("=" * 70)

    success_count = 0
    total_new_chunks = 0

    for idx, (fid, info) in enumerate(list(meta.items()), 1):
        file_path_str = info.get("path")
        orig_name = info.get("name", fid)
        org_id = info.get("organization_id", 1)
        dept = info.get("department", "General")
        cat_id = info.get("category_id")

        if not file_path_str or not Path(file_path_str).exists():
            # Check relative to uploads/
            alt_path = rag_engine.UPLOAD_DIR / Path(file_path_str).name if file_path_str else None
            if alt_path and alt_path.exists():
                file_path = alt_path
            else:
                print(f"[{idx}/{len(meta)}] ⏩ ข้าม {orig_name}: ไม่พบไฟล์บนดิสก์")
                continue
        else:
            file_path = Path(file_path_str)

        print(f"[{idx}/{len(meta)}] 🔄 กำลังประมวลผล: {orig_name} (Org: {org_id}) ...")
        try:
            res = rag_engine.ingest_file(
                file_path=file_path,
                original_name=orig_name,
                department=dept,
                category_id=cat_id,
                org_id=org_id,
                force=True
            )
            chunks = res.get("chunks", 0)
            status = res.get("status", "unknown")
            print(f"       ✅ สำเร็จ: สร้าง {chunks} chunks (สถานะ: {status})")
            success_count += 1
            total_new_chunks += chunks
        except Exception as e:
            print(f"       ❌ ล้มเหลว: {e}")

    print("=" * 70)
    kb = rag_engine._get_kb()
    vcount = kb.collection.count()
    print(f"🎉 เสร็จสิ้น! Re-index สำเร็จ {success_count}/{len(meta)} ไฟล์")
    print(f"📊 จำนวน Chunks ใน Vector Store ปัจจุบัน: {vcount} chunks")
    print("=" * 70)


if __name__ == "__main__":
    reindex_all()
