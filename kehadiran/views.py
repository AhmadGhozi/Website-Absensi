from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Siswa
import qrcode

def halaman_scan(request):
    return render(request, 'kehadiran/scan.html')

def manajemen_siswa(request):
    semua_siswa = Siswa.objects.all()
    context = {'semua_siswa': semua_siswa}
    return render(request, 'kehadiran/manajemen_siswa.html', context)

def tambah_siswa(request):
    if request.method == 'POST':
        nisn = request.POST.get('nisn')
        nama = request.POST.get('nama')
        kelas = request.POST.get('kelas')
        
        Siswa.objects.create(nisn=nisn, nama=nama, kelas=kelas)
        return redirect('manajemen_siswa')
        
    return render(request, 'kehadiran/tambah_siswa.html')

def edit_siswa(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    
    if request.method == 'POST':
        siswa.nisn = request.POST.get('nisn')
        siswa.nama = request.POST.get('nama')
        siswa.kelas = request.POST.get('kelas')
        siswa.save() # Simpan perubahan
        return redirect('manajemen_siswa')
        
    context = {'siswa': siswa}
    return render(request, 'kehadiran/edit_siswa.html', context)

def hapus_siswa(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    siswa.delete()
    return redirect('manajemen_siswa')

def download_qr(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    if siswa.qr_code:
        response = HttpResponse(siswa.qr_code.read(), content_type="image/png")
        response['Content-Disposition'] = f'attachment; filename="QR-{siswa.nisn}-{siswa.nama}.png"'
        return response
    return redirect('manajemen_siswa')