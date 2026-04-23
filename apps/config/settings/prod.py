"""
Production Django settings for enroll_project.
Extends base.py with production-specific configurations.
"""

from .base import *

# ============================================================================
# PRODUCTION SETTINGS
# ============================================================================

DEBUG = False

# Restrict allowed hosts in production
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ============================================================================
# POSTGRESQL DATABASE CONFIGURATION
# ============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="enrollment_db"),
        "USER": env("DB_USER", default="enrollment_user"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env.int("DB_PORT", default=5432),
        # Connection pooling and optimization
        "CONN_MAX_AGE": 600,  # 10 minutes
        "OPTIONS": {
            "connect_timeout": 10,
        }
    }
}

# ============================================================================
# SECURITY SETTINGS FOR PRODUCTION
# ============================================================================

# HTTPS/SSL
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "cdn.jsdelivr.net"),
    "style-src": ("'self'", "cdn.jsdelivr.net", "'unsafe-inline'"),
    "img-src": ("'self'", "data:", "https:"),
}

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Prevent clickjacking
X_FRAME_OPTIONS = 'DENY'

# ============================================================================
# EMAIL CONFIGURATION FOR PRODUCTION
# ============================================================================

# Override with SMTP backend for production (base.py provides email credentials from env vars)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


# ============================================================================
# LOGGING FOR PRODUCTION
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(BASE_DIR / 'logs' / 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# ============================================================================
# CACHING (Optional - uncomment if using Redis)
# ============================================================================

# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# ============================================================================
# WHITENOISE (For serving static files in production)
# ============================================================================

# Uncomment if deploying with WhiteNoise
# MIDDLEWARE = [
#     'whitenoise.middleware.WhiteNoiseMiddleware',
# ] + MIDDLEWARE
#
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
