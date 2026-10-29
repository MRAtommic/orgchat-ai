# -*- coding: utf-8 -*-
import os

def update_main_lot_fix(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # In project_report.cls, LOT continuation header often comes from a macro or fancyhdr
    # We can provide header override right before \customLOTthai
    target = r"\customLOTthai"
    replacement = r"""\fancyhead[C]{\textbf{สารบัญตาราง (ต่อ)}\\[4pt]\textbf{ตารางที่}\hfill\textbf{หน้า}}
    \customLOTthai"""
    if r"\textbf{สารบัญตาราง (ต่อ)}" not in content:
        content = content.replace(target, replacement)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

update_main_lot_fix(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Main.tex')
update_main_lot_fix(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT\Main.tex')

print("Main.tex updated with LOT header fix!")
