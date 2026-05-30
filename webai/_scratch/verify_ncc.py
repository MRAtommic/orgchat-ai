# -*- coding: utf-8 -*-
import fitz
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ทดสอบ พงด\ใบกำกับ"

def inspect_ncc(filename):
    filepath = os.path.join(pdf_dir, filename)
    print(f"\n===== Inspecting {filename} =====")
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    
    # print lines containing specific patterns
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        if any(k in line.lower() for k in ["เลขที่", "วันที่", "document no", "date", "no.", "ref", "0305700"]):
            print(f"  {line}")

inspect_ncc("242000096430102026(1) (2).pdf")
inspect_ncc("242000150430102026 (2).pdf")
