from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Siswa
import qrcode
import json
from datetime import datetime
from .models import Siswa, Absensi
from django.utils import timezone
from datetime import time

def halaman_scan(request):
    return render(request, 'kehadiran/scan.html')

def proses_scan(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nisn_scanned = data.get('nisn')
        
        siswa = Siswa.objects.filter(nisn=nisn_scanned).first()
        if not siswa:
            return JsonResponse({'status': 'error', 'pesan': 'QR Code tidak terdaftar!'})
            
        waktu_sekarang = datetime.now()
        hari_ini = waktu_sekarang.date()
        jam_ini = waktu_sekarang.time()
        
        if Absensi.objects.filter(siswa=siswa, tanggal=hari_ini).exists():
            return JsonResponse({
                'status': 'warning', 
                'pesan': f'{siswa.nama} sudah absen hari ini.'
            })
            
        batas_waktu = time(7, 0, 0)
        status_kehadiran = 'Terlambat' if jam_ini > batas_waktu else 'Hadir'
        
        Absensi.objects.create(siswa=siswa, status=status_kehadiran)
        
        return JsonResponse({
            'status': 'success',
            'nama': siswa.nama,
            'status_kehadiran': status_kehadiran,
            'waktu': waktu_sekarang.strftime('%H:%M:%S')
        })
    
    # TAMBAHAN INI: Jika diakses lewat GET, kembalikan ke halaman scan agar tidak error
    return redirect('scan')

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
        siswa.save()
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