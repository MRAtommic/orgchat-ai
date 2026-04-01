import sqlite3
import os

DB_PATH = 'chat_history.db'
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Checking user_settings Schema ---")
    cursor.execute("PRAGMA table_info(user_settings)")
    for col in cursor.fetchall():
        print(col)
        
    print("\n--- Checking likes table Schema (New Reaction System) ---")
    cursor.execute("PRAGMA table_info(likes)")
    columns = cursor.fetchall()
    has_reaction = any(col[1] == 'reaction' for col in columns)
    for col in columns:
        print(col)
        
    if has_reaction:
        print("\n✅ OK: 'reaction' column found. New system should work.")
    else:
        print("\n❌ MISSING: 'reaction' column. Database migration failed or didn't run.")
        
    conn.close()
else:
    print(f"❌ Database not found at {DB_PATH}")
