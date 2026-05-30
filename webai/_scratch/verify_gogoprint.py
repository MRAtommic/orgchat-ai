# -*- coding: utf-8 -*-
import fitz
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ทดสอบ พงด\ใบกำกับ\IN-2602004674 (2).pdf"
doc = fitz.open(pdf_path)
print("===== IN-2602004674 (2).pdf =====")
text = ""
for page in doc:
    text += page.get_text()
print(text)
