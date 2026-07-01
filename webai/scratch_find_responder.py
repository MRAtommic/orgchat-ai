with open('templates/index.html', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'การตั้งค่า AI ตอบกลับ' in line or 'Groq Llama' in line or 'auto_responder_enabled' in line:
            print(f"{idx}: {line.strip()[:150]}")
