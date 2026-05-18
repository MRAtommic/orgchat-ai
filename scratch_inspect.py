import os

def search_files(directory, query):
    results = []
    for root, dirs, files in os.walk(directory):
        if any(ignored in root for ignored in [".git", "__pycache__", "chroma_db", "node_modules"]):
            continue
        for file in files:
            if file.endswith((".py", ".html", ".js")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if query in line:
                                results.append((path, line_num, line.strip()))
                except Exception as e:
                    pass
    return results

print("Searching for 'สรุปข่าวสาร'...")
res = search_files(".", "สรุปข่าวสาร")
for r in res:
    print(f"Match: {r[0]} (Line {r[1]}): {r[2]}")

print("\nSearching for 'สวัสดีตอนเช้า'...")
res2 = search_files(".", "สวัสดีตอนเช้า")
for r in res2:
    print(f"Match: {r[0]} (Line {r[1]}): {r[2]}")
