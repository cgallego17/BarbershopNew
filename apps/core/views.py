from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import TemplateView


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
        from apps.products.models import Product
        from .models import HomeSection, HomeHeroSlide, HomeAboutBlock, HomeBrand, HomeTestimonial

        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(is_active=True, is_featured=True)[:8]
        if not products:
            products = Product.objects.filter(is_active=True)[:8]
        context['featured_products'] = products

        # Datos para secciones administrables del home
        context['active_sections'] = HomeSection.get_active_sections()
        context['hero_slides'] = HomeHeroSlide.objects.all()[:10]
        context['about_block'] = HomeAboutBlock.get()
        context['home_brands'] = HomeBrand.objects.all()[:20]
        context['home_testimonials'] = HomeTestimonial.objects.all()[:10]

        return context


def contact_view(request):
    return render(request, 'core/contact.html')


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
