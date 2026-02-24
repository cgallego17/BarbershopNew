from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Order, OrderItem
from apps.cart.cart import Cart
from apps.coupons.models import Coupon
from apps.accounts.forms import (
    AddressBookForm,
    CustomerPasswordChangeForm,
    CustomerProfileForm,
)
from .forms import CheckoutForm
from apps.accounts.models import UserAddress
from apps.products.models import ProductFavorite
from apps.core.emails import notify_order_created

GUEST_ORDER_SESSION_KEY = 'guest_order_numbers'


def _remember_guest_order(request, order_number):
    guest_orders = request.session.get(GUEST_ORDER_SESSION_KEY, [])
    if order_number not in guest_orders:
        guest_orders.append(order_number)
        request.session[GUEST_ORDER_SESSION_KEY] = guest_orders[-30:]
        request.session.modified = True


def _can_access_order(request, order):
    if order.user_id:
        return request.user.is_authenticated and request.user.id == order.user_id
    guest_orders = request.session.get(GUEST_ORDER_SESSION_KEY, [])
    return order.order_number in guest_orders


def checkout_view(request):
    from django.urls import reverse
    from apps.core.models import Country
    import json
    from apps.accounts.models import UserAddress

    cart = Cart(request)
    if not cart:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('products:list')

    def build_checkout_prefill(user):
        prefill = {
            'address': getattr(user, 'address', '') if user and user.is_authenticated else '',
            'country': getattr(user, 'country', '') if user and user.is_authenticated else '',
            'state': getattr(user, 'state', '') if user and user.is_authenticated else '',
            'city': getattr(user, 'city', '') if user and user.is_authenticated else '',
            'postal_code': getattr(user, 'postal_code', '') if user and user.is_authenticated else '',
        }
        if not user or not user.is_authenticated:
            return prefill
        default_address = UserAddress.objects.filter(
            user=user,
            is_default=True,
        ).first()
        if not default_address:
            return prefill
        return {
            'address': prefill['address'] or default_address.address,
            'country': prefill['country'] or default_address.country,
            'state': prefill['state'] or default_address.state,
            'city': prefill['city'] or default_address.city,
            'postal_code': prefill['postal_code'] or default_address.postal_code,
        }

    if request.method == 'POST':
        checkout_form = CheckoutForm(request.POST)
        if not checkout_form.is_valid():
            messages.error(request, 'Revisa los datos de facturación e inténtalo de nuevo.')
            countries = Country.objects.all().order_by('name')
            user = getattr(request, 'user', None)
            checkout_prefill = build_checkout_prefill(user)
            from apps.core.models import SiteSettings
            free_shipping_min_amount = SiteSettings.get().free_shipping_min_amount
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'cart_total': cart.get_total_price(),
                'free_shipping_min_amount': free_shipping_min_amount,
                'countries': countries,
                'geo_countries_json': json.dumps(
                    [{'id': c.id, 'name': c.name} for c in countries]
                ),
                'geo_states_url': reverse('core:geo_states'),
                'geo_cities_url': reverse('core:geo_cities'),
                'initial_state': checkout_prefill.get('state', ''),
                'initial_city': checkout_prefill.get('city', ''),
                'checkout_prefill': checkout_prefill,
            })
        cleaned = checkout_form.cleaned_data
        billing_type = cleaned.get('billing_customer_type', 'person')
        billing_dob = cleaned.get('billing_date_of_birth')
        billing_last = cleaned.get('billing_last_name', '') if billing_type == 'person' else ''
        billing_doctype = cleaned.get('billing_document_type', '')
        subtotal = cart.get_total_price()
        shipping_total = Decimal('0.00')
        from apps.core.models import City, ShippingPrice, SiteSettings
        free_shipping_min_amount = SiteSettings.get().free_shipping_min_amount or Decimal('0.00')
        is_free_shipping = free_shipping_min_amount > 0 and subtotal >= free_shipping_min_amount
        billing_city_name = cleaned.get('billing_city', '').strip()
        billing_state_name = cleaned.get('billing_state', '').strip()
        billing_country_name = cleaned.get('billing_country', '').strip()
        if not is_free_shipping and billing_city_name and billing_country_name:
            city = City.objects.filter(
                name__iexact=billing_city_name,
                state__name__iexact=billing_state_name,
                state__country__name__iexact=billing_country_name,
            ).first()
            if city:
                try:
                    sp = ShippingPrice.objects.get(city=city, is_active=True)
                    shipping_total = sp.price
                except ShippingPrice.DoesNotExist:
                    pass

        order = Order(
            user=request.user if request.user.is_authenticated else None,
            billing_customer_type=billing_type,
            billing_document_type=billing_doctype,
            billing_document_number=cleaned.get('billing_document_number', ''),
            billing_date_of_birth=billing_dob,
            billing_first_name=cleaned.get('billing_first_name'),
            billing_last_name=billing_last,
            billing_email=cleaned.get('billing_email'),
            billing_phone=cleaned.get('billing_phone', ''),
            billing_address=cleaned.get('billing_address'),
            billing_city=billing_city_name,
            billing_state=billing_state_name,
            billing_country=billing_country_name,
            billing_postal_code=cleaned.get('billing_postal_code', ''),
            subtotal=subtotal,
            shipping_total=shipping_total,
            total=subtotal + shipping_total,
        )
        coupon_code = cleaned.get('coupon_code', '').strip()
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code, is_active=True)
                discount = coupon.get_discount(subtotal)
                order.discount_total = discount
                order.total = subtotal - discount + shipping_total
                order.coupon_code = coupon.code
            except Coupon.DoesNotExist:
                messages.error(request, 'Cupón inválido.')
        order.save()
        if order.user_id is None:
            _remember_guest_order(request, order.order_number)

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

        notify_order_created(order)
        cart.clear()

        # Creación opcional de cuenta durante el checkout
        if not request.user.is_authenticated and request.POST.get('create_account') == '1':
            new_password = request.POST.get('new_password', '').strip()
            email = cleaned.get('billing_email', '').strip()
            if new_password and len(new_password) >= 8 and email:
                from django.contrib.auth import get_user_model, login as _auth_login
                UserModel = get_user_model()
                if not UserModel.objects.filter(email=email).exists():
                    try:
                        new_user = UserModel.objects.create_user(
                            username=email,
                            email=email,
                            password=new_password,
                            first_name=cleaned.get('billing_first_name', ''),
                            last_name=billing_last,
                        )
                        order.user = new_user
                        order.save(update_fields=['user'])
                        _auth_login(
                            request, new_user,
                            backend='django.contrib.auth.backends.ModelBackend',
                        )
                        messages.success(
                            request,
                            'Cuenta creada exitosamente. Ya iniciaste sesión.',
                        )
                    except Exception:
                        pass

        # Redirigir a la pasarela de pago Wompi
        return redirect('payments:payment_page', order_number=order.order_number)

    user = getattr(request, 'user', None)
    checkout_prefill = build_checkout_prefill(user)
    countries = Country.objects.all().order_by('name')
    from apps.core.models import SiteSettings
    free_shipping_min_amount = SiteSettings.get().free_shipping_min_amount
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'cart_total': cart.get_total_price(),
        'free_shipping_min_amount': free_shipping_min_amount,
        'countries': countries,
        'geo_countries_json': json.dumps([{'id': c.id, 'name': c.name} for c in countries]),
        'geo_states_url': reverse('core:geo_states'),
        'geo_cities_url': reverse('core:geo_cities'),
        'initial_state': checkout_prefill.get('state', ''),
        'initial_city': checkout_prefill.get('city', ''),
        'checkout_prefill': checkout_prefill,
    })


def order_detail(request, order_number):
    order = Order.objects.filter(order_number=order_number).prefetch_related('items').first()
    if not order:
        return redirect('core:home')
    if not _can_access_order(request, order):
        return redirect('core:home')
    return render(request, 'orders/order_detail.html', {'order': order})


def validate_coupon(request):
    """AJAX: valida un cupón y devuelve el descuento calculado."""
    from django.contrib.humanize.templatetags.humanize import intcomma
    from apps.core.models import SiteSettings

    code = request.GET.get('code', '').strip()
    if not code:
        return JsonResponse({'valid': False, 'error': 'Ingresa un código.'})

    cart = Cart(request)
    subtotal = cart.get_total_price()
    if not subtotal:
        return JsonResponse({'valid': False, 'error': 'El carrito está vacío.'})

    try:
        coupon = Coupon.objects.get(code__iexact=code, is_active=True)
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
        'discount_amount': float(discount),
        'new_total': f'{currency}{intcomma(int(new_total))}',
    })


@login_required
def order_list(request):
    import json
    from django.urls import reverse
    from apps.core.models import Country
    from django.db.models import Count

    def build_address_book_form(data=None, instance=None):
        if data is not None:
            return AddressBookForm(data, instance=instance)
        if instance is not None:
            return AddressBookForm(instance=instance)
        return AddressBookForm()

    def sync_user_address_fields(address):
        request.user.address = address.address
        request.user.city = address.city
        request.user.state = address.state
        request.user.country = address.country
        request.user.postal_code = address.postal_code
        request.user.save(
            update_fields=['address', 'city', 'state', 'country', 'postal_code']
        )

    active_tab = request.GET.get('tab', 'orders')
    editing_address_id = request.GET.get('edit_address')
    editing_address = None
    if editing_address_id and str(editing_address_id).isdigit():
        editing_address = UserAddress.objects.filter(
            user=request.user,
            pk=editing_address_id,
        ).first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profile':
            profile_form = CustomerProfileForm(request.POST, instance=request.user)
            address_book_form = build_address_book_form(instance=editing_address)
            password_form = CustomerPasswordChangeForm(request.user)
            active_tab = 'profile'
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Tus datos de perfil se actualizaron correctamente.')
                return redirect(f"{request.path}?tab=profile")
            messages.error(request, 'Revisa los datos del perfil e inténtalo de nuevo.')
        elif action in ('address_add', 'address_edit'):
            address_id = request.POST.get('address_id')
            target_address = None
            if action == 'address_edit' and address_id and address_id.isdigit():
                target_address = UserAddress.objects.filter(
                    user=request.user,
                    pk=address_id,
                ).first()

            profile_form = CustomerProfileForm(instance=request.user)
            address_book_form = build_address_book_form(
                data=request.POST,
                instance=target_address,
            )
            password_form = CustomerPasswordChangeForm(request.user)
            active_tab = 'addresses'
            if address_book_form.is_valid():
                saved_address = address_book_form.save(commit=False)
                saved_address.user = request.user
                if not UserAddress.objects.filter(user=request.user).exclude(
                    pk=saved_address.pk
                ).exists():
                    saved_address.is_default = True
                saved_address.save()
                if saved_address.is_default:
                    sync_user_address_fields(saved_address)
                msg = (
                    'Dirección actualizada correctamente.'
                    if action == 'address_edit'
                    else 'Dirección agregada correctamente.'
                )
                messages.success(request, msg)
                return redirect(f"{request.path}?tab=addresses")
            editing_address = target_address
            messages.error(request, 'Revisa los datos de la dirección e inténtalo de nuevo.')
        elif action == 'address_delete':
            address_id = request.POST.get('address_id')
            profile_form = CustomerProfileForm(instance=request.user)
            password_form = CustomerPasswordChangeForm(request.user)
            address_book_form = build_address_book_form()
            active_tab = 'addresses'
            if address_id and address_id.isdigit():
                target = UserAddress.objects.filter(user=request.user, pk=address_id).first()
                if target:
                    was_default = target.is_default
                    target.delete()
                    if was_default:
                        next_default = UserAddress.objects.filter(user=request.user).first()
                        if next_default:
                            next_default.is_default = True
                            next_default.save(update_fields=['is_default'])
                            sync_user_address_fields(next_default)
                    messages.success(request, 'Dirección eliminada correctamente.')
            return redirect(f"{request.path}?tab=addresses")
        elif action == 'address_set_default':
            address_id = request.POST.get('address_id')
            profile_form = CustomerProfileForm(instance=request.user)
            password_form = CustomerPasswordChangeForm(request.user)
            address_book_form = build_address_book_form()
            active_tab = 'addresses'
            if address_id and address_id.isdigit():
                target = UserAddress.objects.filter(user=request.user, pk=address_id).first()
                if target:
                    UserAddress.objects.filter(user=request.user, is_default=True).update(
                        is_default=False
                    )
                    target.is_default = True
                    target.save(update_fields=['is_default'])
                    sync_user_address_fields(target)
                    messages.success(
                        request,
                        f'La dirección "{target.alias}" quedó como predeterminada.',
                    )
            return redirect(f"{request.path}?tab=addresses")
        elif action == 'password':
            profile_form = CustomerProfileForm(instance=request.user)
            address_book_form = build_address_book_form(instance=editing_address)
            password_form = CustomerPasswordChangeForm(request.user, request.POST)
            active_tab = 'security'
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Tu contraseña se cambió correctamente.')
                return redirect(f"{request.path}?tab=security")
            messages.error(request, 'No fue posible cambiar la contraseña. Verifica los datos.')
        else:
            profile_form = CustomerProfileForm(instance=request.user)
            address_book_form = build_address_book_form(instance=editing_address)
            password_form = CustomerPasswordChangeForm(request.user)
    else:
        profile_form = CustomerProfileForm(instance=request.user)
        address_book_form = build_address_book_form(instance=editing_address)
        password_form = CustomerPasswordChangeForm(request.user)

    addresses = UserAddress.objects.filter(user=request.user).order_by(
        '-is_default',
        '-updated_at',
        '-id',
    )
    orders = (
        Order.objects.filter(user=request.user)
        .annotate(items_count=Count('items'))
        .order_by('-created_at')
    )
    favorites = (
        ProductFavorite.objects.filter(user=request.user)
        .select_related('product', 'product__brand')
        .prefetch_related('product__images')
        .order_by('-created_at')
    )
    countries = Country.objects.all().order_by('name')
    initial_country = address_book_form['country'].value() or ''
    initial_state = address_book_form['state'].value() or ''
    initial_city = address_book_form['city'].value() or ''

    return render(
        request,
        'orders/order_list.html',
        {
            'orders': orders,
            'favorites': favorites,
            'addresses': addresses,
            'active_tab': active_tab,
            'profile_form': profile_form,
            'address_book_form': address_book_form,
            'password_form': password_form,
            'editing_address': editing_address,
            'countries': countries,
            'geo_countries_json': json.dumps(
                [{'id': c.id, 'name': c.name} for c in countries]
            ),
            'geo_states_url': reverse('core:geo_states'),
            'geo_cities_url': reverse('core:geo_cities'),
            'initial_country': initial_country,
            'initial_state': initial_state,
            'initial_city': initial_city,
        },
    )
