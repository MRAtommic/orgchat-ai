# 🏢 OrgChat AI — Enterprise AI & Smart Office Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Flask%20%7C%20SQLite%20%7C%20TailwindCSS-lightgrey.svg)]()
[![AI Provider](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)]()

**OrgChat AI** คือแพลตฟอร์มผู้ช่วยอัจฉริยะระดับองค์กร (Enterprise AI Assistant) และระบบจัดการสำนักงานอัจฉริยะ (Smart Office) เชื่อมโยงข้อมูลผ่านระบบ **RAG (Retrieval-Augmented Generation)**, **LINE OA API**, **Google Cloud Suite (Drive, Sheets)**, และระบบการเงิน/ภาษีบัญชีอย่างครบวงจร เพื่อยกระดับความเร็วในการทำงานและความโปร่งใสภายในองค์กร

---

## 🚀 คุณสมบัติเด่น (Key Features)

### 🤖 1. AI Assistant "น้องพั้น" (LINE OA Integration)
* **Smart Chatbot:** สนทนาโต้ตอบอย่างเป็นธรรมชาติ สุภาพ ถูกกาลเทศะ และเข้าใจบริบทองค์กร
* **Document RAG System:** ค้นหาคำตอบจากไฟล์คลังความรู้องค์กร (PDF, DOCX, XLSX, TXT) ได้โดยตรงผ่านช่องแชท LINE
* **Multi-File Cloud Storage:** อัปโหลดรูปภาพ สลิปโอนเงิน หรือไฟล์เอกสารหลายรายการพร้อมกันใน LINE เพื่ออัปโหลดขึ้น Google Drive จัดระเบียบแยก ปี > เดือน > วัน ให้อัตโนมัติ

### 📊 2. ระบบจัดการการเงินและบัญชีอัจฉริยะ (Google Cloud & Financial Automations)
* **Auto-Bookkeeping:** ถอดข้อมูลจากรูปภาพใบเสร็จ/สลิปด้วยระบบ OCR และ AI วิเคราะห์ แล้วนำไปลงบัญชีใน **Google Sheets** แยกหมวดหมู่ให้อัตโนมัติ
* **Reconciliation System:** ระบบกระทบยอดอัจฉริยะ จับคู่รูปสลิปโอนเงินกับข้อมูลใบกำกับภาษี ป้องกันการส่งซ้ำ
* **Real-time Expense Reporting:** ตรวจสอบยอดรวมสรุปรายจ่าย สรุปหมวดหมู่ และประเมินภาษีผ่านคำสั่งแชทหรือหน้า Dashboard

### 🏥 3. ระบบจัดการงานบุคคลและสวัสดิการ (Leave Management & HR Tools)
* **Leave Requests via LINE:** พนักงานสามารถส่งใบลาป่วย ลากิจ ลาพักร้อน พร้อมแนบภาพเอกสารรับรองแพทย์ได้จาก LINE และแจ้งเตือนทีมทันที
* **Leave Control Dashboard:** ฝั่งผู้ดูแลระบบ (Admin) สามารถตั้งค่าสิทธิ์การลา อนุมัติ/ปฏิเสธใบลา รีเซ็ตจำนวนวันลาคงเหลือของพนักงานรายบุคคลได้ผ่านแผงควบคุมหลังบ้าน

### 🛡️ 4. แผงควบคุมระบบรักษาความปลอดภัยและการทำงาน (Security & Admin Settings)
* **Session Fingerprint Security:** ป้องกันการโจรกรรมเซสชัน (Session Hijacking) ด้วยระบบตรวจจับ User-Agent Fingerprint
* **Multi-Theme Interface:** สลับโหมดมืด (Dark Mode) และโหมดสว่าง (Light Mode) ได้อย่างราบรื่น
* **Robust CSRF Protection:** ปกป้องข้อมูลในทุกช่องทางการส่งข้อมูล (Forms, File Uploads)

---

## 📁 โครงสร้างโปรเจกต์ (Project Directory Structure)

```text
├── webai/
│   ├── app_server.py           # จุดเริ่มต้นของแอปพลิเคชัน (Flask Server Setup & Middleware)
│   ├── database.py             # ฟังก์ชันการจัดเก็บและดึงข้อมูลจากฐานข้อมูล SQLite
│   ├── rag_engine.py           # เครื่องมือจัดการ Vector DB (Chroma) และระบบ Parsing เอกสาร
│   ├── ai_providers.py         # ตัวเชื่อมต่อ API บริการ LLM (Google Gemini / Groq)
│   ├── google_drive_service.py # บริการจัดการไฟล์บน Google Drive & Google Sheets
│   ├── routes/                 # โฟลเดอร์แยกโมดูล API และเส้นทางการประมวลผล (Blueprints)
│   │   ├── auth.py             # ระบบสมาชิก ความปลอดภัย และการยืนยันตัวตน
│   │   ├── admin.py            # การตั้งค่าองค์กร จัดการพนักงาน และการเงินหลังบ้าน
│   │   ├── features.py         # ฟีเจอร์เสริม (CRM, ใบเสนอราคา, การประชุม)
│   │   └── social.py           # ฟีดข่าวสารภายในองค์กรและระบบ LINE Notifications
│   ├── static/                 # ไฟล์ Frontend Static (JavaScript Core, Styles, Images)
│   └── templates/              # หน้าตาเว็บส่วนประสานงานผู้ใช้ (HTML JINJA Templates)
```

---

## 🛠️ ขั้นตอนการติดตั้งและการรันระบบ (Setup & Running)

### 1. ติดตั้งซอฟต์แวร์ที่จำเป็น
* ติดตั้ง **Python 3.10** ขึ้นไปบนเครื่องเซิร์ฟเวอร์
* ติดตั้ง **Tesseract OCR** บน OS เพื่อใช้งานระบบสแกนเอกสารจากรูปภาพ:
  * **Windows:** ดาวน์โหลดจาก [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) และเพิ่ม Path ใน Environment Variable
  * **Linux (Ubuntu/Debian):** `sudo apt-get install tesseract-ocr tesseract-ocr-tha`

### 2. ติดตั้งโมดูลเสริม (Dependencies)
เปิด Terminal ในโฟลเดอร์โปรเจกต์และพิมพ์:
```bash
pip install -r requirements.txt
```

### 3. กำหนดค่าตัวแปรระบบ (.env)
สร้างไฟล์ `.env` ไว้ที่โฟลเดอร์รากของโปรเจกต์ และระบุคีย์สำคัญตามตัวอย่างดังนี้:
```env
# AI & Core Settings
GEMINI_API_KEY=your_gemini_api_key_here
MY_COMPANY_NAME="ชื่อบริษัทของคุณ"

# LINE API
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Google API Credentials
SPREADSHEET_ID=your_google_spreadsheet_id_here
PARENT_FOLDER_ID=your_google_drive_folder_id_here
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service_account_credentials.json"

# App Security Settings
FLASK_SECRET_KEY=your_random_secret_key_for_sessions
```

### 4. รันระบบเซิร์ฟเวอร์
* **โหมดนักพัฒนา (Development Server):**
  ```bash
  python app_server.py
  ```
* **โหมดใช้งานจริง (Production Server - Gunicorn):**
  ```bash
  gunicorn -w 4 -b 0.0.0.0:8000 app_server:app
  ```

---

## 💬 ตัวอย่างคำสั่งใช้งานผ่าน LINE OA
พนักงานสามารถพิมพ์แชทคำสั่งหาบอทผู้ช่วยได้ทันที เช่น:
* 🏥 `ขอลาป่วย 1 วัน พร้อมใบรับรองแพทย์` - ระบบบันทึกและส่งแจ้งเตือนใบลา
* 📊 `สรุปรายจ่ายเดือนนี้` - สรุปรายการใช้จ่ายแบบเรียลไทม์
* 📁 `ค้นหาไฟล์ [ชื่อไฟล์]` - ค้นหาและขอลิงก์เข้าถึงเอกสารใน Drive ของส่วนกลาง
* 🤝 `ตรวจสอบกระทบยอด` - ค้นหาและกระทบยอดเงินโอนอัตโนมัติ

---
**พัฒนาโดยทีมงาน OrgChat AI — เชื่อมต่อการสื่อสาร คลังความรู้ และการทำงานอย่างมีประสิทธิภาพด้วยพลังแห่งปัญญาประดิษฐ์** 🌟
