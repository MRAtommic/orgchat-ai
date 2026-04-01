#!/bin/bash

# ==========================================
# WebAI - VPS Deployment Script (Complete)
# ==========================================

echo "🚀 Starting Full Deployment on Linux VPS..."

# 1. System Update & Install Prerequisites
echo "📦 Updating system packages and installing prerequisites..."
sudo apt update && sudo apt install -y python3-pip python3-venv tesseract-ocr nginx ufw
echo "✅ System packages installed."

# 2. Setup Virtual Environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists."
fi

# 3. Install Python Dependencies
echo "📥 Installing requirements in venv..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn eventlet  # Ensure WSGI server is available
echo "✅ Dependencies installed."

# 4. Prepare Directories and Data
echo "📁 Configuring directories..."
mkdir -p uploads chroma_db exports logs
chmod -R 775 uploads chroma_db exports logs
# Make sure database is present or will be initialized
touch chat_history.db
chmod 664 chat_history.db
echo "✅ Directories prepared."

# 5. Define App Settings
APP_NAME="webai"
WORKING_DIR=$(pwd)
CURRENT_USER=$(whoami)
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"

# 6. Service Configuration (Systemd)
echo "⚙️ Creating Systemd service for Gunicorn..."
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Gunicorn instance to serve $APP_NAME
After=network.target

[Service]
User=$CURRENT_USER
Group=www-data
WorkingDirectory=$WORKING_DIR
Environment="PATH=$WORKING_DIR/venv/bin"
# Using eventlet worker for WebSockets (SocketIO) support
ExecStart=$WORKING_DIR/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Reloading and starting service..."
sudo systemctl daemon-reload
sudo systemctl start $APP_NAME
sudo systemctl enable $APP_NAME
echo "✅ Systemd service created and started."

# 7. Nginx Configuration
echo "🌐 Configuring Nginx reverse proxy..."

read -p "Enter your Domain Name or Public IP (e.g. example.com or 192.168.1.100): " SERVER_DOMAIN
if [ -z "$SERVER_DOMAIN" ]; then
    SERVER_DOMAIN="_"
fi

sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $SERVER_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias $WORKING_DIR/static/;
        expires 30d;
    }

    location /uploads/ {
        alias $WORKING_DIR/uploads/;
    }

    # Restrict hidden files
    location ~ /\. {
        deny all;
    }
}
EOF

# Enable Nginx Site
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Restart Nginx
sudo nginx -t && sudo systemctl restart nginx
echo "✅ Nginx configured and restarted."

# 8. Setup Firewall (UFW)
echo "🔒 Configuring UFW firewall for Nginx and SSH..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable
echo "✅ Firewall enabled."

# 9. SSL Configuration (Certbot)
echo "🔒 Setting up HTTPS with Let's Encrypt..."
read -p "Do you want to secure your site with HTTPS using Certbot? (y/n): " SETUP_SSL
if [[ "$SETUP_SSL" == "y" || "$SETUP_SSL" == "Y" ]]; then
    if [ "$SERVER_DOMAIN" != "_" ]; then
        echo "📦 Installing certbot..."
        sudo apt install -y certbot python3-certbot-nginx
        echo "🔐 Obtaining and configuring SSL certificate..."
        sudo certbot --nginx -d $SERVER_DOMAIN
        echo "✅ HTTPS configured successfully."
    else
        echo "⚠️ Cannot set up HTTPS without a valid domain name."
    fi
else
    echo "⏭️ Skipping HTTPS setup."
fi

echo "🎉 Deployment Complete! Your app is now running on http://$SERVER_DOMAIN (or https if configured)."
