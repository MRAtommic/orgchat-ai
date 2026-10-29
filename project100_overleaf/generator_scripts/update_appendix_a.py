# -*- coding: utf-8 -*-
import os

appendix_a_content = r"""%*************************************
% ภาคผนวก ก.
%*************************************
\appendixChapterTitle{ก}{คู่มือการติดตั้งและกำหนดค่าระบบ}
\vspace{0.2in}

\section{ความต้องการของระบบ (System Requirements)}
\hspace*{1.3em}
การติดตั้งและเปิดใช้งานระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร OrgChat AI มีข้อกำหนดความต้องการด้านฮาร์ดแวร์ ซอฟต์แวร์ และบริการภายนอกที่จำเป็น ดังนี้:

\subsection{ความต้องการด้านฮาร์ดแวร์ (Hardware Requirements)}
\begin{mycustomitem}
\item \textbf{เครื่องแม่ข่าย (Server Environment)}:
  \begin{itemize}[leftmargin=2em]
    \item หน่วยประมวลผลกลาง (CPU): 64-bit Dual-Core 2.0 GHz ขึ้นไป (แนะนำ Quad-Core 2.5 GHz ขึ้นไป สำหรับประมวลผลเวกเตอร์)
    \item หน่วยความจำหลัก (RAM): ไม่น้อยกว่า 4 GB (แนะนำ 8 GB ขึ้นไป เพื่อรองรับการรัน FastEmbed และแคชของ ChromaDB)
    \item พื้นที่จัดเก็บข้อมูล (Disk Storage): พื้นที่ว่างไม่น้อยกว่า 10 GB สำหรับจัดเก็บฐานข้อมูล SQLite, คลังเวกเตอร์ ChromaDB และไฟล์แคชโมเดล
    \item เครือข่าย (Network): การเชื่อมต่ออินเทอร์เน็ตความเร็วสูงที่เสถียร พร้อมรองรับการเชื่อมต่อขาออกไปยัง Google APIs และ LINE APIs
  \end{itemize}
\end{mycustomitem}

\begin{mycustomitem}
\item \textbf{เครื่องลูกข่ายและอุปกรณ์ผู้ใช้งาน (Client Devices)}:
  \begin{itemize}[leftmargin=2em]
    \item คอมพิวเตอร์ส่วนบุคคล: รองรับระบบปฏิบัติการ Windows 10/11, macOS, หรือ Linux พร้อมเว็บบราวเซอร์สมัยใหม่
    \item สมาร์ตโฟน: ระบบปฏิบัติการ iOS 15.0 ขึ้นไป หรือ Android 10.0 ขึ้นไป พร้อมติดตั้งแอปพลิเคชัน LINE เวอร์ชันล่าสุด
  \end{itemize}
\end{mycustomitem}

\subsection{ความต้องการด้านซอฟต์แวร์ (Software Requirements)}
\begin{mycustomitem}
\item ระบบปฏิบัติการเครื่องแม่ข่าย: Linux (Ubuntu 20.04 LTS / 22.04 LTS แนะนำ) หรือ Windows Server 2019 / Windows 10/11 64-bit
\item สภาพแวดล้อมรันไทม์: Python เวอร์ชัน 3.10.x หรือ 3.11.x (ไม่แนะนำ 3.12+ เนื่องจากความเข้ากันได้ของไลบรารีวิทยาศาสตร์ข้อมูลบางตัว)
\item ระบบจัดการแพ็กเกจ: pip เวอร์ชัน 23.0 ขึ้นไป และ virtualenv
\item ระบบฐานข้อมูล: SQLite 3.35.0 ขึ้นไป (รองรับฟังก์ชัน UPSERT และ JSON)
\item เว็บบราวเซอร์: Google Chrome 110+, Mozilla Firefox 110+, หรือ Microsoft Edge 110+
\end{mycustomitem}

\subsection{บริการคลาวด์และบัญชีนักพัฒนาภายนอก (External Cloud Services)}
\begin{mycustomitem}
\item \textbf{LINE Developers Account}: สำหรับสร้างและจัดการ Messaging API Channel และ LINE Login Channel
\item \textbf{Google Cloud Platform (GCP)}: สำหรับเปิดใช้งาน Google Drive API, สร้าง Service Account Credentials (ไฟล์ JSON)
\item \textbf{Google AI Studio}: สำหรับขอรับ Gemini API Key สำหรับโมเดล Gemini 1.5 Flash
\item \textbf{โดเมนเนมและใบรับรองความปลอดภัย}: โดเมนเนมที่ติดตั้ง SSL/TLS Certificate (HTTPS) สำหรับตั้งค่า Webhook URL ของ LINE
\end{mycustomitem}

\section{การกำหนดค่าตัวแปรสภาพแวดล้อม (Environment Configuration)}
\hspace*{1.3em}
การทำงานของระบบควบคุมผ่านไฟล์กำหนดค่าตัวแปรสภาพแวดล้อม (\texttt{.env}) ซึ่งต้องวางไว้ที่โฟลเดอร์หลัก (Root Directory) ของโปรเจกต์ โดยมีตัวแปรสำคัญดังนี้:

\begin{table}[htbp]
\centering
\caption{ตัวแปรสภาพแวดล้อมในไฟล์ .env และคำอธิบายการตั้งค่า}
\label{tabA:env_vars}
\begin{tabularx}{\textwidth}{| L | c | L |}
\hline
\textbf{ชื่อตัวแปรสภาพแวดล้อม} & \textbf{ความจำเป็น} & \textbf{คำอธิบายและการใช้งาน} \\ \hline
\texttt{FLASK\_SECRET\_KEY} & จำเป็น & คีย์ลับสำหรับเข้ารหัส Session Cookie บนเว็บ \\ \hline
\texttt{LINE\_CHANNEL\_ACCESS\_TOKEN} & จำเป็น & Long-lived Token จาก LINE Messaging API \\ \hline
\texttt{LINE\_CHANNEL\_SECRET} & จำเป็น & Secret Key ตรวจสอบลายเซ็น X-Line-Signature \\ \hline
\texttt{LINE\_LOGIN\_CHANNEL\_ID} & จำเป็น & Channel ID สำหรับบริการ LINE Login OAuth 2.0 \\ \hline
\texttt{LINE\_LOGIN\_CHANNEL\_SECRET} & จำเป็น & Secret Key แลกเปลี่ยน Token ใน LINE Login \\ \hline
\texttt{GEMINI\_API\_KEY} & จำเป็น & API Key สำหรับเรียกใช้งาน Google Gemini 1.5 \\ \hline
\texttt{GOOGLE\_SERVICE\_ACCOUNT\_FILE} & จำเป็น & ที่อยู่ของไฟล์ JSON กุญแจ Service Account \\ \hline
\texttt{GOOGLE\_DRIVE\_FOLDER\_ID} & ไม่บังคับ & ID โฟลเดอร์หลักบน Google Drive ที่จัดเก็บไฟล์ \\ \hline
\texttt{DATABASE\_PATH} & จำเป็น & ที่อยู่ไฟล์ฐานข้อมูล SQLite เช่น \texttt{data/orgchat.db} \\ \hline
\texttt{CHROMA\_DB\_DIR} & จำเป็น & ไดเรกทอรีจัดเก็บเวกเตอร์ ChromaDB \\ \hline
\end{tabularx}
\end{table}

\section{ขั้นตอนการติดตั้งและเริ่มต้นการทำงานของระบบ}
\hspace*{1.3em}
การติดตั้งระบบแบ่งออกเป็น 6 ขั้นตอนตามลำดับ ดังนี้:

\subsection{ขั้นตอนที่ 1: การดาวน์โหลดซอร์สโค้ดโครงงาน}
\hspace*{1.3em}
เปิดเทอร์มินัลหรือคอมมานด์ไลน์ และโคลนซอร์สโค้ดจาก Git Repository ไปยังเครื่องเซิร์ฟเวอร์:
\begin{mycustomitem}
\item \texttt{git clone https://github.com/MRAtommic/orgchat-ai.git}
\item \texttt{cd orgchat-ai}
\end{mycustomitem}

\subsection{ขั้นตอนที่ 2: การสร้างสภาพแวดล้อมเสมือน (Virtual Environment)}
\hspace*{1.3em}
สร้างและเปิดใช้งาน Virtual Environment เพื่อป้องกันการชนกันของเวอร์ชันไลบรารี:
\begin{mycustomitem}
\item สำหรับระบบปฏิบัติการ Linux / macOS:
  \begin{itemize}[leftmargin=2em]
    \item \texttt{python3 -m venv venv}
    \item \texttt{source venv/bin/activate}
  \end{itemize}
\item สำหรับระบบปฏิบัติการ Windows:
  \begin{itemize}[leftmargin=2em]
    \item \texttt{python -m venv venv}
    \item \texttt{venv\textbackslash Scripts\textbackslash activate}
  \end{itemize}
\end{mycustomitem}

\subsection{ขั้นตอนที่ 3: การติดตั้งแพ็กเกจและไลบรารีที่จำเป็น}
\hspace*{1.3em}
อัปเกรดตัวจัดการแพ็กเกจ pip และติดตั้งโมดูลที่เกี่ยวข้องทั้งหมดจากไฟล์ \texttt{requirements.txt}:
\begin{mycustomitem}
\item \texttt{pip install --upgrade pip}
\item \texttt{pip install -r requirements.txt}
\end{mycustomitem}

\subsection{ขั้นตอนที่ 4: การกำหนดค่าตัวแปรสภาพแวดล้อม}
\hspace*{1.3em}
คัดลอกไฟล์ตัวอย่างคอนฟิก และกรอกข้อมูล API Keys ที่ได้รับจากผู้ให้บริการ:
\begin{mycustomitem}
\item \texttt{cp .env.example .env} (หรือคัดลอกไฟล์บน Windows)
\item แก้ไขไฟล์ \texttt{.env} ด้วยโปรแกรมแก้ไขข้อความ และวางค่า Channel Token, Secret, Gemini API Key และวางไฟล์ Service Account JSON ในโฟลเดอร์ของระบบ
\end{mycustomitem}

\subsection{ขั้นตอนที่ 5: การเริ่มต้นโครงสร้างฐานข้อมูล (Database Migration)}
\hspace*{1.3em}
สั่งรันสคริปต์เริ่มต้นเพื่อสร้างตารางข้อมูลใน SQLite และสร้างคอลเลกชันใน ChromaDB:
\begin{mycustomitem}
\item \texttt{python init\_db.py}
\end{mycustomitem}

\subsection{ขั้นตอนที่ 6: การเริ่มต้นการทำงานของเซิร์ฟเวอร์}
\hspace*{1.3em}
สำหรับการรันในสภาพแวดล้อมพัฒนา (Development Mode):
\begin{mycustomitem}
\item \texttt{python app.py}
\end{mycustomitem}
\hspace*{1.3em}
สำหรับการรันในสภาพแวดล้อมใช้งานจริง (Production Mode ด้วย Gunicorn และ Reverse Proxy Nginx):
\begin{mycustomitem}
\item \texttt{gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 wsgi:app}
\end{mycustomitem}

\section{ปัญหาที่พบบ่อยในการติดตั้งและวิธีแก้ไข (Troubleshooting)}
\hspace*{1.3em}
ตารางที่ ก-2 สรุปปัญหาและข้อผิดพลาดที่อาจพบได้ในระหว่างการติดตั้งระบบ พร้อมสาเหตุและแนวทางแก้ไข:

\begin{table}[htbp]
\centering
\caption{ปัญหาที่พบบ่อยในขั้นตอนการติดตั้งระบบและแนวทางแก้ไข}
\label{tabA:troubleshooting}
\begin{tabularx}{\textwidth}{| L | L | L |}
\hline
\textbf{ปัญหา / ข้อผิดพลาด} & \textbf{สาเหตุที่เป็นไปได้} & \textbf{แนวทางการแก้ไข} \\ \hline
\texttt{Invalid Signature} (Webhook Error 403) & ค่า \texttt{LINE\_CHANNEL\_SECRET} ใน .env ไม่ตรงกับคอนโซล & ตรวจสอบและคัดลอก Channel Secret จาก LINE Developers Console ให้ถูกต้อง \\ \hline
\texttt{Webhook URL verification failed} & เซิร์ฟเวอร์ไม่รองรับ HTTPS หรือไม่ได้ตอบกลับ HTTP 200 & ติดตั้ง SSL Certificate ให้โดเมน และตรวจสอบว่าเปิดใช้งาน Webhook ใน LINE Console แล้ว \\ \hline
\texttt{ChromaDB / SQLite error: unable to open database} & สิทธิ์การเขียนโฟลเดอร์ (Permission Denied) & ตรวจสอบสิทธิ์ของไดเรกทอรีที่จัดเก็บไฟล์ SQLite และให้สิทธิ์ Read/Write แก่โพรเซส \\ \hline
\texttt{Gemini API Quota Exceeded (429)} & เรียกใช้ API เกินโควตาคำขอต่อนาทีของแพ็กเกจฟรี & เว้นระยะการส่งคำขอ หรือสลับไปใช้ Gemini API Key สำรองที่ผูกบัญชี Billing \\ \hline
\texttt{Google Drive: Credentials not found} & ไม่พบไฟล์ JSON หรือไม่ได้ระบุ Path ให้ถูกต้อง & ตรวจสอบที่อยู่ไฟล์ \texttt{service\_account.json} ใน .env และตรวจสอบสิทธิ์การเข้าถึง \\ \hline
\texttt{ModuleNotFoundError: fastembed} & การติดตั้งแพ็กเกจไม่สมบูรณ์ หรือเวอร์ชัน Python ไม่ตรง & ตรวจสอบว่าเปิดใช้งาน Virtual Environment และใช้ Python 3.10-3.11 ในการติดตั้ง \\ \hline
\end{tabularx}
\end{table}
"""

with open(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Project_101_AppendixA.tex', 'w', encoding='utf-8') as f:
    f.write(appendix_a_content)

with open(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT\Project_101_AppendixA.tex', 'w', encoding='utf-8') as f:
    f.write(appendix_a_content)

print("Appendix A updated successfully in both folders!")
