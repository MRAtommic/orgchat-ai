# -*- coding: utf-8 -*-
"""
tz_fix.py — แก้ปัญหา "เวลาในเซิร์ฟเวอร์ช้ากว่าจริง 7 ชั่วโมง" บน Windows

สาเหตุ: .env ตั้ง TZ=Asia/Bangkok (ชื่อแบบ IANA) แล้วแอปโหลดเข้า os.environ ก่อนมีการอ่านนาฬิกาครั้งแรก
        ไลบรารีภาษา C ของ Windows (UCRT) อ่านรูปแบบนี้ไม่ออก จึงถือว่าเป็น UTC → datetime.now() ได้เวลา UTC
        ผลคือเช็คชื่อบันทึกเวลา/ตัดสินสายผิด, นัดหมายและตัวเตือนเลื่อน 7 ชม., สรุปประจำวันตรงเวลาผิด ฯลฯ

วิธีแก้: แปลง TZ ที่เป็นชื่อ IANA เป็นรูปแบบ POSIX ที่ Windows เข้าใจ (เช่น LOCAL-7) แล้วสั่งให้ไลบรารีอ่านค่าใหม่ทันที
        เรียกซ้ำได้ (idempotent) และไม่ทำอะไรบนระบบที่ไม่ใช่ Windows
"""
import os
import sys


def _offset_hours(tz_name: str):
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        off = datetime.now(ZoneInfo(tz_name)).utcoffset()
        return off.total_seconds() / 3600.0
    except Exception:
        return 7.0 if tz_name == "Asia/Bangkok" else None   # ไม่มีฐานข้อมูลโซนเวลา → รู้จักเฉพาะไทย


def apply() -> str:
    """คืนค่า TZ ที่ใช้อยู่หลังแก้ (เพื่อบันทึกล็อก/ทดสอบ)"""
    tz = os.environ.get("TZ", "")
    if sys.platform != "win32" or "/" not in tz:
        return tz
    hours = _offset_hours(tz)
    if hours is None:
        os.environ.pop("TZ", None)           # ไม่รู้จักโซนนี้ → ใช้โซนของระบบปฏิบัติการแทน (ดีกว่า UTC เงียบๆ)
    else:
        # รูปแบบ POSIX กลับเครื่องหมาย: UTC+7 เขียนเป็น "LCL-7" (ชื่อโซนต้องยาว 3 ตัวอักษรพอดี ไม่งั้น CRT อ่านไม่ออก)
        os.environ["TZ"] = f"LCL{-hours:+.0f}" if hours == int(hours) else f"LCL{-hours:+.2f}"
    try:
        import ctypes
        ctypes.CDLL("ucrtbase")._tzset()      # บังคับให้ CRT อ่าน TZ ใหม่ (Python ไม่มี time.tzset บน Windows)
    except Exception:
        pass
    return os.environ.get("TZ", "")
