"""AI recommendation engine powered by Google Gemini with fallback library and personalization."""

import json
import re
import random
import logging
import httpx
from youtube_search import YoutubeSearch
from config import Config
from database import get_db

logger = logging.getLogger(__name__)

FALLBACK_LIBRARY = {
    "anime": [
        {"title": "Врата Штейна", "year_genre": "2011, научная фантастика, триллер", "category": "Аниме", "description": "Если нужен умный и эмоциональный сюжет, **«Врата Штейна»** отлично сработает. История держит темп и постепенно раскрывает сильные повороты."},
        {"title": "Клинок, рассекающий демонов", "year_genre": "2019, приключения, фэнтези", "category": "Аниме", "description": "Для динамичного вечера подойдет **«Клинок, рассекающий демонов»**: красивый визуал, мощные бои и понятная мотивация героев."},
        {"title": "Охотник x Охотник", "year_genre": "2011, приключения, сёнэн", "category": "Аниме", "description": "**«Охотник x Охотник»** сочетает легкий старт и глубокое развитие мира. Сериал легко смотреть благодаря ярким персонажам и насыщенным аркам."},
        {"title": "Тетрадь смерти", "year_genre": "2006, триллер, детектив", "category": "Аниме", "description": "**«Тетрадь смерти»** — это интеллектуальный поединок двух гениев. Идеально для тех, кто любит **напряжённый сюжет** с неожиданными поворотами."},
        {"title": "Атака титанов", "year_genre": "2013, экшен, драма", "category": "Аниме", "description": "**«Атака титанов»** начинается как эпичный экшен и превращается в глубокую историю о войне и морали. Один из самых **масштабных аниме-сериалов**."},
        {"title": "Ванпанчмен", "year_genre": "2015, комедия, экшен", "category": "Аниме", "description": "**«Ванпанчмен»** — отличная пародия на жанр супергероев. Юмор и **крутая анимация** первого сезона делают его лёгким для просмотра."},
        {"title": "Магическая битва", "year_genre": "2020, экшен, фэнтези", "category": "Аниме", "description": "**«Магическая битва»** предлагает стильные бои и харизматичных персонажей. Один из лучших **современных боевых аниме**."},
        {"title": "Стальной алхимик: Братство", "year_genre": "2009, приключения, фэнтези", "category": "Аниме", "description": "**«Стальной алхимик: Братство»** считается одним из лучших аниме всех времён. Сочетание **глубокого сюжета**, юмора и экшена."},
        {"title": "Ковбой Бибоп", "year_genre": "1998, космос, нуар", "category": "Аниме", "description": "Стильный и атмосферный **«Ковбой Бибоп»** — классика жанра с невероятным **саундтреком** и запоминающимися персонажами."},
        {"title": "Евангелион", "year_genre": "1995, меха, психология", "category": "Аниме", "description": "**«Евангелион»** — культовое аниме, которое сломало шаблоны жанра меха. Глубокий **психологический подтекст** и незабываемый финал."},
        {"title": "Твоё имя", "year_genre": "2016, романтика, фэнтези", "category": "Аниме", "description": "**«Твоё имя»** — красивейший фильм Макото Синкая. Трогательная история с потрясающей **визуальной режиссурой** и музыкой."},
        {"title": "Код Гиасс", "year_genre": "2006, меха, стратегия", "category": "Аниме", "description": "**«Код Гиасс»** — это шахматная партия с мехами. **Харизматичный антигерой** и постоянные повороты сюжета не дают заскучать."},
        {"title": "Mob Psycho 100", "year_genre": "2016, комедия, экшен", "category": "Аниме", "description": "**Mob Psycho 100** от автора «Ванпанчмена» — история о подростке с **невероятной психической силой**. Юмор, экшен и искренние эмоции."},
        {"title": "Обещанный Неверленд", "year_genre": "2019, триллер, мистика", "category": "Аниме", "description": "Первый сезон **«Обещанного Неверленда»** — это чистый **напряжённый триллер**. Умные дети против системы — сюжет держит в тонусе."},
        {"title": "Наруто: Ураганные хроники", "year_genre": "2007, сёнэн, приключения", "category": "Аниме", "description": "**«Наруто: Ураганные хроники»** — это масштабная история взросления с **эпичными боями** и эмоционально сильными арками."},
    ],
    "movie": [
        {"title": "Бегущий по лезвию 2049", "year_genre": "2017, фантастика, драма", "category": "Фильм", "description": "**«Бегущий по лезвию 2049»** дает сильный визуальный опыт и взрослую историю. Отличный вариант для **вдумчивого просмотра**."},
        {"title": "Начало", "year_genre": "2010, фантастика, триллер", "category": "Фильм", "description": "**«Начало»** — интеллектуальный экшен с мощной идеей. Картина держит темп и работает для **соло-просмотра** и обсуждения."},
        {"title": "Достать ножи", "year_genre": "2019, детектив, комедия", "category": "Фильм", "description": "**«Достать ножи»** — стильный детектив с **харизматичными персонажами** и понятной динамикой сюжета."},
        {"title": "Интерстеллар", "year_genre": "2014, фантастика, драма", "category": "Фильм", "description": "**«Интерстеллар»** — масштабное космическое путешествие с глубоким **эмоциональным ядром**. Идеальный фильм для большого экрана."},
        {"title": "Паразиты", "year_genre": "2019, триллер, драма", "category": "Фильм", "description": "**«Паразиты»** Пон Джун-хо — это мастерский микс жанров. **Социальная сатира** и саспенс, который не отпускает до конца."},
        {"title": "Побег из Шоушенка", "year_genre": "1994, драма", "category": "Фильм", "description": "**«Побег из Шоушенка»** — вечная классика о надежде и **силе человеческого духа**. Фильм, который стоит пересматривать."},
        {"title": "Тёмный рыцарь", "year_genre": "2008, экшен, триллер", "category": "Фильм", "description": "**«Тёмный рыцарь»** Нолана — лучший фильм о Бэтмене. **Джокер Хита Леджера** превратил супергеройский фильм в настоящий триллер."},
        {"title": "Матрица", "year_genre": "1999, фантастика, экшен", "category": "Фильм", "description": "**«Матрица»** изменила кинематограф. **Революционные спецэффекты** и философские вопросы о реальности актуальны до сих пор."},
        {"title": "Одержимость", "year_genre": "2014, драма, музыка", "category": "Фильм", "description": "**«Одержимость»** — мощная история о стремлении к совершенству. **Джей Кей Симмонс** в роли безжалостного преподавателя — настоящий мастер-класс."},
        {"title": "Дюна", "year_genre": "2021, фантастика, эпик", "category": "Фильм", "description": "**«Дюна»** Вильнёва — эпическая экранизация великого романа. **Потрясающий визуал** и масштабный мир, который затягивает."},
        {"title": "Всё везде и сразу", "year_genre": "2022, фантастика, драма", "category": "Фильм", "description": "**«Всё везде и сразу»** — это безумный мультивселенский экшен с глубоким **семейным посланием**. Смешной, трогательный и оригинальный."},
        {"title": "Бойцовский клуб", "year_genre": "1999, триллер, драма", "category": "Фильм", "description": "**«Бойцовский клуб»** — культовый фильм Финчера с **незабываемым поворотом** сюжета. Провокационный и стильный."},
        {"title": "Джанго освобождённый", "year_genre": "2012, вестерн, драма", "category": "Фильм", "description": "**«Джанго освобождённый»** Тарантино — брутальный вестерн с **блестящими диалогами** и харизматичными персонажами."},
        {"title": "Остров проклятых", "year_genre": "2010, триллер, детектив", "category": "Фильм", "description": "**«Остров проклятых»** Скорсезе — атмосферный **психологический триллер** с Ди Каприо. Фильм, который хочется пересмотреть после финала."},
        {"title": "Гран Торино", "year_genre": "2008, драма", "category": "Фильм", "description": "**«Гран Торино»** — сильная драма с **Клинтом Иствудом** о предрассудках и искуплении. Простая история с мощным финалом."},
    ],
    "series": [
        {"title": "Черное зеркало", "year_genre": "2011, антология, sci-fi", "category": "Сериал", "description": "**«Черное зеркало»** удобно смотреть по эпизодам. Каждая серия — отдельная **завершенная история** с сильным послевкусием."},
        {"title": "Аркейн", "year_genre": "2021, анимация, фэнтези", "category": "Сериал", "description": "**«Аркейн»** — визуально сильный и эмоциональный. Подойдет для **вечернего просмотра** в одиночку и в компании."},
        {"title": "Очень странные дела", "year_genre": "2016, приключения, мистика", "category": "Сериал", "description": "**«Очень странные дела»** — отличный выбор для **дружеского просмотра**. Ностальгический вайб и быстрый сюжет."},
        {"title": "Во все тяжкие", "year_genre": "2008, криминал, драма", "category": "Сериал", "description": "**«Во все тяжкие»** — один из лучших сериалов в истории. Трансформация **Уолтера Уайта** от учителя до наркобарона — мастерский сторителлинг."},
        {"title": "Игра престолов", "year_genre": "2011, фэнтези, драма", "category": "Сериал", "description": "**«Игра престолов»** — эпическое фэнтези с **непредсказуемым сюжетом** и запоминающимися персонажами. Первые сезоны — настоящий шедевр."},
        {"title": "Настоящий детектив", "year_genre": "2014, детектив, триллер", "category": "Сериал", "description": "Первый сезон **«Настоящего детектива»** — это **шедевр атмосферы**. Макконахи и Харрельсон в лучших ролях."},
        {"title": "Мистер Робот", "year_genre": "2015, триллер, драма", "category": "Сериал", "description": "**«Мистер Робот»** — умный **хакерский триллер** с неожиданными поворотами. Технически достоверный и стильно снятый."},
        {"title": "Чернобыль", "year_genre": "2019, историческая драма", "category": "Сериал", "description": "**«Чернобыль»** HBO — пугающе реалистичная история катастрофы. **Невероятная атмосфера** и сильнейшая актёрская игра."},
        {"title": "Сёгун", "year_genre": "2024, историческая драма", "category": "Сериал", "description": "**«Сёгун»** — масштабная историческая драма о **феодальной Японии**. Красивейшая картинка и интриги на каждом шагу."},
        {"title": "Тед Лассо", "year_genre": "2020, комедия, драма", "category": "Сериал", "description": "**«Тед Лассо»** — невероятно добрый и **жизнеутверждающий сериал**. Идеально, когда хочется улыбнуться и зарядиться позитивом."},
        {"title": "Белый лотос", "year_genre": "2021, сатира, драма", "category": "Сериал", "description": "**«Белый лотос»** — остроумная **социальная сатира** в курортном антураже. Каждый сезон — новая история и новые герои."},
        {"title": "Выживание Медведя", "year_genre": "2022, драма, кулинария", "category": "Сериал", "description": "**«Выживание» (The Bear)** — напряжённая драма о ресторанной кухне. **Мощная энергетика** и реалистичные персонажи."},
        {"title": "Тьма", "year_genre": "2017, фантастика, триллер", "category": "Сериал", "description": "**«Тьма»** — немецкий сай-фай триллер о **путешествиях во времени**. Сложный, но невероятно продуманный сюжет."},
        {"title": "Мандалорец", "year_genre": "2019, фантастика, приключения", "category": "Сериал", "description": "**«Мандалорец»** — лучший сериал во вселенной **Звёздных войн**. Стильный вестерн в космосе с харизматичным героем."},
        {"title": "Пацаны", "year_genre": "2019, экшен, сатира", "category": "Сериал", "description": "**«Пацаны»** — жёсткая деконструкция **супергеройского жанра**. Чёрный юмор, провокации и мощный сюжет."},
    ],
    "game": [
        {"title": "It Takes Two", "year_genre": "2021, кооператив, приключения", "category": "Игра", "description": "**It Takes Two** — построена на **взаимодействии** и постоянно предлагает новые механики. Отличный вариант для пары или друзей."},
        {"title": "Hades", "year_genre": "2020, roguelike, экшен", "category": "Игра", "description": "**Hades** — динамичный геймплей **короткими сессиями** с ощущением прогресса. Легко запускается «на 30 минут»."},
        {"title": "Stardew Valley", "year_genre": "2016, симулятор, инди", "category": "Игра", "description": "**Stardew Valley** — **расслабляющий опыт** без давления. Отлично работает после напряженного дня."},
        {"title": "The Witcher 3: Wild Hunt", "year_genre": "2015, RPG, фэнтези", "category": "Игра", "description": "**«Ведьмак 3»** — одна из лучших RPG в истории. **Захватывающий открытый мир** и сильнейший нарратив."},
        {"title": "Red Dead Redemption 2", "year_genre": "2018, экшен, приключения", "category": "Игра", "description": "**RDR2** — это не просто игра, а **кинематографический опыт**. Лучшая история в жанре вестерна в играх."},
        {"title": "Hollow Knight", "year_genre": "2017, метроидвания, инди", "category": "Игра", "description": "**Hollow Knight** — огромный мир, **атмосферная музыка** и хардкорные босс-файты. Один из лучших инди-проектов."},
        {"title": "Baldur's Gate 3", "year_genre": "2023, RPG, фэнтези", "category": "Игра", "description": "**Baldur's Gate 3** — новый стандарт для **ролевых игр**. Свобода выбора, которая действительно влияет на историю."},
        {"title": "Celeste", "year_genre": "2018, платформер, инди", "category": "Игра", "description": "**Celeste** — сложный платформер с трогательной историей о **борьбе с тревожностью**. Простой в освоении, тяжёлый для мастерства."},
        {"title": "God of War: Ragnarök", "year_genre": "2022, экшен, приключения", "category": "Игра", "description": "**God of War: Ragnarök** — эпичный финал скандинавской саги. **Мощный экшен** и эмоциональная история отца и сына."},
        {"title": "Disco Elysium", "year_genre": "2019, RPG, детектив", "category": "Игра", "description": "**Disco Elysium** — уникальная **текстовая RPG** с невероятной глубиной диалогов. Для тех, кто ценит нарратив выше экшена."},
        {"title": "Elden Ring", "year_genre": "2022, RPG, экшен", "category": "Игра", "description": "**Elden Ring** — масштабный **открытый мир** от создателей Dark Souls при участии Джорджа Мартина. Хардкорно и красиво."},
        {"title": "Portal 2", "year_genre": "2011, головоломка", "category": "Игра", "description": "**Portal 2** — гениальные головоломки и **лучший юмор** в игровой индустрии. Кооператив тоже великолепен."},
        {"title": "Undertale", "year_genre": "2015, RPG, инди", "category": "Игра", "description": "**Undertale** — уникальная RPG, где можно **пройти без единого убийства**. Юмор, 4-я стена и незабываемые персонажи."},
        {"title": "Outer Wilds", "year_genre": "2019, приключения, исследование", "category": "Игра", "description": "**Outer Wilds** — одна из лучших **игр-исследований** с петлёй времени. Каждое открытие меняет понимание мира."},
        {"title": "Cyberpunk 2077", "year_genre": "2020, RPG, киберпанк", "category": "Игра", "description": "После патчей **Cyberpunk 2077** стал тем, чем должен был быть. **Невероятный Найт-Сити** и сильная история."},
    ],
    "music": [
        {"title": "Lo-fi Beats Mix", "year_genre": "lo-fi, instrumental", "category": "Музыка", "description": "**Lo-fi Beats Mix** — ровный ритм без резких переходов для **удержания концентрации** во время работы."},
        {"title": "Synthwave Drive", "year_genre": "synthwave, electronic", "category": "Музыка", "description": "**Synthwave Drive** — энергичный, но не перегруженный звук для **вечерней работы** или поездок."},
        {"title": "Neo-Classical Focus", "year_genre": "neoclassical, ambient", "category": "Музыка", "description": "**Neo-Classical Focus** — эмоциональная глубина и **спокойное продуктивное** состояние без отвлечений."},
        {"title": "Hans Zimmer Essentials", "year_genre": "soundtrack, orchestral", "category": "Музыка", "description": "**Hans Zimmer** — грандиозные саундтреки от мастера кино-музыки. **Эпичные оркестровки** для вдохновения."},
        {"title": "Radiohead — OK Computer", "year_genre": "1997, alt-rock", "category": "Музыка", "description": "**OK Computer** — знаковый альбом **Radiohead**. Пророческий взгляд на технологии, актуальный как никогда."},
        {"title": "Daft Punk — Discovery", "year_genre": "2001, electronic, house", "category": "Музыка", "description": "**Discovery** от Daft Punk — классика электронной музыки. **Танцевальные хиты** и ностальгический французский хаус."},
        {"title": "Ludovico Einaudi — Underwater", "year_genre": "2022, neoclassical, piano", "category": "Музыка", "description": "**Einaudi** создает **пространство для размышлений**. Минималистичное фортепиано, которое успокаивает и фокусирует."},
        {"title": "Arctic Monkeys — AM", "year_genre": "2013, indie rock", "category": "Музыка", "description": "**AM** — мрачный инди-рок с **риффами, которые не выходят из головы**. Стильный и дерзкий альбом."},
        {"title": "Кино — Группа крови", "year_genre": "1988, русский рок", "category": "Музыка", "description": "**«Группа крови»** — легенда **русского рока**. Цой остаётся актуальным и сегодня. Мощная энергия и вечные тексты."},
        {"title": "Nujabes — Modal Soul", "year_genre": "2005, jazzhop, instrumental", "category": "Музыка", "description": "**Modal Soul** от Nujabes — атмосферный **джаз-хоп** для спокойного вечера. Идеально сочетает джаз и хип-хоп биты."},
        {"title": "Tame Impala — Currents", "year_genre": "2015, psychedelic pop", "category": "Музыка", "description": "**Currents** — **психоделический поп** с глубоким звучанием. Каждый трек — отдельное звуковое путешествие."},
        {"title": "Interstellar OST", "year_genre": "2014, soundtrack, ambient", "category": "Музыка", "description": "Саундтрек **«Интерстеллара»** — это **космическая эмоция** в чистом виде. Орган Циммера пробирает до мурашек."},
    ],
}

MODE_HINTS = {
    "balanced": "Give a balanced mix of safe and fresh recommendations.",
    "fast": "Favor instant picks: recognizable titles and quick-start options.",
    "deep": "Provide thoughtful picks with one hidden gem and richer reasoning.",
    "surprise": "Prioritize unusual, bold, and less obvious options.",
}


def normalize_title(value):
    lowered = str(value or "").lower().strip()
    cleaned = re.sub(r"[^\wа-яё]+", " ", lowered, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def detect_bucket(query):
    q = query.lower()
    if any(k in q for k in ["аниме", "isekai", "исекай"]):
        return "anime"
    if any(k in q for k in ["игр", "game", "steam", "ps5", "xbox"]):
        return "game"
    if any(k in q for k in ["музык", "music", "трек", "playlist"]):
        return "music"
    if any(k in q for k in ["сериал", "series", "show"]):
        return "series"
    return "movie"


def find_trailer(title, category=""):
    try:
        search_q = f"{title} trailer"
        if category and ("музыка" in category.lower() or "music" in category.lower()):
            search_q = f"{title} official video"
        results = YoutubeSearch(search_q, max_results=1).to_dict()
        return results[0]["id"] if results else None
    except Exception:
        return None


def normalize_recommendations(raw_text):
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("[")
        end = raw_text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return []
        try:
            parsed = json.loads(raw_text[start:end + 1])
        except Exception:
            return []

    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return []

    normalized = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "title": str(item.get("title") or item.get("name") or "Без названия").strip(),
            "year_genre": str(item.get("year_genre") or item.get("yearGenre") or "").strip(),
            "description": str(item.get("description") or item.get("desc") or "Подбор по запросу.").strip(),
            "category": str(item.get("category") or "").strip(),
            "why_this": str(item.get("why_this") or item.get("why") or "Подходит по запросу.").strip(),
        })
    return normalized[:12]


def collect_recent_titles(user_id, limit=60):
    db = get_db()
    try:
        rows = db.execute(
            'SELECT ai_response_json FROM ai_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()
        titles = []
        seen = set()
        for row in rows:
            if not row['ai_response_json']:
                continue
            try:
                payload = json.loads(row['ai_response_json'])
            except Exception:
                continue
            if isinstance(payload, dict):
                payload = [payload]
            if not isinstance(payload, list):
                continue
            for item in payload:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or "").strip()
                key = normalize_title(title)
                if not key or key in seen:
                    continue
                seen.add(key)
                titles.append(title)
                if len(titles) >= limit:
                    return titles
        return titles
    finally:
        db.close()


def collect_feedback_summary(user_id, limit=300):
    db = get_db()
    try:
        rows = db.execute(
            'SELECT title, category, feedback_type FROM ai_feedback WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()
        liked = set()
        disliked = set()
        watched = set()
        pref_cats = {}
        avoid_cats = {}
        for row in rows:
            t = normalize_title(row['title'])
            c = normalize_title(row['category'] or "")
            ft = (row['feedback_type'] or "").lower().strip()
            if ft == "like":
                liked.add(t)
                if c:
                    pref_cats[c] = pref_cats.get(c, 0) + 1
            elif ft == "dislike":
                disliked.add(t)
                if c:
                    avoid_cats[c] = avoid_cats.get(c, 0) + 1
            elif ft == "watched":
                watched.add(t)
        return {
            "liked_titles": liked,
            "disliked_titles": disliked,
            "watched_titles": watched,
            "preferred_categories": sorted(pref_cats, key=pref_cats.get, reverse=True)[:4],
            "avoid_categories": sorted(avoid_cats, key=avoid_cats.get, reverse=True)[:4],
        }
    finally:
        db.close()


def build_personalization(query, mood, company, time_minutes, assistant_mode, prefs_dict, recent_titles, feedback):
    mode = (assistant_mode or prefs_dict.get('discovery_mode') or 'balanced').lower()
    hint = MODE_HINTS.get(mode, MODE_HINTS['balanced'])
    parts = [
        f"User query: {query}",
        f"Assistant mode: {mode}. {hint}",
        f"Preferred language: {prefs_dict.get('preferred_language', 'ru')}",
        f"Allowed age rating: {prefs_dict.get('age_rating', 'any')}",
    ]
    if prefs_dict.get('favorite_categories'):
        parts.append(f"Favorite categories: {', '.join(prefs_dict['favorite_categories'])}")
    if prefs_dict.get('disliked_categories'):
        parts.append(f"Avoid categories: {', '.join(prefs_dict['disliked_categories'])}")
    if mood:
        parts.append(f"Current mood: {mood}")
    if company:
        parts.append(f"Company: {company}")
    if time_minutes and time_minutes > 0:
        parts.append(f"Available time: ~{time_minutes} minutes")
    if recent_titles:
        parts.append(f"Avoid repeating: {', '.join(recent_titles[:12])}")
    if feedback.get('preferred_categories'):
        parts.append(f"Feedback preferred: {', '.join(feedback['preferred_categories'])}")
    return "\n".join(parts)


def select_best(candidates, recent_titles, feedback, limit=3):
    if not candidates:
        return []
    recent_norm = {normalize_title(t) for t in recent_titles}
    disliked = set(feedback.get("disliked_titles") or [])
    watched = set(feedback.get("watched_titles") or [])
    preferred = set(feedback.get("preferred_categories") or [])
    avoid = set(feedback.get("avoid_categories") or [])

    unique = []
    seen_titles = set()
    for idx, item in enumerate(candidates):
        tn = normalize_title(item.get("title", ""))
        if not tn or tn in seen_titles:
            continue
        seen_titles.add(tn)
        copy = dict(item)
        copy["_tn"] = tn
        copy["_cn"] = normalize_title(item.get("category", ""))
        copy["_idx"] = idx
        unique.append(copy)

    def score(item):
        pts = 0
        if item["_tn"] not in recent_norm:
            pts += 5
        else:
            pts -= 2
        if item["_tn"] in disliked:
            pts -= 100
        if item["_tn"] in watched:
            pts -= 100
        if item["_cn"] in preferred:
            pts += 4
        if item["_cn"] in avoid:
            pts -= 10
        return pts

    ranked = sorted(unique, key=lambda x: (score(x), -x["_idx"]), reverse=True)

    selected = []
    used_cats = set()
    used_titles = set()

    # Pass 1: diverse categories, skip recent/disliked/watched
    for item in ranked:
        if len(selected) >= limit:
            break
        if item["_tn"] in used_titles or item["_tn"] in recent_norm:
            continue
        if item["_tn"] in disliked or item["_tn"] in watched:
            continue
        cat = item["_cn"]
        if cat and cat in used_cats:
            continue
        selected.append(item)
        used_titles.add(item["_tn"])
        if cat:
            used_cats.add(cat)

    # Pass 2: allow same category
    for item in ranked:
        if len(selected) >= limit:
            break
        if item["_tn"] in used_titles or item["_tn"] in disliked or item["_tn"] in watched:
            continue
        selected.append(item)
        used_titles.add(item["_tn"])

    # Pass 3: fill any remaining
    for item in ranked:
        if len(selected) >= limit:
            break
        if item["_tn"] in used_titles:
            continue
        selected.append(item)
        used_titles.add(item["_tn"])

    return [{k: v for k, v in item.items() if not k.startswith("_")} for item in selected[:limit]]


def build_why_this(item, mood=None, company=None, time_minutes=None, prefs=None):
    existing = str(item.get("why_this") or "").strip()
    if existing:
        return existing
    reasons = []
    if mood:
        reasons.append(f"совпадает с настроением «{mood}»")
    if company:
        reasons.append(f"учитывает формат просмотра «{company}»")
    if time_minutes and int(time_minutes) > 0:
        reasons.append(f"подходит под доступное время около {time_minutes} минут")
    if prefs and item.get("category") and prefs.get("favorite_categories"):
        reasons.append("соответствует вашим любимым категориям")
    if not reasons:
        reasons.append("соответствует вашему текущему запросу")
    return "Подходит потому что " + ", ".join(reasons[:3]) + "."


def build_fallback(query, recent_titles, feedback, limit=3):
    bucket = detect_bucket(query)
    pool = list(FALLBACK_LIBRARY.get(bucket, FALLBACK_LIBRARY["movie"]))
    # Mix in a couple from other categories for diversity
    other_keys = [k for k in FALLBACK_LIBRARY if k != bucket]
    for k in other_keys:
        pool.extend(random.sample(FALLBACK_LIBRARY[k], min(2, len(FALLBACK_LIBRARY[k]))))
    random.shuffle(pool)
    recent_norm = {normalize_title(t) for t in recent_titles}
    disliked = set(feedback.get("disliked_titles") or [])
    watched = set(feedback.get("watched_titles") or [])
    selected = []
    seen = set()
    for item in pool:
        tn = normalize_title(item.get("title", ""))
        if not tn or tn in seen or tn in disliked or tn in watched:
            continue
        if tn in recent_norm:
            continue
        selected.append(dict(item))
        seen.add(tn)
        if len(selected) >= limit:
            break
    # If still not enough, relax recent filter
    if len(selected) < limit:
        for item in pool:
            tn = normalize_title(item.get("title", ""))
            if not tn or tn in seen or tn in disliked or tn in watched:
                continue
            selected.append(dict(item))
            seen.add(tn)
            if len(selected) >= limit:
                break
    return selected[:limit]


def get_admin_rules():
    db = get_db()
    try:
        rows = db.execute('SELECT title, category, rule_type FROM admin_content_rules').fetchall()
        result = {"black_titles": set(), "black_categories": set()}
        for row in rows:
            if (row['rule_type'] or '').lower() == 'blacklist':
                t = normalize_title(row['title'] or '')
                c = normalize_title(row['category'] or '')
                if t:
                    result["black_titles"].add(t)
                if c:
                    result["black_categories"].add(c)
        return result
    finally:
        db.close()


def apply_rules(items, rules):
    return [
        item for item in items
        if normalize_title(item.get("title", "")) not in rules["black_titles"]
        and normalize_title(item.get("category", "")) not in rules["black_categories"]
    ]


def inject_pinned(query, recommendations, limit=3):
    db = get_db()
    try:
        rows = db.execute(
            'SELECT * FROM admin_pinned WHERE is_active = 1 ORDER BY created_at DESC'
        ).fetchall()
        if not rows:
            return recommendations[:limit]
        selected = list(recommendations)
        seen = {normalize_title(i.get("title", "")) for i in selected}
        for row in rows:
            tn = normalize_title(row['title'] or '')
            if not tn or tn in seen:
                continue
            selected.insert(0, {
                "title": row['title'],
                "year_genre": row['year_genre'] or "",
                "description": row['description'],
                "category": row['category'] or "",
                "why_this": row['why_this'] or "Рекомендация от администратора.",
                "video_id": row['video_id'],
            })
            seen.add(tn)
            if len(selected) >= limit:
                break
        return selected[:limit]
    finally:
        db.close()


def get_ai_prefs(user_id):
    db = get_db()
    try:
        row = db.execute('SELECT * FROM ai_preferences WHERE user_id = ?', (user_id,)).fetchone()
        if row:
            return {
                "favorite_categories": [c.strip() for c in (row['favorite_categories'] or '').split(',') if c.strip()],
                "disliked_categories": [c.strip() for c in (row['disliked_categories'] or '').split(',') if c.strip()],
                "favorite_platforms": [c.strip() for c in (row['favorite_platforms'] or '').split(',') if c.strip()],
                "preferred_language": row['preferred_language'] or 'ru',
                "age_rating": row['age_rating'] or 'any',
                "discovery_mode": row['discovery_mode'] or 'balanced',
                "onboarding_completed": bool(row['onboarding_completed']),
            }
        return {
            "favorite_categories": [], "disliked_categories": [], "favorite_platforms": [],
            "preferred_language": "ru", "age_rating": "any", "discovery_mode": "balanced",
            "onboarding_completed": False,
        }
    finally:
        db.close()


async def request_gemini(system_instruction, force_lite=False):
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")

    primary = Config.GEMINI_PRIMARY_MODEL
    fallback = Config.GEMINI_FALLBACK_MODEL
    chain = [fallback, primary] if force_lite else [primary, fallback]

    payload = {
        "contents": [{"parts": [{"text": system_instruction}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }

    last_error = None
    async with httpx.AsyncClient() as client:
        for model in chain:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            for attempt in range(3):
                try:
                    resp = await client.post(url, json=payload, timeout=45.0)
                    if resp.status_code != 200:
                        raise RuntimeError(f"{model} status {resp.status_code}")
                    data = resp.json()
                    raw = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = normalize_recommendations(raw)
                    if parsed:
                        return parsed, model
                except Exception as e:
                    last_error = e
                    if attempt < 2:
                        import asyncio
                        await asyncio.sleep(1.1 * (2 ** attempt))
    raise RuntimeError(str(last_error) if last_error else "All models failed")


async def get_recommendation(user_id, query, session_id, mood=None, company=None,
                              time_minutes=None, assistant_mode="balanced", temporary=False):
    if not query.strip():
        return {"recommendations": "Введите запрос для получения рекомендаций.", "is_json": False}

    # Check daily limit
    if not temporary:
        db = get_db()
        try:
            setting = db.execute("SELECT value FROM admin_settings WHERE key = 'default_daily_limit'").fetchone()
            daily_limit = int(setting['value']) if setting else Config.DEFAULT_DAILY_LIMIT
            user = db.execute("SELECT daily_limit FROM users WHERE id = ?", (user_id,)).fetchone()
            if user and user['daily_limit']:
                daily_limit = user['daily_limit']
            today_count = db.execute(
                "SELECT COUNT(*) as c FROM ai_history WHERE user_id = ? AND date(timestamp) = date('now')",
                (user_id,)
            ).fetchone()['c']
            if today_count >= daily_limit:
                return {
                    "recommendations": f"Достигнут дневной лимит ({daily_limit}). Попробуй позже.",
                    "is_json": False,
                }
        finally:
            db.close()

    prefs = get_ai_prefs(user_id)
    recent = collect_recent_titles(user_id)
    feedback = collect_feedback_summary(user_id)
    rules = get_admin_rules()

    # Check force lite mode
    db = get_db()
    try:
        lite_row = db.execute("SELECT value FROM admin_settings WHERE key = 'force_lite_mode'").fetchone()
        force_lite = lite_row and lite_row['value'] in ('1', 'true')
    finally:
        db.close()

    context = build_personalization(query, mood, company, time_minutes, assistant_mode, prefs, recent, feedback)

    system_instruction = (
        "You are a personal entertainment assistant.\n"
        "You provide personalized recommendations for movies, series, games, music and anime.\n"
        "Use the following personalization context:\n"
        f"{context}\n\n"
        "Rules:\n"
        "1) Return exactly 6 candidate recommendations in JSON array.\n"
        "2) Each recommendation must include: title, year_genre, description, category, why_this.\n"
        "3) Description should be 2-4 sentences in Markdown with strong personalization.\n"
        "4) In every description, highlight at least 2 key terms/entities using **bold**.\n"
        "5) why_this must be 1 concise sentence: why it fits this user now.\n"
        "6) Avoid recent repeated titles and disliked signals from context.\n"
        "7) If query asks a specific category, prioritize it.\n"
        "8) Return STRICT JSON array only. No prose outside JSON.\n"
        "9) Never ask the user to уточнить/clarify before giving results; if the query is broad, make reasonable assumptions and still return candidates.\n"
        "Output format example:\n"
        '[{"title":"...","year_genre":"...","description":"...","category":"...","why_this":"..."}]'
    )

    source = "llm"
    candidates = []
    model_used = ""
    try:
        candidates, model_used = await request_gemini(system_instruction, force_lite)
        source = f"llm:{model_used}"
    except Exception:
        source = "fallback"

    selected = select_best(candidates, recent, feedback, limit=3)
    selected = apply_rules(selected, rules)

    if len(selected) < 3:
        source = "fallback"
        fb = build_fallback(query, recent, feedback, limit=3)
        fb = apply_rules(fb, rules)
        merged = []
        seen = set()
        for item in selected + fb:
            k = normalize_title(item.get("title", ""))
            if k in seen:
                continue
            merged.append(item)
            seen.add(k)
            if len(merged) >= 3:
                break
        selected = merged

    selected = inject_pinned(query, selected, limit=3)

    # Build why_this and find trailers
    for item in selected:
        item["why_this"] = build_why_this(item, mood, company, time_minutes, prefs)
        if not item.get("video_id"):
            item["video_id"] = find_trailer(item.get("title", ""), item.get("category", ""))

    if not selected:
        return {"recommendations": "Не удалось подобрать варианты. Попробуй другой запрос.", "is_json": False}

    # Save to history
    if not temporary:
        db = get_db()
        try:
            db.execute(
                'INSERT INTO ai_history (user_id, session_id, user_query, ai_response, ai_response_json) VALUES (?, ?, ?, ?, ?)',
                (user_id, session_id, query,
                 "\n\n".join(f"**{i['title']}**\n{i['description']}" for i in selected),
                 json.dumps(selected, ensure_ascii=False))
            )
            db.execute(
                'INSERT INTO api_usage (user_id, endpoint, model_name, status_code, source, query_text) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, '/recommend', model_used or None, 200, source, query)
            )
            db.commit()
        finally:
            db.close()

    return {"recommendations": selected, "is_json": True, "source": source}
