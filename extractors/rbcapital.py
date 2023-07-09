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
fua = UserAgent(verify_ssl=False)
headers = {'User-Agent': fua.random}

months = { 'января': '01',
            'февраля': '02',
            'марта': '03',
            'апреля': '04',
            'мая': '05',
            'июня': '06',
            'июля': '07',
            'августа': '08',
            'сентября': '09',
            'октября': '10',
            'ноября': '11',
            'декабря': '12',
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
        tag_string = tag
        for key in months.keys():
            if key in tag:
                tag_string = tag.replace(f' {key} ', f'.{months[key]}.')
        dates = re.search('(?P<date>\d{2}.\d{2}.\d{4})', tag_string)
        times = re.search('(?P<time>\d{2}:\d{2})', tag_string)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = dates['date']
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        text_title = doc.select_one('span.DocumentLink__nameOriginal')
        date_info = doc.select_one('div.DocumentLink__info_detail')
        a_tag = doc.select_one('a')
        if text_title is not None and date_info is not None and a_tag is not None:
            text = text_title.string
            date = self.__get_date(date_info.string)
            href = a_tag['href']
            return (text, date, href)
        else:
            return None


    def __parse_contents(self, soup):
        sections = soup.select('div.Step_tab:has(div.slidedown)')
        for section in sections:
            doclist = []
            title = section.select_one('p.Step__title')
            if title is not None:
                caption = title.string
            else:
                caption = 'Раскрытие информации'
            docs = section.select('div.Step__bodyContent li.DocumentsList__item:has(a)')
            for doc in docs:
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

        collapsed_sections_ids = [e.get_attribute('id') for e in driver.find_elements(By.XPATH, \
                                            '//div[contains(@class,"ComponentKit__section") and \
                                            not(./div[contains(@class,"AdditionalLinks")])]')]
        for id in collapsed_sections_ids:
            try:
                clickable_element = EC.element_to_be_clickable((By.ID, id))
                WebDriverWait(driver, 30).until(clickable_element)
                driver.find_element(By.ID, id).click()
            except:
                continue
            try:
                slidedown_present = EC.presence_of_element_located((By.CSS_SELECTOR, f'div#{id} div.slidedown'))
                WebDriverWait(driver, 30).until(slidedown_present)
            except:
                driver.find_element(By.ID, id).click()

        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', driver.current_url)
        self.__domain = s[0]
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)
        driver.quit()
