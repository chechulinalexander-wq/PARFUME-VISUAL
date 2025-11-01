# 🚀 Quick Start - Video Generation

## ⚡ За 3 минуты до первого видео!

### 1️⃣ Получить Replicate API Token (1 мин)

1. Откройте: https://replicate.com/signin
2. Зарегистрируйтесь (можно через GitHub)
3. Перейдите: https://replicate.com/account/api-tokens
4. Скопируйте токен (начинается с `r8_`)

### 2️⃣ Добавить токен в .env (30 сек)

Откройте файл `.env` и замените:

```env
REPLICATE_API_TOKEN=
```

На:

```env
REPLICATE_API_TOKEN=r8_ваш_токен_здесь
```

### 3️⃣ Запустить сервер (30 сек)

```bash
python app.py
```

Вы увидите:
```
[INIT] Replicate API Token loaded: r8_xxxxxxxx...xxxx
```

### 4️⃣ Сгенерировать изображение + видео (1 мин)

1. Откройте: http://localhost:8080
2. Нажмите **"Load Paris'L.A. Example"**
3. Нажмите **"Generate Visual"** → подождите 30-60 сек
4. Нажмите **"🎬 Generate Video"** → подождите 40-90 сек
5. **Готово!** Видео появится в превью

---

## 💰 Стоимость

- **Изображение:** $0.0032 (~0.26₽)
- **Видео:** $0.05 (~4.05₽)
- **Итого:** $0.0532 (~4.31₽)

Replicate дает **$5 бесплатных кредитов** при регистрации = ~100 видео! 🎉

---

## 🎬 Кастомизация промптов

### Для вращения бутылки:

Откройте **"Show Prompts"** → измените **"Video Animation Prompt"**:

```
The perfume bottle slowly rotates 360 degrees. Smooth rotation. Professional showcase.
```

### Для плавающего эффекта:

```
Gentle floating motion. Soft vertical movement. Elegant and smooth. Luxury video.
```

### Для драматичного зума:

```
Slow zoom in towards the bottle. Dramatic camera movement. Cinematic reveal.
```

---

## 🐛 Troubleshooting

**"Replicate API token not configured"**
→ Перезапустите сервер после добавления токена в `.env`

**Видео не генерируется**
→ Сначала сгенерируйте изображение, потом появится кнопка видео

**Слишком долго (>2 мин)**
→ Проверьте статус: https://status.replicate.com/

---

## 📖 Полная документация

Смотрите `STABLE_DIFFUSION_SETUP.md` для детальной информации.

---

## ✅ Готово!

Наслаждайтесь генерацией видео! 🎬✨




