from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from bs4 import NavigableString

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
co = ChromeOptions()

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
localtime = pytz.timezone("Asia/Krasnoyarsk")
fua = UserAgent(verify_ssl=False)
headers = {'User-Agent': fua.random}

class Extractor:
    __scraped_data = None
    __url = None
    __pif_id = None

    def __init__(self, url):
        s = re.search('.*#(?P<pif_id>.*)$', url)
        if s:
            self.__pif_id = s['pif_id']
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
        
    def __extract_element(self, doc):
        a_tag = doc.find('a')
        if a_tag:
            href = '/'.join((self.__domain, a_tag['href']))
            text_p = doc.select_one('div.file-title p')
            if text_p:
                text = text_p.string
            else:
                text = 'Наименование документа не указано'
            date_li = doc.select_one('div.file-title ul li')
            if date_li:
                date = self.__get_date(date_li.text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup):
        doclist = {} 
        for doc in soup.select(f'section.content div#{self.__pif_id}.content-block div.content-file'):
            result = self.__extract_element(doc)
            if result:
                caption_h2 = doc.find_previous(lambda tag: tag.name == 'h2' \
                                and 'id' in tag.attrs.keys() \
                                and re.search('fid-.*mid-.*', tag['id']))
                if caption_h2:
                    caption = caption_h2.string
                else:
                    caption = 'Раскрытие информации'
                if doclist.get(caption):
                    doclist[caption].append(result)
                else:
                    doclist[caption] = [result]
        for key in doclist.keys():
            if self.__scraped_data is None:
                self.__scraped_data = [] 
                self.__scraped_data.append([key, doclist[key]])
            else:
                self.__scraped_data.append([key, doclist[key]])

    def scrape(self):
        driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=co)
        driver.get(self.__url)
        element_present = EC.presence_of_element_located((By.XPATH, '//section[@class="content"]'))
        WebDriverWait(driver, 10).until(element_present)
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', driver.current_url)
        self.__domain = s[0]
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        driver.quit()
        self.__parse_contents(soup)
