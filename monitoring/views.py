from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import UK, MonitoringLog, PUCB, PIF
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timezone
import pytz
localtime = pytz.timezone("Asia/Krasnoyarsk")

# Create your views here.

@login_required
def monitoring_view(request):
    #return HttpResponse("Monitoring app")
    pifs = {}
    pifs['total'] = PIF.objects.count()
    #pifs['lastchange'] = PIF.objects.latest('pif_lastupdate', '-pif_lastupdate')['pif_lastupdate']
    #pifs['lastchange'] = pifs['lastchange'].astimezone(localtime).strftime("%d.%m.%Y %H:%M:%S")
    monlog = MonitoringLog.objects.filter(status='Ended').last()
    if monlog is not None:
        lastmon = {}
        lastmon['date'] = '{}'.format(monlog.date.astimezone(localtime).strftime("%d.%m.%Y %H:%M:%S"))
        sites = UK.objects.filter(~Q(uk_site=''))
        lastmon['total'] = len(sites)
        pucb = PUCB.objects.filter(pucb_enabled=True)
        lastmon['total'] += len(pucb)
        lastmon['unavailable'] = monlog.unavailable
        lastmon['errors'] = monlog.errors
        monerrors = []
        #for error in UK.objects.filter(~Q(uk_site_unavailable_code=0)):
        #    monerrors.append({'site': error.uk_site, 'code': error.uk_site_unavailable_code, 'text': error.uk_site_error_text})
        return render(request, 'front_page.html', { 'lastmon': lastmon, 
                                'monerrors' : monerrors, 'pifs' : pifs })
    else:
        return render(request, 'front_page.html', {'pifs': pifs})


@csrf_protect
def report_generation(request):
    if request.method == 'POST':
        # Получение данных из формы
        date = request.POST.get('date')
        parameters = request.POST.get('parameters')

        # Выполнение требуемых действий с данными
        # Например, вы можете вызвать ваш скрипт или выполнить какую-то другую логику здесь

        # Возвращение ответа
        return HttpResponse('Действие выполнено успешно!')