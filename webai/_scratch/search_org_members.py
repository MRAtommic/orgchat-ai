with open("database.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if "organization_members" in line:
        out.append(f"{i+1}: {line.strip()}")

with open("_scratch/search_org_members_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
