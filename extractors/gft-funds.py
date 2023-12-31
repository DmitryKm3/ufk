from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

import requests
from urllib3.exceptions import InsecureRequestWarning
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
        a_tag = doc.find('a')
        if a_tag is not None:
            href = self.__domain + a_tag['href']
            text = a_tag.string
            tds = doc.select('td')
            if tds:
                date = self.__get_date(tds[1].string)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __extract_page(self, soup):
        doclist = []
        for row in soup.select('table.info_disclos tr:has(a)'):
            result = self.__extract_element(row)
            if result is not None:
                doclist.append(result)
        for docs_category in soup.select('div.right_column ul.accordion-list li.cuhair'):
            doc_name = docs_category.h3.text
            for doc in docs_category.select('a'):
                href = self.__domain + doc['href']
                text = doc_name + doc.string.replace('Скачать отчет', '')
                date_small = doc.find_next_sibling('small', string=re.compile('\d{2}.\d{2}.\d{4}'))
                if date_small:
                    date = self.__get_date(date_small.string)
                else:
                    date = self.__get_date(text)
                doclist.append((text, date, href))
        return doclist

    def __parse_contents(self, soup, caption):
        active_page = soup.select_one('div.right_column div.page_select:has(li.active)')
        if active_page:
            all_contents = active_page.find_next('a', string=re.compile('все', re.IGNORECASE))
            response = requests.get(self.__domain + all_contents['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            doclist = self.__extract_page(soup)
        else:
            #чтобы собрать всю отчетность, необходимо пройти по ссылкам с помощью Selenium
            doclist = []
            doclist += self.__extract_page(soup)
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
        active_element = soup.select_one('ul#gft-left-menu li.active ul.root-item li.active a')
        if active_element:
            caption = active_element.string
        else:
            caption = 'Раскрытие информации'
        self.__parse_contents(soup, caption)
        menu_elements = soup.select('ul#gft-left-menu li.active ul.root-item li:not(.active) a')
        for menu_element in menu_elements:
            response = requests.get(self.__domain + menu_element['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            caption = menu_element.string
            self.__parse_contents(soup, caption)
