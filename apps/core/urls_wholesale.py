"""URLs del panel de mayoristas."""
from django.urls import path

from . import views_wholesale

app_name = 'wholesale'

urlpatterns = [
    path('', views_wholesale.wholesale_panel, name='panel'),
]
