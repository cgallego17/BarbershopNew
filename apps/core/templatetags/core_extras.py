"""Filtros y tags para plantillas del core."""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def safe_file_url(field):
    """Devuelve la URL del archivo o cadena vacía si falla (evita 500 en preview)."""
    if not field:
        return ''
    try:
        return field.url
    except (ValueError, OSError, AttributeError):
        return ''
