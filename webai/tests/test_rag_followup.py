# -*- coding: utf-8 -*-
"""
Tests for RAG Follow-up Query Rewriting, Contact Answering Rules, and Placeholder Scanner.
Covers:
1. rag_query: is_followup_query, extract_recent_user_turns, build_search_query
2. Query rewriting integration in rag_engine.retrieve_context
3. User turn separation & history bounding
4. Task 2 System prompt rules (factual honesty & partial contact details)
5. Task 3 tools/scan_kb_placeholders scanner logic
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

WEBAI_DIR = Path(__file__).resolve().parent.parent
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

from tests.test_helpers import BaseTestCase
import rag_query
import rag_engine
from tools.scan_kb_placeholders import scan_file_text


class TestRagFollowUp(BaseTestCase):

    def test_is_followup_query_detects_followups(self):
        """Conversational Thai follow-ups should be recognized as needing expansion."""
        follow_ups = [
            "ทำไมจะไม่มีไปเช็คดู",
            "แล้วอีเมลล่ะ",
            "แล้วมีเบอร์ไหม",
            "แล้วอันนั้นล่ะ",
            "อันนี้เท่าไหร่",
            "แล้วใครเป็นผู้ก่อตั้ง",
            "ต้องแนบอะไรไหม",
            "แล้วที่ไหนล่ะ",
            "เช็คดูหน่อย",
            "เบอร์ล่ะ",
            "อีเมลด้วย",
            "มีไหม",
        ]
        for q in follow_ups:
            self.assertTrue(rag_query.is_followup_query(q), f"Expected follow-up for: {q}")

    def test_is_followup_query_keeps_standalone(self):
        """Clear, self-contained questions should NOT be flagged as follow-ups."""
        standalone_queries = [
            "ขอเบอร์ติดต่อของบริษัท ชื่นชอบ จำกัด หน่อยครับ",
            "ระเบียบการลาพักร้อนประจำปีสำหรับพนักงานประจำ",
            "ขั้นตอนการเบิกจ่ายค่ารักษาพยาบาลของบริษัท",
            "นโยบายการทำงานจากที่บ้าน (Work From Home) มีอะไรบ้าง",
        ]
        for q in standalone_queries:
            self.assertFalse(rag_query.is_followup_query(q), f"Should be standalone: {q}")

    def test_extract_recent_user_turns(self):
        """Ensure bot responses and greetings (with various Thai polite particles) are filtered out while user turns are extracted."""
        # 1. Polite greeting with 'ครับ'
        history_krub = [
            {"role": "user", "text": "สวัสดีครับ"},
            {"role": "model", "text": "สวัสดีค่ะ มีอะไรให้น้องพั้นช่วยไหมคะ"},
            {"role": "user", "text": "ขอเบอร์ติดต่อบริษัทหน่อย"},
            {"role": "model", "text": "ในระบบไม่มีข้อมูลเบอร์โทรศัพท์ค่ะ"},
        ]
        user_turns = rag_query.extract_recent_user_turns(history_krub, max_turns=2)
        self.assertEqual(user_turns, ["ขอเบอร์ติดต่อบริษัทหน่อย"])

        # 2. Polite greeting with 'ค่ะ' and informal 'หวัดดี'
        history_ka = [
            {"role": "user", "text": "หวัดดีค่ะ"},
            {"role": "model", "text": "สวัสดีค่ะ"},
            {"role": "user", "text": "ขอระเบียบการลาหน่อย"},
        ]
        user_turns_ka = rag_query.extract_recent_user_turns(history_ka, max_turns=2)
        self.assertEqual(user_turns_ka, ["ขอระเบียบการลาหน่อย"])

        # 3. Addressing forms like 'สวัสดีครับพี่', 'หวัดดี', 'hello', 'hi'
        for greet in ["สวัสดีครับพี่", "หวัดดี", "hello", "hi"]:
            h = [
                {"role": "user", "text": greet},
                {"role": "model", "text": "สวัสดีค่ะ"},
                {"role": "user", "text": "สวัสดิการค่ารักษาพยาบาลเบิกได้เท่าไหร่"},
            ]
            turns = rag_query.extract_recent_user_turns(h, max_turns=2)
            self.assertEqual(turns, ["สวัสดิการค่ารักษาพยาบาลเบิกได้เท่าไหร่"], f"Failed to strip greeting: '{greet}'")

    def test_build_search_query_standalone_unchanged(self):
        """Standalone questions should remain unchanged when built into search queries."""
        q = "ระเบียบการลาพักร้อนประจำปีสำหรับพนักงานประจำ"
        history = [{"role": "user", "text": "ขอเบอร์ติดต่อบริษัทหน่อย"}]
        rewritten = rag_query.build_search_query(q, history=history)
        self.assertEqual(rewritten, q)

    def test_build_search_query_followup_expansion(self):
        """Follow-up questions should be expanded with prior user query context."""
        history = [
            {"role": "user", "text": "ขอเบอร์ติดต่อบริษัทหน่อย"},
            {"role": "model", "text": "ไม่พบข้อมูลเบอร์โทรศัพท์ในระบบค่ะ"},
        ]
        follow_up = "ทำไมจะไม่มีไปเช็คดู"
        rewritten = rag_query.build_search_query(follow_up, history=history)
        self.assertIn("ขอเบอร์ติดต่อบริษัทหน่อย", rewritten)
        self.assertIn("ทำไมจะไม่มีไปเช็คดู", rewritten)

    def test_build_search_query_user_isolation(self):
        """Different users' conversation histories must remain strictly separated."""
        history_user_a = [
            {"role": "user", "text": "ขอเบอร์ติดต่อบริษัท ชื่นชอบ"},
        ]
        history_user_b = [
            {"role": "user", "text": "นโยบายค่าเดินทางไปต่างจังหวัด"},
        ]
        follow_up = "แล้วอีเมลล่ะ"

        query_a = rag_query.build_search_query(follow_up, history=history_user_a)
        query_b = rag_query.build_search_query(follow_up, history=history_user_b)

        self.assertIn("ชื่นชอบ", query_a)
        self.assertNotIn("ต่างจังหวัด", query_a)

        self.assertIn("ต่างจังหวัด", query_b)
        self.assertNotIn("ชื่นชอบ", query_b)

    def test_build_search_query_max_len_bounded(self):
        """Search query length should never exceed max_len."""
        long_prev = "คำถามที่ยาวมาก " * 30
        history = [{"role": "user", "text": long_prev}]
        rewritten = rag_query.build_search_query("แล้วอันนั้นล่ะ", history=history, max_len=100)
        self.assertLessEqual(len(rewritten), 100)

    def test_retrieve_context_uses_rewritten_query(self):
        """retrieve_context should pass the rewritten search query to the hybrid retriever."""
        mock_kb = MagicMock()
        mock_kb.hybrid_query.return_value = [
            {
                "chunk_id": "c1",
                "text": "บริษัท ชื่นชอบ จำกัด ข้อมูลการติดต่อ อีเมล: contact@chuenchob.co.th LINE OA: @chuenchob",
                "name": "ประวัติบริษัท.txt",
                "file_id": "f1",
                "category_id": "cat1",
                "score": 0.85,
            }
        ]

        with patch.object(rag_engine, "_get_kb", return_value=mock_kb), \
             patch.object(rag_engine, "_load_meta", return_value={}):

            history = [{"role": "user", "text": "ขอเบอร์ติดต่อบริษัท ชื่นชอบ จำกัด"}]
            follow_up = "ทำไมจะไม่มีไปเช็คดู"

            ctx, sources = rag_engine.retrieve_context(follow_up, history=history)

            # Check that hybrid_query was called with an expanded query containing "ชื่นชอบ"
            self.assertTrue(mock_kb.hybrid_query.called)
            called_query = mock_kb.hybrid_query.call_args[0][0]
            self.assertIn("ชื่นชอบ", called_query)
            self.assertIn("contact@chuenchob.co.th", ctx)

    def test_system_prompt_rules_included(self):
        """Verify Task 2 system prompt rules exist in chat and LINE prompt sources."""
        chat_path = WEBAI_DIR / "routes" / "chat.py"
        line_path = WEBAI_DIR / "routes" / "line_webhook.py"

        chat_src = chat_path.read_text(encoding="utf-8")
        line_src = line_path.read_text(encoding="utf-8")

        # Must include Comprehensive Contact & Factual Honesty rule and placeholder guidance
        self.assertIn("Comprehensive Contact & Factual Honesty", chat_src)
        self.assertIn("Comprehensive Contact & Factual Honesty", line_src)
        self.assertIn("02-XXX-XXXX", chat_src)
        self.assertIn("02-XXX-XXXX", line_src)

        # Must instruct not to claim the entire system only stores directory/email
        self.assertIn("ในระบบมีแค่", chat_src)
        self.assertIn("ในระบบมีแค่", line_src)

    def test_scan_kb_placeholders_patterns(self):
        """Placeholder scanner should identify sample phone numbers, emails, and brackets."""
        sample_doc = (
            "1. ข้อมูลทั่วไป บริษัท ตัวอย่าง จำกัด\n"
            "2. เบอร์ติดต่อ: 02-XXX-XXXX\n"
            "3. อีเมลฝ่ายขาย: contact@example.com\n"
            "4. ที่อยู่: [ใส่ที่อยู่สำนักงานใหญ่ที่นี่]\n"
            "5. ผู้จัดการ: นาย สมมุติ รักงาน\n"
            "6. วันที่เริ่มใช้: วัน/เดือน/ปี\n"
        )
        findings = scan_file_text("sample.txt", sample_doc)
        rules_found = {f["rule"] for f in findings}

        self.assertIn("SAMPLE_COMPANY_NAME", rules_found)
        self.assertIn("PHONE_PLACEHOLDER", rules_found)
        self.assertIn("EMAIL_PLACEHOLDER", rules_found)
        self.assertIn("BRACKET_INSTRUCTION", rules_found)
        self.assertIn("SAMPLE_PERSON_NAME", rules_found)
        self.assertIn("DATE_PLACEHOLDER", rules_found)

        # Verify line numbers
        phone_finding = next(f for f in findings if f["rule"] == "PHONE_PLACEHOLDER")
        self.assertEqual(phone_finding["line"], 2)
        self.assertEqual(phone_finding["matched"], "02-XXX-XXXX")


if __name__ == "__main__":
    unittest.main()
