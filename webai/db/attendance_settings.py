# -*- coding: utf-8 -*-
"""
db/attendance_settings.py — ตั้งค่าการเช็คชื่อเข้างาน "ต่อองค์กร"

เดิม พิกัดสำนักงาน/รัศมี/เวลาเข้างาน มาจากตัวแปรสภาพแวดล้อมทั้งระบบ (ค่าเริ่มต้น = กลางกรุงเทพ รัศมี 1 กม.)
ทำให้ทุกองค์กรใช้พิกัดเดียวกันและพนักงานจริงถูกตัดสินว่า "นอกพื้นที่" เกือบทั้งหมด

ตอนนี้: แต่ละองค์กรตั้งเองได้ ถ้ายังไม่ตั้ง (configured=False) ระบบจะ "ไม่ตัดสินว่านอกพื้นที่" แทนที่จะใช้พิกัดกรุงเทพมั่วๆ
"""
import os

from db.connection import _get_conn

DEFAULT_START = (9, 15)


def _ensure(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS org_attendance_settings (
            org_id INTEGER PRIMARY KEY,
            office_lat REAL,
            office_lng REAL,
            radius_m REAL DEFAULT 200,
            work_start_h INTEGER DEFAULT 9,
            work_start_m INTEGER DEFAULT 15,
            updated_by TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _env_start():
    try:
        return int(os.getenv("WORK_START_HOUR", DEFAULT_START[0])), int(os.getenv("WORK_START_MINUTE", DEFAULT_START[1]))
    except ValueError:
        return DEFAULT_START


def get_settings(org_id) -> dict:
    """คืนค่าตั้งของ org; configured=False เมื่อยังไม่ได้ตั้งพิกัด (ใช้เวลาเข้างานจาก env เป็นค่าเริ่มต้น)"""
    h, m = _env_start()
    base = {"configured": False, "office_lat": None, "office_lng": None, "radius_m": 200.0, "work_start_h": h, "work_start_m": m}
    if org_id is None:
        return base
    conn = _get_conn()
    try:
        _ensure(conn)
        r = conn.execute("SELECT office_lat, office_lng, radius_m, work_start_h, work_start_m FROM org_attendance_settings WHERE org_id = ?",
                         (int(org_id),)).fetchone()
    finally:
        conn.close()
    if not r:
        return base
    lat, lng, rad, sh, sm = r
    return {
        "configured": lat is not None and lng is not None,
        "office_lat": lat, "office_lng": lng,
        "radius_m": float(rad or 200), "work_start_h": int(sh if sh is not None else h), "work_start_m": int(sm if sm is not None else m),
    }


def validate(data: dict):
    """คืน (clean_dict, error_text)"""
    try:
        lat = float(data.get("office_lat"))
        lng = float(data.get("office_lng"))
    except (TypeError, ValueError):
        return None, "พิกัดสำนักงานไม่ถูกต้อง"
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None, "พิกัดอยู่นอกช่วงที่เป็นไปได้"
    try:
        radius = float(data.get("radius_m", 200))
    except (TypeError, ValueError):
        return None, "รัศมีไม่ถูกต้อง"
    if not (20 <= radius <= 20000):
        return None, "รัศมีต้องอยู่ระหว่าง 20 ถึง 20,000 เมตร (GPS ในอาคารคลาดเคลื่อนได้หลายสิบเมตร)"
    st = str(data.get("work_start", "09:15"))
    try:
        hh, mm = [int(x) for x in st.split(":")[:2]]
        assert 0 <= hh <= 23 and 0 <= mm <= 59
    except Exception:
        return None, "เวลาเข้างานต้องเป็นรูปแบบ HH:MM"
    return {"office_lat": lat, "office_lng": lng, "radius_m": radius, "work_start_h": hh, "work_start_m": mm}, None


def save_settings(org_id: int, clean: dict, updated_by: str):
    conn = _get_conn()
    try:
        _ensure(conn)
        conn.execute(
            "INSERT OR REPLACE INTO org_attendance_settings (org_id, office_lat, office_lng, radius_m, work_start_h, work_start_m, updated_by, updated_at) "
            "VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (int(org_id), clean["office_lat"], clean["office_lng"], clean["radius_m"], clean["work_start_h"], clean["work_start_m"], updated_by))
        conn.commit()
    finally:
        conn.close()


def month_summary(org_id: int, ym: str) -> dict:
    """สรุปการเช็คชื่อรายเดือนทั้งองค์กร: รวม / รายคน / รายวัน (ใช้กับแท็บ 'เวลาเข้างาน' ในหน้าจัดการองค์กร)"""
    from collections import defaultdict
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT username, check_date, check_time, check_type, status FROM time_attendance "
            "WHERE org_id = ? AND check_date LIKE ? ORDER BY check_date, check_time", (int(org_id), ym + "-%")).fetchall()
        members = conn.execute(
            "SELECT COUNT(*) FROM organization_members WHERE organization_id = ?", (int(org_id),)).fetchone()[0]
    finally:
        conn.close()

    def secs(t):
        try:
            p = [int(x) for x in str(t).split(":")[:3]] + [0, 0]
            return p[0] * 3600 + p[1] * 60 + p[2]
        except Exception:
            return None

    per = defaultdict(lambda: {"days": {}, })
    for u, d, t, ty, st in rows:
        day = per[u]["days"].setdefault(d, {"in": None, "out": None, "status": None})
        if ty == "check_in" and day["in"] is None:
            day["in"], day["status"] = t, st
        elif ty == "check_out":
            day["out"] = t
    employees, by_day = [], defaultdict(lambda: {"present": 0, "late": 0, "outside": 0})
    tot = {"checkins": 0, "on_time": 0, "late": 0, "outside": 0, "hours": 0.0}
    for u, info in per.items():
        e = {"username": u, "days": 0, "on_time": 0, "late": 0, "outside": 0, "hours": 0.0}
        for d, v in info["days"].items():
            if v["in"] is None:
                continue
            e["days"] += 1
            st = v["status"] or "on_time"
            if st == "late":
                e["late"] += 1
            elif st == "outside_geofence":
                e["outside"] += 1
            else:
                e["on_time"] += 1
            a, b = secs(v["in"]), secs(v["out"]) if v["out"] else None
            if a is not None and b is not None and b > a:
                e["hours"] += (b - a) / 3600.0
            bd = by_day[d]
            bd["present"] += 1
            bd["late"] += 1 if st == "late" else 0
            bd["outside"] += 1 if st == "outside_geofence" else 0
        e["hours"] = round(e["hours"], 1)
        tot["checkins"] += e["days"]
        tot["on_time"] += e["on_time"]
        tot["late"] += e["late"]
        tot["outside"] += e["outside"]
        tot["hours"] += e["hours"]
        employees.append(e)
    employees.sort(key=lambda x: (-x["late"], -x["days"], x["username"]))
    tot["hours"] = round(tot["hours"], 1)
    tot["people"] = len(employees)
    tot["members"] = members
    tot["on_time_pct"] = round(100 * tot["on_time"] / tot["checkins"]) if tot["checkins"] else 0
    tot["avg_hours_per_day"] = round(tot["hours"] / tot["checkins"], 1) if tot["checkins"] else 0
    days = [{"date": d, **v} for d, v in sorted(by_day.items())]
    return {"month": ym, "totals": tot, "employees": employees, "days": days}
