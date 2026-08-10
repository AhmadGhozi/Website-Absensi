from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Siswa
import qrcode
import json
from datetime import datetime
from .models import Siswa, Absensi

def halaman_scan(request):
    return render(request, 'kehadiran/scan.html')

def proses_scan(request):
    if request.method == 'POST':
        # Mengambil data NISN yang dikirim oleh Javascript
        data = json.loads(request.body)
        nisn_scanned = data.get('nisn')
        
        # 1. Cari apakah NISN tersebut ada di database?
        siswa = Siswa.objects.filter(nisn=nisn_scanned).first()
        if not siswa:
            return JsonResponse({'status': 'error', 'pesan': 'QR Code tidak terdaftar!'})
            
        # 2. Cek apakah anak ini sudah absen hari ini?
        hari_ini = datetime.now().date()
        if Absensi.objects.filter(siswa=siswa, tanggal=hari_ini).exists():
            return JsonResponse({'status': 'warning', 'pesan': f'{siswa.nama} sudah absen hari ini.'})
            
        # 3. Tentukan status (Misal: Lewat dari jam 07:00 dianggap Terlambat)
        sekarang = datetime.now().time()
        batas_waktu = datetime.strptime('07:00:00', '%H:%M:%S').time()
        status_kehadiran = 'Terlambat' if sekarang > batas_waktu else 'Hadir'
        
        # 4. Simpan ke database Absensi
        Absensi.objects.create(siswa=siswa, status=status_kehadiran)
        
        return JsonResponse({'status': 'success', 'pesan': f'Berhasil: {siswa.nama} ({status_kehadiran})'})

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