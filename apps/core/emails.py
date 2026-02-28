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


def notify_order_pending_payment(order):
    """Envía recordatorio al cliente para que complete el pago de su pedido pendiente."""
    try:
        if not order.billing_email:
            return
        send_templated_email(
            subject=f"Completa tu pedido #{order.order_number}",
            to_emails=[order.billing_email],
            template_key="customer_order_pending_payment",
            context={"order": order},
        )
    except Exception:
        logger.exception(
            "Error en notify_order_pending_payment para order=%s",
            getattr(order, "order_number", None),
        )


def notify_cart_abandoned(email, cart_items, cart_total):
    """
    Envía recordatorio de carrito abandonado.
    cart_items: lista de dicts con product_name, variant (opcional), quantity, total
    cart_total: Decimal o número
    """
    try:
        if not email or not (cart_items or []):
            return
        from decimal import Decimal
        total = Decimal(str(cart_total)) if cart_total is not None else Decimal("0")
        send_templated_email(
            subject="¿Olvidaste algo en tu carrito?",
            to_emails=[email],
            template_key="customer_cart_abandoned",
            context={
                "cart_items": cart_items,
                "cart_total": total,
            },
        )
    except Exception:
        logger.exception(
            "Error en notify_cart_abandoned para email=%s",
            email,
        )


def _build_product_items_for_email(order, include_image=False):
    """Construye lista de items con URLs para emails (reseña, recompra)."""
    from django.contrib.sites.models import Site
    base = getattr(settings, "SITE_URL", "") or ""
    if not base and hasattr(Site, "objects"):
        try:
            s = Site.objects.get_current()
            domain = (s.domain or "").strip()
            if domain:
                base = ("https://" + domain).rstrip("/")
        except Exception:
            pass
    if not base:
        base = "http://localhost:8000"
    base = base.rstrip("/")
    items = []
    for item in order.items.select_related("product").prefetch_related(
            "product__images"
    ).all():
        product = item.product
        path = product.get_absolute_url()
        product_url = base + path
        img_url = None
        if include_image:
            main_img = product.get_main_image()
            if main_img and main_img.image:
                img_url = base + main_img.image.url
        items.append({
            "product_name": item.product_name,
            "variant": str(item.variant) if item.variant else "",
            "product_url": product_url,
            "product_slug": product.slug,
            "product_image_url": img_url,
        })
    return items


def notify_request_review(order):
    """Envía solicitud de reseña con enlaces a cada producto comprado."""
    try:
        if not order.billing_email:
            return
        product_items = _build_product_items_for_email(order, include_image=True)
        if not product_items:
            return
        send_templated_email(
            subject=f"¿Cómo fue tu experiencia con tu pedido #{order.order_number}?",
            to_emails=[order.billing_email],
            template_key="customer_request_review",
            context={
                "order": order,
                "product_items": product_items,
            },
        )
    except Exception:
        logger.exception(
            "Error en notify_request_review para order=%s",
            getattr(order, "order_number", None),
        )


def notify_repurchase_reminder(order):
    """Envía recordatorio de recompra con enlaces a cada producto."""
    try:
        if not order.billing_email:
            return
        product_items = _build_product_items_for_email(order)
        if not product_items:
            return
        send_templated_email(
            subject=f"¿Necesitas reponer? Tus productos de {SiteSettings.get().site_name}",
            to_emails=[order.billing_email],
            template_key="customer_repurchase_reminder",
            context={
                "order": order,
                "product_items": product_items,
            },
        )
    except Exception:
        logger.exception(
            "Error en notify_repurchase_reminder para order=%s",
            getattr(order, "order_number", None),
        )


def notify_back_in_stock(product, email):
    """Notifica que un producto volvió a tener stock."""
    try:
        if not email or not product:
            return
        from django.contrib.sites.models import Site
        base = getattr(settings, "SITE_URL", "") or ""
        if not base:
            try:
                s = Site.objects.get_current()
                domain = (s.domain or "").strip()
                if domain:
                    base = ("https://" + domain).rstrip("/")
            except Exception:
                pass
        if not base:
            base = "http://localhost:8000"
        product_url = base.rstrip("/") + product.get_absolute_url()
        send_templated_email(
            subject=f"¡{product.name} ya está disponible!",
            to_emails=[email],
            template_key="customer_back_in_stock",
            context={
                "product": product,
                "product_url": product_url,
            },
        )
    except Exception:
        logger.exception(
            "Error en notify_back_in_stock para product=%s email=%s",
            getattr(product, "id", None),
            email,
        )


def notify_order_status_changed(order):
    """Envía por email al cliente que el estado o pago de su pedido fue actualizado.
    Lanza si el envío falla para que la vista pueda informar al usuario.
    """
    if not order.billing_email:
        logger.warning(
            "notify_order_status_changed: pedido %s sin billing_email, no se envía correo",
            order.order_number,
        )
        return
    logger.info(
        "Enviando correo actualización de pedido #%s a %s",
        order.order_number,
        order.billing_email,
    )
    sent = send_templated_email(
        subject=f"Actualización de tu pedido #{order.order_number}",
        to_emails=[order.billing_email],
        template_key="customer_order_status_updated",
        context={"order": order},
    )
    if not sent:
        logger.error(
            "send_templated_email devolvió 0 para customer_order_status_updated, pedido %s",
            order.order_number,
        )
        raise RuntimeError(
            "No se pudo enviar el correo de actualización de pedido al cliente"
        )
    logger.info("Correo actualización pedido #%s enviado correctamente", order.order_number)
