# -*- coding: utf-8 -*-
"""
db/sanitize.py — ทำความสะอาด "ป้ายชื่อ" ที่ผู้ใช้ตั้งเอง (ชื่อแสดง, ชื่อห้องแชท, แผนก, ตำแหน่ง ฯลฯ) ก่อนบันทึก

ทำไม: ชื่อเหล่านี้ถูกแสดงให้ผู้ใช้คนอื่นเห็นในหน้าเว็บ ถ้าตั้งเป็น <img onerror=...> แล้วหน้าเว็บบางจุดลืม escape
จะกลายเป็น stored XSS (รันสคริปต์ในเซสชันของเพื่อนร่วมองค์กร รวมถึงแอดมิน). ฝั่งเว็บ escape แล้ว แต่ต้องมีชั้นที่สองที่ต้นทาง
(defense in depth) — ชื่อคนไม่ควรมี < > อยู่แล้ว
"""
import re

_CTRL = re.compile(r"[\x00-\x1f\x7f​-‏‪-‮⁦-⁩]")   # ตัวควบคุม + ตัวอักษรล่องหน/สลับทิศทาง
_BAD = re.compile(r"[<>]")
_WS = re.compile(r"\s+")


def clean_label(value, maxlen: int = 80):
    """None → None; อย่างอื่น → สตริงที่ไม่มี < > ตัวควบคุม/อักขระล่องหน, ยุบช่องว่าง, ตัดความยาว"""
    if value is None:
        return None
    s = _CTRL.sub(" ", str(value))
    s = _BAD.sub("", s)
    s = _WS.sub(" ", s).strip()
    return s[:maxlen]
