"""Movie routes — trending, search, details, recommendations, trailers, genres."""

import logging
from flask import Blueprint, request, jsonify
from services.tmdb_service import tmdb_service

logger = logging.getLogger(__name__)
movies_bp = Blueprint('movies', __name__)


@movies_bp.route('/trending')
def trending():
    """Get trending movies with randomized results."""
    try:
        page = request.args.get('page', 1, type=int)
        return jsonify(tmdb_service.get_trending(page=page))
    except Exception as e:
        logger.exception('Error fetching trending movies')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@movies_bp.route('/search')
def search():
    """Search movies by query string."""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    if not q:
        return jsonify([])
    try:
        return jsonify(tmdb_service.search(q, page=page))
    except Exception as e:
        logger.exception('Error searching movies: q=%s', q)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@movies_bp.route('/<movie_id>')
def movie_detail(movie_id):
    """Get detailed information about a specific movie."""
    try:
        movie = tmdb_service.get_movie(movie_id)
        if not movie:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(movie)
    except Exception as e:
        logger.exception('Error fetching movie %s', movie_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@movies_bp.route('/<movie_id>/recommendations')
def movie_recommendations(movie_id):
    """Get similar movie recommendations."""
    try:
        return jsonify(tmdb_service.get_recommendations(movie_id))
    except Exception as e:
        logger.exception('Error fetching recommendations for %s', movie_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@movies_bp.route('/<movie_id>/videos')
def movie_videos(movie_id):
    """Get trailers and videos for a movie."""
    try:
        return jsonify(tmdb_service.get_videos(movie_id))
    except Exception as e:
        logger.exception('Error fetching videos for %s', movie_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@movies_bp.route('/genres')
def genres():
    """Get list of available movie genres."""
    try:
        return jsonify(tmdb_service.get_genres())
    except Exception as e:
        logger.exception('Error fetching genres')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@movies_bp.route('/discover')
def discover():
    """Discover movies by genre with pagination."""
    try:
        genre_id = request.args.get('genre')
        page = request.args.get('page', 1, type=int)
        return jsonify(tmdb_service.discover(genre_id, page=page))
    except Exception as e:
        logger.exception('Error discovering movies')
        return jsonify({'error': 'Service temporarily unavailable'}), 503
