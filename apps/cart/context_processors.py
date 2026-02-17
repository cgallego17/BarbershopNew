def cart(request):
    """Context processor para el carrito en todas las vistas."""
    from .cart import Cart
    cart = Cart(request)
    return {
        'cart': cart,
        'cart_count': len(cart),
        'cart_total': cart.get_total_price(),
    }
