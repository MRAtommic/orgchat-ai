with open("../templates/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "สร้างกลุ่มใหม่" in line or "เลือกบทสนทนา" in line or "พิมพ์ข้อความของคุณที่นี่" in line:
        print(f"Match on line {i+1}: {line.strip()[:100]}")
        # Write context (30 lines before and 100 lines after)
        start = max(0, i - 30)
        end = min(len(lines), i + 150)
        with open("messenger_context.html", "w", encoding="utf-8") as out:
            for idx in range(start, end):
                out.write(f"{idx+1}: {lines[idx]}")
        print("Saved context to messenger_context.html successfully.")
        break
