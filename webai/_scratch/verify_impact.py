# -*- coding: utf-8 -*-
import fitz
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ทดสอบ พงด\ใบกำกับ\IM2600000876-บริษัท_ฮาร์ทวอมมิ่ง_จำกัด(00058138)CNX050.pdf"
doc = fitz.open(pdf_path)
print("===== IM2600000876 =====")
text = ""
for page in doc:
    text += page.get_text()
print(text[:1200])
