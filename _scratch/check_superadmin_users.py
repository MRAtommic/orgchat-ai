import sys
sys.path.append(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai")
import traceback

try:
    import database
    print("DB TYPE:", database.DB_TYPE)
    users = database.superadmin_get_all_users()
    print("Success! Number of users:", len(users))
except Exception as e:
    print("Failed!")
    traceback.print_exc()
