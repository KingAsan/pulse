import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', '')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)

    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH',
                                   os.path.join(os.path.dirname(__file__), 'entertainment.db'))

    # External APIs
    KINOPOISK_API_KEY = os.environ.get('KINOPOISK_API_KEY', '')
    KINOPOISK_BASE_URL = 'https://api.kinopoisk.dev'
    GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY', '')
    GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    GEMINI_PRIMARY_MODEL = os.environ.get('GEMINI_PRIMARY_MODEL', 'gemini-2.5-flash')
    GEMINI_FALLBACK_MODEL = os.environ.get('GEMINI_FALLBACK_MODEL', 'gemini-2.0-flash-lite')

    # Limits
    DEFAULT_DAILY_LIMIT = int(os.environ.get('DEFAULT_DAILY_LIMIT', '40'))

    # CORS — configurable via env, falls back to localhost for development
    CORS_ORIGINS = [
        o.strip() for o in os.environ.get(
            'CORS_ORIGINS',
            'http://localhost:5000,http://127.0.0.1:5000,http://localhost:5173,http://127.0.0.1:5173'
        ).split(',') if o.strip()
    ]

    @classmethod
    def validate(cls):
        """Validate required environment variables on startup."""
        missing = []
        if not cls.SECRET_KEY:
            missing.append('SECRET_KEY')
        if not cls.JWT_SECRET_KEY:
            missing.append('JWT_SECRET_KEY')
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}. "
                             f"Copy .env.example to .env and fill in the values.")
        warnings = []
        if not cls.KINOPOISK_API_KEY:
            warnings.append('KINOPOISK_API_KEY')
        if not cls.GOOGLE_BOOKS_API_KEY:
            warnings.append('GOOGLE_BOOKS_API_KEY')
        if not cls.GEMINI_API_KEY:
            warnings.append('GOOGLE_API_KEY')
        if warnings:
            import logging
            logging.getLogger(__name__).warning(
                'Optional API keys not set: %s — some features will be limited', ', '.join(warnings)
            )
