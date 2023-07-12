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
        #Информация о документах всех фондов располагается 
        #на одной странице
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
        dates = re.search('.*опублик.+?(?P<date>\d{2}.\d{2}.\d{4})', tag)
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
        return (text, date, href)

    def __parse_contents(self, soup):
        caption = 'Раскрытие информации'
        doclist = []
        title = soup.find(lambda tag: tag.name=='span' and \
                            re.search(self.__pif_name, tag.text))
        if title:
            next_title = title.find_next('span', string=re.compile('\d{1,}.*пае.*инвес', re.I))
            link_list = []
            next_element = title.find_next('a', href=re.compile('\/files\/'))
            if next_title:
                while next_element and next_element.sourceline < next_title.sourceline:
                    link_list.append(next_element)
                    next_element = next_element.find_next('a', href=re.compile('\/files\/'))
            else:
                while next_element:
                    link_list.append(next_element)
                    next_element = next_element.find_next('a', href=re.compile('\/files\/'))
            for link in link_list:
                result = self.__extract_element(link)
                if result:
                    doclist.append(result)
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
