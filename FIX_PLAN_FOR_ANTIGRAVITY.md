# แผนแก้ไข OrgChat AI ก่อนขึ้น Production (สำหรับ Antigravity)

> เอกสารนี้เขียนจากการตรวจโค้ดจริงเมื่อ 2026-11-04 ทุกข้อมี **ไฟล์/บรรทัดที่อ้างอิง** และ **เกณฑ์ผ่าน (Acceptance)**
> ข้อที่ติดป้าย `[ยืนยันแล้ว]` = รันหรืออ่านโค้ดแล้วพบจริง, `[ต้องตรวจ]` = สงสัยจาก grep ยังไม่ได้ยืนยัน

## กติกาการทำงาน (อ่านก่อน)
- ห้ามรัน background task / loop เองโดยไม่ได้รับคำสั่ง (ดู `.agents/AGENTS.md`)
- ห้ามเปิด/พิมพ์/commit ไฟล์ `.env` (มี key จริง) และห้าม push ขึ้น git จนกว่าเจ้าของโปรเจกต์สั่ง
- โค้ดอยู่ใน `webai/` รันเทสต์ด้วย: `cd webai` แล้ว `..\.venv\Scripts\python.exe run_tests.py`
  (ปัจจุบัน 59 เทสต์ ต้องผ่านทั้งหมดหลังแก้ทุกข้อ)
- แก้ทีละข้อ → เพิ่มเทสต์ → รันเทสต์ทั้งชุด → ค่อยไปข้อถัดไป ห้ามแก้หลายข้อรวมกันแล้วรันครั้งเดียว
- ทำงานตามลำดับ P0 → P1 → P2 → P3

---

## P0 — ต้องแก้ทันที (ช่องโหว่ที่ใช้ได้จริง)

### P0-1 `/api/line/test-login` เป็น backdoor เข้าระบบเป็น superadmin โดยไม่ต้อง login `[ยืนยันแล้ว]`
- **ไฟล์:** `webai/routes/auth.py` ฟังก์ชัน `line_test_login` (~บรรทัด 4122) และลิงก์ใน `webai/templates/index.html:240`
- **ปัญหา:** GET เดียวโดยไม่มี session ก็ได้ session ของผู้ใช้ `mxmm2547` ที่ role = superadmin (ทดสอบแล้วบนเครื่อง dev คืน 302 และ session เป็น superadmin) ไม่มีการตรวจ environment
- **ต้องทำ:** ลบ route นี้ทิ้งทั้งหมด และลบลิงก์ใน `index.html` ถ้าต้องการ dev helper ให้เปิดเฉพาะเมื่อ `not is_production()` และ host เป็น localhost เท่านั้น (`is_production` อยู่ใน `routes/shared.py`)
- **Acceptance:** เพิ่มเทสต์ว่า GET/POST `/api/line/test-login` ได้ 404 (หรือ 403 นอก localhost) และ `session` ไม่มี `user`
- **หลังแก้:** เจ้าของระบบต้องตรวจ `audit log` หา event "Simulated LINE Login SSO (Dev Mode)" ว่ามีใครใช้ใน production หรือไม่ และเปลี่ยนรหัส/ทำให้ session เก่าหมดอายุ (เพิ่ม session_version)

### P0-2 secret สำรองที่ฮาร์ดโค้ด `[ยืนยันแล้ว]`
- **ไฟล์:** `webai/routes/auth.py` ~บรรทัด 2690 และ 2709 `os.environ.get("SECRET_KEY", "orgchat-default-secret-change-me")`
- **ปัญหา:** ถ้าไม่ได้ตั้ง `SECRET_KEY` ใครก็ปลอม invite token ได้ และชื่อตัวแปรไม่ตรงกับ `FLASK_SECRET_KEY` ที่คู่มือบอกให้ตั้ง
- **ต้องทำ:** รวมเป็นตัวแปรเดียว (ใช้ `FLASK_SECRET_KEY` และรองรับ `SECRET_KEY` เป็น alias) ถ้าไม่ได้ตั้งใน production ให้ `RuntimeError` ตอนสตาร์ท (ใช้ `is_production()`) ใน dev ค่อยสุ่มค่าชั่วคราว
- **Acceptance:** เทสต์ว่า production + ไม่มี secret → สตาร์ทไม่ได้, token ที่เซ็นด้วยค่าเริ่มต้นเก่าใช้ไม่ได้ (ถอด legacy token fallback ที่ไม่มี timestamp ด้วย)

### P0-3 cookie ไม่ Secure โดยค่าเริ่มต้น `[ยืนยันแล้ว]`
- **ไฟล์:** `webai/app_server.py` ~บรรทัด 291-298 ตั้ง `SESSION_COOKIE_SECURE=True` เฉพาะเมื่อ env `SESSION_COOKIE_SECURE=true`
- **ต้องทำ:** ให้ค่าเริ่มต้นเป็น `True` เมื่อ `is_production()` (ปิดได้ด้วย env เท่านั้นเมื่อมีเหตุผล)
- **Acceptance:** เทสต์อ่าน `app.config['SESSION_COOKIE_SECURE']` ภายใต้ `APP_ENV=production`

### P0-4 หมุน key ทั้งหมด (งานของเจ้าของ ไม่ใช่โค้ด)
- Groq, Gemini, LINE token/secret, Stripe, Google service account, Google OAuth client secret, `FLASK_SECRET_KEY`
- เหตุผล: `.env` เคยอยู่ในโฟลเดอร์ที่ถูกบีบอัด/แชร์ (`orgchat-ai-main.rar`, backups) — ถือว่าอาจรั่ว
- Antigravity: **ห้ามทำเอง** ให้แค่ตรวจว่า `.gitignore` ครอบ `.env*`, `*.rar`, `*.zip` และไม่มีไฟล์ลับถูก track (`git ls-files`)

---

## P1 — ความปลอดภัยที่เหลือ

### P1-1 `/uploads/social_feed/<file>` เปิดให้ใครก็ได้ที่ปลอม User-Agent `[ยืนยันแล้วจากโค้ด]`
- **ไฟล์:** `webai/routes/misc.py` ~บรรทัด 91-115 ถ้า UA มี `linebot-imagefetch`/`line-poker`/`facebookexternalhit` จะส่งไฟล์ทันทีโดยไม่ตรวจ login
- **ต้องทำ:** ลบเงื่อนไข UA ใช้เฉพาะ `preview_token` ที่เซ็นแล้ว (`verify_file_token`) หรือ login ตามเดิม
- **Acceptance:** เทสต์ request ที่ UA เป็น `linebot-imagefetch` แต่ไม่มี token/login → 401/403

### P1-2 SSRF guard อ่อน `[ยืนยันแล้วจากโค้ด]`
- **ไฟล์:** `webai/routes/shared.py` `_is_safe_url` (~บรรทัด 593) ตรวจเฉพาะ IP ที่เขียนตรง ๆ ชื่อโดเมนที่ resolve ไป IP ภายใน (หรือ 169.254.169.254 ผ่านโดเมน) ผ่านได้ และไม่ตามเช็ก redirect
- **ต้องทำ:** resolve ชื่อโฮสต์ด้วย `socket.getaddrinfo` แล้วตรวจทุก IP (private/loopback/link-local/reserved/multicast) ปิด redirect อัตโนมัติหรือตรวจซ้ำทุก hop และจำกัดพอร์ต; ใช้ฟังก์ชันเดียวกันกับ `web_crawler.py` และ `/api/link-preview`
- **Acceptance:** เทสต์ด้วย mock `getaddrinfo` ที่คืน 10.0.0.5 / 127.0.0.1 / 169.254.169.254 → ปฏิเสธ

### P1-3 `/api/evaluation/submit` และ `/api/evaluation/stats` ไม่ต้อง login และเชื่อ username/role จาก body `[ยืนยันแล้วจากโค้ด]`
- **ไฟล์:** `webai/routes/misc.py` ~บรรทัด 592-640
- **ปัญหา:** ใครก็ส่งคะแนนปลอมซ้ำได้ ปั่นสถิติ (ถ้าใช้ผลนี้ในงานวิจัย/รายงาน ข้อมูลไม่น่าเชื่อถือ) และปลอมเป็น role อื่นได้
- **ต้องทำ:** ใช้ `session["user"]`/`session["role"]` เท่านั้น ไม่รับจาก body, จำกัด 1 ครั้งต่อผู้ใช้ (หรือต่อ IP ถ้า anonymous), ใส่ rate limit, clamp คะแนน 1-5
- **Acceptance:** เทสต์ส่งซ้ำ → ปฏิเสธ, ส่ง `role=superadmin` ใน body → ถูกเมิน, คะแนน 99 → ถูก clamp หรือปฏิเสธ

### P1-4 `/api/auth/google/debug-uri` เปิดสาธารณะ `[ยืนยันแล้ว]`
- **ไฟล์:** `webai/routes/auth.py` ~บรรทัด 342 → ลบ หรือจำกัดเฉพาะ admin/dev

### P1-5 endpoint ที่ไม่ต้อง login แต่ควรตรวจ rate limit/ความเสี่ยง `[ต้องตรวจ]`
- `/api/2fa/send-email-otp`, `/api/auth/forgot-password`, `/api/auth/verify-reset-otp`, `/api/qr/generate`, `/api/org/signup`, `/api/login`, `/api/login/google`
- ตรวจ: มี `_limiter.limit` ทุกตัว, OTP หมดอายุและใช้ได้ครั้งเดียว, เปรียบเทียบ OTP แบบ constant-time (`hmac.compare_digest`), ข้อความ error ไม่บอกว่ามีอีเมลนี้ในระบบหรือไม่ (user enumeration), มีการล็อกบัญชีหลังพยายามผิดซ้ำ (ตรวจ `db/finance.py` ส่วน lockout ว่าถูกเรียกใช้จริงใน `/api/login`)
- **Acceptance:** เทสต์ล็อกอินผิดเกินกำหนดแล้วถูกล็อก; OTP ใช้ซ้ำไม่ได้

### P1-6 `requests` ที่ไม่มี timeout `[ต้องตรวจ]`
- grep พบราว 18 จุด (อาจเป็นการเรียกหลายบรรทัดที่ timeout อยู่บรรทัดถัดไป ให้ตรวจด้วยตา): `line_webhook.py`, `oauth2_service.py:698,740`, `peak_service.py:47,103`, `rag_engine.py:254`, `routes/admin.py:5018`
- **ต้องทำ:** ทุก call ต้องมี `timeout=(connect, read)` ถ้าไม่มี worker อาจค้างจน gunicorn timeout 120 วินาที (มี 2 worker × 8 thread เท่านั้น)

---

## P2 — บั๊กความถูกต้องของข้อมูล

### P2-1 ฟังก์ชัน DB ถูกประกาศซ้ำ (ตัวหลังทับตัวแรกเงียบ ๆ) `[ยืนยันแล้ว]`
ปัญหาแบบเดียวกับที่ทำให้ Kanban รั่วข้ามองค์กร (แก้ไปแล้วใน `db/social.py` เฉพาะ kanban) ที่ยังเหลือ:
| ไฟล์ | ฟังก์ชัน (บรรทัด) |
|---|---|
| `db/social.py` | `wiki_get_all_pages` 523/714, `wiki_get_page` 535/743, `wiki_create_page` 550/729, `wiki_update_page` 574/758, `wiki_delete_page` 600/780, `wiki_search` 609/721 |
| `db/finance.py` | `search_drive_logs` 214/327 |
| `db/orgs.py` | `transfer_org_ownership` 552/720 |
| `db/security.py` | `log_audit_event` 24/41/322 |
| `db/settings.py` | `log_event` 62/864 |
| `db/users.py` | `get_persona` 730/945 |
- **ต้องทำ:** เทียบแต่ละคู่ว่าตัวไหนถูกต้อง (ตัวหลังคือตัวที่ทำงานอยู่ตอนนี้) รวมเหลือตัวเดียว คงพฤติกรรมของตัวที่ใช้งานอยู่ ยกเว้นกรณีมีบั๊กชัดเจน ตรวจให้ `org_id` ถูกกรองทุก query; wiki ตัวแรก `wiki_get_all_pages(org_id=1)` ที่ default เป็น 1 ระวัง
- **เพิ่ม:** เทสต์อัตโนมัติ (AST) ที่ล้มเมื่อมี top-level function ซ้ำชื่อในไฟล์เดียวกันใต้ `webai/db/` กันบั๊กกลับมา
- **Acceptance:** เทสต์ผ่าน และเพิ่มเทสต์แยกองค์กรของ wiki (องค์กร A อ่าน/แก้/ลบหน้า wiki ขององค์กร B ไม่ได้)

### P2-2 ตรวจสิทธิ์องค์กรทุก query ที่รับ id จากผู้ใช้ `[ต้องตรวจ]`
- สาเหตุ: schema ใช้ทั้ง `org_id` และ `organization_id` ปนกัน (`db/schema.py`)
- ทำ: ไล่ทุก `UPDATE/DELETE/SELECT ... WHERE id = ?` ใน `db/*.py` ที่ตารางมีคอลัมน์ org และทุก route ที่เรียก ตรวจว่ามีเงื่อนไของค์กร หรือ route ตรวจ ownership ก่อนเรียก
- ลำดับความเสี่ยง: finance, leave, line_group_mappings, kanban_cards (แก้แล้ว), posts, user_settings
- Acceptance: เทสต์ "สององค์กร" ต่อโมดูลหลัก (ผู้ใช้องค์กร A เรียก endpoint ด้วย id ขององค์กร B ต้องได้ 403/404)

### P2-3 เทสต์เขียนลงฐานข้อมูลจริง `[ยืนยันแล้ว]`
- `tests/test_helpers.py` ตั้ง `database.DB_PATH` แต่ `db/connection.py` อ่านค่า path ตอน import → เทสต์เขียนลง `webai/chat_history.db` จริง (พบ Stripe event ของเทสต์ 38 รายการ)
- **ต้องทำ:** ตั้ง `DB_PATH` ผ่าน env ก่อน import `database` (เช่นใน `run_tests.py` และ `tests/__init__.py`) หรือให้ `_get_conn()` อ่าน path ทุกครั้ง; เพิ่มเทสต์ยืนยันว่าเทสต์ไม่แตะไฟล์ DB จริง
- ลบแถว `stripe_processed_events` ที่ขึ้นต้น `evt_` ที่เทสต์สร้าง **เฉพาะหลังสำรองไฟล์ DB และเจ้าของยืนยัน**

---

## P3 — สถาปัตยกรรมและความพร้อมใช้งานจริง

### P3-1 Vector store กำลังใช้ตัว fallback แบบ Pure Python `[ยืนยันแล้ว]`
- ตอนรันเทสต์ขึ้นข้อความ `No module named 'hnswlib'. Falling back to Pure Python Vector Store` และเทสต์ RAG 3 ตัวถูก skip (รวมเทสต์แยก vector ข้ามองค์กร)
- **ต้องทำ:** ใน `requirements.txt` บรรทัด `# hnswlib` ถูก comment ไว้ ให้ทำให้ติดตั้งได้ใน Docker (ต้องมี gcc/g++ ซึ่ง Dockerfile มีแล้ว) หรือเปลี่ยนไปใช้ vector store ที่เป็น service (pgvector/Qdrant) แล้วทำให้เทสต์ 3 ตัวนั้นรันจริงใน CI
- ต้องมี persistent volume ให้ `chroma_db/` บน Railway ไม่เช่นนั้นข้อมูล vector หายทุก deploy

### P3-2 ฐานข้อมูล
- ย้ายไป Postgres จริงใน production (ตอนนี้ `db/connection.py` เลียนแบบ sqlite3 บน psycopg2) ทดสอบทุก query กับ Postgres, ใช้ Alembic แทนการ `ALTER TABLE` ใน `schema.py`/`migrations.py`
- ตั้ง backup อัตโนมัติ + ทดสอบ restore (ปัจจุบันคู่มือมีแค่ `cp` มือ)

### P3-3 แตกไฟล์ใหญ่ (ทำหลังมีเทสต์ครอบคลุมเท่านั้น)
| ไฟล์ | ขนาด | แนวทาง |
|---|---|---|
| `routes/line_webhook.py` | 3,596 (เหลือหลังแยก Flex แล้ว) | `process_line_command` เดี่ยว ๆ ยาว ~1,400 บรรทัด → แยกเป็น command handlers ต่อคำสั่ง + dispatcher |
| `routes/admin.py` | 6,267 | แยกตามโดเมน: billing, users, settings, finance, backup |
| `routes/auth.py` | 4,312 | แยก login/2FA/OAuth/LINE login/org signup |
| `google_drive_service.py` | 4,116 | คลาส `GoogleWorkspaceManager` ยาว 3,676 บรรทัด → แยก Drive / Sheets / ภาษี-หัก ณ ที่จ่าย เป็น mixin หรือ service |
| `rag_engine.py` | 1,802 | แยก vector store / file processor / knowledge base |
- กฎ: ย้ายโค้ดโดยไม่เปลี่ยน logic, คง re-export ชื่อเดิม (ดูตัวอย่างที่ทำแล้ว `routes/line_flex.py`), ตรวจชื่อที่ไม่ได้นิยามด้วย AST, รันเทสต์ทุกครั้งที่ย้ายก้อนหนึ่ง

### P3-4 เทสต์ที่ขาด (เกี่ยวกับเงิน)
- ระบบกระทบยอด `reconciliation_service.py` (`process_files`), การลง Google Sheets (mock Sheets API), PEAK import, การคำนวณหัก ณ ที่จ่าย, OCR สลิป → ข้อมูลที่ลงบัญชี, LINE `process_line_command` (อย่างน้อยคำสั่งสรุปรายจ่ายและลา)
- เป้า: ครอบคลุมเส้นทางที่ทำให้ตัวเลขบัญชีเปลี่ยน

### P3-5 Logging / Observability
- เหลือ `print(` ราว 130 จุด (ไฟล์ที่ไม่มี `logger`: `db/chat.py`, `db/settings.py`, `db/finance.py`, `db/orgs.py` ฯลฯ) → เพิ่ม `logger = logging.getLogger(...)` แล้วแปลง
- ตั้ง `SENTRY_DSN` บน production (ตอนนี้โค้ดมีแต่ `.env` ไม่ได้ตั้ง) และทดสอบว่า error ส่งไปจริง
- แยก Celery worker เป็น service ของตัวเอง (ตอนนี้ `start_prod.sh` สตาร์ทเป็น background ไม่มี supervisor)

### P3-6 ความสะอาด repo
- แยก OrgChat ออกจากเกม/วิทยานิพนธ์/`.agents` ที่ปนอยู่ใน repo เดียว
- แก้ README ชั้นนอก (อ้าง `app.py`, `start.bat` ที่ไม่มี) และตามหา `คู่มือ-Deploy-Oracle-Cloud.md` ที่คู่มืออ้างถึงแต่ไม่พบ
- ลบ/ย้าย `scratch_*.py`, `_scratch/` ออกจาก `webai/`
- ตรวจ `project100_overleaf/OrgChat_Overleaf_Package.zip` ที่ถูก track ว่ามีข้อมูลลับหรือไม่
- `/api/auth/google/debug-uri` และโค้ดทดสอบอื่น ๆ ใน production ให้ลบ

### P3-7 กฎหมาย/ข้อมูลส่วนบุคคล (เจ้าของต้องตัดสินใจ ไม่ใช่งานโค้ดล้วน)
- PDPA: ข้อมูลใบลา/ใบรับรองแพทย์ ต้องมีนโยบายเก็บ-ลบข้อมูล, ความยินยอม, การส่งออก/ลบข้อมูลตามคำขอ
- ระบบบัญชี: เพิ่มขั้นตอน "คนตรวจก่อนลงบัญชี" สำหรับผล OCR/AI และ audit log (ใคร แก้อะไร เมื่อไร)
- แจ้งผู้ใช้ว่าข้อมูลถูกส่งไปยัง Groq/Gemini

---

## สถานะที่ทำไปแล้ว (อย่าทำซ้ำ)
commit `4ee8102` + การแก้ใน working tree ที่ยังไม่ commit:
- LINE signature ใช้ `hmac.compare_digest`; CORS fail ใน production; Kanban ข้ามองค์กร (ลบฟังก์ชันซ้ำ + ตรวจ column ปลายทาง); log error อัตราหัก ณ ที่จ่าย; แยก `routes/line_flex.py`; GitHub Actions CI (`.github/workflows/ci.yml`, ยังไม่เคยรันจริง); `tests/test_hardening.py`, `tests/test_stripe_flow.py`; แปลง `print` → `logger` 144 จุด (ยังไม่ commit)

## ลำดับที่แนะนำ
1. P0-1 → P0-2 → P0-3 (ครึ่งวัน, เทสต์ชุดเล็ก)
2. P1-1 → P1-3 → P1-2 → P1-4 → P1-5 → P1-6
3. P2-3 (ให้เทสต์ปลอดภัยก่อน) → P2-1 → P2-2
4. P3-1, P3-2 → P3-4 → P3-3 → P3-5 → P3-6
5. P3-7 เจ้าของโปรเจกต์ตัดสินใจคู่ขนานไปได้เลย

---

## ภาคผนวก — ผลทดสอบการโจมตีจริง (2026-11-04, สำเนาแยก ฐานข้อมูลเปล่า)

### ผ่านการทดสอบ (อย่าทำให้เสียหายเมื่อแก้ไฟล์ใหญ่)
CSRF บังคับใช้ (POST ไม่มี token → 403), ล็อกบัญชีหลังใส่รหัสผิดซ้ำ (ทดสอบหมุน IP ก็ยังล็อก), rate limit login 5/นาที, ข้อความ login ผิดไม่บอกว่ามี user หรือไม่, endpoint `/api/superadmin/*` ตอบ 403 สำหรับผู้ใช้สมัครฟรี, wiki/kanban ไม่รั่วข้ามองค์กร, path traversal ถูกบล็อก (403/404), WAF บล็อก SQLi/XSS/LFI, header ป้องกันพื้นฐาน (X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy) มีครบ
→ เพิ่มเทสต์ถาวรสำหรับสิ่งเหล่านี้ใน `webai/tests/` (ปัจจุบันครอบแค่บางส่วน)

### P1 เพิ่มเติม
- **CSP อ่อน:** `script-src` มี `'unsafe-inline' 'unsafe-eval'` ทำให้ XSS ที่หลุดเข้ามาใช้งานได้เต็มที่ (`app_server.py` ส่วน security headers) ต้องย้าย inline script/handler (487 `onclick=`) ออกแล้วใช้ nonce/hash และเลิก `unsafe-eval` (Tailwind CDN เป็นเหตุผลหนึ่ง → ดู U5 ในแผน UX)
- **ไม่มี `Strict-Transport-Security`** ในการตอบกลับของแอป (ตรวจในโหมดทดสอบ) ให้เพิ่มเมื่อ `is_production()` หรือยืนยันว่า proxy ใส่ให้
- **ข้อความ error รั่ว:** ~33 จุดใน `routes/` ส่ง `str(e)` หรือ f-string ของ exception กลับไปให้ client (เช่น `routes/auth.py` `/api/qr/generate`) → ใช้ข้อความกลางและ log รายละเอียดฝั่ง server (มี helper `_err500` ใน `line_webhook.py` ให้ใช้แบบเดียวกัน)
- **endpoint สาธารณะที่ไม่ควรเปิด:** `/api/auth/google/debug-uri` (เปิดเผยค่า config), `/health` (บอกชนิด DB), `/api/evaluation/stats`
- **`LEGACY_USER_*` env:** รองรับรหัสผ่านแบบ plain text เปรียบเทียบตรง ๆ (`routes/shared.py:724`) → ลบกลไกนี้ หรือ hash ทั้งหมด และ log warning ตอนสตาร์ท (มีแล้ว) ให้เจ้าของตรวจว่า `.env` ไม่มีตัวแปรนี้
- **สิทธิ์ superadmin อิงอีเมลฮาร์ดโค้ด** `mxmm2547@gmail.com` (`routes/shared.py:302`) และ `superadmin_required` ยอมรับ role `admin` ด้วย (บรรทัด 323-340) ทดสอบแล้วผู้ใช้ทั่วไปแก้อีเมลตัวเองไม่ทำให้เป็น superadmin แต่ต้องยืนยันว่า (1) อีเมลถูกตรวจยืนยันความเป็นเจ้าของก่อนใช้ตัดสินสิทธิ์ (2) ไม่มีเส้นทางให้ role `admin` ถูกตั้งโดยผู้ใช้เอง (3) ควรย้ายรายชื่อ superadmin ไป env/ตาราง ไม่ฮาร์ดโค้ด
- **Superadmin SQL console** (`/api/superadmin/db/query`, `/db/table/*/row*`) รัน SQL ดิบ ถ้าบัญชี superadmin ถูกยึดจะดูดข้อมูลทุกองค์กรได้ทันที → บังคับ 2FA สำหรับ superadmin, จำกัดเป็น read-only หรือปิดใน production, เก็บ audit log ที่แก้ไม่ได้
- **ล็อกบัญชีแบบถาวรโดยผู้โจมตี (DoS):** ใครก็ล็อกบัญชีคนอื่นได้ด้วยการใส่รหัสผิดซ้ำ → ใช้ backoff ตามเวลา/ตาม IP+ชื่อผู้ใช้ แทนล็อกยาวทั้งบัญชี และมีทางปลดล็อกทางอีเมล

### P2 เพิ่มเติม
- **ติดตั้งใหม่ Kanban พัง:** `db/schema.py:465` สร้าง `kanban_columns(id, name, org_id, position)` แต่โค้ดใน `db/social.py` ใช้คอลัมน์ `title/color/created_by` → บนฐานข้อมูลเปล่า `POST /api/kanban/columns` ตอบ 500 (ฐานข้อมูลเดิมของคุณใช้ได้เพราะถูกสร้างด้วย `kanban_init_db`) แก้ให้ schema เดียว + migration + เทสต์ "ฐานข้อมูลเปล่า → สร้าง column/card ได้"
- migration `003_leave_requests_indexes` ล้มบนฐานข้อมูลเปล่า (ดู U0-4 ในแผน UX)

---

## ข้อแก้ไขตามการใช้งานจริง (อ่านก่อนทำ P3) — ยืนยันเมื่อ 2026-11-04

**สภาพแวดล้อมจริง:** รันบนเครื่อง Windows ของเจ้าของโปรเจกต์ (`python app_server.py`, พอร์ต 5005) เปิดสู่อินเทอร์เน็ตผ่าน **Cloudflare Tunnel เท่านั้น** (`openchat.sbs` → `http://127.0.0.1:5005`, tunnel ชื่อ `orgchat`, config ที่ `%USERPROFILE%\.cloudflared\config.yml`) **ไม่ได้ใช้ Railway, Raspberry Pi, VPS, Docker**

ผลต่อแผนข้างบน:
- **P0-1 (`/api/line/test-login`) เร่งด่วนที่สุด:** route นี้น่าจะเข้าถึงได้จาก `https://openchat.sbs` ตอนนี้ ลบแล้วต้องรีสตาร์ตเซิร์ฟเวอร์ (โปรเซสที่รันอยู่โหลดโค้ดเก่า)
- **P0-3 / `is_production()`:** ปัจจุบันอิงตัวแปร `RAILWAY_*` ซึ่งไม่มีในเครื่องนี้ → ให้เลิกอิง Railway และตัดสินจาก `APP_ENV=production` เท่านั้น แล้วให้เจ้าของตั้ง `APP_ENV=production` (ใน `.env` หรือสคริปต์สตาร์ต) ไม่เช่นนั้นการบังคับ `BASE_URL`/CORS/secret ในโค้ดจะไม่ทำงาน
- **ลบไฟล์ที่ไม่ใช้:** `railway.toml`, `railway.json`, `Procfile`, `webai/Procfile`, `webai/railway.json`, ส่วนที่อ้าง Railway ใน `routes/shared.py` (`RAILWAY_STATIC_URL`), `app_server.py`, `google_drive_service.py`, `rag_engine.py`, `dns_patch.py`, `ENV_GUIDE.md` และ `webai/deploy/*pi*`, `deploy_vps.sh`, `nginx-openchat.conf`, `orgchat*.service` (ย้ายไป `archive/` ก็ได้ ถ้าเจ้าของยังไม่แน่ใจ) อัปเดต `COMPANY_HANDOVER_MANUAL.md` และ README ให้ตรงกับการรันบน Windows + Tunnel
- **P3-1 (hnswlib/volume) และ P3-2 (ย้าย Postgres): ยกเลิก** ไม่เหมาะกับการใช้งานจริง (องค์กรเดียว เครื่องเดียว) SQLite ใช้ต่อได้ถ้ามีการสำรองข้อมูลที่ดี
- **เพิ่มงานใหม่ (P1):**
  1. **เซิร์ฟเวอร์ production ตอนนี้คือ Flask dev server** (`socketio.run(..., allow_unsafe_werkzeug=True)` ใน `app_server.py` ~บรรทัด 1019; log แจ้ง "development server, do not use in production") → เปลี่ยนเป็น `waitress` (gunicorn ใช้บน Windows ไม่ได้) ทดสอบ Socket.IO ว่าทำงานแบบ long-polling ได้ และเพิ่มเทสต์ smoke
  2. **รันเป็นบริการ Windows ที่รีสตาร์ตเองได้** (NSSM หรือ Task Scheduler: at startup + restart on failure) ใช้ Python ใน `.venv` ของโปรเจกต์ ไม่ใช่ Python ระบบ (ตอนนี้โปรเซสใช้ `Python312` ระบบ) และกันเครื่อง sleep (Power plan: never sleep เมื่อเสียบปลั๊ก)
  3. **โฟลเดอร์โปรเจกต์อยู่ใน `OneDrive\Desktop`:** `.env` (key จริง), `chat_history.db`, `chroma_db`, `uploads` ถูกซิงก์ขึ้นคลาวด์ Microsoft และ SQLite บน OneDrive เสี่ยงไฟล์เสีย/ล็อก ให้ย้ายโฟลเดอร์รัน (โดยเฉพาะ `.env` + DB + uploads) ไปนอก OneDrive เช่น `C:\orgchat\` แล้วตั้ง `DB_PATH` ชี้ไปที่นั่น และเพิ่มสคริปต์สำรองข้อมูลรายคืน (ใช้ SQLite backup API ไม่ใช่ copy ไฟล์สด) ไปยังที่เก็บคนละที่กับเครื่อง พร้อมทดสอบกู้คืน
  4. **Cloudflare (ฝั่งเจ้าของทำ ไม่ใช่โค้ด):** ใส่ Cloudflare Access ครอบ path ผู้ดูแล (`/api/superadmin/*`, `/api/admin/*`, หน้า superadmin), ตั้ง WAF/rate-limit rule ที่ Cloudflare, ตรวจว่ามี cloudflared เพียงตัวเดียวต่อ tunnel (ตอนนี้พบทั้ง Windows service `Cloudflared` และโปรเซส `tunnel run orgchat` ผ่าน `npx` ทำงานพร้อมกัน)
  5. ตรวจว่า IP ที่ใช้ทำ rate limit/ล็อกบัญชี/log เป็น IP ผู้ใช้จริงผ่าน Cloudflare (`CF-Connecting-IP`) ไม่ใช่ `127.0.0.1` (ตอนนี้ใช้ `ProxyFix(x_for=1)`) ถ้าเป็น 127.0.0.1 ผู้ใช้ทุกคนจะแชร์ rate limit เดียวกัน
