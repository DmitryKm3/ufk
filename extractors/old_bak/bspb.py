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

bspb = UK.objects.filter(uk_ogrn = '1067746469757').first()
pifset = PIF.objects.filter(Q(pif_uk = bspb) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):
    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    
    sibarray = [] 

    if not sub:
        menu = soup.select('div.disclosure-pif-filter a')
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        domain = s[0]
        menuitems = [domain + '/' + a['href'] for a in menu if a.text != 'Все']
        #main page
    else:
        title = soup.select_one('div.disclosure-pif-filter a.current').text
        elemarray = []
        for row in soup.select('div.tbl-black table tbody tr'):
            a = row.find('a')
            href = a['href']
            text = a.text
            datetd = row.find('td', text=re.compile('\d{2}.\d{2}.\d{4}'))
            if datetd is not None:
                date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datetd.text)
                time = re.search('(?P<time>\d{2}:\d{2})', datetd.text)
                datetime = '01.01.0001 00:00'
                if date is not None:
                    datetime = date['date']
                    if time is not None:
                        datetime = datetime + ' ' + time['time']
                    else:
                        datetime = datetime + ' 00:00'
            else:
                datetime = '01.01.0001 00:00'
            elemarray.append([text, datetime, href])
        if len(elemarray) > 0:
            sibarray.append([title, elemarray])
        
    if not sub:
        for item in menuitems:
                sibarray = sibarray + getcontents(item, True)
    
    return sibarray

bspbcheck = open('/home/ufk/monitoring_project/templates/bspb.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    bspbcheck.write('<div class="container">')
    bspbcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            bspbcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    bspbcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    bspbcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    bspbcheck.write('</div>')
    bspbcheck.write('</div>')
bspbcheck.close()
