# คู่มือส่งมอบและดูแลระบบ OrgChat AI

คู่มือนี้สำหรับทีมไอทีหรือผู้รับมอบระบบ เพื่อให้สามารถเปลี่ยน API Key บริการต่าง ๆ ดูแลรักษา และแก้ปัญหาเบื้องต้นได้

---

## 1. การเปลี่ยน LINE Bot

1. ไปที่ [LINE Developers Console](https://developers.line.biz/)
2. สร้าง Provider และ Messaging API Channel
3. คัดลอก **Channel Secret** (แท็บ Basic settings) และ **Channel Access Token** (แท็บ Messaging API → กด Issue)
4. เปิดไฟล์ `webai/.env` แก้ไขค่า:
   ```
   LINE_CHANNEL_ACCESS_TOKEN=ค่าใหม่
   LINE_CHANNEL_SECRET=ค่าใหม่
   ```
5. ใน LINE Developers Console ตั้ง Webhook URL เป็น `https://yourdomain.com/callback`
6. รีสตาร์ท server

---

## 2. การเปลี่ยน AI Provider

### Groq (AI สนทนาหลัก)
1. ไปที่ [console.groq.com/keys](https://console.groq.com/keys) → Create API Key
2. แก้ไขใน `webai/.env`:
   ```
   AI_PROVIDER=groq
   GROQ_API_KEY=gsk_...
   GROQ_API_KEY_BACKUP=gsk_...   # key สำรอง (ถ้ามี)
   ```

### Google Gemini (Knowledge Base Embedding)
1. ไปที่ [aistudio.google.com](https://aistudio.google.com/app/apikey) → Create API Key
2. แก้ไขใน `webai/.env`:
   ```
   AI_EMBEDDING_PROVIDER=gemini
   GEMINI_API_KEY=AIzaSy...
   ```

---

## 3. การเปลี่ยน Google Drive / Sheets (Service Account)

ระบบใช้ **Service Account** (ไม่ใช่ OAuth ส่วนตัว) เพื่อเข้าถึง Drive/Sheets ขององค์กร

### วิธีสร้าง Service Account ใหม่
1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. เลือก Project → **IAM & Admin** → **Service Accounts** → **Create Service Account**
3. ตั้งชื่อ → Create → ข้ามขั้นตอน Grant/Grant access
4. คลิก Service Account ที่สร้าง → แท็บ **Keys** → **Add Key** → **Create new key** → JSON → Download
5. เปิดไฟล์ JSON ที่ได้ — **Minify** (ลบ whitespace/newline ให้อยู่บรรทัดเดียว) แล้วใส่ทั้งก้อนใน `.env`:
   ```
   GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
   ```
6. แชร์โฟลเดอร์ Drive และ Spreadsheet ให้ email ของ Service Account (รูปแบบ `xxxxx@project.iam.gserviceaccount.com`) เป็น **Editor**
7. อัปเดต Folder ID และ Spreadsheet ID ใน `.env`:
   ```
   GOOGLE_DRIVE_PARENT_ID=ไอดีโฟลเดอร์จาก URL Drive
   SPREADSHEET_ID=ไอดี Spreadsheet
   ```

> **หมายเหตุ**: ไม่มีไฟล์ credentials.json หรือ token.json ในโปรเจกต์นี้ ทุกอย่างอยู่ใน `.env` เท่านั้น

---

## 4. การเปลี่ยน Google OAuth2 (Login ด้วย Google)

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**
2. **+ Create Credentials** → **OAuth 2.0 Client IDs** → Web application
3. Authorized redirect URIs เพิ่ม: `https://yourdomain.com/api/auth/google/callback`
4. คัดลอก Client ID และ Client Secret
5. แก้ไขใน `webai/.env`:
   ```
   GOOGLE_OAUTH2_CLIENT_ID=xxxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_ID=xxxxxxxxx.apps.googleusercontent.com
   GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-...
   OAUTH2_REDIRECT_URI=https://yourdomain.com/api/auth/google/callback
   ```

---

## 5. การเปลี่ยน Stripe (ระบบชำระเงิน)

1. ไปที่ [dashboard.stripe.com](https://dashboard.stripe.com) → **Developers** → **API keys**
2. คัดลอก **Secret key** (`sk_live_...` สำหรับ production, `sk_test_...` สำหรับทดสอบ)
3. **Products** → สร้าง Product → สร้าง Price → คัดลอก Price ID (`price_...`)
4. **Developers** → **Webhooks** → **Add endpoint**
   - URL: `https://yourdomain.com/webhook/stripe`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`
   - คัดลอก Signing secret (`whsec_...`)
5. แก้ไขใน `webai/.env`:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PRICE_PRO=price_...
   STRIPE_PRICE_BUSINESS=price_...
   ```

> **คำเตือน**: ตรวจสอบให้แน่ใจว่าใช้ `sk_live_` ก่อน production เสมอ

---

## 6. รายการ Environment Variables ทั้งหมด

ไฟล์อยู่ที่ `webai/.env`

```env
# ── ระบบ ─────────────────────────────────────────────────────────────────
FLASK_SECRET_KEY=รหัสสุ่มยาว ๆ (ใช้คำสั่ง: python -c "import secrets; print(secrets.token_hex(32))")
BASE_URL=https://yourdomain.com
PORT=5005
TZ=Asia/Bangkok
SUPERADMIN_USERS=Admin

# ── Database ──────────────────────────────────────────────────────────────
DB_PATH=chat_history.db

# ── AI Provider ──────────────────────────────────────────────────────────
AI_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_API_KEY_BACKUP=gsk_...

# ── Google Gemini (Embedding / Knowledge Base) ───────────────────────────
AI_EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
GEMINI_API_KEY_2=AIzaSy...
GEMINI_API_KEY_3=AIzaSy...

# ── LINE Bot ─────────────────────────────────────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_CHANNEL_SECRET=...

# ── Google OAuth2 (Sign in with Google) ──────────────────────────────────
GOOGLE_OAUTH2_CLIENT_ID=xxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_ID=xxxxxxxxx.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-...
OAUTH2_REDIRECT_URI=https://yourdomain.com/api/auth/google/callback

# ── Google Drive / Sheets (Service Account) ──────────────────────────────
GOOGLE_DRIVE_PARENT_ID=ไอดีโฟลเดอร์ Drive
SPREADSHEET_ID=ไอดี Spreadsheet
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",...}

# ── Stripe ───────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_BUSINESS=price_...
STRIPE_PRICE_PRO_PROMPTPAY=price_...
STRIPE_PRICE_BUSINESS_PROMPTPAY=price_...
```

---

## 7. การ Deploy บน Server (Oracle Cloud / VPS Ubuntu)

ดูรายละเอียดทั้งหมดในไฟล์ **`คู่มือ-Deploy-Oracle-Cloud.md`**

สรุปสั้น ๆ:
```bash
# Clone โปรเจกต์
git clone <repo> ~/orgchat

# ติดตั้ง dependencies
cd ~/orgchat/webai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# แก้ .env ให้ครบ
nano .env

# รันด้วย deploy script
cd deploy
bash deploy_vps.sh
```

Server ใช้ **gunicorn + gthread**, nginx reverse proxy ที่ port 8080 → 80/443

---

## 8. การดูแลรักษาระบบ

### Database
- ไฟล์ database อยู่ที่ `webai/chat_history.db` (กำหนดใน `.env` ที่ `DB_PATH`)
- ควรสำรองข้อมูลสม่ำเสมอ:
  ```bash
  cp webai/chat_history.db backup/chat_history_$(date +%Y%m%d).db
  ```

### Log
```bash
# ดู log แบบ real-time
sudo journalctl -u orgchat -f

# หรือถ้าใช้ไฟล์ log
tail -f /var/log/orgchat/app.log
```

### รีสตาร์ท Service
```bash
sudo systemctl restart orgchat
sudo systemctl status orgchat
```

### อัปเดตโค้ด
```bash
cd ~/orgchat
git pull
cd webai
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart orgchat
```

---

## 9. ความปลอดภัย

- **ห้าม** commit ไฟล์ `.env` ขึ้น GitHub (**ไฟล์นี้มี key จริงทั้งหมด**)
- ไม่มีไฟล์ credentials.json หรือ token.json ในโปรเจกต์ — ทุก key อยู่ใน `.env` เท่านั้น
- ถ้า key หาย: เปลี่ยนทันทีที่ console ของ provider แล้วอัปเดต `.env`
- `FLASK_SECRET_KEY` ถ้าเปลี่ยน: session ผู้ใช้ทั้งหมดจะหมดอายุ (ต้อง login ใหม่)

---

*OrgChat v11.0.4 — เอกสารนี้อัปเดต 2026-05-26*
