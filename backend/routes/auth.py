"""Authentication routes — registration, login, user session management."""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from validators import validate_email, validate_password

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


def _get_limiter():
    from app import limiter
    return limiter


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    ok, err = validate_email(email)
    if not ok:
        return jsonify({'error': err}), 400

    ok, err = validate_password(password)
    if not ok:
        return jsonify({'error': err}), 400

    db = get_db()
    try:
        user_count = db.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        is_admin = 1 if user_count == 0 else 0

        db.execute(
            'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
            (username, email, generate_password_hash(password), is_admin)
        )
        db.commit()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        token = create_access_token(identity=str(user['id']))
        logger.info('User registered: %s (id=%d)', username, user['id'])
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'], 'username': user['username'], 'email': user['email'],
                'is_admin': bool(user['is_admin']),
            }
        }), 201
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': 'Username or email already exists'}), 409
        logger.exception('Registration error for %s', username)
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    db = get_db()
    try:
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            logger.warning('Failed login attempt for: %s', username)
            return jsonify({'error': 'Invalid credentials'}), 401

        if user['is_blocked']:
            logger.warning('Blocked user login attempt: %s', username)
            return jsonify({'error': 'Account is blocked'}), 403

        token = create_access_token(identity=str(user['id']))
        logger.info('User logged in: %s (id=%d)', username, user['id'])
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'], 'username': user['username'], 'email': user['email'],
                'is_admin': bool(user['is_admin']),
            }
        })
    finally:
        db.close()


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    db = get_db()
    try:
        user = db.execute('SELECT id, username, email, is_admin, is_blocked, created_at FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user['is_blocked']:
            return jsonify({'error': 'Account is blocked'}), 403
        return jsonify(dict(user))
    finally:
        db.close()
