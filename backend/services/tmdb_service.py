import logging
import requests
import re
import time
import random
from config import Config

logger = logging.getLogger(__name__)


class TTLCache:
    """Simple in-memory cache with TTL."""
    def __init__(self, ttl=600):
        self.ttl = ttl
        self._data = {}

    def get(self, key):
        if key in self._data:
            val, ts = self._data[key]
            if time.time() - ts < self.ttl:
                return val
            del self._data[key]
        return None

    def set(self, key, value):
        self._data[key] = (value, time.time())


class TmdbService:
    """Movie service powered by KinopoiskDev API with caching and randomized results."""

    def __init__(self):
        self.api_key = Config.KINOPOISK_API_KEY
        self.base_url = Config.KINOPOISK_BASE_URL
        self._cache = TTLCache(ttl=900)  # 15 min cache

    def _get(self, endpoint, params=None):
        cache_key = f"{endpoint}:{params}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            headers = {'X-API-KEY': self.api_key}
            resp = requests.get(
                f"{self.base_url}{endpoint}",
                params=params or {},
                headers=headers,
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self._cache.set(cache_key, data)
                return data
        except Exception as e:
            logger.warning('KinopoiskDev API error: %s', e)
        return None

    def _format_movie(self, movie):
        if not movie:
            return None

        poster_url = None
        if movie.get('poster') and movie['poster'].get('url'):
            poster_url = movie['poster']['url']

        backdrop_url = None
        if movie.get('backdrop') and movie['backdrop'].get('url'):
            backdrop_url = movie['backdrop']['url']
        elif movie.get('poster') and movie['poster'].get('previewUrl'):
            backdrop_url = movie['poster']['previewUrl']

        rating = 0
        if movie.get('rating'):
            rating = movie['rating'].get('kp', 0) or movie['rating'].get('imdb', 0) or 0

        genres = []
        genre_names = []
        if movie.get('genres'):
            for g in movie['genres']:
                name = g.get('name', '')
                if name:
                    genres.append({'id': name, 'name': name})
                    genre_names.append(name)

        year = movie.get('year', '')
        release_date = f"{year}-01-01" if year else ''

        title = movie.get('name') or movie.get('alternativeName') or 'Без названия'

        return {
            'id': movie.get('id'),
            'title': title,
            'overview': movie.get('description') or movie.get('shortDescription') or '',
            'poster_url': poster_url,
            'backdrop_url': backdrop_url,
            'vote_average': round(rating, 1) if rating else 0,
            'release_date': release_date,
            'genre_ids': genre_names,
            'genres': genres,
            'popularity': movie.get('votes', {}).get('kp', 0) if movie.get('votes') else 0,
        }

    def get_trending(self, page=1):
        """Return trending movies, randomizing the page for homepage variety."""
        # Randomize page for variety on homepage (pages 1-5)
        if page == 1:
            page = random.randint(1, 5)
        data = self._get('/v1.4/movie', {
            'page': page,
            'limit': 40,
            'sortField': 'votes.kp',
            'sortType': '-1',
            'type': 'movie',
            'rating.kp': '7-10',
            'votes.kp': '100000-9999999',
        })
        if data and data.get('docs'):
            movies = [self._format_movie(m) for m in data['docs'] if m]
            random.shuffle(movies)
            return movies
        return []

    def search(self, query, page=1):
        """Search movies by title query."""
        data = self._get('/v1.4/movie/search', {
            'query': query,
            'page': page,
            'limit': 40,
        })
        if data and data.get('docs'):
            return [self._format_movie(m) for m in data['docs'] if m]
        return []

    def get_movie(self, movie_id):
        """Fetch a single movie by its KinopoiskDev ID."""
        data = self._get(f'/v1.4/movie/{movie_id}')
        if data and data.get('id'):
            return self._format_movie(data)
        return None

    def get_recommendations(self, movie_id):
        """Return similar movies for the given movie ID."""
        data = self._get(f'/v1.4/movie/{movie_id}')
        if data and data.get('similarMovies'):
            similar = []
            for s in data['similarMovies'][:10]:
                similar.append({
                    'id': s.get('id'),
                    'title': s.get('name') or s.get('alternativeName') or '',
                    'overview': '',
                    'poster_url': s.get('poster', {}).get('url') if s.get('poster') else None,
                    'backdrop_url': s.get('poster', {}).get('previewUrl') if s.get('poster') else None,
                    'vote_average': s.get('rating', {}).get('kp', 0) if s.get('rating') else 0,
                    'release_date': f"{s.get('year', '')}-01-01" if s.get('year') else '',
                    'genre_ids': [],
                    'genres': [],
                    'popularity': 0,
                })
            return similar
        return []

    def get_videos(self, movie_id):
        """Return trailer videos for the given movie, with YouTube fallback."""
        data = self._get(f'/v1.4/movie/{movie_id}')
        if data and data.get('videos') and data['videos'].get('trailers'):
            trailers = []
            for t in data['videos']['trailers']:
                url = t.get('url', '')
                key = self._extract_youtube_key(url)
                if key:
                    trailers.append({
                        'key': key,
                        'name': t.get('name', 'Трейлер'),
                        'type': 'Trailer',
                    })
            if trailers:
                return trailers[:5]
        # Fallback: search YouTube by movie title
        if data:
            title = data.get('name') or data.get('alternativeName') or ''
            year = data.get('year', '')
            if title:
                try:
                    from youtube_search import YoutubeSearch
                    query = f"{title} {year} трейлер" if title else ""
                    results = YoutubeSearch(query, max_results=1).to_dict()
                    if results:
                        return [{'key': results[0]['id'], 'name': f'{title} — Трейлер', 'type': 'Trailer'}]
                except Exception:
                    pass
        return []

    def _extract_youtube_key(self, url):
        if not url:
            return None
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_genres(self):
        """Return the list of available movie genres."""
        data = self._get('/v1/movie/possible-values-by-field', {
            'field': 'genres.name',
        })
        if data and isinstance(data, list):
            return [{'id': g.get('name', ''), 'name': g.get('name', '')} for g in data if g.get('name')]
        return []

    def discover(self, genre_id=None, page=1):
        """Discover movies, optionally filtered by genre."""
        params = {
            'page': page,
            'limit': 40,
            'sortField': 'votes.kp',
            'sortType': '-1',
            'type': 'movie',
            'votes.kp': '10000-9999999',
        }
        if genre_id:
            params['genres.name'] = genre_id
        data = self._get('/v1.4/movie', params)
        if data and data.get('docs'):
            return [self._format_movie(m) for m in data['docs'] if m]
        return []


tmdb_service = TmdbService()
