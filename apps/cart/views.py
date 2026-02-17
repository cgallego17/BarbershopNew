from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

from apps.products.models import Product
from .cart import Cart


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
    messages.success(request, f'"{product.name}" añadido al carrito.')
    return redirect(request.POST.get('next', 'cart:detail'))


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    variant_id = request.POST.get('variant_id') or None
    cart.remove(product_id, variant_id=variant_id)
    messages.success(request, 'Producto eliminado del carrito.')
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


def cart_detail(request):
    from django.shortcuts import render
    return render(request, 'cart/cart.html')
