import re
from get_publication_dates_from_lxml import date_of_pub_parents
from get_download_link import str_download_link
import traceback
from settings import *


def form_raw_list_rss(soup, soup_up, xl_exception):
    temp_list = []
    href_str = '-'
    pub_str = '-'
    if xl_exception == '-':
        for element in patterns:
            temp_list.append(soup_up.find_all(text=re.compile(element, re.I)))
        flat = [x.replace('\n', ' ').strip() for xs in temp_list for x in xs]
        temp_str = '\n'.join(flat)
        if temp_str == '':
            flat = ['-']
        for i in flat.copy():
            if len(i) > 400:
                flat.remove(i)
        href_str = str_download_link(flat, soup_up)
        pub_str = date_of_pub_parents(flat, soup)
    elif xl_exception == 'OnlyRSSByDate':
        flat = soup_up.find_all(text=re.compile(REPORT_DATE))
        href_str = str_download_link(flat, soup_up)
        pub_str = date_of_pub_parents(flat, soup)
    elif xl_exception == 'IncorYear':
        temp_str = '\n'.join(soup_up.find_all(text=re.compile(REPORT_DATE[0:-3] + REPORT_DATE[-1])))
        if temp_str == '':
            temp_str = '\n'.join(soup_up.find_all(text=re.compile(REPORT_DATE[0:-3] \
                                                                  .replace(".", "") + REPORT_DATE[-1].replace(".",
                                                                                                              "")))).replace(
                "\n", "").replace("\t", "").replace(" ", "")
            flat = [re.sub("(\().*?\)", "", temp_str)]
            try:
                href_str = soup.find(text=re.compile(temp_str, re.I)).parent['href']
            except:
                traceback.print_exc()
            pub_str = date_of_pub_parents(flat, soup)
        else:
            flat = [re.sub("(\().*?\)", "", temp_str)]
            href_str = str_download_link(flat, soup_up)
            pub_str = date_of_pub_parents(flat, soup)
    elif xl_exception == 'LetterDate':
        temp_str = '\n'.join(soup_up.find_all(text=re.compile(REPORT_DATE_TEXT, re.I)))
        flat = [temp_str]
        href_str = str_download_link(flat, soup_up)
        pub_str = date_of_pub_parents(flat, soup)
    elif xl_exception == 'By_pub_date':
        try:
            flat = []
            temp_str = soup.find(text=re.compile(PUBLICATION_MONTH)).parent.parent.parent.text.replace("\n", "") \
                           .replace("\t", "").strip().split(PUBLICATION_YEAR)[0] + PUBLICATION_YEAR
            try:
                flat.append(temp_str[temp_str.index(PUBLICATION_MONTH) - 2:temp_str.index(PUBLICATION_MONTH) + 8])
            except ValueError:
                flat.append(soup.find(text=re.compile(PUBLICATION_MONTH)))
            pub_str = date_of_pub_parents(flat, soup)
            href_str = str_download_link(flat, soup_up)
        except AttributeError:
            href_str = '-'
            pub_str = '-'
    elif xl_exception == 'rep_no_day':
        flat = [soup.find(text=re.compile(REPORT_DATE_TEXT_WO_DAY, re.I))]
        href_str = str_download_link(flat, soup_up)
        pub_str = date_of_pub_parents(flat, soup)
    elif xl_exception == 'By_rep_date_less_par':
        try:
            temp_str = '\n'.join(soup.find_all(text=re.compile(REPORT_DATE)))
            flat = [temp_str]
            href_str = str_download_link(flat, soup_up)
            pub_str = date_of_pub_parents(flat, soup)
        except AttributeError:
            flat.append('-')
            pub_str = date_of_pub_parents(flat, soup)
    elif xl_exception == 'Не удалось':
        href_str = '-'
        pub_str = '-'
    elif xl_exception == 'rep_no_year':
        try:
            u = soup.find(text=re.compile(REPORT_DATE_TEXT, re.I)).parent.parent
            href_str = u.find('a')['href']
            str_find = u.find(text=re.compile(PUBLICATION_MONTH, re.I))
            month_pos = str_find.index(PUBLICATION_MONTH)
            pub_str = str_find[month_pos - 2:month_pos + 8]
        except TypeError:
            report_date_text_2 = REPORT_DATE_TEXT[:-5]
            u = soup.find(text=re.compile("средств на " + report_date_text_2, re.I)).parent.parent.parent.parent.parent
            temp_str = u.find(text=re.compile(PUBLICATION_MONTH, re.I))
            pub_str = temp_str
            href_str = u.find('a')['href']
        except AttributeError:
            href_str = '-'
            pub_str = '-'
    elif xl_exception == 'pub_date_inside':
        for element in patterns:
            temp_list.append(soup_up.find_all(text=re.compile(element, re.I)))
        flat = [x.replace('\n', ' ').strip() for xs in temp_list for x in xs]
        flat.reverse()
        for i in flat.copy():
            if not PUBLICATION_MONTH in i:
                flat.remove(i)
        href_str = str_download_link(flat, soup_up)
        pub_str = date_of_pub_parents(flat, soup)
    return pub_str, href_str
