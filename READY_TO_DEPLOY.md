# ✅ Project Ready for Deployment!

## 🎉 What's Been Completed

All deployment files have been created and pushed to GitHub:
- ✅ `deploy_to_server.sh` - Automated deployment script for Ubuntu VPS
- ✅ `deploy_from_windows.ps1` - Windows deployment script (requires SSH key)
- ✅ `gunicorn_config.py` - Production server configuration
- ✅ `requirements.txt` - Updated with production dependencies
- ✅ `DEPLOYMENT_GUIDE.md` - Comprehensive deployment documentation
- ✅ `DEPLOY_MANUAL.md` - **Step-by-step manual deployment guide**

## 🚀 How to Deploy

### Option 1: Direct SSH Deployment (Easiest!)

1. **Connect to your server:**
   ```bash
   ssh root@62.113.106.10
   ```

2. **Download and run deployment script:**
   ```bash
   wget https://raw.githubusercontent.com/chechulinalexander-wq/PARFUME-VISUAL/master/deploy_to_server.sh
   chmod +x deploy_to_server.sh
   bash deploy_to_server.sh
   ```

3. **Enter API keys when prompted:**
   - OpenAI API Key
   - Replicate API Token
   - Telegram Bot Token
   - Telegram Channel ID

4. **Access your app:**
   Open http://62.113.106.10 in browser

⏱️ **Deployment time:** ~5-10 minutes

---

### Option 2: Follow Manual Guide

If you prefer step-by-step instructions or encounter issues:

📖 **See:** [DEPLOY_MANUAL.md](./DEPLOY_MANUAL.md)

This guide includes:
- Copy-paste commands for each step
- Troubleshooting section
- Alternative deployment methods
- Complete setup instructions

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure you have:

- [ ] Server access (SSH to root@62.113.106.10)
- [ ] OpenAI API Key (from `.env`)
- [ ] Replicate API Token (from `.env`)
- [ ] Telegram Bot Token (from `.env`)
- [ ] Telegram Channel ID (from `.env`)

💡 **Tip:** Copy these from your local `.env` file:

```env
OPENAI_API_KEY=sk-proj-...
REPLICATE_API_TOKEN=r8_...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=-1003207484793
```

---

## 🔄 What Happens During Deployment

1. **System Update** - Updates Ubuntu packages
2. **Install Dependencies** - Python, Nginx, Supervisor, etc.
3. **Clone Repository** - Downloads code from GitHub
4. **Setup Environment** - Creates Python venv, installs packages
5. **Configure .env** - Sets up API keys and secrets
6. **Initialize Database** - Creates tables and default prompts
7. **Configure Services** - Sets up Gunicorn, Nginx, Supervisor
8. **Start Application** - Launches the web app
9. **Configure Firewall** - Opens necessary ports

---

## ✨ Features Deployed

Your production app will include:

✅ **Web Interface** - Full React-style UI  
✅ **Randewoo Integration** - Product catalog sync  
✅ **AI Image Generation** - Nano Banana / Gemini 2.5 Flash  
✅ **Video Generation** - Claude + Seedance-1-pro  
✅ **Telegram Publishing** - Automated channel posting  
✅ **Global Prompts** - Database-stored customizable prompts  
✅ **Auto-restart** - Supervisor keeps app running  
✅ **Nginx Proxy** - Fast, secure reverse proxy  
✅ **Log Management** - Centralized logging  

---

## 📍 Server Information

- **IP:** 62.113.106.10
- **Application URL:** http://62.113.106.10
- **Installation Path:** `/opt/perfume-visual`
- **Logs:** `/var/log/perfume-visual/`

### Management Commands

After deployment, you can manage the app with:

```bash
# Check status
supervisorctl status perfume-visual

# Restart app
supervisorctl restart perfume-visual

# View logs
tail -f /var/log/perfume-visual/error.log

# Update app
cd /opt/perfume-visual
git pull origin master
supervisorctl restart perfume-visual
```

---

## 🆚 Old vs New Deployment

### Old Server (Being Replaced)
- IP: 62.113.111.239
- App: perfume-publisher
- Path: /opt/perfume-publisher

### New Server (Current)
- IP: 62.113.106.10
- App: perfume-visual
- Path: /opt/perfume-visual

The deployment script will **automatically stop** any old services if they exist.

---

## 📚 Documentation

- **Quick Start:** [DEPLOY_MANUAL.md](./DEPLOY_MANUAL.md)
- **Full Guide:** [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Project README:** [README.md](./README.md)
- **Global Prompts:** [GLOBAL_PROMPTS_GUIDE.md](./GLOBAL_PROMPTS_GUIDE.md)

---

## 🐛 Troubleshooting

### Application Won't Start

```bash
tail -100 /var/log/perfume-visual/error.log
supervisorctl status perfume-visual
```

### Port Issues

```bash
lsof -i :8080
kill -9 <PID>
supervisorctl restart perfume-visual
```

### Nginx Issues

```bash
nginx -t
tail -50 /var/log/nginx/error.log
systemctl restart nginx
```

**Full troubleshooting guide:** See [DEPLOY_MANUAL.md](./DEPLOY_MANUAL.md#troubleshooting)

---

## 🎯 Next Steps

1. **Deploy the application** using Option 1 or 2 above
2. **Verify it works** by opening http://62.113.106.10
3. **Test all features:**
   - Select a perfume from Randewoo table
   - Generate image
   - Generate video
   - Create Telegram post
4. **Configure SSL** (optional) for HTTPS:
   ```bash
   certbot --nginx -d yourdomain.com
   ```
5. **Set up backups** (optional) - See DEPLOYMENT_GUIDE.md

---

## 🔒 Security Notes

⚠️ **Important:**
- ✅ `.env` is in `.gitignore` (not in git)
- ✅ API keys stored securely on server
- ✅ Firewall configured (UFW)
- ✅ Only ports 22, 80, 443 open
- ⚠️ Consider setting up SSL for HTTPS
- ⚠️ Use strong passwords
- ⚠️ Regular backups recommended

---

## 📞 Support

- **GitHub:** https://github.com/chechulinalexander-wq/PARFUME-VISUAL
- **Issues:** https://github.com/chechulinalexander-wq/PARFUME-VISUAL/issues

---

## 🎊 You're All Set!

Everything is ready for deployment. Just follow the steps above and your application will be live in minutes!

**Good luck! 🚀**

---

*Last updated: 2025-11-01*  
*Deployment target: 62.113.106.10*

