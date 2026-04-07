"""AnimeVost routes — admin-only search, browse, detail, genres."""

import logging
from flask import Blueprint, request, jsonify
from routes.admin import require_admin
from services.animevost_service import animevost_service

logger = logging.getLogger(__name__)
animevost_bp = Blueprint('animevost', __name__)


@animevost_bp.route('/search')
@require_admin
def search():
    """Search AnimeVost for anime."""
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    try:
        limit = request.args.get('limit', 20, type=int)
        return jsonify(animevost_service.search(q, limit=min(limit, 50)))
    except Exception as e:
        logger.exception('AnimeVost search error: q=%s', q)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@animevost_bp.route('/detail')
@require_admin
def detail():
    """Get detailed info about an anime from its AnimeVost page URL."""
    url = request.args.get('url', '')
    if not url or not url.startswith('http'):
        return jsonify({'error': 'Valid url parameter required'}), 400
    try:
        result = animevost_service.get_detail(url)
        if not result:
            return jsonify({'error': 'Could not fetch details'}), 502
        return jsonify(result)
    except Exception as e:
        logger.exception('AnimeVost detail error: url=%s', url)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@animevost_bp.route('/browse')
@require_admin
def browse():
    """Browse latest anime releases on AnimeVost."""
    page = request.args.get('page', 1, type=int)
    try:
        return jsonify(animevost_service.browse(page=max(1, page)))
    except Exception as e:
        logger.exception('AnimeVost browse error: page=%s', page)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@animevost_bp.route('/ongoing')
@require_admin
def ongoing():
    """Get ongoing anime list."""
    try:
        return jsonify(animevost_service.get_ongoing())
    except Exception as e:
        logger.exception('AnimeVost ongoing error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@animevost_bp.route('/genres')
@require_admin
def genres():
    """Get list of anime genres."""
    try:
        return jsonify(animevost_service.get_genres())
    except Exception as e:
        logger.exception('AnimeVost genres error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@animevost_bp.route('/genre/<genre_id>')
@require_admin
def browse_by_genre(genre_id):
    """Browse anime by genre."""
    page = request.args.get('page', 1, type=int)
    try:
        return jsonify(animevost_service.browse_by_genre(genre_id, page=max(1, page)))
    except Exception as e:
        logger.exception('AnimeVost genre browse error: genre=%s page=%s', genre_id, page)
        return jsonify({'error': 'Service temporarily unavailable'}), 503
