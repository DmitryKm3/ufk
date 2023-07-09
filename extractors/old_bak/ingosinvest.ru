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

ingosinvest = UK.objects.filter(uk_ogrn = '1027700339666').first()
pifset = PIF.objects.filter(Q(pif_uk = ingosinvest) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url, sub=False):
    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    sections = soup.select('li:has(ul.large.list):not(:has(div.tabContent))')
    
    sibarray = [] 
    
    for section in sections:
        elemarray = []
        caption = section.select_one('a.lineInfo span.nameInfo')
        title = caption.text
        docs = section.select('ul.large.list li')
        for doc in docs:
            link = doc.select_one('a')
            href = link['href']
            text = link.text
            datespan = doc.find('span', text=re.compile('\d{2}.\d{2}.\d{4}'))
            date = '01.01.0001'
            if datespan is not None:
                s = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datespan.text)
                date = s['date']
                s = re.search('(?P<time>\d{2}:\d{2})', datespan.text)
                if s is not None:
                    date = date + ' ' + s['time']
            elemarray.append([text, date, href])

        if len(elemarray) > 0:
            sibarray.append([title, elemarray])

    #отчетность
    elemarray = []
    section = soup.select_one('li:has(div.tabContent)')
    caption = section.select_one('a.lineInfo span.nameInfo')
    title = caption.text
    lastref = section.select_one('ul.nav li.last a')
    id = lastref['href'].replace('#', '')
    rows = section.select('div#{} div.tableReporting ul li'.format(id))
    header = []
    for row in rows:
        divs = row.findAll('div')
        if len(header) == 0:
            for div in divs:
                header.append(div.text)
        else:
            for i in range(1, len(divs)):
                if divs[i].text.strip() != '-':
                    text = '{} ({})'.format(divs[0].text, header[i])
                    link = divs[i].select_one('a')
                    href = link['href']
                    datespan = divs[i].find('span', {'class': 'fileinfo'})
                    date = '01.01.0001'
                    if datespan is not None:
                        s = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datespan.text)
                        date = s['date']
                        s = re.search('(?P<time>\d{1,2}:\d{2})', datespan.text)
                        if s is not None:
                            date = date + ' ' + s['time']
                    elemarray.append([text, date, href])
    
    if len(elemarray) > 0:
        sibarray.append([title, elemarray])
    
    return sibarray

ingoscheck = open('/home/ufk/monitoring_project/templates/ingosinvest.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    ingoscheck.write('<div class="container">')
    ingoscheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            ingoscheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    ingoscheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    ingoscheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    ingoscheck.write('</div>')
    ingoscheck.write('</div>')
ingoscheck.close()
