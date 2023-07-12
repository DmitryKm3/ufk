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
            ' янв ': '.01.',
            ' февраля ': '.02.',
            ' фев ': '.02.',
            ' марта ': '.03.',
            ' мар ': '.03.',
            ' апреля ': '.04.',
            ' апр ': '.04.',
            ' мая ': '.05.',
            ' июня ': '.06.',
            ' июн ': '.06.',
            ' июля ': '.07.',
            ' июл ': '.07.',
            ' августа ': '.08.',
            ' авг ': '.08.',
            ' сентября ': '.09.',
            ' сен ': '.09.',
            ' октября ': '.10.',
            ' окт ': '.10.',
            ' ноября ': '.11.',
            ' ноя ': '.11.',
            ' декабря ': '.12.',
            ' дек ': '.12.',
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
        dates = re.search('(?P<date>\d{2}.\d{2}.\d{4})', tag, 
                flags=re.IGNORECASE)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates:
            dtstring = dates['date']
            if times:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        else:
            dates = re.search('(?P<day>\d{2}).(?P<mon>\d{2}).(?P<year>\d{2})',
                    tag, flags=re.IGNORECASE)
            if dates:
                dtstring = '.'.join((dates['day'], dates['mon'], 
                            '20'+dates['year']))
                if times:
                    dtstring = dtstring + ' ' + times['time']
                else:
                    dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        a_tag = doc.find('a')
        if a_tag:
            href = a_tag['href'].replace('../..', '..').replace('..', self.__domain)
            if self.__domain not in href:
                href = self.__domain + href
            text = a_tag.text
            date_element = doc.select_one('.views-field-created')
            if date_element:
                date = self.__get_date(date_element.text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.select('.views-row:has(span.field-content:has(a))'):
            result = self.__extract_element(doc)
            if result:
                doclist.append(result)
        if len(doclist) > 0:
            if self.__scraped_data is None:
                self.__scraped_data = [] 
                self.__scraped_data.append([caption, doclist])
            else:
                self.__scraped_data.append([caption, doclist])
        if re.search('документ.*ПИФ', caption, flags=re.IGNORECASE):
            for menu_element in soup.select('div#main \
                    div.center_menu li.leaf:not(.active-trail) a'):
                response = requests.get(self.__domain + '/' +
                    menu_element['href'], headers=headers, verify=False)
                html = response.content
                inner_soup = BeautifulSoup(html, 'html.parser')
                self.__parse_contents(inner_soup, menu_element.string)

    def scrape(self):
        response = requests.get(self.__url, headers=headers, verify=False)
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        self.__domain = s[0]
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        for menu_element in soup.select('div#main div.center_menu li.leaf a'):
            caption = menu_element.string
            response = requests.get(self.__domain + '/' +
                            menu_element['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
