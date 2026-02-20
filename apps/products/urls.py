from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('categoria/<slug:category_slug>/', views.ProductListView.as_view(), name='category'),
    path('producto/<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
]
