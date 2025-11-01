# 🚀 Deployment на новый сервер 84.54.31.86

## Информация о сервере

- **IP:** 84.54.31.86
- **Провайдер:** Beget VPS
- **ОС:** Ubuntu (предположительно 20.04/22.04)
- **Доступ:** root@84.54.31.86

---

## ⚡ Быстрый деплой (3 команды)

### Шаг 1: Подключитесь к серверу

```bash
ssh root@84.54.31.86
```

### Шаг 2: Скачайте и запустите deployment скрипт

```bash
wget https://raw.githubusercontent.com/chechulinalexander-wq/PARFUME-VISUAL/master/deploy_to_84.54.31.86.sh
chmod +x deploy_to_84.54.31.86.sh
bash deploy_to_84.54.31.86.sh
```

### Шаг 3: Введите API ключи

Когда система попросит, введите:
- **OpenAI API Key**
- **Replicate API Token**
- **Telegram Bot Token**
- **Telegram Channel ID**

### Шаг 4: Откройте приложение

```
http://84.54.31.86
```

---

## 📋 Подготовьте эти данные

Скопируйте из локального `.env` файла:

```env
OPENAI_API_KEY=sk-proj-...
REPLICATE_API_TOKEN=r8_...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=-1003207484793
```

---

## ✨ Что будет установлено

### Системные пакеты
- ✅ Python 3 + pip + venv
- ✅ Git
- ✅ Nginx (reverse proxy)
- ✅ Supervisor (process manager)
- ✅ UFW (firewall)
- ✅ SQLite3
- ✅ Curl, Wget, Htop

### Приложение
- ✅ Flask web application
- ✅ Gunicorn WSGI server
- ✅ AI генерация изображений (Nano Banana)
- ✅ Генерация видео (Seedance-1-pro)
- ✅ Telegram интеграция
- ✅ База данных SQLite
- ✅ Глобальные промпты

### Структура директорий

```
/opt/perfume-visual/
├── app.py                    # Main application
├── gunicorn_config.py        # Server config
├── requirements.txt          # Dependencies
├── .env                      # API keys (secret)
├── venv/                     # Python virtual env
├── templates/                # HTML templates
├── static/                   # CSS, JS
├── main_images/             # Uploaded images
├── generated_images/        # AI generated images
├── generated_videos/        # AI generated videos
└── fragrantica_news.db      # SQLite database

/var/log/perfume-visual/
├── access.log               # HTTP access logs
└── error.log                # Application errors
```

---

## ⏱️ Время деплоя

**Общее время:** 5-10 минут

- Обновление системы: 1-2 мин
- Установка пакетов: 2-3 мин
- Клонирование репозитория: 30 сек
- Установка Python зависимостей: 1-2 мин
- Конфигурация сервисов: 1 мин

---

## 🔍 Проверка после деплоя

### 1. Откройте в браузере

```
http://84.54.31.86
```

Вы должны увидеть:
- ✅ "Perfume Visual Generator" интерфейс
- ✅ Таблицу Randewoo Products
- ✅ Секцию "AI Processing Prompts"
- ✅ Кнопку "💾 Save Settings"

### 2. Проверьте статус на сервере

```bash
ssh root@84.54.31.86

# Статус приложения
supervisorctl status perfume-visual
# Должно быть: RUNNING

# Логи (не должно быть ошибок)
tail -20 /var/log/perfume-visual/error.log

# Nginx
systemctl status nginx

# HTTP ответ
curl -I http://localhost:8080
```

---

## 🛠️ Управление приложением

### Перезапуск

```bash
ssh root@84.54.31.86
supervisorctl restart perfume-visual
```

### Просмотр логов

```bash
# Ошибки
tail -f /var/log/perfume-visual/error.log

# Доступ
tail -f /var/log/perfume-visual/access.log

# Оба
tail -f /var/log/perfume-visual/*.log
```

### Остановка/Запуск

```bash
supervisorctl stop perfume-visual
supervisorctl start perfume-visual
supervisorctl status perfume-visual
```

### Обновление кода

```bash
cd /opt/perfume-visual
git pull origin master
supervisorctl restart perfume-visual
```

---

## 🔥 Порты и сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| Nginx | 80 | HTTP (внешний доступ) |
| Gunicorn | 8080 | WSGI server (внутренний) |
| SSH | 22 | Удаленный доступ |

### Firewall (UFW)

```bash
# Проверить статус
ufw status

# Открытые порты
ufw status numbered

# 22 (SSH)
# 80 (HTTP)
# 443 (HTTPS)
```

---

## 🐛 Troubleshooting

### Приложение не запускается

```bash
# Проверить логи
tail -50 /var/log/perfume-visual/error.log

# Проверить supervisor
supervisorctl status

# Попробовать запустить вручную
cd /opt/perfume-visual
source venv/bin/activate
python app.py
```

### Nginx показывает 502 Bad Gateway

```bash
# Проверить что приложение работает
supervisorctl status perfume-visual

# Проверить что порт 8080 слушается
lsof -i :8080

# Перезапустить всё
supervisorctl restart perfume-visual
systemctl restart nginx
```

### Git ошибка "dubious ownership"

```bash
chown -R root:root /opt/perfume-visual
git config --global --add safe.directory /opt/perfume-visual
```

### База данных пустая

```bash
# Проверить что база создана
ls -la /opt/perfume-visual/fragrantica_news.db

# Проверить таблицы
sqlite3 /opt/perfume-visual/fragrantica_news.db "SELECT name FROM sqlite_master WHERE type='table';"

# Должны быть: global_settings, randewoo_products
```

### Порт 8080 занят

```bash
# Найти процесс
lsof -i :8080

# Убить процесс
kill -9 <PID>

# Или найти все Python процессы
ps aux | grep python
```

---

## 🔒 Безопасность

### API ключи

✅ Хранятся в `/opt/perfume-visual/.env`  
✅ Права доступа: `600` (только root)  
✅ Не в git (в `.gitignore`)

### Firewall

✅ UFW включен  
✅ Только необходимые порты открыты  
⚠️ Рассмотрите настройку fail2ban для защиты SSH

### SSL (опционально)

Для включения HTTPS с Let's Encrypt:

```bash
apt-get install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

---

## 📊 Мониторинг

### Ресурсы сервера

```bash
# CPU, RAM, процессы
htop

# Диск
df -h

# Память приложения
ps aux | grep gunicorn
```

### Логи в реальном времени

```bash
# Только ошибки
tail -f /var/log/perfume-visual/error.log

# Доступ + ошибки
tail -f /var/log/perfume-visual/*.log

# Nginx
tail -f /var/log/nginx/error.log
```

---

## 📦 Backup

### Ручной backup

```bash
# База данных
cp /opt/perfume-visual/fragrantica_news.db \
   /opt/perfume-visual/backup_$(date +%Y%m%d).db

# Изображения
tar -czf /tmp/images_backup.tar.gz \
   /opt/perfume-visual/main_images

# Полный backup
tar -czf /tmp/perfume-visual_backup.tar.gz \
   --exclude=/opt/perfume-visual/venv \
   /opt/perfume-visual
```

### Автоматический backup (cron)

```bash
# Создать скрипт
cat > /opt/backup_perfume.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup DB
cp /opt/perfume-visual/fragrantica_news.db \
   $BACKUP_DIR/db_$DATE.db

# Удалить старые (>7 дней)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /opt/backup_perfume.sh

# Добавить в cron (ежедневно в 3:00)
echo "0 3 * * * /opt/backup_perfume.sh" | crontab -
```

---

## 🔄 Сравнение серверов

| Параметр | 62.113.106.10 | 84.54.31.86 (новый) |
|----------|---------------|---------------------|
| **Провайдер** | Beget | Beget |
| **Статус** | Старое приложение | Чистая установка |
| **Приложение** | Perfume Publisher | Perfume Visual |
| **Порт** | 8000 | 8080 |
| **Путь** | /opt/perfume-publisher | /opt/perfume-visual |

---

## ✅ Чеклист после деплоя

- [ ] Приложение доступно по http://84.54.31.86
- [ ] Supervisor показывает RUNNING
- [ ] Nginx работает (active)
- [ ] База данных инициализирована
- [ ] Глобальные промпты сохранены
- [ ] Логи чистые (нет критических ошибок)
- [ ] UFW включен и настроен
- [ ] API ключи в .env файле

---

## 📚 Дополнительные материалы

- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Manual Deploy:** [DEPLOY_MANUAL.md](./DEPLOY_MANUAL.md)
- **Quick Reference:** [QUICK_DEPLOY.txt](./QUICK_DEPLOY.txt)
- **GitHub:** https://github.com/chechulinalexander-wq/PARFUME-VISUAL

---

## 🎉 Готово!

После успешного деплоя у вас будет полностью работающее приложение на новом сервере!

**Удачи! 🚀**

---

*Создано: 2025-11-01*  
*Сервер: 84.54.31.86 (Beget VPS)*  
*Приложение: Perfume Visual Generator*

