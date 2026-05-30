with open("routes/chat.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "/api/chat" in line or "private_messages" in line:
            print(f"Line {i+1}: {line.strip()[:100]}")
