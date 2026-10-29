import json
import os
import re
from latex_helpers import escape_latex

out_dir = r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT"

with open(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\docx_dump.json", "r", encoding="utf-8") as f:
    docx_data = json.load(f)

paragraphs = docx_data["paragraphs"]
tables = docx_data["tables"]

# Table 2-1 (Table 4)
t4_raw = tables[4]
t4_headers = t4_raw[0]

# Wrap column headers nicely
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
]

# Add the overview list (2.1 to 2.10)
ch2_lines.append(r"\begin{mycustomitem}")
for i in range(299, 307):
    p = paragraphs[i].strip()
    if p:
        clean_p = p.replace("• ", "").strip()
        ch2_lines.append(f"\\item {escape_latex(clean_p)}")
ch2_lines.append(r"\end{mycustomitem}")
ch2_lines.append("")

def process_para(p_text):
    lines_out = []
    # If contains newline, split
    sub_paras = [x.strip() for x in p_text.split("\n") if x.strip()]
    for p in sub_paras:
        # Check if major section (2.1, 2.2, ..., 2.10)
        m_sec = re.match(r'^(2\.\d+)\s+(.*)$', p)
        if m_sec and m_sec.group(1).count('.') == 1:
            title = m_sec.group(2).strip()
            lines_out.append(f"\n\\section{{{escape_latex(title)}}}\n")
            continue
        
        # Check if subsection (2.X.Y)
        m_subsec = re.match(r'^(2\.\d+\.\d+)\s+(.*)$', p)
        if m_subsec:
            rest = m_subsec.group(2).strip()
            # Split by colon if present
            if ':' in rest:
                title, desc = rest.split(':', 1)
                lines_out.append(f"\n\\subsection{{{escape_latex(title.strip())}}}")
                lines_out.append(f"\\hspace*{{1.3em}}\n{escape_latex(desc.strip())}\n")
            else:
                lines_out.append(f"\n\\subsection{{{escape_latex(rest)}}}\n")
            continue
        
        # Check if figure
        if p.startswith("ภาพที่ 2"):
            lines_out.append(r"""\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{Image/fig2_1_architecture.png}
\caption{สถาปัตยกรรมระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร (System Architecture Diagram)}
\label{fig2:architecture}
\end{figure}
""")
            continue
        
        # Check if table
        if p.startswith("ตารางที่ 2"):
            lines_out.append(t2_1_tex)
            continue
        
        # Bullet list item
        if p.startswith("•"):
            lines_out.append(f"\\begin{{mycustomitem}}\n\\item {escape_latex(p.replace('• ', '').strip())}\n\\end{{mycustomitem}}")
        else:
            lines_out.append(f"\\hspace*{{1.3em}}\n{escape_latex(p)}\n")
    return lines_out

# Process remaining paragraphs 307 to 353
for i in range(307, 354):
    p = paragraphs[i].strip()
    if not p:
        continue
    res = process_para(p)
    ch2_lines.extend(res)

with open(os.path.join(out_dir, "Project_020_Chapter2.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(ch2_lines))

print("Successfully rebuilt Project_020_Chapter2.tex with clean subsections and fixed Table 2-1!")
