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

raiff = UK.objects.filter(uk_ogrn = '1037702037680').first()
pifset = PIF.objects.filter(Q(pif_uk = raiff) & ~Q(pif_checkpage=''))

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup
import re

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
co = ChromeOptions()

def getcontents(url, sub=False):

    driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=co)
    driver.get(url)

    s = re.search('INFO_SUBSECTION(?P<section>\d*)-(?P<value>\d*)', url)
    filteritem = driver.find_element(By.XPATH, '//option[@value = "{}" and @data-section = "{}"]'.format(s['value'], s['section']))
    fund_name = filteritem.get_property('text')

    menu_section = driver.find_element(By.XPATH, '//*[text()="Паевые инвестиционные фонды"]/../..')
    elements = [e.text for e in menu_section.find_elements(By.XPATH, './/li[not(contains(@class, "active"))]')]
    section = menu_section.find_element(By.XPATH, './/li[contains(@class, "active")]').text

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    sibarray = []

    docs = soup.select('div.list_files div:not(.more_list) a')
    elemarray = []
    for doc in docs:
        text = doc.contents[0].strip()
        href = doc['href']
        datep = doc.find('p')
        if datep is not None:
            dates = re.search('\d{2}.\d{2}.\d{4} \d{2}:\d{2}:\d{2}', datep.text)
            date = dates.group(0)
        elemarray.append([text, date, href])
    sibarray.append([section, elemarray])    

    for e in elements:
        menu_item = driver.find_element(By.XPATH, '//*[text()="{}"]/..'.format(e))
        try:
            element_present = EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"global__preloader") and @style="display: none;"]'))
            WebDriverWait(driver, 10).until(element_present)
            menu_item.click()
        except TimeoutException:
            break
        
        try:
            element_present = EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"global__preloader") and @style="display: none;"]'))
            WebDriverWait(driver, 20).until(element_present)
            filter = driver.find_element(By.XPATH, '//select[@data-key="INFO_FUND"]/..')
            try:
                element_clickable = EC.element_to_be_clickable((By.XPATH, '//select[@data-key="INFO_FUND"]/..'))
                WebDriverWait(driver, 20).until(element_clickable)
                filter.click()
            except TimeoutException:
                break
            fund = driver.find_element(By.XPATH, '//li[@data-prop="INFO_FUND" and text()="{}"]'.format(fund_name))
            try:
                element_clickable = EC.element_to_be_clickable((By.XPATH, '//li[@data-prop="INFO_FUND" and text()="{}"]'.format(fund_name)))
                WebDriverWait(driver, 20).until(element_clickable)
                fund.click()
            except TimeoutException:
                break
        except (NoSuchElementException, TimeoutException):
            break
        

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        docs = soup.select('div.list_files div:not(.more_list) a')
        elemarray = []
        for doc in docs:
            text = doc.contents[0].strip()
            href = doc['href']
            datep = doc.find('p')
            if datep is not None:
                dates = re.search('\d{2}.\d{2}.\d{4} \d{2}:\d{2}:\d{2}', datep.text)
                date = dates.group(0)
            elemarray.append([text, date, href])
        sibarray.append([e, elemarray])    
    
    driver.quit()
    return sibarray

raiff = open('/home/ufk/monitoring_project/templates/raiff.html', 'w')

for pif in pifset:
    content = getcontents(pif.pif_checkpage)
    raiff.write('<div class="container">')
    raiff.write('<h3>{}</h3><a href="{}">{}</a>'.format(pif.pif_shortname, pif.pif_checkpage, pif.pif_checkpage))
    for e in content:
        if len(e) > 0:
            raiff.write('<h5>{}</h5>'.format(e[0]))
            for k in e[1]:
                if len(k) > 0:
                    raiff.write('<div class="d-flex flex-wrap justify-content-between">')
                    raiff.write('<a href=\"{}\">{}</a><p><b>{}</b>'.format(pif.pif_uk.uk_sitetype + '://' + pif.pif_uk.uk_site + k[2], k[0], k[1]))
                    raiff.write('</div>')
    raiff.write('</div>')
raiff.close()
