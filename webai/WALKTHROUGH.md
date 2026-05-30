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
