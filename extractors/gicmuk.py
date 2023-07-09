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
    __kid_url = 'http://www.gicmuk.ru/wealth_management/products/pension/'
    __pif_name = ''

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
        
    def __extract_element(self, doc, date_td_id):
        a_tag = doc.find('a')
        if a_tag is not None:
            href = self.__domain + a_tag['href']
            text = ' '.join([element.string for element in a_tag.contents if isinstance(element, NavigableString)])
            if date_td_id != -1:
                date = self.__get_date(doc.select('td')[date_td_id].text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, caption):
        doclist = []
        for table in soup.select('table.stats:has(a)'):
            table_caption = None
            header = table.parent.find_previous_sibling('h4', class_='slider-head')
            if header:
                table_caption = header.text
            headers = table.select('tr th')
            date_headers = [idth for idth, th in enumerate(headers) if re.search('(раскр|публик)', th.text)]
            if len(date_headers) > 0:
                date_td_id = date_headers[0]
            else:
                date_td_id = -1
            docs = table.select('tr:has(a)')
            for doc in docs:
                result = self.__extract_element(doc, date_td_id)
                if result is not None:
                    doclist.append(result)
            if len(doclist) > 0 and table_caption:
                if self.__scraped_data is None:
                    self.__scraped_data = [] 
                    self.__scraped_data.append([table_caption, doclist])
                else:
                    self.__scraped_data.append([table_caption, doclist])
                doclist = []
        if len(doclist) > 0:
            if self.__scraped_data is None:
                self.__scraped_data = [] 
                self.__scraped_data.append([caption, doclist])
            else:
                self.__scraped_data.append([caption, doclist])

    def __parse_kid(self, soup, pif_name):
        caption = 'Ключевой информационный документ'
        doclist = []
        title = soup.find(lambda tag: tag.name =='h5' and re.search(f'{pif_name}', tag.text))
        if title:
            next_sibling = title.find_next_sibling('div')
            for doc in next_sibling.select('h5:has(a)'):
                a_tag = doc.find('a')
                if a_tag:
                    href = self.__domain + a_tag['href']
                    text = a_tag.text
                    date_string = ' '.join([elem.string for elem in doc.contents if isinstance(elem, NavigableString)])
                    for month in months.keys():
                        date_string = date_string.replace(month, months[month])
                    date = self.__get_date(date_string)
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
        active_element = soup.select_one('aside.left div.submenu li.current a')
        s = re.search('.*\"(?P<pif_name>.*)\".*$', active_element.string)
        self.__pif_name = s['pif_name']
        for element in soup.select('aside.left div.submenu li.current ul li a'):
            caption = element.string
            response = requests.get('/'.join((self.__domain, element['href'])), headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
        response = requests.get(self.__kid_url, headers=headers, verify=False)
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_kid(soup, self.__pif_name)
