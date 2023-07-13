from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from bs4 import NavigableString

import requests
from urllib3.exceptions import InsecureRequestWarning
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
        dates = re.search('.*публик.+?(?P<date>\d{2}.\d{2}.\d{4})', tag, re.IGNORECASE)
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
        a_tag = doc.select_one('div.card-download-link a')
        if a_tag:
            href = self.__domain + a_tag['href']
            text_div = doc.find('div', class_='card-download-text-title')
            if text_div:
                text = text_div.text.strip()
            else:
                text = 'Имя документа не указано'
            date_div = doc.find('div', class_='card-download-text-info')
            if date_div:
                date = self.__get_date(date_div.text)
            else:
                date = self.__get_date(text_div)
            return (text, date, href)

    def __parse_contents(self, soup):
        doclist = []
        for section in soup.select('section#disclosure-list div.disclosure-list-item.section-container'):
            caption_div = section.find('div', class_='disclosure-list-item-title')
            if caption_div:
                caption = caption_div.string.strip()
            else:
                caption = 'Раскрытие информации'
            for doc in section.select('div.disclosure-list-item-list div.card-download'):
                result = self.__extract_element(doc)
                if result:
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
        try:
            element_visible = EC.visibility_of_element_located((By.XPATH, '//section[@id="disclosure-list"]'))
            WebDriverWait(driver, 10).until(element_visible)
        except TimeoutException:
            driver.quit()
            return
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)
        driver.quit()
