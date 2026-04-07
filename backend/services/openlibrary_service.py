import logging
import requests
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


class GoogleBooksService:
    """Book service powered by Google Books API with caching and randomized trending."""

    def __init__(self):
        self.base_url = 'https://www.googleapis.com/books/v1'
        self.api_key = getattr(Config, 'GOOGLE_BOOKS_API_KEY', '')
        self._cache = TTLCache(ttl=900)  # 15 min cache

    def _get(self, endpoint, params=None):
        cache_key = f"{endpoint}:{params}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            p = params or {}
            if self.api_key:
                p['key'] = self.api_key
            resp = requests.get(f"{self.base_url}{endpoint}", params=p, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                self._cache.set(cache_key, data)
                return data
        except Exception as e:
            logger.warning('Google Books API error: %s', e)
        return None

    def _format_book(self, item):
        if not item:
            return None
        v = item.get('volumeInfo', {})
        img = v.get('imageLinks', {})

        # Get best cover URL, prefer larger images, force HTTPS
        cover_url = img.get('thumbnail') or img.get('smallThumbnail')
        if cover_url:
            cover_url = cover_url.replace('http://', 'https://')
            # Request larger image
            cover_url = cover_url.replace('zoom=1', 'zoom=2')

        return {
            'key': item.get('id', ''),
            'title': v.get('title', ''),
            'authors': v.get('authors', []),
            'first_publish_year': int(v.get('publishedDate', '0')[:4]) if v.get('publishedDate') and v['publishedDate'][:4].isdigit() else None,
            'cover_url': cover_url,
            'subjects': v.get('categories', [])[:5],
            'pages': v.get('pageCount'),
            'rating': v.get('averageRating', 0) or 0,
            'description': v.get('description', ''),
        }

    def search(self, query, start_index=0):
        """Search books by query string."""
        data = self._get('/volumes', {
            'q': query,
            'maxResults': 40,
            'startIndex': start_index,
            'orderBy': 'relevance',
            'printType': 'books',
        })
        if data and data.get('items'):
            return [self._format_book(b) for b in data['items'] if b]
        return []

    def get_book(self, key):
        """Fetch a single book by its Google Books volume ID."""
        if key.startswith('/'):
            key = key.lstrip('/')
        data = self._get(f'/volumes/{key}')
        if data and data.get('id'):
            book = self._format_book(data)
            return book
        return None

    def get_trending(self):
        """Return trending books using randomized popular queries."""
        cached = self._cache.get('trending_books')
        if cached is not None:
            random.shuffle(cached)
            return cached

        queries = [
            'subject:fiction', 'bestseller', 'popular novels',
            'subject:thriller', 'subject:fantasy', 'subject:science fiction',
            'award winning books', 'modern classics', 'subject:mystery',
        ]
        query = random.choice(queries)
        data = self._get('/volumes', {
            'q': query,
            'maxResults': 40,
            'orderBy': 'relevance',
            'printType': 'books',
            'langRestrict': 'en',
            'startIndex': random.randint(0, 20),
        })
        if data and data.get('items'):
            results = [self._format_book(b) for b in data['items'] if b]
            self._cache.set('trending_books', results)
            return results

        # Fallback: popular classics
        data = self._get('/volumes', {
            'q': 'popular classic novels',
            'maxResults': 40,
            'orderBy': 'relevance',
            'printType': 'books',
        })
        if data and data.get('items'):
            results = [self._format_book(b) for b in data['items'] if b]
            self._cache.set('trending_books', results)
            return results
        return []

    def get_by_subject(self, subject, start_index=0):
        """Return books filtered by subject category."""
        data = self._get('/volumes', {
            'q': f'subject:{subject}',
            'maxResults': 40,
            'startIndex': start_index,
            'orderBy': 'relevance',
            'printType': 'books',
        })
        if data and data.get('items'):
            return [self._format_book(b) for b in data['items'] if b]
        return []


openlibrary_service = GoogleBooksService()
