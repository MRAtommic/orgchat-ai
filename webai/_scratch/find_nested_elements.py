with open("../templates/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

start = 4850
end = 4980

with open("nested_elements_context.html", "w", encoding="utf-8") as out:
    for idx in range(start, min(len(lines), end)):
        out.write(f"{idx+1}: {lines[idx]}")
print("Wrote nested elements context successfully.")
