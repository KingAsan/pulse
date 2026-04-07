"""AI chat routes — recommendation engine, sessions, feedback, preferences."""

import json
import logging
import asyncio
from collections import Counter
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from services.gemini_service import get_recommendation, get_ai_prefs

logger = logging.getLogger(__name__)
ai_chat_bp = Blueprint('ai_chat', __name__)


@ai_chat_bp.route('/recommend', methods=['POST'])
@jwt_required()
def recommend():
    """Generate AI-powered entertainment recommendations."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    query = data.get('query', '').strip()
    session_id = data.get('session_id', '')
    mood = data.get('mood')
    company = data.get('company')
    time_minutes = data.get('time_minutes')
    assistant_mode = data.get('assistant_mode', 'balanced')
    temporary = data.get('temporary', False)

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            get_recommendation(user_id, query, session_id, mood, company, time_minutes, assistant_mode, temporary)
        )
    finally:
        loop.close()

    return jsonify(result)


@ai_chat_bp.route('/plan-evening', methods=['POST'])
@jwt_required()
def plan_evening():
    """Generate a personalized evening entertainment plan."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    mood = data.get('mood', 'relax')
    company = data.get('company', 'solo')
    time_minutes = data.get('time_minutes', 180)

    query = f"Составь идеальный план вечера. Настроение: {mood}. Компания: {company}. Свободное время: {time_minutes} минут. Подбери: 1 фильм или сериал, 3 музыкальных трека для фона, 1 книгу если останется время. Для каждого обязательно укажи title, category, description, year_genre, why_this."
    session_id = f"evening_{user_id}_{int(__import__('time').time())}"

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            get_recommendation(user_id, query, session_id, mood, company, time_minutes, 'deep', False)
        )
    finally:
        loop.close()
    return jsonify(result)


@ai_chat_bp.route('/sessions')
@jwt_required()
def get_sessions():
    """List all AI chat sessions for the current user."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        rows = db.execute(
            'SELECT session_id, user_query, ai_response_json, timestamp FROM ai_history WHERE user_id = ? ORDER BY timestamp DESC',
            (user_id,)
        ).fetchall()

        sessions = {}
        for row in rows:
            sid = row['session_id']
            if not sid:
                continue
            if sid not in sessions:
                preview = ''
                if row['ai_response_json']:
                    try:
                        payload = json.loads(row['ai_response_json'])
                        if isinstance(payload, list) and payload:
                            preview = payload[0].get('title', '')
                    except Exception:
                        pass
                sessions[sid] = {
                    'session_id': sid,
                    'title': row['user_query'] or 'Новый чат',
                    'message_count': 0,
                    'last_timestamp': row['timestamp'],
                    'preview': preview,
                }
            sessions[sid]['message_count'] += 1

        result = sorted(sessions.values(), key=lambda x: x['last_timestamp'] or '', reverse=True)
        return jsonify(result)
    finally:
        db.close()


@ai_chat_bp.route('/chat/<session_id>')
@jwt_required()
def get_chat(session_id):
    """Retrieve full message history for a specific session."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        rows = db.execute(
            'SELECT * FROM ai_history WHERE session_id = ? AND user_id = ? ORDER BY id',
            (session_id, user_id)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@ai_chat_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Record user feedback (like/dislike/watched) on a recommendation."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    feedback_type = (data.get('feedback_type') or '').strip().lower()
    if feedback_type not in ('like', 'dislike', 'watched'):
        return jsonify({'error': 'feedback_type: like/dislike/watched'}), 400
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'title обязателен'}), 400

    db = get_db()
    try:
        exists = db.execute(
            'SELECT id FROM ai_feedback WHERE user_id = ? AND title = ? AND feedback_type = ? AND session_id = ?',
            (user_id, title, feedback_type, data.get('session_id', ''))
        ).fetchone()
        if exists:
            return jsonify({'status': 'ok', 'created': False})

        db.execute(
            'INSERT INTO ai_feedback (user_id, session_id, query_text, title, category, feedback_type) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, data.get('session_id'), data.get('query_text'), title,
             data.get('category'), feedback_type)
        )
        db.commit()
        return jsonify({'status': 'ok', 'created': True})
    finally:
        db.close()


@ai_chat_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get AI personalization preferences for the current user."""
    user_id = int(get_jwt_identity())
    return jsonify(get_ai_prefs(user_id))


@ai_chat_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Update AI personalization preferences."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    db = get_db()
    try:
        db.execute('''
            INSERT OR REPLACE INTO ai_preferences
            (user_id, favorite_categories, disliked_categories, favorite_platforms,
             preferred_language, age_rating, discovery_mode, onboarding_completed)
            VALUES (?,
                (SELECT COALESCE((SELECT favorite_categories FROM ai_preferences WHERE user_id = ?), '')),
                (SELECT COALESCE((SELECT disliked_categories FROM ai_preferences WHERE user_id = ?), '')),
                (SELECT COALESCE((SELECT favorite_platforms FROM ai_preferences WHERE user_id = ?), '')),
                ?, ?, ?,
                (SELECT COALESCE((SELECT onboarding_completed FROM ai_preferences WHERE user_id = ?), 0)))
        ''', (user_id, user_id, user_id, user_id,
              data.get('preferred_language', 'ru'),
              data.get('age_rating', 'any'),
              data.get('discovery_mode', 'balanced'), user_id))

        if 'favorite_categories' in data:
            db.execute('UPDATE ai_preferences SET favorite_categories = ? WHERE user_id = ?',
                       (', '.join(data['favorite_categories']), user_id))
        if 'disliked_categories' in data:
            db.execute('UPDATE ai_preferences SET disliked_categories = ? WHERE user_id = ?',
                       (', '.join(data['disliked_categories']), user_id))
        if 'favorite_platforms' in data:
            db.execute('UPDATE ai_preferences SET favorite_platforms = ? WHERE user_id = ?',
                       (', '.join(data['favorite_platforms']), user_id))
        db.commit()
        return jsonify(get_ai_prefs(user_id))
    finally:
        db.close()


@ai_chat_bp.route('/onboarding/status')
@jwt_required()
def onboarding_status():
    """Check if user has completed AI onboarding."""
    user_id = int(get_jwt_identity())
    prefs = get_ai_prefs(user_id)
    return jsonify({'completed': prefs['onboarding_completed']})


@ai_chat_bp.route('/onboarding/complete', methods=['PUT'])
@jwt_required()
def complete_onboarding():
    """Complete AI onboarding and save initial preferences."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    db = get_db()
    try:
        fav = ', '.join(data.get('favorite_categories', []))
        dis = ', '.join(data.get('disliked_categories', []))
        plat = ', '.join(data.get('favorite_platforms', []))
        db.execute('''
            INSERT OR REPLACE INTO ai_preferences
            (user_id, favorite_categories, disliked_categories, favorite_platforms,
             preferred_language, age_rating, discovery_mode, onboarding_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (user_id, fav, dis, plat,
              data.get('preferred_language', 'ru'),
              data.get('age_rating', 'any'),
              data.get('discovery_mode', 'balanced')))
        db.commit()
        return jsonify({'completed': True})
    finally:
        db.close()


@ai_chat_bp.route('/insights')
@jwt_required()
def get_insights():
    """Get AI usage statistics and analytics for the current user."""
    user_id = int(get_jwt_identity())
    db = get_db()
    try:
        total_queries = db.execute('SELECT COUNT(*) as c FROM ai_history WHERE user_id = ?', (user_id,)).fetchone()['c']
        sessions_count = db.execute('SELECT COUNT(DISTINCT session_id) as c FROM ai_history WHERE user_id = ?', (user_id,)).fetchone()['c']

        total_recs = 0
        cat_counter = Counter()
        rows = db.execute('SELECT ai_response_json FROM ai_history WHERE user_id = ?', (user_id,)).fetchall()
        for row in rows:
            if not row['ai_response_json']:
                continue
            try:
                payload = json.loads(row['ai_response_json'])
                if isinstance(payload, list):
                    for item in payload:
                        total_recs += 1
                        cat = (item.get('category') or '').strip()
                        if cat:
                            cat_counter[cat] += 1
            except Exception:
                pass

        fb_rows = db.execute('SELECT feedback_type FROM ai_feedback WHERE user_id = ?', (user_id,)).fetchall()
        fb_counter = Counter((r['feedback_type'] or '').lower() for r in fb_rows)
        top_cats = [name for name, _ in cat_counter.most_common(3)]

        setting = db.execute("SELECT value FROM admin_settings WHERE key = 'default_daily_limit'").fetchone()
        daily_limit = int(setting['value']) if setting else 40
        user = db.execute("SELECT daily_limit FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user['daily_limit']:
            daily_limit = user['daily_limit']
        today = db.execute(
            "SELECT COUNT(*) as c FROM ai_history WHERE user_id = ? AND date(timestamp) = date('now')",
            (user_id,)
        ).fetchone()['c']

        return jsonify({
            'total_queries': total_queries,
            'total_sessions': sessions_count,
            'total_recommendations': total_recs,
            'top_categories': top_cats,
            'favorite_category': top_cats[0] if top_cats else 'Нет данных',
            'feedback_likes': fb_counter.get('like', 0),
            'feedback_dislikes': fb_counter.get('dislike', 0),
            'feedback_watched': fb_counter.get('watched', 0),
            'daily_limit': daily_limit,
            'queries_today': today,
            'remaining_today': max(0, daily_limit - today),
        })
    finally:
        db.close()
