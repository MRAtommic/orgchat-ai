import sqlite3
import os
import re
from pathlib import Path

db_path = Path(__file__).parent.parent / 'chat_history.db'

def strip_think_tags(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>[\s\S]*', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'[\s\S]*?</think>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'^(?:Here\'?s a thinking process:?|Thinking [Pp]rocess:?|Analysis:?)[\s\S]*?\n\n', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</?think>', '', cleaned)
    return cleaned.strip()

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Tables in DB: {tables}")
    
    total_sanitized = 0
    for tbl in tables:
        cur.execute(f"PRAGMA table_info({tbl})")
        cols = [c[1] for c in cur.fetchall()]
        # Check for message / text columns
        target_cols = [col for col in cols if any(k in col.lower() for k in ['text', 'message', 'content', 'reply', 'prompt', 'briefing', 'summary'])]
        for col in target_cols:
            try:
                cur.execute(f"SELECT rowid, {col} FROM {tbl} WHERE {col} LIKE '%<think>%' OR {col} LIKE '%Thinking Process%' OR {col} LIKE '%</think>%'")
                rows = cur.fetchall()
                if rows:
                    print(f"Found {len(rows)} matching rows in {tbl}.{col}")
                    for r_id, val in rows:
                        if val:
                            cleaned = strip_think_tags(val)
                            cur.execute(f"UPDATE {tbl} SET {col} = ? WHERE rowid = ?", (cleaned, r_id))
                            total_sanitized += 1
            except Exception as e:
                print(f"Error checking {tbl}.{col}: {e}")
                
    conn.commit()
    print(f"Done! Total fields sanitized across all tables: {total_sanitized}")
    conn.close()
