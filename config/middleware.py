from django.conf import settings


class MaintenanceModeMiddleware:
    """
    Cuando maintenance_mode está activo:
      - Staff / superusuarios pasan sin restricción alguna.
      - El resto de usuarios ve un modal bloqueante inyectado
        desde base.html (site_settings.maintenance_mode en contexto).
      - Rutas técnicas siempre pasan (static, media, admin, panel…).
    No realiza ninguna redirección; el bloqueo visual lo gestiona
    el template mediante el contexto site_settings.
    """

    _BYPASS = (
        '/panel/', '/admin/', '/cuentas/',
        '/static/', '/media/', '/assets/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or '/'

        for prefix in self._BYPASS:
            if path.startswith(prefix):
                return self.get_response(request)

        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and (
            getattr(user, 'can_access_dashboard', False)
            or user.is_staff
            or user.is_superuser
        ):
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
                # Inline scripts y event handlers en base.html y partials; hashes son frágiles
                "script-src": ["'self'", "https:", "'unsafe-inline'"],
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
