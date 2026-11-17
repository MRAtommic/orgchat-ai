# -*- coding: utf-8 -*-
"""ไฟล์เนื้อหาเดียวกันต่างองค์กร ต้องไม่ถูกมองว่า "ซ้ำ" และต้องไม่ชนกัน (ใช้ข้อมูลชั่วคราว)"""
import os, subprocess, sys, tempfile, textwrap
from pathlib import Path

SCRIPT = textwrap.dedent(r'''
    import os, sys, tempfile
    from pathlib import Path
    tmp = tempfile.mkdtemp(prefix="kb_xorg_")
    os.environ["DATA_DIR"] = tmp
    os.environ["VECTOR_BACKEND"] = "python"
    for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "LINE_CHANNEL_ACCESS_TOKEN", "LINE_CHANNEL_SECRET"):
        os.environ[k] = ""
    sys.path.insert(0, os.getcwd())
    import rag_engine as R
    FAILS = []
    def check(n, ok, d=""):
        print(("PASS " if ok else "FAIL ") + n + ((" :: " + str(d)) if d and not ok else ""))
        if not ok: FAILS.append(n)

    f = Path(tmp) / "a.txt"
    f.write_text("นโยบายการลา พนักงานลาพักร้อนได้ปีละ 10 วัน " * 5, encoding="utf-8")
    r1 = R.ingest_file(f, original_name="ระเบียบ.txt", org_id=2, force=False)
    check("org 2 first upload succeeds", r1.get("status") not in ("duplicate", "error", "empty"), r1)
    r2 = R.ingest_file(f, original_name="ระเบียบ.txt", org_id=3, force=False)
    check("same file, other org (3) is NOT a duplicate", r2.get("status") != "duplicate", r2)
    r3 = R.ingest_file(f, original_name="ระเบียบ.txt", org_id=2, force=False)
    check("same file, same org (2) IS a duplicate", r3.get("status") == "duplicate", r3)
    meta = R._load_meta()
    orgs = sorted((v.get("organization_id"), k) for k, v in meta.items())
    check("two separate entries, one per org", len(orgs) == 2 and {o for o, _ in orgs} == {2, 3}, orgs)
    check("pre-check helper agrees (org 3 dup, org 4 not)",
          R._find_org_duplicate(meta, f, 3) is not None and R._find_org_duplicate(meta, f, 4) is None)
    print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
''')


def test_cross_org_same_file_not_duplicate():
    root = Path(__file__).resolve().parent.parent
    p = subprocess.run([sys.executable, "-c", SCRIPT], cwd=str(root), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=240)
    out = (p.stdout or "") + (p.stderr or "")
    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
    assert "ALL PASSED" in out and not fails, "\n".join(fails) or out[-2500:]
