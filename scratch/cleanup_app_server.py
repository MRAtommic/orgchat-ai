
import os

path = r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\app_server.py'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Identify the indices for lines 1155 to 1352 (1-based)
# 0-based indices are 1154 to 1351
start_index = 1154
end_index = 1351

# Filter out the mangled range
new_lines = lines[:start_index] + lines[end_index+1:]

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Removed lines {start_index+1} to {end_index+1}. Total lines now: {len(new_lines)}")
