"""
Custom CSRF failure view for logging and debugging 403 on POST (e.g. login).
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def csrf_failure(request, reason=""):
    """Log CSRF failure details for production debugging."""
    meta = request.META
    trusted = getattr(settings, "CSRF_TRUSTED_ORIGINS", [])
    logger.warning(
        "CSRF 403: reason=%s | path=%s | host=%s | referer=%s | origin=%s | "
        "trusted_origins=%s",
        reason,
        request.path,
        meta.get("HTTP_HOST"),
        meta.get("HTTP_REFERER"),
        meta.get("HTTP_ORIGIN"),
        trusted,
    )
    from django.views.csrf import csrf_failure as default_view
    return default_view(request, reason)
