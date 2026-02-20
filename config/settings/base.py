"""
Django E-commerce - Base Settings
Seguridad y configuración base siguiendo mejores prácticas
"""
import os
from pathlib import Path

os.environ.setdefault('DJANGO_ENV', 'development')

import environ

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    SECRET_KEY=(str, ''),
    DATABASE_URL=(str, 'sqlite:///db.sqlite3'),
    PRODUCTS_API_URL=(str, ''),
    PRODUCTS_API_KEY=(str, ''),
    ERP_API_URL=(str, ''),
    ERP_API_KEY=(str, ''),
    # Wompi
    WOMPI_ENV=(str, 'sandbox'),
    WOMPI_PUBLIC_KEY=(str, ''),
    WOMPI_PRIVATE_KEY=(str, ''),
    WOMPI_INTEGRITY_SECRET=(str, ''),
    WOMPI_EVENTS_SECRET=(str, ''),
)

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / 'apps'

# Read .env file
environ.Env.read_env(BASE_DIR / '.env')

# SECURITY
SECRET_KEY = env('SECRET_KEY') or 'django-insecure-CHANGE-THIS-IN-PRODUCTION-use-env'
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'allauth',
    'django_ckeditor_5',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_htmx',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.products',
    'apps.cart',
    'apps.orders',
    'apps.coupons',
    'apps.payments',
    'apps.integrations',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
SITE_ID = 1

# Templates - Boskery
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            # Permite renderizar directamente los HTML demo de Boskery (p.ej. index-dark.html)
            BASE_DIR / 'boskery' / 'files',
        ],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.cart.context_processors.cart',
                'apps.core.context_processors.site_settings',
                'apps.core.context_processors.django_messages_json',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# Password validation - Security
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'boskery' / 'files',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User
AUTH_USER_MODEL = 'accounts.User'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Django Allauth - login con email únicamente
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_FORMS = {'signup': 'apps.accounts.forms.CustomSignupForm'}
ACCOUNT_ADAPTER = 'apps.accounts.adapters.CustomAccountAdapter'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Security Settings (Production)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# API Integrations
PRODUCTS_API_URL = env('PRODUCTS_API_URL')
PRODUCTS_API_KEY = env('PRODUCTS_API_KEY')
ERP_API_URL = env('ERP_API_URL')
ERP_API_KEY = env('ERP_API_KEY')

# Wompi payment gateway (Colombia)
# Obtén tus llaves en: https://comercios.wompi.co/
WOMPI_ENV              = env('WOMPI_ENV')              # 'sandbox' | 'production'
WOMPI_PUBLIC_KEY       = env('WOMPI_PUBLIC_KEY')       # pub_test_xxx  / pub_prod_xxx
WOMPI_PRIVATE_KEY      = env('WOMPI_PRIVATE_KEY')      # prv_test_xxx  / prv_prod_xxx
WOMPI_INTEGRITY_SECRET = env('WOMPI_INTEGRITY_SECRET') # Llave de integridad (firma del formulario)
WOMPI_EVENTS_SECRET    = env('WOMPI_EVENTS_SECRET')    # Llave de eventos (firma del webhook)

# Cart session key
CART_SESSION_ID = 'cart'

# CKEditor 5 - editor HTML para descripciones
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', '|',
            'link', 'bulletedList', 'numberedList', '|',
            'blockQuote', 'insertImage', '|',
            'outdent', 'indent', '|',
            'sourceEditing',
        ],
        'language': 'es',
    },
}
CKEDITOR_5_FILE_UPLOAD_PERMISSION = 'staff'
