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
    __start_page = None
    __kid_page = 'http://www.capital-am.ru/disclosure/messages'
    __pif_name = ''

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
        dates = re.search('.*публик.+?(?P<date>\d{2}.\d{2}.\d{4})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates:
            dtstring = dates['date']
            if times:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        a_tag = doc.find('a') 
        if a_tag:
            href = a_tag['href']
            text = a_tag.string
            date_div = doc.find(lambda tag: tag.name == 'div' and re.search('публик', tag.text))
            if date_div:
                date = self.__get_date(date_div.text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.select('article div li div.content:has(a)'):
            result = self.__extract_element(doc)
            if result:
                doclist.append(result)      
        if len(doclist) > 0:
            if self.__scraped_data is None:
                self.__scraped_data = [] 
                self.__scraped_data.append([caption, doclist])
            else:
                self.__scraped_data.append([caption, doclist])

    def __parse_kid(self, url):
        doclist = []
        html = self.__fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        for doc in soup.select('article:has(span.ACLink)'):
            text_span = doc.find('span', string=re.compile(f'{self.__pif_name}'))
            if text_span:
                text = text_span.string
                href = url
                date_div = doc.find(lambda tag: tag.name == 'div' and re.search('публик', tag.text))
                if date_div:
                    date = self.__get_date(date_div.text)
                else:
                    date = self.__get_date(text)
                doclist.append((text, date, href))
        next_page = soup.find(lambda tag: tag.name == 'a' and 'Вперед' in tag.text \
                                and re.search('messages\?page', tag.attrs['href']))
        if next_page:
            doclist += self.__parse_kid(self.__domain + next_page['href'])
        return doclist

    #сайт периодически выдает сообщение 'Service unavailable'
    #будем пробовать несколько раз (5
    def __fetch_page(self, url):
        response = requests.get(url, headers=headers, verify=False)
        html = response.content
        retries = 4
        while html == b'Service Unavailable' and retries > 0:
            response = requests.get(url, headers=headers, verify=False)
            html = response.content
            retries -= 1
        self.__start_page = response.url
        if html == b'Service Unavailable':
            s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', url)
            self.__domain = s[0]
            return '' 
        else:
            s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
            self.__domain = s[0]
            return html

    def scrape(self):
        html = self.__fetch_page(self.__url)
        soup = BeautifulSoup(html, 'html.parser')
        href = self.__start_page.replace(self.__domain, '')
        active_element = soup.select_one(f'nav li a[href="{href}"]')
        caption = 'Раскрытие информации'
        if active_element:
            menu = active_element.find_parent('nav')
            self.__pif_name = active_element.find_parent('article').h1.string
            caption = active_element.string
        self.__parse_contents(soup, caption)
        for link in menu.select(f'nav li a:not([href="{href}"])'):
            html = self.__fetch_page(self.__domain + link['href'])
            soup = BeautifulSoup(html, 'html.parser')
            caption = link.string
            self.__parse_contents(soup, caption)
        
        caption = 'Официальные сообщения'
        doclist = self.__parse_kid(self.__kid_page)
        if len(doclist) > 0:
            if self.__scraped_data is None:
                self.__scraped_data = [] 
                self.__scraped_data.append([caption, doclist])
            else:
                self.__scraped_data.append([caption, doclist])

