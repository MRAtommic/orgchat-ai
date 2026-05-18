with open("app_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def create_line_flex_bubble" in line:
        print(f"Line {idx+1}: {line.strip()}")
