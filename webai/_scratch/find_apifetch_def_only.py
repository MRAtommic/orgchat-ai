with open("static/app.js", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "apiFetch" in line and ("function apiFetch" in line or "apiFetch = async" in line or "apiFetch=async" in line):
            print(f"{i+1}: {line.strip()}")
