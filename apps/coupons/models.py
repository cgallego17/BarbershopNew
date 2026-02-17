from decimal import Decimal

from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    """Cupones de descuento - estilo WooCommerce."""
    DISCOUNT_TYPES = [
        ('percent', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    maximum_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'

    def __str__(self):
        return self.code

    def get_discount(self, amount):
        """Calcula el descuento aplicable."""
        if not self.is_active:
            return Decimal('0.00')
        now = timezone.now()
        if self.date_start and now < self.date_start:
            return Decimal('0.00')
        if self.date_end and now > self.date_end:
            return Decimal('0.00')
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return Decimal('0.00')
        if self.minimum_amount and amount < self.minimum_amount:
            return Decimal('0.00')
        if self.discount_type == 'percent':
            discount = amount * (self.discount_value / 100)
        else:
            discount = min(self.discount_value, amount)
        if self.maximum_amount:
            discount = min(discount, self.maximum_amount)
        return discount

    def apply(self, amount):
        """Aplica el cupón y aumenta usage_count."""
        discount = self.get_discount(amount)
        if discount > 0:
            self.usage_count += 1
            self.save(update_fields=['usage_count', 'updated_at'])
        return discount
