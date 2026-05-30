import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("chat_history.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== ORGANIZATIONS ===")
cursor.execute("SELECT * FROM organizations")
orgs = cursor.fetchall()
for o in orgs:
    print(dict(o))

print("\n=== MEMBERS OF EACH ORG ===")
cursor.execute("""
    SELECT om.*, o.name as org_name 
    FROM organization_members om
    JOIN organizations o ON o.id = om.organization_id
""")
members = cursor.fetchall()
for m in members:
    print(dict(m))

print("\n=== USER PROFILES ===")
cursor.execute("SELECT username, display_name, role, is_active FROM user_profiles")
users = cursor.fetchall()
for u in users:
    print(dict(u))

print("\n=== GOOGLE TOKENS / ORG SETTINGS ===")
cursor.execute("SELECT * FROM org_google_tokens")
tokens = cursor.fetchall()
for t in tokens:
    # Print keys but censor token for security
    d = dict(t)
    if 'access_token' in d: d['access_token'] = '***'
    if 'refresh_token' in d: d['refresh_token'] = '***'
    print(d)

conn.close()
