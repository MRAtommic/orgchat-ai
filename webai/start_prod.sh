#!/bin/bash
# OrgChat AI — Production Startup Script (Linux)
# ใช้ Gunicorn + gthread worker (รองรับ SocketIO threading mode)
# รัน: bash start_prod.sh

set -e
cd "$(dirname "$0")"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

PORT=${PORT:-5000}
WORKERS=${WORKERS:-2}
THREADS=${THREADS:-8}

echo ">>> Starting OrgChat AI (production) on port $PORT"
echo ">>> Workers: $WORKERS | Threads: $THREADS"

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
