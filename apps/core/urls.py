from django.urls import path, include

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('contacto/', views.contact_view, name='contact'),
    path('nosotros/', views.about_view, name='about'),
    path('api/geo/estados/', views.geo_states_view, name='geo_states'),
    path('api/geo/ciudades/', views.geo_cities_view, name='geo_cities'),
    path('panel/', views.dashboard_view, name='dashboard'),
    path('panel/', include('apps.core.urls_admin')),
    path('mayoristas/', include('apps.core.urls_wholesale')),
]
