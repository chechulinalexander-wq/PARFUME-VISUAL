#!/bin/bash
# Deploy Perfume Visual Generator to 84.54.31.86 (Beget VPS)
# Fresh installation on new server

set -e  # Exit on error

echo "=========================================="
echo "Deploying Perfume Visual Generator"
echo "Server: 84.54.31.86 (Beget VPS)"
echo "=========================================="

# Server details
SERVER_IP="84.54.31.86"
APP_DIR="/opt/perfume-visual"
REPO_URL="https://github.com/chechulinalexander-wq/PARFUME-VISUAL.git"
BRANCH="master"

echo ""
echo "Step 1: System information..."
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "User: $(whoami)"
echo ""

echo "Step 2: Updating system packages..."
apt-get update -y
apt-get upgrade -y
echo "✓ System updated"

echo ""
echo "Step 3: Installing required packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor \
    ufw \
    sqlite3 \
    curl \
    wget \
    htop
echo "✓ Packages installed"

echo ""
echo "Step 4: Creating application directory..."
mkdir -p $APP_DIR
mkdir -p /var/log/perfume-visual
echo "✓ Directories created"

echo ""
echo "Step 5: Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "Repository exists, pulling latest..."
    
    # Fix ownership issues
    chown -R root:root $APP_DIR
    
    # Add to safe directories if needed
    git config --global --add safe.directory $APP_DIR 2>/dev/null || true
    
    cd $APP_DIR
    git fetch --all
    git checkout $BRANCH
    git reset --hard origin/$BRANCH
    git pull origin $BRANCH
else
    echo "Cloning repository..."
    git clone -b $BRANCH $REPO_URL $APP_DIR
    cd $APP_DIR
    
    # Fix ownership
    chown -R root:root $APP_DIR
    git config --global --add safe.directory $APP_DIR 2>/dev/null || true
fi
echo "✓ Repository ready: $APP_DIR"

echo ""
echo "Step 6: Setting up Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python environment configured"

echo ""
echo "Step 7: Creating .env file..."
echo ""
echo "⚠️  Please provide your API keys:"
echo ""

read -p "OpenAI API Key: " OPENAI_KEY
read -p "Replicate API Token: " REPLICATE_TOKEN
read -p "Telegram Bot Token: " TELEGRAM_TOKEN
read -p "Telegram Channel ID: " TELEGRAM_CHANNEL

cat > $APP_DIR/.env <<EOF
# Flask Configuration
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
DEBUG=False
PORT=8080

# API Keys
OPENAI_API_KEY=$OPENAI_KEY
REPLICATE_API_TOKEN=$REPLICATE_TOKEN
TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHANNEL_ID=$TELEGRAM_CHANNEL

# Database
DB_PATH=$APP_DIR/fragrantica_news.db

# Folders
UPLOAD_FOLDER=$APP_DIR/main_images
VIDEO_FOLDER=$APP_DIR/generated_videos
EOF

chmod 600 $APP_DIR/.env
echo "✓ .env file created"

echo ""
echo "Step 8: Creating application directories..."
mkdir -p $APP_DIR/main_images
mkdir -p $APP_DIR/generated_images
mkdir -p $APP_DIR/generated_videos
mkdir -p $APP_DIR/templates
mkdir -p $APP_DIR/static

chmod 755 $APP_DIR/main_images
chmod 755 $APP_DIR/generated_images
chmod 755 $APP_DIR/generated_videos
echo "✓ Application directories ready"

echo ""
echo "Step 9: Initializing database..."
cd $APP_DIR
source venv/bin/activate

python3 <<PYTHON_SCRIPT
import sqlite3
from datetime import datetime

db_path = '$APP_DIR/fragrantica_news.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create global_settings table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS global_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Create randewoo_products table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS randewoo_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        name TEXT,
        product_url TEXT UNIQUE,
        fragrantica_url TEXT,
        parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        image_path TEXT,
        styled_image_path TEXT,
        video_path TEXT
    )
''')

# Insert default stylize prompt
stylize_prompt = """Transform this perfume bottle image by adding a stunning, vibrant, artistic background while keeping the bottle EXACTLY as it is - same shape, same color, same text, same position.

Create a beautiful atmospheric background that captures the mood and essence of this fragrance: {DESCRIPTION}

The background should feature: vivid elegant colors with glowing bokeh lights in pink, purple, gold, and blue tones, soft dreamy blur, sophisticated luxury ambiance, professional studio lighting with colored gels, cinematic composition. Make it look like high-end commercial perfume advertising photography with magazine quality.

IMPORTANT: Do NOT change the perfume bottle itself - keep it identical to the input. Only transform the background behind it!"""

cursor.execute('''
    INSERT OR REPLACE INTO global_settings (key, value, updated_at)
    VALUES (?, ?, ?)
''', ('prompt_stylize', stylize_prompt, datetime.now()))

# Insert default caption prompt
caption_prompt = """Создай продающий пост для Telegram канала о парфюме {BRAND} {PERFUME_NAME}.

Описание аромата: {DESCRIPTION}

Требования:
- Текст должен быть живым и эмоциональным
- Вызывать желание купить
- Подчеркивать уникальность аромата
- Использовать емодзи (но не переборщить)
- Длина: 3-5 предложений
- Стиль: casual, но профессионально

Формат ответа: только текст поста, без заголовков и пояснений."""

cursor.execute('''
    INSERT OR REPLACE INTO global_settings (key, value, updated_at)
    VALUES (?, ?, ?)
''', ('prompt_caption', caption_prompt, datetime.now()))

conn.commit()
conn.close()
print('✓ Database initialized with default prompts!')
PYTHON_SCRIPT

chmod 644 $APP_DIR/fragrantica_news.db
echo "✓ Database ready"

echo ""
echo "Step 10: Configuring Supervisor..."
cat > /etc/supervisor/conf.d/perfume-visual.conf <<EOF
[program:perfume-visual]
directory=$APP_DIR
command=$APP_DIR/venv/bin/gunicorn app:app -c gunicorn_config.py
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/perfume-visual/error.log
stdout_logfile=/var/log/perfume-visual/access.log
environment=PATH="$APP_DIR/venv/bin"
stopasgroup=true
killasgroup=true
stopsignal=QUIT
EOF

supervisorctl reread
supervisorctl update
echo "✓ Supervisor configured"

echo ""
echo "Step 11: Configuring Nginx..."

# Remove all default server configs
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/default.backup
rm -f /etc/nginx/sites-available/default.backup

cat > /etc/nginx/sites-available/perfume-visual <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name $SERVER_IP _;

    client_max_body_size 100M;
    client_body_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Increased timeouts for AI processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    location /static {
        alias $APP_DIR/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /images {
        alias $APP_DIR/main_images;
        expires 7d;
        add_header Cache-Control "public";
    }

    location /videos {
        alias $APP_DIR/generated_videos;
        expires 7d;
        add_header Cache-Control "public";
    }
}
EOF

ln -sf /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-enabled/perfume-visual

# Test nginx config
nginx -t

if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✓ Nginx configured and reloaded"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

echo ""
echo "Step 12: Configuring firewall (UFW)..."
ufw --force enable
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw reload
echo "✓ Firewall configured"

echo ""
echo "Step 13: Starting application..."
supervisorctl start perfume-visual
sleep 5
echo "✓ Application started"

echo ""
echo "Step 14: Running health checks..."

# Check supervisor status
SUPERVISOR_STATUS=$(supervisorctl status perfume-visual | awk '{print $2}')
echo "Supervisor status: $SUPERVISOR_STATUS"

# Check if app responds
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 || echo "000")
echo "HTTP response: $HTTP_CODE"

# Check nginx
NGINX_STATUS=$(systemctl is-active nginx)
echo "Nginx status: $NGINX_STATUS"

echo ""
echo "=========================================="
if [ "$SUPERVISOR_STATUS" = "RUNNING" ] && [ "$HTTP_CODE" = "200" ]; then
    echo "✅ DEPLOYMENT SUCCESSFUL!"
else
    echo "⚠️  DEPLOYMENT COMPLETED WITH WARNINGS"
fi
echo "=========================================="
echo ""
echo "🌐 Application URL:"
echo "   http://$SERVER_IP"
echo ""
echo "📊 Service Status:"
supervisorctl status perfume-visual
echo ""
echo "📝 Log Files:"
echo "   Access: /var/log/perfume-visual/access.log"
echo "   Errors: /var/log/perfume-visual/error.log"
echo ""
echo "🔧 Management Commands:"
echo ""
echo "  Check status:"
echo "    supervisorctl status perfume-visual"
echo ""
echo "  View logs:"
echo "    tail -f /var/log/perfume-visual/error.log"
echo ""
echo "  Restart application:"
echo "    supervisorctl restart perfume-visual"
echo ""
echo "  Update from GitHub:"
echo "    cd /opt/perfume-visual"
echo "    git pull origin master"
echo "    supervisorctl restart perfume-visual"
echo ""
echo "🎉 Ready to use!"
echo ""

# Show last few log lines
echo "Recent logs:"
tail -10 /var/log/perfume-visual/error.log 2>/dev/null || echo "No errors yet!"
echo ""

