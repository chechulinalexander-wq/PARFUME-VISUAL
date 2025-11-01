# 🔄 Замена старого приложения на новое

## Текущая ситуация

На сервере **62.113.106.10** сейчас работает старое приложение:
- 🔴 **Perfume Publisher** (из проекта PARFUME BOT AND PARSE)
- URL: http://62.113.106.10
- Путь: `/opt/perfume-publisher`

Нужно заменить на:
- 🟢 **Perfume Visual Generator** (текущий проект)
- Путь: `/opt/perfume-visual`

---

## 🚀 Быстрая замена (1 команда)

### Шаг 1: Подключитесь к серверу

```bash
ssh root@62.113.106.10
```

### Шаг 2: Скачайте и запустите скрипт замены

```bash
wget https://raw.githubusercontent.com/chechulinalexander-wq/PARFUME-VISUAL/master/replace_old_app.sh
chmod +x replace_old_app.sh
bash replace_old_app.sh
```

### Шаг 3: Введите API ключи

Когда система попросит, введите:
- **OpenAI API Key**
- **Replicate API Token**
- **Telegram Bot Token**
- **Telegram Channel ID**

### Шаг 4: Готово!

Откройте http://62.113.106.10 — там будет новое приложение! 🎉

---

## 📋 Что делает скрипт

✅ **Останавливает** старое приложение (perfume-app, perfume-publisher)  
✅ **Удаляет** старые конфигурации Supervisor и Nginx  
✅ **Создаёт backup** старого приложения в `/opt/backups/`  
✅ **Клонирует** новый код из GitHub  
✅ **Настраивает** Python окружение  
✅ **Создаёт** базу данных с таблицами  
✅ **Настраивает** Nginx и Supervisor  
✅ **Запускает** новое приложение  
✅ **Проверяет** что всё работает  

---

## 🔍 Проверка после замены

### Откройте в браузере

**http://62.113.106.10**

Вы должны увидеть:
- ✅ Новый интерфейс "Perfume Visual Generator"
- ✅ Секция "AI Processing Prompts"
- ✅ Поле "Background Stylization Prompt"
- ✅ Поле "Caption Generation Prompt"
- ✅ Кнопка "💾 Save Settings"
- ✅ Таблица Randewoo Products

### Проверьте статус на сервере

```bash
ssh root@62.113.106.10

# Статус приложения
supervisorctl status perfume-visual

# Должно показать: RUNNING

# Проверьте логи (не должно быть ошибок)
tail -20 /var/log/perfume-visual/error.log

# Проверьте Nginx
systemctl status nginx
```

---

## 🆚 Сравнение старого и нового

| Параметр | Старое приложение | Новое приложение |
|----------|-------------------|------------------|
| **Название** | Perfume Publisher | Perfume Visual Generator |
| **Путь** | `/opt/perfume-publisher` | `/opt/perfume-visual` |
| **Supervisor** | `perfume-app` | `perfume-visual` |
| **Порт** | 8000 | 8080 |
| **WSGI** | web_app:app | app:app |
| **Функции** | Базовое управление | AI генерация изображений/видео |
| **Промпты** | Хардкод | Глобальные (в БД) |
| **API** | OpenAI | OpenAI + Replicate |

---

## 🛠️ Управление новым приложением

### Перезапустить

```bash
ssh root@62.113.106.10
supervisorctl restart perfume-visual
```

### Посмотреть логи

```bash
ssh root@62.113.106.10
tail -f /var/log/perfume-visual/error.log
```

### Обновить код

```bash
ssh root@62.113.106.10
cd /opt/perfume-visual
git pull origin master
supervisorctl restart perfume-visual
```

### Проверить статус

```bash
ssh root@62.113.106.10
supervisorctl status perfume-visual
curl -I http://localhost:8080
```

---

## 🔙 Откат к старому приложению (если нужно)

Если что-то пошло не так, можно вернуть старое приложение:

```bash
ssh root@62.113.106.10

# Остановить новое приложение
supervisorctl stop perfume-visual

# Найти backup
ls -lt /opt/backups/

# Восстановить (замените дату на вашу)
mv /opt/perfume-visual /opt/perfume-visual-failed
mv /opt/backups/perfume-publisher-20251101_123456 /opt/perfume-publisher

# Восстановить конфиги (если нужно)
# ... (старые конфиги в backup)

# Запустить старое приложение
supervisorctl start perfume-app
```

---

## 📦 Где бэкап старого приложения

После замены старое приложение будет здесь:

```
/opt/backups/perfume-publisher-YYYYMMDD_HHMMSS/
```

Можно удалить, когда убедитесь что новое работает:

```bash
rm -rf /opt/backups/perfume-publisher-*
```

---

## 🐛 Troubleshooting

### Приложение не запускается

```bash
# Посмотрите логи
tail -50 /var/log/perfume-visual/error.log

# Проверьте supervisor
supervisorctl status

# Попробуйте запустить вручную
cd /opt/perfume-visual
source venv/bin/activate
python app.py
```

### Nginx показывает 502 Bad Gateway

```bash
# Проверьте что приложение работает
supervisorctl status perfume-visual

# Проверьте порт
lsof -i :8080

# Перезапустите
supervisorctl restart perfume-visual
```

### Старое приложение всё ещё работает

```bash
# Проверьте все процессы supervisor
supervisorctl status

# Остановите всё старое
supervisorctl stop perfume-app
supervisorctl stop perfume-publisher
supervisorctl stop web_app

# Удалите старые конфиги
rm -f /etc/supervisor/conf.d/perfume-app.conf
rm -f /etc/supervisor/conf.d/perfume-publisher.conf
supervisorctl reread
supervisorctl update
```

### База данных пустая

```bash
# Проверьте что база создана
ls -la /opt/perfume-visual/fragrantica_news.db

# Проверьте таблицы
sqlite3 /opt/perfume-visual/fragrantica_news.db "SELECT name FROM sqlite_master WHERE type='table';"

# Должны быть: global_settings, randewoo_products
```

---

## ⏱️ Время замены

**Общее время:** ~5-10 минут

- Подключение к серверу: 30 сек
- Скачивание скрипта: 10 сек
- Выполнение скрипта: 3-5 мин
- Проверка: 1 мин

---

## 📞 Поддержка

Если возникли проблемы:

1. **Проверьте логи:** `/var/log/perfume-visual/error.log`
2. **Проверьте статус:** `supervisorctl status`
3. **GitHub Issues:** https://github.com/chechulinalexander-wq/PARFUME-VISUAL/issues

---

## ✅ Чеклист после замены

- [ ] Старое приложение остановлено
- [ ] Новое приложение запущено
- [ ] http://62.113.106.10 открывается
- [ ] Виден новый интерфейс
- [ ] Есть секция "AI Processing Prompts"
- [ ] База данных инициализирована
- [ ] Логи чистые (нет ошибок)
- [ ] Supervisor показывает RUNNING
- [ ] Nginx работает

---

## 🎉 Готово!

После успешной замены:

✅ **Старое приложение:** Остановлено и в бэкапе  
✅ **Новое приложение:** Работает на http://62.113.106.10  
✅ **Все функции:** Доступны (генерация изображений, видео, Telegram)  
✅ **Глобальные промпты:** Настроены в базе данных  

**Приятной работы! 🚀**

---

*Создано: 2025-11-01*  
*Сервер: 62.113.106.10*  
*Репозиторий: https://github.com/chechulinalexander-wq/PARFUME-VISUAL*

