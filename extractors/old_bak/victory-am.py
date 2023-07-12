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
        
    def __extract_element(self, doc, date_index, prefix):
        a_tag = doc.find('a') 
        if a_tag:
            href = self.__domain + a_tag['href']
            text = a_tag.string
            if len(prefix) > 0:
                text = ' '.join((prefix, text))
            if date_index != -1:
                date = self.__get_date(doc.select('td')[date_index].string)
            else:
                date = self.__get_date(doc.text)
            return (text, date, href)
        else:
            return None

    def __parse_contents(self, soup, caption):
        all_items = soup.select_one('noindex a[rel="nofollow"]')
        if all_items and all_items.string == 'Все':
            response = requests.get(self.__domain + all_items['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, caption)
            return
        tables = soup.select('article.content table.otzchet:has(a)')
        doclist = []
        for table in tables:
            caption_div = table.find_previous_sibling('div', class_='zag_tab')
            if caption_div:
                caption = caption_div.string
            table_headers = [(idth, th.string) for idth, th in enumerate(table.select('th'))]
            date_header_index = -1
            for h in table_headers:
                if re.search('публик', h[1]):
                    date_header_index = h[0]
                    break
            prefix = ''
            for row in table.select('tr:has(td)'):
                if len(row.select('td')) < len(table_headers):
                    prefix = row.td.string
                    if prefix is None:
                        prefix = ''
                else:
                    result = self.__extract_element(row, date_header_index, prefix)
                    if result:
                        doclist.append(result)
            if len(doclist) > 0:
                if self.__scraped_data is None:
                    self.__scraped_data = [] 
                    self.__scraped_data.append([caption, doclist])
                else:
                    self.__scraped_data.append([caption, doclist])
                doclist = []
        l_year = soup.select_one('div.ezh_zag a.l_year')
        if l_year:
            response = requests.get(self.__domain + l_year['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            if re.search('\d{4}$', caption):
                caption = re.sub('\d{4}$', l_year.string, caption)
            else:
                caption = ' '.join((caption, l_year.string))
            self.__parse_contents(soup, caption) 
        for news in soup.select('article.content div.news div.novost'):
            a_tag = [a for a in news.select('a') if 'class' in a.parent.attrs.keys() \
                    and 'extra-wrap' not in a.parent.attrs['class']]
            if len(a_tag) > 0:
                href = self.__domain + a_tag[0]['href']
                text = news.select_one('div.extra-wrap a').string
                date = self.__get_date(news.select_one('time[datetime]').text)
                doclist.append((text, date, href))
            else:
                news_url = self.__domain + news.select_one('div.extra-wrap a')['href']
                news_response = requests.get(news_url, headers=headers, verify=False)
                news_html = news_response.content
                news_soup = BeautifulSoup(news_html, 'html.parser')
                a_tag = news_soup.find('a', href=re.compile('.*\.(pdf|PDF)$'))
                if a_tag and a_tag.find_parent('div', class_='news-detail'):
                    href = a_tag['href']
                    text = a_tag.find_parent('div', class_='news-detail').find('h3').string
                    date = self.__get_date(a_tag.find_parent('div', class_='news-detail').find('span', class_='news-date-time').string)
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
        active_element = soup.select_one('ul.left.menu li.active a')
        if active_element:
            caption = active_element.string
        else:
            caption = 'Раскрытие информации'
        self.__parse_contents(soup, caption)
        for link in soup.select('ul.left.menu li:not(.active) a'):
            response = requests.get(self.__domain + link['href'], headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            caption = link.string
            self.__parse_contents(soup, caption)
