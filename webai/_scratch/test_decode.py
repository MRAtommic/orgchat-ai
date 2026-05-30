try:
    with open(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\routes\chat.py", "r", encoding="cp874") as f:
        content = f.read()
    print("SUCCESS: File decoded perfectly using CP874!")
except Exception as e:
    print(f"FAILED to decode using CP874: {e}")
