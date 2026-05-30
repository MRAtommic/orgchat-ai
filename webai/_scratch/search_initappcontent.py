with open("static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "function initAppContent(" in line or "initAppContent(" in line:
        print(f"Line {i+1}: {line.strip()}")
