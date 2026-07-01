import sqlite3
import os

db_path = os.environ.get("DB_PATH", "chat_history.db")
print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    if 'user_settings' in tables:
        cursor.execute("SELECT username, role, is_active, email, custom_password FROM user_settings")
        for r in cursor.fetchall():
            print(f"User Setting: {r}")
    else:
         print("No user_settings table found")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
