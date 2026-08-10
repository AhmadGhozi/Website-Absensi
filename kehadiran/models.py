from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils import timezone

class Siswa(models.Model):
    nisn = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)
    kelas = models.CharField(max_length=50)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)

    def save(self, *args, **kwargs):
        # Otomatis buat QR Code menggunakan NISN jika belum ada
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.nisn)  # Isi di dalam QR Code adalah NISN siswa
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'qr-{self.nisn}.png'
            
            self.qr_code.save(file_name, File(buffer), save=False)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nisn} - {self.nama}"


class Absensi(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE)
    
    tanggal = models.DateField(default=timezone.now)
    waktu = models.TimeField(default=timezone.now)
    
    status = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.siswa.nama} - {self.tanggal} ({self.status})"