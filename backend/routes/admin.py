"""Admin panel routes — user management, content rules, settings, audit log, exports."""

import json
import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)


def _audit_log(db, admin_id, action, target_type='', target_id=None, details=''):
    db.execute(
        'INSERT INTO admin_audit_log (admin_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)',
        (admin_id, action, target_type, target_id, details)
    )
    db.commit()
    logger.info('Admin action: admin_id=%s action=%s target=%s:%s', admin_id, action, target_type, target_id)


def require_admin(f):
    from functools import wraps
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        db = get_db()
        try:
            user = db.execute('SELECT is_admin, is_blocked FROM users WHERE id = ?', (user_id,)).fetchone()
            if not user or not user['is_admin'] or user['is_blocked']:
                return jsonify({'error': 'Admin access required'}), 403
        finally:
            db.close()
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/stats')
@require_admin
def stats():
    db = get_db()
    try:
        users_total = db.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        users_admins = db.execute('SELECT COUNT(*) as c FROM users WHERE is_admin = 1').fetchone()['c']
        users_blocked = db.execute('SELECT COUNT(*) as c FROM users WHERE is_blocked = 1').fetchone()['c']
        queries_total = db.execute('SELECT COUNT(*) as c FROM ai_history').fetchone()['c']
        feedback_total = db.execute('SELECT COUNT(*) as c FROM ai_feedback').fetchone()['c']
        rules_total = db.execute('SELECT COUNT(*) as c FROM admin_content_rules').fetchone()['c']
        pinned_active = db.execute('SELECT COUNT(*) as c FROM admin_pinned WHERE is_active = 1').fetchone()['c']

        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        active_7d = db.execute(
            'SELECT COUNT(DISTINCT user_id) as c FROM ai_history WHERE timestamp >= ?', (seven_days_ago,)
        ).fetchone()['c']

        top_queries_rows = db.execute(
            'SELECT user_query, COUNT(*) as cnt FROM ai_history GROUP BY user_query ORDER BY cnt DESC LIMIT 8'
        ).fetchall()

        model_rows = db.execute(
            'SELECT model_name, COUNT(*) as cnt FROM api_usage WHERE model_name IS NOT NULL GROUP BY model_name ORDER BY cnt DESC LIMIT 10'
        ).fetchall()

        return jsonify({
            'users_total': users_total,
            'users_admins': users_admins,
            'users_blocked': users_blocked,
            'active_users_7d': active_7d,
            'queries_total': queries_total,
            'feedback_total': feedback_total,
            'content_rules_total': rules_total,
            'pinned_total_active': pinned_active,
            'top_queries': [{'query': r['user_query'], 'count': r['cnt']} for r in top_queries_rows],
            'model_usage': [{'model': r['model_name'], 'count': r['cnt']} for r in model_rows],
        })
    finally:
        db.close()


@admin_bp.route('/users')
@require_admin
def get_users():
    db = get_db()
    try:
        rows = db.execute('''
            SELECT u.id, u.username, u.email, u.is_admin, u.is_blocked, u.daily_limit,
                   COALESCE(h.hist_count, 0) as history_count,
                   COALESCE(fb.fb_count, 0) as feedback_count,
                   COALESCE(td.today_count, 0) as queries_today
            FROM users u
            LEFT JOIN (SELECT user_id, COUNT(*) as hist_count FROM ai_history GROUP BY user_id) h ON h.user_id = u.id
            LEFT JOIN (SELECT user_id, COUNT(*) as fb_count FROM ai_feedback GROUP BY user_id) fb ON fb.user_id = u.id
            LEFT JOIN (SELECT user_id, COUNT(*) as today_count FROM ai_history WHERE date(timestamp) = date('now') GROUP BY user_id) td ON td.user_id = u.id
            ORDER BY u.id
        ''').fetchall()
        return jsonify([{
            'id': r['id'], 'username': r['username'], 'email': r['email'],
            'is_admin': bool(r['is_admin']), 'is_blocked': bool(r['is_blocked']),
            'daily_limit': r['daily_limit'],
            'history_count': r['history_count'], 'feedback_count': r['feedback_count'],
            'queries_today': r['queries_today'],
        } for r in rows])
    finally:
        db.close()


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    data = request.get_json()
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user_id == admin_id and data.get('is_admin') is False:
            return jsonify({'error': 'Cannot remove admin from yourself'}), 400

        changes = []
        if 'is_admin' in data:
            db.execute('UPDATE users SET is_admin = ? WHERE id = ?', (1 if data['is_admin'] else 0, user_id))
            changes.append(f"is_admin={data['is_admin']}")
        if 'is_blocked' in data:
            db.execute('UPDATE users SET is_blocked = ? WHERE id = ?', (1 if data['is_blocked'] else 0, user_id))
            changes.append(f"is_blocked={data['is_blocked']}")
        if 'daily_limit' in data:
            db.execute('UPDATE users SET daily_limit = ? WHERE id = ?', (max(1, int(data['daily_limit'])), user_id))
            changes.append(f"daily_limit={data['daily_limit']}")
        db.commit()

        _audit_log(db, admin_id, 'update_user', 'user', user_id, '; '.join(changes))
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/users/<int:user_id>/history', methods=['DELETE'])
@require_admin
def reset_user_history(user_id):
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute('DELETE FROM ai_history WHERE user_id = ?', (user_id,))
        db.execute('DELETE FROM ai_feedback WHERE user_id = ?', (user_id,))
        db.execute('DELETE FROM api_usage WHERE user_id = ?', (user_id,))
        db.commit()
        _audit_log(db, admin_id, 'reset_history', 'user', user_id)
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/content-rules', methods=['GET'])
@require_admin
def get_rules():
    db = get_db()
    try:
        rows = db.execute('SELECT * FROM admin_content_rules ORDER BY created_at DESC').fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@admin_bp.route('/content-rules', methods=['POST'])
@require_admin
def create_rule():
    data = request.get_json()
    rule_type = (data.get('rule_type') or '').strip().lower()
    if rule_type not in ('blacklist', 'whitelist'):
        return jsonify({'error': 'rule_type: blacklist/whitelist'}), 400
    if not (data.get('title') or data.get('category')):
        return jsonify({'error': 'title or category required'}), 400
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute(
            'INSERT INTO admin_content_rules (title, category, rule_type, notes) VALUES (?, ?, ?, ?)',
            ((data.get('title') or '').strip() or None,
             (data.get('category') or '').strip() or None,
             rule_type, (data.get('notes') or '').strip() or None)
        )
        db.commit()
        _audit_log(db, admin_id, 'create_rule', 'content_rule', None, f"{rule_type}: {data.get('title') or data.get('category')}")
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/content-rules/<int:rule_id>', methods=['DELETE'])
@require_admin
def delete_rule(rule_id):
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute('DELETE FROM admin_content_rules WHERE id = ?', (rule_id,))
        db.commit()
        _audit_log(db, admin_id, 'delete_rule', 'content_rule', rule_id)
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/pinned', methods=['GET'])
@require_admin
def get_pinned():
    db = get_db()
    try:
        rows = db.execute('SELECT * FROM admin_pinned ORDER BY created_at DESC').fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@admin_bp.route('/pinned', methods=['POST'])
@require_admin
def create_pinned():
    data = request.get_json()
    if not data.get('title') or not data.get('description'):
        return jsonify({'error': 'title and description required'}), 400
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute(
            'INSERT INTO admin_pinned (title, year_genre, description, category, why_this, video_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (data['title'], data.get('year_genre'), data['description'],
             data.get('category'), data.get('why_this'), data.get('video_id'),
             1 if data.get('is_active', True) else 0)
        )
        db.commit()
        _audit_log(db, admin_id, 'create_pinned', 'pinned', None, data['title'])
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/pinned/<int:pinned_id>', methods=['PUT'])
@require_admin
def update_pinned(pinned_id):
    data = request.get_json()
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute(
            'UPDATE admin_pinned SET title=?, year_genre=?, description=?, category=?, why_this=?, video_id=?, is_active=? WHERE id=?',
            (data.get('title'), data.get('year_genre'), data.get('description'),
             data.get('category'), data.get('why_this'), data.get('video_id'),
             1 if data.get('is_active', True) else 0, pinned_id)
        )
        db.commit()
        _audit_log(db, admin_id, 'update_pinned', 'pinned', pinned_id)
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/pinned/<int:pinned_id>', methods=['DELETE'])
@require_admin
def delete_pinned(pinned_id):
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        db.execute('DELETE FROM admin_pinned WHERE id = ?', (pinned_id,))
        db.commit()
        _audit_log(db, admin_id, 'delete_pinned', 'pinned', pinned_id)
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/settings', methods=['GET'])
@require_admin
def get_settings():
    from config import Config
    db = get_db()
    try:
        force_lite = db.execute("SELECT value FROM admin_settings WHERE key = 'force_lite_mode'").fetchone()
        daily_limit = db.execute("SELECT value FROM admin_settings WHERE key = 'default_daily_limit'").fetchone()
        return jsonify({
            'force_lite_mode': (force_lite['value'] if force_lite else '0') in ('1', 'true'),
            'default_daily_limit': int(daily_limit['value']) if daily_limit else Config.DEFAULT_DAILY_LIMIT,
            'primary_model': Config.GEMINI_PRIMARY_MODEL,
            'fallback_model': Config.GEMINI_FALLBACK_MODEL,
        })
    finally:
        db.close()


@admin_bp.route('/settings', methods=['PUT'])
@require_admin
def update_settings():
    data = request.get_json()
    admin_id = int(get_jwt_identity())
    db = get_db()
    try:
        changes = []
        if 'force_lite_mode' in data:
            db.execute(
                "INSERT OR REPLACE INTO admin_settings (key, value, updated_at) VALUES ('force_lite_mode', ?, CURRENT_TIMESTAMP)",
                ('1' if data['force_lite_mode'] else '0',)
            )
            changes.append(f"force_lite_mode={data['force_lite_mode']}")
        if 'default_daily_limit' in data:
            db.execute(
                "INSERT OR REPLACE INTO admin_settings (key, value, updated_at) VALUES ('default_daily_limit', ?, CURRENT_TIMESTAMP)",
                (str(max(1, int(data['default_daily_limit']))),)
            )
            changes.append(f"default_daily_limit={data['default_daily_limit']}")
        db.commit()
        _audit_log(db, admin_id, 'update_settings', 'settings', None, '; '.join(changes))
        return jsonify({'status': 'ok'})
    finally:
        db.close()


@admin_bp.route('/audit-log')
@require_admin
def get_audit_log():
    limit = request.args.get('limit', 50, type=int)
    db = get_db()
    try:
        rows = db.execute('''
            SELECT a.*, u.username as admin_name
            FROM admin_audit_log a
            LEFT JOIN users u ON u.id = a.admin_id
            ORDER BY a.created_at DESC LIMIT ?
        ''', (limit,)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@admin_bp.route('/export')
@require_admin
def export_data():
    scope = request.args.get('scope', 'users').lower()
    fmt = request.args.get('format', 'json').lower()
    db = get_db()
    try:
        if scope == 'users':
            rows = db.execute('SELECT id, username, email, is_admin, is_blocked, daily_limit FROM users ORDER BY id').fetchall()
        elif scope == 'history':
            rows = db.execute('SELECT id, user_id, session_id, user_query, timestamp FROM ai_history ORDER BY timestamp DESC').fetchall()
        elif scope == 'feedback':
            rows = db.execute('SELECT id, user_id, title, category, feedback_type, timestamp FROM ai_feedback ORDER BY timestamp DESC').fetchall()
        elif scope == 'usage':
            rows = db.execute('SELECT * FROM api_usage ORDER BY created_at DESC').fetchall()
        else:
            return jsonify({'error': 'scope: users/history/feedback/usage'}), 400

        data = [dict(r) for r in rows]

        if fmt == 'csv' and data:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
            writer.writeheader()
            for row in data:
                writer.writerow(row)
            return Response(output.getvalue(), mimetype='text/csv',
                            headers={'Content-Disposition': f'attachment; filename=admin_{scope}.csv'})

        return Response(json.dumps(data, ensure_ascii=False, indent=2), mimetype='application/json',
                        headers={'Content-Disposition': f'attachment; filename=admin_{scope}.json'})
    finally:
        db.close()
