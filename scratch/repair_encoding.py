import os

file_path = r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ai_providers.py'
if os.path.exists(file_path):
    try:
        # Read with ignore to strip corrupt bytes
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Write back as clean UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully repaired UTF-8 encoding in ai_providers.py")
    except Exception as e:
        print(f"Error repairing file: {e}")
else:
    print("File not found.")
