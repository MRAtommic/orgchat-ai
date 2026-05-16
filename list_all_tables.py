import sqlite3
import os

DB_PATH = 'chat_history.db'
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Listing All Tables in chat_history.db ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"Table: {table[0]}")
        # Also print row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")
        
    conn.close()
else:
    print(f"❌ Database not found at {DB_PATH}")
