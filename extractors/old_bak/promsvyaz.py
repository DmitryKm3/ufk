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

promsvyaz = UK.objects.filter(uk_ogrn = '1027718000067').first()
pifset = PIF.objects.filter(Q(pif_uk = promsvyaz) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):

    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
   
    activemenus = soup.select('div.faq-item:has(div.faq-item__head.active)')
    pifmenu = activemenus[len(activemenus)-1]
    title = pifmenu.select_one('div.faq-item__body a.active').text
    if not sub:
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        domain = s[0]
        menuelements = []

        for e in pifmenu.select('div.faq-item__body a:not(.active)'): 
            menuelements = menuelements + [{'name': e.text, 'link' : domain + e['href']}]
    
    sibarray = [] 
    elemarray = []
    for doc in soup.select('div.doc-box div.file-item'):
        a = doc.select_one('div.file-item__title a')
        href = a['href']
        text = a.text
        datediv = doc.find('div', {'class': 'file-item__label'}, text=re.compile('\d{2}.\d{2}.\d{4}'))
        if datediv is not None:
            date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datediv.string)
            time = re.search('(?P<time>\d{2}:\d{2})', datediv.string)
            if date is None and time is None:
                datetime = '01.01.0001 00:00'
            else:
                datetime = date['date']
                if time is not None:
                    datetime = datetime + ' ' + time['time']
        else:
            datetime = '01.01.0001 00:00'

        elemarray.append([text, datetime, href])
        
    if len(elemarray) > 0:
        sibarray.append([title, elemarray])
    if not sub:
        for e in menuelements:
            sibarray = sibarray + getcontents(e['link'], True) 
    
    return sibarray

promsvyazcheck = open('/home/ufk/monitoring_project/templates/promsvyaz.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    promsvyazcheck.write('<div class="container">')
    promsvyazcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            promsvyazcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    promsvyazcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    promsvyazcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    promsvyazcheck.write('</div>')
    promsvyazcheck.write('</div>')
promsvyazcheck.close()
