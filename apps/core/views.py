from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET


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
        from apps.products.models import Product
        from apps.products.models import Category

        from .models import SiteSettings, HomeSection, HomeHeroSlide, HomeAboutBlock, HomeMeatCategoryBlock, HomeBrand, HomeTestimonial

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
        context['home_brands'] = HomeBrand.objects.all()[:20]
        context['home_testimonials'] = HomeTestimonial.objects.all()[:10]
        context['home_categories'] = Category.objects.filter(is_active=True, parent__isnull=True)[:8]
        context['meat_category_block'] = HomeMeatCategoryBlock.get()
        # Productos de la categoría Kits (id=8) para la sección meat-category
        context['meat_category_products'] = list(
            base_product_qs.filter(categories__id=8).distinct()[:8]
        )

        return context


def contact_view(request):
    return render(request, 'core/contact.html')


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


@dashboard_required
def dashboard_view(request):
    from django.db.models import Sum
    from apps.orders.models import Order
    from apps.products.models import Product

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

    return render(request, 'core/dashboard.html', {
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
    })
