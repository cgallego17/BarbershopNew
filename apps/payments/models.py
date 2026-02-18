"""
Modelo de transacciones Wompi.
Cada intento de pago queda registrado aquí con su estado y datos crudos.
"""
from django.db import models


class WompiTransaction(models.Model):
    """Transacción registrada en Wompi (un pedido puede tener varios intentos)."""

    STATUS_CHOICES = [
        ('PENDING',  'Pendiente'),
        ('APPROVED', 'Aprobado'),
        ('DECLINED', 'Declinado'),
        ('VOIDED',   'Anulado'),
        ('ERROR',    'Error'),
    ]

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='wompi_transactions',
        verbose_name='Pedido',
    )
    wompi_id = models.CharField(
        'ID Wompi', max_length=100, unique=True, db_index=True
    )
    reference = models.CharField(
        'Referencia', max_length=100, db_index=True,
        help_text='Número de pedido enviado como referencia a Wompi'
    )
    status = models.CharField(
        'Estado', max_length=20, choices=STATUS_CHOICES, default='PENDING'
    )
    amount_in_cents = models.BigIntegerField('Monto (centavos)', default=0)
    currency = models.CharField('Moneda', max_length=10, default='COP')
    payment_method_type = models.CharField(
        'Método de pago', max_length=50, blank=True
    )
    raw_data = models.JSONField('Datos crudos Wompi', default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transacción Wompi'
        verbose_name_plural = 'Transacciones Wompi'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} — {self.status} ({self.wompi_id})"

    @property
    def amount_display(self):
        """Monto formateado (divide por 100 para COP)."""
        return self.amount_in_cents / 100
