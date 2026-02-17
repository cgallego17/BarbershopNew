from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('contact/', views.contact_view, name='contact'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/', include('apps.core.urls_admin')),
    path('mayoristas/', include('apps.core.urls_wholesale')),
]
