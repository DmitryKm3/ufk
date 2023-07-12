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

    def __init__(self, url):
        self.__url = url 

    def get_data(self, delta = 30):
        startdate = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=localtime) - timedelta(delta)
        output_list = []

        for section in self.__scraped_data:
            section_data = [e for e in section[1] if e[1] >= startdate]
            if len(section_data) > 0:
                output_list.append([section[0], section_data])

        return output_list

    def __get_date(self, tag):
        dates = re.search('(?P<day>\d{2}).(?P<mon>\d{2}).(?P<year>\d{4})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = '.'.join((dates['day'], dates['mon'], dates['year']))
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
    
    def __extract_page(self, soup):
        doclist = []
        tables = soup.select('div#content table:has(a)')
        for table in tables:
            doclist += self.__extract_table(table)
        return doclist

    def __extract_table(self, table):
        doclist = []
        links_count_in_rows = [len(row.select('a')) for row in table.select('tr:has(a)')]
        table_headers = [th.string.replace('*','').strip() for th in table.select('tr th')]
        if min(links_count_in_rows) > 1:
        #Таблица годовой отчетности
            year = ''
            for row in table.select('tr:has(a)'):
                for idtd, td in enumerate(row.select('td')):
                    if idtd == 0:
                        year = td.string
                    a_tag = td.find('a')
                    if a_tag is not None:
                        text = f'Отчетность за {table_headers[idtd]} {year} года'
                        date = self.__get_date(td.text)
                        href = self.__domain + a_tag['href']
                        doclist.append((text, date, href))
        else:
            if len(table_headers) == 2:
            #КИД
                for row in table.select('tr:has(a)'):
                    cells = row.select('td')
                    text = f'{table_headers[1]} {cells[1].text}'
                    date = self.__get_date(cells[0].string)
                    a_tag = cells[1].find('a')
                    if a_tag is not None:
                        href = self.__domain + a_tag['href']
                        doclist.append((text, date, href))
            else:
                for row in table.select('tr:has(a)'):
                    cells = row.select('td')
                    text = cells[0].string
                    date_td = row.find('td', text=re.compile('\d{2}:\d{2}'))
                    if date_td is not None:
                        date = self.__get_date(date_td.string)
                    else:
                        date = self.__get_date('')
                    a_tag = row.select_one('a')
                    if a_tag is not None:
                        href = self.__domain + a_tag['href']
                        doclist.append((text, date, href))
        return doclist

    def __parse_contents(self, soup):
        tables = soup.select('div#content table:has(a)')
        if len(tables) > 0:
            doclist = []
            caption = 'Раскрытие информации'
            h2_tag = tables[0].find_previous_sibling('h2')
            if h2_tag is not None:
                caption = h2_tag.string
            doclist += self.__extract_page(soup)
            year_menu = soup.select('div#content ul.menu#found li:not(.active) a')
            for year in year_menu:
                url = self.__domain + year['href']
                response = requests.get(url, headers=headers, verify=False)
                html = response.content
                inner_soup = BeautifulSoup(html, 'html.parser')
                doclist += self.__extract_page(inner_soup)
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
        self.__root_url = '/'.join(self.__url.split('/')[:-1])
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)
        #пункты меню "Раскрытие информации" за исключением раздела новостей
        menu_elements = [e for e in soup.select('div#list a') if 'news' not in e['href']]
        for element in menu_elements:
            response = requests.get(self.__domain + element['href'], headers=headers, verify=False) 
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup)
