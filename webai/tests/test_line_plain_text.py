# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("FLASK_SECRET_KEY", "x" * 24)


def _fn():
    import importlib
    import routes.line_webhook as LW
    return LW.line_plain_text


def test_bold_markers_removed():
    f = _fn()
    assert f("ที่อยู่คือ **123 ถนนพหลโยธิน** ค่ะ") == "ที่อยู่คือ 123 ถนนพหลโยธิน ค่ะ"
    assert "**" not in f("• **ระยะเวลา** – 12 เดือน\n• **ข้อยกเว้น** – ใช้ผิดวิธี")


def test_bullets_and_headings():
    f = _fn()
    assert f("# หัวข้อ\n* ข้อหนึ่ง\n- ข้อสอง") == "หัวข้อ\n• ข้อหนึ่ง\n• ข้อสอง"


def test_plain_text_untouched_and_empty_safe():
    f = _fn()
    assert f("สวัสดีค่ะ 2*3=6 ครับ") == "สวัสดีค่ะ 2*3=6 ครับ"
    assert f("") == "" and f(None) is None
