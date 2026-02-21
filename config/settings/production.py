from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

# Security flags must be explicit in production regardless of .env DEBUG.
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


def _is_placeholder_secret(secret):
    if not secret:
        return True
    lowered = secret.lower()
    return (
        lowered.startswith('django-insecure-')
        or 'tu-clave-secreta' in lowered
        or len(secret) < 50
    )


if _is_placeholder_secret(SECRET_KEY):
    raise ImproperlyConfigured(
        'SECRET_KEY insegura para producción. Define una clave robusta en .env.'
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        'ALLOWED_HOSTS vacío en producción. Define al menos un dominio real.'
    )

# Wompi hard checks (mandatory for production mode of the gateway).
if (WOMPI_ENV or '').strip().lower() == 'production':
    required_wompi = {
        'WOMPI_PUBLIC_KEY': WOMPI_PUBLIC_KEY,
        'WOMPI_PRIVATE_KEY': WOMPI_PRIVATE_KEY,
        'WOMPI_INTEGRITY_SECRET': WOMPI_INTEGRITY_SECRET,
        'WOMPI_EVENTS_SECRET': WOMPI_EVENTS_SECRET,
        'WOMPI_REDIRECT_URL': WOMPI_REDIRECT_URL,
    }
    missing = [name for name, value in required_wompi.items() if not str(value).strip()]
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
