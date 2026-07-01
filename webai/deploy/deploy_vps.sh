#!/bin/bash

# ==========================================
# OrgChat - VPS Deployment Script
# Ubuntu 22.04 LTS
# ==========================================

set -e

echo "=== OrgChat VPS Deployment ==="

# 1. System packages
echo "[1/7] Installing system packages..."
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip \
    tesseract-ocr nginx ufw git
echo "Done."

# 2. Virtual environment
echo "[2/7] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# 3. Install Python packages
echo "[3/7] Installing requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Done."

# 4. Prepare directories
echo "[4/7] Preparing directories..."
mkdir -p uploads chroma_db exports logs
chmod -R 775 uploads chroma_db exports logs
echo "Done."

# 5. Systemd service
APP_NAME="orgchat"
WORKING_DIR=$(pwd)
CURRENT_USER=$(whoami)
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

echo "[5/7] Creating systemd service..."
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=OrgChat AI Server
After=network.target

[Service]
User=$CURRENT_USER
Group=www-data
WorkingDirectory=$WORKING_DIR
EnvironmentFile=$WORKING_DIR/.env
Environment="PATH=$WORKING_DIR/venv/bin"
ExecStart=$WORKING_DIR/venv/bin/gunicorn app_server:app --worker-class gthread --workers 1 --threads 4 --bind 127.0.0.1:8080 --timeout 300
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl start $APP_NAME
echo "Service started."

# 6. Nginx
echo "[6/7] Configuring Nginx..."
read -p "Enter your domain name (e.g. example.com): " SERVER_DOMAIN
if [ -z "$SERVER_DOMAIN" ]; then SERVER_DOMAIN="_"; fi

NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $SERVER_DOMAIN;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:8080/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
echo "Nginx configured."

# 7. Firewall + SSL
echo "[7/7] Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

if [ "$SERVER_DOMAIN" != "_" ]; then
    read -p "Setup HTTPS with Let's Encrypt? (y/n): " SETUP_SSL
    if [[ "$SETUP_SSL" == "y" ]]; then
        sudo apt install -y certbot python3-certbot-nginx
        sudo certbot --nginx -d $SERVER_DOMAIN
    fi
fi

echo ""
echo "=== Deployment complete ==="
echo "App running at: http://$SERVER_DOMAIN"
