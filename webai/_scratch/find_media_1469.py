with open("../static/style.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

start = 1460
end = 1540

with open("media_1469_context.css", "w", encoding="utf-8") as out:
    for idx in range(start, min(len(lines), end)):
        out.write(f"{idx+1}: {lines[idx]}")
print("Wrote media context successfully.")
