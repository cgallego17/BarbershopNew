from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<str:order_number>/',  views.payment_page,        name='payment_page'),
    path('return/',                  views.payment_return,       name='payment_return'),
    path('wompi/webhook/',           views.wompi_webhook,        name='wompi_webhook'),
    path('status/<str:order_number>/', views.payment_status_api, name='payment_status'),
]
