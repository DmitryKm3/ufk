from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidArgumentException, TimeoutException
import time
import pandas as pd


def start_wd() -> webdriver.Remote:
    """
    s = Service(r'geckodriver.exe')
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.alwaysAsk.force", False)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference(
        "plugin.disable_full_page_plugin_for_types", "application/pdf")
    options.set_preference("pdfjs.disabled", True)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    """
    co = ChromeOptions()
    #browser = webdriver.Remote(service=s, options=options)
    browser = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=co)
    #browser.maximize_window()
    browser.implicitly_wait(10)
    browser.set_page_load_timeout(10)
    return browser


def save_page(path: str, num_page: int, lx_page) -> None:
    with open(path + str(num_page) + 'page.lxml', 'w', encoding='utf-8') as parse_page:
        parse_page.write(lx_page)


def download_lxml(urls: list, lxml_path: str, browser) -> None:
    error_link_list = []
    error_link_index = []
    for url_index, url in enumerate(urls):
        print(url_index, url)
        try:
            browser.get(url)
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body')))
            page = browser.find_element(By.XPATH, '/html/body').get_attribute("innerHTML")
            save_page(lxml_path, url_index, page)
        except TimeoutException:
            error_link_list.append(url)
            error_link_index.append(url_index)
            continue
        except InvalidArgumentException:
            pass
        except Exception as e:
            print(str(e))
            error_link_list.append(url)
            error_link_index.append(url_index)
            continue
        finally:
            print('dfdf')
            #browser.quit()
            #save_page(lxml_path, url_index, page)
    browser.quit()
    data = {'UK_num': error_link_index,
            'URL': error_link_list}
    pd.DataFrame(data).to_excel('inputs/error_link_list.xlsx', index=None)


def download_error_lxml(lxml_path, browser) -> None:  # it's better to recheck urls by hands
    df = pd.read_excel('inputs/error_link_list.xlsx')
    error_link_dict = dict(zip(df['UK_num'].to_list(), df['URL'].to_list()))
    for out_index, url in error_link_dict.items():
        try:
            print(url)
            browser.get(url)
            WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body')))
            time.sleep(1.5)
            page = browser.page_source
            save_page(lxml_path, out_index, page)
        except InvalidArgumentException:
            pass
        except TimeoutException:
            continue
