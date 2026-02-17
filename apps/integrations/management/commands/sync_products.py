from django.core.management.base import BaseCommand

from apps.integrations.services import sync_products_from_api


class Command(BaseCommand):
    help = 'Sincroniza productos desde la API externa'

    def handle(self, *args, **options):
        try:
            result = sync_products_from_api()
            self.stdout.write(self.style.SUCCESS(
                f'Sincronización completada: {result["created"]} creados, {result["updated"]} actualizados.'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
