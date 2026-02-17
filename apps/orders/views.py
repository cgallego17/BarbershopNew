from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Order, OrderItem
from apps.cart.cart import Cart
from apps.coupons.models import Coupon


def checkout_view(request):
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
        messages.success(request, f'Pedido {order.order_number} creado correctamente.')
        return redirect('orders:detail', order_number=order.order_number)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'cart_total': cart.get_total_price(),
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


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})
