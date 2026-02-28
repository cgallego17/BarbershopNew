"""
Envía recordatorios de pago a clientes con pedidos pendientes.

Uso:
  python manage.py send_payment_reminders
  python manage.py send_payment_reminders --hours 2
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order
from apps.core.emails import notify_order_pending_payment


class Command(BaseCommand):
    help = 'Envía recordatorios de pago a pedidos pendientes que aún no han recibido uno.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Solo pedidos creados hace al menos N horas (default: 1)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué pedidos se enviarían sin enviar correos.',
        )

    def handle(self, *args, **options):
        hours = max(0, options['hours'])
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(hours=hours)

        qs = Order.objects.filter(
            status='pending',
            payment_status='pending',
            payment_reminder_sent_at__isnull=True,
            created_at__lte=cutoff,
        ).exclude(billing_email='')

        orders = list(qs)
        if not orders:
            self.stdout.write(
                self.style.WARNING(f'No hay pedidos pendientes de pago (creados hace >={hours}h sin recordatorio).')
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
                notify_order_pending_payment(order)
                order.payment_reminder_sent_at = timezone.now()
                order.save(update_fields=['payment_reminder_sent_at'])
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  Enviado recordatorio #{order.order_number}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  Error #{order.order_number}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Se enviaron {sent} recordatorio(s).'))
