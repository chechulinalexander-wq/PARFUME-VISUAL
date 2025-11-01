#!/bin/bash
# Replace old Perfume Publisher with new Perfume Visual Generator
# Server: 62.113.106.10

set -e

echo "=========================================="
echo "Replacing Old App with New One"
echo "=========================================="
echo ""

SERVER_IP="62.113.106.10"
APP_DIR="/opt/perfume-visual"
OLD_APP_DIR="/opt/perfume-publisher"
REPO_URL="https://github.com/chechulinalexander-wq/PARFUME-VISUAL.git"
BRANCH="master"

echo "Step 1: Stopping old application..."
# Stop old services
if supervisorctl status perfume-app &>/dev/null 2>&1; then
    supervisorctl stop perfume-app
    echo "✓ Old perfume-app stopped"
fi

if supervisorctl status perfume-publisher &>/dev/null 2>&1; then
    supervisorctl stop perfume-publisher
    echo "✓ Old perfume-publisher stopped"
fi

if supervisorctl status web_app &>/dev/null 2>&1; then
    supervisorctl stop web_app
    echo "✓ Old web_app stopped"
fi

echo ""
echo "Step 2: Removing old supervisor configs..."
rm -f /etc/supervisor/conf.d/perfume-app.conf
rm -f /etc/supervisor/conf.d/perfume-publisher.conf
rm -f /etc/supervisor/conf.d/web_app.conf
supervisorctl reread
supervisorctl update
echo "✓ Old configs removed"

echo ""
echo "Step 3: Removing old nginx configs..."
rm -f /etc/nginx/sites-enabled/perfume-app
rm -f /etc/nginx/sites-enabled/perfume-publisher
rm -f /etc/nginx/sites-available/perfume-app
rm -f /etc/nginx/sites-available/perfume-publisher
echo "✓ Old nginx configs removed"

echo ""
echo "Step 4: Backing up old application..."
if [ -d "$OLD_APP_DIR" ]; then
    BACKUP_DIR="/opt/backups/perfume-publisher-$(date +%Y%m%d_%H%M%S)"
    mkdir -p /opt/backups
    mv $OLD_APP_DIR $BACKUP_DIR
    echo "✓ Old app backed up to: $BACKUP_DIR"
else
    echo "✓ No old app found at $OLD_APP_DIR"
fi

echo ""
echo "Step 5: Creating new application directory..."
mkdir -p $APP_DIR
mkdir -p /var/log/perfume-visual
echo "✓ Directories created"

echo ""
echo "Step 6: Cloning new repository..."
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
fi
echo "✓ Repository cloned/updated"

echo ""
echo "Step 7: Setting up Python environment..."
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
echo "✓ Python environment ready"

echo ""
echo "Step 8: Creating .env file..."
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
echo "Step 9: Creating directories..."
mkdir -p $APP_DIR/main_images
mkdir -p $APP_DIR/generated_images
mkdir -p $APP_DIR/generated_videos
chmod 755 $APP_DIR/main_images
chmod 755 $APP_DIR/generated_images
chmod 755 $APP_DIR/generated_videos
echo "✓ Directories created"

echo ""
echo "Step 10: Initializing database..."
source $APP_DIR/venv/bin/activate
python3 <<PYTHON_SCRIPT
import sqlite3

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
cursor.execute('''
    INSERT OR IGNORE INTO global_settings (key, value)
    VALUES (?, ?)
''', ('prompt_stylize', '''Transform this perfume bottle image by adding a stunning, vibrant, artistic background while keeping the bottle EXACTLY as it is - same shape, same color, same text, same position.

Create a beautiful atmospheric background that captures the mood and essence of this fragrance: {DESCRIPTION}

The background should feature: vivid elegant colors with glowing bokeh lights in pink, purple, gold, and blue tones, soft dreamy blur, sophisticated luxury ambiance, professional studio lighting with colored gels, cinematic composition. Make it look like high-end commercial perfume advertising photography with magazine quality.

IMPORTANT: Do NOT change the perfume bottle itself - keep it identical to the input. Only transform the background behind it!'''))

# Insert default caption prompt
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
print('✓ Database initialized!')
PYTHON_SCRIPT
echo "✓ Database ready"

echo ""
echo "Step 11: Configuring Supervisor..."
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
EOF

supervisorctl reread
supervisorctl update
echo "✓ Supervisor configured"

echo ""
echo "Step 12: Configuring Nginx..."
cat > /etc/nginx/sites-available/perfume-visual <<EOF
server {
    listen 80 default_server;
    server_name $SERVER_IP _;

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

ln -sf /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-enabled/perfume-visual
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
echo "✓ Nginx configured and reloaded"

echo ""
echo "Step 13: Starting new application..."
supervisorctl start perfume-visual
sleep 3
supervisorctl status perfume-visual
echo "✓ Application started"

echo ""
echo "Step 14: Final checks..."
echo "Testing application..."
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Application responding correctly (HTTP $HTTP_CODE)"
else
    echo "⚠️  Warning: HTTP response code: $HTTP_CODE"
    echo "Check logs: tail -50 /var/log/perfume-visual/error.log"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Completed Successfully!"
echo "=========================================="
echo ""
echo "🎉 New application is live at:"
echo "   http://$SERVER_IP"
echo ""
echo "📊 Status:"
supervisorctl status perfume-visual | head -1
echo ""
echo "📝 Logs:"
echo "   Access: /var/log/perfume-visual/access.log"
echo "   Errors: /var/log/perfume-visual/error.log"
echo ""
echo "🔧 Management:"
echo "   Status:  supervisorctl status perfume-visual"
echo "   Restart: supervisorctl restart perfume-visual"
echo "   Logs:    tail -f /var/log/perfume-visual/error.log"
echo ""
echo "📦 Old app backed up to:"
[ -d "/opt/backups" ] && ls -t /opt/backups | head -1 | xargs -I {} echo "   /opt/backups/{}"
echo ""

