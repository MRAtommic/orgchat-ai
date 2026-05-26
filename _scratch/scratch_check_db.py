import sqlite3
import json
import os

DB_PATH = "chat_history.db"

def check():
    if not os.path.exists(DB_PATH):
        with open("scratch_db_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Database {DB_PATH} not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    out_lines = []
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    out_lines.append(f"Tables: {tables}")
    
    # If room_messages exists, let's see the latest 5 messages
    for table_tuple in tables:
        table_name = table_tuple[0]
        if "message" in table_name.lower() or "upload" in table_name.lower() or "log" in table_name.lower():
            out_lines.append(f"\n--- Latest 5 from {table_name} ---")
            try:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 5;")
                rows = cursor.fetchall()
                for row in rows:
                    out_lines.append(str(row))
            except Exception as e:
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                    rows = cursor.fetchall()
                    for row in rows:
                        print(row)
                except Exception as e2:
                    print(f"Error reading {table_name}: {e2}")

    conn.close()

    with open("scratch_db_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))

if __name__ == "__main__":
    check()
