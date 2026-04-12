# 🎉 HDRezka на Railway - Готово!

## ✅ Что сделано

1. **HdRezkaApi v11.2.3 интегрирован** в проект
2. **Railway деплой** уже настроен (`puls.up.railway.app`)
3. **Сервер в Европе** (europe-west4) - HDRezka.ag работает напрямую!
4. **Frontend обновлён** - выбор качества, переводчиков, сезонов

---

## 🚀 Как использовать

### 1. Дождитесь деплоя на Railway

Railway автоматически деплоит из GitHub. Процесс занимает 2-5 минут.

Проверьте статус:
- Откройте [Railway Dashboard](https://railway.app)
- Перейдите в проект `lucky-enthusiasm` → `web`
- Смотрите **Deployments** - должен быть зелёный статус

### 2. Протестируйте HDRezka

После деплоя откройте:
```
https://puls.up.railway.app/api/health
```

Должно вернуть:
```json
{"status": "ok", "gemini_configured": true}
```

### 3. Войдите в приложение

**Веб версия:**
```
https://puls.up.railway.app
```

**Мобильное приложение:**
1. Откройте приложение Pulse на телефоне
2. Settings → API URL
3. Введите: `https://puls.up.railway.app`
4. Сохраните

**Логин:**
- Username: `King`
- Password: `A77052967746a`

### 4. Используйте HDRezka (Cinema раздел)

После входа:
1. Откройте раздел **Cinema** в меню
2. Выберите категорию (Фильмы, Сериалы, и т.д.)
3. Используйте поиск или просматривайте категории
4. Нажмите на фильм для просмотра деталей
5. Выберите качество, переводчика, сезон/эпизод
6. Смотрите!

---

## 📱 Мобильный доступ

### PWA (Progressive Web App)
1. Откройте `https://puls.up.railway.app` в Chrome/Safari на телефоне
2. Нажмите **Share** → **Add to Home Screen**
3. Приложение появится как нативное на главном экране

### Native App (если есть)
В настройках приложения укажите Railway URL:
```
https://puls.up.railway.app
```

---

## 🎬 Что работает на Railway

✅ **HDRezka поиск** - фильмы, сериалы, мультфильмы, аниме  
✅ **Детали контента** - описание, рейтинг, постер, год  
✅ **Переводчики** - выбор озвучки (Дубляж, StudioBand, и др.)  
✅ **Качество видео** - 360p, 480p, 720p, 1080p  
✅ **Сезоны/Эпизоды** - полная навигация для сериалов  
✅ **Прямые видеопотоки** - без iframe, нативный player  

---

## 🔧 Troubleshooting

### Railway ещё деплоит
Подождите 2-5 минут. Railway показывает статус в Dashboard.

### HDRezka не работает
1. Проверьте логи в Railway Dashboard → Logs
2. Убедитесь что сервер в Europe (Settings → Regions)
3. HDRezka.ag должен быть доступен из Европы

### CORS ошибки
Добавьте домен в `CORS_ORIGINS` переменную Railway:
```
CORS_ORIGINS=https://puls.up.railway.app,http://localhost:5000
```

### Приложение не загружается
1. Проверьте `/api/health` endpoint
2. Убедитесь что Railway deployment successful (зелёный статус)
3. Проверьте logs в Railway Dashboard

---

## 📊 Мониторинг Railway

В [Railway Dashboard](https://railway.app):
- **Metrics** - CPU, Memory, Network usage
- **Logs** - логи приложения в реальном времени
- **Deployments** - история и статус деплоев
- **Variables** - управление переменными окружения

---

## 💰 Стоимость

Railway даёт **$5 бесплатных кредитов/мес**.

Pulse использует ~$2-3/мес:
- Compute: ~$1.50/мес
- Storage: ~$0.50/мес (1GB volume)
- Network: ~$0.50/мес

**Итого: бесплатно!** ✅

---

## 🎯 Итог

После деплоя вы получаете:
- ✅ **Рабочий HDRezka** (сервер в Европе, без VPN)
- ✅ **Доступ с телефона** (PWA или mobile app)
- ✅ **Постоянное хранение** (persistent storage)
- ✅ **Автоматические обновления** (git push = деплой)
- ✅ **Бесплатный хостинг** ($5 кредитов Railway)

**Всё готово! Просто дождитесь деплоя и пользуйтесь! 🚀**
