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
        a_tag = doc.select_one('a')
        if a_tag:
            href = self.__domain + a_tag['href']
            text = a_tag.text 
            date_span = doc.find('span', text=re.compile('\d{2}.\d{2}.\d{4}'))
            if date_span:
                date = self.__get_date(date_span.parent.text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None
    def __extract_table(self, table):
        doclist = []
        for doc in table:
            result = self.__extract_element(doc)
            if result:
                doclist.append(result)
        return doclist

    def __parse_contents(self, soup, caption):
        sections = soup.select('div.past-names')
        for section in sections:
            caption_button = section.select_one('button')
            if caption_button:
                section_caption = caption_button.text.strip()
            else:
                section_caption = caption
            doclist = self.__extract_table(section.select('table.table--files tr'))
            if len(doclist) > 0:
                if self.__scraped_data is None:
                    self.__scraped_data = [] 
                    self.__scraped_data.append([section_caption, doclist])
                else:
                   self.__scraped_data.append([section_caption, doclist])
        if len(sections) == 0:
            doclist = self.__extract_table(soup.select('table.table--files tr'))
            next_page = soup.select_one('div.pagination li.pagination__item a.pagination__link--next')
            while next_page:
                response = requests.get(self.__domain + next_page['href'], headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                doclist += self.__extract_table(soup.select('table.table--files tr'))
                next_page = soup.select_one('div.pagination li.pagination__item a.pagination__link--next')
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
        caption = 'Раскрытие информации'
        self.__parse_contents(soup, caption)
        additional_links = soup.select('section p a')
        for link in soup.select('nav.inner-header__nav li.page-nav__item a'):
            link['href'] = self.__domain + link['href']
            additional_links.append(link)
        for link in additional_links:
            response = requests.get(link['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, link.text)
