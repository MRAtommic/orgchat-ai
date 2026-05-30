import sqlite3

def check_schema():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    
    print("--- events Table Schema ---")
    cursor.execute("PRAGMA table_info(events);")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    print("\n--- Latest 5 records ---")
    try:
        cursor.execute("SELECT * FROM events ORDER BY time DESC LIMIT 5;")
        print(cursor.fetchall())
    except Exception as e:
        print(f"Error querying events: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_schema()
