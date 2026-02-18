"""Establece o restablece la contraseña del usuario administrador."""
import os
import getpass
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea o restablece la contraseña del usuario admin. Si no existe, lo crea con username "admin".'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña en texto plano (opcional; si no se pasa, se pedirá por consola o se usará ADMIN_PASSWORD del .env).',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username del admin a modificar (por defecto: admin).',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options.get('password') or os.environ.get('ADMIN_PASSWORD')

        if not password:
            password = getpass.getpass('Nueva contraseña para el admin: ')
            password2 = getpass.getpass('Confirmar contraseña: ')
            if password != password2:
                self.stderr.write(self.style.ERROR('Las contraseñas no coinciden.'))
                return

        if len(password) < 8:
            self.stderr.write(self.style.ERROR('La contraseña debe tener al menos 8 caracteres.'))
            return

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.filter(role='admin').first() or User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_user(
                username=username,
                email=os.environ.get('ADMIN_EMAIL', 'admin@localhost'),
                password=password,
                role='admin',
            )
            self.stdout.write(self.style.SUCCESS(f'Usuario admin "{username}" creado correctamente.'))
        else:
            user.set_password(password)
            user.role = 'admin'
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Contraseña del usuario "{user.username}" actualizada correctamente.'))
