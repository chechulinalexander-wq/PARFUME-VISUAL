# Global Prompts Feature - Руководство

## Обзор

Теперь промпты для генерации изображений и Telegram постов хранятся в базе данных как **глобальные настройки**. Это означает, что одни и те же промпты применяются ко всем парфюмам, но их можно легко редактировать и сохранять прямо в интерфейсе.

## Что изменилось?

### База данных

Создана новая таблица `global_settings`:

```sql
CREATE TABLE global_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

Хранятся два промпта:
- `prompt_stylize` - Промпт для стилизации фона (Nano Banana / Gemini 2.5 Flash)
- `prompt_caption` - Промпт для генерации Telegram постов (Claude 4.5 Sonnet)

### API Endpoints

#### GET /api/settings/prompts
Получить текущие глобальные промпты из БД.

**Response:**
```json
{
    "success": true,
    "prompts": {
        "stylize": "Transform this perfume bottle...",
        "caption": "Создай продающий пост..."
    }
}
```

#### POST /api/settings/prompts
Обновить глобальные промпты в БД.

**Request:**
```json
{
    "prompt_stylize": "Your new stylization prompt...",
    "prompt_caption": "Your new caption prompt..."
}
```

**Response:**
```json
{
    "success": true,
    "message": "Prompts updated successfully"
}
```

## Как использовать?

### 1. Просмотр текущих промптов

1. Откройте веб-приложение
2. В форме генерации нажмите **"Show Prompts"**
3. Вы увидите два промпта, загруженных из БД:
   - **Background Stylization Prompt** (Nano Banana)
   - **Caption Generation Prompt** (Claude)

### 2. Редактирование промптов

1. Откройте секцию промптов
2. Отредактируйте нужный промпт прямо в текстовом поле
3. Нажмите **"💾 Save Settings"**
4. Промпты сохранятся в БД и будут применяться ко всем парфюмам

### 3. Использование плейсхолдеров

#### В промпте стилизации (prompt_stylize):
- `{DESCRIPTION}` - будет заменен на описание парфюма

**Пример:**
```
Create a beautiful atmospheric background that captures the mood and essence of this fragrance: {DESCRIPTION}
```

#### В промпте для Telegram (prompt_caption):
- `{BRAND}` - будет заменен на бренд
- `{PERFUME_NAME}` - будет заменен на название парфюма
- `{DESCRIPTION}` - будет заменен на описание

**Пример:**
```
Создай продающий пост для Telegram канала о парфюме {BRAND} {PERFUME_NAME}.

Описание аромата: {DESCRIPTION}
```

## Технические детали

### Frontend (app.js)

- При загрузке страницы вызывается `loadGlobalPrompts()`, который загружает промпты из БД через API
- Промпты сохраняются в `this.globalPrompts`
- При нажатии "Save Settings" вызывается `handleSavePrompts()`, который отправляет обновленные промпты в БД
- При генерации Telegram поста используется промпт из `this.globalPrompts.caption` с заменой плейсхолдеров

### Backend (app.py)

- `api_get_prompts()` - возвращает промпты из таблицы `global_settings`
- `api_update_prompts()` - обновляет промпты в таблице `global_settings`
- При генерации изображения используется значение поля `prompt_stylize` из формы (которое загружено из БД)

### Database

Инициализация БД выполняется автоматически при первом запуске. Дефолтные промпты уже добавлены.

## Преимущества

✅ **Централизованное управление** - один промпт для всех парфюмов  
✅ **Легкое редактирование** - прямо в интерфейсе, без изменения кода  
✅ **Версионирование** - поле `updated_at` отслеживает последнее обновление  
✅ **Гибкость** - можно использовать плейсхолдеры для динамической подстановки данных  
✅ **Консистентность** - все парфюмы генерируются с одинаковыми настройками качества  

## Обновление существующих промптов

Если вы хотите обновить дефолтные промпты:

1. Откройте веб-интерфейс
2. Нажмите "Show Prompts"
3. Отредактируйте промпты
4. Нажмите "💾 Save Settings"

Альтернативно, можно обновить через SQL:

```sql
UPDATE global_settings 
SET value = 'Your new prompt here', 
    updated_at = CURRENT_TIMESTAMP 
WHERE key = 'prompt_stylize';
```

## Совместимость

Если по какой-то причине БД не доступна или промпты не загружены, система использует хардкоженные дефолтные значения (fallback).

---

**Автор:** Perfume Visual Generator Team  
**Дата:** 2025-11-01

