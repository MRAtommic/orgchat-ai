# -*- coding: utf-8 -*-
import os

flowcharts_latex = r"""\section{ผังงานกระบวนการประมวลผลของระบบ (Process Flowcharts)}
\hspace*{1.3em}
เพื่อแสดงลำดับขั้นตอนการตัดสินใจ เงื่อนไข และกระบวนการทำงานของระบบอย่างละเอียด คณะผู้จัดทำได้จัดทำผังงาน (Flowcharts) มาตรฐานตามวงจรการทำงานหลักของระบบ OrgChat AI โดยมีรายละเอียดขั้นตอนการทำงานในแต่ละส่วนดังนี้:

\subsection{ผังงานขั้นตอนการเข้าสู่ระบบและการยืนยันตัวตน (Authentication Flowchart)}
\hspace*{1.3em}
แสดงขั้นตอนการยืนยันตัวตนของผู้ใช้งานผ่านระบบเว็บแอปพลิเคชันด้วยชื่อผู้ใช้และรหัสผ่าน (Username \& Password) และการเข้าสู่ระบบผ่าน LINE Login OAuth 2.0 โดยระบบจะตรวจสอบความถูกต้องของข้อมูลและออกโทเค็นเซสชันที่ปลอดภัย ดังแสดงในภาพที่ 3-4:

\begin{figure}[htbp]
\centering
\includegraphics[height=0.46\textheight,keepaspectratio]{Image/fig3_3_flow_auth.png}
\caption{ผังงานขั้นตอนการเข้าสู่ระบบและการยืนยันตัวตน (Authentication Flowchart)}
\label{fig3:flow_auth}
\end{figure}

\subsection{ผังงานขั้นตอนการทำงานของระบบคลังความรู้ RAG (RAG Knowledge Retrieval Flowchart)}
\hspace*{1.3em}
แสดงขั้นตอนการแปลงคำถามภาษาธรรมชาติเป็นเวกเตอร์เอ็มเบดดิง การสืบค้นใน ChromaDB และตรวจสอบค่าคะแนนความคล้ายคลึง หากเกินเกณฑ์ 0.65 จะดึงท่อนบริบทส่งให้โมเดล Google Gemini 1.5 Flash สังเคราะห์คำตอบและจัดรูปแบบส่งกลับทาง LINE Flex Message ดังแสดงในภาพที่ 3-5:

\begin{figure}[htbp]
\centering
\includegraphics[height=0.46\textheight,keepaspectratio]{Image/fig3_6_flow_rag.png}
\caption{ผังงานขั้นตอนการทำงานของระบบคลังความรู้ RAG (RAG Knowledge Retrieval Flowchart)}
\label{fig3:flow_rag}
\end{figure}

\subsection{ผังงานขั้นตอนการสกัดข้อมูลสลิปและใบเสร็จด้วย OCR (OCR \& Bookkeeping Flowchart)}
\hspace*{1.3em}
แสดงขั้นตอนการรับภาพสลิปโอนเงิน การปรับปรุงคุณภาพภาพ (Grayscale, Threshold, Denoise, Deskew) และส่งให้ Google Cloud Vision API ร่วมกับ Regex สกัดฟิลด์สำคัญ จากนั้นจำแนกหมวดหมู่บัญชี บันทึกลง Google Sheets และสำรองไฟล์ขึ้น Google Drive ดังแสดงในภาพที่ 3-6:

\begin{figure}[htbp]
\centering
\includegraphics[height=0.46\textheight,keepaspectratio]{Image/fig3_7_flow_ocr.png}
\caption{ผังงานขั้นตอนการสกัดข้อมูลสลิปและใบเสร็จด้วย OCR และการลงบัญชีอัตโนมัติ}
\label{fig3:flow_ocr}
\end{figure}

\subsection{ผังงานขั้นตอนการยื่นคำขอลางานของพนักงาน (Leave Submission Flowchart)}
\hspace*{1.3em}
แสดงขั้นตอนเมื่อพนักงานเปิดเมนูยื่นใบลาจาก LINE Rich Menu ผ่านหน้าต่าง LIFF ระบุข้อมูลการลาและแนบเอกสารรับรอง ระบบจะตรวจสอบโควตาวันลาและบันทึกคำขอลงฐานข้อมูล พร้อมส่งการแจ้งเตือนไปยังหัวหน้างานทาง LINE Flex Message ดังแสดงในภาพที่ 3-7:

\begin{figure}[htbp]
\centering
\includegraphics[height=0.46\textheight,keepaspectratio]{Image/fig3_5_flow_leave_request.png}
\caption{ผังงานขั้นตอนการยื่นคำขอลางานของพนักงานผ่าน LINE (Leave Submission Flowchart)}
\label{fig3:flow_leave_request}
\end{figure}

\subsection{ผังงานขั้นตอนการพิจารณาอนุมัติคำขอลางาน (Leave Approval Process Flowchart)}
\hspace*{1.3em}
แสดงเงื่อนไขและขั้นตอนการพิจารณาอนุมัติคำขอลางานของหัวหน้างาน เมื่อได้รับข้อความแจ้งเตือนทาง LINE Flex Message หากหัวหน้างานกดอนุมัติ ระบบจะตรวจสอบโควตาวันลา ปรับปรุงสถานะคำขอ หักลบโควตาวันลาในฐานข้อมูล และแจ้งผลกลับไปยังพนักงาน ดังแสดงในภาพที่ 3-8:

\begin{figure}[htbp]
\centering
\includegraphics[height=0.46\textheight,keepaspectratio]{Image/fig3_4_flow_leave_approve.png}
\caption{ผังงานขั้นตอนการพิจารณาอนุมัติคำขอลางานของหัวหน้างาน (Leave Approval Flowchart)}
\label{fig3:flow_leave_approve}
\end{figure}
"""

def add_flowcharts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update line 7 intro to include Process Flowcharts
    old_intro = r"การออกแบบข้อมูล (Data Element Description) แบบจำลองความสัมพันธ์ของข้อมูล (ER Diagram)"
    new_intro = r"การออกแบบข้อมูล (Data Element Description) ผังงานกระบวนการประมวลผล (Process Flowcharts) แบบจำลองความสัมพันธ์ของข้อมูล (ER Diagram)"
    if old_intro in content:
        content = content.replace(old_intro, new_intro)

    # Insert flowcharts section right before \clearpage\n\section{การออกแบบฐานข้อมูล (Database Design)}
    target_pos = r"\clearpage" + "\n" + r"\section{การออกแบบฐานข้อมูล (Database Design)}"
    if target_pos in content and r"\section{ผังงานกระบวนการประมวลผลของระบบ (Process Flowcharts)}" not in content:
        insertion = "\n" + flowcharts_latex + "\n" + target_pos
        content = content.replace(target_pos, insertion)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

add_flowcharts(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Project_030_Chapter3.tex')
add_flowcharts(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT\Project_030_Chapter3.tex')

print("Process Flowcharts successfully added to Chapter 3 in both folders!")
