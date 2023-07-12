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
        tag = ' '.join(tag.split()).replace('-', ':')
        dates = re.search('(?P<day>\d{2})\.(?P<mon>\d{2})\.(?P<year>\d{4})', tag)
        times = re.search('(?P<hour>\d{2}):(?P<minute>\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = '.'.join((dates['day'], dates['mon'], dates['year']))
            if times and int(times['hour']) < 24 and int(times['minute']) < 60:
                dtstring = dtstring + ' ' + ':'.join((times['hour'], times['minute']))
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))

    def __get_date_text_around(self, doc):
        #сначала ищем вокруг самого тега
        text_after_tag = ' '.join([element.strip() for element \
                    in doc.next_siblings if isinstance(element, NavigableString)])
        if re.search('\d{2}\.\d{2}\.\d{4}', text_after_tag):
            return text_after_tag
        text_before_tag = ' '.join([element.strip() for element \
                    in doc.previous_siblings if isinstance(element, NavigableString)])
        if re.search('\d{2}\.\d{2}\.\d{4}', text_before_tag):
            return text_before_tag
        #потом в соседней ячейке
        parent_td = doc.find_parent('td')
        if parent_td:
            next_td = parent_td.find_next_sibling('td')
            if next_td and re.search('\d{2}\.\d{2}\.\d{4}', next_td.text):
                return next_td.text
        #и в конце попробуем найти в предыдущих 5 параграфах
        parent_p = doc.find_parent('p')
        if parent_p:
            current_p = parent_p
            for i in range(5):
                current_p = current_p.find_previous_sibling('p')
                if current_p and re.search('\d{2}\.\d{2}\.\d{4}', current_p.text):
                    return current_p.text
        return None
        
    def __extract_element(self, doc):
        href = '/'.join((self.__domain, doc['href']))
        text = doc.string.strip()
        date_text = self.__get_date_text_around(doc)
        if date_text:
            date = self.__get_date(date_text)
        else:
            date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.find_all('a', href=re.compile('download.php\?id')):
            if doc.string and doc.string.strip() != '':
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
        for menu_element in soup.select('div.center div.content ul li a'):
            caption = menu_element.string
            response = requests.get(menu_element['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
