import sqlite3
import os

db_path = "chat_history.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("--- Tables ---")
        for table in tables:
            print(f"Table: {table[0]}")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  Column: {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
