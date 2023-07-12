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
months = {  ' января ': '.01.',
            ' февраля ': '.02.',
            ' марта ': '.03.',
            ' апреля ': '.04.',
            ' мая ': '.05.',
            ' июня ': '.06.',
            ' июля ': '.07.',
            ' августа ': '.08.',
            ' сентября ': '.09.',
            ' октября ': '.10.',
            ' ноября ': '.11.',
            ' декабря ': '.12.',
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
        for mon in months.keys(): 
            tag = re.sub(mon, months[mon], tag, flags=re.IGNORECASE)
        dates = re.search('(?P<date>\d{2}.\d{2}.\d{4})', tag, flags=re.IGNORECASE)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = dates['date']
            if len(dtstring) < 10:
                dtstring = '0' + dtstring
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        tds = doc.select('td')
        doc_td = [(idtd, tag) for idtd, tag in enumerate(tds) if tag.select('a[href]')]
        if len(doc_td) > 0:
            for a_tag in doc_td[0][1].find_all('a'):
                prefix = isinstance(a_tag.previous_sibling, NavigableString)
                href = '/'.join((self.__domain, a_tag['href']))
                text = a_tag.string
                date_td = None
                if prefix:
                    text += f' {a_tag.previous_sibling.string}'
                if doc_td[0][0] > 0:
                    date_td = tds[doc_td[0][0] - 1]
                elif doc_td[0][0] == 0 and len(tds) > 1:
                    date_td = tds[doc_td[0][0] + 1]
                if date_td:
                    date = self.__get_date(date_td.string)
                    return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.select('table#table1 table:not(:has(table)) tr:has(a)'):
            result = self.__extract_element(doc)
            if result is not None:
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
        active_element = soup.select_one('div.buttons div.button:not(:has(a))')
        cur_level = 0
        if active_element:
            cur_level = len([s for s in soup.select_one('div.buttons \
                            div.button:not(:has(a))').string if s==u'\xa0'])
            caption = active_element.string.strip()
            self.__parse_contents(soup, caption)
        for menu_element in soup.select('div.buttons div.button:has(a)'):
            if len([s for s in menu_element.text if s==u'\xa0']) > cur_level:
                caption = menu_element.text.strip()
                response = requests.get('/'.join((self.__domain,
                            menu_element.a['href'])), headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                self.__parse_contents(soup, caption)
