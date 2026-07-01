with open('templates/index.html', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'id="view-line-' in line:
            print(f"{idx}: {line.strip()[:150]}")
