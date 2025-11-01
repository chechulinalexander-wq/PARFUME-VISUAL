# Deployment Guide - Perfume Visual Generator

## Server Information

- **Server IP:** 62.113.106.10
- **Application URL:** http://62.113.106.10
- **Application Directory:** `/opt/perfume-visual`
- **User:** `perfume-visual`

## Prerequisites

### On Your Local Machine (Windows)

1. **Git** installed
2. **SSH key** generated and added to server
3. **PowerShell** or **Git Bash**

### On Server (Ubuntu VPS)

- Ubuntu 20.04 or later
- Root access
- Internet connection

## Quick Deploy from Windows

### Option 1: Using PowerShell Script (Recommended)

```powershell
.\deploy_from_windows.ps1
```

This will:
1. Test SSH connection
2. Copy deployment script to server
3. Run deployment on server
4. Open application in browser

### Option 2: Manual Deployment

1. **Copy script to server:**
```powershell
scp deploy_to_server.sh root@62.113.106.10:/tmp/
```

2. **Connect to server:**
```powershell
ssh root@62.113.106.10
```

3. **Run deployment:**
```bash
chmod +x /tmp/deploy_to_server.sh
bash /tmp/deploy_to_server.sh
```

During deployment, you'll be asked to provide:
- OpenAI API Key
- Replicate API Token
- Telegram Bot Token
- Telegram Channel ID

## What Gets Deployed

### Application Components

- ✅ Flask web application (app.py)
- ✅ Frontend (templates/, static/)
- ✅ Database (SQLite)
- ✅ Image processing
- ✅ Video generation
- ✅ Telegram integration

### System Services

- **Gunicorn:** WSGI HTTP Server
- **Nginx:** Reverse proxy
- **Supervisor:** Process manager
- **UFW:** Firewall

### Directory Structure

```
/opt/perfume-visual/
├── app.py                    # Main Flask application
├── templates/                # HTML templates
├── static/                   # CSS, JS, images
├── main_images/             # Uploaded perfume images
├── generated_images/        # AI-generated images
├── generated_videos/        # AI-generated videos
├── fragrantica_news.db      # SQLite database
├── .env                     # Environment variables (secrets)
├── venv/                    # Python virtual environment
└── gunicorn_config.py       # Gunicorn configuration

/var/log/perfume-visual/
├── access.log               # HTTP access logs
└── error.log                # Application errors
```

## Post-Deployment

### Check Application Status

```bash
# Check if app is running
ssh root@62.113.106.10 "supervisorctl status perfume-visual"

# Check nginx
ssh root@62.113.106.10 "systemctl status nginx"
```

### View Logs

```bash
# Real-time error logs
ssh root@62.113.106.10 "tail -f /var/log/perfume-visual/error.log"

# Real-time access logs
ssh root@62.113.106.10 "tail -f /var/log/perfume-visual/access.log"
```

### Restart Application

```bash
ssh root@62.113.106.10 "supervisorctl restart perfume-visual"
```

### Update Application

```bash
ssh root@62.113.106.10
cd /opt/perfume-visual
git pull origin master
supervisorctl restart perfume-visual
```

## Management Commands

### Supervisor Commands

```bash
# Status
supervisorctl status perfume-visual

# Start
supervisorctl start perfume-visual

# Stop
supervisorctl stop perfume-visual

# Restart
supervisorctl restart perfume-visual

# View logs
supervisorctl tail -f perfume-visual
```

### Nginx Commands

```bash
# Test configuration
nginx -t

# Reload configuration
systemctl reload nginx

# Restart nginx
systemctl restart nginx

# View status
systemctl status nginx
```

### Database Management

```bash
# Backup database
cd /opt/perfume-visual
cp fragrantica_news.db fragrantica_news.db.backup.$(date +%Y%m%d)

# Access database
sqlite3 /opt/perfume-visual/fragrantica_news.db

# Check tables
sqlite3 /opt/perfume-visual/fragrantica_news.db "SELECT name FROM sqlite_master WHERE type='table';"
```

## Troubleshooting

### Application Not Starting

1. **Check logs:**
   ```bash
   tail -50 /var/log/perfume-visual/error.log
   ```

2. **Check supervisor status:**
   ```bash
   supervisorctl status perfume-visual
   ```

3. **Try manual start:**
   ```bash
   cd /opt/perfume-visual
   source venv/bin/activate
   python app.py
   ```

### Port Already in Use

```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>

# Restart application
supervisorctl restart perfume-visual
```

### Permission Issues

```bash
# Fix ownership
chown -R perfume-visual:perfume-visual /opt/perfume-visual

# Fix permissions
chmod 755 /opt/perfume-visual
chmod 644 /opt/perfume-visual/.env
chmod 755 /opt/perfume-visual/main_images
chmod 755 /opt/perfume-visual/generated_videos
```

### Database Errors

```bash
# Check database permissions
ls -la /opt/perfume-visual/fragrantica_news.db

# Fix permissions
chown perfume-visual:perfume-visual /opt/perfume-visual/fragrantica_news.db
chmod 644 /opt/perfume-visual/fragrantica_news.db
```

## Security

### Firewall (UFW)

```bash
# Check firewall status
ufw status

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS
ufw allow 443/tcp

# Allow SSH
ufw allow 22/tcp
```

### SSL Certificate (Optional)

To enable HTTPS with Let's Encrypt:

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com

# Auto-renewal test
certbot renew --dry-run
```

## Monitoring

### Resource Usage

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Application memory
ps aux | grep gunicorn
```

### Log Rotation

Logs are automatically rotated by system logrotate.

Manual rotation:
```bash
logrotate -f /etc/logrotate.d/supervisor
```

## Backup Strategy

### Automated Backup Script

Create `/opt/perfume-visual/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/perfume-visual"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /opt/perfume-visual/fragrantica_news.db $BACKUP_DIR/db_$DATE.db

# Backup uploaded images
tar -czf $BACKUP_DIR/images_$DATE.tar.gz /opt/perfume-visual/main_images

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### Schedule with Cron

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/perfume-visual/backup.sh >> /var/log/perfume-visual/backup.log 2>&1
```

## Migration from Old Server

If migrating from old server (62.113.111.239):

```bash
# 1. Backup database from old server
ssh root@62.113.111.239 "cp /opt/perfume-publisher/fragrantica_news.db /tmp/"
scp root@62.113.111.239:/tmp/fragrantica_news.db ./old_server_backup.db

# 2. Copy to new server
scp old_server_backup.db root@62.113.106.10:/opt/perfume-visual/fragrantica_news.db

# 3. Fix permissions
ssh root@62.113.106.10 "chown perfume-visual:perfume-visual /opt/perfume-visual/fragrantica_news.db"

# 4. Restart application
ssh root@62.113.106.10 "supervisorctl restart perfume-visual"
```

## Support

For issues or questions:
- Check logs: `/var/log/perfume-visual/error.log`
- GitHub Issues: https://github.com/chechulinalexander-wq/PARFUME-VISUAL/issues
- Repository: https://github.com/chechulinalexander-wq/PARFUME-VISUAL

## Version Info

- **Application:** Perfume Visual Generator
- **Python:** 3.8+
- **Flask:** 3.0.0
- **Gunicorn:** 21.2.0
- **Deployment Date:** 2025-11-01

