"""Context processors de core."""
import json
from .models import SiteSettings


def site_settings(request):
    """Inyecta la configuración del sitio en el contexto."""
    return {'site_settings': SiteSettings.get()}


def django_messages_json(request):
    """Serializa los mensajes de Django a JSON para el sistema de toasts."""
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    msgs = [{'message': str(m), 'tags': m.tags} for m in storage]
    return {'django_toast_messages': json.dumps(msgs)}
