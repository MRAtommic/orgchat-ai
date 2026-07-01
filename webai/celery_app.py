"""
Celery Application — Task Queue for OrgChat AI
================================================
Broker & Backend: Redis (ผ่าน REDIS_URL env var)
Fallback: ถ้าไม่มี Redis จะ log warning และ task จะรันแบบ synchronous (eager mode)

Queues:
  - default      : งานทั่วไป (upload, AI scan) — concurrency=2
  - sheets-write  : เขียน Google Sheets — concurrency=1 (serial, ป้องกันทับซ้อน)
"""

import os
import logging

logger = logging.getLogger(__name__)

# ─── Redis URL ────────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "").strip()

# ─── Celery Instance ─────────────────────────────────────────
from celery import Celery

celery_app = Celery("orgchat")

if REDIS_URL:
    celery_app.conf.update(
        broker_url=REDIS_URL,
        result_backend=REDIS_URL,
        broker_connection_retry_on_startup=True,
    )
    logger.info(f"✅ Celery broker: Redis ({REDIS_URL[:30]}...)")
else:
    # Fallback: eager mode — ทำงานแบบ synchronous ใน process เดียว (สำหรับ local dev ที่ไม่มี Redis)
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
    logger.warning("⚠️ REDIS_URL not set — Celery running in EAGER mode (synchronous, no real queue)")

# ─── Common Config ───────────────────────────────────────────
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="Asia/Bangkok",
    enable_utc=True,

    # Queue routing
    task_default_queue="default",
    task_routes={
        "tasks.sheets_queue.*": {"queue": "sheets-write"},
    },

    # Worker settings
    worker_prefetch_multiplier=1,     # ดึงงานทีละ 1 (ป้องกัน queue starvation)
    task_acks_late=True,              # ack หลังทำเสร็จ (ถ้า worker crash งานจะ retry)
    task_reject_on_worker_lost=True,  # reject ถ้า worker หาย

    # Retry defaults
    task_default_retry_delay=5,       # retry หลัง 5 วินาที
    task_max_retries=3,

    # Result expiry
    result_expires=3600,  # ผลลัพธ์หมดอายุหลัง 1 ชม.
)

# ─── Auto-discover tasks ─────────────────────────────────────
celery_app.autodiscover_tasks(["tasks"])
