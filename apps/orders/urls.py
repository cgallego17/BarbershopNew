from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('finalizar-compra/', views.checkout_view, name='checkout'),
    path('validar-cupon/', views.validate_coupon, name='validate_coupon'),
    path('consultar/', views.order_lookup, name='lookup'),
    path('mis-pedidos/', views.order_list, name='list'),
    path('pedido/<str:order_number>/', views.order_detail, name='detail'),
]
