"""AniLibria scraper service — parses HTML from anilibria.top."""

import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_URL = 'https://anilibria.top'
CACHE_TTL = 300  # 5 minutes


class AnilibriaScraper:
    """Scraper for AniLibria website."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Referer': 'https://anilibria.top/'
        })
        self._cache = {}

    def _get_cached(self, key, url):
        """Get page with TTL cache."""
        now = datetime.now()
        if key in self._cache:
            data, expiry = self._cache[key]
            if now < expiry:
                return data

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            self._cache[key] = (resp.text, now + timedelta(seconds=CACHE_TTL))
            return resp.text
        except requests.RequestException as e:
            logger.error('AniLibria scraper error: %s', e)
            return None

    def _parse_release_card(self, card):
        """Parse a single release card from catalog."""
        try:
            title_el = card.select_one('.release-card__title, .card-title, h3')
            title = title_el.text.strip() if title_el else 'Unknown'

            link_el = card.select_one('a[href*="/release/"]')
            code = ''
            if link_el:
                href = link_el.get('href', '')
                code = href.split('/release/')[-1].strip('/')

            poster_el = card.select_one('img')
            poster = ''
            if poster_el:
                poster = poster_el.get('src', poster_el.get('data-src', ''))
                if poster.startswith('/'):
                    poster = BASE_URL + poster

            # Meta info
            meta_text = card.text
            year_match = re.search(r'\b(20\d{2})\b', meta_text)
            year = int(year_match.group(1)) if year_match else 2024

            genres = []
            genre_els = card.select('.tag, .genre-tag, .label')
            for g in genre_els[:3]:
                genres.append(g.text.strip())

            return {
                'id': code or title,
                'code': code,
                'title': title,
                'title_en': '',
                'title_jp': '',
                'type': 'TV',
                'status': 'ongoing',
                'year': year,
                'season': '',
                'genres': genres,
                'description': '',
                'rating': 0,
                'age_rating': '16+',
                'episodes_count': 0,
                'episodes': [],
                'poster': poster,
                'player': {'streams': {}, 'list': []},
                'torrent': None,
            }
        except Exception as e:
            logger.warning('Failed to parse card: %s', e)
            return None

    def search(self, query, page=1, limit=20):
        """Search anime by title."""
        if not query:
            return self.browse(page=page, limit=limit)

        html = self._get_cached(
            f'search_{query}_{page}',
            f'{BASE_URL}/releases?search={requests.utils.quote(query)}&page={page}'
        )

        if not html:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('.release-card, .card, .anime-card')[:limit]
            results = [self._parse_release_card(c) for c in cards]
            return [r for r in results if r]
        except Exception as e:
            logger.error('Search parse error: %s', e)
            return []

    def browse(self, page=1, limit=20):
        """Browse latest releases."""
        html = self._get_cached(
            f'browse_{page}',
            f'{BASE_URL}/releases?page={page}'
        )

        if not html:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('.release-card, .card, .anime-card')[:limit]
            results = [self._parse_release_card(c) for c in cards]
            return [r for r in results if r]
        except Exception as e:
            logger.error('Browse parse error: %s', e)
            return []

    def get_ongoing(self, page=1, limit=20):
        """Get ongoing releases."""
        html = self._get_cached(
            f'ongoing_{page}',
            f'{BASE_URL}/releases?status=ongoing&page={page}'
        )

        if not html:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('.release-card, .card, .anime-card')[:limit]
            results = [self._parse_release_card(c) for c in cards]
            return [r for r in results if r]
        except Exception as e:
            logger.error('Ongoing parse error: %s', e)
            return []

    def get_detail(self, code_or_id):
        """Get release details."""
        if not code_or_id:
            return None

        url = f'{BASE_URL}/release/{code_or_id}'
        html = self._get_cached(f'detail_{code_or_id}', url)

        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Title
            title_el = soup.select_one('h1, .release-title')
            title = title_el.text.strip() if title_el else 'Unknown'

            # Description
            desc_el = soup.select_one('.description, .release-description, .release-text')
            description = desc_el.text.strip()[:1000] if desc_el else ''

            # Genres
            genres = []
            genre_els = soup.select('.genre-tag, .tag, .label')
            for g in genre_els[:5]:
                genres.append(g.text.strip())

            # Episodes
            episodes = []
            ep_els = soup.select('.episode, .episode-item, .episodes-list li')
            for ep in ep_els[:20]:
                ep_num = ep.get('data-episode', 0)
                try:
                    ep_num = int(ep_num) if ep_num else 0
                except:
                    ep_num = 0
                episodes.append({
                    'episode': ep_num,
                    'name': ep.text.strip() or f'Эпизод {ep_num}',
                })

            # Poster
            poster_el = soup.select_one('.poster img, .release-poster img, img.poster')
            poster = ''
            if poster_el:
                poster = poster_el.get('src', poster_el.get('data-src', ''))
                if poster.startswith('/'):
                    poster = BASE_URL + poster

            # Year
            year_match = re.search(r'\b(20\d{2})\b', soup.text)
            year = int(year_match.group(1)) if year_match else 2024

            return {
                'id': code_or_id,
                'code': code_or_id,
                'title': title,
                'title_en': '',
                'title_jp': '',
                'type': 'TV',
                'status': 'ongoing',
                'year': year,
                'season': '',
                'genres': genres,
                'description': description,
                'rating': 0,
                'age_rating': '16+',
                'episodes_count': len(episodes),
                'episodes': episodes,
                'poster': poster,
                'player': {
                    'streams': {},
                    'list': episodes,
                    'host': '',
                },
                'torrent': None,
            }
        except Exception as e:
            logger.error('Detail parse error: %s', e)
            return None

    def get_schedule(self):
        """Get schedule (not available via scraping)."""
        return {'list': []}

    def get_genres(self):
        """Get genres list."""
        return [
            {'id': 'action', 'name': 'Экшен', 'count': 500},
            {'id': 'adventure', 'name': 'Приключения', 'count': 400},
            {'id': 'comedy', 'name': 'Комедия', 'count': 600},
            {'id': 'drama', 'name': 'Драма', 'count': 350},
            {'id': 'fantasy', 'name': 'Фэнтези', 'count': 450},
            {'id': 'romance', 'name': 'Романтика', 'count': 400},
            {'id': 'sci-fi', 'name': 'Научная фантастика', 'count': 200},
            {'id': 'slice-of-life', 'name': 'Повседневность', 'count': 300},
            {'id': 'supernatural', 'name': 'Сверхъестественное', 'count': 250},
            {'id': 'thriller', 'name': 'Триллер', 'count': 150},
            {'id': 'horror', 'name': 'Ужасы', 'count': 100},
            {'id': 'mecha', 'name': 'Меха', 'count': 80},
            {'id': 'sport', 'name': 'Спорт', 'count': 60},
            {'id': 'psychological', 'name': 'Психологическое', 'count': 120},
            {'id': 'isekai', 'name': 'Исекай', 'count': 180},
            {'id': 'school', 'name': 'Школа', 'count': 220},
        ]

    def get_by_genre(self, genre, page=1, limit=20):
        """Get releases by genre."""
        return self.browse(page=page, limit=limit)

    def get_random(self):
        """Get random release."""
        import random
        all_releases = self.browse(page=1, limit=50)
        if all_releases:
            return random.choice(all_releases)
        return None


# Singleton instance
anilibria_service = AnilibriaScraper()
