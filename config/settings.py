"""
Django settings for the project.

Single-file settings (no split base/development/production modules).
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import environ
from django.core.exceptions import ImproperlyConfigured


os.environ.setdefault('DJANGO_ENV', 'development')

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    SECRET_KEY=(str, ''),
    DATABASE_URL=(str, 'sqlite:///db.sqlite3'),
    PRODUCTS_API_URL=(str, ''),
    PRODUCTS_API_KEY=(str, ''),
    ERP_API_URL=(str, ''),
    ERP_API_KEY=(str, ''),
    STOCK_SYNC_API_KEY=(str, ''),
    WOMPI_ENV=(str, 'sandbox'),
    WOMPI_PUBLIC_KEY=(str, ''),
    WOMPI_PRIVATE_KEY=(str, ''),
    WOMPI_INTEGRITY_SECRET=(str, ''),
    WOMPI_EVENTS_SECRET=(str, ''),
    WOMPI_REDIRECT_URL=(str, ''),
    CSP_ALLOW_UNSAFE_EVAL=(bool, False),
    CSP_STRICT_REPORT_ONLY=(bool, True),
    EMAIL_BACKEND=(str, 'django.core.mail.backends.console.EmailBackend'),
    EMAIL_HOST=(str, 'smtp.gmail.com'),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_USE_SSL=(bool, False),
    DEFAULT_FROM_EMAIL=(str, ''),
)

BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / 'apps'

# Read .env file (if present)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY') or 'django-insecure-CHANGE-THIS-IN-PRODUCTION-use-env'
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
_raw_origins = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        'https://barbershop.com.co',
        'https://www.barbershop.com.co',
    ],
)
# Strip whitespace; Django requires exact match (no trailing slash)
CSRF_TRUSTED_ORIGINS = [o.strip().rstrip('/') for o in _raw_origins if o.strip()]

# allauth: usar X-Real-IP (enviado por Nginx) para rate limiting.
# Con Unix socket, REMOTE_ADDR queda vacío y allauth lanzaría PermissionDenied (403).
ALLAUTH_TRUSTED_CLIENT_IP_HEADER = 'X-Real-IP'

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
    'config.middleware.ContentSecurityPolicyMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.MaintenanceModeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
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

DATABASES = {
    'default': env.db('DATABASE_URL')
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'boskery' / 'files',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_FORMS = {
    'signup': 'apps.accounts.forms.CustomSignupForm',
    'login': 'apps.accounts.forms.CustomLoginForm',
    'reset_password': 'apps.accounts.forms.CustomResetPasswordForm',
}
ACCOUNT_ADAPTER = 'apps.accounts.adapters.CustomAccountAdapter'
ACCOUNT_PREVENT_ENUMERATION = True
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_RATE_LIMITS = {
    'login': '30/5m',
    'login_failed': '10/5m',
    'signup': '5/10m',
    'reset_password': '5/30m',
    'reset_password_from_key': '20/5m',
}
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# API Integrations
PRODUCTS_API_URL = env('PRODUCTS_API_URL')
PRODUCTS_API_KEY = env('PRODUCTS_API_KEY')
ERP_API_URL = env('ERP_API_URL')
ERP_API_KEY = env('ERP_API_KEY')
STOCK_SYNC_API_KEY = env('STOCK_SYNC_API_KEY')

# Wompi
WOMPI_ENV = env('WOMPI_ENV')
WOMPI_PUBLIC_KEY = env('WOMPI_PUBLIC_KEY')
WOMPI_PRIVATE_KEY = env('WOMPI_PRIVATE_KEY')
WOMPI_INTEGRITY_SECRET = env('WOMPI_INTEGRITY_SECRET')
WOMPI_EVENTS_SECRET = env('WOMPI_EVENTS_SECRET')
WOMPI_REDIRECT_URL = env('WOMPI_REDIRECT_URL')

CSP_ALLOW_UNSAFE_EVAL = env.bool('CSP_ALLOW_UNSAFE_EVAL', default=DEBUG)
CSP_STRICT_REPORT_ONLY = env.bool('CSP_STRICT_REPORT_ONLY', default=True)

EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL')
_default_from = env('DEFAULT_FROM_EMAIL') or EMAIL_HOST_USER or 'no-reply@localhost'
DEFAULT_FROM_EMAIL = _default_from
SERVER_EMAIL = _default_from

CART_SESSION_ID = 'cart'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'stderr': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['stderr'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['stderr'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['stderr'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

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


def _is_placeholder_secret(secret):
    if not secret:
        return True
    lowered = secret.lower()
    return (
        lowered.startswith('django-insecure-')
        or 'tu-clave-secreta' in lowered
        or len(secret) < 50
    )


# Environment-specific overrides
_django_env = (os.environ.get('DJANGO_ENV') or 'development').strip().lower()

if _django_env == 'development':
    DEBUG = True
    ALLOWED_HOSTS = ['*']

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True

if _django_env == 'production':
    if _is_placeholder_secret(SECRET_KEY):
        raise ImproperlyConfigured(
            'SECRET_KEY insegura para producción. Define una clave robusta en .env.'
        )

    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            'ALLOWED_HOSTS vacío en producción. Define al menos un dominio real.'
        )

    if (WOMPI_ENV or '').strip().lower() == 'production':
        required_wompi = {
            'WOMPI_PUBLIC_KEY': WOMPI_PUBLIC_KEY,
            'WOMPI_PRIVATE_KEY': WOMPI_PRIVATE_KEY,
            'WOMPI_INTEGRITY_SECRET': WOMPI_INTEGRITY_SECRET,
            'WOMPI_EVENTS_SECRET': WOMPI_EVENTS_SECRET,
            'WOMPI_REDIRECT_URL': WOMPI_REDIRECT_URL,
        }
        missing = [
            name for name, value in required_wompi.items() if not str(value).strip()
        ]
        if missing:
            raise ImproperlyConfigured(
                f'Config Wompi incompleta en producción: {", ".join(missing)}'
            )

        parsed = urlparse(WOMPI_REDIRECT_URL.strip())
        if parsed.scheme != 'https' or not parsed.netloc:
            raise ImproperlyConfigured(
                'WOMPI_REDIRECT_URL debe ser https y dominio público en producción.'
            )
        if parsed.hostname in ('localhost', '127.0.0.1'):
            raise ImproperlyConfigured(
                'WOMPI_REDIRECT_URL no puede usar localhost/127.0.0.1 en producción.'
            )
