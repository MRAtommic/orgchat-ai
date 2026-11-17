# รายงานผลการล่าบั๊กแบบเป็นระบบ (Bug Hunt Findings Report)

เอกสารสรุปผลการค้นหาและแก้ไขบั๊กทั้ง 13 ประเภทตามแผนใน `webai/docs/PLAN_BUG_HUNT_PATTERNS.md` และการทดสอบสถานการณ์ผู้ใช้จริง

---

## 1. ตารางรายการบั๊กที่พบและสถานะการแก้ไข (13 หมวดหมู่)

| หมวด | รหัส | ความรุนแรง | ไฟล์และบรรทัด | อาการที่พบ / พฤติกรรมเดิม | ผลกระทบ | การแก้ไข | สถานะ |
|---|---|---|---|---|---|---|---|
| **ประเภท 1: Silent Fallback Identity** | BUG-01 | P1 | `db/settings.py:203` | `get_user_setting()` คืน dict ค่าเริ่มต้นเสมอแม้ไม่มีผู้ใช้ในระบบ | ทำให้ฟังก์ชันเช็ค "มีผู้ใช้ไหม" ประเมินเป็นจริงตลอดกาล, เสี่ยงสร้าง ghost user | เพิ่มพารามิเตอร์ `default=True/False` และสร้าง `database.user_exists(username)` เช็คจริงใน DB | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 1: Silent Fallback Identity** | BUG-02 | P1 | `routes/admin.py:4405` | `superadmin_impersonate()` สวมรอยบัญชีที่ไม่มีอยู่จริงได้สำเร็จ | SuperAdmin สวมรอย username ผี บัญชีว่างเปล่าค้างในระบบ | เปลี่ยนไปใช้ `get_user_setting(username, default=False)` คืน 404 เมื่อไม่พบบัญชี | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 1: Silent Fallback Identity** | BUG-03 | P1 | `routes/admin.py:3220` | `api_org_add_member` เช็คผู้ใช้ด้วย `bool(existing.get("custom_password"))` | ผู้ใช้ที่สมัครผ่าน Google/LINE SSO หรือไม่มีรหัสผ่านเดิม ถูกมองว่า "ไม่มีผู้ใช้" แล้วบังคับให้กรอกรหัสผ่านใหม่ซ้ำ | เปลี่ยนไปเช็คด้วย `database.user_exists(username)` ครอบคลุมทุกช่องทาง | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 2: Identity Mismatch & Ghost Accounts** | BUG-04 | P0 | `routes/auth.py:4464`<br>`db/chat.py:814` | 1) ผู้ใช้ LINE ที่ยังไม่ผูกบัญชี ถูก Auto-provision บัญชีใหม่ไร้องค์กร (Empty account)<br>2) สับสนระหว่าง LINE Bot ID กับ LINE Login ID | ผู้ใช้ล็อกอินแล้วได้บัญชีว่างเปล่า หรือผูกฝั่งหนึ่งแล้วอีกฝั่งจำไม่ได้ | 1) ยกเลิก Auto-provisioning โดยเปลี่ยนเป็นคืน 403 พร้อมข้อความแนะนำให้ล็อกอินด้วยวิธีเดิมแล้วกดเชื่อมต่อในหน้าตั้งค่าบัญชี<br>2) ปรับ `link_line_user(..., is_login=True)` แยกเก็บ `line_login_id` และ `line_user_id` ให้ค้นพบทั้งคู่ | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 3: Guard Skipping** | BUG-05 | P1 | `routes/shared.py:535` | `is_admin()` เช็คเฉพาะ `session.get("role") == "admin"` | SuperAdmin ถูกปฏิเสธสิทธิ์ (403) ในฟังก์ชันทั่วไปของแอดมิน | แก้ให้ครอบคลุม `role in ("admin", "superadmin")` | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 3: Guard Skipping** | BUG-06 | P1 | `routes/shared.py:493` | `can_edit_knowledge_base()` และ `can_view_knowledge_base()` ไม่เช็ค `is_org_admin` | ผู้สร้าง/แอดมินองค์กรใหม่ที่ไม่มี global admin role ถูกบล็อก 403 อัปโหลดไฟล์ไม่ได้ | เพิ่มการตรวจสอบ `database.is_org_admin(org_id, user)` | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 3: Guard Skipping** | BUG-06b | P1 | `routes/auth.py:4335` | ผูก LINE Login ขณะล็อกอินอยู่แล้ว เกิด early return ข้ามการบันทึก | ผู้ใช้กดเชื่อม LINE ในหน้าตั้งค่าแล้วไม่ถูกบันทึกลง DB | บันทึก `database.link_line_user(username, line_user_id, is_login=True)` ก่อนส่งหน้าแจ้งผลสำเร็จ | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 4: Swallowed/Opaque Errors** | BUG-07 | P0 | `routes/admin.py:3842`<br>`static/js/chat.js:18834` | กดปุ่ม "ทดสอบ Morning Brief" ขึ้น Popup "ส่งไม่สำเร็จ internal_error" | ผู้ใช้เห็น popup ข้อผิดพลาดภาษาอังกฤษที่ไร้ประโยชน์ ไม่รู้สาเหตุ | เพิ่ม alias `database.get_organization_by_id`, ครอบ try/except ส่งภาษาไทยชัดเจน, แปลงรหัส error ใน frontend | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 4: Swallowed/Opaque Errors** | BUG-08 | P1 | `app_server.py:786` | Global 500 error handler ส่ง `error: "internal_error"` | ฟรอนต์เอนด์รุ่นเก่าแสดงคำว่า "internal_error" บนกล่องแจ้งเตือน | ปรับส่ง `error: msg` (ภาษาไทยสุภาพ) พร้อม `error_code: "internal_error"` | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 5: Contract Drift** | BUG-09 | P2 | `static/js/chat.js:18834` | API คืน `error` หรือ `message` ไม่ตรงกับที่ UI คาดหวัง | หน้าต่างแจ้งเตือนแสดงข้อความไม่ครบ | แมป fallback ระหว่าง `data.message` และ `data.error` ใน frontend | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 6: Undefined Names / Schema Drift** | BUG-10 | P0 | `db/orgs.py`<br>`db/social.py`<br>`db/leave.py` | ขาดฟังก์ชันใน `database.*`: `get_organization_by_id`, `get_organization_profile`, `kanban_get_or_create_board`, `get_attendance_records` | เกิด `AttributeError` พังกลางคันเมื่อผู้ใช้เปิดใช้งานฟีเจอร์ดังกล่าว | เพิ่ม alias และฟังก์ชัน shim ให้ครบถ้วนตรงตามสเปก | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 7: Race Conditions & Stuck State** | BUG-11 | P0 | `rag_engine.py:387`<br>`app_server.py:1201` | รีสตาร์ตเซิร์ฟเวอร์ขณะประมวลผลไฟล์ ทำให้ไฟล์ค้างสถานะ `processing` | ผู้ใช้ไม่สามารถลบ อัปโหลดซ้ำ หรือใช้งานไฟล์นั้นได้ | เรียก `cleanup_stale_processing(max_age_minutes=0)` ตอนบูตแอป เคลียร์ไฟล์ค้างเป็น error และลบเศษ chunk กำพร้า | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 8: Encoding & Thai Special Chars** | BUG-12 | P1 | `routes/file_upload.py:136`<br>`routes/line_webhook.py:3039` | ชื่อไฟล์ภาษาไทย อักขระพิเศษ สัญลักษณ์ และ emoji ในชื่อไฟล์และลิงก์ดาวน์โหลด LINE | ลิงก์บน LINE Flex Message ใช้งานไม่ได้หากมีอักขระไทยที่ไม่ได้ percent-encode | ทำ `_sanitize_line_uris()` เข้ารหัส URL เป็น ASCII สมบูรณ์ และรองรับ RFC 5987 ในการดาวน์โหลด | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 9: Global CSS Bleed** | BUG-13 | P1 | `static/components.css`<br>`static/css/ui_harmony.css` | `.hidden { display: none !important }` ทับ breakpoint Tailwind บนหน้าจอขนาดต่างๆ | ปุ่ม เมนู และแถบอ้างอิงแหล่งที่มาหายบนหน้าจอมือถือ/แท็บเล็ต (~23 จุด) | ปรับแก้ `.hidden` ใน `components.css` ให้ไม่กระทบ breakpoint, ใช้ `.src-wrap`/`.src-label` และตรวจ computed display ผ่าน Playwright ทั้ง 6 ขนาดหน้าจอ | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 10: LLM Behavior & Prompt Rules** | BUG-14 | P2 | `rag_query.py:112` | ประวัติการสนทนาเก็บคำทักทาย "สวัสดีครับ" ทำให้ขัดขวางการ rewrite follow-up search query | คำถามต่อเนื่อง (follow-up) ค้นหาเอกสารไม่ตรงประเด็น | เพิ่มตัวกรองตัด greeting turns ออกจาก history ก่อนประกอบคำค้น | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 11: Authz & Department Visibility** | BUG-15 | P0 | `db/users.py:get_categories`<br>`routes/shared.py:493` | 1) `get_categories` กรอง SQL ไม่ครอบคลุม `kb_category_departments` ทำให้สมาชิกแผนกมองไม่เห็นหมวดของตนเอง<br>2) Org Admin ถูกบล็อกอัปโหลดไฟล์ | สมาชิกแผนกไม่เห็นเอกสารที่ตนมีสิทธิ์ และแอดมินองค์กรใหม่จัดการคลังความรู้ไม่ได้ | 1) รวมเงื่อนไขแผนกและองค์กรใน SQL subquery อย่างถูกต้อง<br>2) ตรวจสอบสิทธิ์ระดับแอดมินองค์กรอย่างเคร่งครัด | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 12: Data Consistency Tool** | BUG-16 | P2 | `tools/check_data_consistency.py` | ข้อมูลจริงของผู้ใช้มีความไม่สม่ำเสมอสะสมจากการอัปเกรด (ผู้ใช้ไร้องค์กร, chunks ไม่ตรง meta) | เกิด error ลึกลับเฉพาะบนโปรดักชัน | พัฒนาเครื่องมือตรวจสอบแบบ Read-Only ให้ผู้ใช้รันตรวจ DB จริงได้เองอย่างปลอดภัย | **แก้แล้ว-ยืนยันแล้ว** |
| **ประเภท 13: Tunnel & Proxy IP Extraction** | BUG-17 | P1 | `routes/shared.py:get_client_ip` | การใช้งานผ่าน Cloudflare Tunnel ทำให้ audit log และ rate limit ได้รับ IP ของ proxy ซ้ำกัน | ผู้ใช้โดน rate limit รวมกัน หรือบันทึก IP ใน log ผิดพลาด | เพิ่มระบบอ่าน `CF-Connecting-IP` และตรวจสอบ loopback proxy IP อย่างปลอดภัย | **แก้แล้ว-ยืนยันแล้ว** |

---

## 2. ตารางสรุปผลการรัน Pytest จริงทุกชุดทดสอบ (Real Pytest Execution Table)

> **กฎเหล็ก**: ทุกชุดทดสอบด้านล่างผ่านการรันจริงในระบบและบันทึกผลลัพธ์บรรทัดสรุปของ pytest ตรงตามความเป็นจริง

| ไฟล์ชุดทดสอบ | บรรทัดสรุปผลลัพธ์ (Pytest Output) | เวลาที่ใช้ | วัตถุประสงค์การทดสอบ |
|---|---|---|---|
| `tests/test_missing_attributes.py` | `2 passed, 1 warning in 1.00s` | 1.00s | ตรวจสอบ Attribute และฟังก์ชัน DB ที่เคยขาดหาย (ประเภท 6) |
| `tests/test_briefing_and_error_handling.py` | `2 passed, 2 warnings in 10.97s` | 10.97s | ตรวจสอบปุ่ม Morning Brief และ Error handling ภาษาไทย (ประเภท 4) |
| `tests/test_data_consistency_tool.py` | `1 passed, 1 warning in 0.21s` | 0.21s | ตรวจสอบเครื่องมือ Audit Data Consistency (ประเภท 12) |
| `tests/test_scenario_b_concurrent_roles.py` | `1 passed, 2 warnings in 13.97s` | 13.97s | สิทธิ์และการมองเห็นเอกสารตามแผนกและบทบาทพร้อมกัน (Scenario B / ประเภท 11) |
| `tests/test_scenario_e_restart_recovery.py` | `1 passed, 2 warnings in 22.81s` | 22.81s | การกู้คืนสถานะไฟล์ค้าง processing หลัง Restart เซิร์ฟเวอร์ (Scenario E / ประเภท 7) |
| `tests/test_scenario_sec_deep_audit.py` | `5 passed, 2 warnings in 13.43s` | 13.43s | ป้องกัน IDOR ข้ามองค์กร, Path Traversal, CF Tunnel IP (ประเภท 11 & 13) |
| `tests/test_identity_and_guards.py` | `4 passed, 2 warnings in 21.15s` | 21.15s | ป้องกัน Silent Fallback, ตรวจสอบผู้ใช้จริง, ปฏิเสธ Auto-provision บัญชีเปล่าจาก LINE (ประเภท 1–3) |
| `tests/test_scenario_f_thai_special_chars.py` | `4 passed, 3 warnings in 12.23s` | 12.23s | รองรับชื่อไฟล์ไทย, อักขระพิเศษ, LINE flex URL encoding (Scenario F / ประเภท 8) |
| `tests/test_access_control_isolated.py` | `1 passed, 1 warning in 14.98s` | 14.98s | ตรวจสอบสิทธิ์และการเข้าถึงเอกสารและฟังก์ชันระบบ 45 รายการ (ประเภท 11) |
| `tests/test_kb_concurrent_ingest_isolated.py` | `1 passed, 1 warning in 8.05s` | 8.05s | ทดสอบการอัปโหลดไฟล์หลายไฟล์พร้อมกันแบบ Concurrency (ประเภท 7) |
| `tests/test_citation_filter.py` | `10 passed, 1 warning in 0.10s` | 0.10s | การกรองและคัดเลือกแหล่งอ้างอิงให้ตรงกับคำตอบ AI จริง (ประเภท 10) |
| `tests/test_rag_followup.py` | `10 passed, 1 warning in 4.06s` | 4.06s | ตัดคำทักทายออกจากประวัติและการ rewrite คำถามต่อเนื่อง (ประเภท 10) |
| `tools/test_computed_hidden_breakpoints.py` | `Playwright: All 30 checks PASSED` | ~15s | ทดสอบ getComputedStyle บนเบราว์เซอร์จริง 6 ขนาดหน้าจอ (ประเภท 9) |
| `tests/isolated/scenario_a_user_journey_scenarios.py` | `ALL PASSED (RC: 0)` | ~18s | เดินตามเส้นทางผู้ใช้ใหม่ตั้งแต่สร้างองค์กร อัปโหลดไฟล์ จนถึงคุยแชต AI |

---

## 3. รายการที่ต้องทดสอบกับระบบภายนอกจริง (External Services Checklist)

สำหรับฟังก์ชันที่ต้องเชื่อมต่อบริการภายนอกที่มี Live Secret/Credential ซึ่งระบบทดสอบใช้ mock/sandbox ไว้ ให้ผู้ดูแลระบบทดสอบตามขั้นตอนดังนี้:

1. **LINE Official Account (Webhook & Messaging API)**:
   - ส่งข้อความทักทาย เช่น `"สวัสดี"` หรือถามข้อมูลสินค้าใน LINE Chatbot เพื่อดูว่าตอบกลับถูกต้องและมีปุ่มการ์ด Flex ให้ดาวน์โหลดไฟล์ (ที่มี URL ภาษาไทยเข้ารหัสถูกต้อง)
   - ทดสอบกดปุ่มเชื่อมต่อบัญชีใน LINE Bot และเปิดผ่าน LINE Login ในมือถือ
2. **Google Drive & Sheets Integration**:
   - ไปที่เมนู "จัดการองค์กร" > "เชื่อมต่อ Google Drive/Workspace"
   - ทดสอบ Sync ไฟล์จาก Google Drive และเปิดดูในคลังความรู้
   - ตรวจสอบว่าหน้าจอแสดงสถานะ "เชื่อมต่อแล้ว" โดยไม่มี Toast ข้อผิดพลาดสีแดงค้าง
3. **Morning Briefing Broadcast**:
   - ไปที่หน้า Admin แดชบอร์ด > กดปุ่ม "ทดสอบ Morning Brief"
   - สังเกตว่าจะไม่เกิด Popup "ส่งไม่สำเร็จ internal_error" อีกต่อไป โดยระบบจะแสดงข้อความภาษาไทยแจ้งเตือนผลการส่งชัดเจน

---

## 4. สิ่งที่ผู้ใช้/ผู้ดูแลระบบต้องทำเมื่ออัปเดตระบบ (Admin Action Checklist)

- [ ] **Restart Server**: สั่งรีสตาร์ตเซิร์ฟเวอร์หลัก 1 ครั้ง เพื่อให้ `rag_engine.cleanup_stale_processing(max_age_minutes=0)` ทำงานกวาดไฟล์ตกค้างทันที
- [ ] **ล้างแคชเบราว์เซอร์ (Ctrl + F5)**: แนะนำให้ผู้ใช้งานกด `Ctrl + F5` บนคอมพิวเตอร์ หรือล้างแคชในมือถือ เพื่อโหลดไฟล์ `chat.js` และ `style.css` เวอร์ชันล่าสุด
- [ ] **รันเครื่องมือตรวจสอบความสอดคล้องของฐานข้อมูล**:
  ```bash
  python webai/tools/check_data_consistency.py
  ```
  เพื่อดูรายงานภาพรวมของข้อมูลผู้ใช้ บัญชีซ้ำ หรือไฟล์ meta ที่อาจค้างอยู่จากเวอร์ชันเก่า (ทำงานแบบ Read-Only ไม่กระทบข้อมูลจริง)

