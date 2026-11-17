# -*- coding: utf-8 -*-
"""The knowledge base index must never be wiped by cleanup/prune when file metadata is missing or points elsewhere.
(Regression: a test run with a temp DATA_DIR wiped the real vector index through startup cleanup.)"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent

CODE = r'''
import json, os, sys
sys.path.insert(0, os.getcwd())
import rag_engine as R
from pathlib import Path
assert str(R.FALLBACK_VECTOR_JSON).startswith(os.environ["DATA_DIR"]), "vector JSON must live under DATA_DIR"
ef = lambda texts: [[1.0, 0.0, 0.0] for _ in texts]
st = R.PurePythonVectorStore(ef, R.FALLBACK_VECTOR_JSON)
st.upsert(["a", "b"], ["f1_chunk_0", "f2_chunk_0"], [{"file_id": "f1", "organization_id": 1}, {"file_id": "f2", "organization_id": 1}])
kb = R.KnowledgeBase.__new__(R.KnowledgeBase); kb.collection = st
out = {}
out["prune_empty_meta"] = kb.prune_orphaned_chunks([])            # meta empty -> must refuse
out["after_empty"] = st.count()
out["prune_all_orphans"] = kb.prune_orphaned_chunks(["zzz"])      # would delete everything -> must refuse
out["after_all"] = st.count()
out["prune_partial"] = kb.prune_orphaned_chunks(["f1"])           # legit: removes only f2
out["after_partial"] = st.count()
# kb_cleanup must not delete user uploads when file_meta is empty
up = R.UPLOAD_DIR / "keep_me.txt"; up.write_text("data", encoding="utf-8")
R._save_meta({})
import kb_cleanup
R._kb = kb
kb_cleanup.cleanup()
out["upload_kept"] = up.exists()
# saving an empty store keeps a safety copy
st.data = []; st.save()
out["safety_copy"] = any("before_empty" in p.name for p in R.FALLBACK_VECTOR_JSON.parent.iterdir())
print("RESULT " + json.dumps(out))
'''


def test_cleanup_and_prune_never_wipe_everything():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, DATA_DIR=tmp, DB_PATH=str(Path(tmp) / "k.db"), VECTOR_BACKEND="python", PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, "-c", CODE], cwd=str(WEBAI), env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
        line = next((l for l in p.stdout.splitlines() if l.startswith("RESULT ")), None)
        assert line, (p.stdout + p.stderr)[-2500:]
        import json
        r = json.loads(line[7:])
        assert r["prune_empty_meta"] == 0 and r["after_empty"] == 2
        assert r["prune_all_orphans"] == 0 and r["after_all"] == 2
        assert r["prune_partial"] == 1 and r["after_partial"] == 1
        assert r["upload_kept"] is True
        assert r["safety_copy"] is True
