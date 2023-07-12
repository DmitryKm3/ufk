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
        href = self.__domain + doc['href']
        title_span = doc.find('span', class_='lnk')
        if title_span:
            text = title_span.string
        else:
            text = 'Название документа не указано'
        date_span = doc.find('span', class_='date')
        if date_span:
            date = self.__get_date(date_span.string)
        else:
            date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup, caption='Раскрытие информации'):
        tabs = [[a.string.strip() for a in soup.select('table.main-content-blk \
                            td.right_column div.contentTabs ul#contentTabs li a')]]
        if len(tabs[0]) > 0:
            tabs.append([div for div in soup.select('table.main-content-blk \
                    td.right_column div.content div#content_container div[id]') \
                    if 'tab' in div.attrs['id']])
            for tcaption, section in zip(tabs[0], tabs[1]):
                doclist = []
                for doc in section.select('div.file-lnk a'):
                    result = self.__extract_element(doc)
                    if result is not None:
                        doclist.append(result)
                if len(doclist) > 0:
                    if self.__scraped_data is None:
                        self.__scraped_data = [] 
                        self.__scraped_data.append([tcaption, doclist])
                    else:
                        self.__scraped_data.append([tcaption, doclist])
        else:
            doclist = []
            for doc in soup.select('table.main-content-blk td.right_column div.file-lnk a'):
                result = self.__extract_element(doc)
                if result is not None:
                    doclist.append(result)
            #у одного из фондов информация для владельцев паев выкладывается в другой структуре (заберем ее)
            for doc in soup.select('table.main-content-blk td.right_column div.unit_holders_info-list-item:has(a)'):
                a_tag = doc.find('a')
                href = a_tag['href']
                text = a_tag.string
                date_tag = doc.find('div', class_='item-date')
                if date_tag:
                    date = self.__get_date(date_tag.string)
                else:
                    date = self.__get_date(text)
                doclist.append((text, date, href))

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
        selected_element = soup.select_one('ul.ul_left_menu li span.item_selected')
        if selected_element:
            self.__parse_contents(soup, selected_element.string.strip())
        else:
            self.__parse_contents(soup)

        menu_elements = soup.select('li:has(a.left_menu) a')
        for element in menu_elements:
            response = requests.get(self.__domain + element['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, element.string.strip())
