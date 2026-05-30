with open("rag_engine.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "knowledge_base" in line or "CREATE TABLE" in line:
        print(f"Line {i+1}: {line.strip()[:100]}")
