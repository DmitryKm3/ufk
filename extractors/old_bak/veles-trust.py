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
        dates = re.search('(?P<date>\d{2}) (?P<mon>'+ '|'.join(months.keys()) +') (?P<year>\d{2})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = '.'.join([dates['date'], months[dates['mon']], '20' + dates['year']])
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __parse_contents(self, soup):
        content = soup.select_one('div#content div.collapsible:has(div.coll-title)')
        caption = 'Раскрытие информации' 
        doclist = []
        for element in content.children:
            if element.name == 'div' and 'coll-title' in element.attrs['class']:
                if len(doclist) > 0:
                    if self.__scraped_data is None:
                        self.__scraped_data = [] 
                        self.__scraped_data.append([caption, doclist])
                    else:
                        self.__scraped_data.append([caption, doclist])
                title = element.find('h2')
                if title is not None:
                    caption = title.string
                doclist = []
            else:
                if element.name == 'p' and element.find('a') is not None:
                    a_tag = element.find('a')
                    href = self.__domain + a_tag['href']
                    text_span = a_tag.find('span')
                    text = text_span.string.strip()
                    date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=localtime) 
                    doclist.append((text, date, href))
                elif element.name == 'div' and 'coll-content' in element.attrs['class']:
                    ps = element.select('p.doc-upload-date')
                    for p in ps:
                        date = self.__get_date(p.string)
                        a_tag = p.find_next_sibling('a')
                        if a_tag is not None:
                            href = self.__domain + a_tag['href']
                            text_span = a_tag.find('span')
                            text = text_span.string.strip()
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
        self.__parse_contents(soup)
