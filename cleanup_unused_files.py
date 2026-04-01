import sqlite3
import os
from pathlib import Path

def cleanup():
    db_path = 'chat_history.db'
    upload_dir = Path('uploads')
    
    if not os.path.exists(db_path):
        print("❌ ไม่พบฐานข้อมูล")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. รวบรวมไฟล์ที่ใช้อยู่จริงจากฐานข้อมูล
    used_files = set()

    # จากตาราง user_profiles (avatars/backgrounds)
    cursor.execute("SELECT avatar_url, background_url FROM user_profiles")
    for row in cursor.fetchall():
        for item in row:
            if item and 'uploads/' in item:
                used_files.add(item.split('uploads/')[-1])

    # จากตาราง posts (attachments)
    cursor.execute("SELECT attachments FROM posts")
    for row in cursor.fetchall():
        if row[0]:
            try:
                import json
                files = json.loads(row[0])
                for f in files:
                    if isinstance(f, str): used_files.add(f.split('uploads/')[-1])
                    elif isinstance(f, dict) and 'url' in f: used_files.add(f['url'].split('uploads/')[-1])
            except: 
                # ถ้าไม่ใช่ JSON อาจเป็น string ปกติ
                used_files.add(row[0].split('uploads/')[-1])

    # จากข้อความแชท (ถ้ามี attachments)
    for table in ['room_messages', 'private_messages', 'group_messages']:
        try:
            cursor.execute(f"SELECT attachments FROM {table}")
            for row in cursor.fetchall():
                if row[0]:
                    used_files.add(row[0].split('uploads/')[-1])
        except: pass

    # จาก Knowledge Base (ถ้ามีตารางนี้)
    try:
        cursor.execute("SELECT name FROM knowledge_base") # หรือชื่อคอลัมน์ที่เก็บ path
        for row in cursor.fetchall():
            used_files.add(row[0])
    except: pass

    print(f"🔍 พบไฟล์ที่ใช้งานอยู่จริงในระบบ: {len(used_files)} ไฟล์")

    # 2. ตรวจสอบโฟลเดอร์ uploads และลบไฟล์ที่ไม่ได้ใช้
    deleted_count = 0
    if upload_dir.exists():
        for file_path in upload_dir.rglob('*'):
            if file_path.is_file():
                # ตรวจสอบว่าชื่อไฟล์หรือ path สัมพัทธ์อยู่ใน used_files หรือไม่
                rel_path = str(file_path.relative_to(upload_dir)).replace('\\', '/')
                if rel_path not in used_files:
                    # ขอยกเว้นไฟล์ในบางโฟลเดอร์ที่อาจจำเป็น หรือไฟล์ระบบ
                    if not any(x in str(file_path) for x in ['.gitkeep']):
                        print(f"🗑️ ลบไฟล์ที่ไม่ได้ใช้: {file_path}")
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            print(f"❌ ลบไม่ได้: {e}")

    # 3. ลบไฟล์สำรองและสคริปต์ชั่วคราวใน root
    extra_files = [
        'chat_history.db.bak',
        'chat_history_20260304_132243.db.bak',
        'chat_history_20260304_133407.db.bak',
        'chat_history_20260304_134030.db.bak',
        'inspect_dbs.py',
        'verify_changes.py',
        'check_db.py',
        'check_schema.py',
        'debug_db.py'
    ]
    
    for f in extra_files:
        if os.path.exists(f):
            print(f"🗑️ ลบไฟล์ส่วนเกิน: {f}")
            os.remove(f)
            deleted_count += 1

    conn.close()
    print(f"\n✨ ทำความสะอาดเรียบร้อย! ลบไปทั้งหมด {deleted_count} รายการ")

if __name__ == "__main__":
    cleanup()
