with open("database.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "create table" in line.lower() or "execute(" in line.lower() and "table" in line.lower():
        print(f"Line {i+1}: {line.strip()[:100]}")
