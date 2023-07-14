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

aton = UK.objects.filter(uk_ogrn = '1027700027233').first()
pifset = PIF.objects.filter(Q(pif_uk = aton) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):

    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.select('div.content table')
    if len(tables) > 1:
        menu_table = tables[0]
        doc_table = tables[1]
    else: 
        return []
    curmenuitem = menu_table.select('td:not(:has(a))')
    curitem = curmenuitem[0].string
   
    s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
    domain = s[0]
    menuitems = [domain + a['href'] for a in menu_table.select('td:has(a) a')]

    sibarray = [] 
    elemarray = []

    for tr in doc_table.select('tr:has(a)'):
        
        link = tr.select_one('a')
        href = ''
        text = ''
        if link is not None:
            text = link.string
            href = link['href']
        
        date = tr.find('span', string=re.compile('\d{2}.\d{2}.\d{4}'))
        if date is not None:
            elemarray.append([text, date.string, href])

    if len(elemarray) > 0:
        sibarray.append([curitem, elemarray])

    if not sub:
        for item in menuitems:
                sibarray = sibarray + getcontents(item, True)
    
    return sibarray

atoncheck = open('/home/ufk/monitoring_project/templates/aton.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    atoncheck.write('<div class="container">')
    atoncheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            atoncheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    atoncheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    atoncheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    atoncheck.write('</div>')
    atoncheck.write('</div>')
atoncheck.close()
