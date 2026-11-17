import os
import re

root = r'orgchat-ai-main/webai'
pattern = re.compile(r'(\.get\(\s*[\'"]role[\'"]\s*,\s*[\'"]admin[\'"]|or\s+[\'"]admin[\'"]|session\.get\(\s*[\'"]user[\'"]\s*,\s*[\'"]Admin[\'"])', re.IGNORECASE)
results = []
for dirpath, _, filenames in os.walk(root):
    if 'tests' in dirpath:
        continue
    for fn in filenames:
        if fn.endswith('.py'):
            fp = os.path.join(dirpath, fn)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                for idx, line in enumerate(f, 1):
                    if pattern.search(line):
                        results.append((fp, idx, line.strip()))

for r in results:
    print(f'{r[0]}:{r[1]}: {r[2]}')

