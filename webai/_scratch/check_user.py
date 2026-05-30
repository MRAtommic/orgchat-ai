import sqlite3

conn = sqlite3.connect('chat_history.db')
cursor = conn.cursor()

# Get user settings
cursor.execute("SELECT username, role, is_active FROM user_settings WHERE username = 'kanjanaporn.jat' COLLATE NOCASE")
print("User Settings:", cursor.fetchall())

# Get organization members
cursor.execute("SELECT organization_id, username, role FROM organization_members WHERE username = 'kanjanaporn.jat' COLLATE NOCASE")
print("Org Members:", cursor.fetchall())

# Let's list organizations
cursor.execute("SELECT id, name, slug FROM organizations")
print("Organizations:", cursor.fetchall())

conn.close()
