import sqlite3

conn = sqlite3.connect("chat_history.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM user_settings WHERE username = 'mxmm2547'")
    row1 = cursor.fetchone()
    print("--- user_settings for mxmm2547 ---")
    print(dict(row1) if row1 else "Not found")
    
    cursor.execute("SELECT * FROM organization_members WHERE username = 'mxmm2547'")
    rows2 = cursor.fetchall()
    print("--- organization_members for mxmm2547 ---")
    for r in rows2:
        print(dict(r))
        
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
