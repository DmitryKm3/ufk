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
    __pifcode = None

    def __init__(self, url):
        self.__url = url
        s = re.search('\/(?P<code>\d+).*$', url)
        if s:
            self.__pifcode = s['code']

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
        dates = re.search('.*(размещ|публик).+?(?P<date>\d{2}.\d{2}.\d{4})', tag)
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
        a_tag = doc.find('a')
        href = a_tag['href']
        title_div = a_tag.find('div', {'field': 'title'})
        if title_div:
            text = title_div.text
        else:
            text = 'Наименование документа не указано'
        date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup):
        caption = 'Раскрытие информации'
        first_doc_div = soup.select_one('div[data-record-type="374"]:has(a:has(div.t-text))')
        first_title_div = first_doc_div.find_previous_sibling('div', {'data-record-type': '60'})
        if first_title_div:
            caption = first_title_div.find('div', class_='t-title_xxl').text
        next_sibling = first_title_div.find_next_sibling('div')
        doclist = []
        while 'id' in next_sibling.attrs.keys() and next_sibling['id'] != 't-footer':
            if next_sibling.select_one('a:has(img)'):
                result = self.__extract_element(next_sibling)
                if result:
                    doclist.append(result)
            else:
                if 'data-record-type' in next_sibling.attrs.keys() and next_sibling['data-record-type'] == "60":
                    title_div = next_sibling.select_one('div.t-title_xxl')
                    if title_div:
                        if len(doclist) > 0:
                            if self.__scraped_data is None:
                                self.__scraped_data = [] 
                                self.__scraped_data.append([caption, doclist])
                            else:
                                self.__scraped_data.append([caption, doclist])    
                        caption = title_div.text
                        doclist = []
            next_sibling = next_sibling.find_next_sibling('div')

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
        #отчетность и КИДы
        response = requests.get('/'.join((self.__domain, 'infoopen', self.__pifcode)), headers=headers, verify=False)
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)

