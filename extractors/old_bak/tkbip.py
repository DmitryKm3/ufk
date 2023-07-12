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

tkbip = UK.objects.filter(uk_ogrn = '1027809213596').first()
pifset = PIF.objects.filter(Q(pif_uk = tkbip) & ~Q(pif_checkpage=''))

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
   
    s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
    domain = s[0]
    
    addlinks = [{'href': e['href'], 'title': e.text} for e in soup.select('section p a')]
    
    sibarray = [] 

    sections = soup.select('div.past-names')
    for section in sections:
        title = section.select_one('button').text.strip()
        elemarray = []
        for row in section.select('table.table--files tr'):
            a = row.select_one('a')
            if a is not None:
                href = a['href']
                text = a.text
                datespan = row.find('span', text=re.compile('\d{2}.\d{2}.\d{4}'))
                timespan = row.find('span', text=re.compile('\d{2}:\d{2}'))
                datetime = '01.01.0001 00:00'
                if datespan is not None:
                    date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datespan.text)
                    if date is not None:
                        datetime = date['date']
                        if timespan is not None:
                            time = re.search('(?P<time>\d{2}:\d{2})', timespan.text)
                            if time is not None:
                                datetime = datetime + ' ' + time['time']
                            else:
                                datetime = datetime + ' 00:00'
                        else:
                            datetime = datetime + ' 00:00'
                elemarray.append([text, datetime, href])
        if len(elemarray) > 0:
            sibarray.append([title, elemarray])

    for link in addlinks:
        
        elemarray = []
        
        response = requests.get(link['href'], headers=headers, verify=False)
        html = response.content

        soup = BeautifulSoup(html, 'html.parser')
        for row in soup.select('table.table--files tr'):
            a = row.select_one('a')
            if a is not None:
                href = a['href']
                text = a.text
                datespan = row.find('span', text=re.compile('\d{2}.\d{2}.\d{4}'))
                timespan = row.find('span', text=re.compile('\d{2}:\d{2}'))
                datetime = '01.01.0001 00:00'
                if datespan is not None:
                    date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datespan.text)
                    if date is not None:
                        datetime = date['date']
                        if timespan is not None:
                            time = re.search('(?P<time>\d{2}:\d{2})', timespan.text)
                            if time is not None:
                                datetime = datetime + ' ' + time['time']
                            else:
                                datetime = datetime + ' 00:00'
                        else:
                            datetime = datetime + ' 00:00'
                elemarray.append([text, datetime, href])
        
        if len(elemarray) > 0:
            sibarray.append([link['title'], elemarray])

    return sibarray

tkbipcheck = open('/home/ufk/monitoring_project/templates/tkbip.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    tkbipcheck.write('<div class="container">')
    tkbipcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            tkbipcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    tkbipcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    tkbipcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    tkbipcheck.write('</div>')
    tkbipcheck.write('</div>')
tkbipcheck.close()
