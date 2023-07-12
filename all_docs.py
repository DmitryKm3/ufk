#!/home/ufk/ufk_venv/bin/python
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring_project.settings")
django.setup()

from datetime import datetime, timezone
import pytz
localtime = pytz.timezone("Asia/Krasnoyarsk")

from monitoring.models import UK, PIF
from django.db.models import Q

import time
import re

import importlib

def filter_out(content, rules, count=1):
    filtered_content = []
    rules_list = rules.split(';;;')
    for section in content:
        if any([re.match(rule, section[0], re.IGNORECASE) for rule in rules_list]):
            filtered_content += section[1]
            continue
        filtered_content += [doc for doc in section[1] if any([re.match(rule, doc[0], re.IGNORECASE) for rule in rules_list])]
    return sorted(filtered_content, key=lambda tup: tup[1], reverse=True)[:count]

uks = UK.objects.all()
days_count = 49
sum = 0
start_time = time.time()
report_data = []
total_start = time.time()
filename = '/home/ufk/monitoring_project/static/pif_alldocs.xlsx'
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Все документы'
wb.save(filename=filename)
for uk in uks:
    wb = openpyxl.load_workbook(filename)
    ws = wb.active
    print(f'Doing UK: {uk.uk_name}')
    start_time = time.time()
    module = None
    if uk.uk_extractor:
        module = importlib.import_module(f'extractors.{uk.uk_extractor}')
    for pif in PIF.objects.filter(Q(pif_uk = uk)):
        ext = None
        print(pif.pif_name)
        if not pif.pif_enabled:
            continue
        if pif.pif_checkpage and module:
            ws.append((pif.pif_npp, pif.pif_name, '://'.join((uk.uk_sitetype, uk.uk_site))))
            try:
                ext = module.Extractor(pif.pif_checkpage)
                ext.scrape()
                content = filter_out(ext.get_data(days_count), '.*', None)
                if len(content) == 0:
                    content = [['Документы не найдены', localtime.localize(datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M')), '']]
                for doc in content:
                    ws.append(('', doc[0], doc[1].strftime("%d.%m.%Y %H:%M"), doc[2]))
            except Exception as e:
                print(f'Ошибка при получении: {pif.pif_name} \t {pif.pif_checkpage}')
                print(content)
                content = [['Ошибки при работе правила: {e}', localtime.localize(datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M')), '']]
                for doc in content:
                    ws.append(('', doc[0], doc[1].strftime("%d.%m.%Y %H:%M"), doc[2]))
        else:
            ws.append((pif.pif_npp, pif.pif_name, '://'.join((uk.uk_sitetype, uk.uk_site))))
            content = [['Не задана страница фонда или отсутствует правило', localtime.localize(datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M')), '']]
            for doc in content:
                ws.append(('', doc[0], doc[1].strftime("%d.%m.%Y %H:%M"), doc[2]))
        if module and ext:
            del ext
    wb.save(filename)
    del module
    print(f'UK execution time: {time.time() - start_time}')
#for row in report_data:
#    ws.append(row)
#wb.save(filename=filename)    
print(f'Total execution time: {time.time() - total_start}')
