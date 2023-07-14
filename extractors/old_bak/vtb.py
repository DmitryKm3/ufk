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

vtb = UK.objects.filter(uk_ogrn = '1027739323600').first()
pifset = PIF.objects.filter(Q(pif_uk = vtb) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

months = { 'января': '01',
            'февраля': '02',
            'марта': '03',
            'апреля': '04',
            'мая': '05',
            'июня': '06',
            'июля': '07',
            'августа': '08',
            'сентября': '09',
            'октября': '10',
            'ноября': '11',
            'декабря': '12',
        }

def getcontents(url, sub=False):

    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    menu = soup.select('ul.nav-menu-content li:not(.disabled) a')
    curmenuitem = soup.select('ul.nav-menu-content li.disabled a')
    curitem = curmenuitem[0].string
   
    s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
    domain = s[0]
    menuitems = [domain + a['href'] for a in menu if a.text.lower().find('подписаться') == -1]
    sibarray = [] 

    for section in soup.select('div.documents-content-section:has(div.doc-for-content-block-item)'):
        
        elemarray = []
        title = section.select_one('div.document-content-block-title').string
        docs = section.select('div.doc-for-content-block-item a')
        for doc in docs:
            href = doc['href']
            text = doc.select_one('span.doc-for-content-block-item-text-header').string
            dates = doc.select_one('span.doc-for-content-block-item-text-info').text
            s = re.search(', (?P<date>\d{2}) (?P<mon>.*) (?P<year>\d{4}), (?P<time>\d{2}:\d{2})', dates)
            if s is not None:
                date = '.'.join([s['date'], months[s['mon']], s['year']]) + ' ' + s['time'] 
            else:
                s = re.search(', (?P<date>\d{2}) (?P<mon>.*) (?P<year>\d{4})', dates)
                date = '.'.join([s['date'], months[s['mon']], s['year']]) 
            elemarray.append([text, date, href])
        
        if len(elemarray) > 0:
            sibarray.append([title, elemarray])
            
    if len(sibarray) == 0:
        elemarray = []
        docs = soup.select('div.doc-for-content-block-item a')
        for doc in docs:
            href = doc['href']
            text = doc.select_one('span.doc-for-content-block-item-text-header').string
            dates = doc.select_one('span.doc-for-content-block-item-text-info').text
            s = re.search(', (?P<date>\d{2}) (?P<mon>.*) (?P<year>\d{4}), (?P<time>\d{2}:\d{2})', dates)
            if s is not None:
                date = '.'.join([s['date'], months[s['mon']], s['year']]) + ' ' + s['time'] 
            else:
                s = re.search(', (?P<date>\d{2}) (?P<mon>.*) (?P<year>\d{4})', dates)
                date = '.'.join([s['date'], months[s['mon']], s['year']]) 
            elemarray.append([text, date, href])
    
        if len(elemarray) > 0:
            sibarray.append([curitem, elemarray])
        
    if not sub:
        for item in menuitems:
                sibarray = sibarray + getcontents(item, True)
    
    return sibarray

vtbcheck = open('/home/ufk/monitoring_project/templates/vtb.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    vtbcheck.write('<div class="container">')
    vtbcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            vtbcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    vtbcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    vtbcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    vtbcheck.write('</div>')
    vtbcheck.write('</div>')
vtbcheck.close()
