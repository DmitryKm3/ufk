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

firstam = UK.objects.filter(uk_ogrn = '1027739007570').first()
pifset = PIF.objects.filter(Q(pif_uk = firstam) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
co = ChromeOptions()

def getcontents(url, sub=False):

    driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=co)
    driver.get(url)

    menu_elements = driver.find_elements(By.XPATH, "//nav[@id='fund-years']/a")
    ids = []
    for element in menu_elements:
        ids.append({'id':element.get_attribute('data-year'), 'name':element.text})
        element.click()
        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'fund-section-{}'.format(element.get_attribute('data-year'))))
            WebDriverWait(driver, 10).until(element_present)
        except TimeoutException:
            pass
        
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    sibarray = []  
    for id in ids:
        elemarray = []
        docs = soup.select('div.fund-cont-{} div.docs'.format(id['id']))
        if len(docs) == 0:
            print(id)
        for doc in docs:
            href = ''
            link = doc.find('a')
            if link is not None:
                href = link['href']
            text = link.string
            datep = doc.find('p')
            if datep is not None:
                datepos = re.search("\d{2}.\d{2}.\d{4}", datep.text)
                if datepos is not None:
                    elemarray.append([text, datep.text[datepos.span()[0]:], href])
                else:
                    elemarray.append([text, '', href])
            else:
                elemarray.append([text, '', href])

        if len(elemarray) > 0:
            sibarray.append([id['name'], elemarray])

    driver.quit()
    return sibarray

firstamcheck = open('/home/ufk/monitoring_project/templates/firstam.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    firstamcheck.write('<div class="container">')
    firstamcheck.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            firstamcheck.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    firstamcheck.write('<div class="d-flex flex-wrap justify-content-between">')
                    firstamcheck.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    firstamcheck.write('</div>')
    firstamcheck.write('</div>')
firstamcheck.close()
