import json
import logging
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from validators import validate_item_type, validate_string, validate_rating
from messages import get_message

logger = logging.getLogger(__name__)

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    """Return all favorites for the current user, optionally filtered by item type."""
    user_id = get_jwt_identity()
    item_type = request.args.get('type')
    db = get_db()
    try:
        if item_type:
            rows = db.execute(
                'SELECT * FROM favorites WHERE user_id = ? AND item_type = ? ORDER BY created_at DESC',
                (user_id, item_type)
            ).fetchall()
        else:
            rows = db.execute(
                'SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        logger.exception('Error fetching favorites for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    """Add an item to the user's favorites list."""
    user_id = get_jwt_identity()
    data = request.get_json()

    valid, err = validate_item_type(data.get('item_type', ''))
    if not valid:
        return jsonify({'error': err}), 400

    valid, err = validate_string(data.get('title'), field_name='title')
    if not valid:
        return jsonify({'error': err}), 400

    db = get_db()
    try:
        db.execute(
            'INSERT OR REPLACE INTO favorites (user_id, item_type, item_id, title, image_url, metadata) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, data['item_type'], data['item_id'], data['title'],
             data.get('image_url'), json.dumps(data.get('metadata', {})))
        )
        db.commit()
        return jsonify({'status': 'added'})
    except Exception:
        logger.exception('Error adding favorite for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/favorites', methods=['DELETE'])
@jwt_required()
def remove_favorite():
    """Remove an item from the user's favorites list."""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'item_type' not in data or 'item_id' not in data:
        return jsonify({'error': 'item_type and item_id are required'}), 400

    db = get_db()
    try:
        db.execute(
            'DELETE FROM favorites WHERE user_id = ? AND item_type = ? AND item_id = ?',
            (user_id, data['item_type'], data['item_id'])
        )
        db.commit()
        return jsonify({'status': 'removed'})
    except Exception:
        logger.exception('Error removing favorite for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/favorites/check', methods=['GET'])
@jwt_required()
def check_favorite():
    """Check whether a specific item is in the user's favorites."""
    user_id = get_jwt_identity()
    item_type = request.args.get('item_type')
    item_id = request.args.get('item_id')
    db = get_db()
    try:
        row = db.execute(
            'SELECT id FROM favorites WHERE user_id = ? AND item_type = ? AND item_id = ?',
            (user_id, item_type, item_id)
        ).fetchone()
        return jsonify({'is_favorite': row is not None})
    except Exception:
        logger.exception('Error checking favorite for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/ratings', methods=['GET'])
@jwt_required()
def get_ratings():
    """Return all ratings for the current user with associated title and image."""
    user_id = get_jwt_identity()
    db = get_db()
    try:
        rows = db.execute(
            'SELECT r.*, f.title, f.image_url FROM ratings r LEFT JOIN favorites f ON r.user_id = f.user_id AND r.item_type = f.item_type AND r.item_id = f.item_id WHERE r.user_id = ? ORDER BY r.created_at DESC',
            (user_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        logger.exception('Error fetching ratings for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/ratings', methods=['POST'])
@jwt_required()
def add_rating():
    """Add or update a rating for an item."""
    user_id = get_jwt_identity()
    data = request.get_json()

    valid, err = validate_item_type(data.get('item_type', ''))
    if not valid:
        return jsonify({'error': err}), 400

    valid, err = validate_rating(data.get('rating'))
    if not valid:
        return jsonify({'error': err}), 400

    db = get_db()
    try:
        db.execute(
            'INSERT OR REPLACE INTO ratings (user_id, item_type, item_id, rating) VALUES (?, ?, ?, ?)',
            (user_id, data['item_type'], data['item_id'], data['rating'])
        )
        db.commit()
        return jsonify({'status': 'rated'})
    except Exception:
        logger.exception('Error adding rating for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/ratings/check', methods=['GET'])
@jwt_required()
def check_rating():
    """Check the current rating for a specific item."""
    user_id = get_jwt_identity()
    item_type = request.args.get('item_type')
    item_id = request.args.get('item_id')
    db = get_db()
    try:
        row = db.execute(
            'SELECT rating FROM ratings WHERE user_id = ? AND item_type = ? AND item_id = ?',
            (user_id, item_type, item_id)
        ).fetchone()
        return jsonify({'rating': row['rating'] if row else 0})
    except Exception:
        logger.exception('Error checking rating for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/search-history', methods=['POST'])
@jwt_required()
def add_search_history():
    """Save a search query to the user's search history."""
    user_id = get_jwt_identity()
    data = request.get_json()

    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'query is required'}), 400

    db = get_db()
    try:
        db.execute(
            'INSERT INTO search_history (user_id, query, category) VALUES (?, ?, ?)',
            (user_id, query, data.get('category', 'general'))
        )
        db.commit()
        return jsonify({'status': 'saved'})
    except Exception:
        logger.exception('Error saving search history for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/search-history', methods=['GET'])
@jwt_required()
def get_search_history():
    """Return the user's recent distinct search queries."""
    user_id = get_jwt_identity()
    db = get_db()
    try:
        rows = db.execute(
            'SELECT DISTINCT query, category, MAX(created_at) as last_searched FROM search_history WHERE user_id = ? GROUP BY query, category ORDER BY last_searched DESC LIMIT 20',
            (user_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        logger.exception('Error fetching search history for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/watchlist', methods=['GET'])
@jwt_required()
def get_watchlist():
    """Return the user's watchlist ordered by priority and date."""
    user_id = get_jwt_identity()
    db = get_db()
    try:
        rows = db.execute(
            'SELECT * FROM watchlist WHERE user_id = ? ORDER BY priority DESC, created_at DESC',
            (user_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        logger.exception('Error fetching watchlist for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/watchlist', methods=['POST'])
@jwt_required()
def add_to_watchlist():
    """Add an item to the user's watchlist."""
    user_id = get_jwt_identity()
    data = request.get_json()

    valid, err = validate_item_type(data.get('item_type', ''))
    if not valid:
        return jsonify({'error': err}), 400

    valid, err = validate_string(data.get('title'), field_name='title')
    if not valid:
        return jsonify({'error': err}), 400

    db = get_db()
    try:
        db.execute(
            'INSERT OR REPLACE INTO watchlist (user_id, item_type, item_id, title, image_url, metadata, note, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, data['item_type'], data['item_id'], data['title'],
             data.get('image_url', ''), json.dumps(data.get('metadata', {})),
             data.get('note', ''), data.get('priority', 0))
        )
        db.commit()
        return jsonify({'status': 'added'})
    except Exception:
        logger.exception('Error adding to watchlist for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/watchlist', methods=['DELETE'])
@jwt_required()
def remove_from_watchlist():
    """Remove an item from the user's watchlist."""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'item_type' not in data or 'item_id' not in data:
        return jsonify({'error': 'item_type and item_id are required'}), 400

    db = get_db()
    try:
        db.execute(
            'DELETE FROM watchlist WHERE user_id = ? AND item_type = ? AND item_id = ?',
            (user_id, data['item_type'], data['item_id'])
        )
        db.commit()
        return jsonify({'status': 'removed'})
    except Exception:
        logger.exception('Error removing from watchlist for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/watchlist/check', methods=['GET'])
@jwt_required()
def check_watchlist():
    """Check whether a specific item is in the user's watchlist."""
    user_id = get_jwt_identity()
    item_type = request.args.get('item_type')
    item_id = request.args.get('item_id')
    db = get_db()
    try:
        row = db.execute(
            'SELECT id FROM watchlist WHERE user_id = ? AND item_type = ? AND item_id = ?',
            (user_id, item_type, item_id)
        ).fetchone()
        return jsonify({'in_watchlist': row is not None})
    except Exception:
        logger.exception('Error checking watchlist for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Return aggregated profile statistics for the current user."""
    user_id = get_jwt_identity()
    db = get_db()
    try:
        stats = db.execute('''
            SELECT
                (SELECT COUNT(*) FROM favorites WHERE user_id = ?) as favorites,
                (SELECT COUNT(*) FROM ratings WHERE user_id = ?) as ratings,
                (SELECT AVG(rating) FROM ratings WHERE user_id = ?) as avg_rating,
                (SELECT COUNT(*) FROM search_history WHERE user_id = ?) as searches,
                (SELECT COUNT(*) FROM watchlist WHERE user_id = ?) as watchlist,
                (SELECT COUNT(*) FROM ai_history WHERE user_id = ?) as ai_queries,
                (SELECT COUNT(DISTINCT session_id) FROM ai_history WHERE user_id = ?) as ai_sessions,
                (SELECT COUNT(*) FROM ai_feedback WHERE user_id = ? AND feedback_type = 'like') as ai_likes
        ''', (user_id,) * 8).fetchone()

        fav_by_type = db.execute(
            'SELECT item_type, COUNT(*) as count FROM favorites WHERE user_id = ? GROUP BY item_type',
            (user_id,)
        ).fetchall()

        rating_dist = db.execute(
            'SELECT rating, COUNT(*) as count FROM ratings WHERE user_id = ? GROUP BY rating ORDER BY rating',
            (user_id,)
        ).fetchall()

        return jsonify({
            'favorites': stats['favorites'],
            'ratings': stats['ratings'],
            'avg_rating': round(stats['avg_rating'] or 0, 1),
            'searches': stats['searches'],
            'watchlist': stats['watchlist'],
            'ai_queries': stats['ai_queries'],
            'ai_sessions': stats['ai_sessions'],
            'ai_likes': stats['ai_likes'],
            'favorites_by_type': {r['item_type']: r['count'] for r in fav_by_type},
            'rating_distribution': {str(r['rating']): r['count'] for r in rating_dist},
        })
    except Exception:
        logger.exception('Error fetching stats for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@profile_bp.route('/export', methods=['GET'])
@jwt_required()
def export_user_data():
    """Export all user data as a downloadable JSON file."""
    user_id = get_jwt_identity()
    db = get_db()
    try:
        user = db.execute('SELECT id, username, email, created_at FROM users WHERE id = ?', (user_id,)).fetchone()
        favorites = db.execute('SELECT item_type, item_id, title, image_url, created_at FROM favorites WHERE user_id = ?', (user_id,)).fetchall()
        ratings = db.execute('SELECT item_type, item_id, rating, created_at FROM ratings WHERE user_id = ?', (user_id,)).fetchall()
        watchlist = db.execute('SELECT item_type, item_id, title, note, priority, created_at FROM watchlist WHERE user_id = ?', (user_id,)).fetchall()
        activity = db.execute('SELECT item_type, item_id, title, action, rating, consumed_at FROM activity_log WHERE user_id = ?', (user_id,)).fetchall()
        ai_history = db.execute('SELECT session_id, user_query, timestamp FROM ai_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 200', (user_id,)).fetchall()
        prefs = db.execute('SELECT favorite_categories, disliked_categories, favorite_platforms, preferred_language, discovery_mode FROM ai_preferences WHERE user_id = ?', (user_id,)).fetchone()

        export = {
            'profile': dict(user) if user else {},
            'favorites': [dict(r) for r in favorites],
            'ratings': [dict(r) for r in ratings],
            'watchlist': [dict(r) for r in watchlist],
            'activity_log': [dict(r) for r in activity],
            'ai_history': [dict(r) for r in ai_history],
            'preferences': dict(prefs) if prefs else {},
            'export_date': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        }

        return Response(
            json.dumps(export, ensure_ascii=False, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=pulse_export_{user_id}.json'}
        )
    except Exception:
        logger.exception('Error exporting data for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()
