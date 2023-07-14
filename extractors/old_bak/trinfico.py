from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

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
utczone = pytz.timezone("UTC")
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
        
    def __extract_element(self, doc):
        href = self.__proto + doc['href']
        text_span = doc.find('span', class_='name')
        if text_span:
            text = text_span.string
        else:
            text = 'Наименование документа не указано'
        date_span = doc.find('span', text=re.compile('Дата раскрытия:'))
        if date_span:
            date = self.__get_date(date_span.text)
        else:
            date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup, caption):
        sections = soup.select('div.subsection')
        if len(sections) > 0:
            for sub in sections:
                doclist = []
                caption = sub.find('h3').string
                for doc in sub.select('div a'):
                    result = self.__extract_element(doc)
                    if result is not None:
                        doclist.append(result)
                if len(doclist) > 0:
                    if self.__scraped_data is None:
                        self.__scraped_data = [] 
                        self.__scraped_data.append([caption, doclist])
                    else:
                        self.__scraped_data.append([caption, doclist])
        else:
            doclist = []
            for doc in soup.select('div.content b-disclosure-product-section div a'):
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
        driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=co)
        driver.get(self.__url)
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', driver.current_url)
        self.__domain = s[0]
        s = re.findall('(https?:).*', driver.current_url)
        self.__proto = s[0]
        try:
            element_present = EC.presence_of_element_located((By.XPATH, '//b-container/div[@class="sections"]/a'))
            WebDriverWait(driver, 10).until(element_present)
        except TimeoutException:
            return ['Timed out', []]
        for element in driver.find_elements(By.XPATH, '//b-container/div[@class="sections"]/a'):
            element.click()
            try:
                element_present = EC.presence_of_element_located((By.XPATH, '//b-disclosure-product-section/div/a'))
                WebDriverWait(driver, 10).until(element_present)
            except TimeoutException:
                pass  
            caption = element.text
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
        driver.quit()
