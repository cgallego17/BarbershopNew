"""
Integración Wompi — flujo completo:
  1. payment_page      → Muestra formulario con widget/redirect Wompi
  2. payment_return    → Wompi redirige aquí después del pago; consulta estado vía API
  3. wompi_webhook     → Evento server-to-server; actualiza BD, descuenta stock, aplica cupón
"""
import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import models, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.orders.models import Order, OrderItem
from apps.core.emails import (
    notify_low_stock,
    notify_payment_approved,
    notify_payment_failed,
)
from .models import WompiTransaction

logger = logging.getLogger(__name__)
GUEST_ORDER_SESSION_KEY = 'guest_order_numbers'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wompi_api_base() -> str:
    env = getattr(settings, 'WOMPI_ENV', 'sandbox')
    return (
        'https://sandbox.wompi.co/v1'
        if env == 'sandbox'
        else 'https://production.wompi.co/v1'
    )


def _integrity_hash(reference: str, amount_in_cents: int, currency: str) -> str:
    """
    Firma de integridad requerida por Wompi:
    SHA256(reference + amount_in_cents + currency + integrity_secret)
    """
    secret = getattr(settings, 'WOMPI_INTEGRITY_SECRET', '')
    raw = f"{reference}{amount_in_cents}{currency}{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _verify_webhook_signature(body: dict) -> bool:
    """
    Verifica checksum del webhook de Wompi.

    Wompi construye la firma así:
      SHA256( prop1_val + prop2_val + ... + timestamp + events_secret )
    donde propX_val se resuelve desde body["data"] usando la notación
    de puntos que Wompi envía en signature.properties
    (ej. "transaction.id" → body["data"]["transaction"]["id"]).

    Si WOMPI_EVENTS_SECRET no está configurado se acepta el webhook
    (ambiente de desarrollo/sandbox sin secreto definido).
    """
    events_secret = getattr(settings, 'WOMPI_EVENTS_SECRET', '').strip()
    if not events_secret:
        logger.warning(
            "WOMPI_EVENTS_SECRET no configurado — webhook aceptado sin verificar firma."
        )
        return True

    signature  = body.get('signature', {})
    checksum   = signature.get('checksum', '')
    properties = signature.get('properties', [])
    timestamp  = body.get('timestamp', '')

    # Los valores de las propiedades viven en body["data"]
    data = body.get('data', {})

    parts = []
    for prop in properties:
        val = data
        for key in prop.split('.'):
            val = val.get(key, '') if isinstance(val, dict) else ''
        parts.append(str(val))
    parts.append(str(timestamp))
    parts.append(events_secret)

    computed = hashlib.sha256(''.join(parts).encode()).hexdigest()
    ok = hmac.compare_digest(computed, checksum)
    if not ok:
        logger.warning(
            "Firma Wompi inválida. computed=%s checksum=%s", computed, checksum
        )
    return ok


def _fetch_transaction_from_wompi(transaction_id: str) -> dict:
    """Consulta una transacción en la API de Wompi y devuelve los datos."""
    url = f"{_wompi_api_base()}/transactions/{transaction_id}"
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {settings.WOMPI_PRIVATE_KEY}'},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get('data', {})
    except Exception as exc:
        logger.error("Error consultando transacción Wompi %s: %s", transaction_id, exc)
        return {}


def _is_transaction_consistent(order: Order, tx_data: dict) -> bool:
    """Valida referencia, moneda y monto contra el pedido."""
    if str(tx_data.get('reference', '')) != order.order_number:
        return False
    currency = (tx_data.get('currency') or '').strip().upper()
    if currency != 'COP':
        return False
    try:
        tx_amount = int(tx_data.get('amount_in_cents', 0))
        expected = int((Decimal(order.total) * 100).quantize(Decimal('1')))
    except (TypeError, ValueError, InvalidOperation):
        return False
    return tx_amount == expected


def _can_access_order(request, order: Order) -> bool:
    if order.user_id:
        return request.user.is_authenticated and request.user.id == order.user_id
    guest_orders = request.session.get(GUEST_ORDER_SESSION_KEY, [])
    return order.order_number in guest_orders


def _save_transaction(order: Order, tx_data: dict) -> WompiTransaction:
    """Guarda o actualiza el registro de transacción en BD."""
    wompi_id = str(tx_data.get('id', ''))
    if not wompi_id:
        return None
    obj, _ = WompiTransaction.objects.update_or_create(
        wompi_id=wompi_id,
        defaults={
            'order':               order,
            'reference':           tx_data.get('reference', ''),
            'status':              tx_data.get('status', 'PENDING'),
            'amount_in_cents':     tx_data.get('amount_in_cents', 0),
            'currency':            tx_data.get('currency', 'COP'),
            'payment_method_type': tx_data.get('payment_method_type', ''),
            'raw_data':            tx_data,
        },
    )
    return obj


@transaction.atomic
def _fulfill_order(order: Order, tx_data: dict):
    """
    Procesa un pago APPROVED (idempotente):
      - Marca pedido como pagado / en procesamiento
      - Descuenta stock de producto/variante
      - Incrementa usage_count del cupón
    """
    # Refrescar con lock para evitar doble procesamiento
    order = Order.objects.select_for_update().get(pk=order.pk)

    if order.payment_status == 'paid':
        logger.info("Orden %s ya fue procesada anteriormente, omitiendo.", order.order_number)
        return

    # 1. Actualizar estados del pedido
    order.payment_status = 'paid'
    order.status = 'processing'
    order.save(update_fields=['payment_status', 'status', 'updated_at'])

    # 2. Descontar inventario
    low_stock_alerts = []
    for item in order.items.select_related('product', 'variant').all():
        qty = item.quantity

        if item.variant:
            from apps.products.models import ProductVariant
            updated = ProductVariant.objects.filter(
                id=item.variant.id,
                stock_quantity__gte=qty,
            ).update(stock_quantity=models.F('stock_quantity') - qty)
            if not updated:
                # Stock insuficiente: restar hasta 0
                ProductVariant.objects.filter(id=item.variant.id).update(
                    stock_quantity=0
                )
            current_variant = ProductVariant.objects.filter(id=item.variant.id).first()
            if current_variant and current_variant.stock_quantity <= 5:
                low_stock_alerts.append(
                    f"Variante {current_variant} con stock {current_variant.stock_quantity}"
                )
        else:
            product = item.product
            if product.manage_stock:
                from apps.products.models import Product
                updated = Product.objects.filter(
                    id=product.id,
                    stock_quantity__gte=qty,
                ).update(stock_quantity=models.F('stock_quantity') - qty)
                if not updated:
                    Product.objects.filter(id=product.id).update(
                        stock_quantity=0
                    )
                current_product = Product.objects.filter(id=product.id).first()
                if current_product and current_product.stock_quantity <= 5:
                    low_stock_alerts.append(
                        f"Producto {current_product.name} con stock {current_product.stock_quantity}"
                    )

    # 3. Incrementar uso de cupón
    if order.coupon_code:
        from apps.coupons.models import Coupon
        Coupon.objects.filter(code=order.coupon_code).update(
            usage_count=models.F('usage_count') + 1
        )

    logger.info(
        "Orden %s procesada: pago aprobado (Wompi %s).",
        order.order_number,
        tx_data.get('id', ''),
    )
    notify_payment_approved(order)
    notify_low_stock(low_stock_alerts)


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------

def payment_page(request, order_number):
    """Página de pago: muestra el formulario con redirect a Wompi."""
    order = get_object_or_404(Order, order_number=order_number)

    # Seguridad: sólo el dueño del pedido o el invitado que lo creó.
    if not _can_access_order(request, order):
        return redirect('core:home')

    # Si ya fue pagado, ir directo al detalle
    if order.payment_status == 'paid':
        return redirect('orders:detail', order_number=order_number)

    currency       = 'COP'
    amount_cents   = int(order.total * 100)
    redirect_url = (
        getattr(settings, 'WOMPI_REDIRECT_URL', '').strip()
        or request.build_absolute_uri('/pagos/confirmacion/')
    )
    integrity      = _integrity_hash(order_number, amount_cents, currency)

    context = {
        'order':           order,
        'public_key':      getattr(settings, 'WOMPI_PUBLIC_KEY', ''),
        'currency':        currency,
        'amount_cents':    amount_cents,
        'reference':       order_number,
        'redirect_url':    redirect_url,
        'integrity_hash':  integrity,
        'wompi_env':       getattr(settings, 'WOMPI_ENV', 'sandbox'),
    }
    return render(request, 'payments/payment_page.html', context)


def payment_return(request):
    """
    Wompi redirige aquí tras el pago con ?id=<wompi_transaction_id>.
    Consultamos la API para obtener el estado actualizado.
    """
    transaction_id = request.GET.get('id', '').strip()
    if not transaction_id:
        return redirect('core:home')

    tx_data   = _fetch_transaction_from_wompi(transaction_id)
    reference = tx_data.get('reference', '')
    status    = tx_data.get('status', 'ERROR')

    order = Order.objects.filter(order_number=reference).first()

    if order and not _can_access_order(request, order):
        order = None

    if order and tx_data.get('id'):
        _save_transaction(order, tx_data)
        if status == 'APPROVED' and _is_transaction_consistent(order, tx_data):
            _fulfill_order(order, tx_data)
        elif status == 'APPROVED':
            logger.warning(
                "Wompi return inconsistente para %s: amount/currency/reference no coincide.",
                order.order_number,
            )
            status = 'ERROR'
        elif status in ('DECLINED', 'VOIDED', 'ERROR'):
            if order.payment_status not in ('paid', 'failed'):
                order.payment_status = 'failed'
                order.save(update_fields=['payment_status', 'updated_at'])
                notify_payment_failed(order)

    STATUS_LABELS = {
        'APPROVED': ('success', '¡Pago aprobado!',      'Tu pedido está en proceso.'),
        'PENDING':  ('warning', 'Pago en proceso…',     'Tu transacción está siendo verificada.'),
        'DECLINED': ('error',   'Pago declinado',       'Tu banco rechazó el pago. Puedes intentar de nuevo.'),
        'VOIDED':   ('error',   'Pago anulado',         'La transacción fue anulada.'),
        'ERROR':    ('error',   'Error en el pago',     'Ocurrió un error. Contacta soporte si el dinero fue debitado.'),
    }
    kind, title, subtitle = STATUS_LABELS.get(status, STATUS_LABELS['ERROR'])

    context = {
        'order':          order,
        'status':         status,
        'kind':           kind,
        'title':          title,
        'subtitle':       subtitle,
        'transaction_id': transaction_id,
    }
    return render(request, 'payments/payment_result.html', context)


@csrf_exempt
@require_POST
def wompi_webhook(request):
    """
    Webhook de eventos Wompi (server-to-server).
    Endpoint público, verificado con firma HMAC-SHA256.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse('Bad Request', status=400)

    if not _verify_webhook_signature(body):
        logger.warning("Firma Wompi inválida — webhook rechazado.")
        return HttpResponse('Unauthorized', status=401)

    event = body.get('event', '')

    if event == 'transaction.updated':
        tx_data   = body.get('data', {}).get('transaction', {})
        reference = tx_data.get('reference', '')
        status    = tx_data.get('status', '')

        order = Order.objects.filter(order_number=reference).first()
        if order:
            _save_transaction(order, tx_data)
            if status == 'APPROVED' and _is_transaction_consistent(order, tx_data):
                _fulfill_order(order, tx_data)
            elif status == 'APPROVED':
                logger.warning(
                    "Webhook Wompi inconsistente para %s: amount/currency/reference no coincide.",
                    order.order_number,
                )
            elif status in ('DECLINED', 'VOIDED', 'ERROR'):
                if order.payment_status not in ('paid', 'failed'):
                    order.payment_status = 'failed'
                    order.save(update_fields=['payment_status', 'updated_at'])
                    notify_payment_failed(order)
        else:
            logger.warning("Webhook Wompi: pedido %s no encontrado.", reference)

    return HttpResponse('OK', status=200)


def payment_status_api(request, order_number):
    """
    Mini-API JSON para polling del estado de pago desde el frontend.
    Útil para actualizar la página de resultado sin recargar.
    """
    order = Order.objects.filter(order_number=order_number).only(
        'payment_status', 'status', 'user_id', 'order_number'
    ).first()
    if not order:
        return JsonResponse({'error': 'not found'}, status=404)
    if not _can_access_order(request, order):
        return JsonResponse({'error': 'forbidden'}, status=403)
    return JsonResponse({
        'payment_status': order.payment_status,
        'order_status':   order.status,
    })
