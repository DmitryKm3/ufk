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

bcswm = UK.objects.filter(uk_ogrn = '1027739003489').first()
pifset = PIF.objects.filter(Q(pif_uk = bcswm) & ~Q(pif_checkpage=''))

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
    if not sub:
        menuelements = [e['href'] for e in soup.select('div.fund-menu li:not(.active) a')]
    
    curelement = soup.select_one('div.fund-menu li.active a')
    title = curelement.text

    sibarray = [] 
    elemarray = []

    #закрепленный(ые) документ(ы)
    pinneddocs = soup.select('div.pdu_block div.pdu_block-text')
    for doc in pinneddocs:
        a = doc.find('a')
        if a is not None:
            href = a['href']
            text = a.text
            datediv = doc.find('div', class_='pdu_file_data')
            datetime = '01.01.0001 00:00'
            if datediv is not None:
                date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datediv.text)
                time = re.search('(?P<time>\d{2}:\d{2})', datediv.text)
                if date is not None:
                    datetime = date['date']
                    if time is not None:
                        datetime = datetime + ' ' + time['time']
                    else:
                        datetime = datetime + ' 00:00'
            elemarray.append([text, datetime, href])
    
    for row in soup.select('table.fund-table tr:has(a)'):
        a = row.find('a')
        if a is not None:
            href = a['href']
            text = a.select_one('span.inform-block-text').text
        datetd = row.find('td', text=re.compile('\d{2}.\d{2}.\d{4}'))
        if datetd is not None:
            date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datetd.text)
            time = re.search('(?P<time>\d{2}:\d{2})', datetd.text)
            if date is not None:
                datetime = date['date']
                if time is not None:
                    datetime = datetime + ' ' + time['time']
                else:
                    datetime = datetime + ' 00:00'
        elemarray.append([text, datetime, href])

    yearsmenu = soup.select_one('div.fund-detail-years:has(a)')
    if yearsmenu is not None:
        activeyear = yearsmenu.select_one('li.active')
        prevyear = activeyear.find_previous_sibling()
        a = prevyear.find('a')['href']
        response = requests.get(domain + a, headers=headers, verify=False)
        html = response.content

        soup = BeautifulSoup(html, 'html.parser')
        for row in soup.select('table.fund-table tr:has(a)'):
            a = row.find('a')
            if a is not None:
                href = a['href']
                text = a.select_one('span.inform-block-text').text
            datetd = row.find('td', text=re.compile('\d{2}.\d{2}.\d{4}'))
            if datetd is not None:
                date = re.search('(?P<date>\d{2}.\d{2}.\d{4})', datetd.text)
                time = re.search('(?P<time>\d{2}:\d{2})', datetd.text)
                if date is not None:
                    datetime = date['date']
                    if time is not None:
                        datetime = datetime + ' ' + time['time']
                    else:
                        datetime = datetime + ' 00:00'
            elemarray.append([text, datetime, href])

    if len(elemarray) > 0:
        sibarray.append([title, elemarray])

    if not sub:        
        for e in menuelements:
            sibarray = sibarray + getcontents(domain + e, True)

    return sibarray

bcswmcheck = open('/home/ufk/monitoring_project/templates/bcswm.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    bcswmcheck.write('<div class="container">')
    bcswmcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            bcswmcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    bcswmcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    bcswmcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    bcswmcheck.write('</div>')
    bcswmcheck.write('</div>')
bcswmcheck.close()
