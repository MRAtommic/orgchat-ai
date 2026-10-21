# -*- coding: utf-8 -*-
"""
webai/tests/test_rag.py — Vector Store & RAG Engine Tests
Validates Native HNSW ChromaDB initialization, Cosine similarity search, and Multi-tenant metadata isolation.
"""

import sys
import tempfile
import shutil
from pathlib import Path

WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import unittest
import chromadb

class TestRAGVectorStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
        cls.client = chromadb.PersistentClient(path=cls.temp_dir)

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.temp_dir)
        except Exception:
            pass

    def test_chromadb_native_hnsw_collection_initialization(self):
        """Verify ChromaDB native HNSW cosine collection initializes properly."""
        collection = self.client.get_or_create_collection(
            name="test_knowledge_collection",
            metadata={"hnsw:space": "cosine"}
        )
        self.assertIsNotNone(collection)
        self.assertEqual(collection.name, "test_knowledge_collection")
        self.assertEqual(collection.metadata.get("hnsw:space"), "cosine")

    def test_vector_similarity_search_and_ranking(self):
        """Verify adding vectors and retrieving the most relevant chunk via cosine similarity."""
        collection = self.client.get_or_create_collection(
            name="test_similarity_ranking",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add 3 distinct document chunks with 4-dimensional normalized vectors
        collection.add(
            ids=["doc_attendance", "doc_leave", "doc_sales"],
            documents=[
                "พนักงานต้องลงเวลาเข้างานก่อน 09:00 น. และสแกนพิกัด GPS",
                "สิทธิ์การลาพักร้อนประจำปีคือ 10 วันต่อปี ต้องยื่นล่วงหน้า 3 วัน",
                "ใบเสนอราคาต้องมีลายเซ็นผู้จัดการฝ่ายขายและยอดเงินรวมภาษีมูลค่าเพิ่ม 7%"
            ],
            embeddings=[
                [0.9, 0.1, 0.0, 0.0],  # Attendance vector
                [0.0, 0.9, 0.1, 0.0],  # Leave vector
                [0.0, 0.0, 0.1, 0.9],  # Sales vector
            ],
            metadatas=[
                {"category": "attendance", "org_id": 1},
                {"category": "leave", "org_id": 1},
                {"category": "sales", "org_id": 1}
            ]
        )

        # Query vector close to Leave policy [0.05, 0.95, 0.05, 0.0]
        results = collection.query(
            query_embeddings=[[0.05, 0.95, 0.05, 0.0]],
            n_results=1
        )
        top_id = results["ids"][0][0]
        self.assertEqual(top_id, "doc_leave")
        self.assertIn("ลาพักร้อน", results["documents"][0][0])

    def test_multi_tenant_vector_isolation(self):
        """Verify metadata filtering strictly isolates vectors between Organization 1 and Organization 2."""
        collection = self.client.get_or_create_collection(
            name="test_tenant_isolation",
            metadata={"hnsw:space": "cosine"}
        )
        
        collection.add(
            ids=["org1_secret_doc", "org2_secret_doc"],
            documents=[
                "ข้อมูลลับองค์กรที่ 1: งบการเงินไตรมาส 3",
                "ข้อมูลลับองค์กรที่ 2: กลยุทธ์การตลาดลับ"
            ],
            embeddings=[
                [0.5, 0.5, 0.0, 0.0],
                [0.5, 0.5, 0.0, 0.0]
            ],
            metadatas=[
                {"org_id": 1, "owner": "Org1_Admin"},
                {"org_id": 2, "owner": "Org2_Admin"}
            ]
        )

        # Query as Org 1
        org1_res = collection.query(
            query_embeddings=[[0.5, 0.5, 0.0, 0.0]],
            where={"org_id": 1},
            n_results=5
        )
        returned_ids_org1 = org1_res["ids"][0]
        self.assertIn("org1_secret_doc", returned_ids_org1)
        self.assertNotIn("org2_secret_doc", returned_ids_org1)

        # Query as Org 2
        org2_res = collection.query(
            query_embeddings=[[0.5, 0.5, 0.0, 0.0]],
            where={"org_id": 2},
            n_results=5
        )
        returned_ids_org2 = org2_res["ids"][0]
        self.assertIn("org2_secret_doc", returned_ids_org2)
        self.assertNotIn("org1_secret_doc", returned_ids_org2)

if __name__ == "__main__":
    unittest.main()
