"""Context processors de core."""
import json
from datetime import timedelta

from django.utils import timezone

from .models import SiteSettings


def site_settings(request):
    """Inyecta la configuración del sitio en el contexto."""
    ctx = {'site_settings': SiteSettings.get()}
    if (
        getattr(request, 'user', None)
        and getattr(request.user, 'can_access_dashboard', False)
        and '/panel/' in request.path
    ):
        from django.urls import reverse
        from apps.accounts.models import User
        from apps.core.models import NewsletterSubscriber
        from apps.orders.models import Order
        from apps.products.models import Product, ProductReview

        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        pending_reviews = ProductReview.objects.filter(is_approved=False).count()
        pending_orders = Order.objects.filter(status='pending').count()
        failed_payments_24h = Order.objects.filter(
            created_at__gte=last_24h,
            payment_status='failed',
        ).count()
        zero_stock_count = Product.objects.filter(
            is_active=True,
            manage_stock=True,
            stock_quantity=0,
        ).count()
        low_stock_count = Product.objects.filter(
            is_active=True,
            manage_stock=True,
            stock_quantity__gt=0,
            stock_quantity__lte=5,
        ).count()
        new_orders_24h = Order.objects.filter(created_at__gte=last_24h).count()
        new_customers_24h = User.objects.filter(
            date_joined__gte=last_24h,
            role__in=['client', 'wholesale'],
        ).count()
        new_newsletter_24h = NewsletterSubscriber.objects.filter(
            created_at__gte=last_24h,
        ).count()

        notifications = []
        if pending_orders:
            notifications.append({
                'level': 'warning',
                'icon': 'fas fa-clock',
                'text': f'{pending_orders} pedidos pendientes por gestionar.',
                'url': reverse('core:admin_panel:order_list') + '?status=pending',
            })
        if failed_payments_24h:
            notifications.append({
                'level': 'danger',
                'icon': 'fas fa-credit-card',
                'text': f'{failed_payments_24h} pagos fallidos en las últimas 24h.',
                'url': reverse('core:admin_panel:order_list') + '?payment_status=failed',
            })
        if zero_stock_count:
            notifications.append({
                'level': 'danger',
                'icon': 'fas fa-exclamation-triangle',
                'text': f'{zero_stock_count} productos sin stock.',
                'url': reverse('core:admin_panel:product_list') + '?status=active',
            })
        if low_stock_count:
            notifications.append({
                'level': 'warning',
                'icon': 'fas fa-box-open',
                'text': f'{low_stock_count} productos con stock bajo.',
                'url': reverse('core:admin_panel:product_list') + '?status=active',
            })
        if new_orders_24h:
            notifications.append({
                'level': 'info',
                'icon': 'fas fa-shopping-cart',
                'text': f'{new_orders_24h} pedidos nuevos en las últimas 24h.',
                'url': reverse('core:admin_panel:order_list'),
            })
        if new_customers_24h:
            notifications.append({
                'level': 'info',
                'icon': 'fas fa-user-plus',
                'text': f'{new_customers_24h} clientes nuevos en las últimas 24h.',
                'url': reverse('core:admin_panel:customer_list'),
            })
        if pending_reviews:
            notifications.append({
                'level': 'info',
                'icon': 'fas fa-star-half-alt',
                'text': f'{pending_reviews} reseñas pendientes de aprobación.',
                'url': reverse('core:admin_panel:review_list') + '?status=pending',
            })
        if new_newsletter_24h:
            notifications.append({
                'level': 'success',
                'icon': 'fas fa-envelope-open-text',
                'text': f'{new_newsletter_24h} suscriptores newsletter nuevos en 24h.',
                'url': reverse('core:admin_panel:newsletter_list'),
            })

        ctx['pending_reviews_count'] = pending_reviews
        ctx['admin_notifications'] = notifications
        ctx['admin_notifications_count'] = len(notifications)
    return ctx


def django_messages_json(request):
    """Serializa los mensajes de Django a JSON para el sistema de toasts."""
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    msgs = [{'message': str(m), 'tags': m.tags} for m in storage]
    return {'django_toast_messages': json.dumps(msgs)}
