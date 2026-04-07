# Cinema Section - AnimeVost Integration

## Обзор

Добавлена новая категория **AnimeVost** в раздел Cinema, которая парсит контент с сайта v12.vost.pw рядом с существующей категорией HDRezka.

## Backend

### Новые файлы

1. **`backend/services/animevost_service.py`** - Сервис для парсинга AnimeVost
   - Поиск аниме
   - Получение деталей
   - Просмотр по категориям
   - Список онгоингов
   - Фильтрация по жанрам

2. **`backend/routes/animevost.py`** - API endpoints для AnimeVost
   - `GET /api/animevost/search?q=` - Поиск аниме
   - `GET /api/animevost/detail?url=` - Детали аниме
   - `GET /api/animevost/browse?page=` - Просмотр последних релизов
   - `GET /api/animevost/ongoing` - Список онгоингов
   - `GET /api/animevost/genres` - Список жанров
   - `GET /api/animevost/genre/<genre_id>?page=` - Просмотр по жанру

3. **`backend/tests/test_animevost.py`** - Тесты для AnimeVost (15 тестов)

### Изменения в существующих файлах

- **`backend/app.py`** - Зарегистрирован blueprint `animevost_bp` на `/api/animevost`

## Frontend

### Новые файлы

1. **`frontend/src/pages/CinemaPage.jsx`** - Страница Cinema с переключением между HDRezka и AnimeVost
   - Переключатель источников (HDRezka / AnimeVost)
   - Поиск по выбранному источнику
   - Фильтрация по категориям/жанрам
   - Модальное окно с деталями контента
   - Доступ только для администраторов

2. **`frontend/src/pages/CinemaPage.css`** - Стили для страницы Cinema

### Изменения в существующих файлах

- **`frontend/src/App.jsx`** - Добавлен route `/cinema` для CinemaPage
- **`frontend/src/components/layout/Navbar.jsx`** - Добавлена ссылка "Cinema" в навигацию

## Функционал

### Для администраторов:

1. **Переключение источников**: HDRezka ↔ AnimeVost
2. **Поиск**: Поиск контента по выбранному источнику
3. **Категории**: 
   - HDRezka: Фильмы, Сериалы, Мультфильмы, Аниме
   - AnimeVost: 27 жанров (Боевые искусства, Комедия, Романтика, и т.д.)
4. **Детали**: Клик по карточке открывает модальное окно с:
   - Постер
   - Название (оригинальное и русское)
   - Год, жанры, рейтинги
   - Описание
   - Ссылка для просмотра на источнике

### Безопасность:

- Все endpoints AnimeVost требуют admin-авторизацию (`@require_admin`)
- Frontend проверяет `user.is_admin` перед отображением контента
- Неавторизованные пользователи видят сообщение "Admin Access Required"

## Тестирование

Запуск тестов:
```bash
cd backend
python -m pytest tests/test_animevost.py -v
```

Результат: **15 passed in 14.30s** ✅

## API Endpoints

### AnimeVost

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/animevost/search?q=` | Поиск аниме | Admin |
| GET | `/api/animevost/detail?url=` | Детали аниме | Admin |
| GET | `/api/animevost/browse?page=` | Последние релизы | Admin |
| GET | `/api/animevost/ongoing` | Онгоинги | Admin |
| GET | `/api/animevost/genres` | Список жанров | Admin |
| GET | `/api/animevost/genre/<genre_id>?page=` | По жанру | Admin |

### HDRezka (существующие)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/hdrezka/search?q=` | Поиск контента | Admin |
| GET | `/api/hdrezka/detail?url=` | Детали контента | Admin |
| GET | `/api/hdrezka/browse?category=&page=` | Просмотр по категории | Admin |
| GET | `/api/hdrezka/categories` | Список категорий | Admin |

## Структура данных

### AnimeVost Search/Browse Response
```json
[
  {
    "id": "3856",
    "title": "Название аниме",
    "url": "https://v12.vost.pw/tip/tv/3856-title.html",
    "image": "https://v12.vost.pw/uploads/posts/...",
    "type": "anime"
  }
]
```

### AnimeVost Detail Response
```json
{
  "anime_id": "3856",
  "title": "Название аниме",
  "url": "https://v12.vost.pw/tip/tv/3856-title.html",
  "poster": "https://v12.vost.pw/uploads/posts/...",
  "description": "Описание...",
  "year": "2025",
  "genres": ["Комедия", "Романтика"],
  "type": "ТВ",
  "episodes": "12",
  "status": "Онгоинг",
  "player_url": "...",
  "source_url": "https://v12.vost.pw/tip/tv/3856-title.html",
  "content_type": "anime"
}
```

## Использование

1. Войдите как администратор
2. Перейдите в раздел **Cinema** в навигации
3. Выберите источник: **HDRezka** или **AnimeVost**
4. Используйте поиск или выберите категорию/жанр
5. Кликните на карточку для просмотра деталей
6. Нажмите "Watch on AnimeVost/HDRezka" для перехода на источник

## Технические детали

- **Парсинг**: BeautifulSoup4 для HTML-парсинга
- **Timeout**: 12 секунд для запросов
- **User-Agent**: Chrome 120.0.0.0
- **Кэширование**: Нет (можно добавить в будущем)
- **Rate Limiting**: Наследуется от admin blueprint (20 req/min)

## Возможные улучшения

1. Добавить кэширование результатов поиска
2. Реализовать встроенный плеер (как в HDRezka)
3. Добавить пагинацию на frontend
4. Интегрировать с системой избранного/watchlist
5. Добавить фильтры по году, статусу
6. Реализовать API AnimeVost (если доступно) вместо парсинга
