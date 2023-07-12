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
    __pif_code = None

    def __init__(self, url):
        #информация о раскрытии размещается для всех ПИФ в одном разделе без сортировки
        #для фильтрации в системе к адресу страницы добавляем информацию в формате "?PIF=код"
        #код можно посмотреть в имени файла соответствующего ПИФ
        
        #перед разбором страницы отрежем код из url
        pif_code = re.search('\?PIF=(?P<code>\d+)', url)
        if pif_code:
            self.__pif_code = 'PIF' + pif_code['code']
            url = url[:pif_code.start()]
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
        
    def __extract_element(self, doc, pifcode):
        a_tag = doc.find('a', href=re.compile('.*\/' + pifcode +'_.*\.[a-zA-Z]{3,4}'))
        if a_tag:
            s = re.search('https?', a_tag['href'])
            if s:
                href = a_tag['href']
            else:
                href = self.__domain + a_tag['href']
            text = a_tag.string
            date_td = a_tag.parent.find_previous_sibling('td')
            if date_td:
                date = self.__get_date(date_td.string)
            else:
               date = self.__get_date(text)
            return (text, date, href)

    def __extract_page(self, soup, pifcode):
        doclist = []
        for doc in soup.select('div.content div.cont_inside table tr.Zebra3:has(a)'):
            result = self.__extract_element(doc, pifcode)
            if result:
                doclist.append(result)
        if len(doclist) > 0:
            if self.__scraped_data is None:
                self.__scraped_data = [] 
                self.__scraped_data.append(['Раскрытие информации', doclist])
            else:
                self.__scraped_data[0][1] += doclist

    def __parse_contents(self, soup, pifcode):
        self.__extract_page(soup, pifcode)
        pages = soup.select('div.content div.cont_inside p:has(a)')
        next_page = None
        for page in pages:
            a_tags = page.find_all('a', href=re.compile('.*/\?page=.*'))
            for a_tag in a_tags:
                if a_tag.find('span', string='›'):
                    next_page = a_tag
                    break
        if next_page:
            s = re.search('.*(?P<subpage>\?page=.*)', next_page['href'])
            response = requests.get(self.__url + s['subpage'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, pifcode)

    def scrape(self):
        response = requests.get(self.__url, headers=headers, verify=False)
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        self.__domain = s[0]
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup, self.__pif_code)
