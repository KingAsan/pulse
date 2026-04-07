import json
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from validators import validate_string, validate_item_type, validate_timestamp
from messages import get_message

logger = logging.getLogger(__name__)

assistant_bp = Blueprint('assistant', __name__)


# ==================== ACTIVITY LOG ====================

@assistant_bp.route('/activity', methods=['GET'])
@jwt_required()
def get_activity():
    """Return the user's activity log, optionally filtered by item type."""
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 50, type=int)
    item_type = request.args.get('type')
    db = get_db()
    try:
        if item_type:
            rows = db.execute(
                'SELECT * FROM activity_log WHERE user_id = ? AND item_type = ? ORDER BY consumed_at DESC LIMIT ?',
                (user_id, item_type, limit)
            ).fetchall()
        else:
            rows = db.execute(
                'SELECT * FROM activity_log WHERE user_id = ? ORDER BY consumed_at DESC LIMIT ?',
                (user_id, limit)
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        logger.exception('Error fetching activity for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/activity', methods=['POST'])
@jwt_required()
def log_activity():
    """Log a new activity (e.g. watched, read, listened) for the user."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'title required'}), 400

    item_type = data.get('item_type', 'movie')
    valid, err = validate_item_type(item_type)
    if not valid:
        return jsonify({'error': err}), 400

    db = get_db()
    try:
        db.execute('''
            INSERT OR REPLACE INTO activity_log
            (user_id, item_type, item_id, title, image_url, action, rating, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, item_type, data.get('item_id', title),
              title, data.get('image_url', ''), data.get('action', 'watched'),
              data.get('rating'), data.get('note', '')))
        db.commit()

        _create_notification(db, user_id, 'activity',
                             get_message('activity_logged'),
                             get_message('added_to_history', title=title))
        return jsonify({'status': 'logged'})
    except Exception:
        logger.exception('Error logging activity for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/activity', methods=['DELETE'])
@jwt_required()
def delete_activity():
    """Delete an activity entry by item_type and item_id."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or 'item_type' not in data or 'item_id' not in data:
        return jsonify({'error': 'item_type and item_id are required'}), 400

    db = get_db()
    try:
        db.execute(
            'DELETE FROM activity_log WHERE user_id = ? AND item_type = ? AND item_id = ?',
            (user_id, data['item_type'], data['item_id'])
        )
        db.commit()
        return jsonify({'status': 'removed'})
    except Exception:
        logger.exception('Error deleting activity for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/activity/check', methods=['GET'])
@jwt_required()
def check_activity():
    """Check if a specific item exists in the user's activity log."""
    user_id = int(get_jwt_identity())
    item_type = request.args.get('item_type')
    item_id = request.args.get('item_id')
    db = get_db()
    try:
        row = db.execute(
            'SELECT id, action, consumed_at FROM activity_log WHERE user_id = ? AND item_type = ? AND item_id = ?',
            (user_id, item_type, item_id)
        ).fetchone()
        return jsonify({'consumed': row is not None, 'data': dict(row) if row else None})
    except Exception:
        logger.exception('Error checking activity for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


# ==================== WEEKLY RECAP ====================

@assistant_bp.route('/weekly-recap', methods=['GET'])
@jwt_required()
def weekly_recap():
    """Return a weekly recap of user activity, favorites, ratings, and trends."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        activities = db.execute(
            'SELECT * FROM activity_log WHERE user_id = ? AND consumed_at >= ? ORDER BY consumed_at DESC',
            (user_id, week_ago)
        ).fetchall()

        ai_queries = db.execute(
            'SELECT COUNT(*) as c FROM ai_history WHERE user_id = ? AND timestamp >= ?',
            (user_id, week_ago)
        ).fetchone()['c']

        new_favorites = db.execute(
            'SELECT COUNT(*) as c FROM favorites WHERE user_id = ? AND created_at >= ?',
            (user_id, week_ago)
        ).fetchone()['c']

        new_ratings = db.execute(
            'SELECT COUNT(*) as c FROM ratings WHERE user_id = ? AND created_at >= ?',
            (user_id, week_ago)
        ).fetchone()['c']

        type_counter = Counter()
        for a in activities:
            type_counter[a['item_type']] += 1

        activity_list = [dict(a) for a in activities]

        prev_week_start = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        prev_activities = db.execute(
            'SELECT COUNT(*) as c FROM activity_log WHERE user_id = ? AND consumed_at >= ? AND consumed_at < ?',
            (user_id, prev_week_start, week_ago)
        ).fetchone()['c']

        trend = 'up' if len(activities) > prev_activities else ('down' if len(activities) < prev_activities else 'same')

        return jsonify({
            'period_start': week_ago,
            'total_consumed': len(activities),
            'by_type': dict(type_counter),
            'ai_queries': ai_queries,
            'new_favorites': new_favorites,
            'new_ratings': new_ratings,
            'trend': trend,
            'prev_week_count': prev_activities,
            'activities': activity_list[:20],
        })
    except Exception:
        logger.exception('Error building weekly recap for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


# ==================== NOTIFICATIONS ====================

@assistant_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Return the user's notifications with unread count."""
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 30, type=int)
    db = get_db()
    try:
        rows = db.execute(
            'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()
        unread = db.execute(
            'SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0',
            (user_id,)
        ).fetchone()['c']
        return jsonify({'notifications': [dict(r) for r in rows], 'unread': unread})
    except Exception:
        logger.exception('Error fetching notifications for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/notifications/read', methods=['PUT'])
@jwt_required()
def mark_notifications_read():
    """Mark one or all notifications as read for the user."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    db = get_db()
    try:
        if 'id' in data:
            db.execute('UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?',
                       (data['id'], user_id))
        else:
            db.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user_id,))
        db.commit()
        return jsonify({'status': 'ok'})
    except Exception:
        logger.exception('Error marking notifications read for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/notifications/clear', methods=['DELETE'])
@jwt_required()
def clear_notifications():
    """Delete all read notifications for the user."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute('DELETE FROM notifications WHERE user_id = ? AND is_read = 1', (user_id,))
        db.commit()
        return jsonify({'status': 'cleared'})
    except Exception:
        logger.exception('Error clearing notifications for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


# ==================== REMINDERS ====================

@assistant_bp.route('/reminders', methods=['GET'])
@jwt_required()
def get_reminders():
    """Return all pending (not done) reminders for the user."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        rows = db.execute(
            'SELECT * FROM reminders WHERE user_id = ? AND is_done = 0 ORDER BY remind_at ASC',
            (user_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        logger.exception('Error fetching reminders for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/reminders', methods=['POST'])
@jwt_required()
def add_reminder():
    """Create a new reminder for a specific item."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    valid, err = validate_string(data.get('title'), field_name='title')
    if not valid:
        return jsonify({'error': err}), 400

    valid, err = validate_timestamp(data.get('remind_at', ''))
    if not valid:
        return jsonify({'error': err}), 400

    db = get_db()
    try:
        db.execute('''
            INSERT INTO reminders (user_id, item_type, item_id, title, remind_at, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, data.get('item_type', ''), data.get('item_id', ''),
              data['title'], data['remind_at'], data.get('note', '')))
        db.commit()

        _create_notification(db, user_id, 'reminder',
                             get_message('reminder_created'),
                             get_message('reminder_about', title=data['title']))
        return jsonify({'status': 'created'})
    except Exception:
        logger.exception('Error adding reminder for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/reminders/<int:reminder_id>', methods=['PUT'])
@jwt_required()
def complete_reminder(reminder_id):
    """Mark a reminder as done."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute('UPDATE reminders SET is_done = 1 WHERE id = ? AND user_id = ?',
                   (reminder_id, user_id))
        db.commit()
        return jsonify({'status': 'done'})
    except Exception:
        logger.exception('Error completing reminder %s for user %s', reminder_id, user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


@assistant_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
@jwt_required()
def delete_reminder(reminder_id):
    """Delete a reminder by its ID."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?',
                   (reminder_id, user_id))
        db.commit()
        return jsonify({'status': 'deleted'})
    except Exception:
        logger.exception('Error deleting reminder %s for user %s', reminder_id, user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


# ==================== DAILY PICKS ====================

@assistant_bp.route('/daily-picks', methods=['GET'])
@jwt_required()
def daily_picks():
    """Return daily picks including due reminders, top watchlist items, streak, and pinned content."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        reminders_due = db.execute(
            "SELECT * FROM reminders WHERE user_id = ? AND is_done = 0 AND date(remind_at) <= date('now') ORDER BY remind_at ASC LIMIT 5",
            (user_id,)
        ).fetchall()

        watchlist_items = db.execute(
            'SELECT * FROM watchlist WHERE user_id = ? ORDER BY priority DESC, created_at DESC LIMIT 5',
            (user_id,)
        ).fetchall()

        recent_activity = db.execute(
            'SELECT COUNT(*) as c FROM activity_log WHERE user_id = ? AND date(consumed_at) = ?',
            (user_id, today)
        ).fetchone()['c']

        streak = _calculate_streak(db, user_id)

        prefs = db.execute(
            'SELECT * FROM ai_preferences WHERE user_id = ?', (user_id,)
        ).fetchone()

        fav_cats = []
        if prefs and prefs['favorite_categories']:
            fav_cats = [c.strip() for c in prefs['favorite_categories'].split(',') if c.strip()]

        pinned = db.execute(
            'SELECT * FROM admin_pinned WHERE is_active = 1 ORDER BY created_at DESC LIMIT 3'
        ).fetchall()

        return jsonify({
            'date': today,
            'reminders_due': [dict(r) for r in reminders_due],
            'watchlist_top': [dict(w) for w in watchlist_items],
            'today_activity_count': recent_activity,
            'streak': streak,
            'favorite_categories': fav_cats,
            'pinned_recommendations': [dict(p) for p in pinned],
        })
    except Exception:
        logger.exception('Error fetching daily picks for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


# ==================== ASSISTANT SUMMARY ====================

@assistant_bp.route('/summary', methods=['GET'])
@jwt_required()
def assistant_summary():
    """Return main assistant dashboard data with aggregated counts and streak."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        stats = db.execute('''
            SELECT
                (SELECT COUNT(*) FROM activity_log WHERE user_id = ?) as total_consumed,
                (SELECT COUNT(*) FROM favorites WHERE user_id = ?) as total_favorites,
                (SELECT COUNT(*) FROM watchlist WHERE user_id = ?) as total_watchlist,
                (SELECT COUNT(*) FROM ai_history WHERE user_id = ?) as total_ai,
                (SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0) as unread_notifs,
                (SELECT COUNT(*) FROM reminders WHERE user_id = ? AND is_done = 0 AND date(remind_at) <= date('now')) as pending_reminders
        ''', (user_id,) * 6).fetchone()

        streak = _calculate_streak(db, user_id)

        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        week_consumed = db.execute(
            'SELECT COUNT(*) as c FROM activity_log WHERE user_id = ? AND consumed_at >= ?',
            (user_id, week_ago)
        ).fetchone()['c']

        type_counts = db.execute(
            'SELECT item_type, COUNT(*) as c FROM activity_log WHERE user_id = ? GROUP BY item_type',
            (user_id,)
        ).fetchall()

        return jsonify({
            'total_consumed': stats['total_consumed'],
            'total_favorites': stats['total_favorites'],
            'total_watchlist': stats['total_watchlist'],
            'total_ai_queries': stats['total_ai'],
            'unread_notifications': stats['unread_notifs'],
            'pending_reminders': stats['pending_reminders'],
            'streak': streak,
            'week_consumed': week_consumed,
            'consumed_by_type': {r['item_type']: r['c'] for r in type_counts},
        })
    except Exception:
        logger.exception('Error building assistant summary for user %s', user_id)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()


# ==================== HELPERS ====================

def _calculate_streak(db, user_id):
    """Calculate the user's consecutive-day activity streak."""
    rows = db.execute(
        "SELECT DISTINCT date(consumed_at) as d FROM activity_log WHERE user_id = ? ORDER BY d DESC LIMIT 60",
        (user_id,)
    ).fetchall()
    if not rows:
        return 0
    dates = [r['d'] for r in rows]
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    if dates[0] != today and dates[0] != yesterday:
        return 0
    streak = 1
    for i in range(1, len(dates)):
        prev = datetime.strptime(dates[i - 1], '%Y-%m-%d')
        curr = datetime.strptime(dates[i], '%Y-%m-%d')
        if (prev - curr).days == 1:
            streak += 1
        else:
            break
    return streak


def _create_notification(db, user_id, ntype, title, message, link=None):
    """Insert a notification record for the user."""
    db.execute(
        'INSERT INTO notifications (user_id, type, title, message, link) VALUES (?, ?, ?, ?, ?)',
        (user_id, ntype, title, message, link)
    )
    db.commit()
