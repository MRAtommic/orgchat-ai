import sqlite3
import logging
from .connection import _get_conn, DB_PATH, DB_TYPE

logger = logging.getLogger("OrgChatAI.DB.Schema")

def init_db(conn=None):
    should_close = False
    if conn is None:
        conn = _get_conn()
        should_close = True
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_broadcast_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            org_id INTEGER DEFAULT 1,
            text TEXT NOT NULL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            username TEXT DEFAULT 'System',
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            hash_signature TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN org_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN hash_signature TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_integrity_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            sha256_hash TEXT NOT NULL,
            file_size INTEGER,
            category TEXT DEFAULT 'uploads',
            last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL DEFAULT 1,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            created_by TEXT DEFAULT 'Admin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE line_broadcast_history ADD COLUMN org_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE line_broadcast_history ADD COLUMN scheduled_at TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            org_id INTEGER DEFAULT 1,
            check_date TEXT NOT NULL,
            check_time TEXT NOT NULL,
            check_type TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            address TEXT,
            distance_meters REAL,
            status TEXT DEFAULT 'on_time',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN reminder_sent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE time_attendance ADD COLUMN note TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE time_attendance ADD COLUMN updated_by TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT DEFAULT 'Admin',
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            sources TEXT,
            feedback INTEGER DEFAULT 0, -- 1 for up, -1 for down, 0 for none
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT DEFAULT 'Admin',
            title TEXT NOT NULL,
            description TEXT,
            start_date TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            start_time TEXT DEFAULT '09:00',
            is_public INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            author TEXT DEFAULT 'Anonymous',
            category TEXT DEFAULT 'General',
            summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            link TEXT,
            attachments TEXT,
            is_pinned INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_views (
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(post_id, username),
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    # Migration: Add new columns if they don't exist
    try: cursor.execute("ALTER TABLE posts ADD COLUMN link TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE posts ADD COLUMN attachments TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE posts ADD COLUMN is_pinned INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    # Ensure no NULLs in is_pinned for old rows
    cursor.execute("UPDATE posts SET is_pinned = 0 WHERE is_pinned IS NULL")

    # NEW Migration for schedules
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN is_public INTEGER DEFAULT 0")
        logger.info("✅ Database migrated: Added is_public column to schedules.")
    except sqlite3.OperationalError:
        pass
    
    cursor.execute("UPDATE schedules SET is_public = 0 WHERE is_public IS NULL")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            author TEXT DEFAULT 'Anonymous',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            post_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            PRIMARY KEY(post_id, user),
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            avatar_url TEXT,
            background_url TEXT,
            department TEXT DEFAULT 'General',
            position TEXT,
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            attachments TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: Add feedback column if it doesn't exist for older databases
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN feedback INTEGER DEFAULT 0")
        logger.info("✅ Database migrated: Added feedback column.")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN start_time TEXT DEFAULT '09:00'")
        logger.info("✅ Database migrated: Added start_time column to schedules.")
    except sqlite3.OperationalError:
        pass

    # NEW: Add username column to messages and schedules if not exists
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN username TEXT DEFAULT 'Admin'")
    except sqlite3.OperationalError: pass
    
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN username TEXT DEFAULT 'Admin'")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN department TEXT DEFAULT 'General'")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN position TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN line_user_id TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN line_login_id TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN target_departments TEXT") # Comma separated depts
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN target_users TEXT") # Comma separated usernames
    except sqlite3.OperationalError: pass

    # Migrations for leave_requests to sync duplicate schemas
    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN line_user_id TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN leave_type TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN type TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN file_link TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN approved_by TEXT")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN approver_note TEXT")
    except sqlite3.OperationalError: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            text TEXT NOT NULL,
            attachments TEXT,
            is_read INTEGER DEFAULT 0,
            is_pinned INTEGER DEFAULT 0,
            reply_to_id INTEGER,
            organization_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try: cursor.execute("ALTER TABLE private_messages ADD COLUMN reply_to_id INTEGER")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE private_messages ADD COLUMN organization_id INTEGER")
    except sqlite3.OperationalError: pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            avatar_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL DEFAULT 1,
            line_user_id TEXT,
            username TEXT,
            leave_type TEXT,
            type TEXT,
            start_date TEXT,
            end_date TEXT,
            reason TEXT,
            file_link TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            approver_note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN org_id INTEGER NOT NULL DEFAULT 1")
    except Exception:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_leave_quotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            org_id INTEGER NOT NULL DEFAULT 1,
            year INTEGER NOT NULL,
            sick_leave INTEGER NOT NULL DEFAULT 30,
            personal_leave INTEGER NOT NULL DEFAULT 6,
            vacation_leave INTEGER NOT NULL DEFAULT 6,
            other_leave INTEGER NOT NULL DEFAULT 30,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, org_id, year)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            username TEXT,
            event_type TEXT NOT NULL,
            action_detail TEXT,
            ip_address TEXT,
            user_agent TEXT,
            ai_model TEXT,
            tokens_used INTEGER DEFAULT 0,
            department TEXT DEFAULT 'General',
            status TEXT DEFAULT 'success',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_user_id TEXT,
            username TEXT,
            vendor TEXT,
            amount REAL,
            expense_date TEXT,
            file_link TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_members (
            room_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            last_read_id INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(room_id, username),
            FOREIGN KEY(room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            attachments TEXT,
            is_pinned INTEGER DEFAULT 0,
            reply_to_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE
        )
    """)
    try: cursor.execute("ALTER TABLE room_messages ADD COLUMN reply_to_id INTEGER")
    except sqlite3.OperationalError: pass
    # Migration: Add is_pinned to room_messages if not exists
    try:
        cursor.execute("ALTER TABLE room_messages ADD COLUMN is_pinned INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kb_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            avatar_url TEXT,
            visibility TEXT DEFAULT 'public', -- public, private, restricted
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: Add visibility & access_level to kb_categories if not exists
    try:
        cursor.execute("ALTER TABLE kb_categories ADD COLUMN visibility TEXT DEFAULT 'public'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE kb_categories ADD COLUMN access_level TEXT DEFAULT 'public'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN clearance_level TEXT DEFAULT 'employee'")
    except sqlite3.OperationalError: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            organization_id INTEGER DEFAULT 1,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_ts ON audit_logs(timestamp)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_category_access (
            username TEXT,
            category_id INTEGER,
            PRIMARY KEY (username, category_id),
            FOREIGN KEY(category_id) REFERENCES kb_categories(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            system_prompt TEXT NOT NULL,
            scope_category_id INTEGER,
            avatar_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_by TEXT,
            organization_id INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(scope_category_id) REFERENCES kb_categories(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wiki_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT,
            content TEXT,
            author TEXT,
            category_id INTEGER,
            org_id INTEGER DEFAULT 1,
            views INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            name TEXT,
            org_id INTEGER DEFAULT 1,
            position INTEGER DEFAULT 0,
            color TEXT DEFAULT '#6366f1',
            created_by TEXT DEFAULT 'System'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            column_id INTEGER DEFAULT 1,
            position INTEGER DEFAULT 0,
            assignee TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'normal',
            labels TEXT,
            color TEXT,
            is_done INTEGER DEFAULT 0,
            created_by TEXT,
            org_id INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: Add missing columns to wiki_pages and kanban_cards if tables existed previously
    for alter_sql in [
        "ALTER TABLE wiki_pages ADD COLUMN org_id INTEGER DEFAULT 1",
        "ALTER TABLE wiki_pages ADD COLUMN category_id INTEGER",
        "ALTER TABLE wiki_pages ADD COLUMN views INTEGER DEFAULT 0",
        "ALTER TABLE kanban_cards ADD COLUMN org_id INTEGER DEFAULT 1",
        "ALTER TABLE kanban_cards ADD COLUMN created_by TEXT",
        "ALTER TABLE kanban_cards ADD COLUMN labels TEXT",
        "ALTER TABLE kanban_cards ADD COLUMN color TEXT",
        "ALTER TABLE kanban_columns ADD COLUMN org_id INTEGER DEFAULT 1",
        "ALTER TABLE kanban_columns ADD COLUMN title TEXT",
        "ALTER TABLE kanban_columns ADD COLUMN color TEXT DEFAULT '#6366f1'",
        "ALTER TABLE kanban_columns ADD COLUMN created_by TEXT DEFAULT 'System'",
    ]:
        try:
            cursor.execute(alter_sql)
        except sqlite3.OperationalError:
            pass

    # Migration: Add organization_id to ai_personas if not exists
    try:
        cursor.execute("ALTER TABLE ai_personas ADD COLUMN organization_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError: pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            username TEXT PRIMARY KEY,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            can_view_kb INTEGER DEFAULT 0,
            can_edit_kb INTEGER DEFAULT 0,
            can_delete_kb INTEGER DEFAULT 0,
            custom_password TEXT,
            notes TEXT,
            line_permissions TEXT DEFAULT 'report,links,reconcile,search,folder,leave',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col, col_type in [
        ("totp_secret", "TEXT"), 
        ("totp_backup_codes", "TEXT"), 
        ("totp_enabled", "INTEGER DEFAULT 0"), 
        ("totp_type", "TEXT DEFAULT 'authenticator'"), 
        ("session_version", "INTEGER DEFAULT 1"),
        ("can_broadcast_line", "INTEGER DEFAULT 0"),
        ("can_manage_peak", "INTEGER DEFAULT 0")
    ]:
        try: cursor.execute(f"ALTER TABLE user_settings ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE organizations ADD COLUMN owner_username TEXT")
    except sqlite3.OperationalError: pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_invite_tokens (
            token TEXT PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            created_by TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            department TEXT,
            max_uses INTEGER DEFAULT 0,
            used_count INTEGER DEFAULT 0,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ip_blacklist (
            ip_address TEXT PRIMARY KEY,
            reason TEXT,
            blocked_until DATETIME,
            violation_count INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_edits (
            line_user_id TEXT PRIMARY KEY,
            sheet_name TEXT,
            row_index INTEGER,
            data_json TEXT,
            state TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Default settings
    cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('allow_user_edit', '0')")

    # Default Personas
    cursor.execute("SELECT COUNT(*) FROM ai_personas")
    if cursor.fetchone()[0] == 0:
        personas = [
            ("ผู้ช่วยมืออาชีพ (Professional)", "คุณเป็นเลขานุการผู้บริหารที่สุขุม รอบคอบ และเป็นทางการมาก ตอบคำถามด้วยสำนวนภาษาธุรกิจที่ไพเราะและชัดเจน", "เน้นความเป็นทางการ ข้อมูลแม่นยำ และภาษาสวยงาม", None, "https://cdn-icons-png.flaticon.com/512/1077/1077114.png", "System"),
            ("พี่ใจดี (Kind Assistant)", "คุณเป็นรุ่นพี่ในที่ทำงานที่ใจดี เข้าถึงง่าย และพร้อมช่วยเหลือน้องๆ เสมอ ตอบแบบเป็นกันเอง ใช้ภาษาที่เป็นมิตรและให้กำลังใจ", "เน้นความเป็นกันเอง สไตล์พี่สอนน้อง เข้าใจง่าย", None, "https://cdn-icons-png.flaticon.com/512/4140/4140048.png", "System"),
            ("สรุปสาระสำคัญ (Concise Specialist)", "คุณเป็นผู้เชี่ยวชาญด้านการสรุปข้อมูลที่เน้นความเร็วและเนื้อหาสำคัญเท่านั้น ตอบเป็นข้อๆ (Bullet points) สั้นที่สุดเท่าที่จะทำได้", "เน้นความรวดเร็ว สรุปเนื้อๆ ไม่เน้นน้ำ", None, "https://cdn-icons-png.flaticon.com/512/9131/9131546.png", "System")
        ]
        cursor.executemany("INSERT INTO ai_personas (name, system_prompt, description, scope_category_id, avatar_url, created_by) VALUES (?, ?, ?, ?, ?, ?)", personas)

    # Migrations for existing user_settings
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_view_kb INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_edit_kb INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_delete_kb INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN email TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_view_financial INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_manage_leave INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN line_permissions TEXT DEFAULT 'report,links,reconcile,search,folder,leave'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN locked_until DATETIME")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN totp_enabled INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN totp_secret TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN totp_backup_codes TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_use_ai INTEGER DEFAULT 1")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN can_claim_expense INTEGER DEFAULT 1")
    except sqlite3.OperationalError: pass

    # Migration: Add category_id to knowledge_base
    try:
        cursor.execute("ALTER TABLE knowledge_base ADD COLUMN category_id INTEGER")
    except sqlite3.OperationalError:
        pass

    # Migration: Add status to schedules for Kanban
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN status TEXT DEFAULT 'todo'")
        logger.info("✅ Database migrated: Added status column to schedules (Kanban).")
    except sqlite3.OperationalError:
        pass

    # Migration: Add is_archived to schedules
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN is_archived INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Migration: expense_claims columns for WHT & Multi-tenancy
    for col_sql in [
        "ALTER TABLE expense_claims ADD COLUMN org_id INTEGER DEFAULT 1",
        "ALTER TABLE expense_claims ADD COLUMN vendor_name TEXT",
        "ALTER TABLE expense_claims ADD COLUMN vendor_tax_id TEXT",
        "ALTER TABLE expense_claims ADD COLUMN wht_type TEXT",
        "ALTER TABLE expense_claims ADD COLUMN wht_rate REAL DEFAULT 0",
        "ALTER TABLE expense_claims ADD COLUMN wht_amount REAL DEFAULT 0",
        "ALTER TABLE expense_claims ADD COLUMN description TEXT",
    ]:
        try:
            cursor.execute(col_sql)
        except sqlite3.OperationalError:
            pass
    try:
        cursor.execute("UPDATE expense_claims SET vendor_name = vendor WHERE (vendor_name IS NULL OR vendor_name = '') AND vendor IS NOT NULL")
    except Exception:
        pass

    # Migration: Add reaction column to likes table
    try:
        cursor.execute("ALTER TABLE likes ADD COLUMN reaction TEXT DEFAULT 'like'")
        logger.info("✅ Database migrated: Added reaction column to likes.")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            username TEXT NOT NULL,
            subscription_json TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(username, subscription_json)
        )
    """)
    
    # --- Notifications Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT,
            is_read INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # --- Interactive Polls ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_votes (
            poll_id INTEGER NOT NULL,
            option_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            PRIMARY KEY(poll_id, username),
            FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE,
            FOREIGN KEY(option_id) REFERENCES poll_options(id) ON DELETE CASCADE
        )
    """)

    # Migration: Add edited_at to room_messages and private_messages for message edit feature
    try:
        cursor.execute("ALTER TABLE room_messages ADD COLUMN edited_at DATETIME")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE private_messages ADD COLUMN edited_at DATETIME")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE private_messages ADD COLUMN is_pinned INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass

    # Search History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            username TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- User Status Tracking (Online/Offline) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_status (
            username TEXT PRIMARY KEY,
            is_online INTEGER DEFAULT 0,
            current_room TEXT,
            typing_in_room TEXT,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Message Read Receipts ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_read_receipts (
            message_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            room_id INTEGER,
            read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(message_id, username),
            FOREIGN KEY(message_id) REFERENCES room_messages(id) ON DELETE CASCADE
        )
    """)

    # --- Private Message Read Status ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS private_message_read_status (
            message_id INTEGER NOT NULL,
            is_read INTEGER DEFAULT 0,
            read_at DATETIME,
            PRIMARY KEY(message_id),
            FOREIGN KEY(message_id) REFERENCES private_messages(id) ON DELETE CASCADE
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wiki_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            category_id INTEGER,
            organization_id INTEGER DEFAULT 1,
            status TEXT DEFAULT 'published',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES kb_categories(id) ON DELETE SET NULL
        )
    """)
    # Migration: add status column to existing wiki_pages tables
    try:
        cursor.execute("ALTER TABLE wiki_pages ADD COLUMN status TEXT DEFAULT 'published'")
    except Exception:
        pass

    # --- Performance Optimization: Indexes ---
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_username ON messages(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_room_messages_room_id ON room_messages(room_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_private_messages_participants ON private_messages(sender, recipient)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_private_messages_org_id ON private_messages(organization_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(start_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_status_online ON user_status(is_online)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_read_receipts ON message_read_receipts(message_id, username)")
    
    # --- Leave Requests Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            approved_by TEXT,
            approver_note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leave_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            comment TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(leave_id) REFERENCES leave_requests(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_text TEXT,
            user TEXT,
            organization_id INTEGER DEFAULT 1,
            time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN organization_id INTEGER DEFAULT 1")
    except Exception:
        pass

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(time)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lunch_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT, -- เช่น ตามสั่ง, ส้มตำ, ญี่ปุ่น
            location TEXT,
            added_by TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add initial data if empty
    cursor.execute("SELECT COUNT(*) FROM lunch_places")
    if cursor.fetchone()[0] == 0:
        places = [
            ("ข้าวมันไก่หน้าปากซอย", "ไก่ตอน", "หน้าปากซอย"),
            ("ส้มตำแซ่บเวอร์", "อีสาน", "ข้างออฟฟิศ"),
            ("ราเมนเด็ด", "ญี่ปุ่น", "ในห้าง"),
            ("ตามสั่งป้าดาว", "อาหารตามสั่ง", "ตึกแถวตรงข้าม"),
            ("ผัดไทยโบราณ", "เส้น", "ทางเดินรถเมล์")
        ]
        cursor.executemany("INSERT INTO lunch_places (name, type, location) VALUES (?,?,?)", places)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drive_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT,
            amount REAL,
            doc_date TEXT,
            summary TEXT,
            file_link TEXT,
            user_id TEXT,
            org_id INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: add org_id, sync_status, local_filepath to drive_logs if missing
    try:
        cursor.execute("ALTER TABLE drive_logs ADD COLUMN org_id INTEGER DEFAULT 1")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE drive_logs ADD COLUMN sync_status TEXT DEFAULT 'synced'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE drive_logs ADD COLUMN local_filepath TEXT")
    except Exception:
        pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_created_at ON drive_logs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_filename ON drive_logs(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drive_logs_org_id ON drive_logs(org_id)")

    # --- Offline-First Resilient Upload Queue ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offline_upload_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            username TEXT,
            user_id TEXT,
            original_filename TEXT NOT NULL,
            local_filepath TEXT NOT NULL,
            mimetype TEXT,
            folder_id TEXT,
            folder_name TEXT,
            analysis_json TEXT,
            extracted_data_json TEXT,
            verification_status TEXT,
            line_sender_name TEXT,
            sync_status TEXT DEFAULT 'pending',
            drive_link TEXT,
            sheets_row INTEGER,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            synced_at DATETIME
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_offline_queue_sync_status ON offline_upload_queue(sync_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_offline_queue_org_id ON offline_upload_queue(org_id)")

    # --- Per-User Google OAuth2 Token Storage (personal / no-org users) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_google_tokens (
            username TEXT PRIMARY KEY,
            google_email TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TEXT,
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Multi-Tenancy: Organizations ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT UNIQUE,
            owner_username TEXT,
            plan TEXT DEFAULT 'free',
            max_users INTEGER DEFAULT 10,
            trial_ends_at DATETIME,
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Per-Org Google OAuth2 Token Storage (1 Google account shared by entire org) ---
    
    try:
        cursor.execute("ALTER TABLE organizations ADD COLUMN owner_username TEXT")
    except Exception:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_google_tokens (
            org_id INTEGER PRIMARY KEY,
            google_email TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TEXT,
            spreadsheet_id TEXT,
            drive_folder_id TEXT,
            connected_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)

    # --- B2B LINE Group Mapping Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_group_mappings (
            group_id TEXT PRIMARY KEY,
            owner_username TEXT NOT NULL,
            group_name TEXT,
            default_folder_id TEXT,
            default_folder_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner_username) REFERENCES user_profiles(username) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_members (
            organization_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            invited_by TEXT,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            manager_username TEXT,
            PRIMARY KEY (organization_id, username),
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_profiles (
            org_id INTEGER PRIMARY KEY,
            business_type TEXT,
            vat_status TEXT,
            branch_type TEXT,
            business_name_th TEXT,
            business_name_en TEXT,
            tax_id TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            district TEXT,
            province TEXT,
            zipcode TEXT,
            phone TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    # --- Per-Org LINE Bot Channel Key Integration ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_line_configs (
            org_id INTEGER PRIMARY KEY,
            channel_access_token TEXT,
            channel_secret TEXT,
            bot_basic_id TEXT,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    # Add organization_id columns to key tables (migrations)
    for tbl in ("messages", "schedules", "posts", "chat_rooms", "wiki_pages"):
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN organization_id INTEGER DEFAULT 1")
        except Exception:
            pass
    # Billing: usage tracking per org per month
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_tracking (
            org_id      INTEGER NOT NULL,
            year_month  TEXT    NOT NULL,
            expense_count    INTEGER DEFAULT 0,
            ai_query_count   INTEGER DEFAULT 0,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (org_id, year_month)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_login_tokens (
            token      TEXT PRIMARY KEY,
            status     TEXT DEFAULT 'pending',
            username   TEXT,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stripe_processed_events (
            event_id     TEXT PRIMARY KEY,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # DB-backed LINE link tokens (แทน in-memory PENDING_LINE_LINKS)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_line_links (
            token        TEXT PRIMARY KEY,
            line_user_id TEXT NOT NULL,
            expires_at   REAL NOT NULL
        )
    """)
    # DB-backed OAuth2 states (แทน in-memory _OAUTH_STATES)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_states (
            state       TEXT PRIMARY KEY,
            data_json   TEXT NOT NULL,
            expires_at  REAL NOT NULL
        )
    """)

    # Custom Categories & AI Auto-Categorization Rules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_expense_categories (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id        INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            account_code  TEXT DEFAULT '',
            parent_id     INTEGER DEFAULT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_category_rules (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id        INTEGER NOT NULL,
            keyword       TEXT NOT NULL,
            category_name TEXT NOT NULL,
            rule_type     TEXT DEFAULT 'contains',
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_members_username ON organization_members(username)")
    # Migration: plan_expires_at, Stripe fields on organizations
    for col_sql in [
        "ALTER TABLE organizations ADD COLUMN plan_expires_at DATETIME",
        "ALTER TABLE organizations ADD COLUMN stripe_customer_id TEXT",
        "ALTER TABLE organizations ADD COLUMN stripe_subscription_id TEXT",
        "ALTER TABLE organizations ADD COLUMN whitelist_enabled INTEGER DEFAULT 0",
        "ALTER TABLE organization_members ADD COLUMN manager_username TEXT",
    ]:
        try:
            cursor.execute(col_sql)
        except Exception:
            pass

    # --- Whitelist Emails ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_allowed_emails (
            organization_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            added_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (organization_id, email),
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER DEFAULT 1,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            created_by TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            color TEXT DEFAULT '#3b82f6',
            icon TEXT DEFAULT 'building',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(organization_id, name COLLATE NOCASE),
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_departments_org ON organization_departments(organization_id)")
    try:
        cursor.execute("ALTER TABLE organization_allowed_emails ADD COLUMN role TEXT DEFAULT 'member'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE organization_departments ADD COLUMN head_username TEXT DEFAULT ''")
    except Exception:
        pass

    # Migration: add org_id to line_group_mappings for multi-tenant support
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN org_id INTEGER")
    except Exception:
        pass
    # Migration: store real LINE group name and picture fetched from LINE API
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN line_real_name TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN line_picture_url TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE line_group_mappings ADD COLUMN bot_enabled INTEGER DEFAULT 1")
    except Exception:
        pass

    # Seed default organization
    cursor.execute("INSERT OR IGNORE INTO organizations (id, name, slug, plan) VALUES (1, 'Default Organization', 'default', 'free')")
    # Ensure system admin accounts are in default org if needed
    for uname in ("Admin", "admin"):
        cursor.execute("SELECT 1 FROM organization_members WHERE username = ? COLLATE NOCASE AND organization_id = 1", (uname,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO organization_members (organization_id, username, role)
                VALUES (1, ?, 'admin')
            """, (uname,))

    # Database Consistency: Clean orphan records to maintain PRAGMA foreign_key_check = 0
    try:
        cursor.execute("DELETE FROM comments WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM post_views WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM likes WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM polls WHERE post_id NOT IN (SELECT id FROM posts)")
        cursor.execute("DELETE FROM poll_votes WHERE poll_id NOT IN (SELECT id FROM polls)")
        cursor.execute("DELETE FROM poll_options WHERE poll_id NOT IN (SELECT id FROM polls)")
        cursor.execute("DELETE FROM room_members WHERE room_id NOT IN (SELECT id FROM chat_rooms)")
    except Exception:
        pass


    # ══════════════════════════════════════════════════════
    # Feature: Quotation / Invoice
    # ══════════════════════════════════════════════════════
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id          INTEGER NOT NULL,
            quotation_no    TEXT NOT NULL,
            type            TEXT DEFAULT 'quotation',   -- quotation | invoice
            customer_name   TEXT NOT NULL,
            customer_company TEXT DEFAULT '',
            customer_address TEXT DEFAULT '',
            customer_tax_id  TEXT DEFAULT '',
            customer_email   TEXT DEFAULT '',
            customer_phone   TEXT DEFAULT '',
            items           TEXT DEFAULT '[]',           -- JSON [{name,qty,unit,price}]
            subtotal        REAL DEFAULT 0,
            discount        REAL DEFAULT 0,
            vat_rate        REAL DEFAULT 7,
            vat_amount      REAL DEFAULT 0,
            wht_rate        REAL DEFAULT 0,
            wht_amount      REAL DEFAULT 0,
            total           REAL DEFAULT 0,
            status          TEXT DEFAULT 'draft',        -- draft|sent|approved|rejected|paid
            notes           TEXT DEFAULT '',
            valid_until     TEXT DEFAULT '',
            created_by      TEXT NOT NULL,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotations_org ON quotations(org_id, created_at)")

    # ══════════════════════════════════════════════════════
    # Feature: CRM — Customers & Deals
    # ══════════════════════════════════════════════════════
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id      INTEGER NOT NULL,
            name        TEXT NOT NULL,
            company     TEXT DEFAULT '',
            email       TEXT DEFAULT '',
            phone       TEXT DEFAULT '',
            address     TEXT DEFAULT '',
            tax_id      TEXT DEFAULT '',
            tags        TEXT DEFAULT '[]',
            notes       TEXT DEFAULT '',
            created_by  TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_customers_org ON crm_customers(org_id)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_deals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id          INTEGER NOT NULL,
            customer_id     INTEGER,
            title           TEXT NOT NULL,
            value           REAL DEFAULT 0,
            stage           TEXT DEFAULT 'lead',  -- lead|qualified|proposal|negotiation|won|lost
            probability     INTEGER DEFAULT 50,
            expected_close  TEXT DEFAULT '',
            assigned_to     TEXT DEFAULT '',
            notes           TEXT DEFAULT '',
            created_by      TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES crm_customers(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_deals_org ON crm_deals(org_id, stage)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_activities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id      INTEGER NOT NULL,
            deal_id     INTEGER,
            customer_id INTEGER,
            type        TEXT DEFAULT 'note',   -- note|call|email|meeting
            content     TEXT NOT NULL,
            created_by  TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(deal_id) REFERENCES crm_deals(id) ON DELETE CASCADE
        )
    """)

    # ══════════════════════════════════════════════════════
    # Feature: Meeting Notes
    # ══════════════════════════════════════════════════════
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_notes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id          INTEGER NOT NULL,
            title           TEXT NOT NULL,
            audio_filename  TEXT DEFAULT '',
            transcript      TEXT DEFAULT '',
            summary         TEXT DEFAULT '',
            action_items    TEXT DEFAULT '[]',   -- JSON [{task, assignee, due}]
            participants    TEXT DEFAULT '',
            meeting_date    TEXT DEFAULT '',
            wiki_page_id    INTEGER DEFAULT NULL,
            created_by      TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_notes_org ON meeting_notes(org_id, created_at)")

    # ══════════════════════════════════════════════════════
    # Feature: Org Flex Card Customization
    # ══════════════════════════════════════════════════════
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS org_flex_settings (
            org_id INTEGER PRIMARY KEY,
            primary_color TEXT DEFAULT '#2563EB',
            header_bg TEXT DEFAULT '#1B2838',
            header_text_color TEXT DEFAULT '#FFFFFF',
            header_icon TEXT DEFAULT '📢',
            header_title TEXT DEFAULT 'ประกาศใหม่',
            header_sub TEXT DEFAULT 'NEW ANNOUNCEMENT',
            badge_text TEXT DEFAULT 'GENERAL',
            badge_bg TEXT DEFAULT '#EFF6FF',
            badge_color TEXT DEFAULT '#2563EB',
            button_style TEXT DEFAULT 'primary',
            button_color TEXT DEFAULT '#2563EB',
            portal_button_text TEXT DEFAULT '💬 ดูในระบบ OrgChat',
            feed_primary_color TEXT DEFAULT '#7C3AED',
            feed_header_bg TEXT DEFAULT '#7C3AED',
            feed_header_icon TEXT DEFAULT '✨',
            feed_header_title TEXT DEFAULT 'โพสต์ใหม่ใน Feed',
            feed_header_sub TEXT DEFAULT 'NEW FEED POST',
            card_style TEXT DEFAULT 'modern',
            show_avatar INTEGER DEFAULT 1,
            custom_json_template TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')


    # ══════════════════════════════════════════════════════
    # High-Performance Composite Indexes
    # ══════════════════════════════════════════════════════
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_org_user_time ON messages(organization_id, username, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_room_messages_room_time ON room_messages(room_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(username, is_read, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_org_date ON schedules(organization_id, start_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(username, organization_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_tracking_org_ym ON usage_tracking(org_id, year_month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotations_org_created ON quotations(org_id, created_at)")

    conn.commit()

    try:
        from .migrations import run_migrations
        run_migrations(conn)
    except Exception as e:
        logger.warning(f"Database migration notice: {e}")

    if should_close:
        conn.close()


