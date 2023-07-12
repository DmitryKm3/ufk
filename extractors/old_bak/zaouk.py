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
    __pif_name = None

    def __init__(self, url):
        #Информация о ключевых информационных документах располагается 
        #общим списком на отдельной странице
        #
        #Для отбора нужных в url страницы фонда необходимо
        #добавить строку в формате <PIFNAME=имя фонда>
        pif_name = re.search('<PIFNAME=(?P<pif_name>.+)>', url)
        if pif_name:
            self.__pif_name = pif_name['pif_name']
            url = url[:pif_name.start()]
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
        times = re.search('.*публик.+?(?P<time>\d{2}[:|-]\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates:
            dtstring = dates['date']
            if times:
                dtstring = dtstring + ' ' + times['time'].replace('-', ':')
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc, kid=False):
        href = doc['href'].lstrip('.')
        if href[:1] != '/':
            href = self.__domain + '/' + href
        else:
            href = self.__domain + href
        text = doc.string
        date = self.__get_date(doc.text)
        if kid and not re.search(self.__pif_name, text):
            return None
        else:
            return (text, date, href)

    def __parse_contents(self, soup, caption='Документы'):
        doclist = []
        for doc in soup.select('table div.txt a'):
            current_element = doc
            str_list = []
            while isinstance(current_element.previous_sibling, NavigableString):
                str_list.append(current_element.previous_sibling.text.strip(',').strip())
                current_element = current_element.previous_sibling
            str_list = str_list[::-1]
            current_element = doc
            while isinstance(current_element.next_sibling, NavigableString):
                str_list.append(current_element.next_sibling.text.strip(',').strip())
                current_element = current_element.next_sibling  
            if doc.string:
                doc.string += ' '.join(str_list)
            else:
                doc.string = ' '.join(str_list)
            if caption == 'Ключевой информационный документ':
                result = self.__extract_element(doc, True)
            else:
                result = self.__extract_element(doc, False)
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
        kid_url = 'http://www.azkapital.ru/?page=du&no=3'
        response = requests.get(kid_url, headers=headers, verify=False)
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup, 'Ключевой информационный документ')
