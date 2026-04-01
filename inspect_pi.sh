#!/bin/bash
# ============================================================
#  OrgChat — Raspberry Pi Health Inspector
# ============================================================

echo "╔══════════════════════════════════════════════╗"
echo "║  🔍  OrgChat Pi Health Dashboard             ║"
echo "╚══════════════════════════════════════════════╝"

# 1. System Info
echo "📅 Date: $(date)"
echo "🌡️  CPU Temp: $(vcgencmd measure_temp | cut -d'=' -f2)"
echo ""

# 2. CPU Usage (Last 1 min load)
LOAD=$(cat /proc/loadavg | awk '{print $1}')
echo "💻 CPU Load (1m): $LOAD"

# 3. RAM Usage
echo "🧠 RAM Usage:"
free -h | grep -v + | sed 's/Mem://g' | awk '{print "   Total: "$1" | Used: "$2" | Free: "$3}'

# 4. Disk Usage
echo ""
echo "💾 Disk Usage (/):"
df -h / | tail -1 | awk '{print "   Total: "$2" | Used: "$3" | Free: "$4" [Usage: "$5"]"}'

# 5. OrgChat Service Status
echo ""
echo "⚙️  Service Status (Gunicorn):"
if systemctl is-active --quiet orgchat; then
    echo "   ✅ OrgChat is RUNNING"
    # Find how many workers are active
    WORKERS=$(ps aux | grep gunicorn | grep app:app | wc -l)
    echo "   👷 Active Workers: $WORKERS"
else
    echo "   ❌ OrgChat is STOPPED"
fi

# 6. Port Check
echo ""
echo "🌐 Port 5000 Status:"
if sudo lsof -i :5000 > /dev/null; then
    echo "   ✅ Port 5000 is LISTENING"
else
    echo "   ❌ Port 5000 index is CLOSED"
fi

echo "══════════════════════════════════════════════"
