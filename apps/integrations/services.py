"""
Servicios de integración con API de productos y ERP.
Configura PRODUCTS_API_URL, PRODUCTS_API_KEY, ERP_API_URL, ERP_API_KEY en .env
"""
import logging
import os
import re

import requests
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify

logger = logging.getLogger(__name__)

# API Tersa Cosmeticos - productos públicos
TERSA_API_URL = 'https://tersacosmeticos.com/prod/api/productos-publicos/'
TERSA_BASE_URL = 'https://tersacosmeticos.com'
TERSA_BRANDS = ['BARBERSHOP', 'BARBER UP']
# IDs de la API a importar además de las marcas BARBERSHOP y BARBER UP
TERSA_EXTRA_PRODUCT_IDS = [
    '200233', '200691', '200692', '200693', '200694', '200699', '200068',
]


def fetch_tersa_products(brands=None, extra_ids=None):
    """
    Obtiene productos desde la API de Tersa Cosmeticos.
    Filtra por nombre_marca en BARBERSHOP y BARBER UP, más los IDs extra indicados.
    """
    brands = brands or TERSA_BRANDS
    extra_ids = extra_ids if extra_ids is not None else TERSA_EXTRA_PRODUCT_IDS
    extra_set = {str(i).strip() for i in extra_ids if i}
    try:
        response = requests.get(TERSA_API_URL, timeout=60)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return []
        brand_set = {b.upper() for b in brands}
        return [
            p for p in data
            if (p.get('nombre_marca') or '').strip().upper() in brand_set
            or str(p.get('id', '')).strip() in extra_set
        ]
    except Exception as e:
        logger.exception("Error fetching Tersa products")
        raise Exception(f"Error fetching Tersa API: {e}")


def _download_image(url):
    """Descarga imagen desde URL y devuelve (filename, ContentFile) o None si falla."""
    if not url or url.endswith('/media/0') or url == '/media/0':
        return None
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        if not resp.content or len(resp.content) < 100:
            return None
        ext = '.jpg'
        ct = resp.headers.get('Content-Type', '')
        if 'png' in ct:
            ext = '.png'
        elif 'webp' in ct:
            ext = '.webp'
        else:
            # Inferir por magic bytes
            if resp.content[:8] == b'\x89PNG\r\n\x1a\n':
                ext = '.png'
            elif resp.content[:2] == b'\xff\xd8':
                ext = '.jpg'
        name = re.sub(r'[^\w\-.]', '_', os.path.basename(url.split('?')[0])) or 'image'
        if not name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            name += ext
        return (name[:100], ContentFile(resp.content))
    except Exception:
        return None


def sync_tersa_products(brands=None, download_images=True):
    """
    Sincroniza productos desde la API Tersa (solo BARBERSHOP y BARBER UP).
    Crea/actualiza Product, Brand y Category según corresponda.
    """
    from apps.products.models import Product, ProductImage, Category, Brand

    data = fetch_tersa_products(brands=brands)
    created = updated = 0

    for item in data:
        external_id = str(item.get('id', ''))
        nombre = (item.get('nombre_producto') or 'Sin nombre').strip()
        attr = (item.get('nombreAtributo') or '').strip()
        if attr and attr.upper() != 'SIN ATRIBUTO':
            nombre = f"{nombre} {attr}"
        sku = (item.get('codigo') or '').strip() or (f"TERSA-{external_id}" if external_id else None)
        precio = item.get('precio5') or item.get('precio_min') or 0
        try:
            price = Decimal(str(precio))
        except Exception:
            price = Decimal('0')
        ficha = item.get('ficha_tecnica') or {}
        descripcion = ficha.get('descripcion', '') or ''
        short = (descripcion[:500] + '...') if len(descripcion) > 500 else descripcion
        cat_name = (ficha.get('categoria') or '').strip()
        if not cat_name or cat_name.upper() in ('SIN CATEGORIA', 'S/A', 'N/A'):
            cat_name = 'General'
        category = None
        if cat_name:
            cat_slug = slugify(cat_name) or 'general'
            category, _ = Category.objects.get_or_create(
                slug=cat_slug,
                defaults={'name': cat_name, 'is_active': True}
            )
        brand_name = (item.get('nombre_marca') or '').strip()
        brand = None
        if brand_name:
            brand_slug = slugify(brand_name) or brand_name.lower().replace(' ', '-')
            brand, _ = Brand.objects.get_or_create(
                slug=brand_slug,
                defaults={'name': brand_name, 'is_active': True}
            )
        base_slug = slugify(nombre)
        slug = f"{base_slug}-{external_id}" if external_id else f"{base_slug}-{hash(nombre) % 10**8}"
        estado = item.get('estado', True)
        if isinstance(estado, str):
            estado = estado.lower() in ('true', '1', 'si', 'yes', 'activo')

        # SKU único: TERSA-{id} para evitar colisiones con codigo repetido
        api_sku = f"TERSA-{external_id}" if external_id else (sku or f"TERSA-{hash(nombre) % 10**10}")
        codigo_api = (item.get('codigo') or '').strip()
        defaults = {
            'name': nombre,
            'slug': slug,
            'sku': api_sku,
            'codigo': codigo_api,
            'external_id': external_id,
            'regular_price': price,
            'short_description': short,
            'description': descripcion,
            'is_active': estado,
            'source': 'api',
            # Stock gestionado exclusivamente por push_stock_barbershop (bodega 2).
            # El importador no sobreescribe stock ni umbral.
            'manage_stock': True,
        }
        if brand:
            defaults['brand'] = brand
        lookup = {'external_id': external_id, 'source': 'api'} if external_id else {'sku': api_sku, 'source': 'api'}
        product, created_flag = Product.objects.update_or_create(defaults=defaults, **lookup)
        # Asignar categorías solo si el producto es nuevo; si ya existía no las tocamos
        if created_flag:
            if category:
                product.categories.set([category])
            else:
                product.categories.clear()
        if created_flag:
            created += 1
        else:
            updated += 1

        # Imagen: descargar si no hay imágenes y la API tiene URL
        if download_images and not product.images.exists():
            img_path = item.get('imagen') or ''
            if img_path and not img_path.endswith('/media/0'):
                url = img_path if img_path.startswith('http') else f"{TERSA_BASE_URL.rstrip('/')}{img_path}"
                result = _download_image(url)
                if result:
                    filename, content = result
                    try:
                        pi = ProductImage(product=product, order=0, is_primary=True, alt_text=nombre[:255])
                        pi.image.save(filename, content, save=True)
                    except Exception as e:
                        logger.warning("No se pudo guardar imagen para %s: %s", sku, e)

    return {'created': created, 'updated': updated, 'total': len(data)}


def fetch_products_from_api():
    """Obtiene productos desde API externa."""
    url = settings.PRODUCTS_API_URL
    if not url:
        return []
    headers = {}
    if settings.PRODUCTS_API_KEY:
        headers['Authorization'] = f'Bearer {settings.PRODUCTS_API_KEY}'
        headers['X-API-Key'] = settings.PRODUCTS_API_KEY
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        if isinstance(data, dict) and 'products' in data:
            return data['products']
        if isinstance(data, dict) and 'items' in data:
            return data['items']
        return []
    except Exception as e:
        raise Exception(f"Error fetching products API: {e}")


def sync_products_from_api():
    """Sincroniza productos desde API al modelo local."""
    from apps.products.models import Product, Category

    data = fetch_products_from_api()
    created = updated = 0

    for item in data:
        external_id = str(item.get('id') or item.get('external_id', '')).strip() or None
        name = item.get('name') or item.get('title') or item.get('nombre', 'Sin nombre')
        sku = item.get('sku') or item.get('codigo') or (f"API-{external_id}" if external_id else None)
        codigo_api = (item.get('codigo') or '').strip()
        price = item.get('price') or item.get('precio') or item.get('regular_price', 0)
        if isinstance(price, str):
            price = Decimal(price.replace(',', '.'))
        else:
            price = Decimal(str(price))
        description = item.get('description') or item.get('descripcion', '')
        image_url = item.get('image') or item.get('imagen') or item.get('thumbnail')
        api_sku = sku or (f"API-{external_id}" if external_id else f"API-{hash(name) % 10**10}")
        base_slug = slugify(name)
        slug = f"{base_slug}-{external_id}" if external_id else f"{base_slug}-{hash(name) % 10**6}"
        lookup = {'external_id': external_id, 'source': 'api'} if external_id else {'sku': api_sku, 'source': 'api'}
        product, created_flag = Product.objects.update_or_create(
            defaults={
                'name': name,
                'slug': slug,
                'sku': api_sku,
                'codigo': codigo_api,
                'external_id': external_id or '',
                'regular_price': price,
                'short_description': description[:500] if description else '',
                'description': description,
                'is_active': item.get('is_active', item.get('activo', True)),
            },
            **lookup
        )
        if created_flag:
            created += 1
        else:
            updated += 1

    return {'created': created, 'updated': updated}


def send_order_to_erp(order):
    """Envía pedido al ERP Django."""
    url = settings.ERP_API_URL
    if not url:
        return None
    headers = {'Content-Type': 'application/json'}
    if settings.ERP_API_KEY:
        headers['Authorization'] = f'Bearer {settings.ERP_API_KEY}'
        headers['X-API-Key'] = settings.ERP_API_KEY

    payload = {
        'order_number': order.order_number,
        'customer_email': order.billing_email,
        'customer_name': f"{order.billing_first_name} {order.billing_last_name}",
        'total': str(order.total),
        'items': [
            {
                'product_id': item.product.id,
                'product_name': item.product_name,
                'quantity': item.quantity,
                'price': str(item.price),
            }
            for item in order.items.all()
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        erp_id = data.get('id') or data.get('order_id')
        if erp_id:
            order.erp_order_id = str(erp_id)
            order.save(update_fields=['erp_order_id'])
        return data
    except Exception as e:
        raise Exception(f"Error sending order to ERP: {e}")


def sync_products_from_api_task():
    """Wrapper para ejecutar como tarea (management command o Celery)."""
    return sync_products_from_api()


# ---------------------------------------------------------------------------
# Sincronización de stock desde TersaSoft → productos locales
# ---------------------------------------------------------------------------

def fetch_tersa_stock(brands=None, extra_ids=None):
    """
    Llama a la API pública de Tersa y devuelve un dict:
      external_id (str) -> existencia (int)

    Filtra las mismas marcas y IDs extra que fetch_tersa_products.
    Se usa 'existencia' del objeto para obtener el stock actual.
    """
    products = fetch_tersa_products(brands=brands, extra_ids=extra_ids)
    stock_map = {}
    for item in products:
        ext_id = str(item.get('id', '')).strip()
        if not ext_id:
            continue
        existencia = item.get('existencia', 0)
        try:
            stock_map[ext_id] = max(0, int(existencia))
        except (TypeError, ValueError):
            stock_map[ext_id] = 0
    return stock_map


def sync_tersa_stock(brands=None, extra_ids=None, dry_run=False):
    """
    Actualiza SOLO stock_quantity en los productos locales cuyo
    external_id coincide con un producto de la API Tersa.

    Parámetros:
      brands    – lista de marcas a filtrar (default: TERSA_BRANDS)
      extra_ids – IDs adicionales a incluir (default: TERSA_EXTRA_PRODUCT_IDS)
      dry_run   – si True, no guarda cambios en BD

    Retorna dict con claves:
      updated      – productos actualizados
      unchanged    – stock ya era igual
      not_found    – external_id no existe en BD local
      total_api    – total de productos recibidos de la API
    """
    from apps.products.models import Product

    stock_map = fetch_tersa_stock(brands=brands, extra_ids=extra_ids)
    total_api = len(stock_map)

    updated = unchanged = not_found = 0
    results = []

    for ext_id, new_stock in stock_map.items():
        product = Product.objects.filter(external_id=ext_id, source='api').first()

        if not product:
            not_found += 1
            results.append({
                'status': 'not_found',
                'external_id': ext_id,
                'stock': new_stock,
            })
            continue

        if product.stock_quantity == new_stock:
            unchanged += 1
            results.append({
                'status': 'unchanged',
                'external_id': ext_id,
                'name': product.name,
                'sku': product.sku,
                'stock': new_stock,
            })
            continue

        old_stock = product.stock_quantity
        if not dry_run:
            product.stock_quantity = new_stock
            product.manage_stock = True
            product.save(update_fields=['stock_quantity', 'manage_stock', 'updated_at'])

        updated += 1
        results.append({
            'status': 'updated',
            'external_id': ext_id,
            'name': product.name,
            'sku': product.sku,
            'old_stock': old_stock,
            'new_stock': new_stock,
        })

    return {
        'updated': updated,
        'unchanged': unchanged,
        'not_found': not_found,
        'total_api': total_api,
        'results': results,
        'dry_run': dry_run,
    }
