# 🏢 OrgChat — AI ผู้ช่วยองค์กร

ระบบ AI Chatbot สำหรับจัดการความรู้ในองค์กร (RAG Engine) ที่ช่วยให้คุณสามารถอัปโหลดเอกสาร (PDF, CSV, TXT, รูปภาพ) และสอบถามข้อมูลจากเอกสารเหล่านั้นได้ทันทีผ่าน Google Gemini AI

## ✨ คุณสมบัติ
- **RAG System**: ค้นหาข้อมูลที่เกี่ยวข้องจากเอกสารของคุณโดยเฉพาะ
- **Multi-format Support**: รองรับไฟล์ PDF, CSV, แผ่นงาน, ข้อความ และรูปภาพ (OCR)
- **Modern UI**: หน้าตาสวยงาม ใช้งานง่าย รองรับ Dark Mode และ Responsive
- **Secure**: เก็บข้อมูลและ API Key ไว้บนเครื่องของคุณเท่านั้น

## 🛠 การติดตั้ง

### 1. ติดตั้ง Dependencies
ใช้ Python 3.10 ขึ้นไป และรันคำสั่ง:
```bash
pip install -r requirements.txt
```

### 2. ติดตั้ง Tesseract-OCR (สำหรับอ่านรูปภาพ)
- **Windows**: ดาวน์โหลดตัวติดตั้งจาก [GitHub tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki) และเพิ่ม Path ไปยัง System Environment
- **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-tha`

### 3. ตั้งค่า API Key
- ไปที่ [Google AI Studio](https://aistudio.google.com) เพื่อรับ API Key
- สามารถใส่ผ่านหน้าเว็บได้โดยตรง หรือสร้างไฟล์ `.env` และใส่:
```env
GEMINI_API_KEY=your_api_key_here
```

## 🚀 วิธีใช้งาน
รันไฟล์ `start.bat` (สำหรับ Windows) หรือรันคำสั่ง:
```bash
python app.py
```
จากนั้นเปิดเบราว์เซอร์ไปที่ `http://localhost:5000`

## 📂 โครงสร้างโปรเจกต์
- `app.py`: Flask Backend API
- `rag_engine.py`: ระบบประมวลผลเอกสารและ Vector Store (ChromaDB)
- `static/`: ไฟล์ CSS และ JavaScript สำหรับ Frontend
- `templates/`: ไฟล์ HTML
- `uploads/`: โฟลเดอร์เก็บไฟล์ที่อัปโหลด
- `chroma_db/`: ฐานข้อมูล Vector
