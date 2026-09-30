import os
import sys
import shutil
import uuid
from pathlib import Path

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

import rag_engine

docs_dir = Path(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\company_docs")
org_id = 2
category_id = 3

print("Starting ingestion for Chuenchob.co.th (org_id=2, category_id=3)...")
for file_path in docs_dir.glob("*.txt"):
    orig_name = file_path.name
    uid = str(uuid.uuid4())[:8]
    save_path = rag_engine.UPLOAD_DIR / f"{uid}_{orig_name}"
    shutil.copy2(file_path, save_path)
    res = rag_engine.ingest_file(
        save_path, 
        original_name=orig_name, 
        department="General", 
        category_id=category_id, 
        org_id=org_id
    )
    print(f"File: {orig_name} -> status: {res.get('status')} | chunks: {res.get('chunks', 0)}")

print("All done!")
