with open("routes/auth.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
for i in range(1080, 1155):
    if i < len(lines):
        out.append(f"{i+1}: {lines[i].strip()}")

with open("_scratch/print_api_login_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
