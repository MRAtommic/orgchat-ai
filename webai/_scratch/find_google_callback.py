with open("routes/auth.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if "google" in line.lower() or "callback" in line.lower() or "oauth" in line.lower() or "login" in line.lower():
        out.append(f"{i+1}: {line.strip()}")

with open("_scratch/find_google_callback_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
