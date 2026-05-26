import os

search_term = "created_at"
root_dir = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\routes"

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if search_term in line and ("profile" in line or "p." in line):
                            print(f"{file}:{line_num} -> {line.strip()}")
            except Exception:
                pass
