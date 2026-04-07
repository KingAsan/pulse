import logging
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.recommendation_engine import recommendation_engine

logger = logging.getLogger(__name__)

recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.route('/for-you')
@jwt_required()
def for_you():
    """Return personalized recommendations for the current user."""
    user_id = get_jwt_identity()
    try:
        return jsonify(recommendation_engine.get_for_you(user_id))
    except Exception:
        logger.exception('Error generating for-you recommendations for user %s', user_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@recommendations_bp.route('/taste')
@jwt_required()
def taste():
    """Return a summary of the user's taste profile based on their activity."""
    user_id = get_jwt_identity()
    try:
        return jsonify(recommendation_engine.get_taste_summary(user_id))
    except Exception:
        logger.exception('Error generating taste summary for user %s', user_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@recommendations_bp.route('/because-you-liked/<item_type>/<item_id>')
@jwt_required()
def because_you_liked(item_type, item_id):
    """Return recommendations based on a specific item the user liked."""
    user_id = get_jwt_identity()
    try:
        return jsonify(recommendation_engine.because_you_liked(user_id, item_type, item_id))
    except Exception:
        logger.exception('Error generating because-you-liked for user %s, %s/%s', user_id, item_type, item_id)
        return jsonify({'error': 'Service temporarily unavailable'}), 503
