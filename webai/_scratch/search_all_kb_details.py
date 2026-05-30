for filename in ["database.py", "rag_engine.py"]:
    print(f"=== {filename} ===")
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            if "knowledge_base" in line:
                print(f"Line {i+1}: {line.strip()}")
