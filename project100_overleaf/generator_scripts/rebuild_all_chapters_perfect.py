import json
import os
import re
from latex_helpers import escape_latex, clean_caption, format_table_tabularx

out_dir = r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT"

with open(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\docx_dump.json", "r", encoding="utf-8") as f:
    docx_data = json.load(f)

paragraphs = docx_data["paragraphs"]
tables = docx_data["tables"]

def make_fig(path, caption, label, width="0.95\\textwidth"):
    c = clean_caption(caption)
    return f"""\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width={width}]{{{path}}}
\\caption{{{escape_latex(c)}}}
\\label{{{label}}}
\\end{{figure}}
"""

# =============================================================================
# REBUILD CHAPTER 2
# =============================================================================
t4_raw = tables[4]
t4_headers = t4_raw[0]

header_0 = escape_latex(t4_headers[0])
header_1 = "ระบบที่พัฒนา\\ (OrgChat)"
header_2 = escape_latex(t4_headers[2])
header_3 = escape_latex(t4_headers[3])
header_4 = "ChatGPT\\ Ent."
header_5 = "LINE\\ WORKS"

t2_1_tex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{ตารางเปรียบเทียบคุณสมบัติระบบที่พัฒนากับแอปพลิเคชันอื่นในท้องตลาด}}
\\label{{tab2:comparison}}
\\begin{{tabularx}}{{\\textwidth}}{{| >{{\\RaggedRight\\arraybackslash}}p{{4.8cm}} | >{{\\centering\\arraybackslash}}p{{1.7cm}} | >{{\\centering\\arraybackslash}}p{{1.4cm}} | >{{\\centering\\arraybackslash}}p{{1.5cm}} | >{{\\centering\\arraybackslash}}p{{1.7cm}} | >{{\\centering\\arraybackslash}}p{{1.6cm}} |}}
\\hline
\\textbf{{{header_0}}} & \\textbf{{{header_1}}} & \\textbf{{{header_2}}} & \\textbf{{{header_3}}} & \\textbf{{{header_4}}} & \\textbf{{{header_5}}} \\\\ \\hline
"""

for r in t4_raw[1:]:
    feat = escape_latex(r[0])
    c1 = r"\cmark" if r[1] == '✓' else r"\xmark"
    c2 = r"\cmark" if r[2] == '✓' else r"\xmark"
    c3 = r"\cmark" if r[3] == '✓' else r"\xmark"
    c4 = r"\cmark" if r[4] == '✓' else r"\xmark"
    c5 = r"\cmark" if r[5] == '✓' else r"\xmark"
    t2_1_tex += f"{feat} & {c1} & {c2} & {c3} & {c4} & {c5} \\\\ \\hline\n"

t2_1_tex += """\\end{tabularx}
\\end{table}
"""

ch2_lines = [
    "%*************************************",
    "% บทที่ 2",
    "%*************************************",
    r"\chapterTitle{2}{แนวคิด ทฤษฎี และงานวิจัยที่เกี่ยวข้อง}",
    r"\providecommand{\cmark}{\ensuremath{\surd}}",
    r"\providecommand{\xmark}{\ensuremath{\times}}",
    r"\vspace{0.2in}",
    r"\hspace*{1.3em}",
    escape_latex(paragraphs[298]),
    "",
    r"\begin{mycustomitem}",
]

for i in range(299, 307):
    p = paragraphs[i].strip()
    if p:
        clean_p = p.replace("• ", "").strip()
        ch2_lines.append(f"\\item {escape_latex(clean_p)}")
ch2_lines.append(r"\end{mycustomitem}")
ch2_lines.append("")

for i in range(307, 354):
    p = paragraphs[i].strip()
    if not p:
        continue
    
    sub_paras = [x.strip() for x in p.split("\n") if x.strip()]
    for sp in sub_paras:
        m_sec = re.match(r'^(2\.\d+)\s+(.*)$', sp)
        if m_sec and m_sec.group(1).count('.') == 1:
            title = m_sec.group(2).strip()
            ch2_lines.append(f"\n\\section{{{escape_latex(title)}}}\n")
            continue
        
        m_subsec = re.match(r'^(2\.\d+\.\d+)\s+(.*)$', sp)
        if m_subsec:
            rest = m_subsec.group(2).strip()
            # Split by colon after parenthesis or plain colon
            m_split = re.match(r'^(.*?\))\s*:\s*(.*)$', rest)
            if not m_split:
                m_split = re.match(r'^([^:]+)\s*:\s*(.*)$', rest)
            
            if m_split:
                title = m_split.group(1).strip()
                desc = m_split.group(2).strip()
                ch2_lines.append(f"\n\\subsection{{{escape_latex(title)}}}")
                ch2_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(desc)}\n")
            else:
                ch2_lines.append(f"\n\\subsection{{{escape_latex(rest)}}}\n")
            continue
        
        if sp.startswith("ภาพที่ 2"):
            ch2_lines.append(r"""\begin{figure}[htbp]
\\centering
\includegraphics[width=0.95\textwidth]{Image/fig2_1_architecture.png}
\caption{สถาปัตยกรรมระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร (System Architecture Diagram)}
\label{fig2:architecture}
\end{figure}
""")
            continue
        
        if sp.startswith("ตารางที่ 2"):
            ch2_lines.append(t2_1_tex)
            continue
        
        if sp.startswith("•"):
            ch2_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(sp.replace('• ', '').strip())}\n\\end{{mycustomitem}}")
        else:
            ch2_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(sp)}\n")

with open(os.path.join(out_dir, "Project_020_Chapter2.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(ch2_lines))
print("Rebuilt Project_020_Chapter2.tex")


# =============================================================================
# REBUILD CHAPTER 3
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

# Map paragraph index to action in Chapter 3 with clean captions & L columns
table_map_ch3 = {
    383: (5, "รายการ Data Flow Description ข้อมูลผู้ใช้งานที่เข้าสู่ระบบ", "tab3:df1", "| c | L |"),
    385: (6, "รายการ Data Flow Description ข้อมูลคำถามจากผู้ใช้ผ่าน LINE", "tab3:df2", "| c | L |"),
    387: (7, "รายการ Data Flow Description ข้อมูลภาพถ่ายสลิปโอนเงินและใบเสร็จ", "tab3:df3", "| c | L |"),
    389: (8, "รายการ Data Flow Description ข้อมูลคำขอลางานของพนักงาน", "tab3:df4", "| c | L |"),
    391: (9, "รายการ Data Flow Description ผลการอนุมัติคำขอลางานจากหัวหน้างาน", "tab3:df5", "| c | L |"),
    395: (10, "รายการ Data Store ของระบบ OrgChat AI", "tab3:datastore", "| c | c | c | L |"),
    424: (11, "ตารางรายการตารางข้อมูลในระบบฐานข้อมูล (Table List)", "tab3:tablelist", "| c | L | c | c |"),
    427: (12, "โครงสร้างตารางข้อมูล users (ผู้ใช้งานระบบ)", "tab3:tb_users", "| c | c | c | c | c | L |"),
    429: (13, "โครงสร้างตารางข้อมูล organizations (ข้อมูลองค์กร)", "tab3:tb_orgs", "| c | c | c | c | c | L |"),
    431: (14, "โครงสร้างตารางข้อมูล user_leave_quotas (โควตาวันลาพนักงาน)", "tab3:tb_quotas", "| c | c | c | c | c | L |"),
    433: (15, "โครงสร้างตารางข้อมูล leave_requests (รายการขอลางาน)", "tab3:tb_leaves", "| c | c | c | c | c | L |"),
    435: (16, "โครงสร้างตารางข้อมูล audit_logs (บันทึกประวัติการใช้งานระบบ)", "tab3:tb_audits", "| c | c | c | c | c | L |"),
    437: (17, "โครงสร้างตารางข้อมูล drive_logs (บันทึกเอกสารและสลิปการเงิน)", "tab3:tb_drives", "| c | c | c | c | c | L |"),
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
    
    if i in table_map_ch3:
        t_idx, cap, lbl, col_spec = table_map_ch3[i]
        tbl = tables[t_idx]
        t_tex = format_table_tabularx(tbl[0], tbl[1:], cap, lbl, col_spec)
        ch3_lines.append(t_tex)
        continue
    
    if i in fig_map_ch3:
        img_p, cap, lbl = fig_map_ch3[i]
        ch3_lines.append(make_fig(img_p, cap, lbl))
        continue
    
    if p.startswith("ตารางที่ 3") or p.startswith("ภาพที่ 3"):
        continue

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
            ch3_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', '').strip())}\n\\end{{mycustomitem}}")
        else:
            ch3_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_030_Chapter3.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(ch3_lines))
print("Rebuilt Project_030_Chapter3.tex")


# =============================================================================
# REBUILD CHAPTER 4
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

t4_1_tex = format_table_tabularx(
    tables[18][0], tables[18][1:],
    "สรุปผลการทดสอบเชิงหน้าที่ (Functional Testing Test Cases)",
    "tab4:functional",
    col_spec="| c | c | L | L | c |"
)

t4_2_tex = format_table_tabularx(
    tables[19][0], tables[19][1:],
    "ผลการทดสอบประสิทธิภาพและความแม่นยำของระบบ OCR สลิปและใบเสร็จ (50 ตัวอย่าง)",
    "tab4:ocr",
    col_spec="| L | c | c | c | c |"
)

t4_3_tex = format_table_tabularx(
    tables[20][0], tables[20][1:],
    "ผลการทดสอบความถูกต้องในการสืบค้นและตอบคำถามของระบบ RAG (50 ข้อ)",
    "tab4:rag",
    col_spec="| L | c | c | c | c |"
)

t21_clean_rows = []
for r in tables[21][1:]:
    t21_clean_rows.append([c.replace("X̄", r"$\bar{X}$") for c in r])
t21_headers = [c.replace("X̄", r"$\bar{X}$") for c in tables[21][0]]
t4_4_tex = format_table_tabularx(
    t21_headers, t21_clean_rows,
    "ผลการประเมินความพึงพอใจของผู้ใช้งานระบบ บริษัท ฮาร์ทวอมมิ่ง จำกัด (N = 20)",
    "tab4:satisfaction",
    col_spec="| c | L | c | c | c |"
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
            ch4_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', '').strip())}\n\\end{{mycustomitem}}")
        else:
            ch4_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_040_Chapter4.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(ch4_lines))
print("Rebuilt Project_040_Chapter4.tex")


# =============================================================================
# REBUILD APPENDIX B
# =============================================================================
t22_tex = format_table_tabularx(
    tables[22][0], tables[22][1:],
    "แบบสอบถามการประเมินความพึงพอใจของผู้ใช้งาน",
    "tabB:survey",
    col_spec="| c | L | c | c | c | c | c |"
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
        app_b_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', '').strip())}\n\\end{{mycustomitem}}")
    else:
        app_b_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

with open(os.path.join(out_dir, "Project_102_AppendixB.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(app_b_lines))
print("Rebuilt Project_102_AppendixB.tex")
