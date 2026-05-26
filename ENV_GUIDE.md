# 📘 คู่มือการตั้งค่าไฟล์ `.env` สำหรับระบบ OrgChat-AI (Environment Configuration Guide)

คู่มือนี้จัดทำขึ้นเป็นภาษาไทยเพื่ออธิบายวิธีตั้งค่าตัวแปรสภาพแวดล้อม (Environment Variables) ทั้งหมดในระบบ **OrgChat-AI** ให้ทำงานได้อย่างสมบูรณ์แบบ ทั้งบนเครื่องนักพัฒนาทั่วไป (Local Dev) และบนระบบโปรดักชันจริง (Railway / Cloud Server)

---

## 🛠️ ขั้นตอนการเริ่มต้นใช้งานครั้งแรก

1. คัดลอกไฟล์ต้นแบบ `.env.example` ไปสร้างเป็นไฟล์ใหม่ชื่อ `.env` ในโฟลเดอร์หลัก (`webai/`)
   ```bash
   cp .env.example .env
   ```
2. เปิดไฟล์ `.env` และกรอกค่าคอนฟิกต่าง ๆ ตามรายละเอียดด้านล่างนี้
3. **⚠️ ข้อควรระวังด้านความปลอดภัย**: ห้ามอัปโหลดไฟล์ `.env` ที่มีกุญแจ API จริง (เช่น Keys ต่าง ๆ) ขึ้น Git เด็ดขาด! (ระบบได้ทำการเพิกถอนสิทธิ์โดยอัตโนมัติผ่านไฟล์ `.gitignore` แล้ว)

---

## 📋 สารบัญตัวแปรทั้งหมดในระบบ

| ลำดับ | หมวดหมู่การตั้งค่า | ความจำเป็น | ฟังก์ชันการทำงานหลัก |
|:---:|---|:---:|---|
| 1 | [FLASK & SERVER](#1-flask--server) | **จำเป็น** | การทำงานระดับพื้นฐานของเว็บและ Uptime |
| 2 | [DATABASE](#2-database) | **จำเป็น** | เชื่อมต่อ SQLite (Local) หรือ Supabase (Postgres) |
| 3 | [AI PROVIDERS (Groq / Gemini)](#3-ai-providers) | **จำเป็น** | การถามตอบของบอทอัจฉริยะและการทำ RAG Knowledge |
| 4 | [LINE MESSAGING API](#4-line-messaging-api) | *เลือกใส่* | การส่งการแจ้งเตือนและการคุยผ่าน LINE Group |
| 5 | [GOOGLE OAUTH2](#5-google-oauth2-sign-in-with-google) | *เลือกใส่* | การล็อกอินแบบ One-Tap ด้วย Google Account |
| 6 | [GOOGLE SERVICE ACCOUNT](#6-google-service-account) | *เลือกใส่* | การประสานงานไฟล์ Google Drive และ Google Sheets |
| 7 | [STRIPE PAYMENT](#7-stripe-payment) | *เลือกใส่* | ระบบชำระเงินและจัดการ Plan (Pro / Business) |

---

## 1. FLASK & SERVER
ตั้งค่าการทำงานหลักของเว็บเซิร์ฟเวอร์

* `FLASK_SECRET_KEY` [REQUIRED]
  * **คำอธิบาย**: คีย์ลับเพื่อเข้ารหัสเซสชัน (Session Cookie) เพื่อความปลอดภัย
  * **วิธีสร้าง**: รันคำสั่งนี้ใน Terminal เพื่อสุ่มคีย์ที่มีความปลอดภัยสูง:
    ```bash
    python -c "import secrets; print(secrets.token_hex(32))"
    ```
* `BASE_URL` [REQUIRED]
  * **คำอธิบาย**: URL หลักของระบบที่เปิดสู่ภายนอก (ห้ามลงท้ายด้วย `/`)
  * **ตัวอย่าง**: `https://openchat.sbs` หรือตอนทดสอบ Local เช่น `http://127.0.0.1:5005`
* `PORT` [OPTIONAL]
  * **คำอธิบาย**: พอร์ตที่ต้องการให้เซิร์ฟเวอร์รัน (ปกติบนเครื่องใช้ `5005` ส่วนบน Railway ระบบจะสุ่มให้เอง)
* `TZ` [OPTIONAL]
  * **คำอธิบาย**: เขตเวลาหลักของระบบ เช่น `Asia/Bangkok` เพื่อให้ระบบนัดหมายแสดงผลเป็นเวลาไทย

---

## 2. DATABASE
แชร์ข้อมูลการเก็บประวัติแชท นัดหมาย และข้อมูลการตั้งค่าองค์กรทั้งหมด

> [!NOTE]
> ระบบ OrgChat-AI ได้พัฒนาสถาปัตยกรรมตัวแปลงคิวรี่อัตโนมัติ (Dynamic Translation) เพื่อรองรับทั้ง SQLite และ PostgreSQL โดยไม่ต้องแก้ไขโค้ดฐานข้อมูล

### 💻 ตั้งค่าสำหรับพัฒนาบนเครื่องโลคอล (SQLite)
* `DB_PATH=chat_history.db`
  *(หมายเหตุ: บนเครื่องสามารถละการตั้งค่า `DB_TYPE` ได้ ระบบจะเลือก SQLite เป็นค่าเริ่มต้นอัตโนมัติ)*

### 🚀 ตั้งค่าสำหรับขึ้นระบบจริง (Supabase / Postgres on Cloud)
* `DB_TYPE=postgres`
* `POSTGRES_HOST=your-supabase-db-host.supabase.co`
* `POSTGRES_PORT=5432`
* `POSTGRES_DB=postgres`
* `POSTGRES_USER=postgres`
* `POSTGRES_PASSWORD=your-super-secure-db-password`

---

## 3. AI PROVIDERS
ระบบสมองกลอัจฉริยะ (AI Engine) และระบบสืบค้นข้อมูล RAG (Knowledge Base)

### 3.1 บอทถามตอบ (หลัก)
เลือกระหว่าง **Groq** (ฟรีและรวดเร็วมาก) หรือ **Gemini** (สมบูรณ์แบบในการวิเคราะห์ภาพ)
* `AI_PROVIDER=groq` (หรือ `gemini`)
* `GROQ_API_KEY` (เมื่อเลือก Groq)
  * **วิธีสมัคร**: ไปที่ [Groq Console](https://console.groq.com) → API Keys → กดสร้างคีย์ใหม่
* `GEMINI_API_KEY` (เมื่อเลือก Gemini)
  * **วิธีสมัคร**: ไปที่ [Google AI Studio](https://aistudio.google.com/app/apikey) → กดสร้าง API Key

> [!TIP]
> **ระบบสำรองคีย์ (Backup Keys)**: คุณสามารถใส่คีย์สำรองได้ถึง 3 ตัว ป้องกันการติดขัดจาก Rate Limit
> `GROQ_API_KEY_BACKUP=...`
> `GEMINI_API_KEY_2=...`
> `GEMINI_API_KEY_3=...`

### 3.2 เวกเตอร์ความรู้ (Embedding Provider)
สำหรับบอทสืบค้นข้อมูลในเอกสารของบริษัท (PDF, CSV, MD ฯลฯ)
* `AI_EMBEDDING_PROVIDER=gemini`
* `SKIP_SYNC=0` (หากตั้งเป็น `1` จะข้ามการประมวลผลไฟล์เวกเตอร์ตอนรันเพื่อประหยัดทรัพยากรเวลา dev)

---

## 4. LINE MESSAGING API
ใช้สำหรับเชื่อมต่อบอทเข้ากับกลุ่มไลน์ออฟฟิศ เพื่อแจ้งเตือนบิล นัดหมาย และให้บอทโต้ตอบผ่าน LINE

1. เข้าสู่ระบบ [LINE Developers Console](https://developers.line.biz/)
2. สร้าง Channel ประเภท Messaging API
3. คอนฟิกค่าใน `.env`:
   * `LINE_CHANNEL_ACCESS_TOKEN`: คัดลอกค่าจากหัวข้อ *Messaging API → Channel access token (long-lived)*
   * `LINE_CHANNEL_SECRET`: คัดลอกค่าจากหัวข้อ *Basic settings → Channel secret*
4. ไปที่ LINE Console ตั้งค่า **Webhook URL** เป็น: `https://<BASE_URL>/webhook/line` และเปิดใช้งาน *Use webhook*

---

## 5. GOOGLE OAUTH2 (Sign in with Google)
ใช้ล็อกอินด่วนแบบ One-Tap และอำนวยความสะดวกการสมัครสมาชิกใหม่

1. ไปยัง [Google Cloud Console](https://console.cloud.google.com/)
2. สร้างโปรเจกต์ใหม่และสร้าง OAuth client ID ประเภท *Web Application*
3. กำหนดลิงก์ปลายทางความปลอดภัย (Authorized redirect URIs) เป็น:
   * `https://<BASE_URL>/api/auth/google/callback`
4. คอนฟิกค่าใน `.env`:
   * `GOOGLE_OAUTH2_CLIENT_ID`
   * `GOOGLE_OAUTH2_CLIENT_SECRET`
   * `OAUTH2_REDIRECT_URI=https://<BASE_URL>/api/auth/google/callback`

---

## 6. GOOGLE SERVICE ACCOUNT
ระบบเชื่อมโยง Google Drive และ Google Sheets สำหรับเก็บใบเสนอราคา เอกสาร และการบันทึกการส่งออกประวัติแบบ Real-Time

1. บนโปรเจกต์ [Google Cloud Console](https://console.cloud.google.com/)
2. เปิดใช้บริการ Google Drive API และ Google Sheets API
3. ไปที่เมนู *IAM & Admin → Service Accounts* → สร้างบัญชีบริการใหม่
4. ที่บัญชีบริการที่สร้าง กดแถบ *Keys → Add Key → Create new key (JSON)*
5. แปลงเนื้อหาไฟล์ JSON ที่ดาวน์โหลดมาให้อยู่ใน **บรรทัดเดียว (Minified JSON)** แล้วนำมาใส่ใน:
   * `GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}`
6. คอนฟิกโฟลเดอร์ปลายทางบนไดรฟ์ของบริษัท:
   * `GOOGLE_DRIVE_PARENT_ID`: รหัสโฟลเดอร์หลักบน Google Drive ที่ต้องการให้เก็บรูปและไฟล์
   * `SPREADSHEET_ID`: รหัสของเทมเพลตไฟล์ Google Sheets ที่ต้องการใช้สำหรับทำสรุปยอดการกระทบยอดการเงิน

---

## 7. STRIPE PAYMENT
ระบบรับชำระเงินค่าสมัครใช้งานแพ็กเกจ (Pro / Business) พร้อมการออกใบเสร็จและการตรวจสอบสลิปอัตโนมัติ

1. ลงทะเบียนและเข้าใช้งาน [Stripe Dashboard](https://dashboard.stripe.com/)
2. สลับไปโหมดทดสอบ (Test Mode) หรือใช้งานจริง และคัดลอก **Secret key** (เริ่มต้นด้วย `sk_test_` หรือ `sk_live_`):
   * `STRIPE_SECRET_KEY`
3. ไปเมนู Products → สร้างแผนราคา (Pro 299 บาท, Business 599 บาท ทั้งแบบบัตรเครดิตปกติ และ PromptPay)
4. คัดลอกรหัสราคา (Price ID เริ่มต้นด้วย `price_`) นำมาใส่ใน:
   * `STRIPE_PRICE_PRO`
   * `STRIPE_PRICE_BUSINESS`
   * `STRIPE_PRICE_PRO_PROMPTPAY`
   * `STRIPE_PRICE_BUSINESS_PROMPTPAY`
   * `STRIPE_PRICE_TEST_1THB` (คีย์ทดสอบ 1 บาท)
5. ไปที่ Stripe Developers → Webhooks → สร้าง Webhook Endpoint ใหม่:
   * **Endpoint URL**: `https://<BASE_URL>/webhook/stripe`
   * **เหตุการณ์ที่เปิดรับ (Events)**: เลือก `checkout.session.completed` และ `invoice.payment_succeeded`
   * คัดลอกคีย์ความลับของ Webhook มาใส่ใน: `STRIPE_WEBHOOK_SECRET=whsec_...`
