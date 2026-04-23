"""
Development Django settings for enroll_project.
Extends base.py with development-specific configurations.
"""

from .base import *

# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Development uses SQLite (no override needed, base.py default is used)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================================================
# EMAIL CONFIGURATION FOR DEVELOPMENT
# ============================================================================

# Use SMTP in development by default so registration emails can be delivered.
# Override this with EMAIL_BACKEND in .env if needed.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

# Development tools (add more as needed)
if 'django_extensions' in INSTALLED_APPS or True:
    SHELL_PLUS_IMPORTS = [
        'from apps.academics.models import *',
        'from apps.accounts.models import *',
        'from apps.student.models import *',
    ]

# Weak security settings for development only
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
