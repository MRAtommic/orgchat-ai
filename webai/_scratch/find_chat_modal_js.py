with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

start = 8820
end = 8910

with open("chat_modal_js.js", "w", encoding="utf-8") as out:
    for idx in range(start, min(len(lines), end)):
        out.write(f"{idx+1}: {lines[idx]}")
print("Wrote context to chat_modal_js.js successfully.")
