from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from bs4 import NavigableString

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
        dates = re.search('(?P<day>\d{2})\.(?P<mon>\d{2})\.(?P<year>\d{2,4}).+?г\.', tag, flags=re.IGNORECASE)
        times = re.search('г\..{0,5}(?P<time>\d{2}.\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = '.'.join((dates['day'], dates['mon']))
            if len(dates['year']) < 4:
                dtstring += f'.20{dates["year"]}'
            else:
                dtstring += f'.{dates["year"]}'
            if times is not None:
                dtstring = dtstring + ' ' + times['time'].replace('.', ':')
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        a_tag = doc.find('a')
        href = self.__domain + a_tag['href']
        if doc.name == 'tr':
            tds = doc.select('td')
            text = tds[1].text
            date = self.__get_date(tds[2].text)
        else:
            text = a_tag.text
            default_date = localtime.localize(datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M'))
            date_string = ' '.join([e.string for e in doc.contents \
                                    if isinstance(e, NavigableString)])
            date = self.__get_date(date_string)
            if date == default_date:
                date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup, caption):
        doclist = []
        #таблица - страница "Отчетность"
        for doc in soup.select('div.page div.article-box table tr:has(a)'):
            result = self.__extract_element(doc)
            if result:
                doclist.append(result)
        #список - страница "Документы"
        for doc in soup.select('div.page div.article-box ul li:has(a)'):
            result = self.__extract_element(doc)
            if result:
                doclist.append(result)
        #параграф - страница "Архив"
        for doc in soup.select('div.page div.article-box p:has(a)'):
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
        for menu_element in soup.select('div.page div.about-box a.item-file'):
            caption = menu_element.find('div', class_='file-title').string
            response = requests.get(self.__domain + \
                    menu_element['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
