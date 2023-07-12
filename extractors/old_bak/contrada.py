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
        if dates:
            dtstring = dates['date']
            if times:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc, current_url):
        rows = doc.select('tr')
        a_tag = rows[1].find('a', string=lambda s: s is not None)
        if a_tag:
            if a_tag.get('target', None) and a_tag['target'] == '_blank':
                href = self.__domain + a_tag['href']
                text = a_tag.string
                date_div = rows[0].find('div', class_='text')
                if date_div:
                    date = self.__get_date(date_div.text)
                else:
                    date = self.__get_date(text)
                return [(text, date, href)]
            else:
                response = requests.get(current_url + a_tag['href'], headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                text_h = soup.select_one('h1#title')
                if text_h:
                    doclist = []
                    date_div = text_h.parent.find('div', class_='text')
                    for link in text_h.parent.select('p a'):
                        text = ' '.join((text_h.text, link.text))
                        href = self.__domain + link['href']
                        date = self.__get_date(date_div.text)
                        doclist.append((text, date, href))
                    if len(doclist) > 0:
                        return doclist
                    else:
                        return None
        else:
            return None

    def __parse_contents(self, soup, current_url, caption='Раскрытие информации'):
        doclist = []
        for doc in soup.select('div.list6:has(a)'):
            result = self.__extract_element(doc, current_url)
            if result:
                doclist += result
        left_arrow = soup.find('img', src='/common/pif/img/but/n-n-a.gif')
        if left_arrow and left_arrow.parent.name == 'a':
            response = requests.get(self.__domain + left_arrow.parent['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            for doc in soup.select('div.list6:has(a)'):
                result = self.__extract_element(doc, current_url)
                if result:
                    doclist += result
        else:
            nav_links = soup.select('div.nav.noprint a')
            for link in nav_links:
                response = requests.get(self.__domain + link['href'], headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                for doc in soup.select('div.list6:has(a)'):
                    result = self.__extract_element(doc, current_url)
                    if result:
                        doclist += result
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
            element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.dTreeNodeSel'))
            WebDriverWait(driver, 30).until(element_present)
            html = driver.page_source
        except:
            driver.refresh()           
        html = driver.page_source
        driver.quit()
        soup = BeautifulSoup(html, 'html.parser')
        active_element = soup.select_one('div.dtree div.dTreeNodeSel')
        if active_element:
            for link in active_element.parent.select('div a'):
                response = requests.get(self.__domain + link['href'], headers=headers, verify=False)
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                caption = ' '.join([t.text for t in link.contents if t.text != ''])
                self.__parse_contents(soup, response.url, caption)
