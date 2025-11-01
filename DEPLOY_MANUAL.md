# Manual Deployment Guide

## Quick Deploy to 62.113.106.10

### Prerequisites
- SSH access to server (password or key)
- Server: Ubuntu 20.04+
- Root access

---

## Method 1: Direct SSH Deployment (Recommended)

### Step 1: Connect to Server

```bash
ssh root@62.113.106.10
```

Enter password when prompted.

### Step 2: Download and Run Deployment Script

```bash
# Download script from GitHub
wget https://raw.githubusercontent.com/chechulinalexander-wq/PARFUME-VISUAL/master/deploy_to_server.sh

# Make executable
chmod +x deploy_to_server.sh

# Run deployment
bash deploy_to_server.sh
```

### Step 3: Provide API Keys

During deployment, you'll be prompted to enter:

1. **OpenAI API Key** (from your .env)
2. **Replicate API Token** (from your .env)
3. **Telegram Bot Token** (from your .env)
4. **Telegram Channel ID** (from your .env)

> 💡 **Tip:** Copy these from your local `.env` file before starting!

### Step 4: Verify Deployment

After deployment completes, check:

```bash
# Check application status
supervisorctl status perfume-visual

# Check nginx
systemctl status nginx

# View logs
tail -f /var/log/perfume-visual/error.log
```

### Step 5: Access Application

Open in browser: **http://62.113.106.10**

---

## Method 2: Using PuTTY (Windows)

### Step 1: Download Files

1. Open PuTTY
2. Connect to: `root@62.113.106.10`
3. Enter password

### Step 2: Upload Deployment Script

Using WinSCP or PSCP:

```cmd
pscp deploy_to_server.sh root@62.113.106.10:/tmp/
```

Or manually:
1. Open `/tmp/deploy_to_server.sh` in nano
2. Copy-paste content from local file
3. Save (Ctrl+X, Y, Enter)

### Step 3: Run Deployment

```bash
cd /tmp
chmod +x deploy_to_server.sh
bash deploy_to_server.sh
```

---

## Method 3: Copy-Paste Deployment Commands

If you can't download the script, run these commands directly:

### 1. System Update
```bash
apt-get update -y && apt-get upgrade -y
```

### 2. Install Dependencies
```bash
apt-get install -y python3 python3-pip python3-venv git nginx supervisor ufw
```

### 3. Clone Repository
```bash
mkdir -p /opt/perfume-visual
cd /opt/perfume-visual
git clone https://github.com/chechulinalexander-wq/PARFUME-VISUAL.git .
```

### 4. Setup Python Environment
```bash
python3 -m venv /opt/perfume-visual/venv
source /opt/perfume-visual/venv/bin/activate
pip install --upgrade pip
pip install -r /opt/perfume-visual/requirements.txt
```

### 5. Create .env File
```bash
cat > /opt/perfume-visual/.env <<EOF
OPENAI_API_KEY=your_openai_key_here
REPLICATE_API_TOKEN=your_replicate_token_here
TELEGRAM_BOT_TOKEN=your_telegram_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
DEBUG=False
PORT=8080
DB_PATH=/opt/perfume-visual/fragrantica_news.db
EOF
```

**⚠️ Replace the API keys with your actual keys!**

### 6. Create Directories
```bash
mkdir -p /opt/perfume-visual/main_images
mkdir -p /opt/perfume-visual/generated_videos
mkdir -p /var/log/perfume-visual
```

### 7. Initialize Database
```bash
cd /opt/perfume-visual
source venv/bin/activate
python3 <<EOF
import sqlite3
conn = sqlite3.connect('fragrantica_news.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS global_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
cursor.execute('CREATE TABLE IF NOT EXISTS randewoo_products (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, name TEXT, product_url TEXT UNIQUE, fragrantica_url TEXT, parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, description TEXT, image_path TEXT, styled_image_path TEXT, video_path TEXT)')
conn.commit()
conn.close()
print('Database initialized!')
EOF
```

### 8. Configure Supervisor
```bash
cat > /etc/supervisor/conf.d/perfume-visual.conf <<EOF
[program:perfume-visual]
directory=/opt/perfume-visual
command=/opt/perfume-visual/venv/bin/gunicorn app:app -c gunicorn_config.py
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/perfume-visual/error.log
stdout_logfile=/var/log/perfume-visual/access.log
environment=PATH="/opt/perfume-visual/venv/bin"
stopasgroup=true
killasgroup=true
EOF
```

### 9. Configure Nginx
```bash
cat > /etc/nginx/sites-available/perfume-visual <<EOF
server {
    listen 80;
    server_name 62.113.106.10;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
    }

    location /static {
        alias /opt/perfume-visual/static;
    }

    location /images {
        alias /opt/perfume-visual/main_images;
    }

    location /videos {
        alias /opt/perfume-visual/generated_videos;
    }
}
EOF

ln -sf /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
```

### 10. Configure Firewall
```bash
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
```

### 11. Start Services
```bash
supervisorctl reread
supervisorctl update
supervisorctl start perfume-visual
nginx -t
systemctl restart nginx
```

### 12. Check Status
```bash
supervisorctl status perfume-visual
curl -I http://localhost:8080
```

---

## Post-Deployment

### Access Application
Open browser: **http://62.113.106.10**

### View Logs
```bash
tail -f /var/log/perfume-visual/error.log
```

### Restart Application
```bash
supervisorctl restart perfume-visual
```

### Update Application
```bash
cd /opt/perfume-visual
git pull origin master
supervisorctl restart perfume-visual
```

---

## Troubleshooting

### Application Won't Start

1. Check logs:
```bash
tail -100 /var/log/perfume-visual/error.log
```

2. Check supervisor status:
```bash
supervisorctl status
```

3. Test manual start:
```bash
cd /opt/perfume-visual
source venv/bin/activate
python app.py
```

### Port 8080 in Use

```bash
# Find process
lsof -i :8080

# Kill it
kill -9 <PID>

# Restart
supervisorctl restart perfume-visual
```

### Nginx Errors

```bash
# Test config
nginx -t

# Check logs
tail -50 /var/log/nginx/error.log

# Restart
systemctl restart nginx
```

---

## Quick API Keys Reference

Copy these from your local `.env` file:

```
OPENAI_API_KEY=sk-proj-...
REPLICATE_API_TOKEN=r8_...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=-1003207484793
```

---

## Success Indicators

✅ Application accessible at http://62.113.106.10  
✅ `supervisorctl status perfume-visual` shows RUNNING  
✅ `systemctl status nginx` shows active (running)  
✅ No errors in `/var/log/perfume-visual/error.log`  

---

## Support

**Repository:** https://github.com/chechulinalexander-wq/PARFUME-VISUAL  
**Deployment Guide:** DEPLOYMENT_GUIDE.md

For detailed management commands, see DEPLOYMENT_GUIDE.md

