"""
Endpoints de integración para sincronización externa.

POST /api/integraciones/sync-stock/
  Recibe un JSON con stock desde sistemas externos (TersaSoft, ERP, etc.)
  y actualiza stock_quantity de los productos locales por external_id.

Autenticación: Header  X-Sync-Api-Key: <STOCK_SYNC_API_KEY>
"""
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def _check_api_key(request):
    """Valida el header X-Sync-Api-Key. Retorna True si es válido."""
    expected = getattr(settings, 'STOCK_SYNC_API_KEY', '').strip()
    if not expected:
        logger.error("STOCK_SYNC_API_KEY no configurado — endpoint deshabilitado.")
        return False
    provided = (
        request.headers.get('X-Sync-Api-Key', '')
        or request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
    )
    return provided == expected


@csrf_exempt
@require_POST
def sync_stock_endpoint(request):
    """
    Recibe un array JSON con items de stock y actualiza los productos locales.

    Payload esperado:
        [
            {"external_id": "200233", "stock": 15},
            {"external_id": "200691", "stock": 0},
            ...
        ]

    Respuesta exitosa (200):
        {
            "ok": true,
            "updated": 12,
            "unchanged": 5,
            "not_found": 2,
            "errors": 0,
            "total_received": 19
        }
    """
    if not _check_api_key(request):
        logger.warning(
            "sync_stock_endpoint: clave API inválida desde %s",
            request.META.get('REMOTE_ADDR', '?'),
        )
        return JsonResponse({'ok': False, 'error': 'Unauthorized'}, status=401)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    if not isinstance(payload, list):
        return JsonResponse(
            {'ok': False, 'error': 'Expected a JSON array'},
            status=400,
        )

    from apps.products.models import Product

    updated = unchanged = not_found = errors = 0

    for item in payload:
        ext_id = str(item.get('external_id', '')).strip()
        if not ext_id:
            errors += 1
            continue

        try:
            new_stock = max(0, int(item.get('stock', 0)))
        except (TypeError, ValueError):
            errors += 1
            logger.warning("sync_stock: valor de stock inválido para external_id=%s", ext_id)
            continue

        product = Product.objects.filter(external_id=ext_id, source='api').first()
        if not product:
            not_found += 1
            continue

        if product.stock_quantity == new_stock:
            unchanged += 1
            continue

        try:
            product.stock_quantity = new_stock
            product.manage_stock = True
            product.save(update_fields=['stock_quantity', 'manage_stock', 'updated_at'])
            updated += 1
        except Exception as exc:
            errors += 1
            logger.error(
                "sync_stock: error guardando producto external_id=%s: %s", ext_id, exc
            )

    logger.info(
        "sync_stock: updated=%d unchanged=%d not_found=%d errors=%d total=%d",
        updated, unchanged, not_found, errors, len(payload),
    )

    return JsonResponse({
        'ok': True,
        'updated': updated,
        'unchanged': unchanged,
        'not_found': not_found,
        'errors': errors,
        'total_received': len(payload),
    })
