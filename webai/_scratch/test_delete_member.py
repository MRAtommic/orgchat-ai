import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_server import app
import database as db

def main():
    print("🧪 Testing org member deletion API endpoint...")
    client = app.test_client()
    
    # 1. Check current members of org 1
    org_id = 1
    username_to_delete = "donut2548donut"
    
    # Ensure the user is a member of org 1 first
    if not db.is_org_member(org_id, username_to_delete):
        db.add_org_member(org_id, username_to_delete, role="member")
        
    print(f"📋 Is {username_to_delete} org member before test: {db.is_org_member(org_id, username_to_delete)}")
    
    # 2. Simulate API delete request as an org admin
    # mxmm2547 is an admin of org 1 in the database
    with client.session_transaction() as sess:
        sess['user'] = 'mxmm2547'
        sess['org_id'] = 1
        sess['role'] = 'admin'
        sess['org_role'] = 'admin'
        
    print(f"📡 Sending DELETE request to /api/org/members/{username_to_delete}...")
    resp = client.delete(f'/api/org/members/{username_to_delete}')
    
    print(f"📥 Response Code: {resp.status_code}")
    print(f"📥 Response Body: {resp.get_json()}")
    
    # Check if actually deleted from database
    is_still_member = db.is_org_member(org_id, username_to_delete)
    print(f"📋 Is {username_to_delete} org member after test: {is_still_member}")
    
    if resp.status_code == 200 and resp.get_json().get("ok") is True:
        if is_still_member:
            print("❌ BUG FOUND! API returned 200 OK but member was NOT deleted from the database!")
        else:
            print("✅ SUCCESS! Member was successfully deleted from the database.")
    else:
        print(f"❌ FAILED! API returned error: {resp.get_json()}")

if __name__ == '__main__':
    main()
