# 🚀 Quick Start: Telegram Post с Claude

## Что изменилось

**Кнопка переименована:**  
"Publish to Telegram" → "Create TG post"

**Новые возможности:**
- ✅ Автоматическая генерация caption через Claude
- ✅ Редактируемый промпт для Claude
- ✅ Редактируемый сгенерированный текст
- ✅ Кнопка "Recreate TG text" для регенерации
- ✅ Автоматическое прикрепление видео (если есть)
- ✅ Live preview с видео/изображением

## Как использовать

### Simple Workflow

```
1. Generate Visual
   ↓
2. [Optional] Generate Video
   ↓
3. Click "Create TG post"
   ↓
4. [AUTO] Claude генерирует caption (~10 секунд)
   ↓
5. [Optional] Edit prompt/caption
   ↓
6. [Optional] Click "Recreate TG text"
   ↓
7. Click "Publish to Telegram"
   ↓
8. Done! Video прикрепится автоматически если есть
```

## UI Layout

```
┌─────────────────────────────────────────┐
│ 📤 Post to Telegram              [✕]   │
├─────────────────────────────────────────┤
│                                         │
│ Caption Generation Prompt:              │
│ ┌─────────────────────────────────────┐ │
│ │ Создай продающий пост для...       │ │  <- Можно редактировать
│ │ (промпт для Claude)                 │ │
│ └─────────────────────────────────────┘ │
│           [🔄 Recreate TG text]         │
│                                         │
│ Generated Caption:                      │
│ ┌─────────────────────────────────────┐ │
│ │ ✨ Givenchy L'Interdit – это...   │ │  <- Можно редактировать
│ │ (сгенерированный текст)             │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Preview:                                │
│ ┌─────────────────────────────────────┐ │
│ │ [VIDEO PLAYER]     🎬 Video         │ │  <- Видео если есть
│ │                                     │ │
│ │ ✨ Givenchy L'Interdit – это...   │ │  <- Live preview
│ └─────────────────────────────────────┘ │
│                                         │
│ ℹ️ Ready to publish                     │
│                                         │
│        [🚀 Publish to Telegram]         │
│                                         │
└─────────────────────────────────────────┘
```

## Примеры

### Example 1: Basic Usage

**Input:**
- Brand: Givenchy
- Name: L'Interdit
- Description: Белый цветок туберозы...

**Claude Output:**
```
✨ Givenchy L'Interdit – это магия белого 
цветка туберозы, которая окутывает вас 
роскошным шлейфом! 🌸

Этот аромат создан для смелых женщин, 
которые не боятся выделяться 💫
```

**Action:** Click "Publish" → Done!

### Example 2: Custom Prompt

**Edit Prompt:**
```
Создай короткий luxury пост (2 предложения) 
для парфюма Givenchy L'Interdit. 
Без емодзи. Формальный тон.
```

**Click "Recreate TG text"**

**New Output:**
```
Givenchy L'Interdit воплощает изысканность 
и смелость в одном флаконе.

Белый цветок туберозы в окружении восточных 
нот создаёт незабываемую композицию для 
уверенных в себе женщин.
```

### Example 3: With Video

```
1. Generate Visual ✓
2. Generate Video ✓
3. Click "Create TG post"
   → Preview показывает VIDEO
   → Badge: "🎬 Video"
4. Caption generated
5. Click "Publish"
   → VIDEO отправится в Telegram с caption
```

## Console Output

### Successful Flow
```
[TG] Generating caption...
[TG CAPTION] Calling Claude 4.5 Sonnet via Replicate...
[TG CAPTION] ✓ Caption generated: ✨ Givenchy...
[TG] Caption generated
[TELEGRAM] Publishing: {media_type: "video", ...}
[TELEGRAM] ✓ Published successfully!
```

### With Recreate
```
[TG] Generating caption...
[TG CAPTION] ✓ Caption generated: ✨ Givenchy...
(user clicks Recreate)
[TG] Generating caption...
[TG CAPTION] ✓ Caption generated: 💫 Новый текст...
```

## Tips

### 💡 Tip 1: Edit Prompt for Different Styles

**Luxury:**
```
Создай luxury пост без емодзи в формальном тоне
```

**Casual:**
```
Создай casual пост с емодзи и разговорным стилем
```

**Short:**
```
Создай короткий пост (1-2 предложения)
```

### 💡 Tip 2: Live Preview

При редактировании caption в textarea - preview обновляется в реальном времени.

### 💡 Tip 3: Video Priority

Если есть и image, и video - в Telegram отправится **VIDEO** автоматически.

### 💡 Tip 4: Manual Edit

Можно полностью заменить текст вручную, Claude - это лишь starting point.

## Timing

| Action | Time |
|--------|------|
| Generate caption | ~10 seconds |
| Edit caption | Instant |
| Recreate caption | ~10 seconds |
| Publish | ~2-5 seconds |

**Total:** ~15-30 seconds от "Create TG post" до "Published"

## Requirements

- ✅ Replicate API token (для Claude)
- ✅ Telegram Bot token
- ✅ Generated image (required)
- ✅ Generated video (optional)

## Cost per Post

| Component | Cost |
|-----------|------|
| Caption generation (Claude) | ~$0.003 |
| Video generation (Seedance) | ~$0.10 |
| Publish to Telegram | Free |

**Total:** $0.003 (image only) or $0.103 (with video)

## Troubleshooting

### "⏳ Generating..." бесконечно

✅ **Solution:** Check Replicate API token in .env

### Caption пустой

✅ **Solution:** Wait 10 seconds or check console for errors

### Video не прикрепился

✅ **Solution:** Check that video was generated before clicking "Create TG post"

### Preview не обновляется

✅ **Solution:** Hard refresh (Ctrl+F5)

## Next Steps

После publish:
1. Проверь пост в Telegram канале
2. Если нужно - edit post в Telegram
3. Monitor engagement

---

**Quick Reference:**
- Full docs: `TELEGRAM_POST_CLAUDE_INTEGRATION.md`
- Video docs: `VIDEO_CLAUDE_SEEDANCE.md`
- Error handling: `VIDEO_502_ERROR_FIX.md`



