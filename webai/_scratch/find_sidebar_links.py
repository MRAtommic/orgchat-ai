with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "sidebar" in line.lower() and ("click" in line or "clickListener" in line or "addEventListener" in line):
        print(f"Line {i+1}: {line.strip()[:100]}")
