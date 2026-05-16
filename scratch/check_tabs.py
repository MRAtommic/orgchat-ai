import sys

with open(r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\app_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '\t' in line:
        print(f"Tab found at line {i+1}")
    # Check for mixed indentation if possible
    stripped = line.lstrip(' ')
    if stripped.startswith('\t'):
        print(f"Tab indentation at line {i+1}")
    if line.startswith(' ') and '\t' in line[:line.find(line.lstrip().split()[0] if line.lstrip() else ' ')]:
         print(f"Mixed space/tab at line {i+1}")
