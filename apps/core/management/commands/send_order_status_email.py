"""
Envía el correo de actualización de estado de pedido para probar que funciona.

Uso:
  python manage.py send_order_status_email 20
  python manage.py send_order_status_email 20 --email otro@correo.com
"""
from django.core.management.base import BaseCommand

from apps.orders.models import Order
from apps.core.emails import notify_order_status_changed


class Command(BaseCommand):
    help = 'Envía el correo de actualización de estado para un pedido (para pruebas).'

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int, help='ID del pedido')
        parser.add_argument(
            '--email',
            type=str,
            help='Email destino (por defecto usa billing_email del pedido)',
        )

    def handle(self, *args, **options):
        order_id = options['order_id']
        override_email = options.get('email')

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Pedido {order_id} no existe.'))
            return

        to_email = override_email or order.billing_email
        if not to_email:
            self.stderr.write(
                self.style.ERROR(
                    f'El pedido #{order.order_number} no tiene billing_email. '
                    'Usa: --email tu@correo.com'
                )
            )
            return

        if override_email:
            order.billing_email = override_email

        self.stdout.write(
            f'Enviando correo de actualización de pedido #{order.order_number} a {to_email}...'
        )
        try:
            notify_order_status_changed(order)
            self.stdout.write(
                self.style.SUCCESS('Correo enviado. Revisa bandeja (y spam).')
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
