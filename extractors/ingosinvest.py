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
        
    def __extract_element(self, doc, text=''):
        a_tag = doc.find('a')
        if a_tag:
            href = self.__domain + a_tag['href']
            if text == '':
                text = a_tag.text 
            date_span = doc.find('span', text=re.compile('\d{2}.\d{2}.\d{4}'))
            if date_span:
                date = self.__get_date(date_span.text)
            else:
                date_span = doc.find('span', class_='fileinfo')
                if date_span:
                    date = self.__get_date(date_span.text)
                else:
                    date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup):
        for section in soup.select('li:has(ul.large.list):not(:has(div.tabContent))'):
            doclist = []
            caption_span = section.select_one('a.lineInfo span.nameInfo')
            if caption_span:
                caption = caption_span.text
            else:
                caption = 'Раскрытие информации'
            for doc in section.select('ul.large.list li'):
                result = self.__extract_element(doc)
                if result:
                    doclist.append(result)
            if len(doclist) > 0:
                if self.__scraped_data is None:
                    self.__scraped_data = [] 
                    self.__scraped_data.append([caption, doclist])
                else:
                   self.__scraped_data.append([caption, doclist])
        #отчетность
        doclist = []
        section = soup.select_one('li:has(div.tabContent)')
        caption_span = section.select_one('a.lineInfo span.nameInfo')
        if caption_span:
            caption = caption_span.text
        else:
            caption = 'Раскрытие информации'
        lastref = section.select_one('ul.nav li.last a')
        id_ = lastref['href'].replace('#', '')
        rows = section.select(f'div#{id_} div.tableReporting ul li')
        header = []
        for row in rows:
            divs = row.findAll('div')
            if len(header) == 0:
                for div in divs:
                    header.append(div.text)
            else:
                for i in range(1, len(divs)):
                    if divs[i].text.strip() != '-':
                        text = f'{divs[0].text} ({header[i]})'
                        result = self.__extract_element(divs[i], text)
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
