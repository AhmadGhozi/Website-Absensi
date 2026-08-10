from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.halaman_login, name='login'),
    path('logout/', views.proses_logout, name='logout'),
    path('scan/', views.halaman_scan, name='scan'),
    path('scan/proses/', views.proses_scan, name='proses_scan'),
    path('siswa/', views.manajemen_siswa, name='manajemen_siswa'),
    path('siswa/tambah/', views.tambah_siswa, name='tambah_siswa'),
    path('siswa/edit/<int:pk>/', views.edit_siswa, name='edit_siswa'),
    path('siswa/hapus/<int:pk>/', views.hapus_siswa, name='hapus_siswa'),
    path('siswa/download-qr/<int:pk>/', views.download_qr, name='download_qr'),
    path('laporan/cetak/', views.cetak_laporan, name='cetak_laporan'),
]