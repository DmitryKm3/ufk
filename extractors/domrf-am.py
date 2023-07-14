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
        dates = re.search('(?P<date>\d{2}.\d{2}.\d{4})', tag, flags=re.IGNORECASE)
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
        a_tag = doc.find('a', class_='document__download')
        if a_tag:
            href = '/'.join((self.__domain, a_tag['href']))
            div_tag = doc.find(class_='document__name')
            if div_tag:
                text = div_tag.text.strip()
            else:
                text = 'Наименование документа не указано'
            parent = doc.find_parent('div', class_='report')
            if parent:
                group_div = parent.select_one('div.document:not(:has(a.document__download))')
                suffix = group_div.select_one('p.document__name').string.strip()
                text += f' {suffix}'
                date_div = group_div.find('div', class_='document__published')
                if date_div:
                    date = self.__get_date(date_div.text)
                else:
                    date = self.__get_date(text)
            else:
                date_div = doc.find('div', class_='document__published')
                if date_div:
                    date = self.__get_date(date_div.text)
                else:
                    date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, caption, current_url):
        if soup.select('div.documents__wrapper p.messages__read-more a'):
            driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=co)
            driver.get(current_url)
            try:
                read_more = driver.find_element(By.CSS_SELECTOR, \
                        'div.documents__wrapper p.messages__read-more a')
                while read_more:
                    read_more.click()
                    element_present = EC.presence_of_element_located((By.CSS_SELECTOR, \
                        'div.documents__wrapper p.messages__read-more a'))
                    WebDriverWait(driver, 2).until(element_present)
                    read_more = driver.find_element(By.CSS_SELECTOR, \
                        'div.documents__wrapper p.messages__read-more a')
            except:
                pass
            html = driver.page_source 
            driver.quit()
            soup = BeautifulSoup(html, 'html.parser')
        doclist = []
        for doc in soup.select('section.content-wrap div.document:has(a.document__download)'):
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
        html = driver.page_source
        driver.quit()
        soup = BeautifulSoup(html, 'html.parser')
        for menu_element in soup.select('section.page-body div.page-body__content \
                                        div.inf-sub-list._show a'):
            p_tag = menu_element.select_one('p.inf-sub-list-item__title')
            if p_tag:
                caption = p_tag.string
            else:
                caption = 'Раскрытие информации'
            current_url = '/'.join((self.__domain, menu_element['href']))
            response = requests.get(current_url, headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            if soup.select('section.reporting-banner div.reporting-block__hero-links'):
                active_link = soup.select_one('section.reporting-banner \
                        div.reporting-block__hero-links a.active-link')
                caption_tab = caption + f' {active_link.string}'
                self.__parse_contents(soup, caption_tab, current_url)
                for tab in soup.select('section.reporting-banner \
                    div.reporting-block__hero-links a:not(.active-link)'):
                    current_url = '/'.join((self.__domain, tab['href']))
                    caption_tab = caption + f' {tab.string}'
                    self.__parse_contents(soup, caption_tab, current_url)
            else:
                self.__parse_contents(soup, caption, current_url)

