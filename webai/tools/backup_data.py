# -*- coding: utf-8 -*-
"""Backup OrgChat data into a dated zip.

What is saved (safe while the server is running - SQLite online backup API is used):
  * SQLite database (consistent snapshot + integrity_check on the copy)
  * file_meta.json and the vector store (chroma_db_fallback.json, chroma_db/ if present)
  * uploads/ (optional, --with-uploads; can be large)
NOT saved on purpose: .env (secrets). Keep a separate private copy of it.

Usage:
  python tools/backup_data.py                       -> C:\\OrgChatBackups (outside OneDrive)
  python tools/backup_data.py --dest D:\\Backups --keep 30 --with-uploads
Exit code 0 = ok, 1 = failed. Schedule it with tools/install_scheduled_tasks.ps1.
"""
import argparse
import json
import logging
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEBAI))
try:  # pick up DB_PATH etc. from .env without printing it
    from dotenv import load_dotenv
    load_dotenv(WEBAI / ".env")
except Exception:
    pass

log = logging.getLogger("backup")


def resolve_db() -> Path:
    p = Path(os.environ.get("DB_PATH", "chat_history.db"))
    return p if p.is_absolute() else (WEBAI / p)


def snapshot_db(src: Path, dst: Path):
    """Consistent copy using sqlite3's online backup API, then verify it."""
    s = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True, timeout=60)
    d = sqlite3.connect(str(dst))
    try:
        s.backup(d)
    finally:
        d.close()
        s.close()
    chk = sqlite3.connect(str(dst))
    try:
        res = chk.execute("PRAGMA integrity_check").fetchone()[0]
        tables = chk.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    finally:
        chk.close()
    if res != "ok":
        raise RuntimeError(f"integrity_check failed on backup copy: {res}")
    return tables


def add_path(z: zipfile.ZipFile, path: Path, arc: str):
    if path.is_dir():
        for f in path.rglob("*"):
            if f.is_file():
                z.write(f, f"{arc}/{f.relative_to(path).as_posix()}")
    elif path.exists():
        z.write(path, arc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=os.environ.get("BACKUP_DIR", r"C:\OrgChatBackups"))
    ap.add_argument("--keep", type=int, default=14, help="number of newest backups to keep")
    ap.add_argument("--with-uploads", action="store_true")
    a = ap.parse_args()

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(dest / "backup.log", encoding="utf-8")])
    t0 = time.time()
    db = resolve_db()
    if not db.exists():
        log.error("database not found: %s", db)
        return 1
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = dest / f"orgchat_backup_{stamp}.zip"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "chat_history.db"
            tables = snapshot_db(db, snap)
            log.info("database snapshot ok (%d tables, %.1f MB)", tables, snap.stat().st_size / 1e6)
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(snap, "chat_history.db")
                for name in ("file_meta.json", "chroma_db_fallback.json", "line_config.json"):
                    add_path(z, WEBAI / name, name)
                add_path(z, WEBAI / "chroma_db", "chroma_db")
                if a.with_uploads:
                    add_path(z, WEBAI / "uploads", "uploads")
                z.writestr("BACKUP_INFO.json", json.dumps({
                    "created": datetime.now().isoformat(timespec="seconds"), "database": str(db),
                    "with_uploads": a.with_uploads, "note": ".env is NOT included"}, ensure_ascii=False, indent=2))
        # verify the zip opens and contains the DB
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and "chat_history.db" in z.namelist()
        log.info("backup written: %s (%.1f MB) in %.1fs", out, out.stat().st_size / 1e6, time.time() - t0)
    except Exception as e:
        log.error("BACKUP FAILED: %s", e)
        try:
            out.unlink(missing_ok=True)
        except Exception:
            pass
        return 1
    olds = sorted(dest.glob("orgchat_backup_*.zip"))
    for old in olds[:-max(1, a.keep)]:
        try:
            old.unlink()
            log.info("removed old backup %s", old.name)
        except Exception as e:
            log.warning("could not remove %s: %s", old, e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
