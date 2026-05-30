import sqlite3

def test_delete():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    username = "bfbfbf"
    
    tables = [
        "user_profiles", "user_settings", "user_category_access", 
        "room_members", "likes", "messages", "schedules", 
        "posts", "comments", "private_messages", "organization_members",
        "room_messages", "group_messages", "push_subscriptions",
        "user_google_tokens", "user_status", "search_history",
        "message_read_receipts", "private_message_read_status",
        "leave_requests", "leave_comments", "expense_claims", "wiki_pages"
    ]
    
    for table in tables:
        col = "username"
        if table == "private_messages":
            query = f"DELETE FROM private_messages WHERE sender = '{username}' OR recipient = '{username}'"
        elif table == "likes":
            col = "user"
            query = f"DELETE FROM {table} WHERE {col} = '{username}'"
        elif table in ["comments", "posts", "wiki_pages"]:
            col = "author"
            query = f"DELETE FROM {table} WHERE {col} = '{username}'"
        else:
            query = f"DELETE FROM {table} WHERE {col} = '{username}'"
            
        try:
            cursor.execute(query)
            print(f"[OK] Success on table: {table}")
        except Exception as e:
            print(f"[FAIL] Failed on table {table}: {e}")

    try:
        cursor.execute(f"DELETE FROM kanban_cards WHERE assignee = '{username}' OR created_by = '{username}'")
        print("[OK] Success on table: kanban_cards")
    except Exception as e:
        print(f"[FAIL] Failed on table kanban_cards: {e}")

    conn.close()

if __name__ == "__main__":
    test_delete()
