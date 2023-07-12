from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from bs4 import NavigableString

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
        dates = re.search('.+?(публ|раскр|обнов|редак).+?(?P<date>\d{2}.\d{2}.\d{4})', tag, flags=re.IGNORECASE)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = dates['date']
            if times is not None:
                if times['time'] and int(times['time'][:2]) < 24 \
                        and int(times['time'][-2:]) < 60:
                    dtstring = dtstring + ' ' + times['time']
                else:
                    dtstring = dtstring + ' 00:00'
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        href = '/'.join((self.__domain, doc['href']))
        text = doc.text
        if doc.parent.name == 'li':
            parent_ul = doc.find_parent('ul')
            if parent_ul:
                h2_tag = parent_ul.find_previous_sibling('h2')
                if h2_tag:
                    text = h2_tag.text
        next_sibling = doc.next_sibling
        default_date = localtime.localize(datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M'))
        if isinstance(next_sibling, NavigableString):
            date = self.__get_date(next_sibling.string)
            if date == default_date:
                date = self.__get_date(text)
        else:
            date = self.__get_date(text)
        return (text, date, href)

    def __extract_page(self, soup):
        doclist = []
        for doc in soup.find_all('a', href=re.compile('\/.+\.\w{3,4}$')):
            result = self.__extract_element(doc)
            if result:
                doclist.append(result)
        return doclist

    def __parse_contents(self, soup):
        caption = 'Раскрытие информации'
        doclist = []
        doclist += self.__extract_page(soup)
        for link in soup.select('a.contentpagetitle, a.blogsection'): 
            response = requests.get(link['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            doclist += self.__extract_page(soup)
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
        header = soup.select_one('div.container div.page-header')
        self.__parse_contents(soup)

