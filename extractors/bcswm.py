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
        if a_tag:
            href = self.__domain + a_tag['href']
            text_span = a_tag.select_one('span.inform-block-text')
            if text_span:
                text = text_span.text
            else:
                text = 'Наименование документа не указано'
            date_td = doc.find('td', text=re.compile('\d{2}.\d{2}.\d{4}'))
            if date_td:
                date = self.__get_date(date_td.text)
            else:
                date_th = doc.find(lambda tag: tag.name == 'th' and re.search('\d{2}.\d{2}.\d{4}', tag.text))
                if date_th:
                    date = self.__get_date(date_th.text)
                else:
                    date = self.__get_date(text)
            return [(text, date, href)]
        else:
            return []
    
    def __extract_pinned_doc(self, doc):
        a_tag = doc.find('a')
        if a_tag:
            href = self.__domain + a_tag['href']
            text = a_tag.text
            date_div = doc.find('div', class_='pdu_file_data')
            if date_div:
                date = self.__get_date(date_div.text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __extract_table(self, soup):
        doclist = []
        for doc in soup.select('table.fund-table tr:has(a)'):
            doclist += self.__extract_element(doc)
        for doc in soup.select('div.js_collapseArea table.table-requisities tr:has(a)'):
            doclist += self.__extract_element(doc)
        return doclist


    def __parse_contents(self, soup, caption):
        doclist= []
        for doc in soup.select('div.pdu_block div.pdu_block-text'):
            result = self.__extract_pinned_doc(doc)
            if result:
                doclist.append(result)
        doclist += self.__extract_table(soup)
        years_menu = soup.select_one('div.fund-detail-years:has(a)')
        if years_menu:
            active_year = years_menu.select_one('li.active')
            previous_year = active_year.find_previous_sibling()
            previous_year_link = previous_year.find('a')
            if previous_year_link:
                response = requests.get(self.__domain + previous_year_link['href'], headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                doclist += self.__extract_table(soup)
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
        active_element = soup.select_one('div.fund-menu li.active a')
        if active_element:
            caption = active_element.text
        else:
            caption = 'Раскрытие информации' 
        self.__parse_contents(soup, caption)
        for menu_element in soup.select('div.fund-menu li:not(.active) a'):
            response = requests.get(self.__domain + menu_element['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, menu_element.text)
