with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(8890, 8960):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].rstrip()}")
