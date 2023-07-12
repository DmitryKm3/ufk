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

rshb = UK.objects.filter(uk_ogrn = '1127746635950').first()
pifset = PIF.objects.filter(Q(pif_uk = rshb) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):

    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    
    menu_items = soup.select('div.rules_tabs ul.uk-slider-items li')
    menu = []
    for item in menu_items:
        menu.append(item.string)
    
    sibarray = [] 

    for i in range(len(menu)):
        elemarray = []
        docs = soup.select('li.rules_tabs{} ul.docs.container li'.format(i+1))
        if len(docs) > 0:
            for doc in docs:
                link = doc.find('a')
                if link is not None:
                    href = link['href']
                    text = link.text
                    date = doc.find('span', string=re.compile('\d{2}.\d{2}.\d{4} \d{2}:\d{2}'))
                    if date is not None:
                        elemarray.append([text, date.string, href])
                    else:
                        elemarray.append([text, '', href])
            if len(elemarray) > 0:
                sibarray.append([menu[i], elemarray])

    return sibarray

rshbcheck = open('/home/ufk/monitoring_project/templates/rshb.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    rshbcheck.write('<div class="container">')
    rshbcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            rshbcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    rshbcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    rshbcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    rshbcheck.write('</div>')
    rshbcheck.write('</div>')
rshbcheck.close()
