# -*- coding: utf-8 -*-
import os

def fix_ch3_clearpage(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    target = r"\section{ผังงานกระบวนการประมวลผลของระบบ (Process Flowcharts)}"
    replacement = r"\clearpage" + "\n" + target
    if "\clearpage\n" + target not in content:
        content = content.replace(target, replacement)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_ch3_clearpage(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Project_030_Chapter3.tex')
fix_ch3_clearpage(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT\Project_030_Chapter3.tex')

print("Added clearpage before Section 3.8 in Chapter 3 successfully!")
