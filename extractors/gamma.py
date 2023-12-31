from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

import requests
from urllib3.exceptions import InsecureRequestWarning
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
        

    def __parse_contents(self, soup):
        headers = soup.find_all(["h1","h2","h3", "h4", "h5", "h6"])
        for header in headers:
            if header.text != "":
                caption = header.text.strip(':')
                doclist = []
                sibling = header.find_next_sibling()
                while sibling is not None:
                    if sibling.name == "p" and sibling.find('a') is not None:
                        a_tag = sibling.find('a')
                        href = self.__domain + a_tag['href']
                        text = a_tag.text
                        sibling = sibling.find_next_sibling()
                        if sibling.name == "p":
                            date = self.__get_date(sibling.text) 
                            doclist.append((text, date, href))
                    elif sibling.name in ["h1","h2","h3", "h4", "h5", "h6"]:
                        break
                    sibling = sibling.find_next_sibling()
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
