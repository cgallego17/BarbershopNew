import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.core.models import SiteSettings

logger = logging.getLogger(__name__)


def _default_from_email():
    site = SiteSettings.get()
    configured = getattr(settings, "DEFAULT_FROM_EMAIL", "").strip()
    if configured:
        return configured
    if site.email:
        return site.email
    return "no-reply@localhost"


def _site_context():
    site = SiteSettings.get()
    logo_url = None
    if getattr(site, "logo", None) and site.logo:
        try:
            from django.contrib.sites.models import Site
            s = Site.objects.get_current()
            domain = (s.domain or "").strip()
            if domain:
                base = ("https://" + domain).rstrip("/")
                logo_url = base + site.logo.url
        except Exception:
            pass
    return {
        "site_settings": site,
        "site_name": site.site_name or "The BARBERSHOP",
        "site_logo_url": logo_url,
    }


def get_staff_admin_emails():
    from apps.accounts.models import User

    return list(
        User.objects.filter(
            role__in=["staff", "admin"],
            is_active=True,
        )
        .exclude(email="")
        .values_list("email", flat=True)
        .distinct()
    )


def send_templated_email(
    subject,
    to_emails,
    template_key,
    context=None,
    reply_to=None,
):
    recipients = [e for e in (to_emails or []) if e]
    if not recipients:
        return 0

    payload = _site_context()
    if context:
        payload.update(context)

    try:
        text_body = render_to_string(f"emails/{template_key}.txt", payload)
        html_body = render_to_string(f"emails/{template_key}.html", payload)
    except Exception:
        logger.exception(
            "Error renderizando template de email '%s'",
            template_key,
        )
        return 0

    site = SiteSettings.get()
    from_email = _default_from_email()
    reply_to_list = reply_to
    if reply_to_list is None and getattr(site, "email", None) and site.email.strip():
        reply_to_list = [site.email.strip()]

    headers = {
        "X-Auto-Response-Suppress": "All",
        "X-Priority": "3",
        "Precedence": "auto",
        "Auto-Submitted": "auto-generated",
        "X-Mailer": "Django (The BARBERSHOP)",
    }

    message = EmailMultiAlternatives(
        subject=subject.strip().replace("\n", " "),
        body=text_body,
        from_email=from_email,
        to=recipients,
        reply_to=reply_to_list,
        headers=headers,
    )
    message.attach_alternative(html_body, "text/html")
    try:
        return message.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Error enviando email '%s' a %s",
            template_key,
            recipients,
        )
        return 0


def notify_new_customer(user):
    try:
        if user.email:
            send_templated_email(
                subject=f"Bienvenido a {SiteSettings.get().site_name}",
                to_emails=[user.email],
                template_key="customer_welcome",
                context={"user": user},
            )

        staff_emails = get_staff_admin_emails()
        send_templated_email(
            subject="Nuevo cliente registrado",
            to_emails=staff_emails,
            template_key="admin_new_customer",
            context={"user": user},
        )
    except Exception:
        logger.exception(
            "Error en notify_new_customer para user=%s",
            getattr(user, "id", None),
        )


def notify_order_created(order):
    try:
        if order.billing_email:
            send_templated_email(
                subject=f"Pedido recibido #{order.order_number}",
                to_emails=[order.billing_email],
                template_key="customer_order_created",
                context={"order": order},
            )

        send_templated_email(
            subject=f"Nuevo pedido #{order.order_number}",
            to_emails=get_staff_admin_emails(),
            template_key="admin_new_order",
            context={"order": order},
        )
    except Exception:
        logger.exception(
            "Error en notify_order_created para order=%s",
            getattr(order, "order_number", None),
        )


def notify_payment_approved(order):
    try:
        if order.billing_email:
            send_templated_email(
                subject=f"Pago aprobado #{order.order_number}",
                to_emails=[order.billing_email],
                template_key="customer_payment_approved",
                context={"order": order},
            )

        send_templated_email(
            subject=f"Pago aprobado en pedido #{order.order_number}",
            to_emails=get_staff_admin_emails(),
            template_key="admin_payment_approved",
            context={"order": order},
        )
    except Exception:
        logger.exception(
            "Error en notify_payment_approved para order=%s",
            getattr(order, "order_number", None),
        )


def notify_payment_failed(order):
    try:
        if order.billing_email:
            send_templated_email(
                subject=f"Pago no completado #{order.order_number}",
                to_emails=[order.billing_email],
                template_key="customer_payment_failed",
                context={"order": order},
            )

        send_templated_email(
            subject=f"Pago fallido en pedido #{order.order_number}",
            to_emails=get_staff_admin_emails(),
            template_key="admin_payment_failed",
            context={"order": order},
        )
    except Exception:
        logger.exception(
            "Error en notify_payment_failed para order=%s",
            getattr(order, "order_number", None),
        )


def notify_low_stock(items):
    try:
        if not items:
            return
        send_templated_email(
            subject="Alerta de stock bajo",
            to_emails=get_staff_admin_emails(),
            template_key="admin_low_stock_alert",
            context={"items": items},
        )
    except Exception:
        logger.exception("Error en notify_low_stock")


def notify_order_note_to_customer(order, note_content):
    """Envía por email al cliente una nota del equipo sobre su pedido."""
    try:
        if not order.billing_email or not (note_content or "").strip():
            return 0
        send_templated_email(
            subject=f"Mensaje sobre tu pedido #{order.order_number}",
            to_emails=[order.billing_email],
            template_key="customer_order_note",
            context={"order": order, "note_content": (note_content or "").strip()},
        )
    except Exception:
        logger.exception(
            "Error enviando nota al cliente para pedido %s", order.order_number
        )
        return 0


def notify_order_status_changed(order):
    """Envía por email al cliente que el estado o pago de su pedido fue actualizado.
    Lanza si el envío falla para que la vista pueda informar al usuario.
    """
    if not order.billing_email:
        return
    sent = send_templated_email(
        subject=f"Actualización de tu pedido #{order.order_number}",
        to_emails=[order.billing_email],
        template_key="customer_order_status_updated",
        context={"order": order},
    )
    if not sent:
        raise RuntimeError(
            "No se pudo enviar el correo de actualización de pedido al cliente"
        )
