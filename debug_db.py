import sqlite3
import os

DB_PATH = 'chat_history.db'
if not os.path.exists(DB_PATH):
    print(f"DB not found at {DB_PATH}")
else:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_settings WHERE username = 'Admin'")
    row = cursor.fetchone()
    print(f"User settings for Admin: {row}")
    # Also list all user settings to see if something changed
    cursor.execute("SELECT * FROM user_settings")
    all_users = cursor.fetchall()
    print(f"All user settings: {all_users}")
    conn.close()
