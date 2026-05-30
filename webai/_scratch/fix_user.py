import sqlite3

conn = sqlite3.connect('chat_history.db')
cursor = conn.cursor()

# Promote kanjanaporn.jat in user_settings to 'admin'
cursor.execute("UPDATE user_settings SET role = 'admin' WHERE username = 'kanjanaporn.jat' COLLATE NOCASE")
conn.commit()

# Double check
cursor.execute("SELECT username, role, is_active FROM user_settings WHERE username = 'kanjanaporn.jat' COLLATE NOCASE")
print("Updated User Settings:", cursor.fetchall())

conn.close()
