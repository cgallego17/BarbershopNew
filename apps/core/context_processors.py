"""Context processors de core."""
from .models import SiteSettings


def site_settings(request):
    """Inyecta la configuración del sitio en el contexto."""
    return {'site_settings': SiteSettings.get()}
