from django.contrib import admin
from django.urls import path, include
from kehadiran import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.halaman_login, name='home'),
    path('', include('dashboard.urls')),
    path('', include('kehadiran.urls')),
    path('', include('kehadiran.urls')),
    path('siswa/tambah/', include('kehadiran.urls')),
    path('siswa/hapus/<int:pk>/', include('kehadiran.urls')),
    path('siswa/download-qr/<int:pk>/', include('kehadiran.urls')),
]