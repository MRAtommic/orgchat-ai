import os
import glob

for pyfile in glob.glob("**/*.py", recursive=True):
    with open(pyfile, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if "knowledge_base" in content:
        print(f"File: {pyfile}")
