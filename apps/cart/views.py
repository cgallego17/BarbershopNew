from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

from apps.products.models import Product
from .cart import Cart


def cart_sidebar_json(request, toast_msg=None, toast_type='success'):
    """Devuelve el HTML del sidebar + totales + toast para actualizaciones AJAX."""
    from apps.core.models import SiteSettings
    from django.contrib.humanize.templatetags.humanize import intcomma
    cart = Cart(request)
    settings = SiteSettings.get()
    html = render_to_string(
        'partials/cart_sidebar_items.html',
        {'cart': cart, 'cart_count': len(cart),
         'cart_total': cart.get_total_price(),
         'site_settings': settings},
        request=request
    )
    total = cart.get_total_price()
    currency = settings.currency or ''
    data = {
        'html': html,
        'count': len(cart),
        'total': f"{currency}{intcomma(int(total))}",
    }
    if toast_msg:
        data['toast'] = {'message': toast_msg, 'type': toast_type}
    return JsonResponse(data)


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    variant_id = request.POST.get('variant_id') or None
    if variant_id:
        variant_id = int(variant_id)
    price = None
    if request.user.is_authenticated and getattr(request.user, 'is_wholesale', False):
        if variant_id:
            variant = product.variants.get(id=variant_id)
            price = variant.get_price(request.user)
        else:
            price = product.get_price(request.user)
    cart.add(product, quantity=quantity, variant_id=variant_id, price=price)
    msg = f'"{product.name}" añadido al carrito.'
    # Si es petición AJAX devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return cart_sidebar_json(request, toast_msg=msg, toast_type='success')
    messages.success(request, msg)
    # Redirect normal con flag para abrir sidebar
    next_url = request.POST.get('next') or 'cart:detail'
    sep = '&' if '?' in next_url else '?'
    return redirect(f"{next_url}{sep}cart_open=1")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    variant_id = request.POST.get('variant_id') or None
    cart.remove(product_id, variant_id=variant_id)
    msg = 'Producto eliminado del carrito.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return cart_sidebar_json(request, toast_msg=msg, toast_type='info')
    messages.success(request, msg)
    return redirect('cart:detail')


@require_POST
def cart_update(request):
    cart = Cart(request)
    for key, item in cart.cart.items():
        qty = request.POST.get(f'quantity_{key}')
        if qty is not None:
            try:
                qty = int(qty)
                if qty > 0:
                    cart.cart[key]['quantity'] = qty
                else:
                    del cart.cart[key]
            except ValueError:
                pass
    cart.save()
    messages.success(request, 'Carrito actualizado.')
    return redirect('cart:detail')


@require_POST
def cart_update_item(request, item_key):
    """Actualiza la cantidad de un ítem específico y devuelve totales en JSON."""
    from decimal import Decimal
    from django.contrib.humanize.templatetags.humanize import intcomma
    from apps.core.models import SiteSettings

    cart = Cart(request)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1

    if item_key not in cart.cart:
        return JsonResponse({'ok': False, 'error': 'Item no encontrado'}, status=404)

    settings = SiteSettings.get()
    currency = settings.currency or ''

    if qty < 1:
        del cart.cart[item_key]
        cart.save()
    else:
        cart.cart[item_key]['quantity'] = qty
        cart.save()

    # Calcular subtotal del ítem
    if item_key in cart.cart:
        item_data   = cart.cart[item_key]
        price       = Decimal(item_data['price'])
        item_qty    = item_data['quantity']
        item_total  = price * item_qty
    else:
        item_total = Decimal('0')
        item_qty   = 0

    cart_total = cart.get_total_price()
    count      = len(cart)

    return JsonResponse({
        'ok':         True,
        'item_total': f"{currency}{intcomma(int(item_total))}",
        'item_qty':   item_qty,
        'cart_total': f"{currency}{intcomma(int(cart_total))}",
        'cart_count': count,
        'removed':    item_key not in cart.cart,
    })


def cart_detail(request):
    from django.shortcuts import render
    return render(request, 'cart/cart.html')
