#!/home/ufk/ufk_venv/bin/python
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring_project.settings")
django.setup()

from datetime import datetime, timezone
import pytz
localtime = pytz.timezone("Asia/Krasnoyarsk")

from fake_useragent import UserAgent
fua = UserAgent(verify_ssl=False)

from monitoring.models import UK, PIF
from django.db.models import Q

sistema = UK.objects.filter(uk_ogrn = '1027700421605').first()
pifset = PIF.objects.filter(Q(pif_uk = sistema) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):
    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    
    sibarray = [] 
    elemarray = []
    
    sections = soup.select('main section')
    docsection = sections[len(sections)-1]
    for header in docsection.select('h6'):
        title = header.text
        for sib in header.next_siblings:
            if sib.name == 'h6':
                break
            elif sib.name == 'div' and 'row' in sib['class']:
                rows = sib.select('table.table-content tr:not(.head)')
                for row in rows:
                    if 'class' in row.attrs.keys() and 'tit' in row['class']:
                        if len(elemarray) > 0:
                            sibarray.append([title, elemarray])
                            elemarray = []
                        title = row.find('td').text
                        continue

                    a = row.select_one('a')
                    if a is not None:
                        href = a['href']
                        text = a.text
                        datetds = row.find_all('td', text=re.compile('\d{2}.\d{2}.\d{4}'))
                        datetime = '01.01.0001 00:00'
                        for datetd in datetds:
                            if len(datetd.select('a')) == 0:
                                date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datetd.text)
                                time = re.search('(?P<time>\d{2}:\d{2})', datetd.text)
                                datetime = '01.01.0001 00:00'
                                if date is not None:
                                    datetime = date['date']
                                    if time is not None:
                                        datetime = datetime + ' ' + time['time']
                                    else:
                                        datetime = datetime + ' 00:00'
                                break
                        elemarray.append([text, datetime, href])

        if len(elemarray) > 0:
            sibarray.append([title, elemarray])
            elemarray = []
    
    return sibarray

sistemacheck = open('/home/ufk/monitoring_project/templates/sistema.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    sistemacheck.write('<div class="container">')
    sistemacheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            sistemacheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    sistemacheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    sistemacheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    sistemacheck.write('</div>')
    sistemacheck.write('</div>')
sistemacheck.close()
