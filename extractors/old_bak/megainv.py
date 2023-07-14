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
        dates = re.search('.*публик.+?(?P<date>\d{2}.\d{2}.\d{4})', tag)
        dtstring = '01.01.1970 00:00'
        if dates:
            dtstring = dates['date'].replace(':', '.')
            times = re.search(f'{dtstring}.+(?P<time>\d{2}:\d{2})', tag)
            if times:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        if 'http' in doc['href']:
            href = doc['href']
        else:
            if doc['href'][0] == '/':
                href = self.__domain + doc['href']
            else:
                href = self.__domain + '/' + doc['href']
        if doc.text.strip() != '':
            text = doc.text.strip()
            date_text = doc.find_next(string=re.compile('публик'))
            if date_text:
                date = self.__get_date(date_text.string)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, caption):
        doclist = []
        content = soup.select_one('table#main td#center')
        for doc in content.find_all('a'):
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
        current_link = response.url.replace(self.__domain + '/', '')
        active_element = soup.find('a', href=current_link)
        if active_element:
            caption = active_element.string
        else:
            caption = 'Раскрытие информации'
        self.__parse_contents(soup, caption)
        for link in active_element.parent.find_all('a', href=lambda h: h != current_link):
            if 'http' not in link['href']:
                response = requests.get('/'.join((self.__domain, link['href'].replace('&amp;', '&'))), \
                                        headers=headers, verify=False)
            else:
                response = requests.get(link['href'].replace('&amp;', '&'), headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            caption = link.string
            self.__parse_contents(soup, caption)
