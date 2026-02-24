"""
Custom CSRF failure view for logging and debugging 403 on POST (e.g. login).
"""
import logging

from django.conf import settings
from django.http import HttpResponseForbidden
from django.middleware.csrf import (
    REASON_NO_CSRF_COOKIE,
    REASON_BAD_TOKEN,
    REASON_NO_REFERER,
    REASON_BAD_REFERER,
)
from django.views.csrf import csrf_failure as default_csrf_failure

logger = logging.getLogger(__name__)

CSRF_REASONS = {
    REASON_NO_CSRF_COOKIE: "No CSRF cookie",
    REASON_BAD_TOKEN: "CSRF token missing or incorrect",
    REASON_NO_REFERER: "Referer checking failed - no Referer header",
    REASON_BAD_REFERER: (
        "Referer checking failed - origin not in CSRF_TRUSTED_ORIGINS"
    ),
}


def csrf_failure(request, reason=""):
    """Log CSRF failure details for production debugging."""
    meta = request.META
    trusted = getattr(settings, "CSRF_TRUSTED_ORIGINS", [])
    logger.warning(
        "CSRF 403: reason=%s | path=%s | host=%s | referer=%s | origin=%s | "
        "trusted_origins=%s",
        CSRF_REASONS.get(reason, reason),
        request.path,
        meta.get("HTTP_HOST"),
        meta.get("HTTP_REFERER"),
        meta.get("HTTP_ORIGIN"),
        trusted,
    )
    return default_csrf_failure(request, reason)
