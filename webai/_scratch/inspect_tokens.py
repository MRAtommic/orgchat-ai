import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("chat_history.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== org_google_tokens schema ===")
cursor.execute("PRAGMA table_info(org_google_tokens)")
for col in cursor.fetchall():
    print(dict(col))

print("\n=== org_google_tokens contents ===")
cursor.execute("SELECT * FROM org_google_tokens")
for row in cursor.fetchall():
    d = dict(row)
    # Censor tokens
    for k in ['access_token', 'refresh_token', 'credentials_json']:
        if k in d and d[k]: d[k] = '***'
    print(d)

print("\n=== organizations credentials / drive settings ===")
cursor.execute("PRAGMA table_info(organizations)")
for col in cursor.fetchall():
    print(dict(col))

conn.close()
