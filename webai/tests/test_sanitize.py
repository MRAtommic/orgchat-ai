# -*- coding: utf-8 -*-
"""กรองป้ายชื่อที่ผู้ใช้ตั้งเอง (ชื่อแสดง/ชื่อห้อง/แผนก) ก่อนบันทึก — กัน stored XSS ที่ต้นทาง"""
import pytest

import database
from db.sanitize import clean_label

PAYLOAD = '<img src=x onerror="alert(1)">'


@pytest.mark.parametrize("raw,expected", [
    (None, None),
    ("สมชาย ใจดี", "สมชาย ใจดี"),
    ("  a   b \n c ", "a b c"),
    ("<b>x</b>", "bx/b"),
    (PAYLOAD, 'img src=x onerror="alert(1)"'),
    ("a‮b​c\x00d", "a b c d"),     # ตัวสลับทิศทาง/ล่องหน/ควบคุม
])
def test_clean_label(raw, expected):
    assert clean_label(raw) == expected


def test_clean_label_length():
    assert len(clean_label("x" * 500, 80)) == 80


def test_no_angle_brackets_ever():
    for s in ["<<>>", "a<script>b", "</script>", "<img>"]:
        out = clean_label(s)
        assert "<" not in out and ">" not in out


def test_room_name_sanitized_on_create_and_rename():
    database.init_db()
    database.admin_create_user("sx_owner", "Passw0rd!x", role="user", email="sx@example.com")
    rid = database.create_room("Team " + PAYLOAD, "sx_owner", ["sx_owner"], org_id=1)
    conn = database._get_conn()
    try:
        name = conn.execute("SELECT name FROM chat_rooms WHERE id = ?", (rid,)).fetchone()[0]
    finally:
        conn.close()
    assert "<" not in name and ">" not in name and name.startswith("Team")
    database.update_group_profile(rid, name="New " + PAYLOAD)
    conn = database._get_conn()
    try:
        name = conn.execute("SELECT name FROM chat_rooms WHERE id = ?", (rid,)).fetchone()[0]
    finally:
        conn.close()
    assert "<" not in name and name.startswith("New")


def test_display_name_and_department_sanitized():
    database.init_db()
    database.admin_create_user("sx_user", "Passw0rd!x", role="user", email="sx2@example.com", display_name="Hi " + PAYLOAD)
    database.update_user_profile("sx_user", display_name="Yo " + PAYLOAD, department="Dept " + PAYLOAD)
    conn = database._get_conn()
    try:
        row = conn.execute("SELECT display_name, department FROM user_profiles WHERE username = ?", ("sx_user",)).fetchone()
    finally:
        conn.close()
    assert row and all("<" not in (v or "") and ">" not in (v or "") for v in row), row
