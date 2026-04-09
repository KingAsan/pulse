"""AniLibria routes — search, browse, detail, schedule, genres."""

import logging
from flask import Blueprint, request, jsonify
from routes.admin import require_admin
from services.anilibria_service import anilibria_service

logger = logging.getLogger(__name__)
anilibria_bp = Blueprint('anilibria', __name__)


@anilibria_bp.route('/search')
@require_admin
def search():
    """Search AniLibria for anime."""
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        results = anilibria_service.search(q, page=page, limit=min(limit, 50))
        return jsonify(results)
    except Exception as e:
        logger.exception('AniLibria search error: q=%s', q)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@anilibria_bp.route('/detail')
@require_admin
def detail():
    """Get detailed info about an anime by code or ID."""
    code = request.args.get('code', '')
    anime_id = request.args.get('id', '')
    
    if not code and not anime_id:
        return jsonify({'error': 'code or id parameter required'}), 400
    
    try:
        identifier = code or anime_id
        result = anilibria_service.get_detail(identifier)
        if not result:
            return jsonify({'error': 'Could not fetch details'}), 502
        return jsonify(result)
    except Exception as e:
        logger.exception('AniLibria detail error: code=%s id=%s', code, anime_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@anilibria_bp.route('/browse')
@require_admin
def browse():
    """Browse latest anime releases on AniLibria."""
    page = request.args.get('page', 1, type=int)
    try:
        results = anilibria_service.browse(page=max(1, page))
        return jsonify(results)
    except Exception as e:
        logger.exception('AniLibria browse error: page=%s', page)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@anilibria_bp.route('/ongoing')
@require_admin
def ongoing():
    """Get ongoing (currently airing) anime."""
    try:
        results = anilibria_service.get_ongoing()
        return jsonify(results)
    except Exception as e:
        logger.exception('AniLibria ongoing error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@anilibria_bp.route('/schedule')
@require_admin
def schedule():
    """Get weekly release schedule."""
    try:
        result = anilibria_service.get_schedule()
        return jsonify(result)
    except Exception as e:
        logger.exception('AniLibria schedule error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@anilibria_bp.route('/random')
@require_admin
def random():
    """Get a random anime release."""
    try:
        result = anilibria_service.get_random()
        return jsonify(result) if result else jsonify({})
    except Exception as e:
        logger.exception('AniLibria random error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@anilibria_bp.route('/genres')
@require_admin
def genres():
    """Get list of anime genres."""
    try:
        return jsonify(anilibria_service.get_genres())
    except Exception as e:
        logger.exception('AniLibria genres error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@anilibria_bp.route('/genre/<genre_id>')
@require_admin
def browse_by_genre(genre_id):
    """Browse anime by genre."""
    page = request.args.get('page', 1, type=int)
    try:
        results = anilibria_service.get_by_genre(genre_id, page=max(1, page))
        return jsonify(results)
    except Exception as e:
        logger.exception('AniLibria genre browse error: genre=%s page=%s', genre_id, page)
        return jsonify({'error': 'Service temporarily unavailable'}), 503
