import sqlite3

def main():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT * FROM line_group_mappings")
    cols = [col[0] for col in c.description]
    rows = c.fetchall()
    print("LINE GROUP MAPPINGS:")
    for r in rows:
        row_dict = dict(zip(cols, r))
        print(f"Group: {row_dict.get('group_name')} | Real Name: {row_dict.get('line_real_name')} | Org ID: {row_dict.get('org_id')}")
        print(f"  default_folder_id: {row_dict.get('default_folder_id')}")
        print(f"  default_folder_name: {row_dict.get('default_folder_name')}")
        print(f"  group_id: {row_dict.get('group_id')}")
        print("-" * 50)

if __name__ == '__main__':
    main()
