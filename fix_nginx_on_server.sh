#!/bin/bash
# Fix nginx configuration on 84.54.31.86 to properly handle API requests

set -e

echo "=========================================="
echo "Fixing nginx configuration for API routing"
echo "Server: 84.54.31.86"
echo "=========================================="
echo ""

APP_DIR="/opt/perfume-visual"

echo "Step 1: Backing up current nginx config..."
cp /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-available/perfume-visual.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backup created"

echo ""
echo "Step 2: Updating nginx configuration..."
cat > /etc/nginx/sites-available/perfume-visual <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name 84.54.31.86 _;

    client_max_body_size 100M;
    client_body_timeout 300s;

    # Static files (CSS, JS, etc)
    location /static {
        alias /opt/perfume-visual/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Images - try main_images first, then generated_images
    location /images {
        alias /opt/perfume-visual/main_images;
        try_files $uri @generated_images;
        expires 7d;
        add_header Cache-Control "public";
    }

    location @generated_images {
        alias /opt/perfume-visual/generated_images;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Videos
    location /videos {
        alias /opt/perfume-visual/generated_videos;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API endpoints - proxy to Flask app
    location /api {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increased timeouts for AI processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Everything else - proxy to Flask app
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increased timeouts for AI processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
EOF

echo "✓ Configuration updated"

echo ""
echo "Step 3: Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✓ Configuration test passed"

    echo ""
    echo "Step 4: Reloading nginx..."
    systemctl reload nginx
    echo "✓ Nginx reloaded"

    echo ""
    echo "Step 5: Testing API endpoint..."
    sleep 2
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/test)
    echo "API response code: $HTTP_CODE"

    echo ""
    echo "=========================================="
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ FIX SUCCESSFUL!"
        echo ""
        echo "API is now working correctly."
        echo "Test it: http://84.54.31.86/api/test"
    else
        echo "⚠️  Warning: API returned code $HTTP_CODE"
        echo ""
        echo "Checking application status..."
        supervisorctl status perfume-visual
        echo ""
        echo "Check logs:"
        echo "  tail -f /var/log/perfume-visual/error.log"
    fi
    echo "=========================================="
else
    echo "❌ Configuration test failed!"
    echo "Restoring backup..."
    cp /etc/nginx/sites-available/perfume-visual.backup.* /etc/nginx/sites-available/perfume-visual
    exit 1
fi

echo ""
echo "🎉 Done!"
echo ""
