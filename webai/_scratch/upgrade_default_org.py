import sqlite3

conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()

try:
    cursor.execute("UPDATE organizations SET plan = 'business', plan_expires_at = NULL WHERE id = 1")
    conn.commit()
    print("Successfully upgraded organization ID 1 to Business plan!")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
