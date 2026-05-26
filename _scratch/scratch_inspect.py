import sys
import os

filepath = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\app_server.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "/api/login" in line:
        output.append(f"Line {idx+1}: {line.strip()}")
        # print some surrounding lines
        for j in range(max(0, idx-5), min(len(lines), idx+40)):
            output.append(f"  {j+1}: {lines[j].strip()}")
        output.append("="*40)
        break

with open("scratch_inspect_output.txt", "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(output))
print("Done writing to scratch_inspect_output.txt")
