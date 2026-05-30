import sqlite3

conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()

# Remove ai.heartwarming from Default Organization (id=1)
cursor.execute("DELETE FROM organization_members WHERE organization_id = 1 AND username = 'ai.heartwarming'")
deleted_count = cursor.rowcount
conn.commit()
conn.close()

print(f"Successfully deleted {deleted_count} row(s) for ai.heartwarming from Default Organization (id=1)")
