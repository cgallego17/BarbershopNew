from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product', 'variant']
    readonly_fields = ['product_name', 'price', 'total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_status',
        'total', 'created_at'
    ]
    list_filter = ['status', 'payment_status']
    search_fields = ['order_number', 'billing_email', 'billing_first_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
