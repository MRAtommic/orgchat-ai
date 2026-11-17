# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from citation_filter import SourceRef, select_cited_sources  # noqa: E402


def ref(name, text, loc="Document", fid=None):
    r = SourceRef({"file_id": fid or name, "name": name, "location": loc, "department": "General", "type": "txt"})
    r.snippet = text
    return r


ADDR = "ที่อยู่บริษัท เชนชอบ จำกัด 123 ถนนพหลโยธิน แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร 10900 โทรศัพท์ 02-XXX-XXXX"
IT = "นโยบายความปลอดภัยด้านไอที พนักงานต้องตั้งรหัสผ่านอย่างน้อย 10 ตัวอักษร ห้ามใช้รหัสผ่านร่วมกัน ห้ามนำข้อมูลลูกค้าออกนอกระบบของบริษัท"
STAFF = "รายชื่อพนักงาน ฟิว วีรภัทร ชื่นชอบ ตำแหน่ง IT เบอร์โทร 063-653-4337 โด ธนากร ธนบวรพล เบอร์โทร 085-677-4443"
LEAVE = "ระเบียบการลา พนักงานมีสิทธิ์ลาพักร้อนปีละ 10 วัน ต้องยื่นคำขอล่วงหน้าอย่างน้อย 3 วันทำงาน ลาป่วยเกิน 2 วันต้องแนบใบรับรองแพทย์"


def make():
    return [ref("hm1.pdf", ADDR, "Page 1"), ref("นโยบายIT.txt", IT), ref("รายชื่อ.txt", STAFF), ref("ระเบียบการลา.txt", LEAVE)]


def names(x):
    return [s["name"] for s in x]


def test_single_source_answer_cites_only_that_file():
    ans = "พี่คะ บริษัทเชนชอบ จำกัด มีที่อยู่ดังนี้ 123 ถนนพหลโยธิน แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร 10900"
    assert names(select_cited_sources(ans, make())) == ["hm1.pdf"]


def test_answer_using_two_files_cites_both_not_the_others():
    ans = "พนักงานต้องตั้งรหัสผ่านอย่างน้อย 10 ตัวอักษร และห้ามใช้รหัสผ่านร่วมกัน ส่วนสิทธิ์ลาพักร้อนคือปีละ 10 วัน ต้องยื่นคำขอล่วงหน้าอย่างน้อย 3 วันทำงาน"
    got = names(select_cited_sources(ans, make()))
    assert set(got) == {"นโยบายIT.txt", "ระเบียบการลา.txt"}


def test_answer_not_from_documents_cites_nothing():
    assert select_cited_sources("สวัสดีค่ะพี่ วันนี้อากาศดีมาก แนะนำให้ดื่มน้ำเยอะๆ นะคะ", make()) == []


def test_not_found_answer_cites_nothing():
    assert select_cited_sources("ขออภัยค่ะ ยังไม่พบข้อมูลที่ตรงกับคำถามของพี่ในระบบ", make()) == []


def test_sources_without_snippet_are_kept_as_is():
    plain = [{"file_id": "a", "name": "a.pdf"}, {"file_id": "b", "name": "b.pdf"}]
    assert names(select_cited_sources("อะไรก็ได้", plain)) == ["a.pdf", "b.pdf"]


def test_same_file_many_chunks_counts_once():
    srcs = [ref("hm1.pdf", ADDR[:60], "Page 1", fid="h"), ref("hm1.pdf", ADDR[60:], "Page 2", fid="h"), ref("นโยบายIT.txt", IT)]
    ans = "ที่อยู่บริษัท เชนชอบ จำกัด 123 ถนนพหลโยธิน แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร 10900"
    got = select_cited_sources(ans, srcs)
    assert names(got) == ["hm1.pdf"]


def test_result_is_json_serializable_and_snippet_is_not_leaked():
    got = select_cited_sources("123 ถนนพหลโยธิน แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร 10900 ที่อยู่บริษัท เชนชอบ จำกัด", make())
    dumped = json.dumps(got, ensure_ascii=False)
    assert "snippet" not in dumped and "ถนนพหลโยธิน" not in dumped


def test_empty_inputs():
    assert select_cited_sources("x", []) == []
    assert select_cited_sources("", make()) == []
    assert select_cited_sources(None, None) == []


def test_more_no_information_phrases_cite_nothing():
    for ans in ("พี่คะ ยังไม่มีรายละเอียดสินค้าจริงของถุงเท้ารุ่นนี้ในระบบค่ะ ข้อมูลที่พบคือถูกใช้เป็นตัวอย่างคำถามเท่านั้น",
                "ตอนนี้ยังไม่พบรายละเอียดเรื่องนี้ในเอกสารค่ะ", "เรื่องนี้ไม่ปรากฏในเอกสารที่มีอยู่ค่ะ"):
        assert select_cited_sources(ans, make()) == []


def test_helpful_answer_that_mentions_a_gap_later_keeps_its_source():
    ans = ("พี่คะ บริษัทเชนชอบ จำกัด มีที่อยู่ดังนี้ 123 ถนนพหลโยธิน แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร 10900 ค่ะ " + "ข้อมูลเพิ่มเติมสำหรับการติดต่อ " * 6 +
           " อย่างไรก็ตามยังไม่มีรายละเอียดเรื่องแผนที่ค่ะ")
    assert names(select_cited_sources(ans, make())) == ["hm1.pdf"]
