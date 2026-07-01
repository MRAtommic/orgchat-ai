with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(4740, 4775):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].rstrip()}")
