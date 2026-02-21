from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductImage, ProductAttribute,
    ProductVariant, ProductReview, ProductView, ProductFavorite
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'product_type', 'source', 'price_display',
        'stock_quantity', 'view_count', 'is_active', 'is_featured', 'created_at'
    ]
    list_filter = ['is_active', 'is_featured', 'product_type', 'source']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['categories']
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ['created_at', 'updated_at']

    def price_display(self, obj):
        return f"${obj.price}"
    price_display.short_description = 'Precio'

    actions = ['sync_from_api']

    @admin.action(description='Sincronizar desde API')
    def sync_from_api(self, request, queryset):
        from apps.integrations.services import sync_products_from_api
        sync_products_from_api()
        self.message_user(request, 'Sincronización iniciada.')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'author_name', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating']
    search_fields = ['author_name', 'comment']


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'session_key', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'user__email', 'session_key']
    readonly_fields = ['product', 'user', 'session_key', 'created_at']


@admin.register(ProductFavorite)
class ProductFavoriteAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'user__email']
    readonly_fields = ['product', 'user', 'created_at']
