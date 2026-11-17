# -*- coding: utf-8 -*-
"""
test_large_doc_ingest.py
Verifies that documents producing > 20 chunks (multi-batch ingestion)
correctly preserve all chunks with unique sequential IDs without overwriting
early batches.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import rag_engine


class TestLargeDocIngest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.orig_data_root = rag_engine._DATA_ROOT
        self.orig_fallback = rag_engine.FALLBACK_VECTOR_JSON
        self.orig_meta_file = rag_engine.META_FILE
        self.orig_kb = rag_engine._kb

        # Setup isolated temp vector environment
        test_root = Path(self.temp_dir.name)
        rag_engine._DATA_ROOT = test_root
        rag_engine.FALLBACK_VECTOR_JSON = test_root / "test_fallback.json"
        rag_engine.META_FILE = test_root / "test_meta.json"
        rag_engine._kb = None

    def tearDown(self):
        rag_engine._DATA_ROOT = self.orig_data_root
        rag_engine.FALLBACK_VECTOR_JSON = self.orig_fallback
        rag_engine.META_FILE = self.orig_meta_file
        rag_engine._kb = self.orig_kb
        self.temp_dir.cleanup()

    def test_multi_batch_add_chunks_no_overwrite(self):
        """Verify that add_chunks with start_idx preserves all chunks across batches."""
        # Create dummy embedding function
        dummy_ef = lambda texts: [[0.1] * 384 for _ in texts]
        store = rag_engine.PurePythonVectorStore(dummy_ef, rag_engine.FALLBACK_VECTOR_JSON)
        
        kb = rag_engine.KnowledgeBase.__new__(rag_engine.KnowledgeBase)
        kb.collection = store
        kb.api_key = "test_key"
        kb.provider = "test"
        kb._ephemeral = True

        # Generate 55 chunks (3 batches: 20, 20, 15)
        total_chunks = 55
        chunks = [f"Chunk content number {i} with key data from page {i // 2 + 1}" for i in range(total_chunks)]
        metas = [{"location": f"Page {i // 2 + 1}", "organization_id": 1} for i in range(total_chunks)]
        file_id = "test_file_large_123"

        batch_size = 20
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_metas = metas[i : i + batch_size]
            kb.add_chunks(batch_chunks, source_name="large_doc.pdf", file_id=file_id, metadatas=batch_metas, start_idx=i)

        # Check total stored count
        self.assertEqual(store.count(), 55, "All 55 chunks must be stored without overwriting!")

        # Verify all chunk IDs are unique and sequential from chunk_0 to chunk_54
        stored_ids = [item["id"] for item in store.data]
        expected_ids = [f"{file_id}_chunk_{i}" for i in range(55)]
        self.assertEqual(sorted(stored_ids), sorted(expected_ids), "IDs must be sequential and distinct across batches!")

        # Verify first batch (page 1) and last batch (page 28) both exist
        page_1_chunks = [item for item in store.data if item["metadata"].get("location") == "Page 1"]
        page_28_chunks = [item for item in store.data if item["metadata"].get("location") == "Page 28"]
        self.assertGreater(len(page_1_chunks), 0, "Page 1 chunks must NOT be overwritten!")
        self.assertGreater(len(page_28_chunks), 0, "Page 28 chunks must exist!")

    def test_ingest_file_multi_batch_end_to_end(self):
        """Verify that ingest_file correctly retains all chunks when ingesting a 45-chunk document."""
        from unittest.mock import patch

        dummy_ef = lambda texts: [[0.05] * 384 for _ in texts]
        store = rag_engine.PurePythonVectorStore(dummy_ef, rag_engine.FALLBACK_VECTOR_JSON)

        mock_kb = rag_engine.KnowledgeBase.__new__(rag_engine.KnowledgeBase)
        mock_kb.collection = store
        mock_kb.api_key = "test_key"
        mock_kb.provider = "test"
        mock_kb._ephemeral = True

        rag_engine._kb = mock_kb

        # Create dummy text file
        test_file = Path(self.temp_dir.name) / "curriculum_100pages.txt"
        test_file.write_text("dummy content", encoding="utf-8")

        total_chunks = 45
        mock_chunks = [f"Section {i} text describing course curriculum on page {i + 1}" for i in range(total_chunks)]
        mock_metas = [{"location": f"Page {i + 1}"} for i in range(total_chunks)]

        with patch.object(rag_engine.FileProcessor, "parse", return_value=(mock_chunks, mock_metas)):
            res = rag_engine.ingest_file(test_file, original_name="curriculum_100pages.pdf", department="IT", org_id=10907, force=True)

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["chunks"], 45)
        self.assertEqual(store.count(), 45, "All 45 chunks must be stored in the vector store!")

        # Verify page 1 (batch 1), page 21 (batch 2), and page 45 (batch 3) are all present
        page_locations = {item["metadata"].get("location") for item in store.data}
        self.assertIn("Page 1", page_locations, "Page 1 from batch 1 must be present!")
        self.assertIn("Page 21", page_locations, "Page 21 from batch 2 must be present!")
        self.assertIn("Page 45", page_locations, "Page 45 from batch 3 must be present!")



if __name__ == "__main__":
    unittest.main()
