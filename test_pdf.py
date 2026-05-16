import os
from ai_providers import analyze_image_contents

pdf_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\ร้านค้าช่องทางต่างๆ (2).pdf"

with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

print("Analyzing PDF...")
result = analyze_image_contents(pdf_bytes, "application/pdf")
print("Result:", result)
