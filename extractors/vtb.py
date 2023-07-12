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

class Extractor:
    __scraped_data = None
    __url = None

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
        dates = re.search(', (?P<date>\d{2}) (?P<mon>.*) (?P<year>\d{4})', tag)
        times = re.search(', (?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = '.'.join([dates['date'], months[dates['mon']], dates['year']])
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        href = self.__domain + doc['href']
        text_span = doc.select_one('span.doc-for-content-block-item-text-header')
        if text_span:
            text = text_span.string
        else:
            text = 'Наименование документа не указано'
        date_span = doc.select_one('span.doc-for-content-block-item-text-info')
        if date_span:
            date = self.__get_date(date_span.string)
        else:
            date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup, caption):
        content_parsed = False
        for section in soup.select('div.documents-content-section:has(div.doc-for-content-block-item)'):
            doclist = [] 
            section_caption = section.select_one('div.document-content-block-title').string
            for doc in section.select('div.doc-for-content-block-item a'):
                result = self.__extract_element(doc)
                if result:
                    doclist.append(result)
            if len(doclist) > 0:
                if self.__scraped_data is None:
                    self.__scraped_data = [] 
                    self.__scraped_data.append([section_caption, doclist])
                else:
                    self.__scraped_data.append([section_caption, doclist])
                content_parsed = True
        if not content_parsed:
            doclist = [] 
            for doc in soup.select('div.doc-for-content-block-item a'):
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
        active_element = soup.select_one('ul.nav-menu-content li.disabled a') 
        caption = active_element.string
        self.__parse_contents(soup, caption)
        menu_elements = [a for a in soup.select('ul.nav-menu-content li:not(.disabled) a') \
                        if a.text.lower().find('подписаться') == -1]
        for menu_element in menu_elements:
            caption = menu_element.string
            response = requests.get(self.__domain + menu_element['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
