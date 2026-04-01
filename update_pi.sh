#!/bin/bash
# ============================================================
#  OrgChat — Raspberry Pi Update Script
#  รัน script นี้บน Pi หลังจาก scp ไฟล์ทั้งหมดมาแล้ว
#  ใช้งาน: ./update_pi.sh
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  🚀  OrgChat Pi Update Script  v2.0      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

PI_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PI_DIR"
echo "📁 Working directory: $PI_DIR"

# ─── 1. สร้าง directory ที่จำเป็น ───────────────────────────
echo ""
echo "📂 [1/6] กำลังสร้าง directories และตั้ง permissions..."
mkdir -p uploads/profiles \
         uploads/social_feed \
         uploads/group_chat \
         uploads/dm_chat \
         uploads/group_profiles \
         uploads/kb \
         chroma_db \
         exports

chmod -R 775 uploads chroma_db exports 2>/dev/null || true
echo "✅ Directories พร้อมแล้ว"

# ─── 2. สำรอง database ──────────────────────────────────────
echo ""
echo "💾 [2/6] สำรอง database..."
if [ -f "chat_history.db" ]; then
    BACKUP_NAME="chat_history_$(date +%Y%m%d_%H%M%S).db.bak"
    cp chat_history.db "$BACKUP_NAME"
    echo "✅ Backed up to: $BACKUP_NAME"
    # เก็บ backup ไว้แค่ 5 อัน ล่าสุด
    ls -t chat_history_*.db.bak 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
else
    echo "⚠️  ไม่พบ chat_history.db (อาจเป็น fresh install)"
fi

# ─── 3. Activate venv ───────────────────────────────────────
echo ""
echo "🐍 [3/6] กำลัง activate Python virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ venv activated: $(python --version)"
else
    echo "⚠️  ไม่พบ venv — กำลังสร้างใหม่..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ venv ใหม่ถูกสร้างแล้ว"
fi

# ─── 4. ติดตั้ง/อัพเดต dependencies (ข้ามถ้าไม่มีการเปลี่ยนแปลง) ────────
echo ""
echo "📦 [4/6] กำลังตรวจสอบ Python dependencies..."

# สร้าง checksum ของ requirements.txt เพื่อเช็คการเปลี่ยนแปลง
REQ_HASH=$(md5sum requirements.txt | awk '{print $1}')
OLD_HASH=""
[ -f ".req_hash" ] && OLD_HASH=$(cat .req_hash)

if [ "$REQ_HASH" != "$OLD_HASH" ]; then
    echo "  → พบการเปลี่ยนแปลงใน requirements.txt — กำลังติดตั้ง..."
    pip install --upgrade pip --quiet
    echo "  → Installing pywebpush..."
    pip install "pywebpush>=1.14.0" --quiet
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt --quiet
        echo "$REQ_HASH" > .req_hash
        echo "✅ Dependencies ทั้งหมดติดตั้ง/อัพเดตแล้ว"
    fi
else
    echo "✅ Dependencies ไม่มีการเปลี่ยนแปลง — ข้ามการติดตั้งเพื่อให้เร็วขึ้น"
fi

# ─── 5. ตั้ง permissions ให้ไฟล์ script ────────────────────
echo ""
echo "🔐 [5/6] ตั้ง file permissions..."
chmod +x update_pi.sh 2>/dev/null || true
chmod 664 *.py 2>/dev/null || true
chmod 664 requirements.txt 2>/dev/null || true
echo "✅ Permissions เรียบร้อย"

# ─── 6. อัพเดต systemd service และ restart ─────────────────
echo ""
echo "⚙️  [6/6] Restart OrgChat service..."

if [ -f "orgchat-pi.service" ]; then
    sudo cp orgchat-pi.service /etc/systemd/system/orgchat.service
    sudo systemctl daemon-reload
    echo "  → Service file updated"
fi

echo "  → Clearing port 5000..."
sudo fuser -k 5000/tcp 2>/dev/null || true

sudo systemctl restart orgchat
sleep 2

echo ""
echo "═══════════════════════════════════════════"
echo "📊 Service Status:"
sudo systemctl status orgchat --no-pager -l
echo "═══════════════════════════════════════════"
echo ""
echo "🎉 Update สำเร็จ!"
echo "🌐 เข้าใช้งานได้ที่: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
