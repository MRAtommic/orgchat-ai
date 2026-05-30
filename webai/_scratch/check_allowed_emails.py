import sqlite3

conn = sqlite3.connect("chat_history.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM organization_allowed_emails")
    rows = cursor.fetchall()
    print("--- organization_allowed_emails ---")
    for r in rows:
        print(dict(r))
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
