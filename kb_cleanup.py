import json
import os
import sys
import io
from pathlib import Path

# Force UTF-8 for Thai support
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path so we can import rag_engine
sys.path.append(os.getcwd())

import rag_engine

def cleanup():
    print("🔍 กำลังตรวจสอบและลบไฟล์ที่ไม่มีอยู่จริงออกจากคลังข้อมูล...")
    
    # Load meta using rag_engine's own loader (which includes self-healing)
    meta = rag_engine._load_meta()
    initial_count = len(meta)
    
    valid_fids = []
    removed_count = 0
    removed_names = []
    
    new_meta = {}
    for fid, info in meta.items():
        path_str = info.get("path")
        if not path_str:
            print(f"⚠️ ไม่พบข้อมูล path สำหรับ {info.get('name', fid)}")
            continue
            
        file_path = Path(path_str)
        if file_path.exists():
            new_meta[fid] = info
            valid_fids.append(fid)
        else:
            print(f"🗑️ พบข้อมูลใน Meta แต่ไฟล์หายไปจากดิสก์: {info.get('name')} (ID: {fid})")
            removed_names.append(info.get('name'))
            # ลบออกจาก ChromaDB (Vector Store)
            try:
                rag_engine._kb.delete_by_file_id(fid)
            except Exception as e:
                print(f"  ⚠️ ไม่สามารถลบข้อมูลใน ChromaDB ได้: {e}")
            removed_count += 1
    
    # บันทึก metadata ที่เหลือ
    rag_engine._save_meta(new_meta)
    
    # 2. ตรวจสอบไฟล์ใน Disk ที่ไม่มีใน Metadata
    print("📂 กำลังตรวจสอบไฟล์ส่วนเกินใน uploads/...")
    disk_files_removed = 0
    valid_paths = [Path(info["path"]).resolve() for info in new_meta.values()]
    
    for item in rag_engine.UPLOAD_DIR.iterdir():
        if item.is_file():
            # Skip hidden files or system files
            if item.name.startswith('.'): continue
            
            if item.resolve() not in valid_paths:
                print(f"🗑️ ลบไฟล์ส่วนเกินที่ไม่ได้ใช้งาน: {item.name}")
                try:
                    item.unlink()
                    disk_files_removed += 1
                except Exception as e:
                    print(f"  ⚠️ ไม่สามารถลบไฟล์ได้: {e}")

    # ลบเศษซาก (Orphaned chunks) ที่อาจจะค้างอยู่
    print("🧹 กำลังตรวจสอบเศษซากข้อมูลใน ChromaDB...")
    orphaned_deleted = rag_engine._kb.prune_orphaned_chunks(valid_fids)
    
    print("\n" + "="*50)
    print(f"✨ ทำความสะอาดคลังข้อมูลเรียบร้อยแล้ว!")
    print(f"📊 ไฟล์เริ่มต้น (ใน Meta): {initial_count} ไฟล์")
    print(f"📊 ลบข้อมูล Meta ที่ไฟล์หาย: {removed_count} รายการ")
    print(f"📊 ลบไฟล์ส่วนเกินบน Disk: {disk_files_removed} ไฟล์")
    print(f"📊 ไฟล์ที่เหลืออยู่: {len(new_meta)} ไฟล์")
    print(f"📊 ลบเศษซากข้อมูลใน ChromaDB: {orphaned_deleted} รายการ")
    print("="*50)
    
    if removed_names:
        print(f"📁 รายชื่อข้อมูลที่ถูกลบออกจาก Index: {', '.join(removed_names[:10])}")
        if len(removed_names) > 10:
            print(f"   ...และอีก {len(removed_names)-10} ไฟล์")

if __name__ == "__main__":
    cleanup()
