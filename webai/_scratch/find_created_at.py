import sys
sys.path.append(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai")

with open(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\database.py", "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        if "created_at" in line and ("profiles" in line or "p." in line):
            print(f"{line_num}: {line.strip()}")
