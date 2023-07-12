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

dohod = UK.objects.filter(uk_ogrn = '1027810309328').first()
pifset = PIF.objects.filter(Q(pif_uk = dohod) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):
    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    curmenuitem = soup.select('ul.filters__list a.filters__link--active')
    curitem = curmenuitem[0].string.strip()
    sibarray = [] 

    if not sub:
        menu = soup.select('ul.filters__list a:not(.filters__link--active)')
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        domain = s[0]
        menuitems = [domain + '/' + a['href'] for a in menu]
        #main page
        sections = soup.select('div.flex_table__row:has(li.files__item)')
        for section in sections:
            elemarray = []

            title = section.find('div', {'class': 'flex_table__cell'})
            if title.text.lower().find('заявка') == -1:
                title = ' '.join(title.text.split())
                for row in section.findAll('li'):
                    a = row.find('a')
                    href = a['href']
                    text = row.find('span', {'class': 'files__name'}).string
                    date = row.find('span', {'class': 'files__caption'}).string
                    elemarray.append([text, date, href])
                if len(elemarray) > 0:
                    sibarray.append([title, elemarray])
    else:
        sections = soup.select('div.reports__block:has(li.files__item)')
        title = curitem
        elemarray = []
        for section in sections:
            for row in section.findAll('li'):
                a = row.find('a')
                href = a['href']
                text = row.find('span', {'class': 'files__name'}).string
                date = row.find('span', {'class': 'files__caption'}).string
                elemarray.append([text, date, href])
        if len(elemarray) > 0:
            sibarray.append([title, elemarray])
        

    if not sub:
        for item in menuitems:
                sibarray = sibarray + getcontents(item, True)
    
    return sibarray

dohodcheck = open('/home/ufk/monitoring_project/templates/dohod.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    dohodcheck.write('<div class="container">')
    dohodcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            dohodcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    dohodcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    dohodcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    dohodcheck.write('</div>')
    dohodcheck.write('</div>')
dohodcheck.close()
