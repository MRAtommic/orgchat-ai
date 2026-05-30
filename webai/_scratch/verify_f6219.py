# -*- coding: utf-8 -*-
import fitz
import os
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ทดสอบ พงด\ใบกำกับ"

def check_pdf(filename, search_terms=None):
    filepath = os.path.join(pdf_dir, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filename}")
        return
    print(f"\n===== Inspecting {filename} =====")
    doc = fitz.open(filepath)
    text = ""
    for p in doc:
        text += p.get_text()
    
    print("Full Extracted Text:")
    print(text)
    
    if search_terms:
        print("\nSearch results:")
        for term in search_terms:
            matches = text.count(term)
            print(f"  '{term}': {matches} matches")

check_pdf("F6219_(20-02-69) (1).pdf")
