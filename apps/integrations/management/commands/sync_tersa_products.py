from django.core.management.base import BaseCommand

from apps.integrations.services import sync_tersa_products, TERSA_BRANDS


class Command(BaseCommand):
    help = 'Sincroniza productos desde API Tersa (solo marcas BARBERSHOP y BARBER UP)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-images',
            action='store_true',
            help='No descargar imágenes de productos',
        )

    def handle(self, *args, **options):
        try:
            result = sync_tersa_products(
                brands=TERSA_BRANDS,
                download_images=not options.get('no_images', False),
            )
            self.stdout.write(self.style.SUCCESS(
                f'Tersa: {result["total"]} productos de API (BARBERSHOP, BARBER UP). '
                f'{result["created"]} creados, {result["updated"]} actualizados.'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise
