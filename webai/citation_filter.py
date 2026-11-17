# -*- coding: utf-8 -*-
"""เลือก "แหล่งอ้างอิง" ที่ใช้ตอบจริง

เดิมระบบแนบไฟล์ทั้งหมดที่ค้นเจอ (top-k) เป็นแหล่งอ้างอิงทุกครั้ง แม้คำตอบมาจากไฟล์เดียว → ผู้ใช้เห็นไฟล์ที่ไม่เกี่ยวข้องและไม่น่าเชื่อถือ
ที่นี่เทียบ "ข้อความคำตอบ" กับ "เนื้อหาท่อนที่ถูกดึงมาของแต่ละไฟล์" แล้วเก็บเฉพาะไฟล์ที่เนื้อหาปรากฏในคำตอบจริง

วิธีทำ (ไม่ต้องเรียก AI เพิ่ม): ตัดข้อความเป็นชิงเกิล 4 ตัวอักษร (ใช้ได้กับภาษาไทยที่ไม่มีช่องว่างคั่นคำ)
ถ่วงน้ำหนักชิงเกิลที่พบในหลายไฟล์ให้น้อยลง (คำทั่วไปอย่าง "ของบริษัท" ไม่ควรทำให้ไฟล์ไหนดูเกี่ยวข้อง) แล้วให้คะแนนแต่ละไฟล์
"""
import re

_NEG_PHRASES = ("ยังไม่พบข้อมูล", "ไม่พบข้อมูล", "ไม่มีข้อมูล", "ไม่พบเบอร์", "ไม่มีการเก็บ", "ไม่ได้เก็บ",
                "ยังไม่มีรายละเอียด", "ไม่มีรายละเอียด", "ไม่พบรายละเอียด", "ยังไม่พบ", "ไม่ปรากฏ", "ไม่มีในระบบ", "ไม่มีในเอกสาร", "ไม่พบในระบบ")
_NEG_WINDOW = 220      # วลีปฏิเสธต้องอยู่ช่วงต้นคำตอบ (คำตอบที่ช่วยได้จริงแล้วค่อยพูดถึงสิ่งที่ยังไม่มี ไม่ควรถูกตัดแหล่งอ้างอิงทิ้ง)
_STRIP = re.compile(r"[^0-9a-zA-Z฀-๿]+")
N = 4                  # ความยาวชิงเกิล
MIN_TOP_SCORE = 2.0    # คะแนนสูงสุดต้องถึงเท่านี้ ไม่งั้นถือว่าคำตอบไม่ได้มาจากเอกสาร
KEEP_RATIO = 0.5       # เก็บไฟล์อื่นที่คะแนน ≥ 50% ของไฟล์ที่ดีที่สุด


class SourceRef(dict):
    """dict ธรรมดา (serialize เป็น JSON/DB ได้เหมือนเดิม) ที่พกเนื้อหาท่อนไว้ใน attribute `.snippet` ซึ่ง JSON ไม่เห็น"""
    snippet = ""


def _norm(s: str) -> str:
    return _STRIP.sub("", (s or "").lower())


def _shingles(s: str, n: int = N) -> set:
    s = _norm(s)
    return {s[i:i + n] for i in range(0, max(0, len(s) - n + 1))}


def select_cited_sources(answer: str, sources, max_n: int = 3):
    """คืนเฉพาะแหล่งที่ถูกใช้ตอบจริง (ลำดับตามความเกี่ยวข้อง สูงสุด max_n ไฟล์)

    - ไม่มีแหล่ง / คำตอบเป็นแนว "ไม่พบข้อมูล" → []
    - แหล่งที่ไม่มีเนื้อหาให้เทียบ (เช่นโหมดแนบไฟล์โดยตรง) → คืนตามเดิม
    - ไม่มีไฟล์ไหนปรากฏในคำตอบเลย (คำตอบทั่วไปจากความรู้ของโมเดล) → []
    """
    try:
        srcs = [s for s in (sources or []) if isinstance(s, dict)]
        if not srcs:
            return []
        ans = answer or ""
        if any(p in ans[:_NEG_WINDOW] for p in _NEG_PHRASES):
            return []
        if not any(getattr(s, "snippet", "") for s in srcs):
            return srcs[:max_n]          # ประเมินไม่ได้ → ไม่เดา คงของเดิม (ตัดจำนวน)

        # รวมเนื้อหาทุกท่อนของไฟล์เดียวกัน (หลายตำแหน่ง/หลายท่อน → นับเป็นไฟล์เดียว)
        files = {}
        for s in srcs:
            key = (s.get("file_id") or "", s.get("name") or s.get("source") or "")
            f = files.setdefault(key, {"entries": [], "text": ""})
            f["entries"].append(s)
            f["text"] += "\n" + getattr(s, "snippet", "")
        sets = {k: _shingles(v["text"]) for k, v in files.items()}
        A = _shingles(ans)
        if not A:
            return []
        df = {}
        for st in sets.values():
            for g in st & A:
                df[g] = df.get(g, 0) + 1
        scores = {k: sum(1.0 / df[g] for g in (st & A)) for k, st in sets.items()}
        top = max(scores.values())
        if top < MIN_TOP_SCORE:
            return []
        order = sorted(scores, key=lambda k: -scores[k])
        chosen = [k for k in order if scores[k] >= KEEP_RATIO * top][:max_n]
        out = []
        for k in chosen:
            out.extend(files[k]["entries"][:1])       # หนึ่งรายการต่อไฟล์ (ตำแหน่งแรกที่ค้นเจอ)
        return out
    except Exception:
        return [s for s in (sources or []) if isinstance(s, dict)][:max_n]   # พังก็ไม่ทำให้คำตอบพัง
