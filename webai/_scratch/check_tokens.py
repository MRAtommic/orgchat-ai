import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('chat_history.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== USER PROFILES WITH LINE ID ===")
try:
    cur.execute("SELECT username, line_user_id, display_name FROM user_profiles")
    for row in cur.fetchall():
        print(dict(row))
except Exception as e:
    print("Error querying user_profiles:", e)

conn.close()
