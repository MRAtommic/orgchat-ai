# คู่มือ Deploy OrgChat บน Oracle Cloud (ฟรีตลอดกาล)
### Always Free Tier — ARM 4 CPU / 24GB RAM

---

## ทำไมถึงเลือก Oracle Cloud

- **ฟรี 100% ไม่มีวันหมด** ไม่ตัดเงิน (ถ้าใช้แค่ Always Free resources)
- VM ARM Ampere A1: **4 OCPU + 24GB RAM** — แรงกว่า VPS เสียเงินหลายเจ้า
- Disk 200GB ฟรี
- SQLite เก็บในดิสก์ถาวร ไม่หายเมื่อ restart

---

## ขั้นตอนที่ 1 — สมัคร Oracle Cloud

1. ไปที่ **https://cloud.oracle.com** → คลิก **Start for free**
2. กรอกข้อมูล:
   - Email, ชื่อ-นามสกุล
   - **Home Region** → เลือก **Singapore** (ap-singapore-1) หรือ **Japan Tokyo** — ใกล้ไทยที่สุด
   - ใส่บัตรเครดิต/เดบิต (ยืนยันตัวตนเท่านั้น **ไม่ตัดเงิน**)
3. รอ verify ประมาณ 5–15 นาที
4. Login เข้า Oracle Cloud Console

> **สำคัญ**: เลือก Home Region แล้ว **เปลี่ยนไม่ได้** เลือกให้ดีก่อน

---

## ขั้นตอนที่ 2 — สร้าง VM Instance

### 2.1 ไปที่ Compute

Console → เมนูซ้าย (hamburger ☰) → **Compute** → **Instances** → **Create Instance**

---

### 2.2 ตั้งชื่อ Instance

- Name: `orgchat-server` (ตั้งชื่ออะไรก็ได้)

---

### 2.3 เลือก Image และ Shape (สำคัญมาก)

คลิก **Edit** ที่ส่วน **Image and shape**

**Image:**
- คลิก **Change image**
- เลือก **Canonical Ubuntu**
- Version: **22.04**
- คลิก **Select image**

**Shape:**
- คลิก **Change shape**
- Instance type: เลือก **Ampere** (ARM — ฟรีและแรงที่สุด)
- Shape: **VM.Standard.A1.Flex**
- OCPUs: **4**
- Memory: **24 GB**
- คลิก **Select shape**

> ถ้าขึ้น "Out of capacity" ให้ลองเปลี่ยน Availability Domain (AD-1, AD-2, AD-3) หรือลอง Region อื่น

---

### 2.4 ตั้งค่า Networking

ปล่อยค่า default ไว้ (Oracle จะสร้าง VCN ให้อัตโนมัติ)

ตรวจสอบว่า **Assign a public IPv4 address** เปิดอยู่

---

### 2.5 สร้าง SSH Key

คลิก **Save private key** → ไฟล์ `.key` จะ download ลงเครื่อง

> เก็บไฟล์นี้ไว้ **อย่าลบ** — ใช้สำหรับ SSH เข้า server

---

### 2.6 สร้าง Instance

เลื่อนลงล่างสุด → คลิก **Create**

รอประมาณ **2–5 นาที** จน Status เปลี่ยนเป็น 🟢 **Running**

---

### 2.7 จด Public IP

Instances → คลิกชื่อ instance → จด **Public IP address**  
เช่น `140.238.xxx.xxx`

---

## ขั้นตอนที่ 3 — เปิด Port บน Oracle Firewall

Oracle Cloud มี Firewall 2 ชั้น ต้องเปิดทั้งคู่

### 3.1 เปิด Port บน Security List (Cloud Firewall)

1. Console → **Networking** → **Virtual Cloud Networks**
2. คลิก VCN ที่สร้างมา (ชื่อจะขึ้นต้นด้วย `vcn-...`)
3. คลิก **Security Lists** → คลิก **Default Security List**
4. คลิก **Add Ingress Rules** → เพิ่ม 2 rule:

**Rule 1 — HTTP:**
```
Source CIDR:  0.0.0.0/0
Protocol:     TCP
Destination Port Range: 80
```

**Rule 2 — HTTPS:**
```
Source CIDR:  0.0.0.0/0
Protocol:     TCP
Destination Port Range: 443
```

คลิก **Add Ingress Rules**

---

### 3.2 เปิด Port บน OS Firewall (iptables)

ทำหลังจาก SSH เข้าไปในข้อถัดไป — Oracle Ubuntu ปิด port ไว้ด้วย iptables ด้วย

---

## ขั้นตอนที่ 4 — SSH เข้า Server

### บน Mac

เปิด Terminal แล้วรัน:

```bash
# แก้ไข permission ไฟล์ key ก่อน (ทำครั้งเดียว)
chmod 400 /path/to/your-key.key

# SSH เข้า server
ssh -i /path/to/your-key.key ubuntu@PUBLIC_IP_ของคุณ
```

ตัวอย่าง:
```bash
chmod 400 ~/Downloads/ssh-key-2024-01-01.key
ssh -i ~/Downloads/ssh-key-2024-01-01.key ubuntu@140.238.xxx.xxx
```

ถ้าขึ้น "Are you sure you want to continue connecting?" → พิมพ์ `yes` → Enter

เมื่อเข้าได้จะเห็น prompt เปลี่ยนเป็น:
```
ubuntu@orgchat-server:~$
```

---

## ขั้นตอนที่ 5 — ตั้งค่า Server

### 5.1 เปิด Port บน OS Firewall

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save
```

ถ้าไม่มี netfilter-persistent:
```bash
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

---

### 5.2 อัปเดต System และติดตั้ง Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip \
    tesseract-ocr nginx ufw git unzip
```

---

### 5.3 ตั้งค่า UFW (OS Firewall)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
sudo ufw status
```

---

## ขั้นตอนที่ 6 — อัปโหลดโค้ดขึ้น Server

**วิธีที่ 1: จาก GitHub (แนะนำ)**

```bash
# บน server
git clone https://github.com/YOUR_USERNAME/orgchat.git
cd orgchat/webai
```

**วิธีที่ 2: SCP จาก Mac**

เปิด Terminal ใหม่บน Mac (อย่าปิดอันเก่า):

```bash
# zip โฟลเดอร์ webai ก่อน
cd /path/to/orgchat-ai-main
zip -r webai.zip webai/ -x "webai/venv/*" -x "webai/chroma_db/*" -x "webai/__pycache__/*"

# อัปโหลดขึ้น server
scp -i ~/Downloads/your-key.key webai.zip ubuntu@PUBLIC_IP:~/

# กลับไปที่ terminal ที่ SSH อยู่ แล้วรัน
cd ~
unzip webai.zip
cd webai
```

---

## ขั้นตอนที่ 7 — ติดตั้ง Python Packages

```bash
# ต้องอยู่ในโฟลเดอร์ webai
cd ~/webai   # หรือ ~/orgchat/webai ถ้า clone จาก GitHub

python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> ใช้เวลา 5–15 นาที ครั้งแรก

---

## ขั้นตอนที่ 8 — ตั้งค่า .env

```bash
# ไฟล์ .env มีอยู่แล้วถ้า zip มาจากเครื่อง
# ถ้าไม่มีให้สร้าง:
nano .env
```

แก้ค่า `BASE_URL` ให้ตรงกับ IP หรือ domain:

```bash
nano .env
```

เปลี่ยนบรรทัด:
```
BASE_URL=https://yourdomain.com
```

บันทึก: `Ctrl+O` → Enter → `Ctrl+X`

---

## ขั้นตอนที่ 9 — ทดสอบรัน

```bash
source venv/bin/activate
python app_server.py
```

ถ้าไม่มี error → `Ctrl+C` เพื่อหยุด แล้วทำขั้นต่อไป

---

## ขั้นตอนที่ 10 — ตั้งค่า Systemd Service

```bash
sudo nano /etc/systemd/system/orgchat.service
```

วางเนื้อหา **(แก้ PATH ให้ตรง)**:

```ini
[Unit]
Description=OrgChat AI Server
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/webai
EnvironmentFile=/home/ubuntu/webai/.env
Environment="PATH=/home/ubuntu/webai/venv/bin"
ExecStart=/home/ubuntu/webai/venv/bin/gunicorn app_server:app --worker-class gthread --workers 1 --threads 4 --bind 127.0.0.1:8080 --timeout 300
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

บันทึก: `Ctrl+O` → Enter → `Ctrl+X`

```bash
sudo systemctl daemon-reload
sudo systemctl enable orgchat
sudo systemctl start orgchat

# ตรวจสอบ
sudo systemctl status orgchat
```

ต้องเห็น `Active: active (running)`

---

## ขั้นตอนที่ 11 — ตั้งค่า Nginx

```bash
sudo nano /etc/nginx/sites-available/orgchat
```

วางเนื้อหา **(แก้ domain หรือ IP)**:

```nginx
server {
    listen 80;
    server_name yourdomain.com;   # หรือใส่ IP ถ้ายังไม่มี domain

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:8080/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/orgchat /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

ทดสอบเปิด browser → `http://PUBLIC_IP`  
ต้องเห็นหน้า OrgChat

---

## ขั้นตอนที่ 12 — ตั้ง HTTPS (ถ้ามี Domain)

ถ้ายังไม่มี domain ข้ามขั้นตอนนี้ไปก่อนได้

### 12.1 ชี้ DNS ของ Domain มาที่ IP

ไปที่ผู้ให้บริการ domain → DNS Management → เพิ่ม A Record:
```
Type: A
Name: @  (หรือ subdomain เช่น chat)
Value: PUBLIC_IP_ของ_Oracle
TTL: 3600
```

รอ DNS propagate ประมาณ 5–30 นาที

### 12.2 ติดตั้ง SSL ด้วย Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

ทำตาม wizard:
- ใส่ email
- Agree to terms: `Y`
- Share email: `N`
- Certbot จะตั้งค่า HTTPS ให้อัตโนมัติ

อัปเดต `.env`:
```bash
nano .env
# เปลี่ยน BASE_URL=https://yourdomain.com
```

```bash
sudo systemctl restart orgchat
```

---

## คำสั่งที่ใช้บ่อยบน Server

```bash
# ดู log แบบ real-time
sudo journalctl -u orgchat -f

# restart app
sudo systemctl restart orgchat

# หยุด app
sudo systemctl stop orgchat

# ดูสถานะ
sudo systemctl status orgchat

# อัปเดตโค้ด (ถ้า clone จาก GitHub)
cd ~/orgchat
git pull
sudo systemctl restart orgchat
```

---

## Checklist หลัง Deploy

```
[ ] Instance สร้างแล้ว Status = Running
[ ] SSH เข้าได้
[ ] Port 80, 443 เปิดทั้ง Security List และ iptables
[ ] pip install -r requirements.txt ผ่าน
[ ] systemctl status orgchat → active (running)
[ ] เปิด http://PUBLIC_IP ได้เห็นหน้า OrgChat
[ ] สมัคร account Admin และเข้า /admin/super ได้
[ ] (ถ้ามี domain) HTTPS ใช้งานได้
[ ] (ถ้าใช้ LINE) อัปเดต Webhook URL ใน LINE Developers Console
```

---

## แก้ปัญหาที่พบบ่อย

| ปัญหา | วิธีแก้ |
|-------|---------|
| เปิด IP แล้วหน้าเว็บไม่ขึ้น | ตรวจ Security List และ `sudo iptables -L` ว่าเปิด port 80 หรือยัง |
| `systemctl status orgchat` error | `sudo journalctl -u orgchat -n 50` ดู error ล่าสุด |
| `Out of capacity` ตอนสร้าง VM | เปลี่ยน Availability Domain หรือลองใหม่ตอนดึก |
| SSH ต่อไม่ได้ | ตรวจว่า Security List เปิด port 22, และ chmod 400 key file |
| Certbot ล้มเหลว | ตรวจว่า DNS ชี้มาถูก IP และ port 80 เปิดอยู่ |

---

*เอกสารนี้ใช้สำหรับ OrgChat v11.0.4 — Oracle Cloud Always Free (ARM Ampere A1)*
