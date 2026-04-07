"""Music routes — charts, search, genres, tracks, artists, albums."""

import logging
from flask import Blueprint, request, jsonify
from services.music_service import music_service

logger = logging.getLogger(__name__)
music_bp = Blueprint('music', __name__)


@music_bp.route('/chart')
def chart():
    """Get top chart tracks with randomized order."""
    try:
        limit = request.args.get('limit', 50, type=int)
        return jsonify(music_service.get_chart(limit))
    except Exception as e:
        logger.exception('Error fetching chart')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@music_bp.route('/search')
def search():
    """Search music tracks by query."""
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    try:
        return jsonify(music_service.search(q))
    except Exception as e:
        logger.exception('Error searching music: q=%s', q)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@music_bp.route('/genres')
def genres():
    """Get list of music genres."""
    try:
        return jsonify(music_service.get_genres())
    except Exception as e:
        logger.exception('Error fetching genres')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@music_bp.route('/genre/<int:genre_id>/tracks')
def genre_tracks(genre_id):
    """Get popular tracks for a specific genre."""
    try:
        return jsonify(music_service.get_genre_tracks(genre_id))
    except Exception as e:
        logger.exception('Error fetching genre tracks for %s', genre_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@music_bp.route('/track/<int:track_id>')
def track(track_id):
    """Get details for a specific track."""
    try:
        result = music_service.get_track(track_id)
        if not result:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(result)
    except Exception as e:
        logger.exception('Error fetching track %s', track_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@music_bp.route('/artist/<int:artist_id>/top')
def artist_top(artist_id):
    """Get top tracks for a specific artist."""
    try:
        return jsonify(music_service.get_artist_top(artist_id))
    except Exception as e:
        logger.exception('Error fetching artist top %s', artist_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@music_bp.route('/album/<int:album_id>')
def album(album_id):
    """Get album details with track listing."""
    try:
        result = music_service.get_album_tracks(album_id)
        if not result:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(result)
    except Exception as e:
        logger.exception('Error fetching album %s', album_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503
