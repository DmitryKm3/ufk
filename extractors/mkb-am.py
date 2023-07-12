from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re

#from selenium import webdriver
#from selenium.webdriver import ChromeOptions
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.common.exceptions import TimeoutException
#from selenium.common.exceptions import NoSuchElementException
#co = ChromeOptions()

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
localtime = pytz.timezone("Asia/Krasnoyarsk")
fua = UserAgent(verify_ssl=False)
headers = {'User-Agent': fua.random}

class Extractor:
    __scraped_data = None
    __url = None
    __kid_page = 'https://www.mkb-am.ru/information/main-documents/'

    def __init__(self, url):
        self.__url = url 

    def get_data(self, delta = 30):
        
        if self.__scraped_data is not None:

            startdate = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=localtime) - timedelta(delta)
            output_list = []
        
            for section in self.__scraped_data:
                section_data = [e for e in section[1] if e[1] >= startdate]
                if len(section_data) > 0:
                    output_list.append([section[0], section_data])

            return output_list
        else:
            return []

    def __get_date(self, tag):
        dates = re.search('(?P<date>\d{2}.\d{2}.\d{4})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = dates['date']
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        a_tag = doc.select_one('a')
        if a_tag:
            href = self.__domain + a_tag['href']
            text = a_tag.text.strip()
            date_span = doc.find('span', text=re.compile('\d{2}.\d{2}.\d{4}'))
            if date_span:
                date = self.__get_date(date_span.parent.text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup):
        tabs = soup.select('div.info-section__content div.info-section__tabs \
                            div.info-section__tabs-nav-item')
        contents = [soup.find('div', id=f'tab-{tab["data-tab"]}') for tab in tabs]
        for tab, content in zip(tabs, contents):
            doclist = []
            caption = tab.text.strip()
            for doc in content.select('div.report-table__row'):
                result = self.__extract_element(doc)
                if result:
                    doclist.append(result)
            if len(doclist) > 0:
                if self.__scraped_data is None:
                    self.__scraped_data = [] 
                    self.__scraped_data.append([caption, doclist])
                else:
                    self.__scraped_data.append([caption, doclist])

    def __parse_kid(self, soup, pif_name):
        pif_accardion = soup.find('div', class_='info-section__accardion-title', text=lambda t: t.lower() == pif_name)
        if pif_accardion:
            doclist = []
            caption = 'Ключевой информационный документ'
            accardion = pif_accardion.find_parent('div', class_='info-section__accardion')
            for doc in accardion.select('div.report-table__row'):
                result = self.__extract_element(doc)
                if result:
                    doclist.append(result)
            if len(doclist) > 0:
                if self.__scraped_data is None:
                    self.__scraped_data = [] 
                    self.__scraped_data.append([caption, doclist])
                else:
                    self.__scraped_data.append([caption, doclist])

    def scrape(self):
        response = requests.get(self.__url, headers=headers, verify=False)
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        self.__domain = s[0]
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)
        pif_tag = soup.select_one('div.info-section__content div.info-section__content-title.h3')
        if pif_tag:
            pif_name = pif_tag.string.strip().lower()
            response = requests.get(self.__kid_page, headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_kid(soup, pif_name)
