import json
import os
import re

out_dir = r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT"

with open(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\docx_dump.json", "r", encoding="utf-8") as f:
    docx_data = json.load(f)

paragraphs = docx_data["paragraphs"]
tables = docx_data["tables"]

def escape_tex(s):
    if not s:
        return ""
    # Map special LaTeX characters
    # Don't touch if it looks like latex command
    s = s.replace('&', r'\&')
    s = s.replace('%', r'\%')
    s = s.replace('$', r'\$')
    s = s.replace('#', r'\#')
    s = s.replace('_', r'\_')
    return s

def clean_txt(s):
    return s.strip()

# -----------------------------------------------------------------------------
# 1. Project_000_Cover.tex
# -----------------------------------------------------------------------------
cover_tex = r"""%*************************************
% ปกนอก
%*************************************
\newpage
\thispagestyle{empty}
\begin{center}

\vspace*{-0.8in}

\includegraphics[width=5.08cm]{Image/Logo_KMUTNB_Thai.png}
\vspace{2mm}

{\bf
    ปัญญาประดิษฐ์แชทบอทสำหรับองค์กร\\
    (กรณีศึกษา : บริษัท ฮาร์ทวอมมิ่ง จำกัด)
}

\vspace{0.3in}

\vspace{56mm}
\bf
นายวีรภัทร ชื่นชอบ\\  %ผู้จัดทำคนที่ 1
นายธนากร ธนบวรพล       %ผู้จัดทำคนที่ 2

\vspace{60mm}  

\vspace{0.4in}

{\bf 
    ปริญญานิพนธ์นี้เป็นส่วนหนึ่งของการศึกษาตามหลักสูตรวิทยาศาสตรบัณฑิต\\
    สาขาวิชาเทคโนโลยีสารสนเทศ ภาควิชาเทคโนโลยีสารสนเทศ\\
    คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ\\
    ปีการศึกษา 2569\\
    ลิขสิทธิ์ของมหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ
}

\end{center}

%*************************************
% ปกในภาษาไทย
%*************************************
\newpage
\thispagestyle{empty}
\begin{center}

\vspace*{-0.5in}

{\bf
    ปัญญาประดิษฐ์แชทบอทสำหรับองค์กร
}

\vspace{0.1in}
{\bf
    (กรณีศึกษา : บริษัท ฮาร์ทวอมมิ่ง จำกัด)
}

\vspace{87mm}
\bf
นายวีรภัทร ชื่นชอบ\\    %ชื่อผู้จัดทำ1
นายธนากร ธนบวรพล       %ชื่อผู้จัดทำ2
\vspace{87mm}  

\vspace{0.1in}

{\bf
    ปริญญานิพนธ์นี้เป็นส่วนหนึ่งของการศึกษาตามหลักสูตรวิทยาศาสตรบัณฑิต\\
    สาขาวิชาเทคโนโลยีสารสนเทศ ภาควิชาเทคโนโลยีสารสนเทศ\\
    คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ\\
    ปีการศึกษา 2569\\
    ลิขสิทธิ์ของมหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ
}

\end{center}

%*************************************
% ปกในภาษาอังกฤษ
%*************************************
\newpage
\thispagestyle{empty}
\begin{center}

\vspace*{-0.5in}

{\bf
    ARTIFICIAL INTELLIGENCE CHATBOT FOR ORGANIZATION
}

\vspace{0.2in}
{\bf
    (Case Study: Heartwarming Co., Ltd.)
}

\vspace{70mm}
\bf
MR. WEERAPHAT CHUENCHOB\\        %ชื่อผู้จัดทำ1
MR. THANAKORN THANABAWONPON        %ชื่อผู้จัดทำ2
\vspace{70mm}  

\vspace{0.2in}

{\bf
    PROJECT REPORT SUBMITTED IN PARTIAL FULFILLMENT OF THE REQUIREMENTS\\
    FOR THE BACHELOR’S DEGREE OF SCIENCE\\
    PROGRAM IN INFORMATION TECHNOLOGY\\
    DEPARTMENT OF INFORMATION TECHNOLOGY\\
    FACULTY OF INDUSTRIAL TECHNOLOGY AND MANAGEMENT\\
    KING MONGKUT’S UNIVERSITY OF TECHNOLOGY NORTH BANGKOK\\
    ACADEMIC YEAR 2026\\
    COPYRIGHT OF KING MONGKUT’S UNIVERSITY OF TECHNOLOGY NORTH BANGKOK
}

\end{center}
"""

with open(os.path.join(out_dir, "Project_000_Cover.tex"), "w", encoding="utf-8") as f:
    f.write(cover_tex)
print("Wrote Project_000_Cover.tex")

# -----------------------------------------------------------------------------
# 2. Project_001_Certificate1.tex (กรณี ไม่มี ที่ปรึกษาร่วม)
# -----------------------------------------------------------------------------
cert1_tex = r"""%**************************************************************************************
% ใบรับรองโครงงาน กรณี ไม่มี ที่ปรึกษาร่วม
%**************************************************************************************
\newpage
\thispagestyle{empty}
\setstretch{1.25}
\setlength{\parindent}{0pt}

\vspace*{-0.5in}

\begin{tcolorbox}[colframe=black, colback=white, width=\textwidth, boxrule=0.8pt, arc=1mm, auto outer arc, left=10pt, right=10pt, top=10pt, bottom=10pt, enhanced jigsaw]

\begin{center}
\vspace{3mm}
\includegraphics[width=3.18cm]{Image/Logo_KMUTNB_Thai.png}

{\bf {\fontTwentyFour
    ใบรับรองปริญญานิพนธ์
    \\
}{\fontEighteen
    คณะเทคโนโลยีและการจัดการอุตสาหกรรม
    \\
    มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ
}}
\end{center}
\vspace{1em}
\fontSixTeen{
\begin{tabbing}
    เรื่อง  \= ปัญญาประดิษฐ์แชทบอทสำหรับองค์กร กรณีศึกษา ฮาร์ทวอมมิ่ง จำกัด       %ชื่อโปรเจ็คภาษาไทย
    \\
    โดย  \> นายวีรภัทร ชื่นชอบ     %ชื่อผู้จัดทำ1 
    \\     %เว้นบรรทัด เมื่อมีเพื่อนร่วมโปรเจ็ค
        \> นายธนากร ธนบวรพล       %ชื่อผู้จัดทำ2
    \\
    \\
         \> ได้รับอนุมัติให้นับเป็นส่วนหนึ่งของการศึกษาตาม 
    \\
         \> หลักสูตรวิทยาศาสตรบัณฑิต  สาขาวิชาเทคโนโลยีสารสนเทศ ภาควิชาเทคโนโลยีสารสนเทศ
\end{tabbing}

\vspace{1.5em}

\begin{flushright}
\makebox[8cm][l]{\rule{7cm}{0.4pt} คณบดี} \\
\makebox[8cm][l]{(ผู้ช่วยศาสตราจารย์ ดร.กฤษฎากร  บุดดาจันทร์)}
\end{flushright}

\vspace{8mm}

\vspace{0.2in}

คณะกรรมการสอบปริญญานิพนธ์

\vspace{1.5em}
\begin{flushleft}
\makebox[7cm][l]{\rule{7cm}{0.4pt} ประธานกรรมการ} \\
\makebox[7cm][c]{(ผู้ช่วยศาสตราจารย์ ดร.สุปิติ กุลจันทร์)}       %ระบุชื่อประธานกรรมการ
\end{flushleft}

\vspace{1.5em}
\begin{flushleft}
\makebox[7cm][l]{\rule{7cm}{0.4pt} กรรมการ} \\
\makebox[7cm][c]{(ผู้ช่วยศาสตราจารย์ ดร.พาฝัน ดวงไพศาล)}            %ระบุชื่อกรรมการ
\end{flushleft}

\vspace{1.5em}
\begin{flushleft}
\makebox[7cm][l]{\rule{7cm}{0.4pt} อาจารย์ที่ปรึกษา} \\
\makebox[7cm][c]{(อาจารย์ ดร.ศิรินทรา แว่วศรี)}       %ระบุชื่ออาจารย์ที่ปรึกษาโปรเจ็ค
\end{flushleft}

} %end fontSixTeen
\end{tcolorbox}
"""

with open(os.path.join(out_dir, "Project_001_Certificate1.tex"), "w", encoding="utf-8") as f:
    f.write(cert1_tex)
print("Wrote Project_001_Certificate1.tex")

# -----------------------------------------------------------------------------
# 3. Project_001_Certificate2.tex (กรณี มี ที่ปรึกษาร่วม - เผื่อไว้ให้ถูกต้องเหมือนกัน)
# -----------------------------------------------------------------------------
cert2_tex = r"""%**************************************************************************************
% ใบรับรองโครงงาน กรณี มี ที่ปรึกษาร่วม
%**************************************************************************************
\newpage
\thispagestyle{empty}
\setstretch{1.25}
\setlength{\parindent}{0pt}

\begin{tcolorbox}[colframe=black, colback=white, width=\textwidth, boxrule=0.8pt, arc=1mm, auto outer arc, left=10pt, right=10pt, top=10pt, bottom=10pt, enhanced jigsaw]

\begin{center}
\vspace{3mm}
\includegraphics[width=3.18cm]{Image/Logo_KMUTNB_Thai.png}

{\bf {\fontTwentyFour
    ใบรับรองปริญญานิพนธ์
    \\
}{\fontEighteen
    คณะเทคโนโลยีและการจัดการอุตสาหกรรม
    \\
    มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ
}}
\end{center}
\vspace{1em}
\fontSixTeen{
\begin{tabbing}
    เรื่อง  \= ปัญญาประดิษฐ์แชทบอทสำหรับองค์กร กรณีศึกษา ฮาร์ทวอมมิ่ง จำกัด       %ชื่อโปรเจ็คภาษาไทย
    \\
    โดย  \> นายวีรภัทร ชื่นชอบ     %ชื่อผู้จัดทำ1 
    \\     %เว้นบรรทัด เมื่อมีเพื่อนร่วมโปรเจ็ค
        \> นายธนากร ธนบวรพล       %ชื่อผู้จัดทำ2
    \\
    \\
         \> ได้รับอนุมัติให้นับเป็นส่วนหนึ่งของการศึกษาตาม 
    \\
         \> หลักสูตรวิทยาศาสตรบัณฑิต  สาขาวิชาเทคโนโลยีสารสนเทศ ภาควิชาเทคโนโลยีสารสนเทศ
\end{tabbing}

\vspace{1em}

\begin{flushright}
\makebox[8cm][l]{\rule{7cm}{0.4pt} คณบดี} \\
\makebox[8cm][l]{(ผู้ช่วยศาสตราจารย์ ดร.กฤษฎากร  บุดดาจันทร์)}
\end{flushright}

\vspace{0.9em}

คณะกรรมการสอบปริญญานิพนธ์

\vspace{0.9em}
\begin{flushleft}
\makebox[7cm][l]{\rule{7cm}{0.4pt} ประธานกรรมการ} \\
\makebox[7cm][c]{(ผู้ช่วยศาสตราจารย์ ดร.สุปิติ กุลจันทร์)}       %ระบุชื่อประธานกรรมการ
\end{flushleft}

\vspace{0.9em}
\begin{flushleft}
\makebox[7cm][l]{\rule{7cm}{0.4pt} กรรมการ} \\
\makebox[7cm][c]{(ผู้ช่วยศาสตราจารย์ ดร.พาฝัน ดวงไพศาล)}            %ระบุชื่อกรรมการ
\end{flushleft}

\vspace{0.9em}
\begin{flushleft}
\makebox[7cm][l]{\rule{7cm}{0.4pt} อาจารย์ที่ปรึกษา} \\
\makebox[7cm][c]{(อาจารย์ ดร.ศิรินทรา แว่วศรี)}       %ระบุชื่ออาจารย์ที่ปรึกษาโปรเจ็ค
\end{flushleft}

} %end fontSixTeen
\end{tcolorbox}
"""

with open(os.path.join(out_dir, "Project_001_Certificate2.tex"), "w", encoding="utf-8") as f:
    f.write(cert2_tex)
print("Wrote Project_001_Certificate2.tex")

# -----------------------------------------------------------------------------
# 4. Project_002_Abstract.tex (บทคัดย่อภาษาไทย + ภาษาอังกฤษ + กิตติกรรมประกาศ)
# -----------------------------------------------------------------------------
p_thai_abs_1 = escape_tex(paragraphs[83])
p_thai_abs_2 = escape_tex(paragraphs[84])
p_thai_abs_3 = escape_tex(paragraphs[85])

p_eng_abs_1 = escape_tex(paragraphs[93])
p_eng_abs_2 = escape_tex(paragraphs[94])
p_eng_abs_3 = escape_tex(paragraphs[95])

p_ack_1 = escape_tex(paragraphs[102])
p_ack_2 = r"ขอขอบพระคุณ ผู้ช่วยศาสตราจารย์ ดร.สุปิติ กุลจันทร์ ประธานกรรมการสอบปริญญานิพนธ์ และผู้ช่วยศาสตราจารย์ ดร.พาฝัน ดวงไพศาล กรรมการสอบปริญญานิพนธ์ ที่ได้ให้ข้อเสนอแนะเชิงวิชาการอันทรงคุณค่า เพื่อให้โครงงานมีความสมบูรณ์รอบด้านยิ่งขึ้น"
p_ack_3 = escape_tex(paragraphs[104])
p_ack_4 = escape_tex(paragraphs[105])

abstract_tex = f"""%**************************************************************************************
% บทคัดย่อภาษาไทย
%**************************************************************************************
\\phantomsection
\\addcontentsline{{toc}}{{chapter}}{{บทคัดย่อภาษาไทย}}

\\vspace*{{-0.5in}}

\\begin{{tabularx}}{{\\textwidth}}{{l L}}
ชื่อ                           & : นายวีรภัทร ชื่นชอบ\\\\
                             & : นายธนากร ธนบวรพล\\\\
ชื่อปริญญานิพนธ์                  & : ปัญญาประดิษฐ์แชทบอทสำหรับองค์กร กรณีศึกษา ฮาร์ทวอมมิ่ง จำกัด\\\\
สาขาวิชา                       & : เทคโนโลยีสารสนเทศ\\\\
สถาบัน                         & : มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ\\\\
อาจารย์ที่ปรึกษาปริญญานิพนธ์        & : อาจารย์ ดร.ศิรินทรา แว่วศรี\\\\
ปีการศึกษา                     & : 2569\\\\
\\end{{tabularx}}

\\vspace{{5mm}}
\\phantomsection
\\begin{{center}}\\textbf{{บทคัดย่อ}}\\end{{center}}
\\hspace*{{1.5em}}
{p_thai_abs_1}

\\\\
\\hspace*{{1.5em}}
{p_thai_abs_2}

\\\\
\\hspace*{{1.5em}}
{p_thai_abs_3}

\\begin{{flushright}}
(ปริญญานิพนธ์มีจำนวนทั้งสิ้น \\pageref{{LastPage}} หน้า)

\\vfill
\\rule{{10 cm}}{{0.4pt}} อาจารย์ที่ปรึกษาปริญญานิพนธ์\\\\
(อาจารย์ ดร.ศิรินทรา แว่วศรี)

\\end{{flushright}}


%**************************************************************************************
% บทคัดย่อภาษาอังกฤษ
%**************************************************************************************
\\newpage
\\phantomsection
\\addcontentsline{{toc}}{{chapter}}{{บทคัดย่อภาษาอังกฤษ}}

\\vspace*{{-0.5in}}

\\begin{{tabularx}}{{\\textwidth}}{{l L}}
Name                    & : MR. WEERAPHAT CHUENCHOB\\\\
                        & : MR. THANAKORN THANABAWONPON\\\\
Project Title           & : Artificial Intelligence Chatbot for Organization (Case Study: Heartwarming Co., Ltd.)\\\\
Major Field             & : Information Technology\\\\
Institution             & : King Mongkut’s University of Technology North Bangkok\\\\
Project Advisor         & : Dr. Sirintra Vaiwsri\\\\
Academic Year           & : 2026\\\\
\\end{{tabularx}}

\\vspace{{5mm}}
\\begin{{center}}\\textbf{{Abstract}}\\end{{center}}

\\hspace*{{1.5em}}
{p_eng_abs_1}

\\\\
\\hspace*{{1.5em}}
{p_eng_abs_2}

\\\\
\\hspace*{{1.5em}}
{p_eng_abs_3}

\\begin{{flushright}}
(Total \\pageref{{LastPage}} pages)

\\vfill
\\rule{{10 cm}}{{0.4pt}} Project Advisor\\\\
(Dr. Sirintra Vaiwsri)

\\end{{flushright}}


%**************************************************************************************
% กิตติกรรมประกาศ
%**************************************************************************************
\\newpage
\\phantomsection
\\addcontentsline{{toc}}{{chapter}}{{กิตติกรรมประกาศ}}

\\vspace*{{-0.5in}}

\\begin{{center}}\\textbf{{กิตติกรรมประกาศ}}\\end{{center}}
\\vspace*{{0.2in}}
\\hspace*{{1.5em}}
{p_ack_1}
\\\\
\\hspace*{{1.5em}}
{p_ack_2}
\\\\
\\hspace*{{1.5em}}
{p_ack_3}
\\\\
\\hspace*{{1.5em}}
{p_ack_4}
\\\\
\\begin{{flushright}}
\\makebox[6cm][l]{{นายวีรภัทร ชื่นชอบ}}\\\\
\\makebox[6cm][l]{{นายธนากร ธนบวรพล}}

\\end{{flushright}}
"""

with open(os.path.join(out_dir, "Project_002_Abstract.tex"), "w", encoding="utf-8") as f:
    f.write(abstract_tex)
print("Wrote Project_002_Abstract.tex")

# -----------------------------------------------------------------------------
# 5. Project_999_Bibliography.bib
# -----------------------------------------------------------------------------
bib_tex = r"""@article{charoenchai2022ocr,
  author  = {กิตติศักดิ์ เจริญชัย and ภาณุพงศ์ วงศ์สวัสดิ์},
  title   = {การรู้จำอักขระจากสลิปโอนเงินผ่านโมบายแบงกิ้งด้วยเทคนิคการประมวลผลภาพดิจิทัล},
  journal = {วารสารเทคโนโลยีสารสนเทศและนวัตกรรม},
  volume  = {8},
  number  = {2},
  pages   = {45--56},
  year    = {2565}
}

@inproceedings{satitthum2023rag,
  author    = {สมชาย สถิตธรรม and คณะ},
  title     = {การพัฒนาระบบตอบคำถามอัตโนมัติด้วยโมเดลภาษาขนาดใหญ่ร่วมกับเทคนิคการค้นคืนข้อมูลเสริม (RAG)},
  booktitle = {การประชุมวิชาการระดับชาติด้านคอมพิวเตอร์และเทคโนโลยีสารสนเทศ ครั้งที่ 19 (NCCIT 2023)},
  pages     = {112--118},
  year      = {2566}
}

@online{chromadb2024,
  author  = {Chroma},
  title   = {ChromaDB: The AI-native open-source embedding database documentation},
  url     = {https://docs.trychroma.com/},
  year    = {2024}
}

@online{googlecloudvision2024,
  author  = {{Google LLC}},
  title   = {Google Cloud Vision API Documentation},
  url     = {https://cloud.google.com/vision/docs},
  year    = {2024}
}

@online{googlegemini2024,
  author  = {{Google LLC}},
  title   = {Google Gemini API Documentation},
  url     = {https://ai.google.dev/docs},
  year    = {2024}
}

@online{googledrive2024,
  author  = {{Google LLC}},
  title   = {Google Drive and Google Sheets API Documentation},
  url     = {https://developers.google.com/workspace/products},
  year    = {2024}
}

@online{lineapi2024,
  author  = {{LINE Corporation}},
  title   = {LINE Messaging API and LINE Login Documentation},
  url     = {https://developers.line.biz/en/docs/},
  year    = {2024}
}

@techreport{nist2020rbac,
  author      = {{National Institute of Standards and Technology (NIST)}},
  title       = {Role-Based Access Control (RBAC) Standard},
  number      = {Special Publication 800-162},
  institution = {U.S. Department of Commerce},
  year        = {2020}
}

@online{nielsen2020heuristics,
  author  = {Jakob Nielsen},
  title   = {10 Usability Heuristics for User Interface Design},
  publisher = {Nielsen Norman Group},
  url     = {https://www.nngroup.com/articles/ten-usability-heuristics/},
  year    = {2020}
}

@online{pallets2024flask,
  author  = {{Pallets Projects}},
  title   = {Flask Documentation (Version 3.0.x)},
  url     = {https://flask.palletsprojects.com/},
  year    = {2024}
}

@online{python2024docs,
  author  = {{Python Software Foundation}},
  title   = {Python 3 Language Reference},
  url     = {https://docs.python.org/3/},
  year    = {2024}
}

@online{sqlite2024docs,
  author  = {{SQLite Consortium}},
  title   = {SQLite Database Engine Documentation},
  url     = {https://www.sqlite.org/docs.html},
  year    = {2024}
}
"""

with open(os.path.join(out_dir, "Project_999_Bibliography.bib"), "w", encoding="utf-8") as f:
    f.write(bib_tex)
print("Wrote Project_999_Bibliography.bib")

# -----------------------------------------------------------------------------
# 6. Main.tex (Ensure Certificate1 is active)
# -----------------------------------------------------------------------------
main_path = os.path.join(out_dir, "Main.tex")
with open(main_path, "r", encoding="utf-8") as f:
    main_content = f.read()

# Replace Certificate2 with Certificate1
main_content = main_content.replace(
    r"\input{Project_001_Certificate2} %กรณี มี ที่ปรึกษาร่วม",
    r"\input{Project_001_Certificate1} %กรณี ไม่มี ที่ปรึกษาร่วม"
)
main_content = main_content.replace(
    r"%\input{Project_001_Certificate1} %กรณี ไม่มี ที่ปรึกษาร่วม",
    r"\input{Project_001_Certificate1} %กรณี ไม่มี ที่ปรึกษาร่วม"
)
with open(main_path, "w", encoding="utf-8") as f:
    f.write(main_content)
print("Updated Main.tex")
