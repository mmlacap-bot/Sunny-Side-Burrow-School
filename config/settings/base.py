"""
Base Django settings for enroll_project project.
All environment-specific settings inherit from this.
"""

import os
from pathlib import Path
import environ

# Initialize environment variables from .env file
env = environ.Env(
    DEBUG=(bool, False),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
)

# Build paths
# __file__ is at: enroll_final_project/config/settings/base.py
# Resolve to get: enroll_final_project/config/settings
# .parent gives: enroll_final_project/config
# .parent.parent gives: enroll_final_project (PROJECT_DIR/BASE_DIR)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
environ.Env.read_env(BASE_DIR / '.env')

# Security & Secrets
SECRET_KEY = env(
    'DJANGO_SECRET_KEY',
    default='django-insecure-change-me-before-deploy'
)
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=['127.0.0.1', 'localhost']
)

# ============================================================================
# BUSINESS LOGIC CONSTANTS
# ============================================================================

# Finance
DEFAULT_TUITION_FEE = 10000  # Default tuition fee in PHP

# Academic Configuration
SECTION_DEFAULT_CAPACITY = 40  # Maximum students per section
SECTION_MIN_CAPACITY = 10      # Minimum students to open a section

# ID Prefixes
STUDENT_ID_PREFIX = "S"
PROFESSOR_ID_PREFIX = "P"

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.student.apps.StudentConfig',
    # New modular app structure
    'apps.accounts',
    'apps.academics',
    'apps.enrollment',
    'apps.finance',
    'apps.support',
    'apps.ai_assistant',
    'apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'enroll_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.csrf',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'enroll_project.wsgi.application'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# ============================================================================
# DATABASE CONFIGURATION (OVERRIDE IN dev.py or prod.py)
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================================
# INTERNATIONALIZATION
# ============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TIME_ZONE', default='Asia/Singapore')
USE_I18N = True
USE_TZ = True

# ============================================================================
# STATIC & MEDIA FILES
# ============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env(
    'DEFAULT_FROM_EMAIL',
    default='no-reply@sunnysideburrow.edu'
)
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')

# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/student_dashboard/'
LOGOUT_REDIRECT_URL = '/'
