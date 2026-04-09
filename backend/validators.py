"""Input validation utilities for API request data."""

import re
from datetime import datetime

VALID_ITEM_TYPES = {'movie', 'book', 'music', 'event', 'series', 'ai_rec', 'game', 'anime'}

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def validate_email(email):
    if not email or not EMAIL_REGEX.match(email):
        return False, 'Invalid email format'
    return True, None


def validate_password(password):
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'
    if len(password) > 128:
        return False, 'Password must be at most 128 characters'
    if not re.search(r'[A-ZА-ЯЁ]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit'
    return True, None


def validate_item_type(item_type):
    if item_type not in VALID_ITEM_TYPES:
        return False, f'Invalid item_type. Must be one of: {", ".join(sorted(VALID_ITEM_TYPES))}'
    return True, None


def validate_string(value, field_name='field', max_len=500):
    if not value or not isinstance(value, str):
        return False, f'{field_name} is required'
    if len(value) > max_len:
        return False, f'{field_name} must be at most {max_len} characters'
    return True, None


def validate_timestamp(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return True, None
    except (ValueError, AttributeError):
        return False, 'Invalid timestamp format. Use ISO 8601'


def validate_rating(rating):
    try:
        r = int(rating)
        if 1 <= r <= 5:
            return True, None
        return False, 'Rating must be between 1 and 5'
    except (ValueError, TypeError):
        return False, 'Rating must be an integer between 1 and 5'
