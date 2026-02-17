"""
Carrito de compras - estilo WooCommerce.
Soporta productos simples y variables, sesión o usuario.
"""
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache


class Cart:
    """Manejo del carrito via sesión."""
    
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, variant_id=None, override=False, price=None):
        """Añadir o actualizar producto en carrito. price: override (ej. precio mayorista)."""
        product_id = str(product.id)
        key = f"{product_id}_{variant_id or ''}".rstrip('_')
        
        if key in self.cart:
            if override:
                self.cart[key]['quantity'] = quantity
                if price is not None:
                    self.cart[key]['price'] = str(price)
            else:
                self.cart[key]['quantity'] += quantity
        else:
            if price is None:
                price = product.price
                if variant_id:
                    variant = product.variants.get(id=variant_id)
                    price = variant.price
            self.cart[key] = {
                'product_id': product_id,
                'variant_id': str(variant_id) if variant_id else None,
                'quantity': quantity,
                'price': str(price),
            }
        self.save()

    def remove(self, product_id, variant_id=None):
        """Eliminar producto del carrito."""
        key = f"{product_id}_{variant_id or ''}".rstrip('_')
        if key in self.cart:
            del self.cart[key]
            self.save()

    def __iter__(self):
        from apps.products.models import Product
        product_ids = set(item['product_id'] for item in self.cart.values())
        products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
        
        for key, item in self.cart.items():
            product = products.get(item['product_id'])
            if product:
                item['product'] = product
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                if item.get('variant_id'):
                    try:
                        item['variant'] = product.variants.get(id=item['variant_id'])
                    except:
                        item['variant'] = None
                else:
                    item['variant'] = None
                item['key'] = key
                yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def save(self):
        self.session.modified = True
