"""Bilingual message system for consistent API responses."""

MESSAGES = {
    # Auth
    'all_fields_required': {
        'ru': 'Все поля обязательны',
        'en': 'All fields are required',
    },
    'invalid_credentials': {
        'ru': 'Неверные учётные данные',
        'en': 'Invalid credentials',
    },
    'username_exists': {
        'ru': 'Имя пользователя или email уже существует',
        'en': 'Username or email already exists',
    },
    'account_blocked': {
        'ru': 'Аккаунт заблокирован',
        'en': 'Account is blocked',
    },

    # Admin
    'admin_required': {
        'ru': 'Требуются права администратора',
        'en': 'Admin access required',
    },
    'user_not_found': {
        'ru': 'Пользователь не найден',
        'en': 'User not found',
    },
    'cannot_remove_self_admin': {
        'ru': 'Нельзя снять admin с себя',
        'en': 'Cannot remove admin from yourself',
    },

    # Validation
    'title_required': {
        'ru': 'Название обязательно',
        'en': 'Title is required',
    },
    'title_category_required': {
        'ru': 'Название или категория обязательны',
        'en': 'Title or category required',
    },
    'title_description_required': {
        'ru': 'Название и описание обязательны',
        'en': 'Title and description required',
    },
    'invalid_item_type': {
        'ru': 'Неверный тип элемента',
        'en': 'Invalid item type',
    },
    'invalid_rating': {
        'ru': 'Рейтинг должен быть от 1 до 5',
        'en': 'Rating must be between 1 and 5',
    },
    'missing_required_fields': {
        'ru': 'Отсутствуют обязательные поля',
        'en': 'Missing required fields',
    },
    'invalid_timestamp': {
        'ru': 'Неверный формат даты',
        'en': 'Invalid timestamp format',
    },

    # Activity
    'activity_logged': {
        'ru': 'Отмечено!',
        'en': 'Logged!',
    },
    'added_to_history': {
        'ru': '"{title}" добавлено в историю просмотров',
        'en': '"{title}" added to watch history',
    },

    # Reminders
    'reminder_created': {
        'ru': 'Напоминание создано',
        'en': 'Reminder created',
    },
    'reminder_about': {
        'ru': 'Напомним о "{title}"',
        'en': 'Reminder set for "{title}"',
    },

    # General
    'no_data': {
        'ru': 'Нет данных',
        'en': 'No data',
    },
    'not_found': {
        'ru': 'Не найдено',
        'en': 'Not found',
    },
    'service_unavailable': {
        'ru': 'Сервис временно недоступен',
        'en': 'Service temporarily unavailable',
    },
    'internal_error': {
        'ru': 'Внутренняя ошибка сервера',
        'en': 'Internal server error',
    },
}


def get_message(key, lang='en', **kwargs):
    """Get a localized message by key with optional template substitution."""
    msg_dict = MESSAGES.get(key, {})
    msg = msg_dict.get(lang, msg_dict.get('en', key))
    if kwargs:
        msg = msg.format(**kwargs)
    return msg
