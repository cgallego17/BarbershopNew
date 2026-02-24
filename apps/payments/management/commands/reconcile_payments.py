"""
Comando de reconciliación de pagos con Wompi.

Consulta la API de Wompi para todos los pedidos cuyo pago esté pendiente
y actualiza el estado en base de datos.

Uso:
    python manage.py reconcile_payments
    python manage.py reconcile_payments --hours 48      # últimas 48 h (default 24)
    python manage.py reconcile_payments --dry-run       # solo muestra, no guarda
    python manage.py reconcile_payments --order ORD-20260224-5B6B6A4D
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.models import WompiTransaction
from apps.payments.views import (
    _fetch_transaction_from_wompi,
    _fulfill_order,
    _is_transaction_consistent,
    _save_transaction,
)
from apps.core.emails import notify_payment_failed


class Command(BaseCommand):
    help = 'Reconcilia pedidos pendientes consultando la API de Wompi'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Rango de tiempo en horas hacia atrás (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Solo muestra resultados sin modificar la BD',
        )
        parser.add_argument(
            '--order',
            type=str,
            default='',
            help='Reconciliar un solo pedido por su número',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        order_number = options['order'].strip()
        since = timezone.now() - timedelta(hours=options['hours'])

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN — no se guardarán cambios'))

        # ── Obtener pedidos a reconciliar ──────────────────────────────────
        qs = Order.objects.filter(payment_status='pending')

        if order_number:
            qs = qs.filter(order_number=order_number)
        else:
            qs = qs.filter(created_at__gte=since)

        # Solo pedidos que hayan intentado pago con Wompi al menos una vez
        qs = qs.filter(wompi_transactions__isnull=False).distinct()

        total = qs.count()
        if total == 0:
            self.stdout.write('No hay pedidos pendientes con transacciones Wompi.')
            return

        self.stdout.write(f'Reconciliando {total} pedido(s)...\n')

        updated = skipped = errors = 0

        for order in qs.prefetch_related('wompi_transactions'):
            # Tomar la transacción más reciente del pedido
            tx_record = (
                order.wompi_transactions
                .order_by('-created_at')
                .first()
            )
            if not tx_record:
                continue

            wompi_id = tx_record.wompi_id
            self.stdout.write(f'  [{order.order_number}] tx={wompi_id} ', ending='')

            try:
                tx_data = _fetch_transaction_from_wompi(wompi_id)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'Error API: {exc}'))
                errors += 1
                continue

            if not tx_data:
                self.stdout.write(self.style.WARNING('sin datos de Wompi'))
                skipped += 1
                continue

            status = tx_data.get('status', 'UNKNOWN')
            self.stdout.write(f'→ {status} ', ending='')

            if status == tx_record.status and status == 'PENDING':
                self.stdout.write('(sin cambio)')
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f'[dry-run] actualizaría a {status}'))
                updated += 1
                continue

            # Guardar transacción actualizada
            _save_transaction(order, tx_data)

            if status == 'APPROVED':
                if _is_transaction_consistent(order, tx_data):
                    _fulfill_order(order, tx_data)
                    self.stdout.write(self.style.SUCCESS('✓ APROBADO y procesado'))
                else:
                    self.stdout.write(self.style.ERROR(
                        '✗ APROBADO pero monto/referencia inconsistente — revisar manualmente'
                    ))
                updated += 1

            elif status in ('DECLINED', 'VOIDED', 'ERROR'):
                if order.payment_status not in ('paid', 'failed'):
                    order.payment_status = 'failed'
                    order.save(update_fields=['payment_status', 'updated_at'])
                    notify_payment_failed(order)
                self.stdout.write(self.style.WARNING(f'✗ {status} — marcado como fallido'))
                updated += 1

            elif status == 'PENDING':
                self.stdout.write('(sigue pendiente en Wompi)')
                skipped += 1

            else:
                self.stdout.write(self.style.WARNING(f'estado desconocido: {status}'))
                skipped += 1

        self.stdout.write(
            f'\nResultado: {updated} actualizado(s), {skipped} sin cambio, {errors} error(es).'
        )
