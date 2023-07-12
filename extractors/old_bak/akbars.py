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

akbars = UK.objects.filter(uk_ogrn = '1021401047799').first()
pifset = PIF.objects.filter(Q(pif_uk = akbars) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):

    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
   
    subs = soup.select('div.free_info_pif')
    
    sibarray = [] 
    for sub in subs:
        elemarray = []
        titletag = sub.find('h2')
        if titletag is not None:
            title = titletag.text
            docs = sub.select('a.documts')
            for doc in docs:
                text = doc.text
                href = doc['href']
                datediv = doc.find_next_sibling('div', class_='info_date')
                if datediv is not None:
                    datei = datediv.find('i', text=re.compile('\d{2}.\d{2}.\d{4}'))
                    if datei is not None:
                        date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datei.string)
                        time = re.search('(?P<time>\d{2}:\d{2}:\d{2})', datei.string)
                        if date is None and time is None:
                            datetime = '01.01.0001 00:00:00'
                        else:
                            datetime = date['date']
                            if time is not None:
                                datetime = datetime + ' ' + time['time']
                    else:
                        datetime = '01.01.0001 00:00:00'

                elemarray.append([text, datetime, href])
        
        if len(elemarray) > 0:
            sibarray.append([title, elemarray])
    
    return sibarray

akbarscheck = open('/home/ufk/monitoring_project/templates/akbars.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    akbarscheck.write('<div class="container">')
    akbarscheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            akbarscheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    akbarscheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    akbarscheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    akbarscheck.write('</div>')
    akbarscheck.write('</div>')
akbarscheck.close()
