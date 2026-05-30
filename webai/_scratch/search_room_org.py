with open("database.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "chat_rooms" in line or "room" in line.lower() and "org" in line.lower():
        print(f"Line {i+1}: {line.strip()[:100]}")
