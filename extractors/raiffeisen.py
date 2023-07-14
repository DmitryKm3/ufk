from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

import requests
from urllib3.exceptions import InsecureRequestWarning
import re

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException as TE
from selenium.common.exceptions import NoSuchElementException as NSEE
co = ChromeOptions()

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
localtime = pytz.timezone("Asia/Krasnoyarsk")
fua = UserAgent(verify_ssl=False)
headers = {'User-Agent': fua.random}

class Extractor:
    __scraped_data = None
    __url = None
    __fund = None

    def __init__(self, url):
        self.__url = url 
        s = re.search('filter-(?P<keyvalues>.*)\/$', self.__url)
        if s:
            kvlist = [e.split(',') for e in s['keyvalues'].split('-')]
            kvdict = {k: v for k, v in zip(kvlist[0], kvlist[1])}
            self.__fund = kvdict.get('INFO_FUND', None)

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
        href = self.__domain + doc['href']
        text = doc.text.strip()
        date_p = doc.find('p')
        if date_p:
            date = self.__get_date(date_p.text)
        else:
            date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.select('div.list_files div:not(.more_list) a'):
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
            pif_menu = driver.find_element(By.XPATH, '//*[text()="Паевые инвестиционные фонды"]/../..')
        except NSEE:
            driver.quit()
            return
        menu_elements = [(e.text, e.get_attribute('href')) for e in pif_menu.find_elements(By.XPATH, './/li/a')]
        current_year = datetime.now().year
        for caption, href in menu_elements:
            filter_str = f'-filter-INFO_FUND-{self.__fund}/'
            driver.get(re.sub('\/$', filter_str, href))
            try:
                element_located = EC.visibility_of_element_located((By.XPATH, '//div[contains(@class, "faq__content-files")]'))
                WebDriverWait(driver, 5).until(element_located)
                fund_selector = driver.find_element(By.XPATH, '//select[contains(@data-key, "INFO_FUND")]')
            except (NSEE, TE):
                continue
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
            try:
                year_selector = driver.find_element(By.XPATH, '//select[contains(@data-key, "INFO_YEAR")]')
                for year in range(current_year-1, current_year-3, -1):
                    filter_str = f'-filter-INFO_FUND,INFO_YEAR2-{self.__fund},{year}/'
                    driver.get(re.sub('-filter.*\/$', filter_str, href))
                    element_located = EC.visibility_of_element_located((By.XPATH, '//div[contains(@class,"list_files")]'))
                    WebDriverWait(driver, 5).until(element_located)
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    self.__parse_contents(soup, caption)
            except:
                continue
        driver.quit()
