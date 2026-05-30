import database

def main():
    print("🧪 Starting LINE unbinding backend test...")
    
    # 1. Choose a test user
    username = "mxmm2547"
    test_line_id = "U1234567890abcdef1234567890abcdef"
    
    # 2. Clear any existing mapping first
    print(f"🧹 Unlinking {username} first...")
    database.unlink_line_user(username)
    
    # 3. Check list
    users = database.admin_get_all_users(org_id=1)
    target = next((u for u in users if u["username"] == username), None)
    if target:
        print(f"📋 Initial state for {username}: line_user_id = {target.get('line_user_id')}")
        assert target.get("line_user_id") is None, "Expected line_user_id to be None initially"
    else:
        print(f"❌ Test user {username} not found in org 1!")
        return

    # 4. Link LINE ID
    print(f"🔗 Linking {username} to {test_line_id}...")
    success = database.link_line_user(username, test_line_id)
    print(f"  Result: {success}")
    assert success, "Failed to link user"
    
    # 5. Check list again
    users = database.admin_get_all_users(org_id=1)
    target = next((u for u in users if u["username"] == username), None)
    print(f"📋 State after link for {username}: line_user_id = {target.get('line_user_id')}")
    assert target.get("line_user_id") == test_line_id, f"Expected line_user_id to be {test_line_id}"
    
    # 6. Unlink
    print(f"🔌 Unlinking {username}...")
    success = database.unlink_line_user(username)
    print(f"  Result: {success}")
    assert success, "Failed to unlink user"
    
    # 7. Check list one last time
    users = database.admin_get_all_users(org_id=1)
    target = next((u for u in users if u["username"] == username), None)
    print(f"📋 Final state after unlink for {username}: line_user_id = {target.get('line_user_id')}")
    assert target.get("line_user_id") is None, "Expected line_user_id to be None after unlinking"
    
    print("✅ All backend database and query tests passed successfully!")

if __name__ == '__main__':
    main()
