from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import UK, MonitoringLog, PUCB, PIF
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect
import pytz
import datetime
from datetime import date, datetime
from kid import kidpy, send_report_email
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
        start_date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
        request_parameters = request.POST.get('parameters')
        email = request.POST.get('email')
        # Выполнение требуемых действий с данными
        today =  date.today()
        delta = today - start_date
        days = delta.days #кол-во дней между датами
        print(f"Дата = {days} Строка подзапроса = {request_parameters} email = {email}")

        #функция s_r_e отправляет отчет на почту, kidpy формирует его и сохраняет путь в виде f'static/report_kid_{date_str}.xlsx'
        kidpy(days, request_parameters)
        send_report_email(email)
        return render(request, 'front_page.html')
        # Возвращение ответа
