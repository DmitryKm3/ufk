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
        dates = re.search('(публик|раскрыт).+?(?P<date>\d{2}\.\d{2}\.\d{4})', tag)
        times = re.search('(?P<time>\d{2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates is not None:
            dtstring = dates['date']
            dtlist = dtstring.split('.')
            #грязный хак для грязных данных
            if (dtlist[1] == '02' and dtlist[0] == '29') and int(dtlist[2]) % 4 != 0:
                dtlist[0] = '28'
                dtstring = '.'.join(dtlist)
            if times is not None:
                dtstring = dtstring + ' ' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __parse_contents(self, soup, caption='Раскрытие информации'):
        doclist = []
        links = soup.select('div.content div.c_column *:not(.nav) a')
        external_urls = {}
        total_count = len(links)
        counter = 0
        for link in links:
            counter += 1
            if 'href' in link.attrs.keys():
                if 'ucnu.ru' not in link['href']:
                    if link['href'][:1] != '/':
                        href = '/'.join((self.__domain, link['href']))
                    else:
                        href = self.__domain + link['href']
                else:
                    href = link['href']
                #проверка на внешнюю ссылку (другой раздел раскрытия информации)
                #чтобы не замедлять обработку, проверим только ссылки в подвале (последние 5, например)
                if (total_count - counter) < 5:
                    head = requests.head(href).headers
                    if 'text/html' in head['Content-Type']:
                        url_caption = ' '.join(link.text.split())
                        if url_caption == '':
                            url_caption = 'Раскрытие информации'
                        external_urls[href] = url_caption
                        continue
                text = ' '.join(link.text.split())
                if text == '':
                    text = 'Название документа не указано'
                #сайт сверстан как попало, в итоге иногда строки с информацией находятся вне тегов
                #соберем следующую текстовую строку на всякий случай
                next_sibling = link.next_sibling
                if isinstance(next_sibling, NavigableString):
                    text = ' '.join([text] + next_sibling.split())
                date = self.__get_date(text)
                doclist.append((text, date, href))

        if len(doclist) > 0:
            if self.__scraped_data is None:
                self.__scraped_data = [] 
                self.__scraped_data.append([caption, doclist])
            else:
                self.__scraped_data.append([caption, doclist])
        for url in external_urls.keys():
            response = requests.get(url, headers=headers, verify=False)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            self.__parse_contents(soup, external_urls[url])

    def scrape(self):
        response = requests.get(self.__url, headers=headers, verify=False)
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', response.url)
        self.__domain = s[0]
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        self.__parse_contents(soup)
