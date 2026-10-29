import json
import os
from latex_helpers import escape_latex, format_table_tabularx

out_dir = r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT"

with open(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\docx_dump.json", "r", encoding="utf-8") as f:
    docx_data = json.load(f)

paragraphs = docx_data["paragraphs"]
tables = docx_data["tables"]

# Format Table 1-1 (Budget)
t1_1_rows = tables[2][1:]
t1_1_headers = tables[2][0]
t1_1_tex = format_table_tabularx(
    t1_1_headers,
    t1_1_rows,
    "งบประมาณโดยประมาณที่ใช้ในการดำเนินงาน",
    "tab1:budget",
    col_spec="| c | L | c |"
)

# Format Table 1-2 (Timeline)
t1_2_rows = tables[3][1:]
t1_2_headers = tables[3][0]
t1_2_tex = format_table_tabularx(
    t1_2_headers,
    t1_2_rows,
    "แผนและระยะเวลาการดำเนินงานโครงงานพิเศษตลอดปีการศึกษา 2569",
    "tab1:timeline",
    col_spec="| c | L | c | c | L |"
)

ch1_tex = rf"""%*************************************
% บทที่ 1
%*************************************
\chapterTitle{{1}}{{บทนำ}}

\section{{ความเป็นมาและความสำคัญของปัญหา}}
\hspace*{{1.3em}}
{escape_latex(paragraphs[209])}

\hspace*{{1.3em}}
{escape_latex(paragraphs[210])}

\hspace*{{1.3em}}
{escape_latex(paragraphs[211])}

\hspace*{{1.3em}}
{escape_latex(paragraphs[212])}

\section{{วัตถุประสงค์ของโครงงาน}}
\begin{{mycustomenum}}[label=1.2.\arabic*]
    \item {escape_latex(paragraphs[215].replace('• 1.2.1 ', ''))}
    \item {escape_latex(paragraphs[216].replace('• 1.2.2 ', ''))}
    \item {escape_latex(paragraphs[217].replace('• 1.2.3 ', ''))}
    \item {escape_latex(paragraphs[218].replace('• 1.2.4 ', ''))}
    \item {escape_latex(paragraphs[219].replace('• 1.2.5 ', ''))}
\end{{mycustomenum}}

\section{{ขอบเขตของโครงงาน}} \label{{sec1:scope}}
\hspace*{{1.3em}}
{escape_latex(paragraphs[221])}

\subsection{{ขอบเขตการดำเนินงานภาคการศึกษาที่ 1/2569 (ระบบคลังความรู้ RAG และ LINE Integration)}}
\begin{{mycustomitem}}
    \item \textbf{{ด้านระบบจัดการผู้ใช้และสิทธิ์การเข้าถึง (Authentication \& RBAC):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[224].replace('• • ', ''))}
        \item {escape_latex(paragraphs[225].replace('• • ', ''))}
        \item {escape_latex(paragraphs[226].replace('• • ', ''))}
        \item {escape_latex(paragraphs[227].replace('• • ', ''))}
        \item {escape_latex(paragraphs[228].replace('• • ', ''))}
    \end{{mycustomitem}}

    \item \textbf{{ด้านระบบคลังความรู้อัจฉริยะ (RAG System \& Knowledge Base):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[230].replace('• • ', ''))}
        \item {escape_latex(paragraphs[231].replace('• • ', ''))}
        \item {escape_latex(paragraphs[232].replace('• • ', ''))}
        \item {escape_latex(paragraphs[233].replace('• • ', ''))}
        \item {escape_latex(paragraphs[234].replace('• • ', ''))}
        \item {escape_latex(paragraphs[235].replace('• • ', ''))}
        \item {escape_latex(paragraphs[236].replace('• • ', ''))}
    \end{{mycustomitem}}

    \item \textbf{{ด้านระบบจัดการและจัดเก็บเอกสารองค์กร (Document Management):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[238].replace('• • ', ''))}
        \item {escape_latex(paragraphs[239].replace('• • ', ''))}
        \item {escape_latex(paragraphs[240].replace('• • ', ''))}
    \end{{mycustomitem}}

    \item \textbf{{ด้านระบบเชื่อมต่อแพลตฟอร์ม LINE (LINE Platform Integration):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[242].replace('• • ', ''))}
        \item {escape_latex(paragraphs[243].replace('• • ', ''))}
    \end{{mycustomitem}}
\end{{mycustomitem}}

\subsection{{ขอบเขตการดำเนินงานภาคการศึกษาที่ 2/2569 (ระบบการเงิน OCR, บริหารงานบุคคล และแดชบอร์ด)}}
\begin{{mycustomitem}}
    \item \textbf{{ด้านระบบจัดการการเงินและบัญชีอัตโนมัติ (Financial \& Bookkeeping Automation):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[246].replace('• • ', ''))}
        \item {escape_latex(paragraphs[247].replace('• • ', ''))}
        \item {escape_latex(paragraphs[248].replace('• • ', ''))}
        \item {escape_latex(paragraphs[249].replace('• • ', ''))}
    \end{{mycustomitem}}

    \item \textbf{{ด้านระบบบริหารงานบุคคล (Human Resource Management):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[251].replace('• • ', ''))}
        \item {escape_latex(paragraphs[252].replace('• • ', ''))}
        \item {escape_latex(paragraphs[253].replace('• • ', ''))}
        \item {escape_latex(paragraphs[254].replace('• • ', ''))}
    \end{{mycustomitem}}

    \item \textbf{{ด้านระบบแผงควบคุมสำหรับผู้บริหารและผู้ดูแลระบบ (Executive \& Admin Dashboard):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[256].replace('• • ', ''))}
        \item {escape_latex(paragraphs[257].replace('• • ', ''))}
        \item {escape_latex(paragraphs[258].replace('• • ', ''))}
        \item {escape_latex(paragraphs[259].replace('• • ', ''))}
        \item {escape_latex(paragraphs[260].replace('• • ', ''))}
    \end{{mycustomitem}}

    \item \textbf{{ด้านระบบรักษาความปลอดภัยและการทดสอบ (Security \& System Evaluation):}}
    \begin{{mycustomitem}}
        \item {escape_latex(paragraphs[262].replace('• • ', ''))}
        \item {escape_latex(paragraphs[263].replace('• • ', ''))}
        \item {escape_latex(paragraphs[264].replace('• • ', ''))}
    \end{{mycustomitem}}
\end{{mycustomitem}}

\section{{ทรัพยากรและงบประมาณที่ใช้ในการจัดทำโครงงาน}}
\hspace*{{1.3em}}
{escape_latex(paragraphs[266])}

\subsection{{อุปกรณ์ฮาร์ดแวร์ (Hardware)}}
\begin{{mycustomitem}}
    \item {escape_latex(paragraphs[268].replace('• ', ''))}
    \item {escape_latex(paragraphs[269].replace('• ', ''))}
\end{{mycustomitem}}

\subsection{{ซอฟต์แวร์และเครื่องมือพัฒนา (Software \& Tools)}}
\begin{{mycustomitem}}
    \item {escape_latex(paragraphs[271].replace('• ', ''))}
    \item {escape_latex(paragraphs[272].replace('• ', ''))}
    \item {escape_latex(paragraphs[273].replace('• ', ''))}
    \item {escape_latex(paragraphs[274].replace('• ', ''))}
    \item {escape_latex(paragraphs[275].replace('• ', ''))}
\end{{mycustomitem}}

\subsection{{งบประมาณที่ใช้ในการจัดทำโครงงาน}}
{t1_1_tex}

\section{{ประโยชน์ที่คาดว่าจะได้รับ}}
\hspace*{{1.3em}}
{escape_latex(paragraphs[285])}
\begin{{mycustomenum}}[label=1.5.\arabic*]
    \item {escape_latex(paragraphs[286].replace('• 1.5.1 ', ''))}
    \item {escape_latex(paragraphs[287].replace('• 1.5.2 ', ''))}
    \item {escape_latex(paragraphs[288].replace('• 1.5.3 ', ''))}
    \item {escape_latex(paragraphs[289].replace('• 1.5.4 ', ''))}
    \item {escape_latex(paragraphs[290].replace('• 1.5.5 ', ''))}
\end{{mycustomenum}}

\section{{แผนและระยะเวลาในการดำเนินงาน}}
\hspace*{{1.3em}}
{escape_latex(paragraphs[292])}

{t1_2_tex}
"""

with open(os.path.join(out_dir, "Project_010_Chapter1.tex"), "w", encoding="utf-8") as f:
    f.write(ch1_tex)
print("Successfully generated Project_010_Chapter1.tex")
