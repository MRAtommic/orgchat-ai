import os
import glob

for pyfile in glob.glob("**/*.py", recursive=True):
    with open(pyfile, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if "knowledge_base" in content and "CREATE" in content:
        print(f"FOUND IN {pyfile}!")
        for i, line in enumerate(content.splitlines()):
            if "knowledge_base" in line or "CREATE" in line:
                print(f"  Line {i+1}: {line.strip()[:100]}")
