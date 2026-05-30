import re
import os

files = ["../page.html", "../index.html"]
for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        sections = re.findall(r'<section\s+id="([^"]+)"', content)
        print(f"Sections in {file_path}:")
        for s in sections:
            print(" -", s)
