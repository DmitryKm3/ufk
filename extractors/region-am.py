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
        if dates is not None:
            dtstring = dates['date']
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc, date_id):
        a_tag = doc.find('a')
        if a_tag:
            tds = doc.select('td')
            href = self.__domain + a_tag['href']
            text = ' '.join([text.strip() for text in tds[0].contents \
                        if isinstance(text, NavigableString) and text.strip() != ''])
            if date_id != -1:
                date = self.__get_date(tds[date_id].text)
            else:
                date = self.__get_date(text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup):
        sections = soup.select('div.ionTabs__item:has(div.rem-table:has(td.td_doc))')
        for section in sections:
            doclist = []
            caption = 'Раскрытие информации'
            menu_id = section.attrs['data-name']
            menu_element = soup.find('div', {'data-target': menu_id})
            if menu_element:
                caption = ' '.join(menu_element.text.split())
            for table in section.select('div.rem-table:has(td.td_doc)'):
                date_id = -1
                table_headers = table.select('tr.first-row-orange td')
                date_column = [(idtd, tag.string) for idtd, tag in enumerate(table_headers) \
                                        if re.match('дат.*раскр', tag.string, re.IGNORECASE)]
                if len(date_column) > 0:
                    date_id = date_column[0][0]
                for row in table.select('tr:has(td.td_doc)'):
                    result = self.__extract_element(row, date_id)
                    if result is not None:
                        doclist.append(result)
                if len(doclist) > 0:
                    tab_caption = None
                    accordion = table.find_parent('div', class_='accordion__toggle')
                    if accordion:
                        tab_caption = caption
                        caption = accordion.find('div', class_='accordion__head').text
                    else:
                        parent = table.find_parent('div', class_='rem-content')
                        if parent and parent.previous_sibling.name == 'h2':
                            tab_caption = caption
                            caption = parent.previous_sibling.string
                    if self.__scraped_data is None:
                        self.__scraped_data = [] 
                        self.__scraped_data.append([caption, doclist])
                    else:
                        self.__scraped_data.append([caption, doclist])
                    if tab_caption:
                        tab_caption, caption = None, tab_caption
                    doclist = []

                    
    def scrape(self):
        response = requests.get(self.__url, headers=headers, verify=False)
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        self.__domain = s[0]
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)
