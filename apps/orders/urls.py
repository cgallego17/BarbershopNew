from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
    path('my-orders/', views.order_list, name='list'),
    path('<str:order_number>/', views.order_detail, name='detail'),
]
