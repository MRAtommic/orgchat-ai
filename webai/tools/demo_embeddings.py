# -*- coding: utf-8 -*-
"""สาธิตให้กรรมการ: เอกสาร -> ตัดเป็นท่อน -> เวกเตอร์ -> เก็บใน ChromaDB -> ค้นหาตามความหมาย
ใช้โฟลเดอร์ชั่วคราว ไม่แตะฐานข้อมูลจริงและไม่อ่าน .env
รัน:  python tools/demo_embeddings.py
      python tools/demo_embeddings.py "คำถามของคุณ" "คำถามที่ 2"          (ถามเอง)
      python tools/demo_embeddings.py --file เอกสาร.txt "คำถามของคุณ"     (ใช้เอกสารของคุณเอง)
"""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tmp = tempfile.mkdtemp(prefix="demo_emb_")
os.environ["DATA_DIR"] = tmp
os.environ["VECTOR_BACKEND"] = "python"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import rag_engine as R  # noqa: E402

_args = sys.argv[1:]
_file = None
if "--file" in _args:
    _i = _args.index("--file")
    _file = _args[_i + 1]
    del _args[_i:_i + 2]

DOC = ("นโยบายการลาของบริษัท พนักงานมีสิทธิ์ลาพักร้อนปีละ 10 วัน ต้องยื่นคำขอล่วงหน้าอย่างน้อย 3 วันทำงาน "
       "การลาป่วยเกิน 2 วันต้องแนบใบรับรองแพทย์ "
       "สวัสดิการค่ารักษาพยาบาลเบิกได้ไม่เกิน 5,000 บาทต่อปี "
       "เวลาทำงานปกติ 8:30 ถึง 17:30 น. วันจันทร์ถึงวันศุกร์ พักกลางวัน 1 ชั่วโมง")

print("=" * 70, "\n1) เอกสารต้นฉบับ\n", "=" * 70)
print(DOC)

chunks = R._chunk_text(DOC, chunk_size=120, overlap=20)
print("\n" + "=" * 70, f"\n2) ตัดเป็นท่อน (chunk) ได้ {len(chunks)} ท่อน\n", "=" * 70)
for i, c in enumerate(chunks):
    print(f"  ท่อน {i}: {c}")

ef = R.FastEmbedEmbeddingFunction()
vecs = [v.tolist() if hasattr(v, "tolist") else list(v) for v in ef(chunks)]
print("\n" + "=" * 70, f"\n3) แปลงเป็นเวกเตอร์ : แต่ละท่อน = ตัวเลข {len(vecs[0])} ตัว\n", "=" * 70)
for i, v in enumerate(vecs):
    print(f"  ท่อน {i}: [{', '.join(f'{x:+.3f}' for x in v[:8])}, ... อีก {len(v) - 8} ตัว]")

import chromadb  # noqa: E402
client = chromadb.PersistentClient(path=os.path.join(tmp, "chroma"),
                                   settings=chromadb.config.Settings(anonymized_telemetry=False))
col = client.get_or_create_collection("demo", metadata={"hnsw:space": "cosine"})
col.upsert(ids=[f"doc1_{i}" for i in range(len(chunks))], documents=chunks, embeddings=vecs,
           metadatas=[{"source": "นโยบายการลา.pdf", "chunk": i} for i in range(len(chunks))])
print("\n" + "=" * 70, f"\n4) เก็บลง ChromaDB แล้ว : {col.count()} รายการ (ข้อความ + เวกเตอร์ + ที่มา)\n", "=" * 70)
rec = col.get(include=["documents", "metadatas"], limit=1)
print("  ตัวอย่าง 1 รายการ:", {"id": rec["ids"][0], "metadata": rec["metadatas"][0], "document": rec["documents"][0][:50] + "..."})

for q in (_args or ["ขอหยุดงานไปเที่ยวได้กี่วัน", "ไปหาหมอเบิกเงินได้เท่าไหร่", "เข้างานกี่โมง"]):
    qv = ef([q])[0]
    qv = qv.tolist() if hasattr(qv, "tolist") else list(qv)
    r = col.query(query_embeddings=[qv], n_results=2, include=["documents", "distances"])
    print("\n" + "=" * 70, f"\n5) ค้นหาตามความหมาย : \"{q}\"\n", "=" * 70)
    for d, dist in zip(r["documents"][0], r["distances"][0]):
        print(f"  ความคล้าย {1 - dist:.0%}  ->  {d}")
    print("  (สังเกต: คำถามไม่ได้ใช้คำเดียวกับเอกสาร แต่ระบบหาท่อนที่ความหมายตรงเจอ)")
    print("  -> ท่อนเหล่านี้จะถูกส่งให้ AI (Groq Llama / Gemini) ใช้เรียบเรียงคำตอบ")

del col, client
shutil.rmtree(tmp, ignore_errors=True)
