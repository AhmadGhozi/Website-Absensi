from django.shortcuts import render
from kehadiran.models import Siswa

def dashboard(request):
    daftar_kelas = Siswa.objects.values_list('kelas', flat=True).distinct().order_by('kelas')
    context = {
        'daftar_kelas': daftar_kelas, 
    }
    return render(request, 'dashboard.html', context)