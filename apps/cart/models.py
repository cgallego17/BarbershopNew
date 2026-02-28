"""Modelos del carrito."""
from django.db import models


class AbandonedCartLead(models.Model):
    """
    Lead de carrito abandonado: usuario dejó su email para recibir recordatorio.
    Un cron envía el correo después de X horas si reminder_sent_at es null.
    """
    email = models.EmailField('Email')
    cart_snapshot = models.JSONField(
        'Snapshot del carrito',
        default=list,
        help_text='Lista de items: {product_id, product_name, quantity, price, total}',
    )
    cart_total = models.DecimalField(
        'Total del carrito',
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Lead carrito abandonado'
        verbose_name_plural = 'Leads carrito abandonado'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.created_at.date()}"
