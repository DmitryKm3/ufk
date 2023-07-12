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
        dates = re.search('.*(публ|размещ|обнов).+?(?P<date>\d{2}.\d{2}.\d{4})', tag, flags=re.IGNORECASE)
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
        text = doc.text
        date = self.__get_date(text)
        default_date = localtime.localize(datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M'))
        if date == default_date:
            next_span = doc.find_next_sibling(lambda tag: tag.name == 'span' \
                and re.search('.*(публ|размещ|обнов).+?(?P<date>\d{2}.\d{2}.\d{4})', 
                tag.text, flags=re.IGNORECASE))
            if next_span:
                date = self.__get_date(next_span.text)
            else:
                previous_sibling = doc.parent.find_previous_sibling()
                if previous_sibling \
                    and previous_sibling.name == 'p' \
                    and re.search('.*(публ|размещ|обнов).+?(?P<date>\d{2}.\d{2}.\d{4})',
                    previous_sibling.text, flags=re.IGNORECASE):
                        date = self.__get_date(previous_sibling.text)
                else:
                    next_sibling = doc.parent.find_next_sibling()
                    if next_sibling \
                        and next_sibling.name == 'p' \
                        and re.search('.*(публ|размещ|обнов).+?(?P<date>\d{2}.\d{2}.\d{4})',
                        next_sibling.text, flags=re.IGNORECASE):
                        date = self.__get_date(next_sibling.text)
        return (text, date, href)

    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.select('main#content a.file[data-entity-type="file"]'):
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
        active_section = soup.select('div#sidebar-first ul.menu li.menu-item--active-trail:has(ul.menu)')
        if active_section:
            for menu_element in active_section[-1].select('ul.menu li.menu-item a'):
                caption = menu_element.string
                response = requests.get(self.__domain + menu_element['href'], headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                self.__parse_contents(soup, caption)
