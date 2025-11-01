#!/bin/bash
# Deployment script for Perfume Visual Generator on Ubuntu VPS
# Server: 62.113.106.10

set -e  # Exit on error

echo "=========================================="
echo "Deploying Perfume Visual Generator"
echo "=========================================="

# Server details
SERVER_IP="62.113.106.10"
SERVER_USER="root"
APP_DIR="/opt/perfume-visual"
REPO_URL="https://github.com/chechulinalexander-wq/PARFUME-VISUAL.git"
BRANCH="master"

echo ""
echo "Step 1: Updating system..."
apt-get update -y
apt-get upgrade -y

echo ""
echo "Step 2: Installing required packages..."
apt-get install -y python3 python3-pip python3-venv git nginx supervisor ufw

echo ""
echo "Step 3: Creating application user..."
if ! id -u perfume-visual &>/dev/null; then
    useradd -m -s /bin/bash perfume-visual
    echo "User perfume-visual created"
else
    echo "User perfume-visual already exists"
fi

echo ""
echo "Step 4: Stopping old services (if exists)..."
# Stop old perfume-publisher app if running
if supervisorctl status perfume-app &>/dev/null; then
    supervisorctl stop perfume-app
    rm -f /etc/supervisor/conf.d/perfume-app.conf
    echo "Old perfume-app stopped and removed"
fi

# Remove old nginx config
rm -f /etc/nginx/sites-enabled/perfume-app
rm -f /etc/nginx/sites-available/perfume-app

echo ""
echo "Step 5: Creating application directory..."
mkdir -p $APP_DIR
mkdir -p /var/log/perfume-visual
chown perfume-visual:perfume-visual /var/log/perfume-visual

echo ""
echo "Step 6: Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "Repository exists, pulling latest..."
    cd $APP_DIR
    git fetch --all
    git checkout $BRANCH
    git pull origin $BRANCH
else
    echo "Cloning repository..."
    git clone -b $BRANCH $REPO_URL $APP_DIR
    cd $APP_DIR
fi

echo ""
echo "Step 7: Setting up Python virtual environment..."
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt

echo ""
echo "Step 8: Creating .env file..."
echo "IMPORTANT: Please provide your API keys!"
echo ""

# Read API keys
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

echo ""
echo "Step 9: Creating directories..."
mkdir -p $APP_DIR/main_images
mkdir -p $APP_DIR/generated_images
mkdir -p $APP_DIR/generated_videos
mkdir -p $APP_DIR/templates
mkdir -p $APP_DIR/static

echo ""
echo "Step 10: Setting permissions..."
chown -R perfume-visual:perfume-visual $APP_DIR
chmod 755 $APP_DIR
chmod 600 $APP_DIR/.env
chmod 755 $APP_DIR/main_images
chmod 755 $APP_DIR/generated_images
chmod 755 $APP_DIR/generated_videos

echo ""
echo "Step 11: Creating/updating database..."
touch $APP_DIR/fragrantica_news.db
chown perfume-visual:perfume-visual $APP_DIR/fragrantica_news.db
chmod 644 $APP_DIR/fragrantica_news.db

# Initialize database tables
source $APP_DIR/venv/bin/activate
python3 <<PYTHON_SCRIPT
import sqlite3
import os

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

# Insert default prompts
cursor.execute('''
    INSERT OR IGNORE INTO global_settings (key, value)
    VALUES (?, ?)
''', ('prompt_stylize', '''Transform this perfume bottle image by adding a stunning, vibrant, artistic background while keeping the bottle EXACTLY as it is - same shape, same color, same text, same position.

Create a beautiful atmospheric background that captures the mood and essence of this fragrance: {DESCRIPTION}

The background should feature: vivid elegant colors with glowing bokeh lights in pink, purple, gold, and blue tones, soft dreamy blur, sophisticated luxury ambiance, professional studio lighting with colored gels, cinematic composition. Make it look like high-end commercial perfume advertising photography with magazine quality.

IMPORTANT: Do NOT change the perfume bottle itself - keep it identical to the input. Only transform the background behind it!'''))

cursor.execute('''
    INSERT OR IGNORE INTO global_settings (key, value)
    VALUES (?, ?)
''', ('prompt_caption', '''Создай продающий пост для Telegram канала о парфюме {BRAND} {PERFUME_NAME}.

Описание аромата: {DESCRIPTION}

Требования:
- Текст должен быть живым и эмоциональным
- Вызывать желание купить
- Подчеркивать уникальность аромата
- Использовать емодзи (но не переборщить)
- Длина: 3-5 предложений
- Стиль: casual, но профессионально

Формат ответа: только текст поста, без заголовков и пояснений.'''))

conn.commit()
conn.close()
print("Database initialized successfully!")
PYTHON_SCRIPT

echo ""
echo "Step 12: Configuring Supervisor..."
cat > /etc/supervisor/conf.d/perfume-visual.conf <<EOF
[program:perfume-visual]
directory=$APP_DIR
command=$APP_DIR/venv/bin/gunicorn app:app -c gunicorn_config.py
user=perfume-visual
autostart=true
autorestart=true
stderr_logfile=/var/log/perfume-visual/error.log
stdout_logfile=/var/log/perfume-visual/access.log
environment=PATH="$APP_DIR/venv/bin"
stopasgroup=true
killasgroup=true
EOF

echo ""
echo "Step 13: Configuring Nginx..."
cat > /etc/nginx/sites-available/perfume-visual <<EOF
server {
    listen 80;
    server_name $SERVER_IP;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
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

# Enable site
ln -sf /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-enabled/perfume-visual
rm -f /etc/nginx/sites-enabled/default

echo ""
echo "Step 14: Configuring firewall (UFW)..."
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload

echo ""
echo "Step 15: Restarting services..."
supervisorctl reread
supervisorctl update
supervisorctl start perfume-visual
nginx -t
systemctl restart nginx

echo ""
echo "Step 16: Checking status..."
sleep 3
supervisorctl status perfume-visual
systemctl status nginx --no-pager | head -10

echo ""
echo "=========================================="
echo "✓ Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Application is available at:"
echo "  http://$SERVER_IP"
echo ""
echo "Logs location:"
echo "  /var/log/perfume-visual/access.log"
echo "  /var/log/perfume-visual/error.log"
echo ""
echo "Management commands:"
echo "  supervisorctl status perfume-visual"
echo "  supervisorctl restart perfume-visual"
echo "  supervisorctl stop perfume-visual"
echo "  tail -f /var/log/perfume-visual/error.log"
echo ""
echo "To update the application:"
echo "  cd $APP_DIR"
echo "  git pull origin $BRANCH"
echo "  supervisorctl restart perfume-visual"
echo ""

