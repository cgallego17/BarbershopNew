from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'site_name',
        'email',
        'phone',
        'city',
        'country',
        'updated_at',
    )
    fieldsets = (
        (
            'Información general',
            {
                'fields': (
                    'site_name',
                    'tagline',
                    'logo',
                )
            },
        ),
        (
            'Contacto',
            {
                'fields': (
                    'email',
                    'phone',
                    'whatsapp',
                )
            },
        ),
        (
            'Dirección',
            {
                'fields': (
                    'address',
                    'city',
                    'state',
                    'country',
                    'postal_code',
                    'business_hours',
                )
            },
        ),
        (
            'Redes sociales',
            {
                'fields': (
                    'facebook_url',
                    'instagram_url',
                    'twitter_url',
                    'youtube_url',
                    'tiktok_url',
                )
            },
        ),
        (
            'Tienda',
            {
                'fields': (
                    'show_out_of_stock_products',
                    'currency',
                    'free_shipping_min_amount',
                )
            },
        ),
        (
            'SEO y enlaces',
            {
                'fields': (
                    'meta_description',
                    'terms_url',
                    'privacy_url',
                    'topbar_marquee_text',
                    'about_text',
                )
            },
        ),
    )

    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)
