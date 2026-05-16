import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('chat_history.db')
cursor = conn.cursor()

# Find table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Search for recon references in all tables
for t in tables:
    tname = t[0]
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{tname}'")
    schema = cursor.fetchone()
    if schema and 'file' in str(schema).lower():
        print(f"\nTable '{tname}' schema: {schema[0][:200]}")
        try:
            cursor.execute(f"SELECT * FROM {tname} LIMIT 1")
            cols = [d[0] for d in cursor.description]
            for col in cols:
                if 'file' in col.lower() or 'name' in col.lower():
                    cursor.execute(f"SELECT COUNT(*) FROM {tname} WHERE {col} LIKE '%recon%'")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"  Found {count} recon entries in {tname}.{col}")
        except:
            pass

conn.close()
