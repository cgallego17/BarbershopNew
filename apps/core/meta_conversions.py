"""
Meta Conversions API - Envío de eventos desde el servidor.

Documentación: https://developers.facebook.com/docs/marketing-api/conversions-api
"""
import hashlib
import logging
import time
from datetime import date, datetime

import requests

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = 'v21.0'
# Dataset Quality API: usar v22.0+ según doc de Meta
DATASET_QUALITY_API_VERSION = 'v22.0'


def _hash_sha256(value):
    """Normaliza y hashea un valor para user_data de Meta (requerido para PII)."""
    if not value or not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def _hash_phone(value):
    """Extrae dígitos del teléfono y hashea."""
    if not value or not isinstance(value, str):
        return None
    digits = ''.join(c for c in value if c.isdigit())
    if not digits:
        return None
    return hashlib.sha256(digits.encode('utf-8')).hexdigest()


def _normalize_dob(value):
    """
    Convierte fecha de nacimiento a formato YYYYMMDD (antes de hash).
    Acepta date/datetime o string.
    """
    if not value:
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y%m%d')
    if isinstance(value, date):
        return value.strftime('%Y%m%d')
    if isinstance(value, str):
        digits = ''.join(c for c in value if c.isdigit())
        if len(digits) == 8:
            return digits
    return None


def _normalize_gender(value):
    """Normaliza género a 'm' o 'f' cuando es posible."""
    if not value:
        return None
    val = str(value).strip().lower()
    if val in ('m', 'male', 'masculino', 'hombre'):
        return 'm'
    if val in ('f', 'female', 'femenino', 'mujer'):
        return 'f'
    return None


def _build_user_data(
    email=None,
    phone=None,
    first_name=None,
    last_name=None,
    date_of_birth=None,
    gender=None,
    city=None,
    state=None,
    zip_code=None,
    country=None,
    external_id=None,
    fbp=None,
    fbc=None,
    client_ip_address=None,
    client_user_agent=None,
):
    """
    Construye el objeto user_data para la Conversions API.
    client_ip_address y client_user_agent son requeridos para website (mejoran EMQ).
    """
    data = {}
    if email:
        h = _hash_sha256(email)
        if h:
            data['em'] = [h]
    if phone:
        h = _hash_phone(phone)
        if h:
            data['ph'] = [h]
    if first_name:
        h = _hash_sha256(first_name)
        if h:
            data['fn'] = [h]
    if last_name:
        h = _hash_sha256(last_name)
        if h:
            data['ln'] = [h]
    if date_of_birth:
        dob = _normalize_dob(date_of_birth)
        h = _hash_sha256(dob) if dob else None
        if h:
            data['db'] = [h]
    if gender:
        ge = _normalize_gender(gender)
        h = _hash_sha256(ge) if ge else None
        if h:
            data['ge'] = [h]
    if city:
        h = _hash_sha256(city)
        if h:
            data['ct'] = [h]
    if state:
        h = _hash_sha256(state)
        if h:
            data['st'] = [h]
    if zip_code:
        h = _hash_sha256(str(zip_code))
        if h:
            data['zp'] = [h]
    if country:
        h = _hash_sha256(country)
        if h:
            data['country'] = [h]
    if external_id:
        h = _hash_sha256(str(external_id))
        if h:
            data['external_id'] = [h]
    if fbp:
        data['fbp'] = fbp
    if fbc:
        data['fbc'] = fbc
    if client_ip_address:
        data['client_ip_address'] = str(client_ip_address)[:45]
    if client_user_agent:
        data['client_user_agent'] = str(client_user_agent)[:256]
    return data


def _get_client_ip(request):
    """Obtiene la IP del cliente, considerando X-Forwarded-For."""
    if not request:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def send_event(
    pixel_id,
    access_token,
    event_name,
    user_data,
    custom_data,
    event_id=None,
    event_source_url=None,
    action_source='website',
    test_event_code=None,
):
    """
    Envía un evento a la Conversions API de Meta.

    Args:
        pixel_id: ID del pixel de Meta
        access_token: Token de acceso (de Events Manager)
        event_name: Nombre del evento (Purchase, AddToCart, ViewContent, InitiateCheckout, etc.)
        user_data: dict con datos hasheados (em, ph, fn, ln, fbp, fbc, client_ip_address, client_user_agent)
        custom_data: dict con value, currency, content_ids, contents, order_id, etc.
        event_id: ID único para deduplicación (mismo que eventID en el pixel del cliente)
        event_source_url: URL de la página donde ocurrió el evento (requerido para website)
        action_source: "website" por defecto (requerido para web)
        test_event_code: Código para Test Events Tool (ej: TEST12345)

    Returns:
        bool: True si el envío fue exitoso
    """
    if not pixel_id or not access_token:
        return False

    event_time = int(time.time())
    event = {
        'event_name': event_name,
        'event_time': event_time,
        'action_source': action_source,
        'user_data': user_data,
        'custom_data': custom_data,
    }
    if event_id:
        event['event_id'] = event_id
    if event_source_url:
        event['event_source_url'] = str(event_source_url)[:256]
    payload = {'data': [event]}
    if test_event_code:
        payload['test_event_code'] = str(test_event_code)[:20]
    url = f'https://graph.facebook.com/{GRAPH_API_VERSION}/{pixel_id}/events'
    params = {'access_token': access_token}

    try:
        resp = requests.post(url, params=params, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get('events_received', 0) < 1:
            logger.warning(
                'Meta CAPI: evento %s no recibido. Respuesta: %s',
                event_name, data
            )
            return False
        return True
    except requests.RequestException as e:
        logger.exception('Meta CAPI: error enviando evento %s: %s', event_name, e)
        return False


def send_purchase(order, request=None):
    """
    Envía evento Purchase cuando un pedido es pagado.
    Para Purchase (webhook) normalmente no hay request; se usan meta_client_ip y meta_client_user_agent
    guardados en el pedido al visitar la página de pago.
    """
    from apps.core.models import SiteSettings
    settings = SiteSettings.get()
    if not settings.meta_pixel_id or not settings.meta_conversions_api_token:
        return

    items = list(order.items.select_related('product').all())
    content_ids = [str(item.product_id) for item in items]
    contents = [{'id': str(item.product_id), 'quantity': item.quantity} for item in items]

    client_ip = _get_client_ip(request) if request else (getattr(order, 'meta_client_ip', None) or '').strip() or None
    client_ua = (request.META.get('HTTP_USER_AGENT') or '')[:256] if request else (getattr(order, 'meta_client_user_agent', None) or '').strip()[:256] or None
    fbp = request.COOKIES.get('_fbp') if request else None
    fbc = request.COOKIES.get('_fbc') if request else None

    user_data = _build_user_data(
        email=order.billing_email,
        phone=order.billing_phone,
        first_name=order.billing_first_name,
        last_name=order.billing_last_name,
        date_of_birth=order.billing_date_of_birth,
        city=order.billing_city,
        state=order.billing_state,
        zip_code=order.billing_postal_code,
        country=order.billing_country,
        external_id=order.user_id,
        fbp=fbp or (getattr(order, 'meta_fbp', None) or None),
        fbc=fbc or (getattr(order, 'meta_fbc', None) or None),
        client_ip_address=client_ip,
        client_user_agent=client_ua,
    )

    custom_data = {
        'currency': 'COP',
        'value': float(order.total),
        'content_ids': content_ids,
        'content_type': 'product',
        'num_items': sum(item.quantity for item in items),
        'order_id': order.order_number,
        'contents': contents,
    }

    base = (settings.site_url or '').strip().rstrip('/') or 'https://barbershop.com.co'
    event_source_url = f'{base}/pedidos/pedido/{order.order_number}/'

    send_event(
        pixel_id=settings.meta_pixel_id,
        access_token=settings.meta_conversions_api_token,
        event_name='Purchase',
        user_data=user_data,
        custom_data=custom_data,
        event_id=f"purchase_{order.order_number}",
        event_source_url=event_source_url,
        test_event_code=getattr(settings, 'meta_test_event_code', None) or None,
    )


def send_add_to_cart(
    product_id, product_name, value, quantity, email=None, phone=None,
    first_name=None, last_name=None, city=None, state=None,
    zip_code=None, country=None, external_id=None,
    event_id=None, request=None, fbp=None, fbc=None,
):
    """Envía evento AddToCart."""
    from apps.core.models import SiteSettings
    settings = SiteSettings.get()
    if not settings.meta_pixel_id or not settings.meta_conversions_api_token:
        return

    client_ip = _get_client_ip(request) if request else None
    client_ua = (request.META.get('HTTP_USER_AGENT') or '')[:256] if request else None
    event_source_url = request.build_absolute_uri() if request else None

    user_data = _build_user_data(
        email=email, phone=phone,
        first_name=first_name, last_name=last_name,
        city=city, state=state, zip_code=zip_code, country=country,
        external_id=external_id,
        client_ip_address=client_ip, client_user_agent=client_ua,
        fbp=fbp, fbc=fbc,
    )

    custom_data = {
        'content_ids': [str(product_id)],
        'content_name': product_name,
        'content_type': 'product',
        'value': float(value),
        'currency': 'COP',
        'num_items': quantity,
        'contents': [{'id': str(product_id), 'quantity': quantity}],
    }

    send_event(
        pixel_id=settings.meta_pixel_id,
        access_token=settings.meta_conversions_api_token,
        event_name='AddToCart',
        user_data=user_data,
        custom_data=custom_data,
        event_id=event_id,
        event_source_url=event_source_url,
        test_event_code=getattr(settings, 'meta_test_event_code', None) or None,
    )


def send_view_content(
    product_id, product_name, value, email=None, phone=None,
    first_name=None, last_name=None, city=None, state=None,
    zip_code=None, country=None, external_id=None,
    event_id=None, request=None, fbp=None, fbc=None,
):
    """Envía evento ViewContent (vista de detalle de producto)."""
    from apps.core.models import SiteSettings
    settings = SiteSettings.get()
    if not settings.meta_pixel_id or not settings.meta_conversions_api_token:
        return

    client_ip = _get_client_ip(request) if request else None
    client_ua = (request.META.get('HTTP_USER_AGENT') or '')[:256] if request else None
    event_source_url = request.build_absolute_uri() if request else None

    user_data = _build_user_data(
        email=email, phone=phone,
        first_name=first_name, last_name=last_name,
        city=city, state=state, zip_code=zip_code, country=country,
        external_id=external_id,
        client_ip_address=client_ip, client_user_agent=client_ua,
        fbp=fbp, fbc=fbc,
    )

    custom_data = {
        'content_ids': [str(product_id)],
        'content_name': product_name,
        'content_type': 'product',
        'value': float(value),
        'currency': 'COP',
        'contents': [{'id': str(product_id), 'quantity': 1}],
    }

    send_event(
        pixel_id=settings.meta_pixel_id,
        access_token=settings.meta_conversions_api_token,
        event_name='ViewContent',
        user_data=user_data,
        custom_data=custom_data,
        event_id=event_id,
        event_source_url=event_source_url,
        test_event_code=getattr(settings, 'meta_test_event_code', None) or None,
    )


def send_initiate_checkout(
    cart_items, cart_total, email=None, phone=None,
    first_name=None, last_name=None, city=None, state=None,
    zip_code=None, country=None, external_id=None,
    event_id=None, request=None, fbp=None, fbc=None,
):
    """
    Envía evento InitiateCheckout.
    cart_items: lista de dicts con product_id, product_name, price, quantity
    """
    from apps.core.models import SiteSettings
    settings = SiteSettings.get()
    if not settings.meta_pixel_id or not settings.meta_conversions_api_token:
        return

    client_ip = _get_client_ip(request) if request else None
    client_ua = (request.META.get('HTTP_USER_AGENT') or '')[:256] if request else None
    event_source_url = request.build_absolute_uri() if request else None

    user_data = _build_user_data(
        email=email, phone=phone,
        first_name=first_name, last_name=last_name,
        city=city, state=state, zip_code=zip_code, country=country,
        external_id=external_id,
        client_ip_address=client_ip, client_user_agent=client_ua,
        fbp=fbp, fbc=fbc,
    )

    content_ids = [str(item['product_id']) for item in cart_items]
    contents = [{'id': str(item['product_id']), 'quantity': item['quantity']} for item in cart_items]
    num_items = sum(item['quantity'] for item in cart_items)

    custom_data = {
        'currency': 'COP',
        'value': float(cart_total),
        'content_ids': content_ids,
        'num_items': num_items,
        'contents': contents,
    }

    send_event(
        pixel_id=settings.meta_pixel_id,
        access_token=settings.meta_conversions_api_token,
        event_name='InitiateCheckout',
        user_data=user_data,
        custom_data=custom_data,
        event_id=event_id,
        event_source_url=event_source_url,
        test_event_code=getattr(settings, 'meta_test_event_code', None) or None,
    )


# ---------------------------------------------------------------------------
# Dataset Quality API
# https://developers.facebook.com/docs/marketing-api/conversions-api/dataset-quality-api/
# ---------------------------------------------------------------------------


def fetch_dataset_quality(pixel_id=None, access_token=None, agent_name=None):
    """
    Obtiene métricas de calidad del dataset desde el Dataset Quality API de Meta.

    https://developers.facebook.com/docs/marketing-api/conversions-api/dataset-quality-api/

    Returns:
        dict: Respuesta de la API con web[...] o None si hay error.
    """
    from apps.core.models import SiteSettings
    settings = SiteSettings.get()
    pixel_id = pixel_id or (settings.meta_pixel_id or '').strip()
    access_token = access_token or (settings.meta_conversions_api_token or '').strip()

    if not pixel_id or not access_token:
        return {'error': 'Configura meta_pixel_id y meta_conversions_api_token en Configuración.'}

    url = f'https://graph.facebook.com/{DATASET_QUALITY_API_VERSION}/dataset_quality'
    # Campos según https://developers.facebook.com/docs/marketing-api/conversions-api/dataset-quality-api/
    fields = (
        'web{event_name,'
        'event_match_quality{composite_score,diagnostics{name,description,solution,percentage}},'
        'event_coverage{percentage,goal_percentage,description},'
        'dedupe_key_feedback{dedupe_key,browser_events_with_dedupe_key{percentage},server_events_with_dedupe_key{percentage}},'
        'data_freshness{upload_frequency,description},'
        'acr{description,percentage}}'
    )
    params = {
        'dataset_id': pixel_id,
        'access_token': access_token,
        'fields': fields,
    }
    if agent_name:
        params['agent_name'] = agent_name

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.exception('Dataset Quality API: error %s', e)
        err_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                err_body = e.response.json()
                err_msg = err_body.get('error', {}).get('message', err_msg)
            except Exception:
                pass
        return {'error': err_msg}
