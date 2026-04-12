# 🚀 Pulse — Деплой на Railway

## Почему Railway?

✅ **$5 бесплатных кредитов/мес** - хватает для одного сервиса  
✅ **Сервер работает постоянно** - не выключается  
✅ **Persistent Storage** - данные сохраняются  
✅ **Серверы в США/Европе** - HDRezka работает без VPN!  
✅ **Автоматический деплой** из GitHub  

---

## 📋 Пошаговая инструкция

### Шаг 1: Подготовка секретов

Сгенерируйте секреты:

```bash
python -c "import secrets; print('SECRET_KEY:', secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_hex(32))"
```

Сохраните вывод - они понадобятся!

### Шаг 2: Подключить репозиторий к Railway

1. Откройте [railway.app](https://railway.app)
2. Войдите через GitHub
3. Нажмите **New Project** → **Deploy from GitHub repo**
4. Выберите репозиторий `KingAsan/pulse`

### Шаг 3: Настроить переменные окружения

В панели проекта перейдите в **Variables** и добавьте:

#### Обязательные:
```
SECRET_KEY=<ваш-сгенерированный-ключ>
JWT_SECRET_KEY=<ваш-сгенерированный-ключ>
```

#### Для HDRezka (работает на Railway автоматически!):
```
# Не нужно настраивать - HDRezka.ag доступен из США/Европы напрямую
```

#### Опционально:
```
KINOPOISK_API_KEY=<ваш-ключ>
GOOGLE_BOOKS_API_KEY=<ваш-ключ>
GOOGLE_API_KEY=<ваш-ключ для Gemini>
```

#### CORS (обновите после деплоя):
```
CORS_ORIGINS=https://your-app.up.railway.app,http://localhost:5000
```

> 💡 Домен Railway узнаете после первого деплоя (вида `pulse-xxxxx.up.railway.app`)

### Шаг 4: Добавить Persistent Storage (для БД)

1. В проекте нажмите **New** → **Persistent Disk**
2. Name: `pulse-data`
3. Mount Path: `/app/backend`
4. Size: `1GB` (бесплатно)

Это сохранит базу данных между перезапусками.

### Шаг 5: Деплой!

Railway автоматически задеплоит после подключения репозитория.

Или вручную:
```bash
# Установите Railway CLI
npm i -g @railway/cli

# Войдите
railway login

# Деплой
railway up
```

### Шаг 6: Проверить работу

Откройте: `https://your-app.up.railway.app/api/health`

Должно вернуть:
```json
{"status": "ok", "gemini_configured": true}
```

---

## 🎬 HDRezka на Railway

**HDRezka.ag работает на Railway автоматически!** ✅

Серверы Railway находятся в США/Европе, где HDRezka не заблокирован.

После деплоя протестируйте:

```bash
# Замените YOUR_APP на ваш домен Railway
export RAILWAY_URL="https://your-app.up.railway.app"

# Логин
curl -X POST $RAILWAY_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"King","password":"A77052967746a"}'

# Поиск (авторизуйтесь сначала)
curl $RAILWAY_URL/api/hdrezka/search?q=Матрица \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📱 Мобильный доступ

После деплоя приложение доступно с телефона:

### Веб версия
Откройте в браузере телефона: `https://your-app.up.railway.app`

### Добавить на главный экран (PWA)
1. Откройте сайт в Chrome/Safari
2. Нажмите **Share** → **Add to Home Screen**
3. Приложение появится как нативное!

### Настроить мобильное приложение
В мобильном приложении Pulse:
1. Settings → API URL
2. Введите: `https://your-app.up.railway.app`
3. Готово!

---

## 🔧 Troubleshooting

### База данных не сохраняется
Убедитесь что Persistent Disk подключён:
- В панели Railway: **Volumes** → `pulse-data` → Mount: `/app/backend`

### CORS ошибки
Добавьте домен Railway в `CORS_ORIGINS`:
```
CORS_ORIGINS=https://pulse-xxxxx.up.railway.app,http://localhost:5000
```

### HDRezka не работает на Railway
На Railway HDRezka должен работать автоматически. Если нет:
1. Проверьте логи в панели Railway
2. Убедитесь что сервер в США/Европе (Settings → Regions)

### Приложение не запускается
Проверьте логи:
```bash
railway logs
```

---

## 📊 Мониторинг

В панели Railway:
- **Metrics** - CPU, Memory, Network
- **Logs** - логи приложения
- **Deployments** - история деплоев

---

## 💰 Стоимость

Railway даёт **$5 бесплатных кредитов/мес**.

Pulse использует ~$2-3/мес:
- Compute: ~$1.50/мес
- Storage: ~$0.50/мес
- Network: ~$0.50/мес

**Итого: бесплатно!** ✅

---

## 🎉 Готово!

После деплоя вы получите:
- ✅ Рабочий HDRezka (сервер в Европе)
- ✅ Доступ с телефона
- ✅ Постоянное хранение данных
- ✅ Автосохранение между перезапусками
- ✅ Бесплатный хостинг
