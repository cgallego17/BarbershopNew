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
    return {
        "site_settings": site,
        "site_name": site.site_name or "The BARBERSHOP",
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

    text_body = render_to_string(f"emails/{template_key}.txt", payload)
    html_body = render_to_string(f"emails/{template_key}.html", payload)

    message = EmailMultiAlternatives(
        subject=subject.strip().replace("\n", " "),
        body=text_body,
        from_email=_default_from_email(),
        to=recipients,
        reply_to=reply_to or None,
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


def notify_order_created(order):
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


def notify_payment_approved(order):
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


def notify_payment_failed(order):
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


def notify_low_stock(items):
    if not items:
        return
    send_templated_email(
        subject="Alerta de stock bajo",
        to_emails=get_staff_admin_emails(),
        template_key="admin_low_stock_alert",
        context={"items": items},
    )
