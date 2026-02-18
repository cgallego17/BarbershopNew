from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Order, OrderItem
from apps.cart.cart import Cart
from apps.coupons.models import Coupon


def checkout_view(request):
    from django.urls import reverse
    from apps.core.models import Country
    import json

    cart = Cart(request)
    if not cart:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('products:list')

    if request.method == 'POST':
        # Crear orden
        order = Order(
            user=request.user if request.user.is_authenticated else None,
            billing_first_name=request.POST.get('billing_first_name'),
            billing_last_name=request.POST.get('billing_last_name'),
            billing_email=request.POST.get('billing_email'),
            billing_phone=request.POST.get('billing_phone', ''),
            billing_address=request.POST.get('billing_address'),
            billing_city=request.POST.get('billing_city'),
            billing_state=request.POST.get('billing_state', ''),
            billing_country=request.POST.get('billing_country'),
            billing_postal_code=request.POST.get('billing_postal_code', ''),
            subtotal=cart.get_total_price(),
            total=cart.get_total_price(),
        )
        coupon_code = request.POST.get('coupon_code', '').strip()
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code.upper(), is_active=True)
                discount = coupon.get_discount(cart.get_total_price())
                order.discount_total = discount
                order.total = cart.get_total_price() - discount
                order.coupon_code = coupon.code
            except Coupon.DoesNotExist:
                messages.error(request, 'Cupón inválido.')
        order.save()

        # Crear líneas
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                variant=item.get('variant'),
                product_name=item['product'].name,
                quantity=item['quantity'],
                price=item['price'],
                total=item['total_price'],
            )

        cart.clear()
        # Redirigir a la pasarela de pago Wompi
        return redirect('payments:payment_page', order_number=order.order_number)

    user = getattr(request, 'user', None)
    countries = Country.objects.all().order_by('name')
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'cart_total': cart.get_total_price(),
        'countries': countries,
        'geo_countries_json': json.dumps([{'id': c.id, 'name': c.name} for c in countries]),
        'geo_states_url': reverse('geo_states'),
        'geo_cities_url': reverse('geo_cities'),
        'initial_state': getattr(user, 'state', '') or '' if user and user.is_authenticated else '',
        'initial_city': getattr(user, 'city', '') or '' if user and user.is_authenticated else '',
    })


def order_detail(request, order_number):
    order = Order.objects.filter(order_number=order_number).prefetch_related('items').first()
    if not order:
        return redirect('home')
    if request.user.is_authenticated and order.user and order.user != request.user:
        return redirect('home')
    if not request.user.is_authenticated and order.user:
        return redirect('home')
    return render(request, 'orders/order_detail.html', {'order': order})


def validate_coupon(request):
    """AJAX: valida un cupón y devuelve el descuento calculado."""
    from django.contrib.humanize.templatetags.humanize import intcomma
    from apps.core.models import SiteSettings

    code = request.GET.get('code', '').strip().upper()
    if not code:
        return JsonResponse({'valid': False, 'error': 'Ingresa un código.'})

    cart = Cart(request)
    subtotal = cart.get_total_price()
    if not subtotal:
        return JsonResponse({'valid': False, 'error': 'El carrito está vacío.'})

    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Cupón inválido o expirado.'})

    discount = coupon.get_discount(subtotal)
    if discount == 0:
        # Determinar razón
        from django.utils import timezone
        now = timezone.now()
        if coupon.date_end and now > coupon.date_end:
            return JsonResponse({'valid': False, 'error': 'Este cupón ha expirado.'})
        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            return JsonResponse({'valid': False, 'error': 'Este cupón ya alcanzó su límite de uso.'})
        if coupon.minimum_amount and subtotal < coupon.minimum_amount:
            currency = SiteSettings.get().currency or ''
            return JsonResponse({
                'valid': False,
                'error': f'El pedido mínimo para este cupón es {currency}{intcomma(int(coupon.minimum_amount))}.'
            })
        return JsonResponse({'valid': False, 'error': 'El cupón no aplica a este pedido.'})

    currency  = SiteSettings.get().currency or ''
    new_total = subtotal - discount

    if coupon.discount_type == 'percent':
        label = f'{int(coupon.discount_value)}% de descuento'
    else:
        label = f'{currency}{intcomma(int(discount))} de descuento'

    return JsonResponse({
        'valid':     True,
        'code':      coupon.code,
        'label':     label,
        'discount':  f'{currency}{intcomma(int(discount))}',
        'new_total': f'{currency}{intcomma(int(new_total))}',
    })


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})
