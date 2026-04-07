"""Content recommendation engine — personalized suggestions based on user history and preferences."""

import json
import os
import logging
from database import get_db

logger = logging.getLogger(__name__)
from services.tmdb_service import tmdb_service
from services.openlibrary_service import openlibrary_service
from services.music_service import music_service
from services.events_service import events_service

GENRES_MAP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'genres.json')


def _load_genre_map():
    if os.path.exists(GENRES_MAP_PATH):
        with open(GENRES_MAP_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


class RecommendationEngine:
    def __init__(self):
        self.genre_map = _load_genre_map()

    def get_user_profile(self, user_id):
        db = get_db()
        try:
            favorites = db.execute(
                'SELECT item_type, item_id, metadata FROM favorites WHERE user_id = ?',
                (user_id,)
            ).fetchall()

            # Build lookup map: (item_type, item_id) -> metadata
            fav_metadata = {}
            for f in favorites:
                if f['metadata']:
                    try:
                        fav_metadata[(f['item_type'], f['item_id'])] = json.loads(f['metadata'])
                    except Exception:
                        pass

            ratings = db.execute(
                'SELECT item_type, item_id, rating FROM ratings WHERE user_id = ?',
                (user_id,)
            ).fetchall()

            genre_weights = {}
            for r in ratings:
                metadata = fav_metadata.get((r['item_type'], r['item_id']))
                if metadata and 'genres' in metadata:
                    weight = r['rating'] - 2
                    for g in metadata['genres']:
                        key = f"{r['item_type']}:{g}"
                        genre_weights[key] = genre_weights.get(key, 0) + weight

            for f in favorites:
                metadata = fav_metadata.get((f['item_type'], f['item_id']))
                if metadata and 'genres' in metadata:
                    for g in metadata['genres']:
                        key = f"{f['item_type']}:{g}"
                        genre_weights[key] = genre_weights.get(key, 0) + 2

            return genre_weights
        finally:
            db.close()

    def get_taste_summary(self, user_id):
        profile = self.get_user_profile(user_id)
        db = get_db()
        try:
            stats = {
                'total_ratings': db.execute('SELECT COUNT(*) as c FROM ratings WHERE user_id = ?', (user_id,)).fetchone()['c'],
                'total_favorites': db.execute('SELECT COUNT(*) as c FROM favorites WHERE user_id = ?', (user_id,)).fetchone()['c'],
                'avg_rating': db.execute('SELECT AVG(rating) as a FROM ratings WHERE user_id = ?', (user_id,)).fetchone()['a'] or 0,
            }

            categories = {}
            for key, weight in sorted(profile.items(), key=lambda x: -x[1]):
                cat, genre = key.split(':', 1)
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append({'genre': genre, 'weight': weight})

            return {
                'stats': stats,
                'top_genres': categories,
                'profile': profile,
            }
        finally:
            db.close()

    def get_for_you(self, user_id):
        profile = self.get_user_profile(user_id)
        results = {'movies': [], 'books': [], 'music': [], 'events': []}

        movie_genres = {k.split(':')[1]: v for k, v in profile.items() if k.startswith('movie:')}
        if movie_genres:
            top_genre = max(movie_genres, key=movie_genres.get)
            genre_list = tmdb_service.get_genres()
            genre_id = None
            for g in genre_list:
                if g['name'].lower() == top_genre.lower():
                    genre_id = g['id']
                    break
            if genre_id:
                results['movies'] = tmdb_service.discover(genre_id)[:6]
        if not results['movies']:
            results['movies'] = tmdb_service.get_trending()[:6]

        book_genres = {k.split(':')[1]: v for k, v in profile.items() if k.startswith('book:')}
        if book_genres:
            top_subject = max(book_genres, key=book_genres.get)
            results['books'] = openlibrary_service.get_by_subject(top_subject)[:6]
        if not results['books']:
            results['books'] = openlibrary_service.get_trending()[:6]

        music_genres = {k.split(':')[1]: v for k, v in profile.items() if k.startswith('music:')}
        if music_genres:
            top_genre = max(music_genres, key=music_genres.get)
            results['music'] = music_service.search(top_genre, limit=6)
        if not results['music']:
            results['music'] = music_service.get_chart(limit=6)

        results['events'] = events_service.browse(limit=6)

        return results

    def because_you_liked(self, user_id, item_type, item_id):
        if item_type == 'movie':
            return tmdb_service.get_recommendations(item_id)
        if item_type == 'music':
            return music_service.get_chart(limit=10)
        if item_type == 'book':
            return openlibrary_service.get_trending()[:10]
        return []


recommendation_engine = RecommendationEngine()
