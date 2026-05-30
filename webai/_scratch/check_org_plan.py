import sqlite3

conn = sqlite3.connect("chat_history.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT id, name, plan, plan_expires_at FROM organizations WHERE id = 1")
    row = cursor.fetchone()
    print("--- organization details ---")
    print(dict(row) if row else "Not found")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
