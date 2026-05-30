import sqlite3

conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in chat_history.db:")
for t in tables:
    print(f" - {t}")
    cursor.execute(f"PRAGMA table_info({t})")
    cols = cursor.fetchall()
    print(f"   Columns: {[c[1] for c in cols]}")

conn.close()
