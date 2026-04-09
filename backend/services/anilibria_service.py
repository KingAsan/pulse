"""AniLibria API v1 service — search, browse, detail, player streams."""

import logging
import requests
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

API_BASE = 'https://api.anilibria.tv/v1'
PLAYER_HOST = 'https://cache.libria.fun'
CACHE_TTL = 300  # 5 minutes cache


class AnilibriaService:
    """Service for interacting with AniLibria API v1."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Pulse/1.0 (Entertainment Platform)',
            'Accept': 'application/json'
        })
        # Simple in-memory cache
        self._cache = {}

    def _get_cached(self, key, url, params=None):
        """Get data with simple TTL cache."""
        now = datetime.now()
        if key in self._cache:
            data, expiry = self._cache[key]
            if now < expiry:
                return data

        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            self._cache[key] = (data, now + timedelta(seconds=CACHE_TTL))
            return data
        except requests.RequestException as e:
            logger.error('AniLibria API error: %s', e)
            return None

    def _normalize_release(self, release):
        """Normalize release data for frontend consumption."""
        if not release:
            return None

        names = release.get('names', {})
        player = release.get('player', {})
        episodes = release.get('episodes', {})
        torrents = release.get('torrents', {}).get('list', {})

        # Get best quality torrent
        best_torrent = None
        if torrents:
            # Sort by quality (1080 > 720 > 480)
            sorted_torrents = sorted(torrents.items(),
                                     key=lambda x: int(x[0]) if x[0].replace('p', '').isdigit() else 0,
                                     reverse=True)
            if sorted_torrents:
                best_torrent = sorted_torrents[0][1]

        # Build episode list
        episode_list = []
        if episodes.get('list'):
            for ep in episodes['list']:
                episode_list.append({
                    'episode': ep.get('episode', 0),
                    'name': ep.get('name', f'Эпизод {ep.get("episode", 0)}'),
                    'updated': ep.get('updated', ''),
                })

        # Get genres
        genres = release.get('genres', [])
        if isinstance(genres, list):
            genres = [g.strip() for g in genres if g]
        elif isinstance(genres, str):
            genres = [g.strip() for g in genres.split(',')]

        return {
            'id': release.get('id'),
            'code': release.get('code', ''),
            'title': names.get('ru', names.get('en', 'Unknown')),
            'title_en': names.get('en', ''),
            'title_jp': names.get('jp', ''),
            'type': release.get('type', {}).get('string', 'TV'),
            'status': release.get('status', 'ongoing'),
            'year': release.get('season', {}).get('year', 2024),
            'season': release.get('season', {}).get('string', ''),
            'genres': genres,
            'description': release.get('description', ''),
            'rating': release.get('rating', 0),
            'age_rating': release.get('ageRating', '16+'),
            'episodes_count': episodes.get('total', len(episode_list)),
            'episodes': episode_list,
            'poster': f"https://anilibria.top/storage/releases/posters/{release.get('code')}.jpg",
            'player': {
                'hls': player.get('hls', ''),
                'mp4': player.get('mp4', {}),
                'host': player.get('host', PLAYER_HOST),
            },
            'torrent': {
                'quality': best_torrent.get('quality', '') if best_torrent else '',
                'size': best_torrent.get('size', '') if best_torrent else '',
                'url': best_torrent.get('url', '') if best_torrent else '',
            } if best_torrent else None,
            'franchise': release.get('franchise', []),
            'related': release.get('related', []),
            'schedule': release.get('schedule', {}),
        }

    def search(self, query, page=1, limit=20):
        """Search anime by title."""
        if not query:
            return []

        data = self._get_cached(
            f'search_{query}_{page}',
            f'{API_BASE}/release/',
            params={
                'search': query,
                'page': page,
                'limit': min(limit, 50),
                'include': 'player,description,episodes,torrents',
                'filter': 'id,code,names,type,status,season,genres,rating,ageRating',
                'sort': 'id',
                'order': 'desc',
            }
        )

        if not data or 'list' not in data:
            return []

        return [self._normalize_release(r) for r in data['list'] if r]

    def get_detail(self, code_or_id):
        """Get full release details by code or ID."""
        if not code_or_id:
            return None

        # Determine if it's ID (numeric) or code (string)
        try:
            int(code_or_id)
            param_key = 'id'
        except ValueError:
            param_key = 'code'

        data = self._get_cached(
            f'detail_{code_or_id}',
            f'{API_BASE}/release/',
            params={
                param_key: code_or_id,
                'include': 'player,description,episodes,torrents,franchise,related,schedule,team',
                'filter': 'id,code,names,type,status,season,genres,rating,ageRating',
            }
        )

        if not data or 'list' not in data or not data['list']:
            return None

        return self._normalize_release(data['list'][0])

    def browse(self, page=1, limit=20):
        """Browse latest releases."""
        data = self._get_cached(
            f'browse_{page}',
            f'{API_BASE}/release/',
            params={
                'page': page,
                'limit': min(limit, 50),
                'include': 'player,episodes',
                'filter': 'id,code,names,type,status,season,genres,rating,ageRating',
                'sort': 'id',
                'order': 'desc',
            }
        )

        if not data or 'list' not in data:
            return []

        return [self._normalize_release(r) for r in data['list'] if r]

    def get_ongoing(self, page=1, limit=20):
        """Get ongoing (currently airing) releases."""
        data = self._get_cached(
            f'ongoing_{page}',
            f'{API_BASE}/release/',
            params={
                'page': page,
                'limit': min(limit, 50),
                'include': 'player,episodes',
                'filter': 'id,code,names,type,status,season,genres,rating,ageRating',
                'sort': 'id',
                'order': 'desc',
            }
        )

        if not data or 'list' not in data:
            return []

        # Filter only ongoing releases
        ongoing = [r for r in data['list'] if r and r.get('status') in ('ongoing', 'anons')]
        return [self._normalize_release(r) for r in ongoing]

    def get_schedule(self):
        """Get weekly release schedule."""
        data = self._get_cached(
            'schedule',
            f'{API_BASE}/release/schedule',
            params={
                'filter': 'id,code,names,season',
            }
        )

        if not data or 'list' not in data:
            return {}

        return data

    def get_genres(self):
        """Get list of available genres."""
        # Genres are not directly available in API v1
        # Return common anime genres
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
        """Get releases by genre (search-based since API v1 doesn't have genre filter)."""
        # Search by genre name in Russian
        genre_map = {
            'action': 'экшен',
            'adventure': 'приключения',
            'comedy': 'комедия',
            'drama': 'драма',
            'fantasy': 'фэнтези',
            'romance': 'романтика',
            'sci-fi': 'фантастика',
            'slice-of-life': 'повседневность',
            'supernatural': 'сверхъестественное',
            'thriller': 'триллер',
            'horror': 'ужасы',
            'mecha': 'меха',
            'sport': 'спорт',
            'psychological': 'психологическое',
            'isekai': 'исекай',
            'school': 'школа',
        }

        genre_name = genre_map.get(genre, genre)

        data = self._get_cached(
            f'genre_{genre}_{page}',
            f'{API_BASE}/release/',
            params={
                'search': genre_name,
                'page': page,
                'limit': min(limit, 50),
                'include': 'player,episodes',
                'filter': 'id,code,names,type,status,season,genres,rating,ageRating',
                'sort': 'rating',
                'order': 'desc',
            }
        )

        if not data or 'list' not in data:
            return []

        return [self._normalize_release(r) for r in data['list'] if r]

    def get_random(self):
        """Get a random release."""
        data = self._get_cached(
            'random',
            f'{API_BASE}/release/random',
            params={
                'include': 'player,description,episodes',
                'filter': 'id,code,names,type,status,season,genres,rating,ageRating',
            }
        )

        if not data:
            return None

        return self._normalize_release(data)


# Singleton instance
anilibria_service = AnilibriaService()
