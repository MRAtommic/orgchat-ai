# 🏢 OrgChat AI — ระบบผู้ช่วยอัจฉริยะและจัดการบัญชีองค์กร

**OrgChat AI** คือโซลูชัน AI แบบครบวงจรที่รวมพลังของ **RAG (Retrieval-Augmented Generation)** เข้ากับการเชื่อมต่อ **LINE OA** และ **Google Workspace** เพื่อเปลี่ยนเอกสารในองค์กรให้กลายเป็นฐานความรู้ที่โต้ตอบได้ พร้อมระบบจัดการบัญชีและไฟล์อัตโนมัติ

---

## ✨ คุณสมบัติเด่น (Core Features)

### 🤖 1. AI Assistant "น้องพั้น" (LINE OA Integration)
- **Smart Chatbot**: โต้ตอบด้วยบุคลิกที่เป็นมิตร สุภาพ และจดจำบริบทขององค์กรได้แม่นยำ
- **RAG Engine**: ค้นหาคำตอบจากฐานข้อมูลเอกสาร (PDF, CSV, TXT) ของบริษัทได้ทันที
- **Multi-File Processing**: อัปโหลดรูปภาพ สลิป หรือไฟล์หลายรายการพร้อมกันผ่าน LINE น้องพั้นจะจัดการเข้า Drive ให้เอง

### 📊 2. ระบบจัดการบัญชีและไฟล์อัตโนมัติ (Google Cloud Automations)
- **Auto-Bookkeeping**: อ่านข้อมูลจากสลิปและใบกำกับภาษีด้วย OCR แล้วบันทึกลง **Google Sheets** แยกหมวดหมู่ให้อัตโนมัติ
- **Reconciliation System**: ระบบกระทบยอดอัจฉริยะ จับคู่สลิปโอนเงินกับใบกำกับภาษีให้อัตโนมัติ
- **Expense Summary**: สั่งสรุปรายจ่ายประจำวัน/เดือน ได้ทันทีผ่านคำสั่งเสียงหรือข้อความใน LINE
- **Smart Drive Storage**: จัดเก็บไฟล์ลง Google Drive แยกตาม ปี > เดือน > วัน > ประเภทเอกสาร อย่างเป็นระเบียบ

### 🏥 3. ระบบสนับสนุนองค์กร (Corporate Tools)
- **Leave Management**: พนักงานสามารถส่งคำลาป่วย/ลากิจ ผ่าน LINE และแนบใบรับรองแพทย์ได้ทันที
- **Knowledge Search**: ค้นหาไฟล์งานเก่าๆ ใน Drive ผ่านการพิมพ์ค้นหาใน LINE แชท

---

## 🛠 การติดตั้ง (Installation)

### 1. เตรียมความพร้อม
- Python 3.10 ขึ้นไป
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (สำหรับระบบอ่านรูปภาพ)

### 2. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Environment Variables (.env)
สร้างไฟล์ `.env` ในโฟลเดอร์หลักและกำหนดค่าดังนี้:
```env
GEMINI_API_KEY=your_gemini_key
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
SPREADSHEET_ID=your_google_sheet_id
PARENT_FOLDER_ID=your_google_drive_folder_id
MY_COMPANY_NAME=ชื่อบริษัทของคุณ
```

---

## 🚀 คำสั่งแนะนำสำหรับ LINE OA (Command Guide)

คุณสามารถพิมพ์คำสั่งเหล่านี้หา "น้องพั้น" ได้ทันที:
- 📊 **"สรุปรายจ่าย"** — เพื่อดูยอดรวมและหมวดหมู่การใช้จ่ายของเดือนนี้
- 🔍 **"หาไฟล์ [ชื่อไฟล์]"** — ค้นหาไฟล์เอกสารใน Google Drive
- ⏳ **"กระทบยอด"** — เริ่มระบบจับคู่สลิปกับใบกำกับภาษีอัตโนมัติ
- 🏥 **"ลาป่วย"** — เพื่อแจ้งการลางานและบันทึกเข้าสู่ระบบ
- 📁 **"เปิด Drive"** — รับลิงก์เข้าสู่โฟลเดอร์เก็บเอกสารขององค์กร

---

## 📂 โครงสร้างโปรเจกต์ (Project Structure)
- `app_server.py`: หัวใจหลักของระบบ จัดการ Webhook และ API ทั้งหมด
- `google_drive_service.py`: ระบบเชื่อมต่อ Google Drive และ Sheets อัจฉริยะ
- `rag_engine.py`: ระบบค้นหาข้อมูลจากฐานความรู้ (Vector Database)
- `database.py`: จัดการฐานข้อมูล SQLite สำหรับ Logs และระบบลางาน
- `ai_providers.py`: ส่วนเชื่อมต่อกับ LLM (Google Gemini / Groq)
- `static/ & templates/`: ส่วนของ Web Interface สำหรับการจัดการหลังบ้าน

---

## 🛡 ความปลอดภัย (Security)
- ข้อมูลและเอกสารของคุณจะถูกประมวลผลและเก็บไว้ใน Google Drive ขององค์กรคุณเอง
- ระบบรองรับการทำงานแบบ On-premise หรือ Deploy บน Cloud (Google Cloud Run) เพื่อความปลอดภัยสูงสุด

---
**พัฒนาโดยทีมงาน OrgChat AI — เพิ่มประสิทธิภาพให้องค์กรด้วยพลังแห่งปัญญาประดิษฐ์** 🌟
