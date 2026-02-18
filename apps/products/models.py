"""
Modelos WooCommerce-style para e-commerce.
Soporta: productos simples, variables, stock, API externa, ERP.
"""
from decimal import Decimal

from django.db import models
from django.db.models import Q, Exists, OuterRef
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class Category(models.Model):
    """Categoría de producto (como WooCommerce)."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='children'
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    """Marca de producto para el catálogo."""
    name = models.CharField('Nombre', max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    logo = models.ImageField('Logo', upload_to='brands/', blank=True, null=True)
    description = models.TextField('Descripción', blank=True)
    order = models.PositiveIntegerField('Orden', default=0)
    is_active = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Producto principal - estilo WooCommerce."""
    SOURCE_CHOICES = [
        ('local', 'Local'),
        ('api', 'API Externa'),
        ('erp', 'ERP'),
    ]
    TYPE_CHOICES = [
        ('simple', 'Simple'),
        ('variable', 'Variable'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    codigo = models.CharField('Código', max_length=100, blank=True, db_index=True,
                              help_text='Código del producto (ej. API Tersa)')
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    regular_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    sale_price_start = models.DateTimeField(null=True, blank=True, verbose_name='Inicio oferta')
    sale_price_end = models.DateTimeField(null=True, blank=True, verbose_name='Fin oferta')
    wholesale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Precio mayorista',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    product_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='simple')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='local')
    external_id = models.CharField(
        'ID API', max_length=100, blank=True, db_index=True,
        help_text='ID del producto en la API externa (ej. Tersa)'
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', verbose_name='Marca'
    )
    categories = models.ManyToManyField(Category, blank=True, related_name='products')
    used_attributes = models.ManyToManyField(
        'ProductAttribute', blank=True, related_name='products',
        verbose_name='Atributos (producto variable)'
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    manage_stock = models.BooleanField(default=False)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    @classmethod
    def q_in_stock(cls):
        """Q filter para productos con stock (para listados según configuración)."""
        simple = Q(product_type='simple') & (Q(manage_stock=False) | Q(stock_quantity__gt=0))
        variable = Q(product_type='variable') & Exists(
            ProductVariant.objects.filter(product=OuterRef('pk'), is_active=True, stock_quantity__gt=0)
        )
        return simple | variable

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_price(self, user=None):
        """Precio según tipo de usuario. Mayoristas ven wholesale_price si existe."""
        if user and getattr(user, 'is_wholesale', False):
            if self.product_type == 'variable' and self.variants.exists():
                prices = [v.get_price(user) for v in self.variants.filter(is_active=True)]
                return min(prices) if prices else (self.wholesale_price or self.regular_price)
            if self.wholesale_price is not None:
                return self.wholesale_price
        return self.price

    @property
    def price(self):
        """Precio actual (sale si existe y está en vigencia, sino regular). Para variables: mínimo de variantes."""
        if self.product_type == 'variable' and self.variants.exists():
            prices = [v.price for v in self.variants.filter(is_active=True) if v.price]
            return min(prices) if prices else self.regular_price
        if self.sale_price and self.sale_price < self.regular_price and self._sale_price_active:
            return self.sale_price
        return self.regular_price

    @property
    def _sale_price_active(self):
        """Verifica si la oferta está vigente según fechas."""
        from django.utils import timezone
        now = timezone.now()
        if self.sale_price_start and now < self.sale_price_start:
            return False
        if self.sale_price_end and now > self.sale_price_end:
            return False
        return True

    @property
    def is_on_sale(self):
        """True si el producto está actualmente en oferta."""
        return bool(
            self.sale_price and self.sale_price < self.regular_price and self._sale_price_active
        )

    @property
    def in_stock(self):
        if self.product_type == 'variable' and self.variants.exists():
            return any(v.in_stock for v in self.variants.filter(is_active=True))
        if not self.manage_stock:
            return True
        return self.stock_quantity > 0

    def _approved_reviews(self):
        """Reseñas aprobadas (solo estas cuentan para valoración y SEO)."""
        return self.reviews.filter(is_approved=True)

    @property
    def average_rating(self):
        """Puntuación media (1-5) solo de reseñas aprobadas."""
        result = self._approved_reviews().aggregate(avg=models.Avg('rating'))
        return result['avg'] or 0

    @property
    def review_count(self):
        """Número de reseñas aprobadas."""
        return self._approved_reviews().count()

    def get_rating_stats(self):
        """Devuelve {average, count} de reseñas aprobadas para mostrar y SEO."""
        agg = self._approved_reviews().aggregate(
            avg=models.Avg('rating'),
            count=models.Count('id')
        )
        return {
            'average': round(float(agg['avg'] or 0), 1),
            'count': agg['count'] or 0,
        }

    def get_main_image(self):
        """Devuelve la imagen principal o la primera disponible."""
        images = list(self.images.all())
        for img in images:
            if img.is_primary:
                return img
        return images[0] if images else None


class ProductImage(models.Model):
    """Imágenes del producto."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} - Imagen {self.order}"


class ProductAttribute(models.Model):
    """Atributos para productos variables (talla, color, etc)."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Atributo'
        verbose_name_plural = 'Atributos'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """Valores de un atributo (ej: Talla -> S, M, L)."""
    attribute = models.ForeignKey(
        ProductAttribute, on_delete=models.CASCADE, related_name='values'
    )
    value = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Valor de atributo'
        verbose_name_plural = 'Valores de atributos'
        ordering = ['order', 'value']
        unique_together = [('attribute', 'value')]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    """Variantes de producto (para productos variables)."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants'
    )
    sku = models.CharField(max_length=100, unique=True, blank=True)
    attributes = models.JSONField(default=dict)  # {"talla": "M", "color": "Rojo"}
    regular_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    sale_price_start = models.DateTimeField(null=True, blank=True, verbose_name='Inicio oferta')
    sale_price_end = models.DateTimeField(null=True, blank=True, verbose_name='Fin oferta')
    wholesale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Precio mayorista'
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/variants/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Variante'
        verbose_name_plural = 'Variantes'

    def __str__(self):
        attrs = ', '.join(f"{k}: {v}" for k, v in self.attributes.items())
        return f"{self.product.name} - {attrs or 'Default'}"

    @property
    def price(self):
        if self.sale_price and self.sale_price < self.regular_price and self._sale_price_active:
            return self.sale_price
        return self.regular_price

    def get_price(self, user=None):
        if user and user.is_wholesale and self.wholesale_price is not None:
            return self.wholesale_price
        return self.price

    @property
    def _sale_price_active(self):
        from django.utils import timezone
        now = timezone.now()
        if self.sale_price_start and now < self.sale_price_start:
            return False
        if self.sale_price_end and now > self.sale_price_end:
            return False
        return True

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    def attributes_display(self):
        return ', '.join(f"{k}: {v}" for k, v in self.attributes.items())


class ProductReview(models.Model):
    """Reseñas de productos."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews'
    )
    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    rating = models.PositiveSmallIntegerField()  # 1-5
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-created_at']
