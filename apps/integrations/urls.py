from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    path('sync-stock/', views.sync_stock_endpoint, name='sync_stock'),
]
