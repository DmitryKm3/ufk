#!/home/ufk/ufk_venv/bin/python
import pandas as pd
from bs4 import BeautifulSoup as bs
from process_soup import form_raw_list_rss
from correct_links import correct_site_link, full_download_link
from settings import *
from download_manager import start_wd, download_lxml, download_error_lxml
from data_post_processing import yes_no_result, correct_publication_dates


if __name__ == "__main__":
    download_mode = 1
    df = pd.read_excel('inputs/list_managementcompanies.xlsx')
    #df = pd.read_excel('inputs/purcb_list.xlsx')

    #small_correction = df.index[df['Ссылка на РСС'].str.contains("profit-garant.ru/")].to_list()[0]  # dynamic link
    #df.loc[small_correction, 'Ссылка на РСС'] = df.loc[small_correction, 'Ссылка на РСС'] + REPORT_DATE[4]
    small_correction = df.index[df['Ссылка на РСС'].str.contains("profit-garant.ru/")].to_list()  # dynamic link
    if small_correction:
        df.loc[small_correction[0], 'Ссылка на РСС'] = df.loc[small_correction[0], 'Ссылка на РСС'] + REPORT_DATE[4]

    exceptions = df['Exceptions'].to_list()
    site_links = correct_site_link(df['Страница в сети Internet'].to_list())

    if download_mode == 1:
        download_lxml(df['Ссылка на РСС'], LXML_PATH, browser=start_wd())
        download_error_lxml(LXML_PATH, browser=start_wd())
    download_link_list = []  # lists for filling
    publication_list = []
    bool_publication_on_report_date = []
    for i in range(len(df.index)):
        print(f'lxml index {i}')
        try:
            try:
                with open(LXML_PATH + str(i) + 'page.lxml', 'r', encoding='utf-8') as f:
                    page = f.read()
            except UnicodeDecodeError:
                with open(LXML_PATH + str(i) + 'page.lxml', 'r', encoding='cp1251') as f:
                    page = f.read()
            soup = bs(page.lower(), 'lxml')
            soup_up = bs(page, 'lxml')
            print(f'EXCEPTION FOR LMXL {exceptions[i]}')
            pub_str, href_str = form_raw_list_rss(soup, soup_up, exceptions[i])
            link = full_download_link(href_str, i, site_links)
        except FileNotFoundError:
            pub_str = '-'
            link = '-'
        finally:
            download_link_list.append(link)
            publication_list.append(pub_str)
    #df = df.drop(['ОГРН', 'Номер лицензии', 'Дата предоставления (начала действия) лицензии', 'Срок действия лицензии',
    #              'Адрес юридического лица', 'Телефоны', 'Полное (фирменное) наименование' \
    #                ' управляющей компании инвестиционных фондов, паевых инвестиционных фондов и негосударственных '
    #                                                     'пенсионных фондов'], axis=1)
    df = df.drop(['ОГРН', 'Адрес юридического лица', 'Телефоны'], axis=1)
    df[f'Раскрыто на {REPORT_DATE}'] = yes_no_result(download_link_list, bool_publication_on_report_date)
    df['Дата раскрытия'] = correct_publication_dates(publication_list)
    df['Ссылка на скачивание'] = download_link_list
    df.to_excel('results/result_floor7_' + REPORT_DATE + '_lxml.xlsx')
