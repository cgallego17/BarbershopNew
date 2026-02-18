from django.contrib import admin
from .models import WompiTransaction


@admin.register(WompiTransaction)
class WompiTransactionAdmin(admin.ModelAdmin):
    list_display  = ['wompi_id', 'reference', 'order', 'status', 'amount_display', 'currency', 'payment_method_type', 'created_at']
    list_filter   = ['status', 'currency', 'payment_method_type']
    search_fields = ['wompi_id', 'reference', 'order__order_number']
    readonly_fields = [
        'wompi_id', 'reference', 'order', 'status', 'amount_in_cents',
        'currency', 'payment_method_type', 'raw_data', 'created_at', 'updated_at',
    ]
    ordering = ['-created_at']

    def amount_display(self, obj):
        return f"${obj.amount_display:,.0f} {obj.currency}"
    amount_display.short_description = 'Monto'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
