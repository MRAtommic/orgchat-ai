import os

templates_dir = 'templates'
for f in os.listdir(templates_dir):
    if f.endswith('.html'):
        path = os.path.join(templates_dir, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            escaped_count = content.count(r'\${')
            escaped_bt = content.count(r'\`')
            if escaped_count > 0 or escaped_bt > 0:
                print(f"File {f}: escaped ${escaped_count}, escaped backticks {escaped_bt}")
