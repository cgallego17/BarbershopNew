from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CsrfTrustedOriginMiddleware(MiddlewareMixin):
    """
    Añade dinámicamente el origen de la petición a CSRF_TRUSTED_ORIGINS.
    Si la petición llegó a Django, el Host ya pasó ALLOWED_HOSTS.
    Soluciona 403 en login (CSRF) con proxy/HTTPS.
    """
    def process_request(self, request):
        try:
            host = request.get_host().strip().split(':')[0]
        except Exception:
            return
        if not host or host.startswith('.') or ' ' in host:
            return
        scheme = 'https' if request.is_secure() else 'http'
        origin = f"{scheme}://{host}"
        trusted = list(getattr(settings, 'CSRF_TRUSTED_ORIGINS', []) or [])
        if origin not in trusted:
            trusted.append(origin)
            settings.CSRF_TRUSTED_ORIGINS = trusted
        # Añadir también el origen del Referer (por si difiere)
        referer = request.META.get('HTTP_REFERER', '').strip()
        if referer and referer.startswith(('http://', 'https://')):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(referer)
                ref_origin = f"{parsed.scheme}://{parsed.netloc.split(':')[0]}"
                if ref_origin and ref_origin not in trusted:
                    trusted.append(ref_origin)
                    settings.CSRF_TRUSTED_ORIGINS = trusted
            except Exception:
                pass


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or '/'
        if path.startswith('/panel/'):
            return self.get_response(request)
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/assets/'):
            return self.get_response(request)
        if path.startswith('/mantenimiento/'):
            return self.get_response(request)

        try:
            from apps.core.models import SiteSettings
            if SiteSettings.get().maintenance_mode:
                from django.shortcuts import redirect
                return redirect('core:maintenance')
        except Exception:
            return self.get_response(request)

        return self.get_response(request)


class ContentSecurityPolicyMiddleware:
    """
    Adds a baseline CSP header and optionally allows unsafe-eval.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        script_src = ["'self'", "'unsafe-inline'", "https:"]
        if getattr(settings, "CSP_ALLOW_UNSAFE_EVAL", False):
            script_src.append("'unsafe-eval'")

        directives = {
            "default-src": ["'self'", "https:", "data:", "blob:"],
            "script-src": script_src,
            "style-src": ["'self'", "'unsafe-inline'", "https:"],
            "img-src": ["'self'", "data:", "blob:", "https:"],
            "font-src": ["'self'", "data:", "https:"],
            "connect-src": ["'self'", "https:", "ws:", "wss:"],
            "frame-src": ["'self'", "https:"],
            "form-action": ["'self'", "https:"],
            "base-uri": ["'self'"],
            "object-src": ["'none'"],
        }
        csp_value = "; ".join(
            f"{directive} {' '.join(sources)}"
            for directive, sources in directives.items()
        )
        response["Content-Security-Policy"] = csp_value
        if getattr(settings, "CSP_STRICT_REPORT_ONLY", False):
            strict_directives = {
                "default-src": ["'self'", "https:", "data:", "blob:"],
                "script-src": ["'self'", "https:"],
                "style-src": ["'self'", "'unsafe-inline'", "https:"],
                "img-src": ["'self'", "data:", "blob:", "https:"],
                "font-src": ["'self'", "data:", "https:"],
                "connect-src": ["'self'", "https:", "ws:", "wss:"],
                "frame-src": ["'self'", "https:"],
                "form-action": ["'self'", "https:"],
                "base-uri": ["'self'"],
                "object-src": ["'none'"],
            }
            strict_value = "; ".join(
                f"{directive} {' '.join(sources)}"
                for directive, sources in strict_directives.items()
            )
            response["Content-Security-Policy-Report-Only"] = strict_value
        return response
