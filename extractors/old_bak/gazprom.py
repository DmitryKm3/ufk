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

gazprom = UK.objects.filter(uk_ogrn = '1047796382920').first()
pifset = PIF.objects.filter(Q(pif_uk = gazprom) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):

    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
   
    #s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
    #domain = s[0]
    menuelements = []
    for e in soup.select('div.page-nav.mainTab-check span'):
        menuelements = menuelements + [{'name': e.text, 'id' : e['data-tab']}]

    sibarray = [] 

    for element in menuelements:
        
        elemarray = []
        rows = soup.select('div.tab[data-tab="{}"] table tbody tr'.format(element['id']))
        for row in rows:
            a = row.select_one('td a')
            href = a['href']
            text = a.find('span', {'class': 'infTable-icon-text'}).text
            datetd = row.select_one('td[data-attr*="публикации"]')
            date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datetd.text)
            time = re.search('(?P<time>\d{2}:\d{2})', datetd.text)
            if date is None and time is None:
                datetime = '01.01.0001 00:00'
            else:
                datetime = date['date']
                if time is not None:
                    datetime = datetime + ' ' + time['time']

            elemarray.append([text, datetime, href])
        
        if len(elemarray) > 0:
            sibarray.append([element['name'], elemarray])
            
    return sibarray

gazpromcheck = open('/home/ufk/monitoring_project/templates/gazprom.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    gazpromcheck.write('<div class="container">')
    gazpromcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            gazpromcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    gazpromcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    gazpromcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    gazpromcheck.write('</div>')
    gazpromcheck.write('</div>')
gazpromcheck.close()
