from django.shortcuts import render

def halaman_scan(request):
    return render(request, 'kehadiran/scan.html')