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
        dates = re.search('(?P<date>\d{2}.\d{2}.\d{4})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.0001 00:00'
        if dates is not None:
            dtstring = dates['date']
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        

    def __parse_contents(self, soup):
        divs = soup.find_all('div', class_ = lambda x: x in ['QuarterData', 'YearData', 'DocsData'])
        for div in divs:
            doclist = []
            if 'class' in div.attrs.keys() and 'RepYear' not in div.attrs['class']:
                if 'QuarterData' in div.attrs['class']:
                    yearclass = next((s for s in div.attrs['class'] if 'Datayear' in s), None)
                    if yearclass is not None:
                        caption = f'Квартальная отчетность за {yearclass[-4:]} год'
                    else:
                        caption = 'Квартальная отчетность'
                    qdivs = div.findChildren('div', recursive=False)
                    for qdiv in qdivs:
                        a_tag = qdiv.select_one('a')
                        if a_tag is not None:
                            href = self.__domain + a_tag['href']
                            text = qdiv.select_one('div').string
                            date = self.__get_date(qdiv.text)
                            doclist.append((text, date, href))
                else:
                    caption = div.select_one('h4.block-title').string
                    rows = div.select('table tr:has(a)')
                    for row in rows:
                        a_tag = row.select_one('a')
                        if a_tag is not None:
                            href = self.__domain + a_tag['href']
                            text = row.select_one('td').string
                            date = self.__get_date(row.text)
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
        self.__parse_contents(soup)
