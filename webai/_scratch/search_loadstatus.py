with open("static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "async function loadStatus(" in line or "function loadStatus(" in line:
        print(f"Line {i+1}: {line.strip()}")
