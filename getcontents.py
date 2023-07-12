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

gamma = UK.objects.filter(uk_ogrn = '1175476116420').first()
pifset = PIF.objects.filter(Q(pif_uk = gamma) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

def getcontents(url):

    response = requests.get(url, headers=headers, verify=False)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')

    sibarray = []
    for tag in soup.find_all(["h1","h2","h3", "h4", "h5", "h6"]):
        if tag.text.strip() != "":
            elemarray = []
            sibling = tag.find_next_sibling()
            while sibling is not None:
                if sibling.name == "p" and sibling.text.strip() != "":
                    name = sibling.text
                    sibling = sibling.find_next_sibling()
                    if sibling is not None:
                        if sibling.name == "p":
                            dates = re.findall(r'\d{2}.\d{2}.\d{4}', sibling.text)
                            if len(dates) > 0:
                                elemarray.append([name, dates[0]])
                            sibling = sibling.find_next_sibling()
                        else:
                            sibling = sibling.find_next_sibling()
                else:
                    sibling = sibling.find_next_sibling()
                if sibling is not None and sibling.name in ["h1","h2","h3", "h4", "h5", "h6", "div"]:
                    sibling = None
            if len(elemarray) > 0:
                sibarray.append([tag.text, elemarray])
    return sibarray

gammacheck = open('/home/ufk/monitoring_project/templates/gamma.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    gammacheck.write('<div class="container">')
    gammacheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        gammacheck.write('<h5>{}</h5>'.format(e[0]))
        #for k in e[1]:
        gammacheck.write('<div class="d-flex flex-wrap justify-content-between">')
        gammacheck.write('<p>{}</p><p><b>{}</b></p>'.format(e[1][0][0], e[1][0][1]))
        gammacheck.write('</div>')
    gammacheck.write('</div>')
gammacheck.close()
