import sqlite3
import sys
sys.path.append('.')
import database

database.init_db()
conn = sqlite3.connect(database.DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in cursor.fetchall()])

cursor.execute("SELECT * FROM line_group_mappings")
rows = [dict(r) for r in cursor.fetchall()]
print("LINE Group Mappings in DB:")
for r in rows:
    print(r)
conn.close()
