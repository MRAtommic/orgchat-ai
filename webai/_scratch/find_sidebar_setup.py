with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "showView" in line and ("'chat'" in line or '"chat"' in line or "viewId" in line):
        print(f"Line {i+1}: {line.strip()[:100]}")
