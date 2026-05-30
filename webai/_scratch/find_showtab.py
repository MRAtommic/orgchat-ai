with open("templates/superadmin.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if "showTab" in line:
        out.append(f"{i+1}: {line.strip()}")

with open("_scratch/find_showtab_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
