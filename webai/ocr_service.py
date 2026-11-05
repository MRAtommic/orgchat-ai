# -*- coding: utf-8 -*-
"""
ocr_service.py — OCR ภาษาไทย+อังกฤษด้วย Tesseract

หา tesseract.exe เอง (ตัวแปร TESSERACT_CMD → PATH → Program Files) และใช้ข้อมูลภาษาจากโฟลเดอร์ webai/tessdata
(มี tha.traineddata) จึงไม่ต้องแก้ไฟล์ใน Program Files  ถ้าไม่มี Tesseract จะคืนค่าว่าง ไม่ทำให้ระบบล้ม
"""
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger("OrgChatAI.OCR")

_BASE = Path(__file__).resolve().parent
_STATE = {"checked": False, "ok": False, "lang": "eng", "msg": ""}

_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]


def _find_cmd():
    env = os.environ.get("TESSERACT_CMD", "").strip()
    if env and Path(env).exists():
        return env
    which = shutil.which("tesseract")
    if which:
        return which
    for c in _CANDIDATES:
        if Path(c).exists():
            return c
    return None


def configure(force: bool = False) -> dict:
    """เตรียม pytesseract ครั้งเดียว คืน {"ok", "lang", "msg"}"""
    if _STATE["checked"] and not force:
        return dict(_STATE)
    _STATE.update(checked=True, ok=False, lang="eng", msg="")
    try:
        import pytesseract
    except Exception:
        _STATE["msg"] = "ไม่ได้ติดตั้ง pytesseract"
        return dict(_STATE)
    cmd = _find_cmd()
    if not cmd:
        _STATE["msg"] = "ไม่พบ Tesseract (ติดตั้งด้วย: winget install UB-Mannheim.TesseractOCR)"
        return dict(_STATE)
    pytesseract.pytesseract.tesseract_cmd = cmd
    local = _BASE / "tessdata"
    if local.is_dir() and not os.environ.get("TESSDATA_PREFIX"):
        os.environ["TESSDATA_PREFIX"] = str(local)
    try:
        langs = set(pytesseract.get_languages(config=""))
    except Exception as e:
        _STATE["msg"] = f"เรียก Tesseract ไม่สำเร็จ: {e}"
        return dict(_STATE)
    use = [l for l in ("tha", "eng") if l in langs]
    if not use:
        _STATE["msg"] = "ไม่พบข้อมูลภาษา tha/eng"
        return dict(_STATE)
    _STATE.update(ok=True, lang="+".join(use), msg="tha" if "tha" in use else "ไม่มีภาษาไทย (มีเฉพาะอังกฤษ)")
    return dict(_STATE)


def available() -> bool:
    return configure()["ok"]


def _prep(img):
    from PIL import ImageOps
    img = img.convert("L")
    w, h = img.size
    if max(w, h) < 1600:  # ภาพเล็ก → ขยายเพื่อให้อ่านตัวอักษรไทยแม่นขึ้น
        f = min(3.0, 1600 / max(w, h))
        img = img.resize((int(w * f), int(h * f)))
    return ImageOps.autocontrast(img)


def ocr_image(img) -> str:
    """รับ PIL.Image คืนข้อความ (ว่างถ้า OCR ใช้ไม่ได้/อ่านไม่ได้)"""
    st = configure()
    if not st["ok"]:
        logger.warning(f"[OCR] unavailable: {st['msg']}")
        return ""
    import pytesseract
    try:
        return (pytesseract.image_to_string(_prep(img), lang=st["lang"], config="--psm 6") or "").strip()
    except Exception as e:
        logger.error(f"[OCR] failed: {e}")
        return ""


def ocr_pdf_page(page, dpi: int = 200) -> str:
    """รับหน้า PyMuPDF (fitz) ที่เป็นภาพสแกน คืนข้อความ"""
    try:
        from PIL import Image
        import io
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return ocr_image(img)
    except Exception as e:
        logger.error(f"[OCR] pdf page failed: {e}")
        return ""
