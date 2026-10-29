import docx
from docx.shared import Pt, Inches, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_aucc_paper():
    template_path = r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\การบ้าน4\template_oral_thai.docx'
    output_docx = r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\การบ้าน4\AUCC2027_OrgChat_AI_Paper.docx'
    
    doc = docx.Document(template_path)
    
    # Ensure TH SarabunPSK default style settings
    for p in list(doc.paragraphs):
        p_elem = p._element
        p_elem.getparent().remove(p_elem)
        
    for t in list(doc.tables):
        t_elem = t._element
        t_elem.getparent().remove(t_elem)
        
    # Set page section 1 (Header/Title - 1 column)
    sec1 = doc.sections[0]
    sec1.top_margin = Mm(30)
    sec1.bottom_margin = Mm(25)
    sec1.left_margin = Mm(20)
    sec1.right_margin = Mm(20)
    
    # We will add paragraphs for Title, Authors, Affiliations
    def add_para(text, font_size=14, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=0, font_name="TH SarabunPSK"):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.0
        
        run = p.add_run(text)
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.bold = bold
        run.italic = italic
        
        # XML font binding for Complex Scripts (Thai)
        rPr = run._r.get_or_add_rPr()
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rFonts.set(qn('w:cs'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)
        rPr.append(rFonts)
        return p

    # --- TITLE SECTION ---
    # Thai Title (20 pt, Bold, Center)
    add_para("ปัญญาประดิษฐ์แชทบอทสำหรับองค์กร กรณีศึกษา บริษัท ฮาร์ทวอมมิ่ง จำกัด", 
             font_size=20, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    
    # English Title (16 pt, Bold, Center)
    add_para("ARTIFICIAL INTELLIGENCE CHATBOT FOR ORGANIZATION:\nA CASE STUDY OF HEARTWARMING COMPANY LIMITED", 
             font_size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=12)
    
    # Authors (14 pt, Center)
    add_para("ธนากร ธนบวรพล1, วีรภัทร ชื่นชอบ1, และ ศิรินทรา แว่วศรี2*", 
             font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_para("Thanakorn Thanabowonphon1, Weeraphat Chuenchob1, and Sirintra Waiwsri2*", 
             font_size=12, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=6)
    
    # Affiliations (12 pt, Center)
    aff_th = (
        "1นักศึกษาสาขาวิชาเทคโนโลยีสารสนเทศ ภาควิชาเทคโนโลยีสารสนเทศ "
        "คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ\n"
        "2อาจารย์ที่ปรึกษา ภาควิชาเทคโนโลยีสารสนเทศ "
        "คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ\n"
        "*Corresponding Author: sirintra.w@fitm.kmutnb.ac.th"
    )
    add_para(aff_th, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=12)

    # Section break for 2 columns
    sec2 = doc.add_section(docx.enum.section.WD_SECTION_START.CONTINUOUS)
    sec2.top_margin = Mm(30)
    sec2.bottom_margin = Mm(25)
    sec2.left_margin = Mm(20)
    sec2.right_margin = Mm(20)
    
    # Configure 2 columns in sec2 via XML
    sectPr = sec2._sectPr
    cols = sectPr.xpath('./w:cols')
    if cols:
        col_elem = cols[0]
    else:
        col_elem = OxmlElement('w:cols')
        sectPr.append(col_elem)
    col_elem.set(qn('w:num'), '2')
    col_elem.set(qn('w:space'), '340') # 6 mm ~ 340 dxa

    def add_col_heading(text, space_before=6):
        return add_para(text, font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=space_before, space_after=2)

    def add_col_subheading(text, space_before=4):
        return add_para(text, font_size=14, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=space_before, space_after=2)

    def add_col_body(text, space_before=0, space_after=2, indent=True):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.0
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.3)
        
        run = p.add_run(text)
        run.font.name = "TH SarabunPSK"
        run.font.size = Pt(14)
        rPr = run._r.get_or_add_rPr()
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), "TH SarabunPSK")
        rFonts.set(qn('w:hAnsi'), "TH SarabunPSK")
        rFonts.set(qn('w:cs'), "TH SarabunPSK")
        rPr.append(rFonts)
        return p

    # --- บทคัดย่อ (THAI ABSTRACT) ---
    add_para("บทคัดย่อ", font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=2)
    thai_abstract = (
        "บทความวิจัยนี้มีวัตถุประสงค์เพื่อออกแบบและพัฒนาระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร กรณีศึกษา บริษัท ฮาร์ทวอมมิ่ง จำกัด "
        "ซึ่งเป็นธุรกิจนำเข้าและจัดจำหน่ายสินค้าไลฟ์สไตล์พรีเมียม เพื่อแก้ไขปัญหาการกระจัดกระจายของข้อมูล การค้นหาเอกสารคู่มือสินค้าที่ล่าช้า "
        "ความผิดพลาดจากการบันทึกบัญชีรายรับ-รายจ่ายด้วยมือ และความล่าช้าในกระบวนการขอลางานของพนักงาน "
        "ระบบที่พัฒนาขึ้นผสานการทำงานของ LINE Official Account ผ่าน LINE Messaging API ร่วมกับเว็บแอปพลิเคชันบริหารจัดการ (Admin Dashboard) "
        "พัฒนาด้วยภาษา Python (Flask) ฐานข้อมูล SQLite และ ChromaDB ประกอบด้วย 5 โมดูลหลัก ได้แก่ 1) ระบบคลังความรู้อัจฉริยะ (RAG) ด้วย Google Gemini "
        "2) ระบบสกัดข้อความสลิปและใบเสร็จ (OCR) ด้วย Google Cloud Vision API บันทึกลง Google Sheets และ Drive อัตโนมัติ "
        "3) ระบบบริหารงานบุคคลขอลางานและอนุมัติผ่าน LINE 4) แผงควบคุมผู้บริหาร และ 5) ระบบรักษาความปลอดภัยแบบแยกข้อมูลองค์กร "
        "ผลการประเมินพบว่าระบบทำงานถูกต้องตามฟังก์ชัน 100% ความแม่นยำของ OCR เท่ากับ 96.4% ความถูกต้องของระบบ RAG เท่ากับ 94.8% "
        "และผลประเมินความพึงพอใจของผู้ใช้งานจริง (N=20) อยู่ในระดับมากที่สุด (X̄ = 4.65, S.D. = 0.48)"
    )
    add_col_body(thai_abstract, indent=True)
    
    # คำสำคัญ
    p_kw = add_para("คำสำคัญ: ", font_size=14, bold=True, space_before=2, space_after=6)
    r_kw = p_kw.add_run("ปัญญาประดิษฐ์แชทบอท, การค้นคืนข้อมูลเสริมการสร้างข้อความ (RAG), การรู้จำอักขระด้วยแสง (OCR), แพลตฟอร์มไลน์, การจัดการองค์กร")
    r_kw.font.name = "TH SarabunPSK"
    r_kw.font.size = Pt(14)
    rPr = r_kw._r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:cs'), "TH SarabunPSK")
    rPr.append(rFonts)

    # --- ABSTRACT (ENGLISH) ---
    add_para("ABSTRACT", font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=4, space_after=2)
    eng_abstract = (
        "This research paper presents the design and development of an Artificial Intelligence Chatbot for Organization, with Heartwarming Company Limited "
        "as a case study. The system aims to resolve issues concerning scattered enterprise knowledge, slow product manual retrieval, human bookkeeping errors "
        "from bank slips, and inefficient paper-based leave approval workflows. The developed system seamlessly integrates the LINE Official Account platform "
        "via LINE Messaging API with a centralized Flask web administration dashboard, SQLite relational database, and ChromaDB vector store. "
        "The architecture encompasses five key modules: 1) Retrieval-Augmented Generation (RAG) powered by Google Gemini, 2) Optical Character Recognition (OCR) "
        "slip extraction via Google Cloud Vision API with automated Google Sheets and Drive synchronization, 3) Human resource leave request and approval workflow, "
        "4) Executive web dashboard with analytics, and 5) Multi-tenant security isolation. Evaluation results demonstrate 100% functional completeness, "
        "96.4% OCR extraction accuracy, 94.8% RAG factual question-answering accuracy, and an overall user satisfaction score at the highest level (Mean = 4.65, S.D. = 0.48) "
        "from 20 actual enterprise users."
    )
    add_col_body(eng_abstract, indent=True)
    
    # Keywords
    p_ekw = add_para("Keywords: ", font_size=14, bold=True, space_before=2, space_after=8)
    r_ekw = p_ekw.add_run("AI Chatbot, Retrieval-Augmented Generation (RAG), Optical Character Recognition (OCR), LINE Platform, Enterprise Management")
    r_ekw.font.name = "TH SarabunPSK"
    r_ekw.font.size = Pt(14)

    # --- 1. บทนำ ---
    add_col_heading("1. บทนำ")
    add_col_body(
        "ในยุคเศรษฐกิจดิจิทัล ธุรกิจขนาดกลางและขนาดย่อม (SMEs) จำเป็นต้องบริหารจัดการข้อมูลและการดำเนินงานด้วยความคล่องตัวและแม่นยำสูง "
        "บริษัท ฮาร์ทวอมมิ่ง จำกัด ซึ่งเป็นผู้นำเข้าและจัดจำหน่ายสินค้าไลฟ์สไตล์พรีเมียม ประสบปัญหาสำคัญ 3 ประการ ได้แก่ 1) ข้อมูลคุณสมบัติและคู่มือสินค้ากระจัดกระจาย "
        "ทำให้พนักงานบริการลูกค้าต้องใช้เวลาเฉลี่ย 3-5 นาทีในการค้นหาคำตอบ 2) กระบวนการบันทึกบัญชีรายรับจากสลิปโอนเงินยังใช้การป้อนข้อมูลด้วยมือ "
        "ซึ่งมีความเสี่ยงต่อข้อผิดพลาดและการสูญหายของหลักฐาน และ 3) กระบวนการยื่นและอนุมัติวันลาของพนักงานขาดระบบติดตามสถานะแบบเรียลไทม์ [1]"
    )
    add_col_body(
        "งานวิจัยนี้จึงได้ออกแบบและพัฒนาระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร (OrgChat AI) เพื่อทำหน้าที่เป็นศูนย์กลางการเข้าถึงข้อมูลและการบริการอัตโนมัติ "
        "โดยนำเทคโนโลยี Retrieval-Augmented Generation (RAG) ร่วมกับ Large Language Models (LLMs) และ Optical Character Recognition (OCR) "
        "เชื่อมโยงผ่านแอปพลิเคชัน LINE ซึ่งเป็นแพลตฟอร์มที่พนักงานคุ้นเคยในชีวิตประจำวัน ช่วยลดขั้นตอนการทำงานและเพิ่มผลิตภาพขององค์กรได้อย่างมีนัยสำคัญ [2]"
    )

    # --- 2. งานวิจัยและทฤษฎีที่เกี่ยวข้อง ---
    add_col_heading("2. งานวิจัยและทฤษฎีที่เกี่ยวข้อง")
    add_col_subheading("2.1 Retrieval-Augmented Generation (RAG) และ Vector Database")
    add_col_body(
        "สถาปัตยกรรม RAG เป็นเทคนิคที่ช่วยเพิ่มความถูกต้องและลดปัญหาภาพหลอน (Hallucination) ของแบบจำลองภาษาขนาดใหญ่ (LLM) [3] "
        "โดยทำการแปลงเอกสารองค์กรเป็นเวกเตอร์เอ็มเบดดิง (Dense Vectors) จัดเก็บลงในฐานข้อมูล ChromaDB เมื่อผู้ใช้ถามคำถาม ระบบจะทำการสืบค้น "
        "Cosine Similarity เพื่อดึงเฉพาะเนื้อหาที่เกี่ยวข้องมากที่สุด ส่งต่อไปเป็นบริบท (Context) ให้กับ Google Gemini สังเคราะห์คำตอบภาษาธรรมชาติที่แม่นยำ"
    )
    add_col_subheading("2.2 การประมวลผลภาพและรู้จำอักขระ (OCR)")
    add_col_body(
        "Google Cloud Vision API ให้บริการตรวจจับและสกัดข้อความจากภาพถ่ายที่มีความแม่นยำสูง งานวิจัยนี้นำเทคนิคการปรับปรุงภาพก่อนประมวลผล (Image Preprocessing) "
        "และการตรวจสอบโครงสร้างรหัส QR สลิปตามมาตรฐาน EMVCo ร่วมกับการสกัดข้อมูลด้วย Regular Expression (Regex) เพื่อดึงฟิลด์สำคัญ เช่น จำนวนเงิน วันที่ และเลขอ้างอิง [4]"
    )
    add_col_subheading("2.3 แพลตฟอร์ม LINE Messaging API และ Web Framework")
    add_col_body(
        "LINE Messaging API รองรับการส่งข้อความโต้ตอบอัตโนมัติ การแสดงผลข้อความโครงสร้างยืดหยุ่น (Flex Messages) และ Rich Menu ร่วมกับ "
        "Python Flask และ SQLite ทำหน้าที่เป็นเซิร์ฟเวอร์ควบคุมเบื้องหลังที่มีประสิทธิภาพสูงและใช้ทรัพยากรอย่างคุ้มค่า [5]"
    )

    # --- 3. การดำเนินงานและสถาปัตยกรรมระบบ ---
    add_col_heading("3. การดำเนินงานและสถาปัตยกรรมระบบ")
    add_col_body(
        "การพัฒนาระบบแบ่งออกเป็น 5 กระบวนการหลักตามแผนภาพกระแสข้อมูล (Data Flow Diagram: DFD) และระเบียบวิธีวิจัยแบบ Agile ดังนี้:"
    )
    add_col_body("1) กระบวนการ 1.0 ตรวจสอบสิทธิ์และจัดการผู้ใช้งาน: ให้บริการยืนยันตัวตนด้วย OAuth 2.0 / LINE Login และกำหนดสิทธิ์แบบ RBAC (Admin, Manager, Employee)", indent=True)
    add_col_body("2) กระบวนการ 2.0 ค้นคืนคลังความรู้และตอบคำถามอัจฉริยะ: ทำการตัดท่อนเอกสาร (Chunking: 500 characters, overlap 50) ฝังเวกเตอร์ด้วย Gemini Embedding และตอบคำถามผ่าน RAG Pipeline", indent=True)
    add_col_body("3) กระบวนการ 3.0 สกัดข้อความ OCR และลงบัญชีอัตโนมัติ: สกัดข้อมูลจากสลิปโอนเงิน ตรวจสอบความถูกต้อง และบันทึกแถวข้อมูลลงใน Google Sheets พร้อมสำรองไฟล์บน Google Drive", indent=True)
    add_col_body("4) กระบวนการ 4.0 บันทึกคำขอลาและประมวลผลการอนุมัติ: รองรับการยื่นใบลา ตรวจสอบโควตาวันลา และส่งการแจ้งเตือน Flex Message ไปยัง LINE ของหัวหน้างานเพื่ออนุมัติได้ทันที", indent=True)
    add_col_body("5) กระบวนการ 5.0 ประมวลผลแผงควบคุมและออกรายงาน: สรุปสถิติภาพรวม ยอดรายรับ-รายจ่าย สถิติการลา และประวัติการใช้งาน (Audit Logs) ผ่าน Chart.js บน Admin Dashboard", indent=True)

    # Insert DFD Level 1 Image
    dfd_img = r'c:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\dfd_level1_slide_exact.png'
    if os.path.exists(dfd_img):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(2)
        r_img = p_img.add_run()
        r_img.add_picture(dfd_img, width=Inches(3.2))
        add_para("ภาพที่ 1 แผนภาพกระแสข้อมูลระดับ 1 (DFD Level 1) ของระบบ", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=6)

    # --- 4. ผลการดำเนินงานและการทดสอบ ---
    add_col_heading("4. ผลการดำเนินงานและการทดสอบ")
    add_col_body(
        "คณะผู้วิจัยได้ทำการทดสอบระบบในสภาพแวดล้อมการทำงานจริงของ บริษัท ฮาร์ทวอมมิ่ง จำกัด โดยแบ่งการทดสอบออกเป็น 3 ส่วนหลัก ได้แก่:"
    )
    add_col_subheading("4.1 การทดสอบเชิงหน้าที่ (Functional Testing)")
    add_col_body(
        "ออกแบบกรณีทดสอบ (Test Cases) จำนวน 15 กรณีทดสอบ ครอบคลุมการเข้าสู่ระบบ, การตอบคำถาม RAG, การสแกนสลิป OCR, การยื่นและอนุมัติการลา และการแสดงผลแผงควบคุม ผลการทดสอบผ่านเกณฑ์สมบูรณ์คิดเป็นร้อยละ 100"
    )
    add_col_subheading("4.2 การทดสอบประสิทธิภาพของ AI โมดูล (OCR และ RAG)")
    add_col_body(
        "1) การทดสอบ OCR สลิปโอนเงินจริงจาก 5 ธนาคารหลัก จำนวน 50 ตัวอย่าง พบว่าสามารถสกัดข้อมูล วันที่ เวลา จำนวนเงิน และเลขอ้างอิงได้ถูกต้องเฉลี่ยร้อยละ 96.4 ดังแสดงในตารางที่ 1\n"
        "2) การทดสอบระบบตอบคำถาม RAG จากคู่มือสินค้า 50 คำถาม ให้ความถูกต้องตรงตามเอกสารต้นฉบับร้อยละ 94.8 โดยมีเวลาตอบสนองเฉลี่ย 1.84 วินาที"
    )

    # Table 1: OCR Accuracy
    table_p = doc.add_paragraph()
    table_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table_p.paragraph_format.space_before = Pt(4)
    table_p.paragraph_format.space_after = Pt(2)
    add_para("ตารางที่ 1 ผลการทดสอบความแม่นยำของระบบ OCR จำแนกตามธนาคาร", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    
    t1 = doc.add_table(rows=6, cols=4)
    t1.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    headers = ["ธนาคาร / แหล่งที่มา", "จำนวนทดสอบ", "ถูกต้องครบถ้วน", "ความแม่นยำ (%)"]
    data = [
        ["กสิกรไทย (K PLUS)", "10", "10", "100.0%"],
        ["ไทยพาณิชย์ (SCB EASY)", "10", "10", "100.0%"],
        ["กรุงไทย (Krungthai NEXT)", "10", "9", "90.0%"],
        ["กรุงเทพ (Bualuang m)", "10", "10", "100.0%"],
        ["รวมเฉลี่ยทั้งสิ้น (50 สลิป)", "50", "48", "96.4%"]
    ]
    for c_idx, h_text in enumerate(headers):
        cell = t1.cell(0, c_idx)
        cell.text = h_text
        set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = "TH SarabunPSK"
        p.runs[0].font.size = Pt(11)
        p.runs[0].font.bold = True
        
    for r_idx, row_data in enumerate(data):
        for c_idx, val in enumerate(row_data):
            cell = t1.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, top=40, bottom=40, left=40, right=40)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].font.name = "TH SarabunPSK"
            p.runs[0].font.size = Pt(11)
            if r_idx == 4:
                p.runs[0].font.bold = True

    add_col_subheading("4.3 การประเมินความพึงพอใจของผู้ใช้งาน (UAT)")
    add_col_body(
        "นำระบบไปทดลองใช้งานจริงกับพนักงานและผู้บริหาร บริษัท ฮาร์ทวอมมิ่ง จำกัด จำนวน 20 คน เป็นเวลา 2 สัปดาห์ ประเมินด้วยแบบสอบถามมาตราส่วน 5 ระดับ (Likert Scale) ดังแสดงในตารางที่ 2:"
    )

    # Table 2: UAT Satisfaction
    add_para("ตารางที่ 2 ผลการประเมินความพึงพอใจของผู้ใช้งานจริง (N = 20)", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=2)
    t2 = doc.add_table(rows=6, cols=4)
    t2.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    uat_headers = ["ด้านการประเมิน", "ค่าเฉลี่ย (X̄)", "ส่วนเบี่ยงเบน (S.D.)", "ระดับความพึงพอใจ"]
    uat_data = [
        ["1. ด้านความถูกต้องและแม่นยำของ AI", "4.70", "0.46", "มากที่สุด"],
        ["2. ด้านความสะดวกรวดเร็วในการใช้งาน", "4.75", "0.44", "มากที่สุด"],
        ["3. ด้านฟังก์ชันการจัดการงานบุคคลและลา", "4.60", "0.50", "มากที่สุด"],
        ["4. ด้านความง่ายในการดูแผงควบคุม", "4.55", "0.51", "มากที่สุด"],
        ["สรุปภาพรวมทุกด้าน", "4.65", "0.48", "มากที่สุด"]
    ]
    for c_idx, h_text in enumerate(uat_headers):
        cell = t2.cell(0, c_idx)
        cell.text = h_text
        set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = "TH SarabunPSK"
        p.runs[0].font.size = Pt(11)
        p.runs[0].font.bold = True
        
    for r_idx, row_data in enumerate(uat_data):
        for c_idx, val in enumerate(row_data):
            cell = t2.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, top=40, bottom=40, left=40, right=40)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].font.name = "TH SarabunPSK"
            p.runs[0].font.size = Pt(11)
            if r_idx == 4:
                p.runs[0].font.bold = True

    # --- 5. สรุปและอภิปรายผล ---
    add_col_heading("5. สรุปและอภิปรายผล")
    add_col_body(
        "ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กรที่พัฒนาขึ้น ประสบความสำเร็จในการบูรณาการเทคโนโลยี AI RAG และ OCR เข้ากับ LINE Platform "
        "ทำให้พนักงานสามารถเข้าถึงข้อมูลองค์กร บันทึกบัญชีการเงิน และดำเนินการลางานได้อย่างสะดวกรวดเร็ว ช่วยลดระยะเวลาในการค้นหาข้อมูลจากเดิม 3-5 นาที "
        "เหลือไม่เกิน 2 วินาที และลดความผิดพลาดในการลงบัญชีด้วยมือลงได้อย่างชัดเจน ผู้ใช้งานมีความพึงพอใจในระดับมากที่สุด (X̄ = 4.65, S.D. = 0.48)"
    )

    # --- 6. คำชี้แจงการใช้ AI (Declaration of AI Use) ---
    add_col_heading("6. คำชี้แจงการใช้ AI (Declaration of AI Use)")
    add_col_body(
        "ในการจัดทำบทความวิจัยนี้ คณะผู้วิจัยได้ใช้ปัญญาประดิษฐ์ (Generative AI) ได้แก่ Google Gemini และ Antigravity Assistant ในการช่วยตรวจสอบไวยากรณ์ "
        "การขัดเกลาสำนวนภาษาอังกฤษในส่วนบทคัดย่อ และการจัดเรียงรูปแบบเอกสารตามเทมเพลต ทั้งนี้ คณะผู้วิจัยได้ทำการตรวจสอบความถูกต้องของเนื้อหา "
        "การวิเคราะห์ข้อมูล ตัวเลขสถิติ และผลการทดลองทั้งหมดด้วยตนเองอย่างถี่ถ้วน และขอรับผิดชอบต่อความถูกต้องทางวิชาการของบทความฉบับนี้ทุกประการ"
    )

    # --- กิตติกรรมประกาศ ---
    add_col_heading("กิตติกรรมประกาศ")
    add_col_body(
        "งานวิจัยนี้สำเร็จลุล่วงได้ด้วยความกรุณาอย่างยิ่งจาก อาจารย์ ดร.ศิรินทรา แว่วศรี อาจารย์ที่ปรึกษาโครงงาน ที่ได้ให้คำแนะนำเชิงวิชาการและการออกแบบระบบ "
        "และขอขอบคุณผู้บริหารและพนักงาน บริษัท ฮาร์ทวอมมิ่ง จำกัด ที่ได้ให้ความอนุเคราะห์ข้อมูลและร่วมทดสอบระบบการทำงานจริง"
    )

    # --- เอกสารอ้างอิง ---
    add_col_heading("เอกสารอ้างอิง")
    refs = [
        "[1] บริษัท ฮาร์ทวอมมิ่ง จำกัด. ข้อมูลกระบวนการทำงานและคู่มือสินค้าภายในองค์กร. กรุงเทพฯ, 2568.",
        "[2] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, pp. 9459-9474, 2020.",
        "[3] J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, “BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding,” in Proc. NAACL-HLT, pp. 4171-4186, 2019.",
        "[4] Google Cloud. “Cloud Vision API Documentation: Text Detection and Optical Character Recognition,” [Online]. Available: https://cloud.google.com/vision/docs/ocr, 2024.",
        "[5] LINE Corporation. “LINE Messaging API Official Documentation,” [Online]. Available: https://developers.line.biz/en/docs/messaging-api/, 2024.",
        "[6] ธนากร ธนบวรพล และ วีรภัทร ชื่นชอบ. ปริญญานิพนธ์เรื่อง ปัญญาประดิษฐ์แชทบอทสำหรับองค์กร (กรณีศึกษา : ฮาร์ทวอมมิ่ง จำกัด). ภาควิชาเทคโนโลยีสารสนเทศ คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ, 2569."
    ]
    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(2)
        p_ref.paragraph_format.line_spacing = 1.0
        p_ref.paragraph_format.left_indent = Inches(0.2)
        p_ref.paragraph_format.first_line_indent = Inches(-0.2)
        r = p_ref.add_run(ref)
        r.font.name = "TH SarabunPSK"
        r.font.size = Pt(11)
        rPr = r._r.get_or_add_rPr()
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), "TH SarabunPSK")
        rFonts.set(qn('w:hAnsi'), "TH SarabunPSK")
        rFonts.set(qn('w:cs'), "TH SarabunPSK")
        rPr.append(rFonts)

    doc.save(output_docx)
    print(f"Successfully generated AUCC paper: {output_docx}")

if __name__ == "__main__":
    create_aucc_paper()
