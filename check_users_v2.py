import sqlite3
import os

db_path = "chat_history.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # Based on inspect_db output, permissions are in 'user_settings'
        cursor.execute("SELECT username, role, can_edit_kb, can_view_kb FROM user_settings")
        rows = cursor.fetchall()
        print("--- User Permissions (from user_settings) ---")
        for row in rows:
            print(f"User: {row['username']} | Role: {row['role']} | Edit KB: {row['can_edit_kb']} | View KB: {row['can_view_kb']}")
    except Exception as e:
        print(f"Error querying table: {e}")
    finally:
        conn.close()
