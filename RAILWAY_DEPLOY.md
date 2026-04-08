# Pulse — Railway Deployment Guide

## 🚀 Быстрый старт на Railway

### 1. Подключи репозиторий
1. Зайди на [railway.app](https://railway.app)
2. Нажми **New Project** → **Deploy from GitHub repo**
3. Выбери `KingAsan/pulse`

### 2. Настрой переменные окружения
В панели Railway перейди в **Variables** и добавь:

#### Обязательные:
```
SECRET_KEY=сгенерируй-случайную-строку
JWT_SECRET_KEY=другая-случайная-строка
```

> 💡 Сгенерировать можно так: `python -c "import secrets; print(secrets.token_hex(32))"`

#### Рекомендуемые:
```
KINOPOISK_API_KEY=твоё-значение
GOOGLE_BOOKS_API_KEY=твоё-значение
GOOGLE_API_KEY=твоё-значение (для Gemini)
CORS_ORIGINS=https://your-app.up.railway.app,http://localhost:5000
```

### 3. Деплой
Railway автоматически запустит сборку после подключения репозитория.

Если нужно вручную:
```bash
railway up
```

### 4. Проверь работоспособность
Открой `https://your-app.up.railway.app/api/health`

Должен вернуться:
```json
{"status": "ok", "gemini_configured": true}
```

## 📦 Что уже настроено

- ✅ `Procfile` — точка входа `web: python backend/app.py`
- ✅ `railway.json` — конфигурация сборки/деплоя
- ✅ `requirements.txt` в корне → указывает на `backend/requirements.txt`
- ✅ SQLite база в `instance/entertainment.db` (Railway persistence)
- ✅ CORS настраивается через env
- ✅ Healthcheck endpoint `/api/health`

## 🔧 Troubleshooting

### База данных не создаётся
Railway ephemeral filesystem → SQLite сохраняется только в persistence volume.
Убедись что `DATABASE_PATH` ведёт в `/app/backend/instance/entertainment.db`

### CORS ошибки
Добавь свой домен Railway в `CORS_ORIGINS`:
```
CORS_ORIGINS=https://pulse-xyz.up.railway.app,http://localhost:5000
```

### Порт не определяется
App читает `PORT` из окружения автоматически (строка в `app.py`):
```python
port = int(os.environ.get('PORT', '5000'))
```

## 🌐 Домен
Railway выдаст домен вида `https://pulse-xxxxx.up.railway.app`
Можно подключить свой домен в настройках проекта.
