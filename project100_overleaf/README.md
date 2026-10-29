# OrgChat AI - เอกสารโครงงานเทคโนโลยีสารสนเทศ (Project 100) & Overleaf Package

โฟลเดอร์นี้รวบรวมไฟล์ซอร์สโค้ด LaTeX ทั้งหมดสำหรับจัดทำเล่มรายงานโครงงานปริญญานิพนธ์ (Project 100) บน **Overleaf** พร้อมชุดสคริปต์ Python ที่ใช้ในการสร้าง (Generate), เรนเดอร์ไดอะแกรม (DFD/Flowchart) และจัดรูปแบบเอกสารให้ได้มาตรฐานทางวิชาการ

---

## 📁 โครงสร้างภายในโฟลเดอร์

```text
project100_overleaf/
├── OrgChat_Overleaf_Package.zip     # ไฟล์ Zip สำหรับ Upload เข้า Overleaf (1-Click Upload)
├── README.md                        # เอกสารคู่มือชุดนี้
│
├── latex_source/                    # โค้ด LaTeX (.tex) และรูปภาพทั้งหมด
│   ├── Main.tex                     # ไฟล์หลักสำหรับ Compile (ตั้งเป็น Main document)
│   ├── Project_000_Cover.tex        # หน้าปกภาษาไทยและภาษาอังกฤษ
│   ├── Project_001_Certificate1.tex # ใบรับรองโครงงาน (สำหรับอาจารย์ที่ปรึกษา)
│   ├── Project_001_Certificate2.tex # ใบรับรองโครงงาน (สำหรับคณะกรรมการสอบ)
│   ├── Project_002_Abstract.tex     # บทคัดย่อ (ไทย & English Abstract)
│   ├── Project_010_Chapter1.tex     # บทที่ 1 บทนำ, ที่มา, วัตถุประสงค์, ขอบเขต
│   ├── Project_020_Chapter2.tex     # บทที่ 2 ทฤษฎีและงานวิจัยที่เกี่ยวข้อง (RAG, LINE OA, OCR)
│   ├── Project_030_Chapter3.tex     # บทที่ 3 การวิเคราะห์และออกแบบระบบ (DFD, ER, Process Specs)
│   ├── Project_040_Chapter4.tex     # บทที่ 4 ผลการดำเนินงานและหน้าจอการทำงานจริง
│   ├── Project_050_Chapter5.tex     # บทที่ 5 สรุปผลการทดลอง อภิปรายผล ปัญหาและข้อเสนอแนะ
│   ├── Project_101_AppendixA.tex    # ภาคผนวก ก: คู่มือการติดตั้งและใช้งานระบบ
│   ├── Project_102_AppendixB.tex    # ภาคผนวก ข: ตารางการทดสอบและกรณีทดสอบ (Test Cases)
│   ├── Project_999_Bibliography.bib # บรรณานุกรมเอกสารอ้างอิงมาตรฐาน
│   └── Image/                       # ไดอะแกรมทางวิชาการและรูปหน้าจอระบบทั้งหมด
│
└── generator_scripts/               # โค้ด Python ที่ใช้สร้าง/เรนเดอร์เอกสาร
    ├── docx_dump.json               # ข้อมูลโครงสร้างและเนื้อหาต้นฉบับ
    ├── latex_helpers.py             # ฟังก์ชันช่วยจัดการ Escape characters, Tabularx, Captions
    ├── rebuild_all_chapters_perfect.py # สคริปต์หลักประกอบเล่มรายงานทุกบท
    ├── build_front_matter.py        # สร้างส่วนหน้า (ปก, ใบรับรอง, บทคัดย่อ)
    ├── build_chapter1.py            # สร้างบทที่ 1
    ├── build_chapter2_fixed.py      # สร้างบทที่ 2
    ├── update_chapter3.py           # สร้างบทที่ 3 (DFD & System Specs)
    ├── update_chapter4.py           # สร้างบทที่ 4 (Screenshots & Evaluation)
    ├── update_chapter5.py           # สร้างบทที่ 5 (Discussion & Future Work)
    ├── update_appendix_a.py         # สร้างภาคผนวก ก
    ├── update_appendix_b.py         # สร้างภาคผนวก ข
    ├── update_bib.py                # สร้างไฟล์บรรณานุกรม .bib
    ├── add_flowcharts_ch3.py        # เชื่อมโยง Flowchart ขั้นตอนการทำงาน
    ├── apply_layout_polishing.py    # จัดความกว้างตารางและการเว้นวรรค
    ├── fix_ch3.py / fix_ch3_clearpage.py # ปรับ Page breaks และ Clearpage
    ├── fix_lot_header.py            # แก้ไขหัวตารางสารบัญ (LOT)
    ├── fix_main_thai_pages.py       # จัดการเลขหน้าภาษาไทย
    ├── render_academic_dfd_final.py # วาด Context Diagram, DFD 0, DFD 1 ด้วย Matplotlib
    ├── render_chapter4_figures.py   # เรนเดอร์รูปภาพประกอบบทที่ 4
    ├── render_perfect_master_dfd.py # เรนเดอร์ Master DFD ความละเอียดสูง
    ├── test_50_questions.py         # คำถามทดสอบความแม่นยำของโมเดล RAG 50 ข้อ
    ├── test_50_results.json         # ผลการทดสอบ RAG 50 ข้อสำหรับบทที่ 4 และ 5
    ├── generate_a1_poster.py        # สคริปต์สร้างโปสเตอร์ A1 สำหรับนำเสนอโครงงาน
    └── generate_aucc_paper.py       # สคริปต์สร้างเอกสารบทความวิจัย AUCC Proceeding
```

---

## 🚀 วิธีการนำเข้าและใช้งานบน Overleaf

1. **เข้าสู่ระบบ Overleaf** ([https://www.overleaf.com](https://www.overleaf.com))
2. **สร้างโปรเจคใหม่**:
   - คลิกปุ่ม **New Project** -> เลือก **Upload Project**
   - ลากไฟล์ `OrgChat_Overleaf_Package.zip` ไปวาง
3. **ตั้งค่า Compiler**:
   - ไปที่เมนู **Menu** ด้านบนซ้าย
   - หัวข้อ **Compiler**: ให้เลือกเป็น **XeLaTeX** (จำเป็นสำหรับการตัดคำและเรนเดอร์ภาษาไทย TH Sarabun New)
   - หัวข้อ **Main document**: ตรวจสอบว่าเป็น `Main.tex`
4. **Compile**:
   - คลิกปุ่ม **Recompile** สีเขียวเพื่อสร้างเอกสาร PDF ที่สมบูรณ์

---

## 🛠️ วิธีการรันสคริปต์สร้างเอกสารใหม่ (Generator Scripts)

หากต้องการปรับปรุงเนื้อหาหรือเรนเดอร์ไดอะแกรมใหม่ด้วย Python:

```bash
cd project100_overleaf/generator_scripts

# 1. วาดไดอะแกรม DFD และสถาปัตยกรรมระบบใหม่
python render_academic_dfd_final.py

# 2. ทำการรันผลทดสอบระบบ RAG 50 คำถาม (ถ้าต้องการอัพเดทผลประเมิน)
python test_50_questions.py

# 3. ประกอบเล่มเอกสารทุกบทเป็นไฟล์ .tex อัตโนมัติ
python rebuild_all_chapters_perfect.py
```
