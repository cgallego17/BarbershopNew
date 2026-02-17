from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('apps.core.urls')),
    path('shop/', include('apps.products.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Compatibilidad con la plantilla Boskery (referencias a /assets/...)
    urlpatterns += [
        path('assets/<path:path>', serve, {'document_root': settings.BASE_DIR / 'boskery' / 'files' / 'assets'}),
    ]
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
