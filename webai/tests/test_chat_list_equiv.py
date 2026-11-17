# -*- coding: utf-8 -*-
"""รายการแชท (get_rooms_for_user) เขียนใหม่ให้เร็ว — ต้องได้ผลเหมือนคำสั่งเก่าทุกประการ: เทียบกับ SQL เดิมบนข้อมูลสุ่ม"""
import random

import pytest

import database

OLD_ROOMS = """
    SELECT r.id, r.name, r.avatar_url, r.owner,
           m.text as last_msg, m.timestamp as last_time, m.username as last_sender,
           m.attachments as last_attachments
    FROM chat_rooms r
    JOIN room_members rm ON r.id = rm.room_id
    LEFT JOIN (
        SELECT room_id, text, attachments, timestamp, username,
               ROW_NUMBER() OVER (PARTITION BY room_id ORDER BY id DESC) as rn
        FROM room_messages
    ) m ON r.id = m.room_id AND m.rn = 1
    WHERE rm.username = ? COLLATE NOCASE
      AND (r.organization_id = ? OR r.organization_id IS NULL)
    ORDER BY COALESCE(m.timestamp, '1970-01-01') DESC
"""

OLD_DMS = """
    SELECT contact, text as last_msg, timestamp as last_time, sender as last_sender, attachments as last_attachments
    FROM (
        SELECT CASE WHEN sender = ? COLLATE NOCASE THEN recipient ELSE sender END as contact,
               text, attachments, timestamp, sender,
               ROW_NUMBER() OVER (PARTITION BY CASE WHEN sender = ? COLLATE NOCASE THEN recipient ELSE sender END ORDER BY id DESC) as rn
        FROM private_messages
        WHERE sender = ? COLLATE NOCASE OR recipient = ? COLLATE NOCASE
    ) pm
    WHERE rn = 1
      AND (
          pm.contact = 'AI-Assistant'
          OR EXISTS (
              SELECT 1 FROM organization_members om1
              JOIN organization_members om2 ON om1.organization_id = om2.organization_id
              WHERE om1.username = ? COLLATE NOCASE
                AND om2.username = pm.contact COLLATE NOCASE
                AND om1.organization_id = ?
          )
      )
    ORDER BY timestamp DESC
"""


@pytest.fixture(scope="module")
def world():
    database.init_db()
    users = [f"eq{i}" for i in range(6)]
    for u in users:
        database.admin_create_user(u, "Passw0rd!x", role="user", email=u + "@example.com")
    oid, _ = database.create_organization("EqOrg", users[0])
    for u in users[1:]:
        database.add_org_member(oid, u, "member", users[0])
    outsider = "eq_out"
    database.admin_create_user(outsider, "Passw0rd!x", role="user", email="o@example.com")
    rng = random.Random(7)
    rooms = [database.create_room(f"R{i}", users[0], rng.sample(users, 3) + [users[0]], org_id=oid) for i in range(5)]
    conn = database._get_conn()
    base = 1_700_000_000
    for i in range(600):
        rid = rng.choice(rooms)
        conn.execute("INSERT INTO room_messages (room_id, username, text, timestamp) VALUES (?,?,?,datetime(?, 'unixepoch'))",
                     (rid, rng.choice(users), f"m{i}", base + rng.randint(0, 100000)))
    pool = users + [outsider, "AI-Assistant"]
    for i in range(900):
        a, b = rng.sample(pool, 2)
        conn.execute("INSERT INTO private_messages (sender, recipient, text, organization_id, timestamp) VALUES (?,?,?,?,datetime(?, 'unixepoch'))",
                     (a, b, f"d{i}", oid, base + rng.randint(0, 100000)))
    conn.commit()
    conn.close()
    return {"users": users, "oid": oid, "rooms": rooms}


def _old(username, oid):
    conn = database._get_conn()
    try:
        rooms = conn.execute(OLD_ROOMS, (username, oid)).fetchall()
        dms = conn.execute(OLD_DMS, (username, username, username, username, username, oid)).fetchall()
    finally:
        conn.close()
    return [(r[0], r[4], r[5], r[6]) for r in rooms], [(d[0], d[1], d[2], d[3]) for d in dms]


def test_same_rooms_and_contacts_as_the_old_query(world):
    for u in world["users"] + ["EQ0", "Eq3"]:           # รวมตัวพิมพ์ใหญ่/เล็กปนกัน (COLLATE NOCASE)
        new = database.get_rooms_for_user(u, org_id=world["oid"])
        old_rooms, old_dms = _old(u, world["oid"])
        assert [(r["id"], r["last_msg"], r["last_time"], r["last_sender"]) for r in new["rooms"]] == \
            [(rid, database.format_chat_message_preview(txt, None) if hasattr(database, "format_chat_message_preview") else txt, ts, snd) for rid, txt, ts, snd in old_rooms], u
        assert [(c["id"], c["last_time"], c["last_sender"]) for c in new["contacts"]] == [(c, ts, snd) for c, _t, ts, snd in old_dms], u


def test_outsider_matches_old_query_and_has_no_org_contacts(world):
    new = database.get_rooms_for_user("eq_out", org_id=world["oid"])
    old_rooms, old_dms = _old("eq_out", world["oid"])
    assert [r["id"] for r in new["rooms"]] == [r[0] for r in old_rooms]        # (ห้องส่วนกลางของระบบ: ทุกคนเป็นสมาชิกอยู่แล้ว ทั้งเก่า/ใหม่ตรงกัน)
    assert not any(r["id"] in world["rooms"] for r in new["rooms"])            # แต่ไม่เห็นห้องของคนอื่นในองค์กร
    assert all(c["id"] == "AI-Assistant" for c in new["contacts"])


def test_cheap_room_helpers(world):
    rid = world["rooms"][0]
    members = database.get_room_ids_for_user("eq0")
    assert isinstance(members, list)
    conn = database._get_conn()
    try:
        member = conn.execute("SELECT username FROM room_members WHERE room_id = ?", (rid,)).fetchone()[0]
    finally:
        conn.close()
    assert database.is_room_member(rid, member, world["oid"]) is True
    assert database.is_room_member(rid, member.upper(), world["oid"]) is True
    assert database.is_room_member(rid, "eq_out", world["oid"]) is False
    assert database.is_room_member(rid, member, 99999) is False
    assert database.get_room_name(rid).startswith("R")
