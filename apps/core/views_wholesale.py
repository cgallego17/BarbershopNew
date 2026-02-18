"""Vistas del panel de mayoristas."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseForbidden

from apps.products.models import Product


def wholesale_required(view):
    """Solo clientes mayoristas pueden acceder."""

    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(request.user, 'is_wholesale', False):
            return HttpResponseForbidden('Acceso solo para clientes mayoristas.')
        return view(request, *args, **kwargs)

    return login_required(wrapped)


@wholesale_required
def wholesale_panel(request):
    """Panel mayoristas: catálogo con precios mayoristas."""
    from apps.core.models import SiteSettings
    qs = Product.objects.filter(is_active=True).prefetch_related('variants', 'categories', 'images')
    if not SiteSettings.get().show_out_of_stock_products:
        qs = qs.filter(Product.q_in_stock())
    products = list(qs)
    products_with_price = [(p, p.get_price(request.user)) for p in products]
    return render(request, 'wholesale/panel.html', {
        'products_with_price': products_with_price,
    })
