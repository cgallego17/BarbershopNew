from django.conf import settings


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
