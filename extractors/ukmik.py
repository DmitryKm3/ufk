from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

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
            if tag.find(mon) > 0:
                tag = tag.replace(mon, months[mon])
                break
        dates = re.search('(?P<date>\d{1,2}.\d{2}.\d{4})', tag)
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
        a_tag = doc.select_one('div.zo-blog-content a')
        if a_tag is not None:
            href = a_tag['href']
            text = a_tag.string
            date_li = doc.select_one('div.zo-blog-meta li.zo-blog-date')
            if date_li:
                date = self.__get_date(date_li.text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __extract_category(self, soup):
        doclist = []
        while soup.select_one('div#content nav.paging-navigation a.next.page-numbers'):
            for doc in soup.select('div#content article:has(a)'):
                result = self.__extract_element(doc)
                if result:
                    doclist.append(result)
            next_page = soup.select_one('div#content nav.paging-navigation a.next.page-numbers')
            response = requests.get(next_page['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
        else:
            for doc in soup.select('div#content article:has(a)'):
                result = self.__extract_element(doc)
                if result:
                    doclist.append(result)
        return doclist

    def __parse_contents(self, soup):
        tabs = soup.select('div.entry-content div.tabs label')
        for tab in tabs:
            caption = tab.string
            doclist = []
            all_docs = soup.select_one(f'div.entry-content div.tabs section#content-{tab["for"]} div.alm-btn-wrap a')
            if all_docs:
                response = requests.get(self.__domain + all_docs['href'], headers=headers, verify=False)
                html = response.content
                sub_soup = BeautifulSoup(html, 'html.parser')
                doclist += self.__extract_category(sub_soup)
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
