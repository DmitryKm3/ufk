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
        startdate = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=localtime) - timedelta(delta)
        output_list = []

        for section in self.__scraped_data:
            section_data = [e for e in section[1] if e[1] >= startdate]
            if len(section_data) > 0:
                output_list.append([section[0], section_data])

        return output_list

    def __get_date(self, tag):
        dates = re.search('(?P<day>\d{2}).(?P<mon>\d{2}).(?P<year>\d{4})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = '.'.join((dates['day'], dates['mon'], dates['year']))
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))

    def __extract_element(self, doc):
        text_title = doc.select_one('span.file__text')
        date_info = doc.select_one('span.file__desc')
        if text_title is not None and date_info is not None:
            text = text_title.string
            date = self.__get_date(date_info.string)
            href = self.__root_url + '/' + doc['href']
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, inner_menu=False):
        sections = soup.select('div.t-Body-main div.container ul.list')
        doclist = []
        caption = 'Раскрытие информации'
        if inner_menu:
            active_elements = soup.select('li.is-current')
            if len(active_elements) > 0:
                inner_active_element = active_elements[-1].select_one('span.t-LinksList-label')
                if inner_active_element is not None:
                    caption = inner_active_element.string #последний вложенный элемент списка

        for section in sections:
            if not inner_menu:
                prev_h2 = section.find_previous_sibling('h2')
                if prev_h2 is not None:
                    caption = prev_h2.string
            for doc in section.select('li a'):
                result = self.__extract_element(doc)
                if result is not None:
                    doclist.append(result)

            if not inner_menu and len(doclist) > 0:
                if self.__scraped_data is None:
                    self.__scraped_data = []
                    self.__scraped_data.append([caption, doclist])
                else:
                    self.__scraped_data.append([caption, doclist])
                doclist = []
        else:
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
        self.__root_url = '/'.join(self.__url.split('/')[:-1])
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)
        menu_elements = soup.select('li.is-current.is-expanded li.is-current ul a')
        for element in menu_elements:
            response = requests.get(self.__root_url + '/' + element['href'], headers=headers, verify=False) 
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, inner_menu=True)
            
