"""
Envía solicitudes de reseña a clientes con pedidos completados hace 3-7 días.

Uso:
  python manage.py send_review_requests
  python manage.py send_review_requests --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order
from apps.core.emails import notify_request_review


class Command(BaseCommand):
    help = 'Envía solicitudes de reseña a clientes con pedidos completados hace 3-7 días.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué pedidos se procesarían sin enviar correos.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        min_date = now - timedelta(days=7)
        max_date = now - timedelta(days=3)

        qs = Order.objects.filter(
            status='completed',
            payment_status='paid',
            review_request_sent_at__isnull=True,
        ).exclude(billing_email='').prefetch_related('items__product')

        orders = []
        for order in qs:
            completed = order.completed_at or order.updated_at
            if completed and min_date <= completed <= max_date:
                if order.items.exists():
                    orders.append(order)

        if not orders:
            self.stdout.write(
                self.style.WARNING('No hay pedidos completados hace 3-7 días sin solicitud de reseña.')
            )
            return

        self.stdout.write(f'Pedidos a procesar: {len(orders)}')
        if dry_run:
            for o in orders:
                self.stdout.write(f'  - #{o.order_number} -> {o.billing_email}')
            self.stdout.write(self.style.WARNING('Dry run: no se enviaron correos.'))
            return

        sent = 0
        for order in orders:
            try:
                notify_request_review(order)
                order.review_request_sent_at = timezone.now()
                order.save(update_fields=['review_request_sent_at'])
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  Enviado a {order.billing_email} (#{order.order_number})'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  Error #{order.order_number}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Se enviaron {sent} solicitud(es) de reseña.'))
