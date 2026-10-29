# -*- coding: utf-8 -*-
import os

def fix_chapter3(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add \clearpage before section 3.5
    target_pspec = r"\section{การกำหนดลักษณะการประมวลผล (Process Specification : PSPEC)}"
    replacement_pspec = r"\clearpage" + "\n" + r"\section{การกำหนดลักษณะการประมวลผล (Process Specification : PSPEC)}"
    if "\clearpage\n" + target_pspec not in content:
        content = content.replace(target_pspec, replacement_pspec)

    # 2. Fix unescaped drive_file_id and drive_url
    target_drive = r"ข้อมูลส่งออก (Output) & รหัสไฟล์บน Drive (drive_file_id), ลิงก์เข้าถึงเอกสาร (drive_url) \\ \hline"
    replacement_drive = r"ข้อมูลส่งออก (Output) & รหัสไฟล์บน Drive (\texttt{drive\_file\_id}), ลิงก์เข้าถึงเอกสาร (\texttt{drive\_url}) \\ \hline"
    content = content.replace(target_drive, replacement_drive)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_chapter3(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Project_030_Chapter3.tex')
fix_chapter3(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT\Project_030_Chapter3.tex')

print("Chapter 3 updated with fixes successfully!")
