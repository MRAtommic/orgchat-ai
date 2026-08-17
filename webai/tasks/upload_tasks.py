"""
Upload Tasks — Background Tasks for File Uploads and AI Smart Scan
===================================================================
"""

import logging
import os
import sys

# Ensure parent directory is in sys.path so we can import modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import celery_app
from redis_manager import RedisManager
import database

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.upload_tasks.process_pending_uploads_task",
    bind=True,
    max_retries=1,
    default_retry_delay=5,
)
def process_pending_uploads_task(self, pending_id, dest_id, folder_id, folder_name, reply_token):
    """
    Celery task wrapper to process uploads asynchronously.
    """
    logger.info(f"🚀 [Upload Task] Started processing {pending_id} for destination {dest_id}")
    
    # 1. Resolve org_id
    try:
        import database
        _upload_org_id = database.get_org_id_by_line_group(dest_id) if (dest_id.startswith("C") or dest_id.startswith("R")) else database.get_org_id_by_line_user(dest_id)
        if _upload_org_id is None:
            _upload_org_id = 1
    except Exception as e:
        logger.error(f"❌ Failed to resolve org_id: {e}")
        _upload_org_id = 1

    # 2. Get files from Redis (using the upgraded RedisManager)
    files = RedisManager.pop_pending_files(pending_id)
    if not files:
        logger.warning(f"⚠️ No pending files found for {pending_id}")
        RedisManager.release_upload_lock(pending_id)
        return {"ok": False, "error": "No pending files"}

    try:
        # Import the inner processor function from routes.chat to run the exact same logic
        from routes.chat import _process_pending_uploads_inner
        _process_pending_uploads_inner(pending_id, dest_id, folder_id, folder_name, reply_token, files, _upload_org_id)
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Upload task execution failed: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}
    finally:
        RedisManager.release_upload_lock(pending_id)
