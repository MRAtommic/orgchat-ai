import json
import os
import sqlite3
import sys
from pathlib import Path

# Reconfigure stdout to use UTF-8 (resilient against Windows encoding issues)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure working directory is set to project root
BASE_DIR = Path(__file__).parent.parent.absolute()
os.chdir(str(BASE_DIR))

# 1. Sync file_meta.json with disk
meta_file = "file_meta.json"
if os.path.exists(meta_file):
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    new_meta = {}
    removed = []
    for fid, info in meta.items():
        path = info.get("path")
        if path and os.path.exists(path):
            new_meta[fid] = info
        else:
            removed.append(info.get("name", fid))
    
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(new_meta, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Synced file_meta.json. Removed {len(removed)} missing files: {removed}")

# 2. Update Database Permissions for Admin users
db_path = "chat_history.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Give all admins Edit KB, View KB, and Delete KB rights
        cursor.execute("""
            UPDATE user_settings 
            SET can_edit_kb = 1, can_view_kb = 1, can_delete_kb = 1 
            WHERE role = 'admin'
        """)
        conn.commit()
        print(f"✅ Updated permissions for {cursor.rowcount} admin users.")
    except Exception as e:
        print(f"❌ DB Error: {e}")
    finally:
        conn.close()
else:
    print("❌ DB not found.")
