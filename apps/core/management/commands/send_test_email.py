"""
Envía un correo de prueba para verificar que el servidor SMTP está bien configurado.

Uso:
  python manage.py send_test_email
  python manage.py send_test_email --email tu@correo.com
  python manage.py send_test_email --email a@x.com b@y.com
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from apps.core.emails import get_staff_admin_emails, _default_from_email


class Command(BaseCommand):
    help = 'Envía un correo de prueba para verificar la configuración SMTP.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            nargs='+',
            type=str,
            help='Email(s) donde enviar la prueba. Sin esto, se usa staff/admin.',
        )

    def handle(self, *args, **options):
        to_emails = options.get('email')
        if not to_emails:
            to_emails = list(get_staff_admin_emails())
            if not to_emails:
                msg = (
                    'No hay emails de staff/admin. '
                    'Usa: python manage.py send_test_email --email tu@correo.com'
                )
                self.stderr.write(self.style.ERROR(msg))
                return

        backend = getattr(settings, 'EMAIL_BACKEND', '')
        from_email = _default_from_email()
        subject = '[TEST] Correo de prueba - The Barbershop'
        body = (
            'Este es un correo de prueba.\n\n'
            'Si recibes este mensaje, el servidor de correo está bien configurado.\n\n'
            f'Backend: {backend}\n'
            f'From: {from_email}\n'
        )

        self.stdout.write(f'Enviando correo de prueba a: {", ".join(to_emails)}')
        self.stdout.write(f'Backend: {backend}')
        self.stdout.write(f'From: {from_email}')

        try:
            sent = send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=to_emails,
                fail_silently=False,
            )
            ok_msg = f'Se enviaron {sent} correo(s). Revisa bandeja (y spam).'
            self.stdout.write(self.style.SUCCESS(ok_msg))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error enviando: {e}'))
