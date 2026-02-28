"""
Modelos de pedidos - estilo WooCommerce.
"""
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Order(models.Model):
    """Pedido principal."""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('on_hold', 'En espera'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending'
    )
    # Billing
    billing_customer_type = models.CharField(
        'Tipo', max_length=20,
        choices=[('person', 'Persona natural'), ('company', 'Empresa')],
        default='person'
    )
    billing_document_type = models.CharField(
        'Tipo de documento', max_length=10, blank=True,
        choices=[
            ('', '--'),
            ('CC', 'Cédula de ciudadanía'),
            ('CE', 'Cédula de extranjería'),
            ('PA', 'Pasaporte'),
            ('NIT', 'NIT'),
        ]
    )
    billing_document_number = models.CharField(
        'Número de identificación', max_length=30, blank=True
    )
    billing_date_of_birth = models.DateField(
        'Fecha de nacimiento', null=True, blank=True
    )
    billing_first_name = models.CharField(max_length=100)
    billing_last_name = models.CharField(max_length=100, blank=True)
    billing_email = models.EmailField()
    billing_phone = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField('Departamento / Estado', max_length=100, blank=True)
    billing_country = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    # Coupon
    coupon_code = models.CharField(max_length=50, blank=True)
    # ERP sync
    erp_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    payment_reminder_sent_at = models.DateTimeField(
        'Recordatorio de pago enviado',
        null=True,
        blank=True,
        help_text='Si está definido, ya se envió el correo de recordatorio para completar el pago.',
    )
    completed_at = models.DateTimeField(
        'Completado/entregado',
        null=True,
        blank=True,
        help_text='Fecha en que el pedido pasó a estado completado (para reseñas y recordatorios).',
    )
    review_request_sent_at = models.DateTimeField(
        'Solicitud de reseña enviada',
        null=True,
        blank=True,
    )
    repurchase_reminder_sent_at = models.DateTimeField(
        'Recordatorio de recompra enviado',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Orden {self.order_number}"

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Línea de pedido."""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.PROTECT
    )
    variant = models.ForeignKey(
        'products.ProductVariant', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Línea de pedido'
        verbose_name_plural = 'Líneas de pedido'

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class OrderNote(models.Model):
    """Nota asociada a un pedido: interna (solo panel) o al cliente (se guarda y se envía por email)."""
    NOTE_TYPE_INTERNAL = 'internal'
    NOTE_TYPE_CLIENT = 'client'
    NOTE_TYPE_CHOICES = [
        (NOTE_TYPE_INTERNAL, 'Nota interna'),
        (NOTE_TYPE_CLIENT, 'Nota al cliente'),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='order_notes'
    )
    note_type = models.CharField(
        max_length=20, choices=NOTE_TYPE_CHOICES, default=NOTE_TYPE_INTERNAL
    )
    content = models.TextField('Contenido')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='order_notes_created'
    )

    class Meta:
        verbose_name = 'Nota de pedido'
        verbose_name_plural = 'Notas de pedido'
        ordering = ['-created_at']

    def __str__(self):
        return f"Nota {self.get_note_type_display()} - {self.order.order_number}"
