from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages


def dashboard_required(view):
    """Solo staff y admin pueden acceder al dashboard."""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(request.user, 'can_access_dashboard', False):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('No tienes acceso al panel de administración.')
        return view(request, *args, **kwargs)
    return login_required(wrapped)


class HomeView(TemplateView):
    template_name = 'index-dark.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        from apps.orders.models import OrderItem
        from apps.products.models import Product, Category, Brand

        from .models import SiteSettings, HomeSection, HomeHeroSlide, HomeAboutBlock, HomeMeatCategoryBlock, HomeBrandBlock, HomeTestimonial, HomePopupAnnouncement

        context = super().get_context_data(**kwargs)
        site_settings = SiteSettings.get()
        base_product_qs = Product.objects.filter(is_active=True)
        if not site_settings.show_out_of_stock_products:
            base_product_qs = base_product_qs.filter(Product.q_in_stock())
        # Productos populares = más vendidos (por cantidad en pedidos completados/procesando)
        sold = (
            OrderItem.objects.filter(order__status__in=['completed', 'processing'])
            .values('product_id')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:8]
        )
        product_ids = [x['product_id'] for x in sold]
        products = list(base_product_qs.filter(id__in=product_ids))
        product_by_id = {p.id: p for p in products}
        featured_products = [product_by_id[pid] for pid in product_ids if pid in product_by_id]
        # Si hay menos de 8, completar con productos activos/destacados que no estén ya
        if len(featured_products) < 8:
            exclude_ids = set(product_ids)
            extra = (
                base_product_qs.exclude(id__in=exclude_ids)
                .order_by('-is_featured', '-created_at')[: 8 - len(featured_products)]
            )
            featured_products = list(featured_products) + list(extra)
        context['featured_products'] = featured_products

        # Datos para secciones administrables del home
        context['active_sections'] = HomeSection.get_active_sections()
        context['hero_slides'] = HomeHeroSlide.objects.all()[:10]
        context['about_block'] = HomeAboutBlock.get()
        context['brand_block'] = HomeBrandBlock.get()
        context['home_brands'] = Brand.objects.filter(
            is_active=True
        ).exclude(
            logo__isnull=True
        ).exclude(
            logo=''
        ).order_by('order', 'name')[:20]
        context['home_testimonials'] = HomeTestimonial.objects.all()[:10]
        context['home_categories'] = Category.objects.filter(is_active=True, parent__isnull=True)[:8]
        context['meat_category_block'] = HomeMeatCategoryBlock.get()
        context['home_popup'] = HomePopupAnnouncement.get()
        # Productos de la categoría Kits (id=8) para la sección meat-category
        context['meat_category_products'] = list(
            base_product_qs.filter(categories__id=8).distinct()[:8]
        )

        return context


def contact_view(request):
    from .models import ContactSubmission

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        message = (request.POST.get('message') or '').strip()

        if not (name and email and phone and message):
            messages.error(request, 'Completa todos los campos.')
            return render(request, 'core/contact.html')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Ingresa un correo válido.')
            return render(request, 'core/contact.html')

        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        ip = ip or request.META.get('REMOTE_ADDR')
        ua = (request.META.get('HTTP_USER_AGENT') or '')[:300]
        ContactSubmission.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message,
            ip_address=ip or None,
            user_agent=ua,
        )
        messages.success(request, 'Mensaje enviado. Te contactaremos pronto.')
        return redirect('core:contact')

    return render(request, 'core/contact.html')


def about_view(request):
    return render(request, 'core/about.html')


def maintenance_view(request):
    return render(request, 'core/maintenance.html')


def robots_txt(request):
    return render(request, 'robots.txt', content_type='text/plain')


@require_GET
def geo_states_view(request):
    """API: lista de estados/departamentos por country_id (JSON)."""
    from .models import State
    country_id = request.GET.get('country_id')
    if not country_id:
        return JsonResponse({'states': []})
    states = State.objects.filter(country_id=country_id).order_by('name').values('id', 'name')
    return JsonResponse({'states': list(states)})


@require_GET
def geo_cities_view(request):
    """API: lista de ciudades por state_id (JSON)."""
    from .models import City
    state_id = request.GET.get('state_id')
    if not state_id:
        return JsonResponse({'cities': []})
    cities = City.objects.filter(state_id=state_id).order_by('name').values('id', 'name')
    return JsonResponse({'cities': list(cities)})


@require_GET
def geo_shipping_info_view(request):
    """API: precio y días de envío por city_id (JSON)."""
    from .models import City, ShippingPrice
    city_id = request.GET.get('city_id')
    if not city_id:
        return JsonResponse({'found': False})
    try:
        sp = ShippingPrice.objects.select_related('city').get(
            city_id=city_id, is_active=True
        )
        return JsonResponse({
            'found': True,
            'price': str(sp.price),
            'days_min': sp.delivery_days_min,
            'days_max': sp.delivery_days_max,
        })
    except ShippingPrice.DoesNotExist:
        return JsonResponse({'found': False})


@require_POST
def newsletter_subscribe_view(request):
    """Recibe suscripciones del formulario newsletter del sitio."""
    from .models import NewsletterSubscriber
    from .security import log_security_event

    if (request.POST.get('website') or '').strip():
        log_security_event(
            request,
            event_type='honeypot_trigger',
            source='newsletter',
            details={'reason': 'honeypot_field_filled'},
        )
        return JsonResponse({'ok': True, 'message': 'Solicitud recibida.'})

    email = (request.POST.get('EMAIL') or request.POST.get('email') or '').strip().lower()
    if not email:
        return JsonResponse(
            {'ok': False, 'message': 'Ingresa un correo válido.'},
            status=400,
        )
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {'ok': False, 'message': 'Ingresa un correo válido.'},
            status=400,
        )
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
    client_ip = client_ip or request.META.get('REMOTE_ADDR', '') or 'unknown'
    throttle_key = f"newsletter:ip:{client_ip}"
    current_attempts = cache.get(throttle_key, 0)
    if current_attempts >= 10:
        log_security_event(
            request,
            event_type='rate_limit_block',
            source='newsletter',
            details={'window_seconds': 300, 'limit': 10},
        )
        return JsonResponse(
            {'ok': False, 'message': 'Demasiados intentos. Intenta de nuevo en unos minutos.'},
            status=429,
        )
    cache.set(throttle_key, current_attempts + 1, timeout=300)

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'is_active': True, 'source': 'footer'},
    )
    if not created and not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=['is_active', 'updated_at'])
        return JsonResponse(
            {
                'ok': True,
                'message': 'Suscripción reactivada. ¡Bienvenido de nuevo!',
            }
        )
    if not created:
        return JsonResponse(
            {
                'ok': True,
                'message': 'Este correo ya estaba suscrito.',
            }
        )
    return JsonResponse(
        {
            'ok': True,
            'message': 'Gracias por suscribirte al newsletter.',
        }
    )


@dashboard_required
def dashboard_view(request):
    from datetime import timedelta
    from django.db.models import Sum
    from django.utils import timezone
    from apps.orders.models import Order
    from apps.products.models import Product
    from .models import SecurityEvent

    total_orders = Order.objects.count()
    total_products = Product.objects.filter(is_active=True).count()
    total_revenue = Order.objects.filter(
        status__in=['completed', 'processing']
    ).aggregate(Sum('total'))['total__sum'] or 0
    pending_orders = Order.objects.filter(status='pending').count()
    recent_orders = Order.objects.select_related('user')[:10]
    low_stock = list(Product.objects.filter(
        manage_stock=True, stock_quantity__lte=5, stock_quantity__gt=0
    )[:5])
    since_24h = timezone.now() - timedelta(hours=24)
    security_24h = SecurityEvent.objects.filter(created_at__gte=since_24h)
    recent_security_events = SecurityEvent.objects.order_by('-created_at')[:10]
    security_summary = {
        'total_24h': security_24h.count(),
        'honeypot_24h': security_24h.filter(event_type='honeypot_trigger').count(),
        'rate_limit_24h': security_24h.filter(event_type='rate_limit_block').count(),
        'auth_honeypot_24h': security_24h.filter(event_type='auth_honeypot').count(),
    }

    return render(request, 'core/dashboard.html', {
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'security_summary': security_summary,
        'recent_security_events': recent_security_events,
    })
