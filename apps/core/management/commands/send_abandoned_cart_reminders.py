"""
Envía recordatorios de carrito abandonado a leads que aún no han recibido uno.

Uso:
  python manage.py send_abandoned_cart_reminders
  python manage.py send_abandoned_cart_reminders --hours 1
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.cart.models import AbandonedCartLead
from apps.core.emails import notify_cart_abandoned


class Command(BaseCommand):
    help = 'Envía recordatorios de carrito abandonado a leads pendientes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Solo leads creados hace al menos N horas (default: 1)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué leads se enviarían sin enviar correos.',
        )

    def handle(self, *args, **options):
        hours = max(0, options['hours'])
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(hours=hours)

        qs = AbandonedCartLead.objects.filter(
            reminder_sent_at__isnull=True,
            created_at__lte=cutoff,
        ).exclude(email='')

        leads = list(qs)
        if not leads:
            self.stdout.write(
                self.style.WARNING(f'No hay leads de carrito abandonado (creados hace >={hours}h sin recordatorio).')
            )
            return

        self.stdout.write(f'Leads a procesar: {len(leads)}')
        if dry_run:
            for lead in leads:
                self.stdout.write(f'  - {lead.email} ({len(lead.cart_snapshot)} items)')
            self.stdout.write(self.style.WARNING('Dry run: no se enviaron correos.'))
            return

        sent = 0
        for lead in leads:
            try:
                cart_items = [
                    {
                        'product_name': i.get('product_name', ''),
                        'variant': i.get('variant', ''),
                        'quantity': i.get('quantity', 1),
                        'total': Decimal(str(i.get('total', 0))),
                    }
                    for i in (lead.cart_snapshot or [])
                ]
                if not cart_items:
                    self.stdout.write(self.style.WARNING(f'  Lead {lead.email} sin items, omitido.'))
                    continue
                notify_cart_abandoned(lead.email, cart_items, lead.cart_total)
                lead.reminder_sent_at = timezone.now()
                lead.save(update_fields=['reminder_sent_at'])
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  Enviado a {lead.email}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  Error {lead.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Se enviaron {sent} recordatorio(s).'))
