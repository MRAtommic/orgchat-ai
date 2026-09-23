import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import billing

def main():
    import database
    conn = database._get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, plan, plan_expires_at FROM organizations")
    orgs = cursor.fetchall()
    conn.close()
    
    if not orgs:
        print("No organizations found.")
        return
        
    print("Select an organization to upgrade:")
    for i, org in enumerate(orgs):
        print(f"[{i+1}] ID: {org['id']} | Name: {org['name']} | Current Plan: {org['plan']} (expires: {org['plan_expires_at']})")
        
    try:
        choice = int(input("Enter organization number: ")) - 1
        if choice < 0 or choice >= len(orgs):
            print("Invalid choice.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return
        
    org = orgs[choice]
    print(f"\nSelected: {org['name']} (ID: {org['id']})")
    print("[1] Upgrade to PRO")
    print("[2] Upgrade to BUSINESS")
    print("[3] Downgrade to FREE")
    
    plan_choice = input("Select plan: ")
    if plan_choice == "1":
        plan = "pro"
    elif plan_choice == "2":
        plan = "business"
    elif plan_choice == "3":
        plan = "free"
    else:
        print("Invalid choice.")
        return
        
    import datetime
    from datetime import timedelta, timezone
    expires_at = (datetime.datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    
    try:
        billing.set_org_plan(org['id'], plan, expires_at if plan != "free" else None)
        print(f"Successfully updated organization ID {org['id']} plan to '{plan}'!")
    except Exception as e:
        print(f"Failed to update plan: {e}")

if __name__ == "__main__":
    main()
