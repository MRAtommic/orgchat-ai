import sqlite3
import os

db_path = "chat_history.db"
print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def dump_table(name):
    print(f"\n--- Table: {name} ---")
    try:
        cursor.execute(f"SELECT * FROM {name}")
        rows = cursor.fetchall()
        if not rows:
            print("(empty)")
            return
        for r in rows:
            print(dict(r))
    except Exception as e:
        print(f"Error reading {name}: {e}")

dump_table("organizations")
dump_table("organization_members")
dump_table("line_group_mappings")
dump_table("app_settings")
dump_table("org_google_tokens")
dump_table("user_google_tokens")
dump_table("user_profiles")

conn.close()
