with open("routes/auth.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if "allowed" in line or "whitelist" in line:
        out.append(f"{i+1}: {line.strip()}")

with open("_scratch/find_whitelist_logic_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
