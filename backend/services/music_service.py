import logging
import time
import random
import httpx

logger = logging.getLogger(__name__)

DEEZER_BASE = 'https://api.deezer.com'


class TTLCache:
    def __init__(self, ttl=900):
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


cache = TTLCache()


def _format_track(t):
    return {
        'id': t.get('id'),
        'title': t.get('title', ''),
        'artist': t.get('artist', {}).get('name', ''),
        'artist_id': t.get('artist', {}).get('id'),
        'artist_picture': t.get('artist', {}).get('picture_medium', ''),
        'album': t.get('album', {}).get('title', ''),
        'album_id': t.get('album', {}).get('id'),
        'cover': t.get('album', {}).get('cover_medium', ''),
        'cover_big': t.get('album', {}).get('cover_big', ''),
        'preview': t.get('preview', ''),
        'duration': t.get('duration', 0),
        'link': t.get('link', ''),
    }


def _get(path, params=None):
    try:
        r = httpx.get(f'{DEEZER_BASE}{path}', params=params or {}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning('Deezer API error on %s: %s', path, e)
        return {}


class DeezerService:
    """Music service powered by Deezer API with caching and chart randomization."""

    def get_chart(self, limit=50):
        """Return chart tracks, shuffled for variety."""
        key = f'chart:{limit}'
        cached = cache.get(key)
        if cached:
            random.shuffle(cached)
            return cached
        data = _get('/chart/0/tracks', {'limit': max(limit, 100)})
        tracks = [_format_track(t) for t in data.get('data', [])]
        cache.set(key, tracks)
        random.shuffle(tracks)
        return tracks[:limit] if limit < len(tracks) else tracks

    def search(self, query, limit=30):
        """Search tracks by query string."""
        if not query:
            return []
        key = f'search:{query}:{limit}'
        cached = cache.get(key)
        if cached:
            return cached
        data = _get('/search', {'q': query, 'limit': limit})
        tracks = [_format_track(t) for t in data.get('data', [])]
        cache.set(key, tracks)
        return tracks

    def get_genres(self):
        """Return the list of available music genres."""
        cached = cache.get('genres')
        if cached:
            return cached
        data = _get('/genre')
        genres = [
            {'id': g['id'], 'name': g['name'], 'picture': g.get('picture_medium', '')}
            for g in data.get('data', []) if g.get('id', 0) != 0
        ]
        cache.set('genres', genres)
        return genres

    def get_genre_tracks(self, genre_id, limit=50):
        """Return tracks for a given genre by aggregating top artist tracks."""
        key = f'genre_tracks:{genre_id}'
        cached = cache.get(key)
        if cached:
            return cached
        # Get artists from genre radio, then get their top tracks
        data = _get(f'/genre/{genre_id}/artists')
        artists = data.get('data', [])[:8]
        tracks = []
        seen = set()
        for artist in artists:
            artist_data = _get(f'/artist/{artist["id"]}/top', {'limit': 5})
            for t in artist_data.get('data', []):
                if t['id'] not in seen:
                    tracks.append(_format_track(t))
                    seen.add(t['id'])
                if len(tracks) >= limit:
                    break
            if len(tracks) >= limit:
                break
        cache.set(key, tracks)
        return tracks

    def get_track(self, track_id):
        """Fetch a single track by its Deezer ID."""
        key = f'track:{track_id}'
        cached = cache.get(key)
        if cached:
            return cached
        data = _get(f'/track/{track_id}')
        if not data.get('id'):
            return None
        track = _format_track(data)
        cache.set(key, track)
        return track

    def get_artist_top(self, artist_id, limit=20):
        """Return top tracks for the given artist."""
        key = f'artist_top:{artist_id}'
        cached = cache.get(key)
        if cached:
            return cached
        data = _get(f'/artist/{artist_id}/top', {'limit': limit})
        tracks = [_format_track(t) for t in data.get('data', [])]
        cache.set(key, tracks)
        return tracks

    def get_album_tracks(self, album_id):
        """Return album info and its tracks."""
        key = f'album:{album_id}'
        cached = cache.get(key)
        if cached:
            return cached
        data = _get(f'/album/{album_id}')
        if not data.get('id'):
            return None
        album_info = {
            'id': data['id'],
            'title': data.get('title', ''),
            'artist': data.get('artist', {}).get('name', ''),
            'cover': data.get('cover_medium', ''),
            'cover_big': data.get('cover_big', ''),
        }
        tracks = [_format_track(t) for t in data.get('tracks', {}).get('data', [])]
        for t in tracks:
            t['cover'] = album_info['cover']
            t['cover_big'] = album_info['cover_big']
            t['album'] = album_info['title']
        result = {'album': album_info, 'tracks': tracks}
        cache.set(key, result)
        return result


music_service = DeezerService()
