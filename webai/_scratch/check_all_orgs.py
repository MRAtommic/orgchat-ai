import sqlite3

conn = sqlite3.connect("chat_history.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT id, plan, plan_expires_at FROM organizations")
    rows = cursor.fetchall()
    print("--- all organizations ---")
    for r in rows:
        print(dict(r))
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
