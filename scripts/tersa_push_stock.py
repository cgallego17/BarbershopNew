"""
Comando Django para el sistema TersaSoft.
Lee el stock de productoBodega y lo empuja al Barbershop via API.

INSTALACIÓN en el sistema TersaSoft:
  1. Copiar este archivo a:
        <tersa_project>/prod/management/commands/push_stock_barbershop.py
  2. Agregar estas variables al .env (o settings) del sistema Tersa:
        BARBERSHOP_API_URL=https://barbershop.com.co/api/integraciones/sync-stock/
        BARBERSHOP_API_KEY=<la clave que configures en STOCK_SYNC_API_KEY del Barbershop>

USO:
  python manage.py push_stock_barbershop
  python manage.py push_stock_barbershop --bodega 2
  python manage.py push_stock_barbershop --marca 1
  python manage.py push_stock_barbershop --dry-run
  python manage.py push_stock_barbershop --dry-run --verbose
"""
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

# ---------- Configuración ----------
BARBERSHOP_API_URL = getattr(
    settings, 'BARBERSHOP_API_URL',
    'https://barbershop.com.co/api/integraciones/sync-stock/',
)
BARBERSHOP_API_KEY = getattr(settings, 'BARBERSHOP_API_KEY', '')

BATCH_SIZE  = 200   # productos por request
SLEEP_BATCH = 0.3   # segundos entre batches


# ---------- Helpers ----------

def _build_stock_payload(marca_id=None, bodega_id=2):
    """
    Lee AtributoProducto y el stock de productoBodega.
    Si marca_id es None (default) trae TODOS los productos sin filtro de marca.
    Retorna lista de dicts: [{"external_id": "...", "stock": n}, ...]
    """
    from prod.models import AtributoProducto, productoBodega

    productos = AtributoProducto.objects.all()
    if marca_id:
        productos = productos.filter(marca_id=marca_id)

    bodegas_qs = productoBodega.objects.filter(
        bodega_id=bodega_id,
        producto__in=productos,
    ).values('producto_id', 'cantidad')

    stock_por_producto = {str(b['producto_id']): max(0, int(b['cantidad'] or 0))
                          for b in bodegas_qs}

    payload = []
    for prod in productos:
        ext_id = str(prod.id)
        stock = stock_por_producto.get(ext_id, 0)
        payload.append({'external_id': ext_id, 'stock': stock})
    return payload


def _push_batch(batch, dry_run=False):
    """
    Envía un batch al endpoint del Barbershop.
    Retorna el dict de respuesta o lanza excepción.
    """
    if dry_run:
        return {
            'ok': True, 'dry_run': True,
            'updated': 0, 'unchanged': 0,
            'not_found': 0, 'errors': 0,
            'total_received': len(batch),
        }

    if not BARBERSHOP_API_KEY:
        raise ValueError(
            "BARBERSHOP_API_KEY no configurado en settings. "
            "Agrega BARBERSHOP_API_KEY al .env del sistema Tersa."
        )

    resp = requests.post(
        BARBERSHOP_API_URL,
        json=batch,
        headers={
            'Content-Type': 'application/json',
            'X-Sync-Api-Key': BARBERSHOP_API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------- Command ----------

class Command(BaseCommand):
    help = (
        'Lee stock de productoBodega y lo envía al Barbershop via API. '
        'Configura BARBERSHOP_API_URL y BARBERSHOP_API_KEY en settings.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--bodega',
            type=int,
            default=2,
            help='ID de bodega a usar como fuente de stock (default: 2)',
        )
        parser.add_argument(
            '--marca',
            type=int,
            default=0,
            help='ID de marca a sincronizar. 0 = todas las marcas (default: 0)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Construye el payload sin enviarlo al Barbershop.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            default=False,
            help='Muestra cada producto en el payload.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        bodega_id = options['bodega']
        marca_id = options['marca']

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠  Modo DRY-RUN — no se enviará nada al Barbershop\n'
            ))

        marca_label = f'Marca ID: {marca_id}' if marca_id else 'Todas las marcas'
        self.stdout.write(
            f'Leyendo stock — {marca_label} | Bodega ID: {bodega_id}...'
        )

        try:
            payload = _build_stock_payload(
                marca_id=marca_id if marca_id else None,
                bodega_id=bodega_id,
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Error leyendo BD local: {exc}'))
            raise

        if not payload:
            self.stdout.write(self.style.WARNING('No se encontraron productos.'))
            return

        self.stdout.write(f'{len(payload)} productos a procesar → batches de {BATCH_SIZE}')

        if verbose:
            for item in payload:
                self.stdout.write(
                    f"  external_id={item['external_id']} | stock={item['stock']}"
                )

        # Envío por batches
        total_updated = total_unchanged = total_not_found = total_errors = 0
        batches = [payload[i:i + BATCH_SIZE] for i in range(0, len(payload), BATCH_SIZE)]

        for idx, batch in enumerate(batches, 1):
            self.stdout.write(
                f'  Batch {idx}/{len(batches)} ({len(batch)} items)...', ending=' '
            )
            try:
                result = _push_batch(batch, dry_run=dry_run)
                total_updated    += result.get('updated', 0)
                total_unchanged  += result.get('unchanged', 0)
                total_not_found  += result.get('not_found', 0)
                total_errors     += result.get('errors', 0)
                self.stdout.write(
                    f"✓ upd={result.get('updated',0)} "
                    f"unch={result.get('unchanged',0)} "
                    f"nf={result.get('not_found',0)}"
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'✗ Error: {exc}'))
                total_errors += len(batch)

            if idx < len(batches):
                time.sleep(SLEEP_BATCH)

        # Resumen
        self.stdout.write('')
        self.stdout.write('─' * 52)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY-RUN — productos preparados: {len(payload)}')
            )
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Actualizados:    {total_updated}'))
            self.stdout.write(f'– Sin cambio:      {total_unchanged}')
            if total_not_found:
                self.stdout.write(
                    self.style.WARNING(f'❗ No encontrados:  {total_not_found}')
                )
            if total_errors:
                self.stdout.write(
                    self.style.ERROR(f'✗ Errores:         {total_errors}')
                )
        self.stdout.write(f'   Total enviados: {len(payload)}')
        self.stdout.write('─' * 52)
