#!/bin/bash
# OrgChat AI — Production Startup Script (Linux)
# ใช้ Gunicorn + gthread worker (รองรับ SocketIO threading mode)
# รัน: bash start_prod.sh

set -e
cd "$(dirname "$0")"

# Load environment
if [ -f .env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
            export "$line"
        fi
    done < .env
fi

PORT=${PORT:-5000}
WORKERS=${WORKERS:-2}
THREADS=${THREADS:-8}

if [ -n "$REDIS_URL" ]; then
    echo ">>> Redis detected (REDIS_URL is set). Starting Celery worker in background..."
    # Run celery worker with 2 concurrent processes to handle background tasks
    celery -A celery_app.celery_app worker --loglevel=info --concurrency=2 &
fi

exec gunicorn \
    --worker-class=gthread \
    --workers=$WORKERS \
    --threads=$THREADS \
    --timeout=120 \
    --keepalive=5 \
    --max-requests=1000 \
    --max-requests-jitter=100 \
    --bind=0.0.0.0:$PORT \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    "app_server:app"
