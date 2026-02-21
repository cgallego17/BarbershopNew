from apps.core.models import SecurityEvent


def log_security_event(request, event_type, source, details=None):
    details = details or {}
    ip_address = None
    path = ''
    user_agent = ''
    if request is not None:
        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip_address = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
        path = request.path[:255]
        user_agent = (request.META.get('HTTP_USER_AGENT') or '')[:255]
    SecurityEvent.objects.create(
        event_type=event_type,
        source=source,
        ip_address=ip_address or None,
        path=path,
        user_agent=user_agent,
        details=details,
    )
