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
        dates = re.search('(?P<date>\d{2}.\d{2}.\d{4})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = dates['date']
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.select('div.main-content div.content-block-body \
                        div.news-list div.news-item div.news-title a'):
            title = doc.string
            response = requests.get(self.__domain + doc['href'], 
                                    headers=headers, verify=False)
            html = response.content
            doc_soup = BeautifulSoup(html, 'html.parser')
            for file_ in doc_soup.select('div.content-block-body \
                                            div.news-detail a'):
                href = self.__domain + file_['href']
                text = title + f' ({file_.string})'
                date_span = file_.find_previous('span', 
                                class_='news-date-time')
                if date_span:
                    date = self.__get_date(date_span.string)
                else:
                    date = self.__get_date(text)
                doclist.append((text, date, href))
        for section in soup.select('div.main-content div.content-block-body \
                        div.catalog-section-list ul.second-level li a'):
            response = requests.get(self.__domain + section['href'], 
                                    headers=headers, verify=False)
            html = response.content
            section_soup = BeautifulSoup(html, 'html.parser')
            for date_row in section_soup.select('table.company-reports tr.report-item'):
                tds = date_row.select('td')
                a_tag = date_row.find('a')
                if a_tag:
                    title_date = f' на {a_tag.string}'
                    pub_date = self.__get_date(tds[1].string)
                    response = requests.get(self.__domain + a_tag['href'],  
                                    headers=headers, verify=False)
                    html = response.content
                    date_soup = BeautifulSoup(html, 'html.parser')
                    for doc in date_soup.select('div.content-block-body \
                            ul.report-detail li a'):
                        href = self.__domain + doc['href']
                        date = pub_date
                        text = re.sub('\.\w{3,4}$', title_date, doc.text)
                        doclist.append((text, date, href))
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
        top_level_menu = soup.select_one('div.sidebar ul.left-menu li.parent')
        if top_level_menu:
            inner_menu = top_level_menu.find_next_sibling('ul')
            for menu_element in inner_menu.select('li a'):
                caption = menu_element.string
                response = requests.get(self.__domain + menu_element['href'], 
                                        headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                self.__parse_contents(soup, caption)
