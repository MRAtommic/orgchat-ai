# OrgChat-AI System Upgrade — Walkthrough

## Overview

This walkthrough documents the complete system upgrade of OrgChat-AI across three phases:

1. **Phase 1**: RAG Migration to `pgvector` on Supabase
2. **Phase 2**: SQLAlchemy ORM for the 44-table schema
3. **Phase 3**: Blueprint Refactoring of `app_server.py`

---

## Phase 3: Blueprint Refactoring (Current)

### Problem
The monolithic `app_server.py` was **10,894 lines** (~527 KB), containing all 243 routes, 23 SocketIO handlers, helper functions, decorators, and the main entry point in a single file.

### Solution
Refactored into a modular **Flask Blueprint architecture** using the **App Factory Pattern**.

### Architecture

```
webai/
├── app_server.py          # ~280 lines — App Factory + startup (was 10,894 lines)
├── routes/
│   ├── __init__.py        # Blueprint registry
│   ├── shared.py          # Shared decorators, helpers, constants, instances
│   ├── auth.py            # 29 functions — Auth, OAuth2, LINE linking, QR login
│   ├── chat.py            # 117 functions — AI chat, LINE webhook, messaging, KB, Drive
│   ├── social.py          # 36 functions — Feed, polls, wiki, kanban
│   ├── admin.py           # 96 functions — Admin panel, billing, settings, schedules
│   └── misc.py            # 23 functions — Health, uploads, notifications, pages
├── _archive/
│   └── app_server_pre_blueprint.py  # Backup of original monolith
```

### Files Created/Modified

| File | Action | Size | Purpose |
|------|--------|------|---------|
| [app_server.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/app_server.py) | **REWRITTEN** | ~280 lines | App Factory pattern |
| [routes/shared.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/routes/shared.py) | **CREATED** | ~350 lines | Shared utilities |
| [routes/__init__.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/routes/__init__.py) | **CREATED** | 18 lines | Blueprint registry |
| [routes/auth.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/routes/auth.py) | **CREATED** | ~1,300 lines | Auth Blueprint |
| [routes/chat.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/routes/chat.py) | **CREATED** | ~6,300 lines | Chat Blueprint |
| [routes/social.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/routes/social.py) | **CREATED** | ~900 lines | Social Blueprint |
| [routes/admin.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/routes/admin.py) | **CREATED** | ~2,400 lines | Admin Blueprint |
| [routes/misc.py](file:///c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/routes/misc.py) | **CREATED** | ~240 lines | Misc Blueprint |

### What `shared.py` Contains

All shared instances and helpers that would cause circular imports if placed in individual Blueprints:

- **Instances**: `socketio`, `_limiter`, `online_users_registry`
- **Decorators**: `login_required`, `admin_required`, `superadmin_required`, `safe_thread_target`
- **Constants**: `VERSION`, `ALLOWED_EXTENSIONS`, `VAPID_*`, `THAI_HOLIDAYS_2026`
- **Auth Helpers**: `USERS`, `OAUTH2_AVAILABLE`, `oauth2_service`, `GOOGLE_AUTH_AVAILABLE`
- **Session Helpers**: `_set_session_org`, `get_current_org_id`
- **KB Helpers**: `can_edit/view/delete_knowledge_base`, `is_admin`, `get_rag_filter`
- **File Validation**: `validate_uploaded_file`, `_is_safe_url`
- **Push Notifications**: `send_push_notification`, `batch_send_push_notification`
- **Weather/Time**: `update_weather_background`, `get_weather_context`, `get_current_time`

### Verification Results

| Test | Result |
|------|--------|
| Server boot | ✅ All 5 Blueprints registered |
| Route count | ✅ ~250 routes registered with Blueprint namespaces |
| SocketIO | ✅ Client connections & room joins working |
| API health | ✅ All tested endpoints return 200 OK |
| Scheduler | ✅ Weather, Reconciliation, Daily Summary jobs running |
| Background init | ✅ KB cleanup, Google Workspace warmup complete |

### Route Namespace Examples

Routes are now namespaced under their Blueprint:

```
auth.api_login           -> /api/login
chat.line_webhook        -> /api/line/webhook
social.manage_posts      -> /api/posts
admin.admin_settings_route -> /api/admin/settings
misc.health_check        -> /health
```

---

## 🛠️ Post-Blueprint Refactoring Stability & Bug Fixes

While validating the newly refactored server, we identified and resolved a crucial stability issue:

### ChromaDB Fallback JSON Serialization Fix
- **Problem**: When ChromaDB is unavailable (e.g. missing `hnswlib` C++ compilation toolchain on Windows), the RAG engine correctly falls back to `PurePythonVectorStore` which serializes to `chroma_db_fallback.json`. However, when embeddings are generated as numpy `ndarray` objects (e.g., during PDF/CSV ingest like `titanic.csv`), JSON serialization failed with `Object of type ndarray is not JSON serializable`, preventing the fallback vector database from saving successfully and leaving the file in a corrupted state.
- **Solution**: Updated the `upsert` method inside `PurePythonVectorStore` in `rag_engine.py` to check for and convert `ndarray` or non-standard list representations into standard Python lists of floats (`emb.tolist()`).
- **Result**: The JSON fallback vector store now synchronizes, saves, and loads perfectly with `Loaded 0 chunks...` / `Sync complete.` and absolutely zero runtime serialization errors.

### 5. Trigger Reconciliation Script (trigger_recon.py) Fix
- **File modified**: [tools/trigger_recon.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/tools/trigger_recon.py)
- **Fix**: 
  - Added parent directory to `sys.path` and loaded environment variables (`dotenv`) at the top of the file so that local modules and settings resolve properly.
  - Replaced the non-existent function call `google_drive_service.perform_auto_reconciliation` with `google_manager.spreadsheet_id = spreadsheet_id` and `google_manager.auto_reconcile_internal()`.
  - Added `set_context` call for initial authentication.
- **Why**: The script had several issues that caused NameError (missing imports), ModuleNotFoundError (missing path config), and AttributeError (calling a function that didn't exist instead of the class method), making it crash upon execution.

---

### 15. ดำเนินการแก้ไขข้อผิดพลาดและความเสี่ยง 6 จุดตามรายงาน QA Audit
* **ไฟล์ที่แก้ไข:** 
  * [routes/admin.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/routes/admin.py)
  * [routes/chat.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/routes/chat.py)
  * [rag_engine.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/rag_engine.py)
  * [app_server.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/app_server.py)
  * [templates/index.html](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/templates/index.html)
* **การแก้ไข:**
  1. **สิทธิ์ API ประวัติการใช้งาน:** กรอง Log กิจกรรมหลังบ้านให้ตรงกับ `org_id` ของแอดมินองค์กรที่ขอ ป้องกันข้อมูลกิจกรรมของแต่ละองค์กรไม่ให้รั่วไหลข้ามระบบ
  2. **สิทธิ์แก้ไข AI Persona ของระบบ:** ระบบจะบล็อกคำขอแก้ไขบอทต้นแบบหลัก (`created_by == 'System'`) หากผู้ใช้ไม่ใช่ superadmin (คืนค่า 403 Forbidden)
  3. **จำกัดจำนวน Excel Chunks:** เพิ่มการ break หยุดดึงข้อมูลจากไฟล์ Excel (.xlsx) เมื่อ Chunks สะสมมีจำนวนครบ 500 แถว เพื่อควบคุมการใช้งานหน่วยความจำ RAM ของเครื่องเซิร์ฟเวอร์
  4. **ความปลอดภัยคุกกี้เซสชัน:** เปิดใช้งานคอนฟิก `SESSION_COOKIE_SAMESITE = 'Lax'` และ `SESSION_COOKIE_HTTPONLY = True` เพื่อบล็อกการโจมตีขโมยคุกกี้และ CSRF และเปิดใช้ `SESSION_COOKIE_SECURE = True` เมื่อรันบน HTTPS (ตรวจสอบแบบ Dynamic)
  5. **รูปแบบ LINE Group ID:** ใช้ Regex `^[CRU][a-fA-F0-9]{32}$` ตรวจสอบความถูกต้องของ Group ID ทั้งฝั่ง Frontend (ใน Javascript) และ Backend (ก่อนนำไปบันทึก) เพื่อป้องกันการใส่ค่ามั่วหรือฟอร์แมตผิดพลาด
  6. **การแสดงผลเตือนเมื่อ Google Drive เชื่อมต่อล้มเหลว:** ปรับใน Dropdown เลือกโฟลเดอร์ของ Google Drive ให้ขึ้นข้อความแจ้งเตือนสีแดงชัดเจนเมื่อยังไม่มีการเชื่อมต่อกับระบบคลาวด์ เพื่อป้องกันแอดมินสับสน
* **เหตุผล:** เพื่ออุดช่องโหว่ความปลอดภัยด้าน Data Isolation, แก้ไขสิทธิ์การเข้าถึงทรัพยากรส่วนกลาง, ป้องกันระบบล่ม (OOM) และปรับปรุงระบบนำเข้า/ผูกบัญชีให้แจ้งรายละเอียดแก่แอดมินได้ดียิ่งขึ้น

---

## ขั้นตอนการทดสอบสำหรับผู้ใช้งาน (Verification Steps)

1. **ตรวจสอบความเรียบร้อยและเริ่มระบบ:**
   * หน้าเว็บและโค้ด HTML ได้รับการอัปเดตเรียบร้อย แนะนำให้ทำการ restart เซิร์ฟเวอร์ (`python app_server.py`) หรือรีเฟรชบราวเซอร์เพื่อโหลดโครงสร้าง UI ใหม่
2. **ทดสอบระบบจำกัดการแก้ไข AI Persona ระบบ:**
   * ลงชื่อเข้าใช้ด้วยแอดมินองค์กรทั่วไป ลองกดแก้ไขข้อมูล AI Persona ระบบที่มีสถานะ System จะโดนระบบปฏิเสธ
3. **ทดสอบกรอกรูปแบบ LINE Group ID:**
   * ลองใส่ Group ID ที่ไม่ใช่รูปแบบมาตรฐาน (เช่น `abc` หรือ `C123`) ระบบจะขึ้นเตือนไม่ถูกต้องตั้งแต่หน้าจอของผู้ใช้
4. **ทดสอบ Google Drive Dropdown:**
   * หากองค์กรยังไม่ได้เชื่อมต่อ Google Drive ระบบจะดึงโฟลเดอร์ไม่ได้ และ Dropdown จะแสดงตัวเลือกเด่นชัด: `❌ Google Drive ยังไม่ได้เชื่อมต่อ (กรุณาเชื่อมต่อก่อน)` เป็นสีแดงเตือนทันที
5. **ทดสอบ compile และตรวจสอบ syntax โค้ดหลังบ้าน:**
   * รันคำสั่งตรวจสอบไวยากรณ์ด้วย Python เรียบร้อยแล้ว ไม่พบข้อผิดพลาดไวยากรณ์ (Syntax Error) โค้ดทำงานได้สมบูรณ์แบบ
6. **Purchase Plan**: Go to the `/pricing` page and select a plan (e.g. PromptPay). The QR code and checkout page should now load successfully.
7. **Refresh the dashboard** page in your browser.
8. Under **Google Drive & Sheets (ทั้งองค์กร)**, click the **ยกเลิกการเชื่อมต่อ Google** (Disconnect Google) button.
   - Confirm the dialog.
   - The status should instantly update to **ยังไม่ได้เชื่อมต่อ** (Not connected).
9. **Re-connect your Google account** for the organization using `mxmm2547@gmail.com`.
10. **Send a document/file/image to the LINE Bot** in your registered group chat.
   - The bot should prompt for a folder. Select the folder.
   - The bot will process, upload the file to your Google Drive folder, and successfully log the record into the Google Sheet.
11. **Trigger Reconciliation Tool**: Run `.venv\Scripts\python tools\trigger_recon.py` from the `webai/` directory. It should parse spreadsheet files and call the reconciliation flow correctly.

---

## Rollback Plan

If any issues arise, the original monolithic `app_server.py` is preserved at:

```
webai/_archive/app_server_pre_blueprint.py
```

To rollback:
```bash
copy _archive\app_server_pre_blueprint.py app_server.py
```

---

## 🔒 Persona Identity Safety Update (New)
* **What**: Added an explicit identity safety guideline (`[คำเตือนเรื่องตัวตน]`) into the system prompt templates across all channels:
  1. **LINE Webhook / Autoreply**: inside `handle_bot_response` in [chat.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/routes/chat.py).
  2. **LINE Group Scheduler / Broadcasts**: inside `run_line_bot_scheduler` in [app_server.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/app_server.py).
  3. **Web AI Chat Client**: inside `api_chat` in [chat.py](file:///c:/Users/FEWIT/Desktop/orgchat-ai-main/webai/routes/chat.py).
* **Why**: To prevent name collision issues where an AI assistant shares the same name as a real organization employee in the knowledge base docs. The safety system prompt explicitly instructs the LLM that it is an AI assistant, and if asked for personal details of a person sharing its name, it must quote the reference documents instead of misrepresenting those details as its own.

