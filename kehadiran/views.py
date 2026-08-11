from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Siswa
import qrcode
import json
import requests
from datetime import datetime, date
from .models import Siswa, Absensi
from django.utils import timezone
from datetime import time
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import logging

def halaman_scan(request):
    return render(request, 'kehadiran/scan.html')

logger = logging.getLogger(__name__)


def kirim_wa_ortu(nomor_tujuan, nama_siswa, jenis_absen, status_kehadiran, waktu):
    api_url = f"{settings.WABLAS_BASE_URL.rstrip('/')}/api/send-message"

    if jenis_absen == 'masuk':
        pesan = (
            f"Halo Bapak/Ibu, pemberitahuan bahwa anak Anda atas nama "
            f"*{nama_siswa}* telah melakukan absensi *MASUK* di sekolah dengan status: "
            f"*{status_kehadiran}* pada pukul {waktu}."
        )
    else:  # pulang
        pesan = (
            f"Halo Bapak/Ibu, pemberitahuan bahwa anak Anda atas nama "
            f"*{nama_siswa}* telah melakukan absensi *PULANG* dari sekolah "
            f"pada pukul {waktu}."
        )

    payload = {"phone": nomor_tujuan, "message": pesan}
    headers = {"Authorization": settings.WABLAS_TOKEN}

    try:
        response = requests.post(api_url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        try:
            hasil_json = response.json()
            logger.info("Berhasil terkirim via Wablas: %s", hasil_json)
            return hasil_json
        except ValueError:
            logger.error("Balasan Wablas bukan JSON (Status %s): %s", response.status_code, response.text)
            return None
    except requests.exceptions.Timeout:
        logger.error("Request ke Wablas timeout.")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error("Wablas HTTP error: %s | Response: %s", e, response.text)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Koneksi ke Wablas gagal: %s", e)
        return None

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
        format_waktu = waktu_sekarang.strftime('%H:%M:%S')

        absensi_hari_ini = Absensi.objects.filter(siswa=siswa, tanggal=hari_ini).first()

        # ==== KASUS 1: belum absen sama sekali hari ini -> ABSEN MASUK ====
        if not absensi_hari_ini:
            batas_masuk = settings.BATAS_JAM_MASUK
            status_kehadiran = 'Terlambat' if jam_ini > batas_masuk else 'Hadir'

            Absensi.objects.create(
                siswa=siswa,
                status=status_kehadiran,
                tanggal=hari_ini,
                jam_masuk=jam_ini,
            )

            if siswa.no_hp_ortu:
                kirim_wa_ortu(
                    nomor_tujuan=siswa.no_hp_ortu,
                    nama_siswa=siswa.nama,
                    jenis_absen='masuk',
                    status_kehadiran=status_kehadiran,
                    waktu=format_waktu,
                )

            return JsonResponse({
                'status': 'success',
                'nama': siswa.nama,
                'jenis': 'masuk',
                'status_kehadiran': status_kehadiran,
                'waktu': format_waktu,
            })

        # ==== KASUS 2: sudah absen masuk, belum absen pulang -> ABSEN PULANG ====
        elif absensi_hari_ini.jam_masuk and not absensi_hari_ini.jam_pulang:
            
            # Validasi: cek apakah sudah lewat batas jam pulang
            if jam_ini < settings.BATAS_JAM_PULANG:
                return JsonResponse({
                    'status': 'warning',
                    'pesan': (
                        f'Belum waktunya pulang. Absen pulang baru bisa dilakukan '
                        f'mulai pukul {settings.BATAS_JAM_PULANG.strftime("%H:%M")}.'
                    ),
                })

            absensi_hari_ini.jam_pulang = jam_ini
            absensi_hari_ini.save()

            if siswa.no_hp_ortu:
                kirim_wa_ortu(
                    nomor_tujuan=siswa.no_hp_ortu,
                    nama_siswa=siswa.nama,
                    jenis_absen='pulang',
                    status_kehadiran=None,
                    waktu=format_waktu,
                )

            return JsonResponse({
                'status': 'success',
                'nama': siswa.nama,
                'jenis': 'pulang',
                'waktu': format_waktu,
            })

        # ==== KASUS 3: sudah absen masuk DAN pulang -> tolak ====
        else:
            return JsonResponse({
                'status': 'warning',
                'pesan': f'{siswa.nama} sudah absen masuk dan pulang hari ini.',
            })

    return redirect('scan')

@login_required
def manajemen_siswa(request):
    semua_siswa = Siswa.objects.all()
    context = {'semua_siswa': semua_siswa}
    return render(request, 'kehadiran/manajemen_siswa.html', context)

def tambah_siswa(request):
    if request.method == 'POST':
        nisn = request.POST.get('nisn')
        nama = request.POST.get('nama')
        kelas = request.POST.get('kelas')
        no_hp_ortu = request.POST.get('no_hp_ortu')
        
        Siswa.objects.create(nisn=nisn, nama=nama, kelas=kelas, no_hp_ortu=no_hp_ortu)
        return redirect('manajemen_siswa')
        
    return render(request, 'kehadiran/tambah_siswa.html')

def edit_siswa(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    
    if request.method == 'POST':
        siswa.nisn = request.POST.get('nisn')
        siswa.nama = request.POST.get('nama')
        siswa.kelas = request.POST.get('kelas')

        siswa.no_hp_ortu = request.POST.get('no_hp_ortu')
        
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

@login_required
def cetak_laporan(request):
    tanggal_str = request.GET.get('tanggal', str(date.today()))
    tanggal_obj = datetime.strptime(tanggal_str, '%Y-%m-%d').date()

    kelas_terpilih = request.GET.get('kelas', 'semua')

    if kelas_terpilih and kelas_terpilih != 'semua':
        daftar_kelas = [kelas_terpilih]
    else:
        daftar_kelas = Siswa.objects.values_list('kelas', flat=True).distinct().order_by('kelas')

    laporan_per_kelas = []

    for kelas in daftar_kelas:
        siswa_kelas = Siswa.objects.filter(kelas=kelas).order_by('nama')
        data_siswa = []

        for s in siswa_kelas:
            absen = Absensi.objects.filter(siswa=s, tanggal=tanggal_obj).first()
            if absen:
                status = absen.status
                jam_masuk = absen.jam_masuk.strftime('%H:%M:%S') if absen.jam_masuk else '-'
                jam_pulang = absen.jam_pulang.strftime('%H:%M:%S') if absen.jam_pulang else '-'
            else:
                status = 'Alpha'
                jam_masuk = '-'
                jam_pulang = '-'

            data_siswa.append({
                'nama': s.nama,
                'nisn': s.nisn,
                'status': status,
                'jam_masuk': jam_masuk,
                'jam_pulang': jam_pulang,
            })

        laporan_per_kelas.append({
            'kelas': kelas,
            'data_siswa': data_siswa
        })

    context = {
        'tanggal': tanggal_obj,
        'laporan_per_kelas': laporan_per_kelas,
        'kelas_terpilih': kelas_terpilih
    }
    return render(request, 'kehadiran/cetak_laporan.html', context)

def halaman_login(request):
    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')
        
        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username atau password salah!')
            
    return render(request, 'kehadiran/login.html')

def proses_logout(request):
    logout(request)
    return redirect('/login/')