"""HDRezkaApi integration service — wraps HdRezkaApi library for Pulse backend."""

import logging
from typing import Optional
from urllib.parse import quote, urlparse
import sys

# CORS прокси для обхода блокировки HDRezka
# Используем наш локальный прокси сервер
LOCAL_PROXY_URL = 'http://localhost:5000/api/proxy/hdrezka'

# Патчим requests для использования нашего локального прокси
import requests
_original_request = requests.Session.request

def _patched_request(self, method, url, *args, **kwargs):
    """Patch requests to route HDRezka through our local proxy."""
    # Don't proxy localhost requests (would cause infinite loop)
    if url and 'hdrezka' in url.lower() and 'localhost' not in url.lower() and '127.0.0.1' not in url.lower():
        # Use our local proxy endpoint
        proxy_url = f'{LOCAL_PROXY_URL}?url={quote(url, safe="")}&method={method}'
        
        # For POST requests, we need to handle body differently
        if method == 'POST':
            # Extract POST data from kwargs
            post_data = kwargs.pop('data', None)
            json_data = kwargs.pop('json', None)
            
            if post_data:
                return _original_request(
                    self, 'POST', proxy_url, 
                    data=post_data, 
                    **kwargs
                )
            elif json_data:
                return _original_request(
                    self, 'POST', proxy_url,
                    json=json_data,
                    **kwargs
                )
        
        return _original_request(self, method, proxy_url, *args, **kwargs)
    return _original_request(self, method, url, *args, **kwargs)

# Применяем monkey patch
requests.Session.request = _patched_request
requests.request = _patched_request

# Теперь импортируем HdRezkaApi (он будет использовать проксированный requests)
from HdRezkaApi import HdRezkaApi, HdRezkaSearch
from HdRezkaApi.errors import FetchFailed, LoginRequiredError, CaptchaError, HTTP

logger = logging.getLogger(__name__)

# Базовый URL HDRezka (можно менять на актуальное зеркало)
HDREZKA_BASE_URL = 'https://hdrezka.ag'

# Маппинг категорий Pulse -> HDRezka URL paths
CATEGORY_MAP = {
    'films': 'films',
    'series': 'series',
    'cartoons': 'cartoons',
    'anime': 'animation',
}


class HdRezkaApiService:
    """Service wrapper над HdRezkaApi для совместимости с Pulse backend.
    
    Все запросы к HDRezka автоматически проходят через CORS прокси
    для обхода региональной блокировки.
    """

    def __init__(self, base_url: str = HDREZKA_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self._search = HdRezkaSearch(self.base_url)

    def _normalize_url(self, url: str) -> str:
        """Убедиться что URL использует правильный базовый домен."""
        if not url:
            return ''
        # Заменить домен на текущий base_url если отличается
        if self.base_url not in url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
            url = f'{self.base_url}{path}'
        return url

    def search(self, query: str, limit: int = 20) -> list:
        """Поиск контента на HDRezka.
        
        Используем GET запрос через страницу поиска вместо POST API
        т.к. CORS прокси лучше работает с GET.

        Returns:
            List[dict]: [{'id', 'title', 'url', 'image', 'type', 'rating'}]
        """
        try:
            # Вместо POST /engine/ajax/search.php используем GET /search/
            # Это работает через наш прокси лучше
            from bs4 import BeautifulSoup
            from HdRezkaApi.types import default_cookies, default_headers
            
            search_url = f'{self.base_url}/search/?do=search&subaction=search&q={quote(query)}'
            
            # Monkey-patched requests уже использует прокси
            r = requests.get(search_url, headers=default_headers, cookies=default_cookies, timeout=20)
            
            if not r.ok:
                return []
            
            soup = BeautifulSoup(r.content, 'html.parser')
            results = []
            
            for item in soup.select('.b-search__section_list li')[:limit]:
                try:
                    title = item.find('span', class_='enty').get_text().strip()
                    url = item.find('a').attrs['href']
                    rating_span = item.find('span', class_='rating')
                    rating = float(rating_span.get_text()) if rating_span else None
                    
                    # Нормализовать URL
                    url = self._normalize_url(url)
                    
                    # Определить тип
                    content_type = 'movie'
                    if '/serialy/' in url:
                        content_type = 'series'
                    elif '/multfilmy/' in url or '/multserial/' in url:
                        content_type = 'cartoon'
                    elif '/animation/' in url:
                        content_type = 'anime'
                    
                    results.append({
                        'id': url.split('/')[-1].split('-')[0] if url else '',
                        'title': title,
                        'url': url,
                        'image': None,  # Fast search не возвращает изображения
                        'type': content_type,
                        'rating': rating,
                    })
                except Exception:
                    continue
            
            return results
        except Exception as e:
            logger.exception('HdRezkaApi search error: q=%s', query)
            return []

    def get_detail(self, url: str) -> Optional[dict]:
        """Получить детальную информацию о фильме/сериале.

        Returns:
            dict: {'title', 'original_title', 'description', 'poster', 'year',
                   'genres', 'country', 'imdb_rating', 'kp_rating', 'quality',
                   'duration', 'translations', 'post_id', 'content_type',
                   'translator_list', 'seasons_info', ...}
        """
        try:
            url = self._normalize_url(url)
            rezka = HdRezkaApi(url)

            if not rezka.ok:
                logger.warning('HdRezkaApi failed to fetch: %s', rezka.exception)
                return None

            # Определить тип контента
            content_type = 'movie'
            type_str = str(rezka.type).split('.')[-1] if rezka.type else ''
            if type_str in ('tv_series', 'series'):
                content_type = 'series'
            elif str(rezka.category).split('.')[-1] == 'cartoon':
                content_type = 'cartoon'
            elif str(rezka.category).split('.')[-1] == 'anime':
                content_type = 'anime'

            # Получить информацию о сезонах для сериалов
            seasons_info = []
            translator_list = []

            if content_type == 'series':
                # Получить информацию о сезонах/эпизодах
                try:
                    episodes_info = rezka.episodesInfo
                    for season_data in episodes_info:
                        season_num = season_data['season']
                        season_text = season_data['season_text']
                        episodes = []
                        for ep in season_data.get('episodes', []):
                            episodes.append({
                                'episode': ep['episode'],
                                'name': ep.get('episode_text', f'Эпизод {ep["episode"]}'),
                                'translations': ep.get('translations', []),
                            })
                        seasons_info.append({
                            'season': season_num,
                            'name': season_text,
                            'episodes': episodes,
                        })
                except Exception as e:
                    logger.warning('Failed to get episodes info: %s', e)

            # Список переводчиков
            for tr_id, tr_data in rezka.translators.items():
                translator_list.append({
                    'id': str(tr_id),
                    'title': tr_data.get('name', ''),
                    'premium': tr_data.get('premium', False),
                })

            # Получить genre/country/year из описания страницы
            # HdRezkaApi не предоставляет это напрямую, парсим из soup
            genres = []
            country = ''
            year = str(rezka.releaseYear) if rezka.releaseYear else None
            quality = ''
            duration = ''

            try:
                # Попробовать извлечь из b-post__info таблицы
                info_table = rezka.soup.find(class_='b-post__info')
                if info_table:
                    for tr in info_table.find_all('tr'):
                        cells = tr.find_all('td')
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True).lower().rstrip(':')
                            value = cells[1].get_text(strip=True)

                            if 'жанр' in label or 'genre' in label:
                                genres = [g.strip() for g in value.split(',') if g.strip()]
                            elif 'страна' in label or 'country' in label:
                                country = value.strip()
                            elif 'качеств' in label or 'quality' in label:
                                quality = value.strip()
                            elif 'время' in label or 'длительност' in label or 'duration' in label:
                                duration = value.strip()
            except Exception as e:
                logger.debug('Failed to parse info table: %s', e)

            result = {
                'url': url,
                'title': rezka.name or '',
                'original_title': rezka.origName or '',
                'description': rezka.description or '',
                'poster': rezka.thumbnailHQ or rezka.thumbnail,
                'year': year,
                'genres': genres,
                'country': country,
                'quality': quality,
                'duration': duration,
                'imdb_rating': rezka.rating.value if rezka.rating.value else None,
                'kp_rating': None,  # HDRezka не всегда предоставляет KP рейтинг
                'content_type': content_type,
                'post_id': str(rezka.id),
                'translator_list': translator_list,
                'seasons_info': seasons_info,
                'source_url': url,
                'player_url': None,  # Стримы получаются через get_streams
            }

            return result
        except Exception as e:
            logger.exception('HdRezkaApi detail error: url=%s', url)
            return None

    def get_seasons(self, url: str) -> list:
        """Получить список сезонов и эпизодов для сериала.

        Returns:
            List[dict]: [{'season', 'name', 'episodes': [{'episode', 'name', 'translations'}]}]
        """
        try:
            url = self._normalize_url(url)
            rezka = HdRezkaApi(url)

            if rezka.type != 'tv_series':
                return []

            result = []
            for season_data in rezka.episodesInfo:
                season_num = season_data['season']
                season_text = season_data['season_text']
                episodes = []
                for ep in season_data.get('episodes', []):
                    episodes.append({
                        'episode': ep['episode'],
                        'name': ep.get('episode_text', f'Эпизод {ep["episode"]}'),
                        'translations': ep.get('translations', []),
                    })
                result.append({
                    'season': season_num,
                    'name': season_text,
                    'episodes': episodes,
                })

            return result
        except Exception as e:
            logger.exception('HdRezkaApi seasons error: url=%s', url)
            return []

    def get_streams(self, url: str, season: str = '', episode: str = '',
                    translator_id: str = '') -> list:
        """Получить прямые ссылки на видеопотоки.

        Args:
            url: URL фильма/сериала
            season: Номер сезона (для сериалов)
            episode: Номер эпизода (для сериалов)
            translator_id: ID переводчика

        Returns:
            List[dict]: [{'voice_id', 'title', 'hls_url', 'has_quality', 'videos': {quality: [urls]}}]
        """
        try:
            url = self._normalize_url(url)
            rezka = HdRezkaApi(url)

            # Если переводчик не указан, использовать первый из приоритетного списка
            if not translator_id:
                translator_id = list(rezka.translators.keys())[0] if rezka.translators else None

            if not translator_id:
                logger.warning('No translators found for: %s', url)
                return []

            stream = None
            if rezka.type == 'tv_series' and season and episode:
                stream = rezka.getStream(season, episode, int(translator_id))
            elif rezka.type == 'movie':
                stream = rezka.getStream(translation=int(translator_id))
            else:
                logger.warning('Invalid stream request: type=%s, season=%s, episode=%s',
                             rezka.type, season, episode)
                return []

            if not stream:
                return []

            # Получить название переводчика
            translator_name = ''
            if translator_id in rezka.translators:
                translator_name = rezka.translators[translator_id]['name']

            # Форматировать видеопотоки
            tracks = []
            videos = stream.videos  # {'360p': [url1, url2], '720p': [...], ...}

            # Создать один трек с всеми качествами
            track = {
                'voice_id': str(translator_id),
                'title': translator_name,
                'has_quality': len(videos) > 1,
                'videos': videos,  # {'360p': [urls], '720p': [urls], ...}
                'subtitles': {},
            }

            # Добавить субтитры если есть
            if stream.subtitles and stream.subtitles.keys:
                for lang_code in stream.subtitles.keys:
                    subtitle_data = stream.subtitles.subtitles.get(lang_code, {})
                    track['subtitles'][lang_code] = {
                        'title': subtitle_data.get('title', lang_code),
                        'link': subtitle_data.get('link', ''),
                    }

            tracks.append(track)
            return tracks
        except Exception as e:
            logger.exception('HdRezkaApi get_streams error: url=%s', url)
            return []

    def browse(self, category: str = 'films', page: int = 1) -> list:
        """Просмотр категории (ограничено через поиск).

        HdRezkaApi не имеет прямого browse API, используем advanced search.
        """
        try:
            # Для browse используем прямой парсинг страницы категории
            from bs4 import BeautifulSoup
            import requests
            from HdRezkaApi.types import default_cookies, default_headers

            category_path = CATEGORY_MAP.get(category, 'films')
            url = f'{self.base_url}/{category_path}/'
            if page > 1:
                url += f'page/{page}/'

            r = requests.get(url, headers=default_headers, cookies=default_cookies, timeout=12)
            if not r.ok:
                return []

            soup = BeautifulSoup(r.content, 'html.parser')
            results = []

            for item in soup.select('.b-content__inline_item'):
                try:
                    link_el = item.select_one('.b-content__inline_item-link a')
                    img_el = item.select_one('.b-content__inline_item-cover img')
                    title_el = item.select_one('.b-content__inline_item-link a')

                    url_item = link_el.get('href', '') if link_el else ''
                    image = img_el.get('src', '') if img_el else ''
                    title = title_el.get_text(strip=True) if title_el else ''

                    # Определить тип
                    cat_el = item.select_one('.cat')
                    content_type = 'movie'
                    if cat_el:
                        classes = cat_el.get('class', [])
                        if 'series' in classes:
                            content_type = 'series'
                        elif 'cartoons' in classes:
                            content_type = 'cartoon'
                        elif 'animation' in classes:
                            content_type = 'anime'

                    results.append({
                        'id': url_item.split('/')[-1].split('-')[0] if url_item else '',
                        'title': title,
                        'url': self._normalize_url(url_item),
                        'image': image,
                        'type': content_type,
                    })
                except Exception:
                    continue

            return results
        except Exception as e:
            logger.exception('HdRezkaApi browse error: cat=%s page=%s', category, page)
            return []

    def get_categories(self) -> list:
        """Список категорий контента."""
        return [
            {'id': 'films', 'name': 'Фильмы', 'url': f'{self.base_url}/films/'},
            {'id': 'series', 'name': 'Сериалы', 'url': f'{self.base_url}/series/'},
            {'id': 'cartoons', 'name': 'Мультфильмы', 'url': f'{self.base_url}/cartoons/'},
            {'id': 'anime', 'name': 'Аниме', 'url': f'{self.base_url}/animation/'},
        ]


# Singleton instance
hdrezka_api_service = HdRezkaApiService()
