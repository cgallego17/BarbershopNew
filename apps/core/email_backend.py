"""
Backend SMTP que permite desactivar la verificación del certificado SSL
cuando el servidor de correo usa un certificado con otro hostname
(ej. hosting compartido con cert para el nombre del servidor).
"""
import ssl
import smtplib

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class EmailBackend(SMTPBackend):
    """SMTP backend que respeta EMAIL_SSL_VERIFY para verificación de certificado."""

    def open(self):
        if self.connection:
            return False

        use_ssl = getattr(settings, "EMAIL_USE_SSL", False)
        use_tls = getattr(settings, "EMAIL_USE_TLS", False)
        ssl_verify = getattr(settings, "EMAIL_SSL_VERIFY", True)

        if use_ssl:
            if ssl_verify:
                connection = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=getattr(settings, "EMAIL_TIMEOUT", None),
                )
            else:
                context = ssl._create_unverified_context()
                connection = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    context=context,
                    timeout=getattr(settings, "EMAIL_TIMEOUT", None),
                )
        else:
            connection = smtplib.SMTP(
                self.host,
                self.port,
                timeout=getattr(settings, "EMAIL_TIMEOUT", None),
            )
            if use_tls:
                if ssl_verify:
                    connection.starttls()
                else:
                    context = ssl._create_unverified_context()
                    connection.starttls(context=context)

        if self.username and self.password:
            connection.login(self.username, self.password)
        self.connection = connection
        return True
