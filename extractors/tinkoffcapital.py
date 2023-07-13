from datetime import datetime, timezone, timedelta
import pytz
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from bs4 import NavigableString

import requests
from urllib3.exceptions import InsecureRequestWarning
import re

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
co = ChromeOptions()

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
localtime = pytz.timezone("Asia/Krasnoyarsk")
fua = UserAgent(verify_ssl=False)
headers = {'User-Agent': fua.random}

class Extractor:
    __scraped_data = None
    __url = None
    __pif_name = None

    def __init__(self, url):
    # Информация о ключевых информационных документах располагается 
    # общим списком на отдельной странице
    #
    # Для отбора нужных в url страницы фонда необходимо
    # добавить строку в формате <PIFNAME=имя фонда>
        pif_name = re.search('<PIFNAME=(?P<pif_name>.+)>', url)
        if pif_name:
            self.__pif_name = pif_name['pif_name']
            url = url[:pif_name.start()]
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
        dates = re.search('.*(доступ|публик).+?(?P<date>\d{2}.\d{2}.\d{4})', tag, re.IGNORECASE)
        times = re.search(' (?P<time>\d{1,2}:\d{2})', tag)
        dtstring = '01.01.1970 00:00'
        if dates:
            dtstring = dates['date']
            if times:
                if len(times['time']) == 5:
                    dtstring = dtstring + ' ' + times['time']
                else:
                    dtstring = dtstring + ' 0' + times['time']
            else:
                dtstring = dtstring + ' 00:00'
        return localtime.localize(datetime.strptime(dtstring, '%d.%m.%Y %H:%M'))
        
    def __extract_element(self, doc):
        href = doc['href']
        text = doc.text
        date_div = doc.find_next_sibling('div')
        date = self.__get_date(date_div.text)
        if date == localtime.localize(datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M')):
            date = self.__get_date(text)
        return (text, date, href)

    def __parse_contents(self, soup, caption):
        doclist = []
        for doc in soup.select('div[data-qa-type="uikit/container"] a[data-qa-type="uikit/link"]'):
            result = self.__extract_element(doc)
            if result:
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
        s = re.findall('(https?://[A-Za-z_0-9.-]+)/.*', driver.current_url)
        self.__domain = s[0]
        try:
            elements_visible = EC.visibility_of_all_elements_located((By.XPATH, '//div[@data-qa-type="uikit/container"]/*'))
            WebDriverWait(driver, 10).until(elements_visible)
        except TimeoutException:
            driver.quit()
            return
        try:
            header = driver.find_element(By.XPATH, f'//header[contains(text(),"{self.__pif_name}")]')
            header.click()
            xpath_selector = '//button[@data-qa-type="uikit/clickable" \
                        and not(.//span[@data-qa-type="uikit/icon"])]'
            menu = driver.find_elements(By.XPATH, xpath_selector)
            for button in menu:
                caption = button.text
                try:
                    button.click()
                except StaleElementReferenceException:
                    button_selector = f'//button[@data-qa-type="uikit/clickable" and (.//span/div[contains(text(),"{button.text}")])]'
                    driver.find_element(By.XPATH, button_selector).click()
                elements_visible = EC.visibility_of_all_elements_located((By.XPATH, '//div[@data-qa-type="uikit/container"]/*'))
                WebDriverWait(driver, 10).until(elements_visible)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                self.__parse_contents(soup, caption)
        except Exception as e:
            print(e)
            driver.quit()
            return
        driver.quit()
