"""Modelos de la aplicación core."""
import re
from django.db import models


# Claves de secciones del home (coinciden con el template Boskery)
SECTION_KEYS = [
    ('hero', 'Hero / Slider'),
    ('about', 'Sobre nosotros'),
    ('brands', 'Marcas / Clientes'),
    ('products', 'Productos destacados'),
    ('meat_category', 'Categorías'),
    ('pricing', 'Precios'),
    ('delivery', 'Entrega'),
    ('why_choose', 'Por qué elegirnos'),
    ('testimonials', 'Testimonios'),
    ('why_choose_three', 'Por qué elegirnos 2'),
    ('blog', 'Blog / Noticias'),
]


class SiteSettings(models.Model):
    """Configuración general de la aplicación (singleton)."""

    # Información general
    site_name = models.CharField('Nombre de la tienda', max_length=200, default='The BARBERSHOP')
    tagline = models.CharField('Slogan o descripción breve', max_length=300, blank=True)
    logo = models.ImageField('Logo', upload_to='settings/', blank=True, null=True)

    # Contacto
    email = models.EmailField('Email de contacto', blank=True)
    phone = models.CharField('Teléfono', max_length=30, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=30, blank=True)

    # Dirección
    address = models.CharField('Dirección', max_length=255, blank=True)
    city = models.CharField('Ciudad', max_length=100, blank=True)
    state = models.CharField('Departamento / Estado', max_length=100, blank=True)
    country = models.CharField('País', max_length=100, blank=True)
    postal_code = models.CharField('Código postal', max_length=20, blank=True)

    # Horarios
    business_hours = models.CharField('Horario de atención', max_length=200, blank=True,
        help_text='Ej: Lun a Dom 9:00am a 6:00pm')

    # Redes sociales
    facebook_url = models.URLField('Facebook', blank=True)
    instagram_url = models.URLField('Instagram', blank=True)
    twitter_url = models.URLField('Twitter/X', blank=True)
    youtube_url = models.URLField('YouTube', blank=True)
    tiktok_url = models.URLField('TikTok', blank=True)

    # Tienda
    show_out_of_stock_products = models.BooleanField(
        'Mostrar productos sin stock',
        default=True,
        help_text='Si está desactivado, los productos sin stock no se mostrarán en la tienda ni en el home.'
    )

    # Información adicional
    about_text = models.TextField('Texto sobre nosotros', blank=True)
    currency = models.CharField('Moneda', max_length=10, default='$')
    terms_url = models.URLField('URL términos y condiciones', blank=True)
    privacy_url = models.URLField('URL política de privacidad', blank=True)

    # Meta
    meta_description = models.CharField('Meta descripción (SEO)', max_length=300, blank=True)
    # Barra superior (marquee)
    topbar_marquee_text = models.TextField(
        'Texto barra superior (marquee)',
        blank=True,
        default='Por compras superiores a $120.000 el envío es gratis',
        help_text='Texto que se muestra en la barra superior en movimiento. Si está vacío, la barra no se muestra.'
    )
    free_shipping_min_amount = models.DecimalField(
        'Envío gratis desde',
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Si el subtotal del pedido es mayor o igual a este valor, el envío será gratis.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del sitio'
        verbose_name_plural = 'Configuración del sitio'

    def __str__(self):
        return self.site_name or 'Configuración'

    @classmethod
    def get(cls):
        """Retorna la instancia única de configuración."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'site_name': 'The BARBERSHOP'})
        return obj

    def get_whatsapp_wa_me_url(self):
        """Número solo dígitos para enlace wa.me. Si tiene 10 dígitos se asume Colombia (+57)."""
        raw = (self.whatsapp or '').strip()
        if not raw:
            return ''
        digits = re.sub(r'\D', '', raw)
        if len(digits) == 10 and digits[0] in '3':
            return f'https://wa.me/57{digits}'
        if len(digits) >= 10:
            return f'https://wa.me/{digits}'
        return ''


# --- Módulo de secciones del Home ---

class HomeSection(models.Model):
    """Configuración de visibilidad y orden de secciones del home."""
    section_key = models.CharField('Clave', max_length=50, choices=SECTION_KEYS, unique=True)
    order = models.PositiveIntegerField('Orden', default=0)
    is_active = models.BooleanField('Activa', default=True)

    class Meta:
        verbose_name = 'Sección del home'
        verbose_name_plural = 'Secciones del home'
        ordering = ['order', 'id']

    def __str__(self):
        return dict(SECTION_KEYS).get(self.section_key, self.section_key)

    @classmethod
    def get_active_sections(cls):
        """Retorna las claves de secciones activas ordenadas."""
        return list(cls.objects.filter(is_active=True).order_by('order').values_list('section_key', flat=True))


class HomeHeroSlide(models.Model):
    """Slide del carrusel hero del home."""
    title = models.CharField('Título principal', max_length=200)
    subtitle = models.CharField('Subtítulo', max_length=150, blank=True)
    text = models.TextField('Descripción', blank=True)
    image = models.ImageField('Imagen', upload_to='home/hero/', blank=True, null=True)
    shape_image = models.ImageField('Imagen decorativa (shape)', upload_to='home/hero/shapes/', blank=True, null=True,
        help_text='Forma decorativa sobre la imagen. Si está vacío se usa la imagen por defecto.')
    button_text = models.CharField('Texto del botón', max_length=50, blank=True)
    button_url = models.CharField('URL del botón', max_length=255, blank=True)
    video_url = models.URLField('URL video (YouTube)', blank=True,
        help_text='Ej: https://www.youtube.com/watch?v=xxxxx. Si lo completas, se mostrará el botón de play sobre la imagen del slide.')
    order = models.PositiveIntegerField('Orden', default=0)

    class Meta:
        verbose_name = 'Slide hero'
        verbose_name_plural = 'Slides hero'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title[:50]


class HomeAboutBlock(models.Model):
    """Bloque de contenido de la sección Sobre nosotros."""
    title = models.CharField('Título', max_length=200)
    subtitle = models.CharField('Subtítulo / Tagline', max_length=200, blank=True)
    content = models.TextField('Contenido')
    image1 = models.ImageField('Imagen principal', upload_to='home/about/', blank=True, null=True)
    image2 = models.ImageField('Imagen secundaria', upload_to='home/about/', blank=True, null=True)
    experience_years = models.CharField('Años de experiencia', max_length=20, blank=True)
    button_text = models.CharField('Texto del botón', max_length=50, blank=True)
    button_url = models.CharField('URL del botón', max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bloque sobre nosotros'
        verbose_name_plural = 'Bloque sobre nosotros'

    def __str__(self):
        return self.title

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'title': 'Sobre nosotros', 'content': ''})
        return obj


class HomeMeatCategoryBlock(models.Model):
    """Contenido editable de la sección Categorías (meat-category) del home."""
    tagline = models.CharField('Subtítulo / Tagline', max_length=150, blank=True, default='primera opción')
    title = models.CharField('Título', max_length=300, blank=True, default='Las mejores categorías en nuestra tienda')
    top_image = models.ImageField('Imagen superior', upload_to='home/meat_category/', blank=True, null=True)
    background_image = models.ImageField('Imagen de fondo', upload_to='home/meat_category/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sección categorías (meat-category)'
        verbose_name_plural = 'Sección categorías (meat-category)'

    def __str__(self):
        return self.title or 'Categorías'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'tagline': 'primera opción', 'title': 'Las mejores categorías en nuestra tienda'})
        return obj


class HomeBrandBlock(models.Model):
    """Configuración de la sección Marcas del home (imagen de fondo, etc.)."""
    background_image = models.ImageField(
        'Imagen de fondo',
        upload_to='home/brands/',
        blank=True,
        null=True,
        help_text='Imagen de fondo de la sección de marcas. Si está vacío se usa la imagen por defecto.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sección marcas (config)'
        verbose_name_plural = 'Sección marcas (config)'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HomeBrand(models.Model):
    """Logo de marca/cliente para el carrusel."""
    name = models.CharField('Nombre', max_length=100, blank=True)
    logo = models.ImageField('Logo', upload_to='home/brands/')
    url = models.URLField('URL', blank=True)
    order = models.PositiveIntegerField('Orden', default=0)

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name or f'Marca #{self.id}'


class HomeTestimonial(models.Model):
    """Testimonio para la sección de reseñas."""
    name = models.CharField('Nombre', max_length=100)
    designation = models.CharField('Cargo / rol', max_length=100, blank=True)
    text = models.TextField('Testimonio')
    image = models.ImageField('Foto', upload_to='home/testimonials/', blank=True, null=True)
    order = models.PositiveIntegerField('Orden', default=0)

    class Meta:
        verbose_name = 'Testimonio'
        verbose_name_plural = 'Testimonios'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


# --- Países, estados/departamentos y ciudades ---

class Country(models.Model):
    """País para direcciones y envíos."""
    name = models.CharField('Nombre', max_length=100)
    iso2 = models.CharField('Código ISO 2', max_length=2, blank=True)
    iso3 = models.CharField('Código ISO 3', max_length=3, blank=True)
    phonecode = models.CharField('Código tel.', max_length=10, blank=True)

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['name']

    def __str__(self):
        return self.name


class State(models.Model):
    """Estado, departamento o región de un país."""
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    name = models.CharField('Nombre', max_length=100)
    iso2 = models.CharField('Código', max_length=10, blank=True)

    class Meta:
        verbose_name = 'Estado / Departamento'
        verbose_name_plural = 'Estados / Departamentos'
        ordering = ['name']
        unique_together = [['country', 'name']]

    def __str__(self):
        return f"{self.name} ({self.country.name})"


class City(models.Model):
    """Ciudad de un estado/departamento."""
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField('Nombre', max_length=100)

    class Meta:
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        ordering = ['name']
        unique_together = [['state', 'name']]

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class ShippingPrice(models.Model):
    """Precio de envío y días de entrega por ciudad."""
    city = models.OneToOneField(
        City, on_delete=models.CASCADE, related_name='shipping_price',
        verbose_name='Ciudad', unique=True
    )
    price = models.DecimalField(
        'Precio de envío', max_digits=12, decimal_places=2,
        default=0
    )
    delivery_days_min = models.PositiveIntegerField(
        'Días de entrega (mínimo)', default=1,
        help_text='Mínimo de días hábiles para la entrega'
    )
    delivery_days_max = models.PositiveIntegerField(
        'Días de entrega (máximo)', default=3,
        help_text='Máximo de días hábiles para la entrega'
    )
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Precio de envío por ciudad'
        verbose_name_plural = 'Precios de envío por ciudad'
        ordering = ['city__state__name', 'city__name']

    def __str__(self):
        if self.delivery_days_min == self.delivery_days_max:
            return f"{self.city} — ${self.price} ({self.delivery_days_min} días)"
        return f"{self.city} — ${self.price} ({self.delivery_days_min} a {self.delivery_days_max} días)"


class NewsletterSubscriber(models.Model):
    """Suscriptor del newsletter desde el formulario del sitio."""

    email = models.EmailField('Email', unique=True)
    is_active = models.BooleanField('Activo', default=True)
    source = models.CharField('Origen', max_length=80, default='footer')
    created_at = models.DateTimeField('Suscrito en', auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Suscriptor newsletter'
        verbose_name_plural = 'Suscriptores newsletter'
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class SecurityEvent(models.Model):
    """Eventos de seguridad detectados en formularios públicos."""

    EVENT_CHOICES = [
        ('honeypot_trigger', 'Honeypot activado'),
        ('rate_limit_block', 'Bloqueo por rate limit'),
        ('auth_honeypot', 'Honeypot en autenticación'),
    ]
    event_type = models.CharField(
        'Tipo de evento',
        max_length=40,
        choices=EVENT_CHOICES,
    )
    source = models.CharField('Origen', max_length=80)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    path = models.CharField('Ruta', max_length=255, blank=True)
    user_agent = models.CharField('User agent', max_length=255, blank=True)
    details = models.JSONField('Detalles', default=dict, blank=True)
    created_at = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Evento de seguridad'
        verbose_name_plural = 'Eventos de seguridad'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['source', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_event_type_display()} ({self.source})'
