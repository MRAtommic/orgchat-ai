with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

start = 13820
end = 13950

with open("qr_js_context.js", "w", encoding="utf-8") as out:
    for idx in range(start, min(len(lines), end)):
        out.write(f"{idx+1}: {lines[idx]}")
print("Wrote context to qr_js_context.js successfully.")
