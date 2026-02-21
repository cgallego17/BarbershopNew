import re
from django.utils.html import strip_tags

try:
    import bleach
except Exception:  # pragma: no cover
    bleach = None


ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u',
    'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'span', 'div',
    'a', 'img',
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'span': ['class'],
    'div': ['class'],
    'p': ['class'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
SCRIPT_STYLE_RE = re.compile(r'<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>', re.I | re.S)


def sanitize_html(value):
    raw = (value or '').strip()
    if not raw:
        return ''

    raw = SCRIPT_STYLE_RE.sub('', raw)
    if bleach is None:
        return strip_tags(raw)

    cleaned = bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    # Defense-in-depth for links with target=_blank
    cleaned = cleaned.replace('target="_blank"', 'target="_blank" rel="noopener noreferrer"')
    return cleaned
