with open("static/app.js", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "apiFetch" in line and ("function" in line or "const" in line or "let" in line or "var" in line):
            print(f"{i+1}: {line.strip()}")
