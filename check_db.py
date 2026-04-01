import sqlite3
import json

DB_PATH = r"c:\Users\FEWIT\Desktop\ai\chat_history.db"

def check_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- room_messages table ---")
    cursor.execute("PRAGMA table_info(room_messages)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    print("\n--- chat_rooms table ---")
    cursor.execute("PRAGMA table_info(chat_rooms)")
    for col in cursor.fetchall():
        print(col)
        
    print("\n--- AI Personas ---")
    cursor.execute("SELECT id, name FROM ai_personas")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
