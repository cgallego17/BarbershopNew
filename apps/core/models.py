"""Modelos de la aplicación core."""
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

    # Información adicional
    about_text = models.TextField('Texto sobre nosotros', blank=True)
    currency = models.CharField('Moneda', max_length=10, default='$')
    terms_url = models.URLField('URL términos y condiciones', blank=True)
    privacy_url = models.URLField('URL política de privacidad', blank=True)

    # Meta
    meta_description = models.CharField('Meta descripción (SEO)', max_length=300, blank=True)
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
    button_text = models.CharField('Texto del botón', max_length=50, blank=True)
    button_url = models.CharField('URL del botón', max_length=255, blank=True)
    video_url = models.URLField('URL video (YouTube)', blank=True)
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
