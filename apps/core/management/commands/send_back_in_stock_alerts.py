"""
Envía notificaciones de "producto de nuevo en stock" a suscriptores.

Uso:
  python manage.py send_back_in_stock_alerts
  python manage.py send_back_in_stock_alerts --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.products.models import Product, ProductStockAlert
from apps.core.emails import notify_back_in_stock


class Command(BaseCommand):
    help = 'Envía notificaciones a suscriptores cuando un producto vuelve a tener stock.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué alertas se procesarían sin enviar correos.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        alerts = ProductStockAlert.objects.filter(
            notified_at__isnull=True,
        ).select_related('product')

        to_notify = [a for a in alerts if a.product.is_active and a.product.in_stock]

        if not to_notify:
            self.stdout.write(
                self.style.WARNING('No hay alertas de stock pendientes para productos con disponibilidad.')
            )
            return

        self.stdout.write(f'Alertas a procesar: {len(to_notify)}')
        if dry_run:
            for a in to_notify:
                self.stdout.write(f'  - {a.product.name} -> {a.email}')
            self.stdout.write(self.style.WARNING('Dry run: no se enviaron correos.'))
            return

        sent = 0
        for alert in to_notify:
            try:
                notify_back_in_stock(alert.product, alert.email)
                alert.notified_at = timezone.now()
                alert.save(update_fields=['notified_at'])
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  Enviado a {alert.email} ({alert.product.name})'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  Error {alert.product.name} -> {alert.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Se enviaron {sent} notificación(es) de stock.'))
