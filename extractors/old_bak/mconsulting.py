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

mc = UK.objects.filter(uk_ogrn = '1027700050168').first()
pifset = PIF.objects.filter(Q(pif_uk = mc) & ~Q(pif_checkpage=''))

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
    
    sibarray = [] 

    sections = soup.select('div.body h3')
    for section in sections:
        elemarray = []
        title = section.text
        table = section.findNext('table', class_='report')
        for row in table.select('tr:has(a)'):
            text = row.find('td').text
            a = row.select_one('a')
            if a is not None:
                href = a['href']
                datetd = row.find('td', text=re.compile('\d{2}.\d{2}.\d{4} \d{2}:\d{2}'))
                datetime = '01.01.0001 00:00'
                if datetd is not None:
                    date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datetd.text)
                    if date is not None:
                        datetime = date['date']
                        time = re.search('(?P<time>\d{2}:\d{2})', datetd.text)
                        if time is not None:
                            datetime = datetime + ' ' + time['time']
                        else:
                            datetime = datetime + ' 00:00'
                elemarray.append([text, datetime, href])
        if len(elemarray) > 0:
            sibarray.append([title, elemarray])

    curitem = soup.select_one('div.body ul.menu li.active')
    nextitem = curitem.find_next_sibling()
    a = nextitem.find('a')
    if a is not None:
        response = requests.get(domain + a['href'], headers=headers, verify=False)
        html = response.content

        soup = BeautifulSoup(html, 'html.parser')
        
        sections = soup.select('div.body h3')
        for section in sections:
            elemarray = []
            title = section.text
            table = section.findNext('table', class_='report')
            for row in table.select('tr:has(a)'):
                text = row.find('td').text
                a = row.select_one('a')
                if a is not None:
                    href = a['href']
                    datetd = row.find('td', text=re.compile('\d{2}.\d{2}.\d{4} \d{2}:\d{2}'))
                    datetime = '01.01.0001 00:00'
                    if datetd is not None:
                        date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datetd.text)
                        if date is not None:
                            datetime = date['date']
                            time = re.search('(?P<time>\d{2}:\d{2})', datetd.text)
                            if time is not None:
                                datetime = datetime + ' ' + time['time']
                            else:
                                datetime = datetime + ' 00:00'
                    elemarray.append([text, datetime, href])
            if len(elemarray) > 0:
                sibarray.append([title, elemarray])

    return sibarray

mccheck = open('/home/ufk/monitoring_project/templates/mc.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    mccheck.write('<div class="container">')
    mccheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            mccheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    mccheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    mccheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    mccheck.write('</div>')
    mccheck.write('</div>')
mccheck.close()
