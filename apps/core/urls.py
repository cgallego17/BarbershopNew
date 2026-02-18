from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('contact/', views.contact_view, name='contact'),
    path('api/geo/states/', views.geo_states_view, name='geo_states'),
    path('api/geo/cities/', views.geo_cities_view, name='geo_cities'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/', include('apps.core.urls_admin')),
    path('mayoristas/', include('apps.core.urls_wholesale')),
]
