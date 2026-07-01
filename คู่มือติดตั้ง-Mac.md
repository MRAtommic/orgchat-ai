# คู่มือติดตั้ง OrgChat บน Mac
### ฉบับสมบูรณ์ — ตั้งแต่เปิดเครื่องจนระบบใช้งานได้

---

## สิ่งที่ต้องเตรียมก่อนเริ่ม

- Mac (Intel หรือ Apple Silicon M1/M2/M3)
- เชื่อมต่ออินเทอร์เน็ต
- เวลาประมาณ 30–60 นาที

---

## ขั้นตอนที่ 1 — ติดตั้ง Tools ที่จำเป็น

### 1.1 เปิด Terminal

กด `Command (⌘) + Space` → พิมพ์ **Terminal** → กด Enter

---

### 1.2 ติดตั้ง Homebrew

Homebrew คือตัวจัดการโปรแกรมบน Mac — จำเป็นสำหรับขั้นตอนต่อไป

วางคำสั่งนี้ใน Terminal แล้วกด Enter:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

> ระหว่างติดตั้งจะถามรหัสผ่าน Mac ให้ใส่แล้วกด Enter (ตัวอักษรจะไม่แสดง — ปกติ)

ตรวจสอบว่าติดตั้งสำเร็จ:

```
brew --version
```

ต้องเห็นข้อความประมาณ `Homebrew 4.x.x`

**สำหรับ Mac Apple Silicon (M1/M2/M3) เพิ่มเติม:**
หลังติดตั้ง Homebrew ให้รันคำสั่งที่มันแนะนำท้ายหน้าจอ (ขึ้นต้นด้วย `echo 'eval`) เพื่อเพิ่ม Homebrew เข้า PATH

---

### 1.3 ติดตั้ง Python และ Tesseract

```
brew install python@3.11 tesseract git
```

> Tesseract ใช้สำหรับอ่านข้อความจากรูปภาพใน Knowledge Base

ตรวจสอบ:

```
python3 --version
tesseract --version
```

ต้องเห็น Python 3.11.x และ tesseract 5.x

---

## ขั้นตอนที่ 2 — วางโค้ดลงเครื่อง

### กรณีได้รับไฟล์ zip มา

1. แตก zip ไฟล์
2. เปิด Terminal แล้วลาก **โฟลเดอร์ webai** เข้าไปใน Terminal หน้าต่าง จะได้ path อัตโนมัติ
3. พิมพ์ `cd ` (มีเว้นวรรค) แล้วลากโฟลเดอร์ใส่ กด Enter

ตัวอย่าง:

```
cd /Users/yourname/Downloads/orgchat-ai-main/webai
```

ตรวจสอบว่าอยู่ถูกโฟลเดอร์:

```
ls
```

ต้องเห็นไฟล์ `app_server.py`, `requirements.txt`, `.env`

---

## ขั้นตอนที่ 3 — เตรียม API Keys

เปิด browser แล้วไปสมัครตามตารางด้านล่าง จดหรือ copy key ไว้

---

### 3.1 AI หลัก — เลือกอย่างใดอย่างหนึ่ง

#### ตัวเลือก A: Groq (แนะนำ — ฟรี เร็ว)

1. ไปที่ **https://console.groq.com**
2. สมัครหรือ Login
3. คลิก **API Keys** → **Create API Key**
4. ตั้งชื่อ key → คัดลอก key เริ่มต้นด้วย `gsk_...`
5. เก็บไว้ — **จะดูได้ครั้งเดียว**

#### ตัวเลือก B: Google Gemini

1. ไปที่ **https://aistudio.google.com/app/apikey**
2. Login ด้วย Google Account
3. คลิก **Create API Key**
4. คัดลอก key เริ่มต้นด้วย `AIzaSy...`

---

### 3.2 Google Gemini (สำหรับ Knowledge Base)

> **จำเป็นต้องมีเสมอ** แม้จะเลือก Groq เป็น AI หลัก
> ถ้าสมัคร Gemini ไปแล้วในข้อ 3.1 ใช้ key เดิมได้เลย

---

### 3.3 LINE Bot (ถ้าต้องการเชื่อม LINE)

1. ไปที่ **https://developers.line.biz/console/**
2. Login ด้วย LINE account
3. คลิก **Create a Provider** → ตั้งชื่อ
4. คลิก **Create a Messaging API channel**
5. กรอกข้อมูล → สร้าง channel
6. เข้า channel → **Basic settings** → คัดลอก **Channel secret**
7. ไปที่ tab **Messaging API** → เลื่อนลงหา **Channel access token** → คลิก **Issue** → คัดลอก

---

### 3.4 Google Login (ถ้าต้องการให้ผู้ใช้ Login ด้วย Google)

1. ไปที่ **https://console.cloud.google.com**
2. Login → สร้าง Project ใหม่ (ถ้ายังไม่มี)
3. ไปที่ **APIs & Services** → **Credentials**
4. คลิก **+ Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs: เพิ่ม `http://localhost:5005/api/auth/google/callback`
7. คลิก **Create** → คัดลอก **Client ID** และ **Client Secret**

---

### 3.5 Stripe (ถ้าต้องการรับชำระเงิน)

1. ไปที่ **https://dashboard.stripe.com**
2. สมัครหรือ Login
3. **Developers** → **API keys** → คัดลอก **Secret key** (`sk_live_...` หรือ `sk_test_...`)
4. **Products** → สร้าง Product → สร้าง Price สำหรับแต่ละ Plan → คัดลอก Price ID (`price_...`)
5. **Developers** → **Webhooks** → **Add endpoint**
   - URL: `https://yourdomain.com/webhook/stripe`
   - Events: เลือก `checkout.session.completed` และ `invoice.payment_succeeded`
   - คัดลอก **Signing secret** (`whsec_...`)

---

## ขั้นตอนที่ 4 — ตรวจสอบไฟล์ .env

ไฟล์ `.env` มีอยู่แล้วในโฟลเดอร์ `webai/` พร้อม key จริงครบทุกตัว
เปิดดูหรือแก้ไขได้ด้วย:

```
open -e .env
```

**สิ่งที่ควรตรวจสอบก่อนรัน:**

| ค่า | ควรเป็น |
|-----|---------|
| `BASE_URL` | `http://localhost:5005` ถ้าทดสอบบน Mac |
| `BASE_URL` | `https://openchat.sbs` ถ้า deploy จริง |
| `PORT` | `5005` |
| `STRIPE_SECRET_KEY` | เริ่มด้วย `sk_live_` ถ้า production, `sk_test_` ถ้าทดสอบ |
| `DB_PATH` | `chat_history.db` (ไฟล์ฐานข้อมูลจะถูกสร้างอัตโนมัติ) |

บันทึกไฟล์หลังแก้: `Command (⌘) + S` → ปิด TextEdit

---

## ขั้นตอนที่ 5 — ติดตั้ง Python Packages

กลับไปที่ Terminal (ต้องอยู่ในโฟลเดอร์ webai):

```
python3 -m venv venv
```

```
source venv/bin/activate
```

> Prompt จะเปลี่ยนเป็น **(venv)** ด้านหน้า — แสดงว่าเปิดใช้งานแล้ว

```
pip install --upgrade pip
```

```
pip install -r requirements.txt
```

> ขั้นนี้ใช้เวลา **5–15 นาที** ครั้งแรก เพราะต้อง download โมเดล AI (~500MB)
> ห้ามปิด Terminal ระหว่างติดตั้ง

ถ้าใช้ **Apple Silicon (M1/M2/M3)** และเจอ error เรื่อง chromadb:

```
pip install chromadb --no-binary chromadb
```

---

## ขั้นตอนที่ 6 — รันระบบ

```
source venv/bin/activate
python app_server.py
```

ถ้าสำเร็จจะเห็น:

```
>>> SYSTEM v11.0.4 READY.
 * Running on http://0.0.0.0:5005
```

เปิด browser ไปที่: **http://localhost:5005**

หยุด server: กด `Control + C`

---

## ขั้นตอนที่ 7 — ตั้งค่าครั้งแรกในระบบ

### 7.1 สมัครบัญชี Admin

1. หน้าแรก → คลิก **Register**
2. ตั้งชื่อ username ว่า **Admin** (ตัว A ใหญ่)
3. ใส่ email และรหัสผ่าน → สมัคร
4. Login ด้วยบัญชีนี้

> ชื่อ `Admin` ต้องตรงกับค่า `SUPERADMIN_USERS=Admin` ในไฟล์ `.env`

### 7.2 เข้าหน้า Super Admin

ไปที่: **http://localhost:5005/admin/super**

### 7.3 สร้าง Organization แรก

Super Admin Panel → แท็บ **Organizations** → **Create Organization**

---

## ขั้นตอนที่ 8 — รันแบบ Background (ไม่ต้องเปิด Terminal ค้างไว้)

สร้างไฟล์ Launch Agent:

```
nano ~/Library/LaunchAgents/com.orgchat.plist
```

วางเนื้อหาด้านล่างทั้งหมด **(แก้ YOUR_USERNAME และ PATH_TO_WEBAI ให้ตรง)**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.orgchat</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/PATH_TO_WEBAI/venv/bin/gunicorn</string>
        <string>app_server:app</string>
        <string>--worker-class</string>
        <string>gthread</string>
        <string>--workers</string>
        <string>1</string>
        <string>--threads</string>
        <string>4</string>
        <string>--bind</string>
        <string>0.0.0.0:5005</string>
        <string>--timeout</string>
        <string>300</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/PATH_TO_WEBAI</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/YOUR_USERNAME/PATH_TO_WEBAI/venv/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/orgchat.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/orgchat-error.log</string>
</dict>
</plist>
```

บันทึก: `Control + O` → Enter → `Control + X`

เปิดใช้งาน:

```
launchctl load ~/Library/LaunchAgents/com.orgchat.plist
launchctl start com.orgchat
```

ดู log:

```
tail -f /tmp/orgchat.log
```

---

## ขั้นตอนที่ 9 — เปิดให้เข้าถึงจากภายนอก (สำหรับ LINE Webhook)

ถ้าต้องการเชื่อม LINE หรือให้คนนอกเข้าถึง ต้องมี URL สาธารณะ

### ตัวเลือก A: Cloudflare Tunnel (แนะนำ — ฟรี ไม่หมดอายุ)

```
brew install cloudflared
cloudflared tunnel --url http://localhost:5005
```

จะได้ URL เช่น `https://xxxx.trycloudflare.com`

อัปเดต `.env`:

```
BASE_URL=https://xxxx.trycloudflare.com
```

รีสตาร์ท server

### ตัวเลือก B: ngrok

```
brew install ngrok
ngrok http 5005
```

จะได้ URL เช่น `https://xxxx.ngrok-free.app`

> URL จะเปลี่ยนทุกครั้งที่รีสตาร์ท (เว้นแต่ใช้แผนเสียเงิน)

---

## คำสั่งที่ใช้บ่อย

| คำสั่ง | ความหมาย |
|--------|----------|
| `source venv/bin/activate` | เปิด virtual environment |
| `python app_server.py` | รัน server ปกติ |
| `deactivate` | ปิด virtual environment |
| `launchctl start com.orgchat` | เริ่ม background service |
| `launchctl stop com.orgchat` | หยุด background service |
| `tail -f /tmp/orgchat.log` | ดู log แบบ real-time |
| `lsof -i :5005` | ดูว่าอะไรใช้ port 5005 อยู่ |

---

## Checklist ก่อนส่งมอบ

```
[ ] ติดตั้ง Homebrew, Python 3.11, Tesseract สำเร็จ
[ ] ไฟล์ .env ตั้งค่าครบ (BASE_URL, GROQ_API_KEY, GEMINI_API_KEY)
[ ] pip install -r requirements.txt ผ่านไม่มี error
[ ] รัน python app_server.py แล้ว startup ไม่มี error
[ ] เปิด http://localhost:5005 ได้
[ ] สมัคร account Admin และเข้า /admin/super ได้
[ ] สร้าง Organization ได้
[ ] ทดสอบส่งข้อความ AI ได้รับคำตอบ
[ ] (ถ้าใช้ LINE) LINE Webhook Verify ผ่าน
[ ] (ถ้าใช้ Stripe) ทดสอบ checkout ด้วย test card ผ่าน
```

---

## แก้ปัญหาที่พบบ่อยบน Mac

| ปัญหา | วิธีแก้ |
|-------|---------|
| `command not found: python` | ใช้ `python3` แทน |
| `command not found: brew` | ติดตั้ง Homebrew ใหม่ตามขั้นตอน 1.2 |
| `ERROR: Could not build chromadb` | `pip install chromadb --no-binary chromadb` |
| `tesseract: command not found` | `brew install tesseract` แล้วปิด-เปิด Terminal ใหม่ |
| Port 5005 ถูกใช้อยู่แล้ว | `lsof -i :5005` แล้ว `kill -9 PID_ที่เห็น` |
| `SSL: CERTIFICATE_VERIFY_FAILED` | เปิด Finder → Applications → Python 3.11 → ดับเบิลคลิก `Install Certificates.command` |
| packages build ล้มเหลว (M1/M2) | `pip install --upgrade pip setuptools wheel` ก่อน แล้วลองใหม่ |
| ลืม activate venv | ถ้าหน้า prompt ไม่มี `(venv)` ให้รัน `source venv/bin/activate` ก่อน |

---

## ข้อมูลติดต่อ

หากติดปัญหาระหว่างติดตั้ง สามารถส่ง log error มาได้ที่:  
**ai.heartwarming@gmail.com**

---

*เอกสารนี้ใช้สำหรับ OrgChat v11.0.4 — อัปเดต 2026-05-26*
