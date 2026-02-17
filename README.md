# Boskery E-commerce - Django

E-commerce completo estilo WooCommerce desarrollado con Django 5, usando la plantilla Boskery.

## Características (estilo WooCommerce)

- **Productos**: simples, variables, categorías, SKU, stock
- **Carrito**: sesión, actualización de cantidades
- **Checkout**: facturación, cupones
- **Pedidos**: historial, estados
- **Usuarios**: registro, login (django-allauth)
- **API Externa**: sincronización de productos desde API
- **Admin**: gestión completa de productos, pedidos, cupones
- **ERP**: envío de pedidos a tu ERP Django
- **Seguridad**: CSRF, validadores de contraseña, headers de seguridad

## Requisitos

- Python 3.10+
- Django 5.2

## Instalación

```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Copiar variables de entorno
copy .env.example .env
# Editar .env con tus valores

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos de prueba (opcional)
python manage.py shell
>>> from apps.products.models import Product, Category
>>> c = Category.objects.create(name="Carnes", slug="carnes")
>>> Product.objects.create(name="Carne Molida", slug="carne-molida", sku="CM001", regular_price=15000, categories=[c])
```

## Configuración API de Productos

En `.env`:
```
PRODUCTS_API_URL=https://tu-api.com/products
PRODUCTS_API_KEY=tu-api-key  # opcional
```

La API debe devolver JSON con estructura compatible (id, name, price, sku, description, etc.).

Sincronización manual:
```bash
python manage.py sync_products
```

Desde el admin: Productos → Acción "Sincronizar desde API".

## Conexión ERP

En `.env`:
```
ERP_API_URL=https://tu-erp-django.com/api/orders
ERP_API_KEY=tu-api-key  # opcional
```

Al crear un pedido, se envía automáticamente al ERP si está configurado. El ERP debe exponer un endpoint POST que reciba:
- order_number, customer_email, customer_name, total
- items: [{product_id, product_name, quantity, price}]

## Ejecutar

```bash
python manage.py runserver
```

- Sitio: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin

## Estructura del proyecto

```
BarbershopNew/
├── config/           # Configuración Django
├── apps/
│   ├── core/         # Home, contacto
│   ├── accounts/     # Usuarios
│   ├── products/     # Productos, categorías
│   ├── cart/         # Carrito
│   ├── orders/       # Pedidos
│   ├── coupons/      # Cupones
│   └── integrations/ # API productos, ERP
├── templates/        # Plantillas Boskery
├── boskery/          # Plantilla HTML original
└── static/
```

## Plantilla Boskery

Los assets estáticos están en `boskery/files/assets/`. Las plantillas Django usan `{% static 'assets/...' %}` para referenciarlos.
