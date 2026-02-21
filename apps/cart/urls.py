from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('agregar/<int:product_id>/', views.cart_add, name='add'),
    path('eliminar/<int:product_id>/', views.cart_remove, name='remove'),
    path('limpiar/', views.cart_clear, name='clear'),
    path('actualizar/', views.cart_update, name='update'),
    path(
        'actualizar-item/<str:item_key>/',
        views.cart_update_item,
        name='update_item'
    ),
    path('sidebar/', views.cart_sidebar_json, name='sidebar_json'),
]
