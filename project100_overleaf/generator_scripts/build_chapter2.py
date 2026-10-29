import json
import os
import re
from latex_helpers import escape_latex, format_table_tabularx

out_dir = r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT"

with open(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\docx_dump.json", "r", encoding="utf-8") as f:
    docx_data = json.load(f)

paragraphs = docx_data["paragraphs"]
tables = docx_data["tables"]

# Table 2-1 (Table 4)
t4_raw = tables[4]
t4_headers = t4_raw[0]
t4_rows = []
for r in t4_raw[1:]:
    clean_r = []
    for c in r:
        val = c.replace('✓', r'$\checkmark$').replace('✗', r'$\times$')
        clean_r.append(val)
    t4_rows.append(clean_r)

# Custom col spec for Table 2-1: 6 columns
t2_1_tex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{\\fontSixTeen ตารางเปรียบเทียบคุณสมบัติระบบที่พัฒนากับแอปพลิเคชันอื่นในท้องตลาด}}
\\label{{tab2:comparison}}
\\fontSixTeen
\\begin{{tabularx}}{{\\textwidth}}{{| X | c | c | c | c | c |}}
\\hline
\\textbf{{{escape_latex(t4_headers[0])}}} & \\textbf{{{escape_latex(t4_headers[1])}}} & \\textbf{{{escape_latex(t4_headers[2])}}} & \\textbf{{{escape_latex(t4_headers[3])}}} & \\textbf{{{escape_latex(t4_headers[4])}}} & \\textbf{{{escape_latex(t4_headers[5])}}} \\\\ \\hline
"""
for r in t4_rows:
    t2_1_tex += f"{escape_latex(r[0])} & {r[1]} & {r[2]} & {r[3]} & {r[4]} & {r[5]} \\\\ \\hline\n"
t2_1_tex += """\\end{tabularx}
\\end{table}
"""

# Now build sections of Chapter 2
ch2_lines = [
    "%*************************************",
    "% บทที่ 2",
    "%*************************************",
    r"\chapterTitle{2}{แนวคิด ทฤษฎี และงานวิจัยที่เกี่ยวข้อง}",
    r"\vspace{0.2in}",
    r"\hspace*{1.3em}",
    escape_latex(paragraphs[298]),
]

for i in range(299, 354):
    p = paragraphs[i].strip()
    if not p:
        continue
    
    # Check if section
    if p.startswith("2.") and (" " in p):
        num_part = p.split(" ")[0]
        title_part = " ".join(p.split(" ")[1:])
        dots = num_part.count(".")
        if dots == 1:
            ch2_lines.append(f"\n\\section{{{escape_latex(title_part)}}}")
        elif dots == 2:
            ch2_lines.append(f"\n\\subsection{{{escape_latex(title_part)}}}")
        elif dots == 3:
            ch2_lines.append(f"\n\\subsubsection{{{escape_latex(title_part)}}}")
        else:
            ch2_lines.append(f"\n\\paragraph{{{escape_latex(title_part)}}}")
    elif p.startswith("ภาพที่ 2"):
        # Figure 2-1
        ch2_lines.append(r"""\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{Image/fig2_1_architecture.png}
\caption{\fontSixTeen{สถาปัตยกรรมระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร (System Architecture Diagram)}}
\label{fig2:architecture}
\end{figure}
""")
    elif p.startswith("ตารางที่ 2"):
        # Table 2-1
        ch2_lines.append(t2_1_tex)
    else:
        # Regular text or bullet
        if p.startswith("•"):
            ch2_lines.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', ''))}\n\\end{{mycustomitem}}")
        else:
            ch2_lines.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")

ch2_tex = "\n".join(ch2_lines)

with open(os.path.join(out_dir, "Project_020_Chapter2.tex"), "w", encoding="utf-8") as f:
    f.write(ch2_tex)
print("Successfully generated Project_020_Chapter2.tex")
