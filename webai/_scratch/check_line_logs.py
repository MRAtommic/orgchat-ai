import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('chat_history.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== RECENT GROUP MESSAGES ===")
try:
    cur.execute("SELECT * FROM group_messages ORDER BY id DESC LIMIT 5")
    for row in cur.fetchall():
        print(dict(row))
except Exception as e:
    print("Error querying group_messages:", e)

print("\n=== RECENT PRIVATE MESSAGES ===")
try:
    cur.execute("SELECT * FROM private_messages ORDER BY id DESC LIMIT 5")
    for row in cur.fetchall():
        print(dict(row))
except Exception as e:
    print("Error querying private_messages:", e)

print("\n=== RECENT EXPENSE CLAIMS ===")
try:
    cur.execute("SELECT * FROM expense_claims ORDER BY id DESC LIMIT 5")
    for row in cur.fetchall():
        print(dict(row))
except Exception as e:
    print("Error querying expense_claims:", e)

print("\n=== RECENT LEAVE REQUESTS ===")
try:
    cur.execute("SELECT * FROM leave_requests ORDER BY id DESC LIMIT 5")
    for row in cur.fetchall():
        print(dict(row))
except Exception as e:
    print("Error querying leave_requests:", e)

conn.close()
