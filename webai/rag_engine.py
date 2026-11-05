# -*- coding: utf-8 -*-
"""
RAG Engine - Handles file parsing, embedding, and retrieval for the chatbot.
Supports: PDF, CSV, TXT, Images (OCR)
"""

import sys
import io
# Force UTF-8 output encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import csv
import hashlib
import json
import threading
import re
import gc
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
# ใช้ google-genai (SDK ใหม่) แทน google-generativeai (deprecated)
from google import genai as _genai_client_factory
import time
import logging
from datetime import datetime

logger = logging.getLogger("OrgChatAI.RAG")

try:
    import fitz # PyMuPDF
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False

os.environ["ANONYMIZED_TELEMETRY"] = "False"
try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None
    embedding_functions = None
# Load environment variables early and override any existing session variables
BASE_DIR = Path(__file__).parent.absolute()
_orig_db_rag = os.environ.get("DB_PATH")
load_dotenv(BASE_DIR / ".env", override=True, encoding="utf-8")
if _orig_db_rag:
    os.environ["DB_PATH"] = _orig_db_rag

try:
    import docx
    DOCX_SUPPORTED = True
except ImportError:
    DOCX_SUPPORTED = False

try:
    import openpyxl
    XLSX_SUPPORTED = True
except ImportError:
    XLSX_SUPPORTED = False

try:
    from PIL import Image
    IMAGE_SUPPORTED = True
except ImportError:
    IMAGE_SUPPORTED = False

try:
    import pptx
    PPTX_SUPPORTED = True
except ImportError:
    PPTX_SUPPORTED = False


BASE_DIR = Path(__file__).parent.absolute()

# Use DATA_DIR env var if set (Railway persistent volume), otherwise fall back to app dir
_DATA_ROOT = Path(os.environ.get("DATA_DIR", str(BASE_DIR)))
_DATA_ROOT.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = _DATA_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

CHROMA_DIR = _DATA_ROOT / "chroma_db"          # โฟลเดอร์ Chroma รุ่นเก่า (ต้องใช้ hnswlib) — คงไว้เป็นข้อมูลสำรอง ไม่เขียนทับ
CHROMA_V2_DIR = _DATA_ROOT / "chroma_v2"       # ที่เก็บเวกเตอร์ปัจจุบัน (ChromaDB 1.x)
CHROMA_DIR.mkdir(exist_ok=True)

META_FILE = _DATA_ROOT / "file_meta.json"
_META_LOCK = threading.RLock()


def _load_meta() -> dict:
    with _META_LOCK:
        if META_FILE.exists():
            with open(META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)

            # --- Path Self-Healing for Migration (Windows <-> Pi/Linux) ---
            modified = False
            for fid, info in meta.items():
                stored_path = info.get("path")
                if stored_path:
                    # If the path looks like Windows (has \) but we are on Linux (or vice versa)
                    # Or if the parent directory no longer matches our actual UPLOAD_DIR
                    # Use regex to split by both / and \ to safely get the filename on any OS
                    # Use a robust way to extract filename from either Windows or Linux absolute paths
                    actual_name = stored_path.replace('\\', '/').split('/')[-1]
                    expected_path = str(UPLOAD_DIR / actual_name)

                    if stored_path != expected_path:
                        # Fix it to match current OS and movement of folder
                        info["path"] = expected_path
                        modified = True

            if modified:
                logger.info(f"[HEALED] Paths in file_meta.json self-healed. Total reconciled: {len([m for m in meta if meta[m].get('path')])}")
                _save_meta(meta)
            return meta
        return {}


def _save_meta(meta: dict):
    with _META_LOCK:
        # Atomic write: write to tmp then rename to avoid corruption during crash/power loss
        tmp_file = META_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        tmp_file.replace(META_FILE)

def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks, optimized for Thai and English."""
    # Pre-clean: collapse whitespace but keep some structure
    text = re.sub(r"([ \t])+", " ", text).strip()
    
    chunks = []
    start = 0
    text_len = len(text)
    
    # Common separators for Thai and English
    # In Thai, spaces are used as phrase/sentence delimiters
    # Thai markers: ๆ (repeat), ฯ (omission), ๆลๆ (etc)
    # Thai conjunctions: ซึ่ง, และ, หรือ, เพราะ, ดังนั้น, ที่
    separators = [
        "\n\n", "\n", 
        ". ", "! ", "? ", 
        " ๆลๆ", " ฯลฯ", " ๆ ", " ฯ ", 
        " ซึ่ง", " และ", " หรือ", " เพราะ", " ดังนั้น", " โดยเฉพาะ", " อย่างไรก็ตาม",
        "  ", ". ", " "
    ] 
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Try to find a logical break point within the last 25% of the chunk
        if end < text_len:
            lookback_limit = max(start, end - 200)
            best_break = -1
            for sep in separators:
                idx = text.rfind(sep, lookback_limit, end)
                if idx != -1:
                    best_break = idx + len(sep)
                    break
            
            if best_break != -1:
                end = best_break
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 5:  # Avoid tiny fragments
            chunks.append(chunk)
            
        # Advance with overlap
        new_start = end - overlap
        if new_start <= start:
            start = end 
        else:
            # Ensure overlap doesn't start in the middle of a short fragment
            start = new_start
            
    return chunks


# ─────────────────────────────────────────────
# Vector Store
# ─────────────────────────────────────────────
class BatchedGoogleEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """ฟังก์ชัน embedding โดยใช้ google-genai SDK ใหม่ แทน deprecated GoogleGenerativeAi."""
    def __init__(self, api_key: str, model_name: str = "models/gemini-embedding-001"):
        self._api_key = api_key
        self._model_name = model_name
        self._client = _genai_client_factory.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        self.daily_quota_hit = False

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not input: return []
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(input), batch_size):
            batch = input[i : i + batch_size]
            try:
                # ใช้ google-genai Client API ใหม่
                response = self._client.models.embed_content(
                    model=self._model_name,
                    contents=batch,
                    config={"task_type": "retrieval_document"}
                )
                # SDK ใหม่คืน response.embeddings เป็น list[ContentEmbedding]
                for emb in response.embeddings:
                    all_embeddings.append(emb.values)
                if len(input) > batch_size:
                    time.sleep(1.0)  # Reduced from 5.0 to 1.0 to keep responsive
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "quota" in err_msg:
                    if any(x in err_msg for x in ["per day", "daily", "limit: 1000", "perday"]):
                        logger.info("🚫 DAILY Quota Exceeded. หยุดการ embed ชั่วคราว")
                        self.daily_quota_hit = True
                        raise Exception("DAILY_QUOTA_EXCEEDED")
                    logger.warning(f"⚠️ Rate Limit — รอ 5 วินาทีแล้วลองใหม่...")
                    time.sleep(5.0)
                    try:
                        response = self._client.models.embed_content(
                            model=self._model_name,
                            contents=batch,
                            config={"task_type": "retrieval_document"}
                        )
                        for emb in response.embeddings:
                            all_embeddings.append(emb.values)
                        continue
                    except Exception:
                        pass
                logger.error(f"❌ Embedding API Error: {e}")
                raise e
        return all_embeddings

class OllamaEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Custom embedding function using Ollama."""
    def __init__(self, model_name="mxbai-embed-large"):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/embeddings"

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not input: return []
        all_embeddings = []
        for text in input:
            try:
                response = requests.post(
                    self.url,
                    json={"model": self.model_name, "prompt": text},
                    timeout=(5, 30)
                )
                if response.status_code == 200:
                    all_embeddings.append(response.json()["embedding"])
                else:
                    raise Exception(f"Ollama Error: {response.text}")
            except Exception as e:
                logger.error(f"❌ Ollama Embedding Error: {e}")
                raise e
        return all_embeddings

class FastEmbedEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Truly local multilingual embedding function using FastEmbed (supports Thai & 50+ languages)."""
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        try:
            from fastembed import TextEmbedding
            # Define a local cache directory to avoid Windows Temp permission issues
            local_cache = os.path.join(str(BASE_DIR), "fastembed_cache")  # อิงโฟลเดอร์โปรเจกต์ ไม่ใช่ cwd (กันโหลดโมเดลไม่เจอเมื่อสตาร์ตจากที่อื่น)
            if not os.path.exists(local_cache):
                os.makedirs(local_cache, exist_ok=True)
            self.model = TextEmbedding(model_name=model_name, cache_dir=local_cache)
        except ImportError:
            logger.error("❌ 'fastembed' not installed. Please run: pip install fastembed")
            raise ImportError("fastembed not installed")

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not input: return []
        # FastEmbed returns a generator of numpy arrays
        embeddings = list(self.model.embed(input))
        return [l.tolist() for l in embeddings]

import requests # Ensure requests is available in rag_engine

# ─────────────────────────────────────────────
# Fallback Vector Store for Windows without C++ compiler (hnswlib issue)
# ─────────────────────────────────────────────
def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = sum(a * a for a in v1) ** 0.5
    norm_v2 = sum(b * b for b in v2) ** 0.5
    if not norm_v1 or not norm_v2:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def evaluate_filter(metadata, filter_expr):
    if not filter_expr:
        return True
    
    if not isinstance(filter_expr, dict):
        return False
        
    for key, val in filter_expr.items():
        if key == "$and":
            if not isinstance(val, list):
                return False
            return all(evaluate_filter(metadata, sub) for sub in val)
            
        elif key == "$or":
            if not isinstance(val, list):
                return False
            return any(evaluate_filter(metadata, sub) for sub in val)
            
        else:
            meta_val = metadata.get(key)
            if isinstance(val, dict):
                for op, op_val in val.items():
                    if op == "$eq":
                        if op_val is None:
                            if meta_val is None or meta_val == "" or meta_val == "None":
                                continue
                            else:
                                return False
                        else:
                            if str(meta_val) == str(op_val):
                                continue
                            else:
                                return False
                    elif op == "$in":
                        if not isinstance(op_val, list):
                            return False
                        string_op_val = {str(x) for x in op_val}
                        if str(meta_val) in string_op_val:
                            continue
                        else:
                            return False
                    else:
                        return False
            else:
                if val is None or val == "":
                    if meta_val is None or meta_val == "" or meta_val == "None":
                        continue
                    else:
                        return False
                else:
                    if str(meta_val) == str(val):
                        continue
                    else:
                        return False
    return True

class PurePythonVectorStore:
    def __init__(self, ef, persist_path):
        self.ef = ef
        self.persist_path = Path(persist_path)
        self.data = []  # List of dicts: {"id": str, "document": str, "metadata": dict, "embedding": list[float]}
        self.load()

    def load(self):
        if self.persist_path.exists():
            try:
                with open(self.persist_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.warning(f"✅ Loaded {len(self.data)} chunks from pure Python vector store fallback.")
            except Exception as e:
                logger.error(f"⚠️ Error loading fallback vector store: {e}. Renaming corrupted file and starting fresh.")
                try:
                    corrupted_path = self.persist_path.with_suffix(".corrupted_" + str(int(time.time())))
                    self.persist_path.rename(corrupted_path)
                except (OSError, IOError) as rename_err:
                    logger.warning(f"Could not rename corrupted fallback vector store: {rename_err}")
                self.data = []

    def save(self):
        try:
            tmp_file = self.persist_path.with_suffix(".tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            tmp_file.replace(self.persist_path)
        except Exception as e:
            logger.error(f"⚠️ Error saving fallback vector store: {e}")

    def upsert(self, documents: list[str], ids: list[str], metadatas: list[dict]):
        try:
            embeddings = self.ef(documents)
        except Exception as e:
            logger.error(f"❌ In-memory upsert embedding error: {e}")
            raise e

        id_set = set(ids)
        self.data = [item for item in self.data if item["id"] not in id_set]

        for doc, cid, meta, emb in zip(documents, ids, metadatas, embeddings):
            if hasattr(emb, "tolist"):
                emb_list = emb.tolist()
            elif isinstance(emb, (list, tuple)):
                emb_list = [float(x) for x in emb]
            else:
                emb_list = [float(x) for x in list(emb)]

            self.data.append({
                "id": cid,
                "document": doc,
                "metadata": meta,
                "embedding": emb_list
            })
        self.save()

    def count(self) -> int:
        return len(self.data)

    def delete(self, ids: list[str] = None, where: dict = None):
        if ids:
            id_set = set(ids)
            self.data = [item for item in self.data if item["id"] not in id_set]
        elif where:
            self.data = [item for item in self.data if not evaluate_filter(item.get("metadata", {}), where)]
        self.save()

    def get(self, where: dict = None, include: list[str] = None, limit: int = None, **kwargs) -> dict:
        matched = []
        for item in self.data:
            if where:
                if not evaluate_filter(item.get("metadata", {}), where):
                    continue
            matched.append(item)

        if limit is not None:
            matched = matched[:limit]

        return {
            "ids": [item["id"] for item in matched],
            "documents": [item["document"] for item in matched],
            "metadatas": [item["metadata"] for item in matched],
            "embeddings": [item["embedding"] for item in matched]
        }

    def update(self, ids: list[str], metadatas: list[dict]):
        meta_dict = {cid: meta for cid, meta in zip(ids, metadatas)}
        for item in self.data:
            cid = item["id"]
            if cid in meta_dict:
                item["metadata"] = meta_dict[cid]
        self.save()

    def query(self, query_texts: list[str], n_results: int = 4, where: dict = None) -> dict:
        if not query_texts:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        matched = []
        for item in self.data:
            if where:
                if not evaluate_filter(item.get("metadata", {}), where):
                    continue
            matched.append(item)

        if not matched:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        try:
            query_embs = self.ef(query_texts)
        except Exception as e:
            logger.error(f"❌ In-memory query embedding error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_emb = query_embs[0]

        scored = []
        for item in matched:
            sim = cosine_similarity(query_emb, item["embedding"])
            dist = 1.0 - sim
            scored.append((item, dist))

        scored.sort(key=lambda x: x[1])
        top_results = scored[:n_results]

        return {
            "documents": [[item[0]["document"] for item in top_results]],
            "metadatas": [[item[0]["metadata"] for item in top_results]],
            "distances": [[item[1] for item in top_results]]
        }

# ─────────────────────────────────────────────────────────────────────────────
# ChromaStore — เก็บเวกเตอร์ด้วย ChromaDB 1.x (ไม่ต้องใช้ hnswlib) โดยมี interface เดียวกับ PurePythonVectorStore
#   • ฝั่งเราคำนวณ embedding เอง (ไม่ผูก embedding_function กับ Chroma)
#   • แปลง where-filter ที่โค้ดเดิมส่งมา (ซึ่ง PurePythonVectorStore ยอมรับแบบหลวม) ให้เป็นรูปแบบที่ Chroma รับได้:
#       - $and/$or ที่มีสมาชิกเดียว → ถอดเป็นเงื่อนไขเดียว
#       - {"$eq": None}/ค่าว่าง → จับคู่กับค่าว่าง "" (หรือไม่ตรงเลยสำหรับคีย์ตัวเลข)
#       - เทียบชนิดข้อมูลตามคีย์ (organization_id = int, นอกนั้น = str) เหมือนการเทียบแบบ str() ของตัวเดิม
#   • ครั้งแรกที่คอลเลกชันว่าง จะนำเข้าจากไฟล์สำรอง chroma_db_fallback.json (มี embedding อยู่แล้ว ไม่เสียค่า API)
# ─────────────────────────────────────────────────────────────────────────────
_TRUE, _FALSE = object(), object()
_INT_KEYS = {"organization_id"}


def _coerce_value(key, v):
    """ปรับค่าให้ชนิดตรงกับที่เก็บ  คืน _FALSE ถ้าเป็นค่าที่ไม่มีทางตรง"""
    if key in _INT_KEYS:
        if v is None or v == "":
            return _FALSE
        try:
            return int(v)
        except (TypeError, ValueError):
            return _FALSE
    if v is None:
        return ""
    return str(v)


def _norm_where(w):
    """คืน dict ที่ Chroma รับได้, _TRUE (ไม่กรอง) หรือ _FALSE (ไม่ตรงอะไรเลย)"""
    if w is None or w == {}:
        return _TRUE
    if not isinstance(w, dict):
        return _FALSE
    if len(w) > 1:
        return _norm_where({"$and": [{k: v} for k, v in w.items()]})
    (key, val), = w.items()
    if key in ("$and", "$or"):
        if not isinstance(val, list):
            return _FALSE
        subs = [_norm_where(s) for s in val]
        if key == "$and":
            if any(s is _FALSE for s in subs):
                return _FALSE
            subs = [s for s in subs if s is not _TRUE]
            if not subs:
                return _TRUE
        else:
            if any(s is _TRUE for s in subs):
                return _TRUE
            subs = [s for s in subs if s is not _FALSE]
            if not subs:
                return _FALSE
        return subs[0] if len(subs) == 1 else {key: subs}
    # leaf
    if isinstance(val, dict):
        parts = []
        for op, ov in val.items():
            if op == "$eq":
                c = _coerce_value(key, ov)
                if c is _FALSE:
                    return _FALSE
                parts.append({key: c})
            elif op == "$ne":
                c = _coerce_value(key, ov)
                if c is _FALSE:
                    continue  # ≠ ค่าที่ไม่มีทางตรง = จริงเสมอ
                parts.append({key: {"$ne": c}})
            elif op in ("$in", "$nin"):
                if not isinstance(ov, list):
                    return _FALSE
                vals = []
                for x in ov:
                    c = _coerce_value(key, x)
                    if c is not _FALSE and c not in vals:
                        vals.append(c)
                if not vals:
                    if op == "$in":
                        return _FALSE
                    continue
                parts.append({key: {op: vals}})
            else:
                return _FALSE
        if not parts:
            return _TRUE
        return parts[0] if len(parts) == 1 else {"$and": parts}
    c = _coerce_value(key, val)
    return _FALSE if c is _FALSE else {key: c}


def _clean_meta(meta):
    out = {}
    for k, v in (meta or {}).items():
        if v is None:
            v = "" if k not in _INT_KEYS else None
        if v is None:
            continue
        if k in _INT_KEYS:
            try:
                v = int(v)
            except (TypeError, ValueError):
                continue
        elif not isinstance(v, (str, int, float, bool)):
            v = str(v)
        out[k] = v
    return out


class ChromaStore:
    """ChromaDB-backed vector store (same interface as PurePythonVectorStore)."""
    _EMPTY_GET = {"ids": [], "documents": [], "metadatas": []}

    def __init__(self, ef, collection):
        self.ef = ef
        self._col = collection

    @classmethod
    def open(cls, ef, path, name, seed_json=None):
        client = chromadb.PersistentClient(path=str(path), settings=chromadb.config.Settings(anonymized_telemetry=False))
        col = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
        store = cls(ef, col)
        if seed_json and col.count() == 0:
            store._seed_from_json(Path(seed_json))
        return store

    def _seed_from_json(self, path):
        try:
            if not path.exists():
                return
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ok = 0
            # ไฟล์สำรองอาจมีเวกเตอร์หลายขนาดปนกัน (เคยเปลี่ยนโมเดล embedding) — Chroma รับได้ขนาดเดียวต่อคอลเลกชัน
            # ใช้ขนาดที่พบมากที่สุดเป็นหลัก ส่วนชิ้นที่ขนาดไม่ตรงจะคำนวณ embedding ใหม่จากข้อความด้วยโมเดลปัจจุบัน
            from collections import Counter as _Counter
            dims = _Counter(len(d["embedding"]) for d in data if d.get("embedding"))
            target = dims.most_common(1)[0][0] if dims else None
            fixed = skipped = 0
            # โมเดลในเครื่อง (FastEmbed) คำนวณใหม่ได้ฟรี และไลบรารีรุ่นใหม่เปลี่ยนวิธีรวมเวกเตอร์ (CLS → mean pooling)
            # ทำให้เวกเตอร์เก่าที่เก็บไว้ไม่ตรงกับเวกเตอร์คำค้นปัจจุบัน → คำนวณใหม่ทั้งหมดเพื่อให้ค้นหาแม่นยำ
            _reembed_all = isinstance(self.ef, FastEmbedEmbeddingFunction)
            for d in data:
                if d.get("document") and (_reembed_all or (d.get("embedding") and len(d["embedding"]) != target)):
                    try:
                        e = self.ef([d["document"]])[0]
                        e = e.tolist() if hasattr(e, "tolist") else [float(x) for x in e]
                        if _reembed_all or len(e) == target:
                            d["embedding"] = e
                            fixed += 1
                            continue
                    except Exception:
                        pass
                    d["embedding"] = None
                    skipped += 1
            if fixed or skipped:
                logger.warning(f"⚠️ Mixed embedding sizes in {path.name}: re-embedded {fixed} chunk(s), skipped {skipped}")
            for i in range(0, len(data), 100):
                batch = [d for d in data[i:i + 100] if d.get("embedding") and d.get("document")]
                if not batch:
                    continue
                self._col.upsert(ids=[d["id"] for d in batch], documents=[d["document"] for d in batch],
                                 embeddings=[d["embedding"] for d in batch],
                                 metadatas=[_clean_meta(d.get("metadata")) or {"source": ""} for d in batch])
                ok += len(batch)
            logger.warning(f"✅ Imported {ok}/{len(data)} chunks from {path.name} into ChromaDB (one-time migration)")
        except Exception as e:
            logger.error(f"⚠️ Seeding ChromaDB from {path.name} failed: {e}")

    # ---- interface ----
    def count(self) -> int:
        return self._col.count()

    def upsert(self, documents, ids, metadatas):
        embs = self.ef(documents)
        embs = [e.tolist() if hasattr(e, "tolist") else [float(x) for x in e] for e in embs]
        self._col.upsert(ids=list(ids), documents=list(documents), embeddings=embs,
                         metadatas=[_clean_meta(m) or {"source": ""} for m in metadatas])

    def get(self, where=None, include=None, limit=None, **kw):
        w = _norm_where(where)
        if w is _FALSE:
            return dict(self._EMPTY_GET)
        args = {"include": [i for i in (include or ["documents", "metadatas"]) if i in ("documents", "metadatas", "embeddings")]}
        if w is not _TRUE:
            args["where"] = w
        if limit is not None:
            args["limit"] = limit
        r = self._col.get(**args)
        return {"ids": r.get("ids") or [], "documents": r.get("documents") or [], "metadatas": r.get("metadatas") or []}

    def query(self, query_texts, n_results=4, where=None):
        empty = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        if not query_texts:
            return empty
        w = _norm_where(where)
        if w is _FALSE:
            return empty
        try:
            q = self.ef(query_texts)
        except Exception as e:
            logger.error(f"❌ Chroma query embedding error: {e}")
            return empty
        q = [x.tolist() if hasattr(x, "tolist") else [float(v) for v in x] for x in q]
        args = {"query_embeddings": q[:1], "n_results": max(1, min(int(n_results), max(1, self._col.count()))),
                "include": ["documents", "metadatas", "distances"]}
        if w is not _TRUE:
            args["where"] = w
        r = self._col.query(**args)
        return {"documents": r["documents"], "metadatas": r["metadatas"], "distances": r["distances"]}

    def update(self, ids, metadatas):
        self._col.update(ids=list(ids), metadatas=[_clean_meta(m) or {"source": ""} for m in metadatas])

    def delete(self, ids=None, where=None):
        if ids:
            self._col.delete(ids=list(ids))
        elif where:
            w = _norm_where(where)
            if w is _FALSE:
                return
            if w is _TRUE:
                raise ValueError("refusing to delete everything via empty filter")
            self._col.delete(where=w)


class KnowledgeBase:
    def __init__(self):
        # Use absolute path for ChromaDB
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not self.api_key:
            logger.warning("⚠️ Warning: GEMINI_API_KEY not found in environment.")
            self.api_key = "dummy_key_for_init"
        self.provider = os.environ.get("AI_EMBEDDING_PROVIDER", "gemini").strip().lower()
        provider = self.provider
        if provider == "ollama":
            embed_model = os.environ.get("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
            logger.info(f"🧠 Using Ollama Embeddings (Model: {embed_model})")
            ef = OllamaEmbeddingFunction(model_name=embed_model)
        elif provider == "local":
            logger.info(f"[LOCAL] Using Local FastEmbed Embeddings")
            try:
                ef = FastEmbedEmbeddingFunction()
            except ImportError:
                logger.warning("⚠️ Falling back to Dummy embeddings because fastembed is missing.")
                ef = None
            except Exception as e:
                logger.error(f"⚠️ [CRASH PREVENTED] Local FastEmbed failed to initialize (e.g. OOM/bad allocation): {e}")
                logger.info(f"☁️ [SELF-HEAL] Automatically falling back to Google Gemini Cloud Embeddings...")
                try:
                    ef = BatchedGoogleEmbeddingFunction(
                        api_key=self.api_key,
                        model_name="models/gemini-embedding-001"
                    )
                    self.provider = "gemini"
                except Exception as ex:
                    logger.error(f"❌ Fallback failed: {ex}")
                    ef = None
        else:
            ef = BatchedGoogleEmbeddingFunction(
                api_key=self.api_key,
                model_name="models/gemini-embedding-001"
            )

        if ef is None:
             raise Exception("EMBEDDING_PROVIDER_NOT_READY")

        self._ephemeral = False

        # ─── ChromaDB (local persistent) ───
        if chromadb is None:
            print("⚠️ chromadb ไม่ได้ติดตั้ง — บังคับใช้ Pure Python Vector Store แทน", flush=True)
            self._ephemeral = True
            self.collection = PurePythonVectorStore(ef, BASE_DIR / "chroma_db_fallback.json")
            print("✅ Pure Python Vector Store Fallback ready.", flush=True)
            return

        if os.environ.get("VECTOR_BACKEND", "chroma").strip().lower() == "python":
            logger.warning("VECTOR_BACKEND=python — using Pure Python Vector Store")
            self._ephemeral = True
            self.collection = PurePythonVectorStore(ef, BASE_DIR / "chroma_db_fallback.json")
            return

        def _open_store():
            _result, _err = [None], [None]
            def _run():
                try:
                    _result[0] = ChromaStore.open(ef, CHROMA_V2_DIR, f"org_knowledge_{self.provider}",
                                                  seed_json=BASE_DIR / "chroma_db_fallback.json")
                except Exception as e:
                    _err[0] = e
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(timeout=60)
            if t.is_alive() or _result[0] is None:
                return None, _err[0] or "Timeout"
            return _result[0], None

        try:
            store, err = _open_store()
            if store is None:
                raise Exception(f"ChromaDB store failed to open: {err}")
            self.collection = store
            logger.info(f"✅ ChromaDB ready ({store.count()} chunks)")
        except Exception as e:
            print(f"⚠️ ChromaDB Error/Timeout detected: {e}. Falling back to Pure Python Vector Store.", flush=True)
            self._ephemeral = True
            self.collection = PurePythonVectorStore(ef, BASE_DIR / "chroma_db_fallback.json")
            print("✅ Pure Python Vector Store Fallback ready.", flush=True)

    def update_api_key(self, api_key: str):
        """อัปเดต API key และรีเซ็ต collection"""
        if not api_key or api_key == "dummy_key_for_init":
            return
        self.api_key = api_key
        ef = BatchedGoogleEmbeddingFunction(
            api_key=api_key,
            model_name="models/gemini-embedding-001"
        )
        if self._ephemeral and isinstance(self.collection, PurePythonVectorStore):
            self.collection.ef = ef
            logger.warning("✅ [FALLBACK] KnowledgeBase API Key updated for pure Python store.")
            return

        if isinstance(self.collection, ChromaStore):
            self.collection.ef = ef
            logger.info("✅ KnowledgeBase API Key อัปเดตแล้ว (ChromaDB)")
            return
        if chromadb is not None:
            try:
                self.collection = ChromaStore.open(ef, CHROMA_V2_DIR, f"org_knowledge_{self.provider}")
                logger.info("✅ KnowledgeBase API Key อัปเดตแล้ว collection รีเซ็ตเรียบร้อย")
                return
            except Exception as e:
                logger.error(f"⚠️ Failed to update API key with chromadb: {e}. Keeping fallback.")
        
        # Fallback if chromadb is None or fails
        self._ephemeral = True
        self.collection = PurePythonVectorStore(ef, BASE_DIR / "chroma_db_fallback.json")

    def is_key_valid(self):
        """Simple check if we have a real key if provider is Gemini."""
        if self.provider != "gemini":
            return True # Local providers don't need GEMINI_API_KEY
        return self.api_key and self.api_key != "dummy_key_for_init"

    def add_chunks(self, chunks: list[str], source_name: str, file_id: str, metadatas: list[dict] = None):
        ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
        if metadatas is None:
            metadatas = [{"source": source_name, "file_id": file_id} for _ in chunks]
        else:
            # Merge with default metadata
            for m in metadatas:
                m["source"] = source_name
                m["file_id"] = file_id
        
        try:
            self.collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        except Exception as e:
            err_msg = str(e).lower()
            if isinstance(self.collection, (PurePythonVectorStore, ChromaStore)):
                # ไม่ลบ/สร้างคอลเลกชันใหม่เอง (กันข้อมูลหายเมื่อเปลี่ยนโมเดล embedding) — ให้แจ้งข้อผิดพลาดแทน
                raise e
            # Only recreate if it's a GENUINE dimension mismatch (e.g. model changed)
            # Standard Chroma dimension error contains 'Expected' and 'got'
            if "dimension" in err_msg and ("expected" in err_msg or "but got" in err_msg):
                logger.warning("⚠️ Critical Dimension mismatch detected. Recreating collection for new model...")
                if chromadb is not None:
                    try:
                        # To change dimensions, we MUST delete the collection and recreate it.
                        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
                        try:
                            client.delete_collection(f"org_knowledge_{self.provider}")
                        except Exception as del_err:
                            logger.debug(f"Collection recreate notice: {del_err}")
                        
                        # Re-init collection using current embedding function
                        self.collection = client.get_or_create_collection(
                            name=f"org_knowledge_{self.provider}",
                            embedding_function=self.collection._embedding_function,
                            metadata={"hnsw:space": "cosine"},
                        )
                        # Retry once
                        self.collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
                        return
                    except Exception as ex:
                        logger.error(f"⚠️ Failed to reset collection: {ex}")
                raise e
            else:
                raise e

    def update_metadata_by_file_id(self, file_id: str, new_meta: dict) -> bool:
        """Update metadata fields for all chunks belonging to a file_id."""
        try:
            results = self.collection.get(where={"file_id": file_id}, include=["metadatas"])
            ids = results.get("ids", [])
            metas = results.get("metadatas", [])
            if ids and metas:
                updated_metas = []
                for m in metas:
                    updated_m = dict(m or {})
                    updated_m.update(new_meta)
                    updated_metas.append(updated_m)
                self.collection.update(ids=ids, metadatas=updated_metas)
                return True
        except Exception as e:
            logger.error(f"⚠️ Error updating metadata for file_id {file_id}: {e}")
        return False

    def query(self, question: str, n_results: int = 4, where: dict = None) -> list[dict]:
        if not self.is_key_valid():
            logger.warning("⚠️ API Key not valid. Skipping query.")
            return []
            
        count = self.collection.count()
        if count == 0:
            return []
        n = min(n_results, count)
        result = self.collection.query(query_texts=[question], n_results=n, where=where)
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        
        results = []
        for d, m, dist in zip(docs, metas, distances):
            # Distance 0 is perfect. Normalize to a 0-1 score
            score = max(0, 1 - (dist / 1.5))
            item = {"text": d, "score": score}
            item.update(m)
            results.append(item)
        return results

    def delete_by_file_id(self, file_id: str):
        try:
            # Direct deletion by metadata filter is more robust in recent Chroma versions
            self.collection.delete(where={"file_id": file_id})
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB deletion warning: {e}")
            # Fallback: ingest might overwrite anyway, so we continue

    def delete_by_source(self, source_name: str):
        """Used for deleting specific Wiki pages or similar by source string."""
        try:
            self.collection.delete(where={"source": source_name})
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB source deletion warning: {e}")

    def update_metadata_by_file_id(self, file_id: str, new_metas_dict: dict):
        """Updates metadata for all chunks with this file_id."""
        try:
            results = self.collection.get(where={"file_id": file_id})
            ids = results.get("ids", [])
            if not ids:
                return
            
            existing_metas = results.get("metadatas", [])
            updated_metas = []
            for meta in existing_metas:
                # Normalize new metadata: convert None to "", others to str
                for k, v in new_metas_dict.items():
                    if k == "category_id":
                        meta[k] = str(v) if v is not None else ""
                    else:
                        meta[k] = v
                updated_metas.append(meta)
            
            self.collection.update(ids=ids, metadatas=updated_metas)
        except Exception as e:
            logger.error(f"⚠️ ChromaDB update error for {file_id}: {e}")

    def fix_chroma_categories(self, meta: dict):
        """One-time utility to sync category_ids from meta file to ChromaDB chunks."""
        logger.info("🛠️ Syncing missing category_ids to ChromaDB...")
        for fid, info in meta.items():
            cat = info.get("category_id")
            # Sync ALL states, normalizing None to ""
            val = str(cat) if cat is not None else ""
            self.update_metadata_by_file_id(fid, {"category_id": val})
        logger.info("✅ Sync complete.")

    def total_chunks(self) -> int:
        return self.collection.count()

    def hybrid_query(self, question: str, n_results: int = 5, where: dict = None) -> list[dict]:
        """Combines semantic vector search with comprehensive Thai/English keyword matching."""
        if not self.is_key_valid():
            return []
            
        count = self.collection.count()
        if count == 0:
            return []

        # 1. Semantic Search (Vector) - Fetch a wider pool (up to 40 candidates)
        fetch_k = min(max(n_results * 6, 40), count)
        vector_results = self.query(question, n_results=fetch_k, where=where)
        
        # 2. Optimized Keyword Match with Thai Tokenization & Fallback
        keywords = []
        try:
            import pythainlp
            tokens = pythainlp.word_tokenize(question, engine="newmm")
            thai_stopwords = {
                "ขอ", "ช่วย", "หน่อย", "ครับ", "ค่ะ", "นะคะ", "คะ", "จ้า", "พี่", "น้อง",
                "มี", "ได้", "ให้", "ใน", "ที่", "และ", "หรือ", "ไหม", "อะไร", "บ้าง",
                "สิ", "นะ", "อยาก", "รู้", "ด้วย", "นี้", "นั้น", "ใคร", "ไหน", "เท่าไหร่",
                "คือ", "ของ", "คุณ", "บอก", "ว่า", "เป็น", "อยู่"
            }
            keywords = [t.lower().strip() for t in tokens if len(t.strip()) > 1 and t.strip() not in thai_stopwords]
        except Exception:
            keywords = []

        if not keywords:
            import re
            raw_tokens = re.findall(r'[฀-๿a-zA-Z0-9]+', question)
            stop_set = {"ขอ", "ช่วย", "หน่อย", "ครับ", "ค่ะ", "นะคะ", "คะ", "พี่", "น้อง", "คือ", "ของ", "คุณ"}
            keywords = [kw.lower() for kw in raw_tokens if len(kw) > 1 and kw not in stop_set]

        # 3. Direct keyword scanning across all candidates in collection matching where
        seen_texts = {item.get("text", ""): item for item in vector_results}
        
        if keywords:
            try:
                # If PurePythonVectorStore:
                if hasattr(self.collection, 'data'):
                    for entry in self.collection.data:
                        if where and not evaluate_filter(entry.get("metadata", {}), where):
                            continue
                        doc_text = entry.get("document", "")
                        doc_lower = doc_text.lower()
                        matches = [kw for kw in keywords if kw in doc_lower]
                        if matches:
                            if doc_text not in seen_texts:
                                sim = cosine_similarity(self.collection.ef([question])[0], entry["embedding"]) if "embedding" in entry else 0.2
                                base_score = max(0, 1 - ((1.0 - sim) / 1.5))
                                item_dict = {
                                    "text": doc_text,
                                    "score": base_score,
                                    **entry.get("metadata", {})
                                }
                                seen_texts[doc_text] = item_dict
                                vector_results.append(item_dict)
                # If ChromaDB collection:
                elif hasattr(self.collection, 'get'):
                    all_c = self.collection.get(where=where, limit=3000, include=['documents', 'metadatas'])
                    docs = all_c.get('documents', []) or []
                    metas = all_c.get('metadatas', []) or []
                    for doc_text, meta in zip(docs, metas):
                        doc_lower = doc_text.lower()
                        matches = [kw for kw in keywords if kw in doc_lower]
                        if matches and doc_text not in seen_texts:
                            item_dict = {
                                "text": doc_text,
                                "score": 0.25,
                                **(meta or {})
                            }
                            seen_texts[doc_text] = item_dict
                            vector_results.append(item_dict)
            except Exception as _k_scan_err:
                logger.debug(f"Keyword scan fallback: {_k_scan_err}")

        # 4. Boost scores for keyword matches
        if keywords:
            for item in vector_results:
                lower_text = item["text"].lower()
                matches = [kw for kw in keywords if kw in lower_text]
                if matches:
                    ratio = len(matches) / len(keywords)
                    item["score"] = min(1.0, item["score"] + ratio * 0.50)
                    item["keyword_matches"] = matches

        # 5. Final Sort and Trim
        final_list = sorted(vector_results, key=lambda x: x["score"], reverse=True)
        return final_list[:n_results]

    def prune_orphaned_chunks(self, valid_file_ids: list[str]) -> int:
        """Remove chunks that don't belong to any file in the current metadata."""
        try:
            # This is a bit expensive as we have to fetch all IDs or iterate
            all_data = self.collection.get(include=['metadatas'])
            all_metas = all_data.get('metadatas', [])
            all_ids = all_data.get('ids', [])
            
            to_delete = []
            for i, meta in enumerate(all_metas):
                fid = meta.get('file_id')
                if fid not in valid_file_ids:
                    to_delete.append(all_ids[i])
            
            if to_delete:
                # Delete in batches to avoid overwhelming the system
                batch_size = 100
                for i in range(0, len(to_delete), batch_size):
                    self.collection.delete(ids=to_delete[i:i+batch_size])
                return len(to_delete)
            return 0
        except Exception as e:
            logger.error(f"⚠️ Pruning error: {e}")
            return 0

    def wipe(self):
        """Clear all data from the collection."""
        ids = self.collection.get()["ids"]
        if ids:
            self.collection.delete(ids=ids)


# File Processor
# ─────────────────────────────────────────────
class FileProcessor:
    @staticmethod
    def parse(file_path: Path) -> tuple[list[str], list[dict]]:
        """Returns (chunks, metadatas)."""
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return FileProcessor._parse_pdf(file_path)
        elif suffix == ".csv":
            return FileProcessor._parse_csv(file_path)
        elif suffix == ".docx":
            return FileProcessor._parse_docx(file_path)
        elif suffix in (".xlsx", ".xls"):
            return FileProcessor._parse_xlsx(file_path)
        elif suffix in (".txt", ".md", ".json"):
            return FileProcessor._parse_text(file_path)
        elif suffix in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
            return FileProcessor._parse_image(file_path)
        elif suffix in (".pptx", ".ppt"):
            return FileProcessor._parse_pptx(file_path)
        else:
            return [], []

    @staticmethod
    def _parse_pdf(path: Path) -> tuple[list[str], list[dict]]:
        if not PDF_SUPPORTED:
            return ["[PDF parsing unavailable]"], [{"location": "error"}]
        chunks, metas = [], []
        doc = fitz.open(str(path))
        for i, page in enumerate(doc, 1):
            text = page.get_text()
            if len((text or "").strip()) < 20:
                # หน้าสแกน (ไม่มีชั้นข้อความ) → OCR
                try:
                    import ocr_service
                    if ocr_service.available():
                        text = ocr_service.ocr_pdf_page(page) or text
                except Exception as _ocr_e:
                    logger.warning(f"OCR fallback failed on page {i}: {_ocr_e}")
            page_chunks = _chunk_text(text)
            for chunk in page_chunks:
                chunks.append(chunk)
                metas.append({"location": f"Page {i}"})
        doc.close()
        return chunks, metas

    @staticmethod
    def _parse_csv(path: Path) -> tuple[list[str], list[dict]]:
        """Parse CSV and group rows to reduce chunk count. Includes Thai encoding fallback."""
        chunks, metas = [], []
        # Try multiple encodings for Thai CSV compatibility
        encodings = ["utf-8-sig", "utf-8", "cp874", "tis-620"]
        
        success = False
        for enc in encodings:
            try:
                with open(path, newline="", encoding=enc) as f:
                    # Use a sample to detect if it's actually readable with this encoding
                    sample = f.read(1024)
                    f.seek(0)
                    reader = csv.DictReader(f)
                    rows = []
                    i = 0
                    for i, row in enumerate(reader, 1):
                        row_text = ", ".join(f"{k}:{v}" for k, v in row.items() if v)
                        if row_text.strip():
                            rows.append(row_text)
                        
                        # Group every 15 rows into one chunk (increased for efficiency)
                        if len(rows) >= 15:
                            chunks.append("\n".join(rows))
                            metas.append({"location": f"Rows {i-14}-{i}"})
                            rows = []
                        
                        # Safety cap for Pi memory: max 500 chunks per file (Optimized for RAM)
                        if len(chunks) >= 500:
                            logger.warning(f"⚠️ File too large for Pi RAM. Capping at 500 chunks.")
                            break
                    
                    # Remaining rows
                    if rows:
                        chunks.append("\n".join(rows))
                        metas.append({"location": f"Rows {i-len(rows)+1}-{i}"})
                
                success = True
                logger.info(f"✅ CSV parsed successfully with {enc} encoding.")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                logger.error(f"⚠️ CSV parsing error with {enc}: {e}")
                continue
        
        if not success:
            return [f"[CSV Error: Could not decode file with supported encodings]"], [{"location": "error"}]
            
        return chunks, metas

    @staticmethod
    def _parse_docx(path: Path) -> tuple[list[str], list[dict]]:
        if not DOCX_SUPPORTED:
            return ["[DOCX parsing unavailable]"], [{"location": "error"}]
        try:
            doc = docx.Document(path)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            chunks = _chunk_text(full_text)
            return chunks, [{"location": "Document"}] * len(chunks)
        except Exception as e:
            return [f"[DOCX Error: {e}]"], [{"location": "error"}]

    @staticmethod
    def _parse_xlsx(path: Path) -> tuple[list[str], list[dict]]:
        if not XLSX_SUPPORTED:
            return ["[XLSX parsing unavailable]"], [{"location": "error"}]
        chunks, metas = [], []
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                for i, row in enumerate(ws.iter_rows(values_only=True), 1):
                    row_text = " | ".join(str(cell) for cell in row if cell is not None)
                    if row_text.strip():
                        chunks.append(row_text)
                        metas.append({"location": f"Sheet: {sheet}, Row {i}"})
                    if len(chunks) >= 500:
                        logger.warning(f"⚠️ File too large for Pi RAM. Capping at 500 chunks.")
                        break
                if len(chunks) >= 500:
                    break
            return chunks, metas
        except Exception as e:
            return [f"[Excel Error: {e}]"], [{"location": "error"}]

    @staticmethod
    def _parse_text(path: Path) -> tuple[list[str], list[dict]]:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            text = path.read_text(encoding="cp874", errors="replace")
        chunks = _chunk_text(text)
        return chunks, [{"location": "Document"}] * len(chunks)

    @staticmethod
    def _parse_image(path: Path) -> tuple[list[str], list[dict]]:
        # คืนลิสต์ว่างเมื่อ OCR ใช้ไม่ได้/อ่านไม่ออก — เดิมคืนข้อความ "[OCR unavailable]" ซึ่งถูกนำเข้าเป็นความรู้ปนเปื้อนคลัง
        if not IMAGE_SUPPORTED:
            return [], []
        try:
            import ocr_service
            if not ocr_service.available():
                logger.warning(f"OCR unavailable for {path.name}: {ocr_service.configure()['msg']}")
                return [], []
            img = Image.open(str(path))
            text = ocr_service.ocr_image(img)
            chunks = _chunk_text(text)
            return chunks, [{"location": "Image OCR"}] * len(chunks)
        except Exception as e:
            logger.error(f"OCR error for {path.name}: {e}")
            return [], []

    @staticmethod
    def _parse_pptx(path: Path) -> tuple[list[str], list[dict]]:
        if not PPTX_SUPPORTED:
            return ["[PowerPoint parser unavailable — python-pptx not installed]"], [{"location": "error"}]
        chunks, metas = [], []
        try:
            prs = pptx.Presentation(str(path))
            for i, slide in enumerate(prs.slides, 1):
                slide_parts = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            t = paragraph.text.strip()
                            if t:
                                slide_parts.append(t)
                    elif shape.has_table:
                        for row in shape.table.rows:
                            row_vals = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                            if row_vals:
                                slide_parts.append(" | ".join(row_vals))
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    note = slide.notes_slide.notes_text_frame.text.strip()
                    if note:
                        slide_parts.append(f"[Speaker Notes: {note}]")
                if slide_parts:
                    slide_text = "\n".join(slide_parts)
                    sub_chunks = _chunk_text(slide_text) or [slide_text]
                    for sc in sub_chunks:
                        chunks.append(sc)
                        metas.append({"location": f"Slide {i}"})
            if not chunks:
                return ["[Presentation has no readable text]"], [{"location": "Slide 1"}]
            return chunks, metas
        except Exception as e:
            return [f"[PowerPoint Error: {e}]"], [{"location": "error"}]


# ─────────────────────────────────────────────
# Public API used by app.py
# ─────────────────────────────────────────────
_kb = None  # Lazy — initialized in background via reinit_kb(), not at import time

def _get_kb() -> "KnowledgeBase":
    """Return the current KnowledgeBase, creating it if not yet initialized."""
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb

# Re-init in case load_dotenv was called in app.py after this module was first loaded
def _migrate_org_id_to_chunks():
    """Backfill organization_id=1 on all existing chunks that lack it."""
    try:
        col = _get_kb().collection
        results = col.get(include=["metadatas"])
        ids = results.get("ids", [])
        metas = results.get("metadatas", [])
        to_update_ids = []
        to_update_metas = []
        for cid, m in zip(ids, metas):
            if m and "organization_id" not in m:
                m2 = dict(m)
                m2["organization_id"] = 1
                to_update_ids.append(cid)
                to_update_metas.append(m2)
        if to_update_ids:
            batch = 100
            for i in range(0, len(to_update_ids), batch):
                col.update(ids=to_update_ids[i:i+batch], metadatas=to_update_metas[i:i+batch])
            logger.info(f"✅ Migrated {len(to_update_ids)} chunks with organization_id=1")
    except Exception as e:
        logger.error(f"⚠️ org_id chunk migration error: {e}")


def reinit_kb():
    global _kb
    logger.info("🔄 Re-initializing KnowledgeBase to refresh settings...")
    _kb = KnowledgeBase()
    try:
        meta = _load_meta()
        _get_kb().fix_chroma_categories(meta)
    except Exception as e:
        logger.error(f"⚠️ Initial Chroma Sync error: {e}")
    try:
        _migrate_org_id_to_chunks()
    except Exception as e:
        logger.error(f"⚠️ org_id migration error: {e}")


def ingest_file(file_path: Path, original_name: str, department: str = "General", category_id: int = None, org_id: int = 1, force: bool = False) -> dict:
    """Parse file, chunk, embed, and store in ChromaDB. Returns metadata dict."""
    meta = _load_meta()
    fid = _file_hash(file_path)

    # 🔄 Auto-update: purge previous chunks or obsolete versions of the same file in this org
    for existing_fid, existing_info in list(meta.items()):
        if existing_info.get("name") == original_name and existing_info.get("organization_id") == org_id:
            if existing_fid != fid:
                logger.info(f"🔄 Auto-updating '{original_name}': Purging stale file_id {existing_fid} from vector store")
                try:
                    _get_kb().delete_by_file_id(existing_fid)
                    old_path = existing_info.get("path")
                    if old_path and Path(old_path).resolve() != file_path.resolve():
                        Path(old_path).unlink(missing_ok=True)
                    if category_id is None and existing_info.get("category_id") is not None:
                        category_id = existing_info.get("category_id")
                    if (department == "General" or not department) and existing_info.get("department"):
                        department = existing_info.get("department")
                    meta.pop(existing_fid, None)
                except Exception as ex:
                    logger.error(f"⚠️ Error cleaning up stale version {existing_fid}: {ex}")
            else:
                try:
                    _get_kb().delete_by_file_id(fid)
                except Exception:
                    pass

    logger.info(f"[INGEST] Ingesting: {original_name} ({fid}) | Dept: {department} | Org: {org_id}")
    if not force and fid in meta and meta[fid].get("status") == "ready":
        logger.info(f"⏩ Duplicate file: {original_name}")
        return {"status": "duplicate", "file_id": fid, "name": original_name}

    # Initial state to show in UI while processing
    meta[fid] = {
        "name": original_name,
        "path": str(file_path),
        "chunks": 0,
        "size": file_path.stat().st_size,
        "type": file_path.suffix.lower().lstrip("."),
        "department": department,
        "category_id": category_id,
        "organization_id": org_id,
        "status": "processing",
        "api_key_status": _get_kb().api_key[:5] + "..." if _get_kb().is_key_valid() else "MISSING KEY",
        "timestamp": datetime.now().isoformat()
    }
    _save_meta(meta)

    def _mark_status(new_status: str, error_msg: str = ""):
        """อัปเดต status ใน meta เสมอ — ป้องกันไฟล์ค้างที่ 'processing'"""
        try:
            m = _load_meta()
            if fid in m:
                m[fid]["status"] = new_status
                if error_msg:
                    m[fid]["error"] = error_msg
                _save_meta(m)
        except Exception:
            pass

    if not _get_kb().is_key_valid():
        logger.error(f"❌ API Key not valid while ingesting {original_name}")
        _mark_status("error", "API Key not set")
        return {"status": "error", "error": "API Key not set. Cannot ingest file.", "file_id": fid, "name": original_name}

    try:
        chunks, chunk_metas = FileProcessor.parse(file_path)
    except Exception as e:
        logger.error(f"❌ Parsing Error: {e}")
        _mark_status("error", f"Parsing failed: {e}")
        return {"status": "error", "error": f"Parsing failed: {e}", "file_id": fid, "name": original_name}

    if not chunks:
        _mark_status("empty")
        return {"status": "empty", "file_id": fid, "name": original_name}

    for m in chunk_metas:
        m["department"] = department
        m["category_id"] = str(category_id) if category_id is not None else ""
        m["organization_id"] = org_id

    try:
        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_metas  = chunk_metas[i : i + batch_size]
            _get_kb().add_chunks(batch_chunks, source_name=original_name, file_id=fid, metadatas=batch_metas)
            gc.collect()
    except Exception as e:
        err_str = str(e)
        _mark_status("error", err_str)
        if "DAILY_QUOTA_EXCEEDED" in err_str:
            raise e
        logger.error(f"❌ Error adding chunks for {original_name}: {e}")
        return {"status": "error", "error": err_str, "file_id": fid, "name": original_name}
    finally:
        gc.collect()

    meta[fid] = {
        "name": original_name,
        "path": str(file_path),
        "chunks": len(chunks),
        "size": file_path.stat().st_size,
        "type": file_path.suffix.lower().lstrip("."),
        "department": department,
        "category_id": category_id,
        "organization_id": org_id,
        "status": "ready",
        "api_key_status": _get_kb().api_key[:5] + "..." if _get_kb().is_key_valid() else "MISSING KEY",
        "timestamp": meta[fid].get("timestamp", datetime.now().isoformat())
    }
    _save_meta(meta)
    return {"status": "ok", "file_id": fid, "name": original_name, "chunks": len(chunks),
            "department": department, "category_id": category_id, "organization_id": org_id}


def set_file_drive_link(file_id: str, link: str) -> bool:
    """เก็บลิงก์ Google Drive ของไฟล์ต้นฉบับไว้ใน metadata เพื่อแสดงในแหล่งอ้างอิง"""
    try:
        m = _load_meta()
        if file_id in m:
            m[file_id]["drive_link"] = link or ""
            _save_meta(m)
            return True
    except Exception as e:
        logger.warning(f"set_file_drive_link failed: {e}")
    return False


def ingest_text(text: str, source_name: str, department: str = "General", category_id: int = None, org_id: int = 1) -> dict:
    """Useful for ingesting Wiki pages or AI-generated content directly."""
    if not text.strip():
        return {"status": "empty"}

    import hashlib
    source_id = hashlib.sha256(source_name.encode()).hexdigest()[:12]

    # First, clear previous version of this source if it exists
    _get_kb().delete_by_source(source_name)

    chunks = _chunk_text(text)
    chunk_metas = []
    for _ in chunks:
        m = {"department": department, "source": source_name, "type": "wiki", "organization_id": org_id}
        m["category_id"] = category_id
        chunk_metas.append(m)

    try:
        _get_kb().add_chunks(chunks, source_name=source_name, file_id=f"text_{source_id}", metadatas=chunk_metas)
        return {"status": "ok", "chunks": len(chunks), "source": source_name}
    except Exception as e:
        logger.error(f"❌ ingest_text Error: {e}")
        return {"status": "error", "error": str(e)}


def list_files(org_id: int = None) -> list[dict]:
    meta = _load_meta()
    files = [{"file_id": fid, **info} for fid, info in meta.items()]
    if org_id is not None:
        files = [f for f in files if f.get("organization_id") == org_id]
    return files

def delete_file(file_id: str, delete_from_disk: bool = True, org_id: int = None) -> bool:
    meta = _load_meta()
    if file_id not in meta:
        return False

    # Check org_id if provided
    if org_id is not None and meta[file_id].get("organization_id") != org_id:
        return False

    _get_kb().delete_by_file_id(file_id)
    info = meta.pop(file_id)
    _save_meta(meta)
    if delete_from_disk:
        try:
            Path(info["path"]).unlink(missing_ok=True)
        except Exception:
            pass
    return True

def update_file_category(file_id: str, category_id: int) -> bool:
    """Updates the category assigned to a file in metadata."""
    meta = _load_meta()
    if file_id not in meta:
        return False
    meta[file_id]["category_id"] = category_id
    _save_meta(meta)
    
    # Also update vector database chunks
    _get_kb().update_metadata_by_file_id(file_id, {"category_id": category_id})
    return True


def rename_file(file_id: str, new_name: str, org_id: int = None) -> dict:
    """Renames a file in file_meta.json, renames file on disk if exists, and updates ChromaDB chunk metadata."""
    meta = _load_meta()
    if file_id not in meta:
        return {"ok": False, "error": "ไม่พบไฟล์ที่ระบุในระบบ"}

    info = meta[file_id]
    if org_id is not None and info.get("organization_id") is not None and info.get("organization_id") != org_id:
        return {"ok": False, "error": "คุณไม่มีสิทธิ์แก้ไขไฟล์ในองค์กรนี้"}

    new_name = (new_name or "").strip()
    if not new_name:
        return {"ok": False, "error": "ชื่อไฟล์ต้องไม่ว่างเปล่า"}

    old_name = info.get("name", "")
    old_ext = Path(old_name).suffix
    new_ext = Path(new_name).suffix

    # If new_name does not have an extension, retain original extension
    if not new_ext and old_ext:
        new_name = new_name + old_ext
        new_ext = old_ext

    # Rename physical file on disk safely
    old_path_str = info.get("path")
    new_path_str = old_path_str
    if old_path_str:
        try:
            old_path = Path(old_path_str)
            if old_path.exists():
                safe_name = re.sub(r'[\\/:*?"<>|]', '_', new_name).strip()
                prefix = f"{file_id[:8]}_"
                new_disk_filename = f"{prefix}{safe_name}"
                new_disk_path = old_path.parent / new_disk_filename
                if old_path != new_disk_path:
                    old_path.rename(new_disk_path)
                    new_path_str = str(new_disk_path)
        except Exception as e:
            logger.warning(f"⚠️ Warning: Could not rename file on disk: {e}")

    info["name"] = new_name
    info["path"] = new_path_str
    if new_ext:
        info["type"] = new_ext.lower().lstrip(".")
    _save_meta(meta)

    # Sync metadata in vector database
    try:
        _get_kb().update_metadata_by_file_id(file_id, {"source": new_name})
    except Exception as e:
        logger.warning(f"⚠️ Warning: vector metadata rename update: {e}")

    return {"ok": True, "file_id": file_id, "name": new_name}


def reprocess_file(file_id: str, org_id: int = None) -> dict:
    """
    Re-chunks and re-embeds a specific file in the Knowledge Base.
    Useful for retrying files that failed due to temporary network/API errors.
    """
    meta = _load_meta()
    if file_id not in meta:
        return {"ok": False, "error": "ไม่พบไฟล์ที่ระบุในระบบ"}

    info = meta[file_id]
    if org_id is not None and info.get("organization_id") is not None and info.get("organization_id") != org_id:
        return {"ok": False, "error": "คุณไม่มีสิทธิ์จัดการไฟล์ในองค์กรนี้"}

    file_path = Path(info.get("path", ""))
    if not file_path.exists() or not file_path.is_file():
        actual_name = file_path.name
        alt_path = UPLOAD_DIR / actual_name
        if alt_path.exists() and alt_path.is_file():
            file_path = alt_path
        else:
            return {"ok": False, "error": f"ไม่พบไฟล์ต้นฉบับในเซิร์ฟเวอร์ ({actual_name})"}

    # Remove stale chunks from vector DB first
    try:
        _get_kb().delete_by_file_id(file_id)
    except Exception as e:
        logger.warning(f"⚠️ [Reprocess] Notice deleting old chunks for {file_id}: {e}")

    meta[file_id]["status"] = "processing"
    meta[file_id]["chunks"] = 0
    meta[file_id].pop("error", None)
    _save_meta(meta)

    orig_name = info.get("name", file_path.name)
    dept = info.get("department", "General")
    cat_id = info.get("category_id")
    file_org_id = info.get("organization_id", 1)

    res = ingest_file(file_path, original_name=orig_name, department=dept, category_id=cat_id, org_id=file_org_id, force=True)
    if res.get("status") == "error":
        return {"ok": False, "error": res.get("error", "เกิดข้อผิดพลาดในการประมวลผล")}
    
    return {"ok": True, "file_id": file_id, "chunks": res.get("chunks", 0), "status": "ready"}


def get_file_content(file_id: str) -> str:
    """Retrieve all text chunks for a specific file_id from vector store."""
    try:
        results = _get_kb().collection.get(where={"file_id": file_id})
        docs = results.get("documents", [])
        if not docs:
            # Fallback: check if it's a 'source' name instead of hash ID
            results = _get_kb().collection.get(where={"source": file_id})
            docs = results.get("documents", [])
        return "\n".join(docs)
    except Exception as e:
        logger.error(f"❌ Error getting file content for {file_id}: {e}")
        return ""


def retrieve_context(question: str, where: dict = None) -> tuple[str, list[dict]]:
    """Return (context_text, list_of_detailed_sources) for the question."""
    logger.info(f"[SEARCH] Starting RAG retrieval for: '{question[:20]}...' Filter: {where}")
    
    # ⚡ FAST PATH: Skip ChromaDB / RAG for pure standalone greetings or single-character noise
    try:
        clean_q = re.sub(r'[0-9๐-๙\s\W_]', '', question)
        # Skip only if truly empty or single character
        if not question or len(clean_q) < 2:
            print(f"ℹ️ Fast Path: Skipping RAG for noisy/short query: '{question}'", flush=True)
            return "", []
        # Skip pure generic greetings that don't need doc retrieval
        standalone_greetings = {"สวัสดี", "หวัดดี", "ฮัลโหล", "hi", "hello", "hey", "ดีครับ", "ดีค่ะ", "มอนิ่ง", "อรุณสวัสดิ์"}
        if clean_q.lower() in standalone_greetings:
            print(f"ℹ️ Fast Path: Skipping RAG for pure greeting: '{question}'", flush=True)
            return "", []
    except Exception as fe:
        logger.error(f"⚠️ Fast Path check error: {fe}")

    final_results = []
    
    try:
        # 1. Filename-based boost (Optimized for Thai: No split needed)
        filename_chunks = []
        if question and len(question) > 2:
            try:
                # 1a. Efficiently get candidates: Fetch unique source names first
                inv_data = _get_kb().collection.get(include=['metadatas'], limit=100)
                sources_in_db = list(set([m.get("source") for m in inv_data.get("metadatas", []) if m.get("source")]))
                
                # 1b. Match filenames against the RAW question (Better for Thai)
                matched_sources = [s for s in sources_in_db if s.lower() in question.lower()]
                
                if matched_sources:
                    logger.info(f"📂 Thai Match filenames: {matched_sources}")
                    # Fetch chunks for matched files
                    f_res = _get_kb().collection.get(
                        where={"source": {"$in": matched_sources}} if not where else {"$and": [where, {"source": {"$in": matched_sources}}]},
                        limit=5
                    )
                    if f_res and f_res['documents']:
                        for i in range(len(f_res['documents'])):
                            filename_chunks.append({
                                "text": f_res['documents'][i],
                                "score": 1.0,
                                **f_res['metadatas'][i]
                            })
            except Exception as fe:
                logger.error(f"⚠️ Filename match error: {fe}")
        
        # 2. Standard Hybrid Query (Semantic + Keyword)
        results = _get_kb().hybrid_query(question, n_results=10, where=where)
        # Filter by score dynamically (keep only >= 0.25 AND within 0.35 of the top score, or keyword matched)
        if results:
            max_score = max(r.get("score", 0) for r in results)
            results = [r for r in results if (r.get("score", 0) >= 0.25 and r.get("score", 0) >= (max_score - 0.35)) or r.get("keyword_matches")]
        
        # Merge results, prioritize filename chunks
        seen_texts = set()
        for r in filename_chunks + results:
            text_small = r.get("text", "")[:200]
            if text_small not in seen_texts:
                final_results.append(r)
                seen_texts.add(text_small)
                
        logger.info(f"✅ RAG query finished. Returned {len(final_results)} relevant chunks.")
    except Exception as e:
        print(f"❌ RAG query error: {e} (filter={where})", flush=True)
        import traceback
        traceback.print_exc()
        return "", []

    if not final_results:
        logger.info("ℹ️ No relevant context found.")
        return "", []
    
    results = final_results[:10] # Limit context size
    
    # Enrich context with location info
    context_parts = []
    detailed_sources = []
    seen_source_keys = set()
    
    try:
        _meta_all = _load_meta()
    except Exception:
        _meta_all = {}
    for idx, r in enumerate(results, 1):
        loc = r.get("location", "Document")
        dept = r.get("department", "General")
        src = r.get("source", "?")
        fid = r.get("file_id", "")
        
        # Build context text for AI
        context_parts.append(f"[เอกสารอ้างอิง {idx}] แหล่งที่มา: {src} [{loc}] ({dept})\nเนื้อหา:\n{r['text']}\n")
        
        # Build structured sources for UI
        source_key = f"{fid}_{loc}"
        if source_key not in seen_source_keys:
            detailed_sources.append({
                "file_id": fid,
                "name": src,
                "location": loc,
                "department": dept,
                "type": r.get("type", "file"),
                "drive_link": (_meta_all.get(fid) or {}).get("drive_link", ""),
            })
            seen_source_keys.add(source_key)
        
    context = "\n\n".join(context_parts)
    logger.info(f"[CONTEXT] Context prepared: {len(context)} chars, {len(detailed_sources)} detailed sources.")
    return context, detailed_sources


def kb_stats(org_id: int = None) -> dict:
    meta = _load_meta()
    if org_id is not None:
        org_files = [f for f in meta.values() if f.get("organization_id") == org_id]
        total_files = len(org_files)
        # Approximate chunks for this org if we don't want to query ChromaDB for each chunk's org_id
        # In a real system, we'd query the vector DB with a where filter for count.
        # For now, let's use the metadata if available or a filtered count if possible.
        return {
            "total_chunks": "N/A", # Needs vector DB count with where filter
            "total_files": total_files,
            "knowledge_base_size": total_files
        }

    chunks = _get_kb().total_chunks()
    return {
        "total_chunks": chunks,
        "total_files": len(meta),
        "knowledge_base_size": chunks
    }


def get_quota_status() -> dict:
    """Check quota for current embedding function."""
    res = {"embedding_quota_hit": False, "provider": "gemini"}
    ef = getattr(_get_kb().collection, "_embedding_function", None)
    if ef:
        if isinstance(ef, BatchedGoogleEmbeddingFunction):
            res["embedding_quota_hit"] = ef.daily_quota_hit
            res["provider"] = "gemini"
        elif isinstance(ef, OllamaEmbeddingFunction):
            res["embedding_quota_hit"] = False # Local doesn't have daily quota
            res["provider"] = "ollama"
    return res


def prune_kb() -> int:
    """Consolidate and remove orphaned chunks from the vector database."""
    meta = _load_meta()
    valid_ids = list(meta.keys())
    return _get_kb().prune_orphaned_chunks(valid_ids)

def wipe_knowledge_base():
    """Wipe all data from the knowledge base and clear meta."""
    meta = _load_meta()
    for fid, info in meta.items():
        try:
            Path(info["path"]).unlink(missing_ok=True)
        except Exception:
            pass
def cleanup_stale_processing(max_age_minutes: int = 30) -> int:
    """
    ล้างไฟล์ที่ติดอยู่ที่ status='processing' นานเกิน max_age_minutes
    คืนค่าจำนวนไฟล์ที่ถูกทำเครื่องหมายเป็น 'error'
    """
    from datetime import timezone as _tz
    meta = _load_meta()
    now = datetime.now(_tz.utc)
    changed = 0
    for fid, info in meta.items():
        if info.get("status") != "processing":
            continue
        ts_str = info.get("timestamp", "")
        if not ts_str:
            info["status"] = "error"
            info["error"] = "processing timeout (no timestamp)"
            changed += 1
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=_tz.utc)
            age_min = (now - ts).total_seconds() / 60
            if age_min > max_age_minutes:
                info["status"] = "error"
                info["error"] = f"processing timeout ({int(age_min)} นาที)"
                changed += 1
                logger.error(f"[Cleanup] {info.get('name')} stuck {int(age_min)}m → error")
        except Exception:
            info["status"] = "error"
            info["error"] = "processing timeout (invalid timestamp)"
            changed += 1
    if changed:
        _save_meta(meta)
    return changed


def fix_categories():
    """Sync and normalize category_ids from meta file to ChromaDB."""
    meta = _load_meta()
    return _get_kb().fix_chroma_categories(meta)

def sync_uploads():
    """Scan the uploads folder and ingest any files that are not already in meta."""
    meta = _load_meta()
    existing_hashes = set(meta.keys())
    results = []
    
    if not UPLOAD_DIR.exists():
        return results

    # Removed is_key_valid check as we use local embeddings now

    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            try:
                fid = _file_hash(file_path)
                
                # DEEP SYNC FIX: Check if the file actually has data in ChromaDB
                in_db = False
                try:
                    db_check = _get_kb().collection.get(where={"file_id": fid}, limit=1)
                    if db_check and db_check.get("ids"):
                        in_db = True
                except Exception as e:
                    logger.debug(f"[SYNC] Collection check notice for {file_path.name}: {e}")

                if fid not in existing_hashes or not in_db:
                    logger.info(f"[SYNC] Re-ingesting or Syncing file: {file_path.name}")
                    existing_info = meta.get(fid, {})
                    original_name = existing_info.get("name")
                    if not original_name:
                        original_name = file_path.name
                        if len(file_path.name) > 9 and file_path.name[8] == "_":
                            original_name = file_path.name[9:]
                    
                    dept = existing_info.get("department", "General")
                    cat_id = existing_info.get("category_id")
                    org_id = existing_info.get("organization_id", 1)

                    try:
                        _get_kb().delete_by_file_id(fid)
                    except Exception:
                        pass

                    res = ingest_file(file_path, original_name=original_name, department=dept, category_id=cat_id, org_id=org_id, force=True)
                    results.append(res)
            except Exception as e:
                logger.error(f"⚠️ Error syncing {file_path.name}: {e}")
                continue
    return results


def search_kb(question: str, n_results: int = 5, where: dict = None) -> list[dict]:
    """Perform a raw search in the knowledge base with optional permissions filter."""
    return _get_kb().hybrid_query(question, n_results=n_results, where=where)

def query(question: str, n_results: int = 4, where: dict = None) -> list[dict]:
    """Alias for search_kb to maintain compatibility."""
    return search_kb(question, n_results=n_results, where=where)

def get_all_chunks(where: dict = None, limit: int = 20) -> list[dict]:
    """Fetch raw chunks from the knowledge base without semantic search."""
    data = _get_kb().collection.get(where=where, limit=limit)
    docs = data.get("documents", [])
    metas = data.get("metadatas", [])
    
    # Simple deduplication by content
    seen = set()
    results = []
    for d, m in zip(docs, metas):
        if d in seen: continue
        seen.add(d)
        item = {"text": d, "score": 0.5}
        item.update(m)
        results.append(item)
    return results


# ═══════════════════════════════════════════════════════════════
# 🔍 Automated KB Duplicate & Anomaly File Detector (Enterprise)
# ═══════════════════════════════════════════════════════════════

def detect_kb_duplicates_and_anomalies(org_id: int = 1) -> dict:
    """
    Scans all files in knowledge base metadata and uploads to detect:
      1. Exact file content duplicates (SHA-256 Hash collisions)
      2. Duplicate original file names uploaded under different IDs
      3. Orphaned / Corrupted / Missing disk files
      4. Empty or unindexed document chunks (Zero Chunk Anomalies)
    """
    meta = _load_meta()
    
    hash_map = {}          # { sha256: [file_info, ...] }
    name_map = {}          # { name_lower: [file_info, ...] }
    duplicates = []
    anomalies = []
    healthy_files = []

    for fid, info in meta.items():
        if info.get("organization_id") and info.get("organization_id") != org_id:
            continue

        name = info.get("name", "Unnamed")
        file_path_str = info.get("path")
        chunks_count = info.get("chunks", 0)
        size = info.get("size", 0)
        status = info.get("status", "unknown")

        file_entry = {
            "file_id": fid,
            "name": name,
            "path": file_path_str,
            "chunks": chunks_count,
            "size": size,
            "status": status,
            "department": info.get("department", "General")
        }

        # 1. Check physical existence on disk
        if not file_path_str or not Path(file_path_str).exists():
            anomalies.append({
                "type": "MISSING_DISK_FILE",
                "severity": "HIGH",
                "file_id": fid,
                "name": name,
                "description": f"ไฟล์ '{name}' มีบันทึกในระบบแต่ไฟล์จริงบน Disk หายไป"
            })
            continue

        p = Path(file_path_str)

        # 2. Check 0-byte or 0-chunk anomaly
        if size == 0 or chunks_count == 0:
            anomalies.append({
                "type": "EMPTY_OR_UNINDEXED",
                "severity": "MEDIUM",
                "file_id": fid,
                "name": name,
                "description": f"ไฟล์ '{name}' มีขนาด 0 bytes หรือไม่มี Chunks ถูกแปลงลงฐานข้อมูล AI"
            })

        # 3. Calculate SHA-256 for exact binary duplication
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            file_entry["sha256"] = h
            hash_map.setdefault(h, []).append(file_entry)
        except Exception as e:
            anomalies.append({
                "type": "READ_ERROR",
                "severity": "HIGH",
                "file_id": fid,
                "name": name,
                "description": f"ไม่สามารถอ่านไฟล์ '{name}' ได้: {e}"
            })
            continue

        # 4. Track file names for duplicate names
        name_lower = name.strip().lower()
        name_map.setdefault(name_lower, []).append(file_entry)
        healthy_files.append(file_entry)

    # Detect exact binary duplicates
    for sha, group in hash_map.items():
        if len(group) > 1:
            duplicates.append({
                "type": "EXACT_BINARY_DUPLICATE",
                "sha256": sha,
                "count": len(group),
                "files": group,
                "suggestion": f"ตรวจพบไฟล์เนื้อหาซ้ำกันเป๊ะ {len(group)} ไฟล์ ({', '.join(f['name'] for f in group)}) ควรลบไฟล์ส่วนเกินเพื่อประหยัดพื้นที่และลดความสับสนของ AI"
            })

    # Detect duplicate filenames
    for name, group in name_map.items():
        if len(group) > 1 and not any(d["sha256"] == group[0].get("sha256") for d in duplicates if "sha256" in d):
            duplicates.append({
                "type": "FILENAME_COLLISION",
                "name": name,
                "count": len(group),
                "files": group,
                "suggestion": f"ตรวจพบชื่อไฟล์ซ้ำกัน {len(group)} รายการแต่เนื้อหาต่างกัน ({', '.join(f['file_id'] for f in group)})"
            })

    total_scanned = len(meta)
    return {
        "ok": True,
        "total_scanned": total_scanned,
        "healthy_count": len(healthy_files),
        "duplicate_groups_count": len(duplicates),
        "anomalies_count": len(anomalies),
        "duplicates": duplicates,
        "anomalies": anomalies,
        "scan_time": datetime.now().isoformat()
    }

