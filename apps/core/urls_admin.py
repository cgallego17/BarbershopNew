"""URLs del panel de administración."""
from django.urls import path

from . import views_admin

app_name = 'admin_panel'

urlpatterns = [
    # Categorías
    path('categorias/', views_admin.CategoryListView.as_view(), name='category_list'),
    path('categorias/nuevo/', views_admin.CategoryCreateView.as_view(), name='category_create'),
    path('categorias/<int:pk>/productos/', views_admin.CategoryProductListView.as_view(), name='category_products'),
    path('categorias/<int:pk>/activar/', views_admin.category_toggle_active_view, name='category_toggle_active'),
    path('categorias/<int:pk>/editar/', views_admin.CategoryUpdateView.as_view(), name='category_edit'),
    path('categorias/<int:pk>/eliminar/', views_admin.CategoryDeleteView.as_view(), name='category_delete'),
    # Marcas (catálogo)
    path('marcas/', views_admin.BrandListView.as_view(), name='brand_list'),
    path('marcas/nueva/', views_admin.BrandCreateView.as_view(), name='brand_create'),
    path('marcas/<int:pk>/editar/', views_admin.BrandUpdateView.as_view(), name='brand_edit'),
    path('marcas/<int:pk>/eliminar/', views_admin.BrandDeleteView.as_view(), name='brand_delete'),
    # Atributos
    path('atributos/', views_admin.AttributeListView.as_view(), name='attribute_list'),
    path('atributos/nuevo/', views_admin.AttributeCreateView.as_view(), name='attribute_create'),
    path('atributos/<int:pk>/editar/', views_admin.AttributeUpdateView.as_view(), name='attribute_edit'),
    path('atributos/<int:pk>/eliminar/', views_admin.AttributeDeleteView.as_view(), name='attribute_delete'),
    # Productos
    path('productos/', views_admin.ProductListView.as_view(), name='product_list'),
    path('productos/sync-tersa/', views_admin.sync_tersa_products_view, name='product_sync_tersa'),
    path('productos/nuevo/', views_admin.ProductCreateView.as_view(), name='product_create'),
    path('productos/<int:pk>/editar/', views_admin.ProductUpdateView.as_view(), name='product_edit'),
    path('productos/<int:pk>/inactivar/', views_admin.product_toggle_active_view, name='product_toggle_active'),
    path('productos/<int:pk>/eliminar/', views_admin.ProductDeleteView.as_view(), name='product_delete'),
    # Clientes
    path('clientes/', views_admin.CustomerListView.as_view(), name='customer_list'),
    path('clientes/nuevo/', views_admin.CustomerCreateView.as_view(), name='customer_create'),
    path('clientes/<int:pk>/', views_admin.customer_detail_view, name='customer_detail'),
    path('clientes/<int:pk>/editar/', views_admin.CustomerUpdateView.as_view(), name='customer_edit'),
    # Pedidos
    path('pedidos/', views_admin.OrderListView.as_view(), name='order_list'),
    path('pedidos/<int:pk>/', views_admin.order_detail_view, name='order_detail'),
    # Cupones
    path('cupones/', views_admin.CouponListView.as_view(), name='coupon_list'),
    path('cupones/nuevo/', views_admin.CouponCreateView.as_view(), name='coupon_create'),
    path('cupones/<int:pk>/editar/', views_admin.CouponUpdateView.as_view(), name='coupon_edit'),
    path('cupones/<int:pk>/eliminar/', views_admin.CouponDeleteView.as_view(), name='coupon_delete'),
    # Precios de envío por ciudad
    path('envios/', views_admin.ShippingPriceListView.as_view(), name='shipping_price_list'),
    path('envios/cargar-todas-colombia/', views_admin.shipping_price_load_all_colombia_view, name='shipping_price_load_all_colombia'),
    path('envios/exportar-excel/', views_admin.shipping_price_export_excel_view, name='shipping_price_export_excel'),
    path('envios/nuevo/', views_admin.ShippingPriceCreateView.as_view(), name='shipping_price_create'),
    path('envios/<int:pk>/editar/', views_admin.ShippingPriceUpdateView.as_view(), name='shipping_price_edit'),
    path('envios/<int:pk>/eliminar/', views_admin.ShippingPriceDeleteView.as_view(), name='shipping_price_delete'),
    # Configuración
    path('configuracion/', views_admin.SiteSettingsUpdateView.as_view(), name='config'),
    # Secciones del Home
    path('secciones/', views_admin.HomeSectionsConfigView.as_view(), name='home_sections'),
    path('secciones/hero/', views_admin.HomeHeroSlideListView.as_view(), name='home_hero_list'),
    path('secciones/hero/nuevo/', views_admin.HomeHeroSlideCreateView.as_view(), name='home_hero_create'),
    path('secciones/hero/<int:pk>/editar/', views_admin.HomeHeroSlideUpdateView.as_view(), name='home_hero_edit'),
    path('secciones/hero/<int:pk>/eliminar/', views_admin.HomeHeroSlideDeleteView.as_view(), name='home_hero_delete'),
    path('secciones/about/', views_admin.HomeAboutBlockUpdateView.as_view(), name='home_about'),
    path('secciones/categorias/', views_admin.HomeMeatCategoryBlockUpdateView.as_view(), name='home_meat_category'),
    path('secciones/marcas/', views_admin.HomeBrandListView.as_view(), name='home_brand_list'),
    path('secciones/marcas/nuevo/', views_admin.HomeBrandCreateView.as_view(), name='home_brand_create'),
    path('secciones/marcas/<int:pk>/editar/', views_admin.HomeBrandUpdateView.as_view(), name='home_brand_edit'),
    path('secciones/marcas/<int:pk>/eliminar/', views_admin.HomeBrandDeleteView.as_view(), name='home_brand_delete'),
    path('secciones/testimonios/', views_admin.HomeTestimonialListView.as_view(), name='home_testimonial_list'),
    path('secciones/testimonios/nuevo/', views_admin.HomeTestimonialCreateView.as_view(), name='home_testimonial_create'),
    path('secciones/testimonios/<int:pk>/editar/', views_admin.HomeTestimonialUpdateView.as_view(), name='home_testimonial_edit'),
    path('secciones/testimonios/<int:pk>/eliminar/', views_admin.HomeTestimonialDeleteView.as_view(), name='home_testimonial_delete'),
]
