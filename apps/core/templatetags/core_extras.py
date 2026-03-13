"""Filtros y tags para plantillas del core."""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def custom_head_html():
    """Carga y renderiza el HTML personalizado del head desde SiteSettings (pixels, scripts)."""
    from apps.core.models import SiteSettings
    try:
        site = SiteSettings.get()
        html = getattr(site, 'custom_body_html', None) or ''
        html = (html or '').strip()
        return mark_safe(html) if html else ''
    except Exception:
        return ''


@register.filter
def safe_file_url(field):
    """Devuelve la URL del archivo o cadena vacía si falla (evita 500 en preview)."""
    if not field:
        return ''
    try:
        return field.url
    except (ValueError, OSError, AttributeError):
        return ''
