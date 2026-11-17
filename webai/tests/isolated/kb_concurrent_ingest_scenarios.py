# -*- coding: utf-8 -*-
"""Uploading several files at once must not leave any file stuck in 'processing' (lost-update on file_meta.json). Temp DATA_DIR, local embeddings."""
import os, sys, threading, tempfile
from pathlib import Path
assert os.environ.get("DATA_DIR")
os.environ["VECTOR_BACKEND"] = "python"
os.environ["AI_EMBEDDING_PROVIDER"] = "local"
sys.path.insert(0, os.getcwd())
import rag_engine  # noqa: E402

N = 6
d = Path(tempfile.mkdtemp(prefix="kbc_"))
paths = []
for i in range(N):
    p = d / f"doc_{i}.txt"
    p.write_text(f"เอกสารทดสอบหมายเลข {i}. " + ("ข้อความตัวอย่างสำหรับทดสอบการทำดัชนีพร้อมกัน " * 12), encoding="utf-8")
    paths.append(p)
results = {}


def run(i):
    results[i] = rag_engine.ingest_file(paths[i], f"doc_{i}.txt", department="General", org_id=1)


ts = [threading.Thread(target=run, args=(i,)) for i in range(N)]
[t.start() for t in ts]
[t.join() for t in ts]
meta = rag_engine._load_meta()
by_name = {v.get("name"): v for v in meta.values()}
fails = []
for i in range(N):
    m = by_name.get(f"doc_{i}.txt") or {}
    ok = results[i].get("status") == "ok" and m.get("status") == "ready" and (m.get("chunks") or 0) > 0
    print(("PASS " if ok else "FAIL ") + f"doc_{i}: result={results[i].get('status')} meta={m.get('status')} chunks={m.get('chunks')}")
    if not ok:
        fails.append(i)
print("ALL PASSED" if not fails else "FAILED")
sys.exit(1 if fails else 0)
