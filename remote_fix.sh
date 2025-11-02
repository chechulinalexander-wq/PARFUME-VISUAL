#!/bin/bash
# Remote fix script - runs commands on 84.54.31.86 from local machine

SERVER="root@84.54.31.86"

echo "=========================================="
echo "Remote Fix for nginx on 84.54.31.86"
echo "=========================================="
echo ""

echo "Step 1: Finding project directory..."
PROJECT_DIR=$(ssh $SERVER "ls -d /root/PARFUME* /opt/perfume* 2>/dev/null | head -1")

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found!"
    echo "Searching in common locations..."
    ssh $SERVER "ls -la /root/ /opt/"
    exit 1
fi

echo "✓ Found project at: $PROJECT_DIR"

echo ""
echo "Step 2: Backing up current nginx config..."
ssh $SERVER "cp /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-available/perfume-visual.backup.\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'No existing config found'"

echo ""
echo "Step 3: Updating nginx configuration..."
ssh $SERVER "cat > /etc/nginx/sites-available/perfume-visual" <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name 84.54.31.86 _;

    client_max_body_size 100M;
    client_body_timeout 300s;

    # Static files (CSS, JS, etc)
    location /static {
        alias /root/PARFUME-VISUAL/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Images - try main_images first, then generated_images
    location /images {
        alias /root/PARFUME-VISUAL/main_images;
        try_files $uri @generated_images;
        expires 7d;
        add_header Cache-Control "public";
    }

    location @generated_images {
        alias /root/PARFUME-VISUAL/generated_images;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Videos
    location /videos {
        alias /root/PARFUME-VISUAL/generated_videos;
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
echo "Step 4: Enabling site..."
ssh $SERVER "ln -sf /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-enabled/perfume-visual"

echo ""
echo "Step 5: Testing nginx configuration..."
TEST_RESULT=$(ssh $SERVER "nginx -t 2>&1")
echo "$TEST_RESULT"

if echo "$TEST_RESULT" | grep -q "test is successful"; then
    echo "✓ Configuration test passed"

    echo ""
    echo "Step 6: Reloading nginx..."
    ssh $SERVER "systemctl reload nginx"
    echo "✓ Nginx reloaded"

    echo ""
    echo "Step 7: Testing API endpoint..."
    sleep 2
    HTTP_CODE=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost/api/test")
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
        ssh $SERVER "systemctl status app.service 2>/dev/null || supervisorctl status 2>/dev/null || echo 'Could not check app status'"
    fi
    echo "=========================================="
else
    echo "❌ Configuration test failed!"
    exit 1
fi

echo ""
echo "🎉 Done!"
echo ""
