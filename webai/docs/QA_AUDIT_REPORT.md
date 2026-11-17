# รายงานการตรวจสอบบั๊กและคุณภาพทั้งระบบ (Full QA Audit Report)

**โปรเจกต์:** OrgChat AI (`webai/`)  
**วันที่ตรวจสอบ:** 10–11 พฤศจิกายน 2026  
**อ้างอิงแผนงาน:** `webai/docs/PLAN_FULL_QA_AUDIT.md`  
**สถานะการทำงาน:** ดำเนินการครบทั้ง 3 รอบ (สำรวจ → แก้ไข → ยืนยันซ้ำ)  

---

## 1. บทสรุปผู้บริหาร (Executive Summary)

ตามที่ได้รับมอบหมายให้ตรวจสอบบั๊กทั้งระบบ ทุกฟังก์ชัน ทุกรูปแบบการใช้งาน โดยปฏิบัติตามกฎเหล็กอย่างเคร่งครัด (ไม่แตะต้อง `.env`, ไม่ยุ่งเกี่ยวกับ `chat_history.db` จริงหรือคลังความรู้จริง, เคลียร์ Secret ภายนอกก่อนรัน, รัน Pytest แยกโพรเซสทีละไฟล์เพื่อป้องกันปัญหาหน่วยความจำ):

1. **สิทธิ์ข้ามองค์กรและ Multi-Tenant (P0):** ผ่านการทดสอบและพิสูจน์การแยกข้อมูลเด็ดขาด ทุกคู่ (บทบาท × endpoint) ป้องกัน IDOR และข้ามองค์กรได้ 100%
2. **ระบบยืนยันตัวตน, เซสชัน, CSRF และล็อก 5 ครั้ง (P0):** กลไก Rate Limit, Session Invalidation, CSRF Token และ Brute-force Lock 15 นาที ทำงานสมบูรณ์
3. **การผูกบัญชี LINE และ Google OAuth (P0–P1):** ป้องกันการผูกผิดพลาด, รองรับรหัส 8 หลัก (`/link`), โทเค็นความปลอดภัย, และการตัดการเชื่อมต่อ Google Drive ใช้งานได้ทุกบทบาทที่มีสิทธิ์
4. **คลังความรู้ RAG และอัปโหลดพร้อมกัน (P1):** ป้องกัน Race condition ในการอัปโหลดไฟล์พร้อมกัน (`_META_LOCK`), การซ่อนไฟล์หมวดหมู่ส่วนตัวตามสิทธิ์ผู้ใช้, และระบบ Query Rewriting สำหรับคำถามติดตามทำงานถูกต้อง
5. **แชทบอท LINE OA (P1):** จัดลำดับค้นหาไฟล์ก่อนรายชื่อสมาชิก, กรองสิทธิ์ไฟล์ตามหมวดหมู่, ป้องกันการส่ง Markdown ตารางไปยัง LINE (แปลงเป็น Bullet Lists)
6. **หน้าตาและ UI บนหลายขนาดหน้าจอ (P2):** แก้ไขปัญหาคลาส `.hidden { display: none !important; }` ที่เคยทับคลาส Tailwind Responsive (`hidden md:flex`, `hidden sm:inline`) รวม 23 จุด ทำให้ปุ่มและเนื้อหาบนจอเดสก์ท็อปและแท็บเล็ตกลับมาแสดงผลถูกต้อง พร้อมผ่านการทดสอบบน Headless Chromium จริงผ่าน Playwright

---

## 2. ตารางรายการบั๊กและการแก้ไข (Bug Matrix)

| ID | หัวข้อ | ระดับ | สถานะ | อาการที่พบ (Actual) | ผลที่ควรเป็น (Expected) | การแก้ไขและไฟล์ที่เกี่ยวข้อง | เทสต์กันถอยหลัง (Regression Test) |
|---|---|---|---|---|---|---|---|
| **BUG-01** | SQLite Connection & WAL on Windows | **P0** | **ยืนยันและแก้แล้ว** | การเรียก `_get_conn()` ทุกครั้งรัน `PRAGMA journal_mode=WAL` โดยตรง หากไฟล์ถูกเข้าถึงพร้อมกันบน Windows/OneDrive จะเกิด `sqlite3.OperationalError: disk I/O error` และส่งผลให้ API ตอบ HTTP 500 | ไม่ทำให้การเชื่อมต่อล้มเหลว รองรับการตั้งค่า fallback อย่างนุ่มนวล | แก้ไข [`webai/db/connection.py`](file:///C:/Users/KC_Ketwilai/OneDrive/Desktop/orgchat-ai-main/orgchat-ai-main/webai/db/connection.py#L460-L470) ครอบ `try...except sqlite3.OperationalError` ในส่วน PRAGMA WAL, synchronous, cache_size | `tests/test_access_control_isolated.py` (ผ่าน 100%), `tests/test_org_admin_isolated.py` (ผ่าน 100%) |
| **BUG-02** | Responsive Utility Override (`.hidden !important`) | **P2** | **ยืนยันและแก้แล้ว** | ใน `style.css` และ `components.css` มีการเขียน `.hidden { display: none !important; }` ทำให้ element ที่ใช้ Tailwind breakpoint เช่น `hidden md:flex`, `hidden sm:inline`, `hidden lg:flex` รวม 23 จุดในหน้าจอคอมพิวเตอร์ถูกซ่อนถาวร ขณะเดียวกันหากยกเลิก `!important` ธรรมดา Element ที่มีคลาสขัดแย้งอาจรั่วมาแสดงบนมือถือ | ต้องซ่อนด้วย `!important` เฉพาะบนขนาดจอที่ระบุ (เช่น จอเล็กกว่า breakpoint) และปล่อยให้คลาส `sm:`, `md:`, `lg:` แสดงผลบนจอใหญ่ | กำหนด Media Queries คุมขนาดจออย่างเข้มงวด: `@media (max-width: 639.98px) { .hidden[class*="sm:"] { display: none !important; } }`, `@media (max-width: 767.98px) { .hidden[class*="md:"] { display: none !important; } }`, `@media (max-width: 1023.98px) { .hidden[class*="lg:"] { display: none !important; } }` ร่วมกับ `.hidden:not(...) { display: none !important; }` เพื่อให้ Element ฝั่งเดสก์ท็อปไม่รั่วบนมือถือแน่นอน | `tests/test_browser_suite.py` (Playwright Headless Chromium ผ่าน 5/5 ข้อ ยืนยันบนทั้ง 375px มือถือ, 768px แท็บเล็ต, และ 1360px เดสก์ท็อป) |
| **BUG-03** | Playwright Browser Fixture Disconnect | **P2** | **ยืนยันและแก้แล้ว** | ใน `tests/test_browser_suite.py` มีการใช้ `with sync_playwright() as p:` ภายใน generator fixture ส่งผลให้ subprocess pipe หลุดและเกิดข้อผิดพลาด `Connection closed while reading from the driver` | Browser instance ต้องคงอยู่ตลอดการรัน module fixture และปิดตัวอย่างปลอดภัยเมื่อจบการทดสอบ | ปรับปรุง [`tests/test_browser_suite.py`](file:///C:/Users/KC_Ketwilai/OneDrive/Desktop/orgchat-ai-main/orgchat-ai-main/webai/tests/test_browser_suite.py) เป็น `pw = sync_playwright().start()` และ `pw.stop()` ใน try/finally | `tests/test_browser_suite.py` (รันผ่านครบ 5 รายการ: login flow, responsive layout, theme toggle, XSS vector, media mocks) |
| **BUG-04** | Thai Greeting Word Stripping in Follow-up Query | **P2** | **ยืนยันและแก้แล้ว** | คำทักทายภาษาไทยที่มีคำลงท้ายสุภาพ เช่น "สวัสดีครับ", "สวัสดีค่ะ", "หวัดดีครับ" ไม่ถูกกรองออกจากประวัติบทสนทนา ส่งผลให้ `test_extract_recent_user_turns` ล้ม (ดึงข้อความทักทายติดไปเป็นบริบทคำค้นหา) | กรองเฉพาะประโยคคำถามจริงของผู้ใช้ โดยตัดคำทักทาย คำลงท้ายสุภาพ และข้อความตอบรับทั่วไปออก | สร้างฟังก์ชัน `is_greeting_or_noise(text)` ใน [`webai/rag_query.py`](file:///C:/Users/KC_Ketwilai/OneDrive/Desktop/orgchat-ai-main/orgchat-ai-main/webai/rag_query.py) ใช้ regex ตัดคำลงท้ายสุภาพ (`(?:ครับ\|ค่ะ\|คะ\|นะครับ\|นะคะ\|นะ\|ค้าบ\|จ้า\|จ้ะ\|คับ)`) พร้อมชุดคำทักทายเต็ม | `tests/test_rag_followup.py` (ผ่าน 10/10 ข้อ รวมถึง `test_extract_recent_user_turns` ทั้งเคส "สวัสดีครับ", "หวัดดีค่ะ") |
| **BUG-05** | Ambiguous File Search Fallback in LINE Bot | **P1** | **ยืนยันและแก้แล้ว** | เมื่อผู้ใช้พิมพ์คำสั่งค้นหาที่ไม่ได้ระบุคำว่า "ไฟล์" เจาะจง (เช่น "ค้นหา ซิ่งๆๆ") แล้วไม่มีไฟล์ตรง บอทตอบกลับด้วยข้อผิดพลาดว่า "ยังไม่พบไฟล์" แทนที่จะส่งต่อให้โมเดล AI ตอบคำถาม | หากเป็นการค้นหาแบบระบุเจาะจง ("ค้นหาไฟล์...") จึงแจ้งไม่พบไฟล์ แต่หากเป็นการค้นหาทั่วไป ("ค้นหา...") ให้ส่งต่อให้ AI/RAG ตอบคำถาม | ปรับปรุงเงื่อนไขใน [`webai/routes/line_webhook.py`](file:///C:/Users/KC_Ketwilai/OneDrive/Desktop/orgchat-ai-main/orgchat-ai-main/webai/routes/line_webhook.py#L3095-L3108) แยก `_is_explicit_file_query` และส่งต่อ fallback ให้ AI pipeline | `tests/test_line_file_search_isolated.py` (ผ่าน 100%) |

---

## 3. ผลการรันชุดทดสอบแยกตามหัวข้อ (Test Verification Results)

การทดสอบทุกชุดดำเนินการผ่านโพรเซสแยกด้วย `python tools/run_tests.py` บนฐานข้อมูลจำลอง (Temp SQLite) โดยไม่มีการติดต่อบริการจริงภายนอก:

### หมวดที่ 1: สิทธิ์และความปลอดภัยข้ามองค์กร (RBAC & Multi-Tenant)
- `tests/test_access_control_isolated.py` — **✅ ผ่าน (PASS)** (ทดสอบ 30+ endpoints ป้องกัน IDOR ข้ามองค์กร)
- `tests/test_org_admin_isolated.py` — **✅ ผ่าน (PASS)** (สิทธิ์ Admin vs Member vs Owner)
- `tests/test_rbac.py` — **✅ ผ่าน (5 passed)**
- `tests/test_p0_security.py` — **✅ ผ่าน (5 passed)**
- `tests/test_p1_security.py` — **✅ ผ่าน (12 passed)**

### หมวดที่ 2: การยืนยันตัวตน เซสชัน CSRF และการผูกบัญชี (Auth & Binding)
- `tests/test_auth.py` — **✅ ผ่าน (3 passed)**
- `tests/test_u0_auth_flow.py` — **✅ ผ่าน (6 passed)**
- `tests/test_line_link_code_isolated.py` — **✅ ผ่าน (1 passed)** (รหัส 8 หลัก, อายุ 10 นาที, ป้องกัน brute force)
- `tests/test_line_link_isolated.py` — **✅ ผ่าน (1 passed)**
- `tests/test_google_oauth_isolated.py` — **✅ ผ่าน (1 passed)**
- `tests/test_google_disconnect_isolated.py` — **✅ ผ่าน (1 passed)**

### หมวดที่ 3: คลังความรู้ RAG และเวกเตอร์ (Knowledge Base & Ingestion)
- `tests/test_kb_concurrent_ingest_isolated.py` — **✅ ผ่าน (1 passed)** (ทดสอบอัปโหลดไฟล์พร้อมกันหลายไฟล์)
- `tests/test_kb_permissions.py` — **✅ ผ่าน (5 passed)** (สิทธิ์การเข้าถึงไฟล์ตามหมวดหมู่)
- `tests/test_kb_safety.py` — **✅ ผ่าน (1 passed)**
- `tests/test_chroma_store.py` — **✅ ผ่าน (46 passed)**
- `tests/test_rag.py` — **✅ ผ่าน**
- `tests/test_rag_followup.py` — **✅ ผ่าน (10 passed)**
- `tests/test_citation_filter.py` — **✅ ผ่าน (10 passed)**

### หมวดที่ 4: แชทบอท LINE OA
- `tests/test_line_file_search_isolated.py` — **✅ ผ่าน (1 passed)**
- `tests/test_line_inbox_isolated.py` — **✅ ผ่าน (1 passed)**
- `tests/test_line_plain_text.py` — **✅ ผ่าน (3 passed)**

### หมวดที่ 5: แชทเว็บ ความปลอดภัย และการสื่อสาร
- `tests/test_chat_send_isolated.py` — **✅ ผ่าน (1 passed)**
- `tests/test_calls_isolated.py` — **✅ ผ่าน (1 passed)**
- `tests/test_presence_isolated.py` — **✅ ผ่าน (1 passed)**
- `tests/test_xss_audit.py` — **✅ ผ่าน (2 passed)**
- `tests/test_sanitize.py` — **✅ ผ่าน (10 passed)**

### หมวดที่ 6: หน้าเว็บ UI เบราว์เซอร์จริง และการแสดงผล
- `tests/test_browser_suite.py` — **✅ ผ่าน (5 passed)** (Playwright Headless Chromium)
- `tests/test_calendar_redesign.py` — **✅ ผ่าน (4 passed)**
- `tests/test_font_preferences.py` — **✅ ผ่าน (8 passed)**

---

## 4. สิ่งที่ระบบจำลองไม่ได้และต้องให้ผู้ใช้ทดสอบจริง (Real System Testing)

เนื่องจากชุดทดสอบอัตโนมัติห้ามติดต่อภายนอก (Mock API) เพื่อป้องกันค่าใช้จ่ายและข้อมูลรั่วไหล รายการต่อไปนี้ขอแนะนำให้ผู้ใช้ทดสอบบนระบบจริง:

1. **การตอบคำถามของ AI จริง (Gemini / Groq Live API):**
   - ถาม: *"ขอเบอร์ติดต่อบริษัทหน่อย"* (ดูว่าบอตระบุอีเมลและ LINE OA ที่มีอยู่จริงในเอกสาร และไม่แต่งเลขเบอร์โทรตัวอย่าง)
   - ถามต่อเนื่องทันที: *"ทำไมจะไม่มีไปเช็คดู"* (ดูว่าระบบ Query Rewriting ดึงเอกสารบริษัทขึ้นมาตอบอย่างสุภาพ)
   - ถามเรื่องทั่วไปที่มีบริบทสืบเนื่อง: *"บริษัทก่อตั้งปีไหน"* ต่อด้วย *"แล้วใครเป็นผู้ก่อตั้ง"*
2. **LINE Messaging API บนอุปกรณ์จริง:**
   - พิมพ์ `"ค้นหา รายชื่อ"` ใน LINE OA จริง: ยืนยันว่าได้ Flex Carousel รายการไฟล์พร้อมปุ่มดาวน์โหลด/เปิดดู
   - พิมพ์ `"รายชื่อพนักงาน"`: ยืนยันว่าได้รายชื่อสมาชิกในองค์กรตามปกติ
3. **Google Sign-In & Google Drive Live Sync:**
   - ทดสอบล็อกอินด้วยปุ่ม Google Sign-In ในหน้าเว็บ
   - ทดสอบเชื่อมต่อ Google Drive ในระดับองค์กร (สำหรับผู้ใช้ที่เป็น Test Users ใน Google Cloud Console)

---

## 5. สิ่งที่ผู้ดูแลระบบต้องดำเนินการ (Action Items for Admin)

1. **รีสตาร์ตเซิร์ฟเวอร์หลัก (Restart Web Server):**
   - มีการแก้ไขไฟล์ Python ฝั่งเซิร์ฟเวอร์ (`db/connection.py`, `rag_query.py`, `rag_engine.py`, `routes/chat.py`, `routes/line_webhook.py`) กรุณารีสตาร์ต `app_server.py` เพื่อให้โค้ดใหม่มีผลทันที
2. **ล้างแคชเบราว์เซอร์ (Hard Refresh):**
   - เนื่องจากมีการปรับปรุง CSS (`style.css`, `components.css`) เพื่อแก้ไข Responsive Breakpoints และเครื่องมือได้อัปเดตเวอร์ชัน Asset ใน `index.html` แล้ว ให้ผู้ใช้กด **Ctrl + F5** (หรือ Cmd + Shift + R บน Mac) เพื่อโหลดไฟล์สไตล์ใหม่
3. **ตรวจสอบไฟล์ต้นฉบับในคลังความรู้:**
   - แนะนำให้รันคำสั่ง `python tools/scan_kb_placeholders.py` เพื่อตรวจดูไฟล์เอกสารที่มีเบอร์โทรหรืออีเมลตัวอย่างค้างอยู่ (เช่น `02-XXX-XXXX` ใน `ประวัติบริษัท_Chuenchob.txt`) เพื่อนำไฟล์จริงมาอัปเดตแทนที่

---

## 6. ภาคผนวก: ผลการตรวจล่าบั๊กอย่างเป็นระบบ (13 หมวดหมู่ — รอบที่ 2)

สรุปผลการรันจริงตามแผน `PLAN_BUG_HUNT_PATTERNS.md` (รายละเอียดฉบับเต็มอยู่ที่ [`docs/BUG_HUNT_FINDINGS.md`](file:///c:/Users/KC_Ketwilai/OneDrive/Desktop/orgchat-ai-main/orgchat-ai-main/webai/docs/BUG_HUNT_FINDINGS.md)):

| หมวด | รายการตรวจสอบและแก้ไข | ผลรัน Pytest จริง |
|---|---|---|
| ประเภท 6: Undefined names & DB methods | เพิ่ม `get_organization_by_id`, `get_organization_profile`, `kanban_get_or_create_board`, `get_attendance_records` | `tests/test_missing_attributes.py`: `2 passed, 1 warning in 1.00s` |
| ประเภท 4: Popup "ส่งไม่สำเร็จ internal_error" | แก้ไขสาเหตุรากเหง้าของปุ่ม Morning Brief + แมปข้อความไทย | `tests/test_briefing_and_error_handling.py`: `2 passed, 2 warnings in 10.97s` |
| ประเภท 12: Data Consistency Tool | พัฒนาสคริปต์ตรวจความสอดคล้อง DB/KB แบบ Read-only สำหรับผู้ใช้ | `tests/test_data_consistency_tool.py`: `1 passed, 1 warning in 0.21s` |
| ประเภท 7: Restart Recovery | แก้ปัญหาไฟล์ค้างสถานะ `processing` และทำความสะอาด chunk กำพร้า | `tests/test_scenario_e_restart_recovery.py`: `1 passed, 2 warnings in 22.81s` |
| ประเภท 11: Security & Cross-Tenant | ป้องกัน IDOR ข้ามองค์กร, Path Traversal, CF Tunnel Client IP extraction | `tests/test_scenario_sec_deep_audit.py`: `5 passed, 2 warnings in 13.43s` |
| ประเภท 1–3: Identity & Guards | ป้องกัน fallback ค่าเริ่มต้นเมื่อไม่พบผู้ใช้, แก้ `user_exists`, ปฏิเสธ Auto-provision บัญชีเปล่าจาก LINE, ตรวจสิทธิ์ Superadmin | `tests/test_identity_and_guards.py`: `4 passed, 2 warnings in 21.15s` |
| ประเภท 8: Thai & Special Characters | รองรับชื่อไฟล์ไทย, อักขระพิเศษ, LINE flex percent-encoding | `tests/test_scenario_f_thai_special_chars.py`: `4 passed, 3 warnings in 12.23s` |
| ประเภท 11: Access Control Matrix | สิทธิ์การเข้าถึงไฟล์ เอกสารลับ แผนก และการจัดการองค์กร 45 จุด | `tests/test_access_control_isolated.py`: `1 passed, 1 warning in 14.98s` |
| ประเภท 7: Concurrent Ingest | อัปโหลดไฟล์พร้อมกันใต้คิวและ Semaphore ไม่กินแรมเกินพิกัด | `tests/test_kb_concurrent_ingest_isolated.py`: `1 passed, 1 warning in 8.05s` |
| ประเภท 10: Citation Filter | กรองแหล่งอ้างอิงให้ตรงกับเนื้อหาที่ AI ใช้ตอบจริง ไม่แนบไฟล์มั่ว | `tests/test_citation_filter.py`: `10 passed, 1 warning in 0.10s` |
| ประเภท 10: RAG Follow-up & Greeting | ตัด "สวัสดีครับ" ออกจาก history และขยายคำค้นเมื่อถามต่อเนื่อง | `tests/test_rag_followup.py`: `10 passed, 1 warning in 4.06s` |
| ประเภท 9: Responsive CSS Display | ตรวจสอบ getComputedStyle บนเบราว์เซอร์จริง 6 ขนาดหน้าจอ | `tools/test_computed_hidden_breakpoints.py`: All 30 checks PASSED |
| User Journey (Scenario A) | เดินตามเส้นทางผู้ใช้ใหม่ตั้งแต่ศูนย์ สร้างองค์กร อัปโหลดไฟล์ จนถึงแชต AI | `tests/isolated/scenario_a_user_journey_scenarios.py`: ALL PASSED |


