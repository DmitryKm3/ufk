from django.shortcuts import render
from django.http import HttpResponse
from .models import DeviceType, Device
from django.db.models import Q
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.contrib.staticfiles.utils import get_files
import os
from django.conf import settings
import random


# Create your views here.
def selfcare(request):
    content = []
    for index, dtype in enumerate(DeviceType.objects.all()):
        group = {'name': dtype.name, 'id': f'type{index}', 'devices': Device.objects.filter(Q(device_type = dtype), enabled=True)}
        content.append(group)
    return render(request, 'selfcare_front.html', {'content': content})

def device_view(request, pk):
    printer = Device.objects.get(id=pk)
    content = []
    for index, dtype in enumerate(DeviceType.objects.all()):
        group = {'name': dtype.name, 'id': f'type{index}', 'devices': Device.objects.filter(Q(device_type = dtype), enabled=True)}
        content.append(group)
    s = StaticFilesStorage()
    files = sorted(list(get_files(s, location=f'img/printers/{pk}')))
    return render(request, 'selfcare_device.html', {'printer': printer, 'content': content, 'files': files})

def mart(request):
    videos = os.listdir(path=f'{settings.STATIC_ROOT}/8marta/')
    return render(request, '8marta.html', {'video_file': random.choice(videos)})

def ui(request):
    return render(request, '8marta_ui.html')


