with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

start = 8440
end = 8480

with open("auto_click_context.js", "w", encoding="utf-8") as out:
    for idx in range(start, min(len(lines), end)):
        out.write(f"{idx+1}: {lines[idx]}")
print("Wrote auto-click context successfully.")
