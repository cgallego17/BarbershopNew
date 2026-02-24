"""
Vistas de cuentas. Incluye wrapper de login sin CSRF como workaround
para 403 en producción (proxy/HTTPS).
"""
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from allauth.account.views import LoginView


@method_decorator(csrf_exempt, name='dispatch')
class LoginViewNoCsrf(LoginView):
    """
    Login sin validación CSRF. Workaround temporal para 403 en producción.
    TODO: Investigar y corregir el problema de CSRF (Referer, cookies, etc.)
    y volver a la vista estándar de allauth.
    """
    pass
