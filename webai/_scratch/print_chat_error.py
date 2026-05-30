with open(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\routes\chat.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx in range(3430, 3480):
    if idx <= len(lines):
        safe_line = lines[idx-1].rstrip().encode('ascii', errors='ignore').decode('ascii')
        print(f"{idx}: {safe_line}")
