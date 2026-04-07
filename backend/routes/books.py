"""Book routes — trending, search, details, subject browsing."""

import logging
from flask import Blueprint, request, jsonify
from services.openlibrary_service import openlibrary_service

logger = logging.getLogger(__name__)
books_bp = Blueprint('books', __name__)


@books_bp.route('/trending')
def trending():
    """Get trending books with randomized results."""
    try:
        return jsonify(openlibrary_service.get_trending())
    except Exception as e:
        logger.exception('Error fetching trending books')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@books_bp.route('/search')
def search():
    """Search books by query string."""
    q = request.args.get('q', '')
    start = request.args.get('start', 0, type=int)
    if not q:
        return jsonify([])
    try:
        return jsonify(openlibrary_service.search(q, start_index=start))
    except Exception as e:
        logger.exception('Error searching books: q=%s', q)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@books_bp.route('/detail/<path:key>')
def book_detail(key):
    """Get detailed information about a specific book."""
    try:
        if not key.startswith('/'):
            key = '/' + key
        book = openlibrary_service.get_book(key)
        if not book:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(book)
    except Exception as e:
        logger.exception('Error fetching book %s', key)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@books_bp.route('/subjects/<subject>')
def by_subject(subject):
    """Browse books by subject category."""
    try:
        start = request.args.get('start', 0, type=int)
        return jsonify(openlibrary_service.get_by_subject(subject, start_index=start))
    except Exception as e:
        logger.exception('Error fetching subject %s', subject)
        return jsonify({'error': 'Service temporarily unavailable'}), 503
