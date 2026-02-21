from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserAddress


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            'Tipo e identificación',
            {
                'fields': (
                    'customer_type',
                    'document_type',
                    'document_number',
                    'date_of_birth',
                )
            },
        ),
        (
            'Información adicional',
            {
                'fields': (
                    'phone',
                    'address',
                    'city',
                    'state',
                    'country',
                    'postal_code',
                )
            },
        ),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = (
        'alias',
        'user',
        'city',
        'state',
        'country',
        'is_default',
        'updated_at',
    )
    list_filter = ('is_default', 'country', 'state')
    search_fields = (
        'alias',
        'user__email',
        'user__first_name',
        'city',
        'address',
    )
    autocomplete_fields = ('user',)
