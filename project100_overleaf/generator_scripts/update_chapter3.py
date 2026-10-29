import os

chapter3_content = r"""%*************************************
% บทที่ 3
%*************************************
\chapterTitle{3}{วิธีการดำเนินงานและการออกแบบระบบ}
\vspace{0.2in}
\hspace*{1.3em}
ในบทนี้จะกล่าวถึงระเบียบวิธีการดำเนินงาน ขั้นตอนการดำเนินงานตามวงจรพัฒนาซอฟต์แวร์ การวิเคราะห์ความต้องการของระบบ แผนภาพสถาปัตยกรรมระบบ แผนภาพกระแสข้อมูล (Data Flow Diagram: DFD) ข้อกำหนดลักษณะการประมวลผล (Process Specification: PSPEC) พจนานุกรมข้อมูล (Data Flow Dictionary) การออกแบบข้อมูล (Data Element Description) แบบจำลองความสัมพันธ์ของข้อมูล (ER Diagram) โครงสร้างตารางฐานข้อมูล (Table Layout) ตลอดจนการออกแบบส่วนต่อประสานผู้ใช้ (User Interface Design) สำหรับระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร กรณีศึกษา บริษัท ฮาร์ทวอมมิ่ง จำกัด ตามขอบเขตการดำเนินงานในภาคการศึกษาที่ 1/2569

\section{ขั้นตอนและแผนการดำเนินงาน}
\hspace*{1.3em}
การจัดทำโครงงานพิเศษนี้ประยุกต์ใช้วงจรการพัฒนาระบบแบบอไจลส์ (Agile Software Development) ร่วมกับกรอบการทำงานสกรัม (Scrum Framework) ซึ่งเน้นการพัฒนาแบบวนซ้ำและเพิ่มพูนทีละส่วน (Iterative and Incremental Development) โดยแบ่งการดำเนินงานออกเป็น 2 ภาคการศึกษา แผนการดำเนินงานแสดงดังตารางที่ 3-1 และตารางที่ 3-2:

\begin{table}[htbp]
\centering
\caption{แผนการดำเนินงาน ภาคการศึกษาที่ 1/2569}
\label{tab3:plan_term1}
\begin{tabularx}{\textwidth}{| L | c | c | c | c |}
\hline
\textbf{กิจกรรมการดำเนินงาน} & \textbf{เดือนที่ 1} & \textbf{เดือนที่ 2} & \textbf{เดือนที่ 3} & \textbf{เดือนที่ 4} \\ \hline
1. ศึกษาความเป็นมาของ บริษัท ฮาร์ทวอมมิ่ง จำกัด และรวบรวมความต้องการ & \cmark & & & \\ \hline
2. ศึกษาทฤษฎี RAG, Vector Database, LINE API และ Google Cloud & \cmark & \cmark & & \\ \hline
3. วิเคราะห์และออกแบบระบบ (DFD, PSPEC, ERD, Data Dictionary) & & \cmark & & \\ \hline
4. พัฒนาระบบยืนยันตัวตน สมาชิก และ LINE Login OAuth 2.0 & & \cmark & \cmark & \\ \hline
5. พัฒนาระบบคลังความรู้ RAG, Text Chunking และ ChromaDB & & & \cmark & \\ \hline
6. เชื่อมต่อ LINE Messaging API, Webhook และสร้าง LINE Flex Message & & & \cmark & \cmark \\ \hline
7. เชื่อมต่อระบบจัดระเบียบไฟล์บน Google Drive API & & & & \cmark \\ \hline
8. ทดสอบระบบเบื้องต้น (Black-Box Testing) และจัดทำรายงานโปรเจค 100 & & & & \cmark \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{แผนการดำเนินงาน ภาคการศึกษาที่ 2/2569}
\label{tab3:plan_term2}
\begin{tabularx}{\textwidth}{| L | c | c | c | c |}
\hline
\textbf{กิจกรรมการดำเนินงาน} & \textbf{เดือนที่ 1} & \textbf{เดือนที่ 2} & \textbf{เดือนที่ 3} & \textbf{เดือนที่ 4} \\ \hline
1. พัฒนาระบบ OCR สกัดข้อมูลสลิปโอนเงินและใบเสร็จรับเงิน & \cmark & \cmark & & \\ \hline
2. พัฒนาระบบลงบัญชีอัตโนมัติลง Google Sheets และระบบกระทบยอด & & \cmark & & \\ \hline
3. พัฒนาระบบบริหารงานบุคคล (การขอลางาน, การอนุมัติผ่าน LINE Flex) & & \cmark & \cmark & \\ \hline
4. พัฒนาแผงควบคุมผู้บริหาร (Admin Dashboard) และระบบวิเคราะห์ข้อมูล & & & \cmark & \\ \hline
5. ทดสอบระบบเต็มรูปแบบ (System Integration \& Performance Testing) & & & \cmark & \cmark \\ \hline
6. นำระบบไปทดลองใช้งานจริงกับพนักงาน บริษัท ฮาร์ทวอมมิ่ง จำกัด & & & & \cmark \\ \hline
7. ประเมินความพึงพอใจของผู้ใช้งาน และจัดทำปริญญานิพนธ์ฉบับสมบูรณ์ & & & & \cmark \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{เครื่องมือและเทคโนโลยีที่ใช้ในการพัฒนาระบบ}
\label{tab3:tools}
\begin{tabularx}{\textwidth}{| c | L | L |}
\hline
\textbf{ประเภท} & \textbf{เครื่องมือ / เทคโนโลยี} & \textbf{วัตถุประสงค์การใช้งาน} \\ \hline
ฮาร์ดแวร์ & คอมพิวเตอร์ส่วนบุคคล (RAM 16GB, CPU Core i7) & พัฒนา ประมวลผล และทดสอบระบบ \\ \hline
ฮาร์ดแวร์ & สมาร์ตโฟนระบบปฏิบัติการ iOS และ Android & ทดสอบการใช้งานแอปพลิเคชัน LINE OA \\ \hline
ภาษาและเฟรมเวิร์ก & Python 3.10+, Flask Web Framework & พัฒนาเซิร์ฟเวอร์ Backend และ Webhook Handler \\ \hline
ส่วนต่อประสานผู้ใช้ & HTML5, CSS3, JavaScript, Bootstrap & พัฒนาหน้าจอเว็บแอปพลิเคชันฝั่ง Frontend \\ \hline
ฐานข้อมูลเชิงสัมพันธ์ & SQLite Database & จัดเก็บข้อมูลบัญชีผู้ใช้ องค์กร และบันทึกประวัติ \\ \hline
ฐานข้อมูลเวกเตอร์ & ChromaDB ร่วมกับ FastEmbed & จัดเก็บและสืบค้นเวกเตอร์เอ็มเบดดิงในระบบ RAG \\ \hline
ปัญญาประดิษฐ์ & Google Gemini 1.5 Flash API & โมเดลภาษาขนาดใหญ่สังเคราะห์คำตอบภาษาธรรมชาติ \\ \hline
บริการภายนอก & LINE Messaging API & รับ-ส่งข้อความและเชื่อมต่อแชทบอทบน LINE OA \\ \hline
บริการภายนอก & Google Drive API & จัดเก็บไฟล์เอกสารและแยกโฟลเดอร์ตามวันที่ \\ \hline
เครื่องมือควบคุม & Git, GitHub, Visual Studio Code & จัดการเวอร์ชันซอร์สโค้ดและสภาพแวดล้อมพัฒนา \\ \hline
\end{tabularx}
\end{table}

\section{การวิเคราะห์ความต้องการของระบบ}

\subsection{ความต้องการเชิงหน้าที่ (Functional Requirements)}
\hspace*{1.3em}
ความต้องการเชิงหน้าที่ของระบบในภาคการศึกษาที่ 1/2569 ประกอบด้วย:
\begin{mycustomitem}
\item FR-1: ระบบยืนยันตัวตนและจัดการบัญชีผู้ใช้ รองรับการสมัครสมาชิก เข้าสู่ระบบด้วย Email/Password และ LINE Login OAuth 2.0 พร้อมการจัดการโปรไฟล์
\end{mycustomitem}
\begin{mycustomitem}
\item FR-2: ระบบคลังความรู้อัจฉริยะ (RAG System) รองรับการอัปโหลดไฟล์เอกสาร (PDF, TXT, สเปรดชีต) สกัดข้อความ แบ่งท่อนข้อความ (Chunking) และแปลงเป็นเวกเตอร์เอ็มเบดดิง
\end{mycustomitem}
\begin{mycustomitem}
\item FR-3: ระบบค้นคืนและตอบคำถามภาษาธรรมชาติ รองรับการค้นคืนข้อมูลด้วยความคล้ายคลึงแบบโคไซน์ (Cosine Similarity) ใน ChromaDB และสังเคราะห์คำตอบด้วย Google Gemini
\end{mycustomitem}
\begin{mycustomitem}
\item FR-4: ระบบแชทบอท LINE OA เชื่อมต่อผ่าน LINE Messaging API รับส่งข้อความภาษาธรรมชาติและตอบกลับด้วยการ์ด LINE Flex Message ที่มีปุ่มกดโต้ตอบ
\end{mycustomitem}
\begin{mycustomitem}
\item FR-5: ระบบจัดการไฟล์และคลาวด์ รองรับการอัปโหลดและจัดระเบียบไฟล์เอกสารขึ้นสู่ Google Drive แยกโฟลเดอร์ตามวันเวลาอัตโนมัติ
\end{mycustomitem}

\subsection{ความต้องการที่ไม่ใช่เชิงหน้าที่ (Non-Functional Requirements)}
\begin{mycustomitem}
\item NFR-1 ด้านประสิทธิภาพ (Performance): ระบบแชทบอท RAG สามารถค้นคืนข้อมูลและสร้างคำตอบส่งกลับทาง LINE ภายในระยะเวลาไม่เกิน 3-5 วินาที
\end{mycustomitem}
\begin{mycustomitem}
\item NFR-2 ด้านความมั่นคงปลอดภัย (Security): ตรวจสอบความถูกต้องของคำขอผ่านลายเซ็นดิจิทัล X-Line-Signature ด้วย HMAC-SHA256 และเข้ารหัสรหัสผ่านด้วยอัลกอริทึม BCrypt
\end{mycustomitem}
\begin{mycustomitem}
\item NFR-3 ด้านการแยกข้อมูลระหว่างองค์กร (Multi-Tenant Isolation): ออกแบบฐานข้อมูลให้แบ่งแยกข้อมูลระหว่างแต่ละองค์กรด้วย Organization ID
\end{mycustomitem}
\begin{mycustomitem}
\item NFR-4 ด้านความง่ายในการใช้งาน (Usability): ผู้ใช้งานสามารถสอบถามข้อมูลผ่านแอปพลิเคชัน LINE ที่คุ้นเคยได้ทันทีโดยไม่ต้องเรียนรู้โปรแกรมใหม่
\end{mycustomitem}
\begin{mycustomitem}
\item NFR-5 ด้านความพร้อมใช้งาน (Availability): ระบบเซิร์ฟเวอร์สามารถให้บริการต่อเนื่องตลอด 24 ชั่วโมง มีความพร้อมใช้งานไม่น้อยกว่าร้อยละ 99.0
\end{mycustomitem}

\section{การออกแบบสถาปัตยกรรมของระบบ (System Architecture)}
\hspace*{1.3em}
สถาปัตยกรรมของระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร ถูกออกแบบตามรูปแบบ Client-Server และ Event-Driven Architecture โดยแบ่งเป็น 3 ส่วนหลัก ได้แก่ 1) ส่วนต่อประสานผู้ใช้ (LINE OA และ Web Frontend), 2) ส่วนประมวลผลเซิร์ฟเวอร์ (Flask Backend, Webhook Handler, RAG Pipeline) และ 3) ส่วนจัดเก็บข้อมูลและบริการภายนอก (SQLite, ChromaDB, Google Gemini, Google Drive) ดังแสดงในภาพที่ 3-1:

\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{Image/fig2_1_architecture.png}
\caption{สถาปัตยกรรมของระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร (System Architecture Diagram)}
\label{fig3:arch}
\end{figure}

\section{แผนภาพกระแสข้อมูล (Data Flow Diagram: DFD)}
\hspace*{1.3em}
แผนภาพกระแสข้อมูลแสดงการไหลของข้อมูลระหว่างเอนทิตีภายนอก (External Entities) กระบวนการประมวลผล (Processes) และแหล่งจัดเก็บข้อมูล (Data Stores) โดยเริ่มต้นจากแผนภาพบริบท (Context Diagram) และจำแนกออกเป็น DFD ระดับต่าง ๆ

\subsection{แผนภาพบริบท (Context Diagram)}
\hspace*{1.3em}
แผนภาพบริบทแสดงภาพรวมความสัมพันธ์ระหว่างระบบ OrgChat AI กับเอนทิตีภายนอก 4 กลุ่ม ได้แก่ 1) พนักงาน (Employee), 2) ผู้ดูแลระบบ (Admin), 3) แพลตฟอร์ม LINE (LINE Platform) และ 4) บริการกูเกิลคลาวด์ (Google Cloud APIs: Gemini, Drive) ดังแสดงในภาพที่ 3-2:

\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{Image/fig3_1_context.png}
\caption{Context Diagram ของระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร}
\label{fig3:context}
\end{figure}

\subsection{แผนภาพกระแสข้อมูลระดับ 0 (DFD Level 0)}
\hspace*{1.3em}
แผนภาพกระแสข้อมูลระดับ 0 แสดงกระบวนการทำงานหลัก 4 กระบวนการของระบบในภาคการศึกษาที่ 1/2569 ที่เชื่อมโยงกับแหล่งจัดเก็บข้อมูล (Data Store D1 - D6) ดังแสดงในภาพที่ 3-3:

\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{Image/fig3_2_dfd.png}
\caption{Data Flow Diagram Level 0 ของระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร}
\label{fig3:dfd0}
\end{figure}

\hspace*{1.3em}
กระบวนการทำงานหลัก 4 กระบวนการ ประกอบด้วย:
\begin{enumerate}[leftmargin=3.5em]
\item[1.0] ตรวจสอบสิทธิ์และจัดการผู้ใช้งาน (Authenticate \& Manage Users)
\item[2.0] ค้นคืนคลังความรู้และตอบคำถามอัจฉริยะ (Retrieve Knowledge \& RAG Chat)
\item[3.0] จัดการเอกสารและเชื่อมโยงคลาวด์ (Manage Documents \& Google Drive)
\item[4.0] เชื่อมต่อและสื่อสารผ่านแพลตฟอร์ม LINE (Connect LINE Messaging \& Reply)
\end{enumerate}

\subsection{แหล่งจัดเก็บข้อมูลของระบบ (Data Store Specifications)}
\hspace*{1.3em}
แหล่งจัดเก็บข้อมูลของระบบในภาคการศึกษาที่ 1/2569 ประกอบด้วย 6 แหล่งจัดเก็บข้อมูลหลัก ดังแสดงในตารางที่ 3-4:

\begin{table}[htbp]
\centering
\caption{แหล่งจัดเก็บข้อมูล (Data Store) ของระบบ}
\label{tab3:datastores}
\begin{tabularx}{\textwidth}{| c | c | c | L |}
\hline
\textbf{รหัส} & \textbf{ชื่อ Data Store} & \textbf{ประเภท} & \textbf{คำอธิบายข้อมูลที่จัดเก็บ} \\ \hline
D1 & users & SQLite & ข้อมูลผู้ใช้งานระบบ รหัสผ่านแฮช บทบาท อีเมล และ LINE User ID \\ \hline
D2 & organizations & SQLite & ข้อมูลนิติบุคคลองค์กร โดเมน และ Channel Access Token \\ \hline
D3 & documents & SQLite & ข้อมูลเอกสารต้นฉบับในคลังความรู้ ชื่อไฟล์ ขนาด และสถานะ \\ \hline
D4 & document\_chunks & SQLite & ข้อมูลท่อนข้อความที่ตัดแบ่งแล้ว และตำแหน่งอ้างอิงหน้า \\ \hline
D5 & vector\_store & ChromaDB & ฐานข้อมูลเวกเตอร์เอ็มเบดดิงสำหรับสืบค้นความคล้ายคลึงบริบท \\ \hline
D6 & drive\_logs & SQLite & บันทึกประวัติไฟล์ที่จัดเก็บ บัญชีผู้ส่ง และลิงก์ Google Drive \\ \hline
\end{tabularx}
\end{table}

\section{การกำหนดลักษณะการประมวลผล (Process Specification : PSPEC)}
\hspace*{1.3em}
การกำหนดลักษณะการประมวลผล (Process Specification: PSPEC) ทำหน้าที่อธิบายตรรกะและขั้นตอนการทำงานของกระบวนการย่อยใน DFD อย่างละเอียด โดยระบุรหัสกระบวนการ ชื่อกระบวนการ ข้อมูลนำเข้า ข้อมูลส่งออก และขั้นตอนการทำงาน (Logic) ดังแสดงในตารางที่ 3-5 ถึงตารางที่ 3-16:

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 1.1 ตรวจสอบการเข้าสู่ระบบ}
\label{tab3:pspec1_1}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 1.1 \\ \hline
ชื่อกระบวนการ & ตรวจสอบการเข้าสู่ระบบ (Authenticate User Login) \\ \hline
ข้อมูลนำเข้า (Input) & ชื่อผู้ใช้หรืออีเมล (username/email), รหัสผ่าน (password) \\ \hline
ข้อมูลส่งออก (Output) & สถานะการเข้าสู่ระบบ, JWT Session Token, ข้อความแจ้งเตือนความผิดพลาด \\ \hline
ตรรกะการประมวลผล & 1. รับค่าชื่อผู้ใช้และรหัสผ่านจากฟอร์มหน้าเว็บ \newline
2. ค้นหาข้อมูลผู้ใช้ในตาราง users (D1) ด้วย username หรือ email \newline
3. หากไม่พบข้อมูล ให้ส่งรหัสข้อผิดพลาด "ไม่พบบัญชีผู้ใช้งาน" \newline
4. ตรวจสอบรหัสผ่านด้วยฟังก์ชัน BCrypt.checkpw() \newline
5. หากรหัสผ่านถูกต้อง สร้าง JWT Token และบันทึกประวัติการเข้าใช้งานลง audit\_logs \newline
6. ส่งผลลัพธ์พร้อม Token กลับไปยังเบราว์เซอร์เพื่อบันทึก Session \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 1.2 เข้าสู่ระบบด้วย LINE Login OAuth 2.0}
\label{tab3:pspec1_2}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 1.2 \\ \hline
ชื่อกระบวนการ & เข้าสู่ระบบด้วย LINE Login (Authenticate via LINE OAuth) \\ \hline
ข้อมูลนำเข้า (Input) & Authorization Code จาก LINE Platform, State Token \\ \hline
ข้อมูลส่งออก (Output) & เซสชันผู้ใช้งาน, LINE Profile Data, หน้าจอปลายทางตามบทบาท \\ \hline
ตรรกะการประมวลผล & 1. ตรวจสอบความถูกต้องของ State Token เพื่อป้องกัน CSRF \newline
2. นำ Authorization Code ไปแลก Access Token กับ LINE OAuth Server \newline
3. เรียกขอข้อมูลโปรไฟล์ (userId, displayName, pictureUrl) จาก LINE API \newline
4. ตรวจสอบว่า line\_user\_id มีอยู่ในตาราง users (D1) แล้วหรือไม่ \newline
5. หากมี ให้สร้างเซสชันและนำทางเข้าสู่ระบบทันที \newline
6. หากยังไม่มี ให้นำทางไปยังหน้าผูกบัญชีหรือลงทะเบียนสมาชิกใหม่ \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 1.3 จัดการโปรไฟล์และสิทธิ์ผู้ใช้งาน}
\label{tab3:pspec1_3}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 1.3 \\ \hline
ชื่อกระบวนการ & จัดการโปรไฟล์และสิทธิ์ผู้ใช้ (Manage Profile and Roles) \\ \hline
ข้อมูลนำเข้า (Input) & รหัสผู้ใช้ (user\_id), ข้อมูลโปรไฟล์ที่แก้ไข, บทบาทสิทธิ์ (Role) \\ \hline
ข้อมูลส่งออก (Output) & ผลการอัปเดตข้อมูลโปรไฟล์ (สำเร็จ / ล้มเหลว) \\ \hline
ตรรกะการประมวลผล & 1. ตรวจสอบสิทธิ์ของผู้ดำเนินการว่ามีสิทธิ์แก้ไขหรือไม่ (Admin หรือเจ้าของบัญชี) \newline
2. ตรวจสอบความถูกต้องของรูปแบบข้อมูล (Data Validation) เช่น รูปแบบอีเมล \newline
3. อัปเดตข้อมูลลงตาราง users (D1) \newline
4. บันทึกประวัติการแก้ไขข้อมูลลงในระบบ audit\_logs \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 2.1 ตรวจสอบและนำเข้าไฟล์เอกสาร}
\label{tab3:pspec2_1}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 2.1 \\ \hline
ชื่อกระบวนการ & ตรวจสอบและนำเข้าไฟล์เอกสาร (Validate and Ingest Document) \\ \hline
ข้อมูลนำเข้า (Input) & ไฟล์เอกสาร (PDF, TXT, CSV, DOCX), รหัสองค์กร (org\_id) \\ \hline
ข้อมูลส่งออก (Output) & ข้อมูลเมทาดาตาของเอกสาร (Document Metadata), ข้อความแจ้งสถานะ \\ \hline
ตรรกะการประมวลผล & 1. ตรวจสอบนามสกุลและ MIME Type ของไฟล์ว่าอยู่ในประเภทที่รองรับหรือไม่ \newline
2. ตรวจสอบขนาดไฟล์ไม่เกิน 25 MB \newline
3. คำนวณค่าแฮช SHA-256 ของเนื้อไฟล์เพื่อป้องกันการอัปโหลดไฟล์ซ้ำ \newline
4. บันทึกข้อมูลไฟล์ลงในตาราง documents (D3) และส่งต่อเข้าคิวสกัดข้อความ \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 2.2 สกัดข้อความและตัดแบ่งท่อนข้อมูล}
\label{tab3:pspec2_2}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 2.2 \\ \hline
ชื่อกระบวนการ & สกัดข้อความและตัดแบ่งท่อนข้อมูล (Extract Text and Chunking) \\ \hline
ข้อมูลนำเข้า (Input) & ไฟล์เอกสารต้นฉบับจากคลังเอกสาร (D3) \\ \hline
ข้อมูลส่งออก (Output) & ท่อนข้อความย่อย (Document Chunks) พร้อมข้อมูลบริบทอ้างอิง \\ \hline
ตรรกะการประมวลผล & 1. อ่านเนื้อหาข้อความจากไฟล์ตามประเภท (PyPDF สำหรับ PDF, Text loader สำหรับ TXT) \newline
2. ทำความสะอาดข้อความ ลบอักขระพิเศษที่ไม่จำเป็นและช่องว่างซ้ำซ้อน \newline
3. ตัดแบ่งข้อความเป็นท่อนย่อย (Chunk Size = 800 ตัวอักษร, Chunk Overlap = 100 ตัวอักษร) \newline
4. ผูกหมายเลขหน้าและรหัสเอกสารเข้ากับแต่ละท่อนข้อความ \newline
5. บันทึกท่อนข้อความลงในตาราง document\_chunks (D4) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 2.3 สร้างเวกเตอร์เอ็มเบดดิง}
\label{tab3:pspec2_3}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 2.3 \\ \hline
ชื่อกระบวนการ & สร้างเวกเตอร์เอ็มเบดดิง (Generate Vector Embeddings) \\ \hline
ข้อมูลนำเข้า (Input) & ท่อนข้อความย่อย (Document Chunks) จาก D4 \\ \hline
ข้อมูลส่งออก (Output) & เวกเตอร์ตัวเลขหลายมิติ (Dense Vector Embeddings) \\ \hline
ตรรกะการประมวลผล & 1. รับรายการท่อนข้อความย่อยเข้าสู่โมเดล FastEmbed / BAAI-bge \newline
2. แปลงข้อความเป็นเวกเตอร์ตัวเลขที่มีขนาดมิติคงที่ (Dimension = 384 หรือ 768) \newline
3. ตรวจสอบความสมบูรณ์ของเวกเตอร์ (ไม่มีค่าว่างหรือ NaN) \newline
4. ส่งผลลัพธ์เวกเตอร์พร้อมเมทาดาตาไปยังกระบวนการบันทึกลงฐานข้อมูลเวกเตอร์ \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 2.4 บันทึกและทำดัชนีเวกเตอร์ใน ChromaDB}
\label{tab3:pspec2_4}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 2.4 \\ \hline
ชื่อกระบวนการ & บันทึกและดัชนีเวกเตอร์ (Index Vectors in ChromaDB) \\ \hline
ข้อมูลนำเข้า (Input) & เวกเตอร์ตัวเลข, รหัสท่อนข้อความ (chunk\_id), เมทาดาตา (org\_id, doc\_id) \\ \hline
ข้อมูลส่งออก (Output) & สถานะการบันทึกสำเร็จ, ดัชนีเวกเตอร์ที่พร้อมใช้งาน \\ \hline
ตรรกะการประมวลผล & 1. เปิดการเชื่อมต่อกับ ChromaDB Client \newline
2. เข้าถึงคอลเลกชัน (Collection) ที่ตรงกับรหัสองค์กร (Multi-Tenant Collection) \newline
3. บันทึกเวกเตอร์ ข้อความต้นฉบับ และเมทาดาตาลงในคอลเลกชัน \newline
4. สร้างดัชนี HNSW (Hierarchical Navigable Small World) เพื่อความรวดเร็วในการค้นหา \newline
5. อัปเดตสถานะเอกสารในตาราง documents (D3) เป็น 'READY' \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 2.5 ค้นคืนท่อนข้อความตามความคล้ายคลึง}
\label{tab3:pspec2_5}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 2.5 \\ \hline
ชื่อกระบวนการ & ค้นคืนท่อนข้อความตามความคล้ายคลึง (Retrieve Context by Similarity) \\ \hline
ข้อมูลนำเข้า (Input) & ข้อความคำถามของผู้ใช้ (Query Text), รหัสองค์กร (org\_id) \\ \hline
ข้อมูลส่งออก (Output) & ท่อนข้อความที่เกี่ยวข้องสูงสุด (Top-K Chunks, K = 3 ถึง 5) \\ \hline
ตรรกะการประมวลผล & 1. นำข้อความคำถามมาแปลงเป็นเวกเตอร์ด้วยโมเดล Embedding เดียวกัน \newline
2. ดำเนินการค้นหาใน ChromaDB (D5) ภายใต้คอลเลกชันขององค์กร \newline
3. คำนวณค่าความคล้ายคลึงแบบโคไซน์ (Cosine Similarity Score) \newline
4. กรองเฉพาะท่อนข้อความที่มีคะแนนเกินเกณฑ์ขั้นต่ำ (Threshold >= 0.65) \newline
5. ส่งคืนท่อนข้อความที่มีความคล้ายคลึงสูงสุด 3-5 รายการแรกพร้อมคะแนน \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 2.6 สังเคราะห์คำตอบด้วย Google Gemini}
\label{tab3:pspec2_6}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 2.6 \\ \hline
ชื่อกระบวนการ & สังเคราะห์คำตอบภาษาธรรมชาติ (Synthesize Response with LLM) \\ \hline
ข้อมูลนำเข้า (Input) & คำถามของผู้ใช้, ท่อนข้อความบริบทที่ค้นคืนได้ (Retrieved Chunks), System Prompt \\ \hline
ข้อมูลส่งออก (Output) & คำตอบภาษาธรรมชาติที่สละสลวย อ้างอิงจากเอกสารองค์กร \\ \hline
ตรรกะการประมวลผล & 1. ประกอบ Augmented Prompt โดยนำท่อนบริบทมาวางต่อจากคำสั่งระบบ (System Prompt) \newline
2. กำหนดเงื่อนไขให้โมเดลตอบเฉพาะข้อมูลที่ปรากฏในบริบท หากไม่มีให้ตอบอย่างสุภาพว่าไม่พบข้อมูล \newline
3. ส่งคำขอไปยัง Google Gemini API ผ่านการเชื่อมต่อ HTTPS \newline
4. รับข้อความคำตอบและตรวจสอบความสมบูรณ์ของประโยค \newline
5. ส่งข้อความคำตอบต่อไปยังกระบวนการจัดรูปแบบและส่งกลับผ่าน LINE \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 3.1 อัปโหลดและจัดระเบียบไฟล์บน Google Drive}
\label{tab3:pspec3_1}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 3.1 \\ \hline
ชื่อกระบวนการ & จัดเก็บไฟล์บน Google Drive (Upload and Organize on Drive) \\ \hline
ข้อมูลนำเข้า (Input) & ไฟล์เอกสารหรือรูปภาพ, ข้อมูลผู้ใช้, วันที่ที่ส่ง \\ \hline
ข้อมูลส่งออก (Output) & รหัสไฟล์บน Drive (drive_file_id), ลิงก์เข้าถึงเอกสาร (drive_url) \\ \hline
ตรรกะการประมวลผล & 1. ยืนยันตัวตนกับ Google Cloud Service Account \newline
2. ตรวจสอบโฟลเดอร์ปลายทางตามปีและเดือน (เช่น /2026/10) หากยังไม่มีให้สร้างโฟลเดอร์ใหม่ \newline
3. อัปโหลดไฟล์ขึ้นสู่โฟลเดอร์บน Google Drive \newline
4. บันทึกข้อมูลประวัติไฟล์และลิงก์ลงตาราง drive\_logs (D6) \newline
5. ส่งคืนลิงก์เอกสารให้ผู้ใช้งานตรวจสอบ \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 4.1 ตรวจสอบและรับเหตุการณ์ LINE Webhook}
\label{tab3:pspec4_1}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 4.1 \\ \hline
ชื่อกระบวนการ & รับและตรวจสอบ LINE Webhook (Handle LINE Webhook Events) \\ \hline
ข้อมูลนำเข้า (Input) & HTTP Request Body จาก LINE Platform, ส่วนหัว X-Line-Signature \\ \hline
ข้อมูลส่งออก (Output) & รายการเหตุการณ์ (Webhook Events), HTTP 200 OK Response \\ \hline
ตรรกะการประมวลผล & 1. ตรวจสอบลายเซ็นดิจิทัล X-Line-Signature ด้วย Channel Secret และ HMAC-SHA256 \newline
2. หากลายเซ็นไม่ถูกต้อง ให้ปฏิเสธคำขอและส่งรหัส HTTP 400 Bad Request \newline
3. แยกวิเคราะห์ JSON Payload ออกเป็นรายการ Event แต่ละรายการ \newline
4. ตรวจสอบประเภท Event (MessageEvent, FollowEvent, PostbackEvent) \newline
5. ส่งต่อข้อความไปยังกระบวนการประมวลผลคลังความรู้ RAG หรือคำสั่งที่เกี่ยวข้อง \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Process Specification: Process 4.2 จัดโครงสร้างและส่งกลับ LINE Flex Message}
\label{tab3:pspec4_2}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสกระบวนการ & 4.2 \\ \hline
ชื่อกระบวนการ & จัดรูปแบบและตอบกลับ Flex Message (Format and Reply Flex Message) \\ \hline
ข้อมูลนำเข้า (Input) & ข้อความคำตอบ, ลิงก์อ้างอิง, ข้อมูลสินค้า, Reply Token \\ \hline
ข้อมูลส่งออก (Output) & LINE Flex Message JSON Payload, สถานะการส่งสำเร็จ \\ \hline
ตรรกะการประมวลผล & 1. สร้างโครงสร้าง Bubble Container ตามรูปแบบมาตรฐาน LINE Flex Message \newline
2. ใส่รูปภาพประกอบ หัวข้อข้อความ รายละเอียดคำตอบ และปุ่มทางลัดไปยังลิงก์ที่เกี่ยวข้อง \newline
3. เรียกใช้ LINE Messaging API method replyMessage ด้วย Reply Token \newline
4. ตรวจสอบการตอบสนองจาก LINE API และบันทึกประวัติการส่งข้อความ \\ \hline
\end{tabularx}
\end{table}

\section{พจนานุกรมข้อมูล (Data Flow Dictionary)}
\hspace*{1.3em}
พจนานุกรมข้อมูลทำหน้าที่อธิบายรายละเอียดของกระแสข้อมูล (Data Flow) ทุกเส้นที่เชื่อมโยงระหว่างเอนทิตีภายนอก กระบวนการ และแหล่งจัดเก็บข้อมูลในระบบ โดยระบุชื่อกระแสข้อมูล คำอธิบาย แหล่งกำเนิด กระบวนการ ปลายทาง และโครงสร้างข้อมูล ดังแสดงในตารางที่ 3-17 ถึงตารางที่ 3-26:

\begin{table}[htbp]
\centering
\caption{Data Dictionary: ข้อมูลการเข้าสู่ระบบ (Login Credentials)}
\label{tab3:df_login}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & ข้อมูลการเข้าสู่ระบบ (Login Credentials) \\ \hline
คำอธิบาย & ข้อมูลที่ผู้ใช้งานป้อนเพื่อขอยืนยันตัวตนเข้าสู่ระบบเว็บแอปพลิเคชัน \\ \hline
แหล่งกำเนิด (Source) & ผู้ใช้งาน (Admin / Employee) \\ \hline
กระบวนการ (Process) & 1.1 ตรวจสอบการเข้าสู่ระบบ \\ \hline
ปลายทาง (Destination) & ฐานข้อมูล D1: users \\ \hline
โครงสร้างข้อมูล & username + password + [line\_user\_id] + timestamp + ip\_address \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: โทเค็นและเซสชันผู้ใช้งาน (Authentication Token)}
\label{tab3:df_token}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & โทเค็นยืนยันตัวตน (Authentication Token \& Session Data) \\ \hline
คำอธิบาย & ข้อมูลการรับรองความถูกต้องของเซสชันที่สร้างขึ้นหลังผ่านการยืนยันตัวตนสำเร็จ \\ \hline
แหล่งกำเนิด (Source) & กระบวนการ 1.1 หรือ 1.2 \\ \hline
กระบวนการ (Process) & 1.0 ตรวจสอบสิทธิ์และจัดการผู้ใช้งาน \\ \hline
ปลายทาง (Destination) & เบราว์เซอร์ผู้ใช้งาน (Web Client Session Storage / Cookie) \\ \hline
โครงสร้างข้อมูล & jwt\_token + user\_id + username + role + org\_id + expires\_at \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: ข้อมูลโปรไฟล์ผู้ใช้งาน (User Profile Data)}
\label{tab3:df_profile}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & ข้อมูลโปรไฟล์ผู้ใช้งาน (User Profile Data) \\ \hline
คำอธิบาย & ข้อมูลส่วนบุคคลของผู้ใช้งานในระบบ เช่น ชื่อ-นามสกุล อีเมล บทบาท และสถานะ \\ \hline
แหล่งกำเนิด (Source) & ผู้ใช้งาน หรือ ผู้ดูแลระบบ \\ \hline
กระบวนการ (Process) & 1.3 จัดการโปรไฟล์และสิทธิ์ผู้ใช้งาน \\ \hline
ปลายทาง (Destination) & ฐานข้อมูล D1: users \\ \hline
โครงสร้างข้อมูล & user\_id + username + display\_name + email + role + org\_id + updated\_at \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: ไฟล์เอกสารคลังความรู้ (Knowledge Documents)}
\label{tab3:df_doc}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & ไฟล์เอกสารคลังความรู้ (Knowledge Documents Payload) \\ \hline
คำอธิบาย & ไฟล์คู่มือสินค้า นโยบายบริษัท และระเบียบปฏิบัติที่อัปโหลดเข้าสู่ระบบ RAG \\ \hline
แหล่งกำเนิด (Source) & ผู้ดูแลระบบ (Admin ผ่านหน้าจัดการคลังความรู้) \\ \hline
กระบวนการ (Process) & 2.1 ตรวจสอบและนำเข้าไฟล์เอกสาร \\ \hline
ปลายทาง (Destination) & ฐานข้อมูล D3: documents และระบบจัดเก็บไฟล์ในเซิร์ฟเวอร์ \\ \hline
โครงสร้างข้อมูล & doc\_id + file\_name + file\_bytes + file\_type + file\_size + file\_hash + upload\_date \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: ท่อนข้อความที่สกัดได้ (Document Chunks)}
\label{tab3:df_chunks}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & ท่อนข้อความที่สกัดได้ (Document Chunks) \\ \hline
คำอธิบาย & เนื้อหาข้อความย่อยที่ผ่านการทำความสะอาดและตัดแบ่งตามขนาดที่กำหนด \\ \hline
แหล่งกำเนิด (Source) & กระบวนการ 2.2 สกัดข้อความและตัดแบ่งท่อนข้อมูล \\ \hline
กระบวนการ (Process) & 2.3 สร้างเวกเตอร์เอ็มเบดดิง \\ \hline
ปลายทาง (Destination) & ฐานข้อมูล D4: document\_chunks \\ \hline
โครงสร้างข้อมูล & chunk\_id + doc\_id + chunk\_index + chunk\_text + page\_number + char\_length \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: เวกเตอร์เอ็มเบดดิง (Embedding Vectors)}
\label{tab3:df_vectors}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & เวกเตอร์เอ็มเบดดิง (Dense Embedding Vectors) \\ \hline
คำอธิบาย & เวกเตอร์ตัวเลขหลายมิติที่แทนความหมายเชิงบริบทของท่อนข้อความ \\ \hline
แหล่งกำเนิด (Source) & กระบวนการ 2.3 สร้างเวกเตอร์เอ็มเบดดิง (FastEmbed) \\ \hline
กระบวนการ (Process) & 2.4 บันทึกและทำดัชนีเวกเตอร์ใน ChromaDB \\ \hline
ปลายทาง (Destination) & ฐานข้อมูลเวกเตอร์ D5: vector\_store (ChromaDB) \\ \hline
โครงสร้างข้อมูล & vector\_id + chunk\_id + org\_id + float\_array[384] + metadata\_json \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: ข้อความคำถามของผู้ใช้งาน (User Question Payload)}
\label{tab3:df_question}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & ข้อความคำถามของผู้ใช้งาน (User Question Payload) \\ \hline
คำอธิบาย & ข้อความภาษาธรรมชาติที่พนักงานพิมพ์สอบถามข้อมูลสินค้าหรือระเบียบผ่าน LINE \\ \hline
แหล่งกำเนิด (Source) & แพลตฟอร์ม LINE (LINE Messaging API Webhook) \\ \hline
กระบวนการ (Process) & 4.1 ตรวจสอบและรับเหตุการณ์ LINE Webhook \\ \hline
ปลายทาง (Destination) & กระบวนการ 2.5 ค้นคืนท่อนข้อความตามความคล้ายคลึง \\ \hline
โครงสร้างข้อมูล & line\_user\_id + message\_id + query\_text + timestamp + reply\_token \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: บริบทเอกสารที่ค้นคืนได้ (Retrieved Context)}
\label{tab3:df_context}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & บริบทเอกสารที่ค้นคืนได้ (Retrieved Context Chunks) \\ \hline
คำอธิบาย & รายการท่อนข้อความที่มีคะแนนความคล้ายคลึงสูงสุดที่ดึงมาจาก ChromaDB \\ \hline
แหล่งกำเนิด (Source) & ฐานข้อมูลเวกเตอร์ D5: vector\_store \\ \hline
กระบวนการ (Process) & 2.6 สังเคราะห์คำตอบด้วย Google Gemini \\ \hline
ปลายทาง (Destination) & โมเดลภาษาขนาดใหญ่ Google Gemini API \\ \hline
โครงสร้างข้อมูล & array\_of\_chunks[chunk\_text + similarity\_score + doc\_name + page\_num] \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: คำตอบภาษาธรรมชาติจาก AI (AI Synthesized Answer)}
\label{tab3:df_ai_answer}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & คำตอบภาษาธรรมชาติจาก AI (AI Synthesized Answer) \\ \hline
คำอธิบาย & ข้อความคำตอบที่โมเดลภาษาขนาดใหญ่สร้างขึ้นโดยอ้างอิงจากบริบทเอกสารจริง \\ \hline
แหล่งกำเนิด (Source) & Google Gemini 1.5 Flash API \\ \hline
กระบวนการ (Process) & 4.2 จัดโครงสร้างและส่งกลับ LINE Flex Message \\ \hline
ปลายทาง (Destination) & กระบวนการตอบกลับข้อความ \\ \hline
โครงสร้างข้อมูล & generated\_answer\_text + confidence\_level + source\_citations + processing\_time \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Dictionary: ข้อความตอบกลับ Flex Message (LINE Flex Message Payload)}
\label{tab3:df_flex_reply}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
ชื่อกระแสข้อมูล & ข้อความตอบกลับ Flex Message (LINE Flex Message Payload) \\ \hline
คำอธิบาย & ชุดข้อมูลการ์ดข้อความพร้อมรูปแบบ UI และปุ่มแอ็กชันส่งกลับไปยังแชท LINE \\ \hline
แหล่งกำเนิด (Source) & กระบวนการ 4.2 จัดโครงสร้างและส่งกลับ LINE Flex Message \\ \hline
กระบวนการ (Process) & 4.0 เชื่อมต่อและสื่อสารผ่านแพลตฟอร์ม LINE \\ \hline
ปลายทาง (Destination) & ผู้ใช้งาน LINE (พนักงาน บริษัท ฮาร์ทวอมมิ่ง จำกัด) \\ \hline
โครงสร้างข้อมูล & reply\_token + flex\_container\_json[header, hero\_image, body, footer\_buttons] \\ \hline
\end{tabularx}
\end{table}

\section{การออกแบบข้อมูล (Data Element Description)}
\hspace*{1.3em}
การออกแบบข้อมูล (Data Element Description) เป็นการอธิบายคุณลักษณะเฉพาะของตัวแปรหรือฟิลด์ข้อมูลแต่ละตัวในระบบ เช่น รหัสข้อมูล ชนิดข้อมูล ขนาด รูปแบบ และตารางที่สังกัด ดังแสดงในตารางที่ 3-27 ถึงตารางที่ 3-42:

\begin{table}[htbp]
\centering
\caption{Data Element Description: รหัสผู้ใช้งาน (id)}
\label{tab3:de_id}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-001 \\ \hline
ชื่อรายการข้อมูล & รหัสผู้ใช้งาน (id) \\ \hline
คำอธิบาย & ตัวเลขรหัสประจำตัวของผู้ใช้งานในระบบ สร้างอัตโนมัติ (Primary Key) \\ \hline
ชนิดข้อมูล (Data Type) & Integer \\ \hline
ความยาว (Length) & - \\ \hline
รูปแบบข้อมูล (Data Format) & ตัวเลขจำนวนเต็มบวก \\ \hline
ตารางข้อมูล (Table) & users (D1) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: ชื่อบัญชีผู้ใช้งาน (username)}
\label{tab3:de_username}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-002 \\ \hline
ชื่อรายการข้อมูล & ชื่อบัญชีผู้ใช้งาน (username) \\ \hline
คำอธิบาย & ชื่อบัญชีสำหรับเข้าสู่ระบบ มีค่าไม่ซ้ำกันในระบบ \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 50 \\ \hline
รูปแบบข้อมูล (Data Format) & ตัวอักษรภาษาอังกฤษและตัวเลข เช่น user01 \\ \hline
ตารางข้อมูล (Table) & users (D1) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: อีเมล (email)}
\label{tab3:de_email}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-003 \\ \hline
ชื่อรายการข้อมูล & อีเมลผู้ใช้งาน (email) \\ \hline
คำอธิบาย & อีเมลสำหรับติดต่อ กู้คืนรหัสผ่าน และการแจ้งเตือน \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 100 \\ \hline
รูปแบบข้อมูล (Data Format) & รูปแบบอีเมลมาตรฐาน เช่น employee@heartwarming.co.th \\ \hline
ตารางข้อมูล (Table) & users (D1) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: รหัสผ่านที่แฮช (password\_hash)}
\label{tab3:de_pwd}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-004 \\ \hline
ชื่อรายการข้อมูล & รหัสผ่านที่ผ่านการแฮช (password\_hash) \\ \hline
คำอธิบาย & ข้อความรหัสผ่านที่ผ่านการเข้ารหัสทางเดียวด้วยอัลกอริทึม BCrypt \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 255 \\ \hline
รูปแบบข้อมูล (Data Format) & ข้อความสตริงแฮช 60 ตัวอักษร เช่น \$2b\$12\$e8X... \\ \hline
ตารางข้อมูล (Table) & users (D1) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: รหัสบัญชี LINE (line\_user\_id)}
\label{tab3:de_line_id}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-005 \\ \hline
ชื่อรายการข้อมูล & รหัสประจำตัวผู้ใช้บน LINE (line\_user\_id) \\ \hline
คำอธิบาย & รหัสเฉพาะที่ออกโดยแพลตฟอร์ม LINE สำหรับระบุตัวตนของผู้ใช้ \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 64 \\ \hline
รูปแบบข้อมูล (Data Format) & ตัวอักษรและตัวเลขขึ้นต้นด้วย U เช่น U1234567890abcdef... \\ \hline
ตารางข้อมูล (Table) & users (D1) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: ระดับบทบาทและสิทธิ์ (role)}
\label{tab3:de_role}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-006 \\ \hline
ชื่อรายการข้อมูล & ระดับบทบาทสิทธิ์ (role) \\ \hline
คำอธิบาย & ระดับสิทธิ์ในการเข้าถึงและใช้งานระบบตามหลักการ RBAC \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 20 \\ \hline
รูปแบบข้อมูล (Data Format) & admin, manager, employee, user \\ \hline
ตารางข้อมูล (Table) & users (D1) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: รหัสองค์กร (org\_id)}
\label{tab3:de_org_id}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-007 \\ \hline
ชื่อรายการข้อมูล & รหัสองค์กร (org\_id) \\ \hline
คำอธิบาย & รหัสประจำตัวองค์กรหรือบริษัท สำหรับแยกข้อมูล Multi-Tenant \\ \hline
ชนิดข้อมูล (Data Type) & Integer \\ \hline
ความยาว (Length) & - \\ \hline
รูปแบบข้อมูล (Data Format) & ตัวเลขจำนวนเต็มบวก (เช่น 1 = บริษัท ฮาร์ทวอมมิ่ง จำกัด) \\ \hline
ตารางข้อมูล (Table) & organizations (D2), users (D1), documents (D3) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: ชื่อองค์กร (org\_name)}
\label{tab3:de_org_name}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-008 \\ \hline
ชื่อรายการข้อมูล & ชื่อองค์กรหรือบริษัท (org\_name) \\ \hline
คำอธิบาย & ชื่อทางการขององค์กร \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 100 \\ \hline
รูปแบบข้อมูล (Data Format) & ข้อความ เช่น บริษัท ฮาร์ทวอมมิ่ง จำกัด \\ \hline
ตารางข้อมูล (Table) & organizations (D2) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: รหัสเอกสาร (doc\_id)}
\label{tab3:de_doc_id}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-009 \\ \hline
ชื่อรายการข้อมูล & รหัสเอกสาร (doc\_id) \\ \hline
คำอธิบาย & รหัสประจำตัวเอกสารที่นำเข้าสู่คลังความรู้ RAG \\ \hline
ชนิดข้อมูล (Data Type) & Integer \\ \hline
ความยาว (Length) & - \\ \hline
รูปแบบข้อมูล (Data Format) & ตัวเลขจำนวนเต็มบวก (Auto Increment) \\ \hline
ตารางข้อมูล (Table) & documents (D3), document\_chunks (D4) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: ชื่อไฟล์เอกสาร (file\_name)}
\label{tab3:de_file_name}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-010 \\ \hline
ชื่อรายการข้อมูล & ชื่อไฟล์เอกสาร (file\_name) \\ \hline
คำอธิบาย & ชื่อไฟล์เอกสารต้นฉบับที่อัปโหลดเข้าสู่ระบบ \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 255 \\ \hline
รูปแบบข้อมูล (Data Format) & ข้อความพร้อมนามสกุล เช่น duit\_manual\_th.pdf \\ \hline
ตารางข้อมูล (Table) & documents (D3) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: รหัสท่อนข้อความ (chunk\_id)}
\label{tab3:de_chunk_id}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-011 \\ \hline
ชื่อรายการข้อมูล & รหัสท่อนข้อความ (chunk\_id) \\ \hline
คำอธิบาย & รหัสเฉพาะของท่อนข้อความย่อยที่ถูกตัดแบ่งจากเอกสาร \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 64 \\ \hline
รูปแบบข้อมูล (Data Format) & สตริงรหัสผสม เช่น doc1\_chunk\_005 \\ \hline
ตารางข้อมูล (Table) & document\_chunks (D4), vector\_store (D5) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: เนื้อหาท่อนข้อความ (chunk\_text)}
\label{tab3:de_chunk_text}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-012 \\ \hline
ชื่อรายการข้อมูล & เนื้อหาท่อนข้อความ (chunk\_text) \\ \hline
คำอธิบาย & ข้อความส่วนย่อยที่สกัดและตัดแบ่งจากเอกสารสำหรับนำไปฝังเวกเตอร์ \\ \hline
ชนิดข้อมูล (Data Type) & Text \\ \hline
ความยาว (Length) & - \\ \hline
รูปแบบข้อมูล (Data Format) & ข้อความภาษาไทยหรือภาษาอังกฤษความยาวประมาณ 500-1,000 ตัวอักษร \\ \hline
ตารางข้อมูล (Table) & document\_chunks (D4) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: เวกเตอร์เอ็มเบดดิง (embedding\_vector)}
\label{tab3:de_vector}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-013 \\ \hline
ชื่อรายการข้อมูล & เวกเตอร์เอ็มเบดดิง (embedding\_vector) \\ \hline
คำอธิบาย & อาร์เรย์ของตัวเลขทศนิยมที่แสดงตำแหน่งเชิงความหมายในปริภูมิเวกเตอร์ \\ \hline
ชนิดข้อมูล (Data Type) & Array of Float \\ \hline
ความยาว (Length) & 384 หรือ 768 มิติ \\ \hline
รูปแบบข้อมูล (Data Format) & [-0.0421, 0.0815, ..., 0.0129] \\ \hline
ตารางข้อมูล (Table) & vector\_store (D5: ChromaDB) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: รหัสไฟล์บน Google Drive (drive\_file\_id)}
\label{tab3:de_drive_id}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-014 \\ \hline
ชื่อรายการข้อมูล & รหัสไฟล์บน Google Drive (drive\_file\_id) \\ \hline
คำอธิบาย & รหัสอ้างอิงไฟล์ที่ออกโดย Google Drive API \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 100 \\ \hline
รูปแบบข้อมูล (Data Format) & สตริงรหัสตัวอักษรและตัวเลข เช่น 1A2b3C4d5E... \\ \hline
ตารางข้อมูล (Table) & drive\_logs (D6) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: ข้อความคำถาม (query\_text)}
\label{tab3:de_query}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-015 \\ \hline
ชื่อรายการข้อมูล & ข้อความคำถามของผู้ใช้ (query\_text) \\ \hline
คำอธิบาย & ข้อความคำถามภาษาธรรมชาติที่ส่งเข้ามาผ่านช่องแชท LINE OA \\ \hline
ชนิดข้อมูล (Data Type) & Text \\ \hline
ความยาว (Length) & - \\ \hline
รูปแบบข้อมูล (Data Format) & ข้อความ เช่น สินค้า duit น้ำพุแมว มีการรับประกันกี่เดือน? \\ \hline
ตารางข้อมูล (Table) & line\_sessions (D5), audit\_logs \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{Data Element Description: โทเค็นการตอบกลับ LINE (reply\_token)}
\label{tab3:de_reply_token}
\begin{tabularx}{\textwidth}{| c | L |}
\hline
\textbf{หัวข้อ} & \textbf{รายละเอียด} \\ \hline
รหัสรายการข้อมูล & DE-016 \\ \hline
ชื่อรายการข้อมูล & โทเค็นการตอบกลับ LINE (reply\_token) \\ \hline
คำอธิบาย & โทเค็นชั่วคราวที่ใช้สำหรับตอบกลับข้อความผ่าน LINE Messaging API \\ \hline
ชนิดข้อมูล (Data Type) & Varchar \\ \hline
ความยาว (Length) & 64 \\ \hline
รูปแบบข้อมูล (Data Format) & สตริงรหัสเฉพาะ มีอายุการใช้งานสั้น (ใช้งานได้ครั้งเดียว) \\ \hline
ตารางข้อมูล (Table) & line\_sessions (D5) \\ \hline
\end{tabularx}
\end{table}

\section{การออกแบบฐานข้อมูล (Database Design)}
\hspace*{1.3em}
การออกแบบฐานข้อมูลเชิงสัมพันธ์ของระบบ OrgChat AI ถูกจัดโครงสร้างตามกฎการนอร์มัลไลเซชันระดับที่ 3 (3NF) เพื่อรักษาบูรณภาพของข้อมูล (Data Integrity) โดยมีแบบจำลองความสัมพันธ์ของข้อมูล (Entity Relationship Diagram: ER Diagram) แสดงดังภาพที่ 3-4:

\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{Image/fig3_8_er_diagram.png}
\caption{Entity Relationship Diagram (ER Diagram) ของระบบ OrgChat AI}
\label{fig3:er_diagram}
\end{figure}

\subsection{รายการตารางข้อมูลในระบบ (Table List)}
\hspace*{1.3em}
ระบบฐานข้อมูลในภาคการศึกษาที่ 1/2569 ประกอบด้วยตารางข้อมูลหลักจำนวน 7 ตาราง ดังแสดงสรุปในตารางที่ 3-43:

\begin{table}[htbp]
\centering
\caption{รายชื่อตารางทั้งหมดในระบบฐานข้อมูล (Table List)}
\label{tab3:tablelist}
\begin{tabularx}{\textwidth}{| c | L | c | c |}
\hline
\textbf{ลำดับ} & \textbf{ชื่อตารางข้อมูล (Table Name)} & \textbf{ชื่อเอนทิตีภาษาไทย} & \textbf{คีย์หลัก (Primary Key)} \\ \hline
1 & users & ข้อมูลบัญชีผู้ใช้งานระบบ & id \\ \hline
2 & organizations & ข้อมูลบริษัทและองค์กร & id \\ \hline
3 & documents & ข้อมูลเอกสารในคลังความรู้ & id \\ \hline
4 & document\_chunks & ข้อมูลท่อนข้อความเอกสาร & id \\ \hline
5 & line\_sessions & ข้อมูลเซสชันการสนทนา LINE & id \\ \hline
6 & drive\_logs & บันทึกประวัติไฟล์บน Google Drive & id \\ \hline
7 & audit\_logs & บันทึกประวัติความปลอดภัยและการทำงาน & id \\ \hline
\end{tabularx}
\end{table}

\subsection{โครงสร้างตารางข้อมูลอย่างละเอียด (Table Layouts)}
\hspace*{1.3em}
รายละเอียดโครงสร้างของแต่ละตารางในฐานข้อมูล แสดงดังตารางที่ 3-44 ถึงตารางที่ 3-50:

\begin{table}[htbp]
\centering
\caption{โครงสร้างตารางข้อมูล users (ผู้ใช้งานระบบ)}
\label{tab3:tb_users}
\begin{tabularx}{\textwidth}{| c | c | c | c | c | L |}
\hline
\textbf{Attribute} & \textbf{Type} & \textbf{Length} & \textbf{Key} & \textbf{Null} & \textbf{Description} \\ \hline
id & INTEGER & - & PK & No & รหัสประจำตัวผู้ใช้ (Auto Increment) \\ \hline
username & VARCHAR & 50 & Unique & No & ชื่อบัญชีผู้ใช้งาน \\ \hline
password\_hash & VARCHAR & 255 & - & No & รหัสผ่านที่เข้ารหัสแฮชด้วย BCrypt \\ \hline
role & VARCHAR & 20 & - & No & ระดับบทบาท (admin, manager, user) \\ \hline
email & VARCHAR & 100 & - & Yes & อีเมลติดต่อของผู้ใช้งาน \\ \hline
display\_name & VARCHAR & 100 & - & Yes & ชื่อ-นามสกุลที่ใช้แสดงผล \\ \hline
line\_user\_id & VARCHAR & 64 & - & Yes & รหัสประจำตัวบนแพลตฟอร์ม LINE \\ \hline
org\_id & INTEGER & - & FK & Yes & รหัสองค์กรที่สังกัด (อ้างอิง organizations.id) \\ \hline
created\_at & DATETIME & - & - & No & วันและเวลาที่สร้างบัญชี \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{โครงสร้างตารางข้อมูล organizations (ข้อมูลองค์กร)}
\label{tab3:tb_orgs}
\begin{tabularx}{\textwidth}{| c | c | c | c | c | L |}
\hline
\textbf{Attribute} & \textbf{Type} & \textbf{Length} & \textbf{Key} & \textbf{Null} & \textbf{Description} \\ \hline
id & INTEGER & - & PK & No & รหัสประจำตัวองค์กร (Auto Increment) \\ \hline
org\_name & VARCHAR & 100 & - & No & ชื่อบริษัท (บจก. ฮาร์ทวอมมิ่ง) \\ \hline
domain & VARCHAR & 100 & - & Yes & โดเมนเนมอีเมลขององค์กร \\ \hline
line\_channel\_token & TEXT & - & - & Yes & Channel Access Token ของ LINE OA \\ \hline
created\_at & DATETIME & - & - & No & วันและเวลาที่ลงทะเบียนองค์กร \\ \hline
status & VARCHAR & 20 & - & No & สถานะการใช้งาน (Active, Suspended) \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{โครงสร้างตารางข้อมูล documents (เอกสารคลังความรู้)}
\label{tab3:tb_docs}
\begin{tabularx}{\textwidth}{| c | c | c | c | c | L |}
\hline
\textbf{Attribute} & \textbf{Type} & \textbf{Length} & \textbf{Key} & \textbf{Null} & \textbf{Description} \\ \hline
id & INTEGER & - & PK & No & รหัสประจำตัวเอกสาร (Auto Increment) \\ \hline
file\_name & VARCHAR & 255 & - & No & ชื่อไฟล์เอกสารต้นฉบับ \\ \hline
file\_path & VARCHAR & 500 & - & No & ตำแหน่งจัดเก็บไฟล์บนเซิร์ฟเวอร์ \\ \hline
file\_hash & VARCHAR & 64 & - & No & ค่าแฮช SHA-256 สำหรับตรวจไฟล์ซ้ำ \\ \hline
file\_size & INTEGER & - & - & No & ขนาดของไฟล์เอกสาร (ไบต์) \\ \hline
file\_type & VARCHAR & 20 & - & No & นามสกุลไฟล์ (pdf, docx, txt, xlsx) \\ \hline
org\_id & INTEGER & - & FK & No & รหัสองค์กรเจ้าของเอกสาร \\ \hline
uploaded\_by & INTEGER & - & FK & No & รหัสผู้ใช้อัปโหลด (อ้างอิง users.id) \\ \hline
status & VARCHAR & 20 & - & No & สถานะเอกสาร (PROCESSING, READY, ERROR) \\ \hline
created\_at & DATETIME & - & - & No & วันเวลาที่อัปโหลดเอกสาร \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{โครงสร้างตารางข้อมูล document\_chunks (ท่อนข้อความเอกสาร)}
\label{tab3:tb_chunks}
\begin{tabularx}{\textwidth}{| c | c | c | c | c | L |}
\hline
\textbf{Attribute} & \textbf{Type} & \textbf{Length} & \textbf{Key} & \textbf{Null} & \textbf{Description} \\ \hline
id & INTEGER & - & PK & No & รหัสประจำตัวท่อนข้อความ (Auto Increment) \\ \hline
doc\_id & INTEGER & - & FK & No & รหัสเอกสารต้นทาง (อ้างอิง documents.id) \\ \hline
chunk\_index & INTEGER & - & - & No & ลำดับของท่อนข้อความในเอกสาร \\ \hline
chunk\_text & TEXT & - & - & No & เนื้อหาข้อความของท่อนข้อมูล \\ \hline
page\_number & INTEGER & - & - & Yes & เลขหน้าที่พบท่อนข้อความในเอกสาร \\ \hline
vector\_id & VARCHAR & 64 & - & Yes & รหัสอ้างอิงเวกเตอร์ใน ChromaDB \\ \hline
created\_at & DATETIME & - & - & No & วันเวลาที่สร้างท่อนข้อความ \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{โครงสร้างตารางข้อมูล line\_sessions (เซสชันการสนทนา LINE)}
\label{tab3:tb_sessions}
\begin{tabularx}{\textwidth}{| c | c | c | c | c | L |}
\hline
\textbf{Attribute} & \textbf{Type} & \textbf{Length} & \textbf{Key} & \textbf{Null} & \textbf{Description} \\ \hline
id & INTEGER & - & PK & No & รหัสบันทึกเซสชัน (Auto Increment) \\ \hline
line\_user\_id & VARCHAR & 64 & - & No & รหัสผู้ใช้งานบน LINE \\ \hline
last\_message & TEXT & - & - & Yes & ข้อความล่าสุดที่ส่งเข้ามา \\ \hline
last\_reply & TEXT & - & - & Yes & ข้อความตอบกลับล่าสุดจากระบบ \\ \hline
context\_state & VARCHAR & 50 & - & Yes & สถานะบริบทการสนทนาปัจจุบัน \\ \hline
updated\_at & DATETIME & - & - & No & วันเวลาที่มีการโต้ตอบล่าสุด \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{โครงสร้างตารางข้อมูล drive\_logs (ประวัติไฟล์บน Google Drive)}
\label{tab3:tb_drive}
\begin{tabularx}{\textwidth}{| c | c | c | c | c | L |}
\hline
\textbf{Attribute} & \textbf{Type} & \textbf{Length} & \textbf{Key} & \textbf{Null} & \textbf{Description} \\ \hline
id & INTEGER & - & PK & No & รหัสบันทึกประวัติไฟล์ (Auto Increment) \\ \hline
file\_name & VARCHAR & 255 & - & No & ชื่อไฟล์ที่อัปโหลดขึ้น Drive \\ \hline
drive\_file\_id & VARCHAR & 100 & - & No & รหัสไฟล์จาก Google Drive API \\ \hline
drive\_url & VARCHAR & 500 & - & Yes & ลิงก์ URL สำหรับเข้าถึงไฟล์ \\ \hline
folder\_path & VARCHAR & 255 & - & Yes & โฟลเดอร์ปลายทางบน Drive \\ \hline
org\_id & INTEGER & - & FK & No & รหัสองค์กรเจ้าของไฟล์ \\ \hline
uploaded\_by & VARCHAR & 64 & - & Yes & ผู้ส่งไฟล์ (line\_user\_id หรือ username) \\ \hline
created\_at & DATETIME & - & - & No & วันเวลาที่จัดเก็บไฟล์ \\ \hline
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{โครงสร้างตารางข้อมูล audit\_logs (บันทึกกิจกรรมความปลอดภัย)}
\label{tab3:tb_audit}
\begin{tabularx}{\textwidth}{| c | c | c | c | c | L |}
\hline
\textbf{Attribute} & \textbf{Type} & \textbf{Length} & \textbf{Key} & \textbf{Null} & \textbf{Description} \\ \hline
id & INTEGER & - & PK & No & รหัสบันทึกกิจกรรม (Auto Increment) \\ \hline
user\_id & VARCHAR & 50 & - & No & ผู้ใช้ที่ทำกิจกรรมในระบบ \\ \hline
action & VARCHAR & 100 & - & No & ประเภทกิจกรรม (LOGIN, RAG\_QUERY, UPLOAD) \\ \hline
details & TEXT & - & - & Yes & รายละเอียดหรือพารามิเตอร์ของกิจกรรม \\ \hline
ip\_address & VARCHAR & 45 & - & Yes & หมายเลข IP Address ของเครื่องผู้ใช้ \\ \hline
created\_at & DATETIME & - & - & No & วันเวลาที่เกิดกิจกรรมตามเวลาเซิร์ฟเวอร์ \\ \hline
\end{tabularx}
\end{table}

\section{การออกแบบส่วนต่อประสานผู้ใช้ (User Interface Design)}
\hspace*{1.3em}
การออกแบบส่วนต่อประสานผู้ใช้ (UI/UX Design) มุ่งเน้นการใช้งานที่ง่ายและตอบโจทย์พนักงาน บริษัท ฮาร์ทวอมมิ่ง จำกัด โดยออกแบบเส้นทางการทำงาน (Screen Flow) เชื่อมโยงระหว่างแอปพลิเคชัน LINE OA กับเว็บแอปพลิเคชันระบบบริหารจัดการ ดังแสดงในภาพที่ 3-5:

\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{Image/fig3_9_screen_flow.png}
\caption{แผนผังลำดับการทำงานของหน้าจอ (Screen Flow Diagram)}
\label{fig3:screen_flow}
\end{figure}

\subsection{การออกแบบหน้าจอหลักของระบบ (Main Screen Layouts)}
\hspace*{1.3em}
การออกแบบหน้าจอของระบบในภาคการศึกษาที่ 1/2569 ประกอบด้วย 3 ส่วนสำคัญ ได้แก่:
\begin{enumerate}[leftmargin=3.5em]
\item \textbf{หน้าจอเข้าสู่ระบบและยืนยันตัวตน (Login Screen):} ออกแบบฟอร์มการเข้าสู่ระบบแบบ Responsive รองรับการกรอก Username/Password สำหรับผู้ดูแลระบบ และปุ่มกดเข้าสู่ระบบผ่าน LINE Login OAuth 2.0 สำหรับพนักงาน เพื่อความสะดวกรวดเร็ว
\item \textbf{หน้าจอจัดการคลังความรู้ (Knowledge Base Management Screen):} หน้าจอเว็บสำหรับผู้ดูแลระบบ แสดงรายการเอกสารที่อัปโหลด แถบแสดงสถานะการแปลงเวกเตอร์ (Processing / Ready) ขนาดไฟล์ จำนวนท่อนข้อความ (Chunks) และปุ่มสำหรับอัปโหลดไฟล์เอกสารใหม่
\item \textbf{หน้าต่างการสนทนา LINE Official Account (LINE OA Chat Screen):} หน้าต่างสนทนาบนแอปพลิเคชัน LINE ออกแบบ Rich Menu ด้านล่างสำหรับการสอบถามข้อมูลด่วน และการแสดงผลคำตอบด้วย LINE Flex Message ที่มีสีสันสวยงาม อ่านง่าย พร้อมปุ่มลิงก์ไปยังข้อมูลสินค้าเพิ่มเติม
\end{enumerate}
"""

target_files = [
    r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Project_030_Chapter3.tex',
    r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT\Project_030_Chapter3.tex'
]

for tf in target_files:
    os.makedirs(os.path.dirname(tf), exist_ok=True)
    with open(tf, 'w', encoding='utf-8') as f:
        f.write(chapter3_content.strip() + '\n')
    print(f'Successfully wrote {tf} (size: {os.path.getsize(tf)} bytes)')
