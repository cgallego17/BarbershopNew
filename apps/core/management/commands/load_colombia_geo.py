"""
Carga país Colombia con sus departamentos (estados) y ciudades desde un JSON.
Formato esperado: array de países con "name", "iso2", "iso3", "phonecode", "states"
y cada state con "name", "iso2", "cities" (array de {"name"}).

Uso:
  python manage.py load_colombia_geo
  python manage.py load_colombia_geo --file "ruta/al/archivo/countries+states+cities.json"
"""
import json
import os

from django.core.management.base import BaseCommand

from apps.core.models import Country, State, City


DEFAULT_JSON_PATH = r"C:\Users\User\Documents\ncs3\NSC-INTERNATIONAL\data\countries+states+cities.json"


class Command(BaseCommand):
    help = 'Carga Colombia (país, departamentos/estados y ciudades) desde el JSON countries+states+cities.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=DEFAULT_JSON_PATH,
            help=f'Ruta al archivo JSON (por defecto: {DEFAULT_JSON_PATH})',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Eliminar datos previos de Colombia antes de cargar (país y sus estados/ciudades).',
        )

    def handle(self, *args, **options):
        filepath = options['file']
        replace = options['replace']

        if not os.path.isfile(filepath):
            self.stderr.write(self.style.ERROR(f'No se encontró el archivo: {filepath}'))
            return

        self.stdout.write(f'Leyendo {filepath}...')
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error al leer el JSON: {e}'))
            return

        if not isinstance(data, list):
            self.stderr.write(self.style.ERROR('El JSON debe ser un array de países.'))
            return

        colombia = None
        for c in data:
            if (c.get('name') or '').strip() == 'Colombia':
                colombia = c
                break

        if not colombia:
            self.stderr.write(self.style.ERROR('No se encontró "Colombia" en el JSON.'))
            return

        if replace:
            Country.objects.filter(name='Colombia').delete()
            self.stdout.write('Datos previos de Colombia eliminados.')

        country, created = Country.objects.get_or_create(
            name='Colombia',
            defaults={
                'iso2': colombia.get('iso2') or 'CO',
                'iso3': colombia.get('iso3') or 'COL',
                'phonecode': str(colombia.get('phonecode') or '57'),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('País Colombia creado.'))
        else:
            country.iso2 = colombia.get('iso2') or 'CO'
            country.iso3 = colombia.get('iso3') or 'COL'
            country.phonecode = str(colombia.get('phonecode') or '57')
            country.save()
            self.stdout.write('País Colombia actualizado.')

        states_data = colombia.get('states') or []
        states_created = 0
        cities_created = 0

        for st in states_data:
            state_name = (st.get('name') or '').strip()
            if not state_name:
                continue
            state, state_created = State.objects.get_or_create(
                country=country,
                name=state_name,
                defaults={'iso2': (st.get('iso2') or '')[:10]}
            )
            if state_created:
                states_created += 1

            for ct in st.get('cities') or []:
                city_name = (ct.get('name') or '').strip()
                if not city_name:
                    continue
                _, city_created = City.objects.get_or_create(
                    state=state,
                    name=city_name
                )
                if city_created:
                    cities_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Colombia cargada: 1 país, {State.objects.filter(country=country).count()} departamentos, '
            f'{City.objects.filter(state__country=country).count()} ciudades. '
            f'(Nuevos: {states_created} estados, {cities_created} ciudades)'
        ))
