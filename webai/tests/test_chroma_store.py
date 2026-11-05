# -*- coding: utf-8 -*-
"""ChromaStore must behave like the old PurePythonVectorStore for every filter shape the app produces.
Differential test with a deterministic fake embedder; uses only temp directories (never real data)."""
import hashlib
import json
import tempfile
from pathlib import Path

try:
    import pytest
except ImportError:
    import unittest
    raise unittest.SkipTest("pytest not installed; skipping test_chroma_store")

import rag_engine as R

pytestmark = pytest.mark.skipif(R.chromadb is None, reason="chromadb not installed")

DIM = 24


def fake_ef(texts):
    out = []
    for t in texts:
        h = hashlib.sha256(t.encode("utf-8")).digest()
        v = [(b - 127.5) / 127.5 for b in h[:DIM]]
        out.append(v)
    return out


ROWS = []
for i in range(30):
    ROWS.append({
        "id": f"f{i % 6}_chunk_{i}",
        "document": f"เอกสารที่ {i} เรื่อง {'บัญชี' if i % 3 == 0 else 'บุคคล' if i % 3 == 1 else 'ทั่วไป'} รายละเอียด {i}",
        "metadata": {
            "source": f"file{i % 6}.pdf", "file_id": f"f{i % 6}",
            "organization_id": 1 if i < 18 else 2,
            "category_id": ["", "3", "4"][i % 3],
            "department": ["General", "บัญชี"][i % 2], "location": f"Page {i % 5 + 1}",
        },
    })


@pytest.fixture(scope="module")
def stores():
    tmp = tempfile.mkdtemp()
    py = R.PurePythonVectorStore(fake_ef, Path(tmp) / "py.json")
    docs = [r["document"] for r in ROWS]
    py.upsert(docs, [r["id"] for r in ROWS], [dict(r["metadata"]) for r in ROWS])
    # Chroma seeded from the python store's JSON (exactly the production migration path)
    ch = R.ChromaStore.open(fake_ef, Path(tmp) / "chroma", "test_col", seed_json=Path(tmp) / "py.json")
    return py, ch, tmp


FILTERS = {
    "none": None,
    "org eq": {"organization_id": 1},
    "org str": {"organization_id": "1"},
    "org+cat in+unassigned (get_rag_filter)": {"$and": [{"organization_id": 1}, {"$or": [{"category_id": {"$in": ["3", "4"]}}, {"category_id": ""}]}]},
    "cat in only": {"category_id": {"$in": ["3"]}},
    "cat in ints": {"category_id": {"$in": [3, 4]}},
    "cat in mixed": {"category_id": {"$in": ["3", 4]}},
    "unassigned only (single or)": {"$or": [{"category_id": ""}]},
    "org + unassigned (single or)": {"$and": [{"organization_id": 1}, {"$or": [{"category_id": ""}]}]},
    "single and": {"$and": [{"organization_id": 2}]},
    "org or null (legacy)": {"$or": [{"organization_id": 1}, {"organization_id": {"$eq": None}}]},
    "cat eq None": {"category_id": {"$eq": None}},
    "cat int vs str": {"category_id": 3},
    "source in": {"$and": [{"organization_id": 1}, {"source": {"$in": ["file1.pdf", "file2.pdf"]}}]},
    "file id": {"file_id": "f2"},
    "empty in": {"category_id": {"$in": []}},
    "impossible org": {"organization_id": -1},
    "org + cat int": {"$and": [{"organization_id": 1}, {"$or": [{"category_id": 3}, {"category_id": "3"}]}]},
    "multi-key dict": {"organization_id": 1, "category_id": "3"},
    "dept": {"$and": [{"organization_id": 1}, {"department": "บัญชี"}]},
    "empty dict": {},
}


@pytest.mark.parametrize("name", list(FILTERS))
def test_get_matches_python_store(stores, name):
    py, ch, _ = stores
    f = FILTERS[name]
    a = set(py.get(where=f)["ids"])
    b = set(ch.get(where=f)["ids"])
    assert a == b, f"{name}: python={sorted(a)} chroma={sorted(b)}"


@pytest.mark.parametrize("name", [n for n in FILTERS if n not in ("empty in",)])
def test_query_matches_python_store(stores, name):
    py, ch, _ = stores
    f = FILTERS[name]
    q = "เอกสารเรื่องบัญชี"
    a = py.query([q], n_results=5, where=f)
    b = ch.query([q], n_results=5, where=f)
    ids_a = [m["file_id"] + m["location"] for m in a["metadatas"][0]]
    ids_b = [m["file_id"] + m["location"] for m in b["metadatas"][0]]
    assert ids_a == ids_b, f"{name}: python={ids_a} chroma={ids_b}"
    for da, db in zip(a["distances"][0], b["distances"][0]):
        assert abs(da - db) < 1e-3


def test_seed_imported_everything(stores):
    py, ch, _ = stores
    assert ch.count() == py.count() == len(ROWS)


def test_survives_reopen(stores):
    py, ch, tmp = stores
    again = R.ChromaStore.open(fake_ef, Path(tmp) / "chroma", "test_col", seed_json=Path(tmp) / "py.json")
    assert again.count() == len(ROWS)  # not re-seeded / not duplicated


def test_upsert_update_delete_by_where():
    tmp = tempfile.mkdtemp()
    ch = R.ChromaStore.open(fake_ef, Path(tmp) / "c", "t_col")
    ch.upsert(["a", "b"], ["x_chunk_0", "y_chunk_0"],
              [{"source": "x", "file_id": "x", "organization_id": 1, "category_id": None},
               {"source": "y", "file_id": "y", "organization_id": 2, "category_id": "9", "weird": None}])
    assert ch.count() == 2
    assert ch.get(where={"category_id": ""})["ids"] == ["x_chunk_0"], "None category must be stored as empty string"
    ch.update(["x_chunk_0"], [{"source": "x", "file_id": "x", "organization_id": 1, "category_id": "5"}])
    assert ch.get(where={"category_id": {"$in": [5]}})["ids"] == ["x_chunk_0"]
    ch.delete(where={"file_id": "y"})
    assert ch.count() == 1
    ch.delete(ids=["x_chunk_0"])
    assert ch.count() == 0
    ch.upsert(["a"], ["z_chunk_0"], [{"source": "z", "file_id": "z", "organization_id": 1}])
    ch.delete(where={"organization_id": {"$eq": None}})  # matches nothing, must not wipe
    assert ch.count() == 1
    ch.delete(where={})  # empty filter must never wipe the store
    ch.delete()
    assert ch.count() == 1


def test_cross_tenant_isolation_in_query(stores):
    _, ch, _ = stores
    r = ch.query(["เอกสาร"], n_results=30, where={"organization_id": 2})
    assert r["metadatas"][0] and all(m["organization_id"] == 2 for m in r["metadatas"][0])


def test_real_production_filter_builder(stores, monkeypatch):
    """The filter produced by routes.shared.get_rag_filter (restricted user) must work and stay tenant-scoped."""
    py, ch, _ = stores
    from routes import shared
    monkeypatch.setattr(shared.database, "get_categories", lambda u, org_id=None: [{"id": 3}, {"id": 4}])
    monkeypatch.setattr(shared.database, "get_user_setting", lambda u: {"role": "user"})
    f = shared.get_rag_filter("someone", org_id=1)
    a, b = set(py.get(where=f)["ids"]), set(ch.get(where=f)["ids"])
    assert a == b and a
    assert all(ch.get(where={"$and": [f, {"file_id": x}]}) is not None for x in ("f0", "f1"))
