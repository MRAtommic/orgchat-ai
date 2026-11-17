# แผนงานสำหรับ Antigravity: บันทึกฟอนต์ที่ผู้ใช้เลือก "ต่อบัญชี" ให้กลับมาเหมือนเดิมทุกครั้งที่เข้าใหม่

## เป้าหมาย
ผู้ใช้แต่ละคนเลือกฟอนต์ (และขนาดตัวอักษร/สีหลัก) แล้วระบบจำไว้ที่เซิร์ฟเวอร์ผูกกับบัญชี
เข้าใหม่ ล็อกอินเครื่องอื่น หรือล้างเบราว์เซอร์ ก็ยังได้ฟอนต์ล่าสุดที่เลือกไว้

## สถานะปัจจุบัน (ตรวจจากโค้ดแล้ว)
- `static/js/appearance.js` เก็บค่าใน **localStorage** เท่านั้น: `custom_font_family`, `custom_font_size`, `custom_accent_color`
- ปัญหา: ค่าผูกกับ "เบราว์เซอร์" ไม่ใช่ "บัญชี"
  - ล็อกอินจากเครื่อง/เบราว์เซอร์อื่น = กลับเป็น Sarabun
  - ล้างข้อมูลเบราว์เซอร์ = หาย
  - คนสองคนใช้เครื่องเดียวกัน = ใช้ฟอนต์ร่วมกัน
- ฟังก์ชันที่เกี่ยวข้อง: `initCustomUISettings()`, `setCustomFont()`, `setCustomFontSize()`, `setCustomAccent()`, `resetCustomUISettings()`
- ตาราง `user_settings` อยู่ใน `db/schema.py` (~บรรทัด 544) มีรูปแบบ migration แบบ `ALTER TABLE ... ADD COLUMN` อยู่แล้ว
- `/api/me` (`routes/auth.py` ~2024) คืนข้อมูลผู้ใช้ตอนเปิดแอป

## การออกแบบ
เก็บที่เซิร์ฟเวอร์เป็นหลัก ใช้ localStorage เป็นแคชกันกะพริบ

1. **DB**: เพิ่มคอลัมน์ใน `user_settings` (migration แบบ ADD COLUMN ใน try/except เหมือนที่มีอยู่)
   - `ui_font TEXT DEFAULT NULL`
   - `ui_font_size TEXT DEFAULT NULL`
   - `ui_accent TEXT DEFAULT NULL`
   - (หรือคอลัมน์เดียว `ui_prefs TEXT` เก็บ JSON — เลือกอย่างใดอย่างหนึ่ง แนะนำ 3 คอลัมน์เพราะตรวจค่าง่ายกว่า)
2. **Backend** (`db/users.py` หรือ `db/settings.py` + route ใน `routes/auth.py`):
   - `get_ui_prefs(username)` / `set_ui_prefs(username, font=None, size=None, accent=None)`
   - `POST /api/profile/ui-prefs` (ต้องล็อกอิน + ผ่าน CSRF เหมือน route อื่น)
   - **ตรวจค่าแบบ allowlist ฝั่งเซิร์ฟเวอร์**: font ต้องอยู่ในรายชื่อเดียวกับ `FONT_MAP`, size ∈ {small, normal, large, xl}, accent ต้องอยู่ในรายชื่อสีที่มี ค่าอื่น = 400 (กัน XSS/ขยะ)
   - `/api/me` คืน `ui_prefs: {font, size, accent}` เพิ่ม
3. **Frontend** (`static/js/appearance.js`):
   - ตอนโหลด: ใช้ค่าจาก localStorage ทันที (กันกะพริบ) แล้วเมื่อ `/api/me` ตอบกลับ ให้ **ค่าจากเซิร์ฟเวอร์ชนะ** และอัปเดต localStorage
   - ตอนผู้ใช้เลือก: apply ทันที → เขียน localStorage → ส่ง `POST /api/profile/ui-prefs` แบบ debounce ~500 ms (เลือกรัวๆ ไม่ยิงทุกคลิก) ถ้าส่งไม่สำเร็จ ไม่ต้องเด้ง error ใหญ่ แค่ลองใหม่ครั้งถัดไป
   - ปุ่มรีเซ็ต: ส่งค่าเริ่มต้นไปเซิร์ฟเวอร์ด้วย (หรือส่ง null เพื่อลบ)
   - ใช้ wrapper `apiFetch` ที่มีอยู่ (ใส่ CSRF ให้แล้ว) อย่าเขียน fetch เอง
   - **ผู้ใช้ที่ยังไม่เคยเลือก** (`null` จากเซิร์ฟเวอร์) แต่มีค่าใน localStorage: ส่งค่าใน localStorage ขึ้นเซิร์ฟเวอร์ 1 ครั้ง (migrate ให้ผู้ใช้เดิมไม่ต้องเลือกใหม่)
4. **กันกะพริบฟอนต์ (FOUC)**: ใส่สคริปต์เล็กๆ ใน `<head>` ของ `templates/index.html` ที่อ่าน localStorage แล้วตั้ง `--user-font-family` ก่อนหน้าจอวาดภาพ (ถ้ายังไม่ทำ) — ทำเฉพาะถ้าเห็นว่ากะพริบจริง
5. **ล็อกเอาต์/สลับบัญชีบนเครื่องเดียว**: ตอน logout ให้ล้าง `custom_*` ใน localStorage หรือผูกคีย์กับ username (เช่น `custom_font_family:<user>`) เพื่อไม่ให้ฟอนต์ของคนก่อนหน้าโผล่ให้คนถัดไป — **แนะนำล้างตอน logout + ตอนล็อกอินใช้ค่าจากเซิร์ฟเวอร์**

## ไฟล์ที่จะแตะ
- `db/schema.py` (migration)
- `db/users.py` หรือ `db/settings.py` (get/set)
- `routes/auth.py` (route ใหม่ + เพิ่มใน `/api/me`)
- `static/js/appearance.js` (ซิงก์กับเซิร์ฟเวอร์)
- `templates/index.html` (เพิ่มเลขเวอร์ชันที่ `?v=` ของ appearance.js ให้เบราว์เซอร์โหลดใหม่)
- `tests/` เพิ่มเทสต์ใหม่

## ข้อควรระวัง
- ห้ามอ่าน/แก้ `webai/.env` และห้ามทดสอบกับ `chat_history.db` จริง ใช้ DB ชั่วคราว (ดูตัวอย่างใน `tests/isolated/*_scenarios.py`)
- ห้าม push ขึ้น git
- ต้อง escape/ตรวจค่าก่อนเอาไปใส่ใน CSS (ใช้ allowlist เท่านั้น ห้ามเอาสตริงจากผู้ใช้ไปต่อเป็น `font-family` ตรงๆ)
- ผู้ใช้ต้องรีสตาร์ตเซิร์ฟเวอร์จริงหลังแก้ Python

## เกณฑ์ที่ถือว่าเสร็จ (ต้องทดสอบจริง)
1. A เลือก Kanit → ปิดเบราว์เซอร์ → เปิดใหม่ = ยังเป็น Kanit
2. A ล็อกอินจากเบราว์เซอร์อื่น/โหมดไม่ระบุตัวตน = ได้ Kanit
3. B (บัญชีอื่น) เลือก Mitr = A ยังเป็น Kanit ไม่ปนกัน
4. ส่งค่าที่ไม่อยู่ใน allowlist (เช่น `x;}body{display:none`) = ถูกปฏิเสธ 400 และฐานข้อมูลไม่เปลี่ยน
5. ไม่ได้ล็อกอิน เรียก API นี้ = 401
6. ผู้ใช้เดิมที่มีค่าใน localStorage = ถูกย้ายขึ้นเซิร์ฟเวอร์อัตโนมัติ ไม่ต้องเลือกใหม่
7. ตอน logout แล้วอีกคนล็อกอินบนเครื่องเดียวกัน = ไม่เห็นฟอนต์ของคนก่อน
8. เทสต์ใหม่ผ่านด้วย DB ชั่วคราว และเทสต์เดิมที่เกี่ยวข้อง (`test_p2_db_integrity.py` ฯลฯ) ยังผ่าน (รันทีละไฟล์)
9. เปิดหน้าจริงทั้งธีมสว่าง/มืด และมือถือ ฟอนต์เปลี่ยนถูกต้อง ไม่มีข้อความล้น

## ลำดับการทำ
1. migration + get/set + allowlist → เขียนเทสต์ DB
2. route + `/api/me` → เทสต์ด้วย Flask test client
3. แก้ `appearance.js` ซิงก์ + debounce + migrate ค่าเดิม + ล้างตอน logout
4. ทดสอบในเบราว์เซอร์ตามเกณฑ์ข้อ 1–7
5. สรุปผลเป็นภาษาไทยให้ผู้ใช้ พร้อมบอกว่าต้องรีสตาร์ตเซิร์ฟเวอร์
