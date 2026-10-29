import json
import os
import re
from latex_helpers import escape_latex, format_table_tabularx

out_dir = r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT"

with open(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\docx_dump.json", "r", encoding="utf-8") as f:
    docx_data = json.load(f)

paragraphs = docx_data["paragraphs"]
tables = docx_data["tables"]

def make_fig(path, caption, label, width="0.95\\textwidth"):
    return f"""\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width={width}]{{{path}}}
\\caption{{\\fontSixTeen{{{escape_latex(caption)}}}}}
\\label{{{label}}}
\\end{{figure}}
"""

# =============================================================================
# BUILD CHAPTER 3
# =============================================================================
ch3_lines = [
    "%*************************************",
    "% บทที่ 3",
    "%*************************************",
    r"\chapterTitle{3}{วิธีการดำเนินงานและการออกแบบระบบ}",
    r"\vspace{0.2in}",
    r"\hspace*{1.3em}",
    escape_latex(paragraphs[356]),
]

# Map paragraph index to action in Chapter 3
table_map_ch3 = {
    383: (5, "ตารางที่ 3 - 1 รายการ Data Flow Description ข้อมูลผู้ใช้งานที่เข้าสู่ระบบ", "tab3:df1", "| c | X |"),
    385: (6, "ตารางที่ 3 - 2 รายการ Data Flow Description ข้อมูลคำถามจากผู้ใช้ผ่าน LINE", "tab3:df2", "| c | X |"),
    387: (7, "ตารางที่ 3 - 3 รายการ Data Flow Description ข้อมูลภาพถ่ายสลิปโอนเงินและใบเสร็จ", "tab3:df3", "| c | X |"),
    389: (8, "ตารางที่ 3 - 4 รายการ Data Flow Description ข้อมูลคำขอลางานของพนักงาน", "tab3:df4", "| c | X |"),
    391: (9, "ตารางที่ 3 - 5 รายการ Data Flow Description ผลการอนุมัติคำขอลางานจากหัวหน้างาน", "tab3:df5", "| c | X |"),
    395: (10, "ตารางที่ 3 - 6 รายการ Data Store ของระบบ OrgChat AI", "tab3:datastore", "| c | c | c | X |"),
    424: (11, "ตารางที่ 3 - 7 ตารางรายการตารางข้อมูลในระบบฐานข้อมูล (Table List)", "tab3:tablelist", "| c | X | c | c |"),
    427: (12, "ตารางที่ 3 - 8 โครงสร้างตารางข้อมูล users (ผู้ใช้งานระบบ)", "tab3:tb_users", "| c | c | c | c | c | X |"),
    429: (13, "ตารางที่ 3 - 9 โครงสร้างตารางข้อมูล organizations (ข้อมูลองค์กร)", "tab3:tb_orgs", "| c | c | c | c | c | X |"),
    431: (14, "ตารางที่ 3 - 10 โครงสร้างตารางข้อมูล user_leave_quotas (โควตาวันลาพนักงาน)", "tab3:tb_quotas", "| c | c | c | c | c | X |"),
    433: (15, "ตารางที่ 3 - 11 โครงสร้างตารางข้อมูล leave_requests (รายการขอลางาน)", "tab3:tb_leaves", "| c | c | c | c | c | X |"),
    435: (16, "ตารางที่ 3 - 12 โครงสร้างตารางข้อมูล audit_logs (บันทึกประวัติการใช้งานระบบ)", "tab3:tb_audits", "| c | c | c | c | c | X |"),
    437: (17, "ตารางที่ 3 - 13 โครงสร้างตารางข้อมูล drive_logs (บันทึกเอกสารและสลิปการเงิน)", "tab3:tb_drives", "| c | c | c | c | c | X |"),
}

fig_map_ch3 = {
    375: ("Image/fig3_1_context.png", "Context Diagram ของระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร", "fig3:context"),
    379: ("Image/fig3_2_dfd.png", "Data Flow Diagram (DFD) Level 0/1 ภาพรวมการทำงานของระบบ", "fig3:dfd"),
    402: ("Image/fig3_3_flow_auth.png", "Flowchart ขั้นตอนการเข้าสู่ระบบและการยืนยันตัวตน", "fig3:flow_auth"),
    406: ("Image/fig3_4_flow_leave_approve.png", "Flowchart ขั้นตอนการอนุมัติคำขอลางาน", "fig3:flow_leave_approve"),
    410: ("Image/fig3_5_flow_leave_request.png", "Flowchart ขั้นตอนการยื่นคำขอลางานของพนักงาน", "fig3:flow_leave_request"),
    414: ("Image/fig3_6_flow_rag.png", "Flowchart ขั้นตอนการทำงานของระบบคลังความรู้ RAG", "fig3:flow_rag"),
    418: ("Image/fig3_7_flow_ocr.png", "Flowchart ขั้นตอนการประมวลผลสลิป/ใบเสร็จ OCR และบันทึกบัญชีอัตโนมัติ", "fig3:flow_ocr"),
    422: ("Image/fig3_8_er_diagram.png", "Entity Relationship Diagram (ER Diagram) ของระบบ OrgChat AI", "fig3:er_diagram"),
    442: ("Image/fig3_9_screen_flow.png", "แผนผังลำดับการทำงานของหน้าจอ (Screen Flow Diagram)", "fig3:screen_flow"),
}

for i in range(357, 450):
    p = paragraphs[i].strip()
    if not p:
        continue
    
    # Check if table
    if i in table_map_ch3:
        t_idx, cap, lbl, col_spec = table_map_ch3[i]
        tbl = tables[t_idx]
        t_tex = format_table_tabularx(tbl[0], tbl[1:], cap, lbl, col_spec)
        ch3_lines.append(t_tex)
        continue
    
    # Check if figure
    if i in fig_map_ch3:
        img_p, cap, lbl = fig_map_ch3[i]
        ch3_lines.append(make_fig(img_p, cap, lbl))
        continue
    
    # Skip figure/table captions if already handled
    if p.startswith("ตารางที่ 3") or p.startswith("ภาพที่ 3"):
        continue

    # Check headings
    if p.startswith("3.") and (" " in p):
        num_part = p.split(" ")[0]
        title_part = " ".join(p.split(" ")[1:])
        dots = num_part.count(".")
        if dots == 1:
            ch3_lines.append(f"\n\\section{{{escape_latex(title_part)}}}")
        elif dots == 2:
            ch3_lines.append(f"\n\\subsection{{{escape_latex(title_part)}}}")
        elif dots == 3:
            ch3_lines.append(f"\n\\subsubsection{{{escape_latex(title_part)}}}")
        else:
            ch3_lines.append(f"\n\\paragraph{{{escape_latex(title_part)}}}")
    else:
        if p.startswith("•"):
            ch3_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', ''))}\n\\end{{mycustomitem}}")
        else:
            ch3_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_030_Chapter3.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(ch3_lines))
print("Successfully generated Project_030_Chapter3.tex")

# =============================================================================
# BUILD CHAPTER 4
# =============================================================================
ch4_lines = [
    "%*************************************",
    "% บทที่ 4",
    "%*************************************",
    r"\chapterTitle{4}{ผลการดำเนินงานและการทดสอบระบบ}",
    r"\vspace{0.2in}",
    r"\hspace*{1.3em}",
    escape_latex(paragraphs[451]),
]

# Table 4-1 to 4-4
t4_1_tex = format_table_tabularx(
    tables[18][0], tables[18][1:],
    "สรุปผลการทดสอบเชิงหน้าที่ (Functional Testing Test Cases)",
    "tab4:functional",
    col_spec="| c | c | X | X | c |"
)

t4_2_tex = format_table_tabularx(
    tables[19][0], tables[19][1:],
    "ผลการทดสอบประสิทธิภาพและความแม่นยำของระบบ OCR สลิปและใบเสร็จ (50 ตัวอย่าง)",
    "tab4:ocr",
    col_spec="| X | c | c | c | c |"
)

t4_3_tex = format_table_tabularx(
    tables[20][0], tables[20][1:],
    "ผลการทดสอบความถูกต้องในการสืบค้นและตอบคำถามของระบบ RAG (50 ข้อ)",
    "tab4:rag",
    col_spec="| X | c | c | c | c |"
)

t21_clean_rows = []
for r in tables[21][1:]:
    t21_clean_rows.append([c.replace("X̄", r"$\bar{X}$") for c in r])
t21_headers = [c.replace("X̄", r"$\bar{X}$") for c in tables[21][0]]
t4_4_tex = format_table_tabularx(
    t21_headers, t21_clean_rows,
    "ผลการประเมินความพึงพอใจของผู้ใช้งานระบบ บริษัท ฮาร์ทวอมมิ่ง จำกัด (N = 20)",
    "tab4:satisfaction",
    col_spec="| c | X | c | c | c |"
)

table_map_ch4 = {
    486: t4_1_tex,
    490: t4_2_tex,
    494: t4_3_tex,
    502: t4_4_tex,
}

fig_map_ch4 = {
    463: ("Image/fig4_1_login.png", "หน้าจอเข้าสู่ระบบและสมัครสมาชิกผ่านเว็บแอปพลิเคชัน", "fig4:login"),
    471: ("Image/fig4_2_line_rag.png", "หน้าจอสนทนา LINE Official Account ถามตอบข้อมูลสินค้าด้วย RAG", "fig4:line_rag"),
    481: ("Image/fig4_3_dashboard.png", "หน้าจอแผงควบคุมผู้บริหาร (Admin Dashboard) สรุปภาพรวมและสถิติองค์กร", "fig4:dashboard"),
}

for i in range(452, 504):
    p = paragraphs[i].strip()
    if not p:
        continue
    
    if i in table_map_ch4:
        ch4_lines.append(table_map_ch4[i])
        continue
    
    if i in fig_map_ch4:
        img_p, cap, lbl = fig_map_ch4[i]
        ch4_lines.append(make_fig(img_p, cap, lbl))
        continue
        
    if p.startswith("ตารางที่ 4") or p.startswith("ภาพที่ 4"):
        continue

    if p.startswith("4.") and (" " in p):
        num_part = p.split(" ")[0]
        title_part = " ".join(p.split(" ")[1:])
        dots = num_part.count(".")
        if dots == 1:
            ch4_lines.append(f"\n\\section{{{escape_latex(title_part)}}}")
        elif dots == 2:
            ch4_lines.append(f"\n\\subsection{{{escape_latex(title_part)}}}")
        elif dots == 3:
            ch4_lines.append(f"\n\\subsubsection{{{escape_latex(title_part)}}}")
        else:
            ch4_lines.append(f"\n\\paragraph{{{escape_latex(title_part)}}}")
    else:
        if p.startswith("•"):
            ch4_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', ''))}\n\\end{{mycustomitem}}")
        else:
            ch4_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_040_Chapter4.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(ch4_lines))
print("Successfully generated Project_040_Chapter4.tex")

# =============================================================================
# BUILD CHAPTER 5
# =============================================================================
ch5_lines = [
    "%*************************************",
    "% บทที่ 5",
    "%*************************************",
    r"\chapterTitle{5}{สรุปผลการดำเนินงาน ปัญหาอุปสรรค และข้อเสนอแนะ}",
    r"\vspace{0.2in}",
]

for i in range(505, 532):
    p = paragraphs[i].strip()
    if not p:
        continue
    
    if p.startswith("5.") and (" " in p):
        num_part = p.split(" ")[0]
        title_part = " ".join(p.split(" ")[1:])
        dots = num_part.count(".")
        if dots == 1:
            ch5_lines.append(f"\n\\section{{{escape_latex(title_part)}}}")
        elif dots == 2:
            ch5_lines.append(f"\n\\subsection{{{escape_latex(title_part)}}}")
        elif dots == 3:
            ch5_lines.append(f"\n\\subsubsection{{{escape_latex(title_part)}}}")
    else:
        if p.startswith("•"):
            ch5_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', ''))}\n\\end{{mycustomitem}}")
        else:
            ch5_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_050_Chapter5.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(ch5_lines))
print("Successfully generated Project_050_Chapter5.tex")

# =============================================================================
# BUILD APPENDIX A
# =============================================================================
app_a_lines = [
    "%*************************************",
    "% ภาคผนวก ก.",
    "%*************************************",
    r"\appendixChapterTitle{ก}{คู่มือการติดตั้งและใช้งานระบบ}",
    r"\section{คู่มือการติดตั้งและใช้งานระบบ}",
    r"\vspace{0.5em}",
]

for i in range(547, 554):
    p = paragraphs[i].strip()
    if not p:
        continue
    if p.startswith("ก."):
        app_a_lines.append(f"\n\\subsection{{{escape_latex(p)}}}")
    elif p.startswith("•"):
        app_a_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', ''))}\n\\end{{mycustomitem}}")
    else:
        app_a_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_101_AppendixA.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(app_a_lines))
print("Successfully generated Project_101_AppendixA.tex")

# =============================================================================
# BUILD APPENDIX B
# =============================================================================
t22_tex = format_table_tabularx(
    tables[22][0], tables[22][1:],
    "แบบสอบถามการประเมินความพึงพอใจของผู้ใช้งาน",
    "tabB:survey",
    col_spec="| c | X | c | c | c | c | c |"
)

app_b_lines = [
    "%*************************************",
    "% ภาคผนวก ข.",
    "%*************************************",
    r"\appendixChapterTitle{ข}{แบบสอบถามประเมินความพึงพอใจและประวัติผู้จัดทำ}",
    r"\section{แบบสอบถามการประเมินความพึงพอใจของผู้ใช้งาน}",
    r"\vspace{0.5em}",
    r"\hspace*{1.3em}",
    escape_latex(paragraphs[555]),
    r"\vspace{0.5em}",
    r"\hspace*{1.3em}",
    escape_latex(paragraphs[556]),
    t22_tex,
    r"\section{ประวัติผู้จัดทำโครงงาน}",
    r"\vspace{0.5em}",
]

for i in range(558, len(paragraphs)):
    p = paragraphs[i].strip()
    if not p:
        continue
    if p.startswith("ประวัติ"):
        continue
    if re.match(r"^\d+\.", p):
        app_b_lines.append(f"\n\\subsection{{{escape_latex(p)}}}")
    elif p.startswith("•"):
        app_b_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', ''))}\n\\end{{mycustomitem}}")
    else:
        app_b_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_102_AppendixB.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(app_b_lines))
print("Successfully generated Project_102_AppendixB.tex")
