# Инструкция по исправлению ошибки API на 84.54.31.86

## Проблема
При открытии http://84.54.31.86/ в блоке "Товары Randewoo" показывается ошибка:
```
Error loading products: Unexpected token '<', "<!DOCTYPE html>..."
```

## Причина
Nginx был настроен неправильно - он не проксировал запросы к `/api/*` на Flask приложение. Вместо этого он пытался найти файлы на диске и возвращал HTML страницу ошибки 404, которую JavaScript пытался распарсить как JSON.

## Решение

### Вариант 1: Быстрый фикс (рекомендуется)

Подключитесь к серверу по SSH и выполните:

```bash
# Скачать скрипт фикса
cd /opt/perfume-visual
git pull origin master

# Запустить скрипт фикса
chmod +x fix_nginx_on_server.sh
sudo ./fix_nginx_on_server.sh
```

Скрипт автоматически:
- Создаст бэкап текущей конфигурации
- Обновит конфигурацию nginx
- Протестирует конфигурацию
- Перезагрузит nginx
- Проверит работу API

### Вариант 2: Ручное исправление

Если нужно исправить вручную:

```bash
# Подключиться к серверу
ssh root@84.54.31.86

# Создать бэкап
sudo cp /etc/nginx/sites-available/perfume-visual /etc/nginx/sites-available/perfume-visual.backup

# Отредактировать конфигурацию
sudo nano /etc/nginx/sites-available/perfume-visual
```

Замените содержимое на:

```nginx
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

    # API endpoints - proxy to Flask app (ВАЖНО!)
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
```

Затем:

```bash
# Проверить конфигурацию
sudo nginx -t

# Если OK, перезагрузить nginx
sudo systemctl reload nginx

# Проверить API
curl http://localhost/api/test
```

## Проверка

После применения фикса откройте в браузере:
- http://84.54.31.86/ - главная страница
- http://84.54.31.86/api/test - должен вернуть JSON с статусом

Блок "Товары Randewoo" должен загрузиться корректно.

## Ключевые изменения

1. **Добавлен блок `location /api`** - теперь все запросы к API проксируются на Flask
2. **Изменен порядок location блоков** - `/api` обрабатывается ДО общего `/`
3. **Исправлен `/images`** - теперь ищет в `main_images`, затем в `generated_images`

## Если не помогло

Проверьте статус приложения:

```bash
# Статус supervisor
sudo supervisorctl status perfume-visual

# Логи приложения
sudo tail -f /var/log/perfume-visual/error.log

# Логи nginx
sudo tail -f /var/log/nginx/error.log

# Если приложение не запущено
sudo supervisorctl restart perfume-visual
```

## Коммит изменений

Изменения уже добавлены в репозиторий:
- `fix_nginx_on_server.sh` - скрипт для быстрого исправления
- `nginx_config_84.54.31.86.conf` - новая конфигурация nginx
- `deploy_to_84.54.31.86.sh` - обновлен скрипт деплоя

Закоммитьте и запушьте в GitHub:

```bash
git add .
git commit -m "fix: Add proper nginx config for API routing on 84.54.31.86"
git push origin master
```
