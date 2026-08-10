from django.urls import path
from . import views

urlpatterns = [
    path('', views.halaman_scan, name='scan'),
]