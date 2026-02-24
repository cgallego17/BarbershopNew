"""
Comando: sync_stock
Sincroniza ÚNICAMENTE el stock desde la API de Tersa hacia los productos locales.
Los precios, imágenes y descripciones NO se modifican.

Uso:
    python manage.py sync_stock
    python manage.py sync_stock --dry-run          # muestra cambios sin guardar
    python manage.py sync_stock --verbose          # lista cada producto
    python manage.py sync_stock --show-not-found   # lista productos de API sin match local
"""
from django.core.management.base import BaseCommand

from apps.integrations.services import (
    TERSA_BRANDS,
    TERSA_EXTRA_PRODUCT_IDS,
    sync_tersa_stock,
)


class Command(BaseCommand):
    help = 'Sincroniza solo el stock desde la API Tersa hacia los productos locales.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Muestra los cambios que se harían sin modificar la base de datos.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            default=False,
            help='Muestra el detalle de cada producto procesado.',
        )
        parser.add_argument(
            '--show-not-found',
            action='store_true',
            default=False,
            help='Lista los external_id de la API que no tienen match en BD local.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        show_not_found = options['show_not_found']

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠  Modo DRY-RUN — no se guardarán cambios\n'))

        self.stdout.write('Consultando API Tersa...')

        try:
            result = sync_tersa_stock(
                brands=TERSA_BRANDS,
                extra_ids=TERSA_EXTRA_PRODUCT_IDS,
                dry_run=dry_run,
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Error al consultar la API: {exc}'))
            raise

        # ── Detalle por producto ────────────────────────────────────────────
        for r in result['results']:
            if r['status'] == 'updated':
                arrow = f"{r['old_stock']} → {r['new_stock']}"
                if verbose:
                    prefix = '[dry-run] ' if dry_run else ''
                    self.stdout.write(
                        f"  {'~' if dry_run else '✓'} {prefix}"
                        f"{r['name']} ({r['sku']}) | "
                        f"external_id={r['external_id']} | stock: {arrow}"
                    )

            elif r['status'] == 'unchanged' and verbose:
                self.stdout.write(
                    f"  – {r['name']} ({r['sku']}) | stock sin cambio: {r['stock']}"
                )

            elif r['status'] == 'not_found' and show_not_found:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ❗ external_id={r['external_id']} no encontrado en BD local "
                        f"(stock API: {r['stock']})"
                    )
                )

        # ── Resumen ─────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write('─' * 52)

        updated_label = '(simulado)' if dry_run else ''
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Actualizados {updated_label}:  {result['updated']}"
            )
        )
        self.stdout.write(f"– Sin cambio:         {result['unchanged']}")
        if result['not_found']:
            self.stdout.write(
                self.style.WARNING(f"❗ No encontrados:     {result['not_found']}")
            )
        self.stdout.write(f"   Total API:         {result['total_api']}")
        self.stdout.write('─' * 52)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nDRY-RUN: ningún cambio fue guardado. '
                    'Ejecuta sin --dry-run para aplicar.'
                )
            )
