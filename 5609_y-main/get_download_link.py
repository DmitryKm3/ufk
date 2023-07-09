from re import search
import re
from settings import REPORT_DATE, REPLACEMENTS, MONTH_DICT, PUBLICATION_MONTH


def recursive_search_href(point, rec_list: list, floor=0):
    try:
        try:
            href = point.find('a')['href']
        except (TypeError, KeyError):
            href = point['href']
        rec_list.append(href)
        return rec_list
    except (TypeError, KeyError):
        pass
    if 5 <= floor:
        return
    parent = point.parent
    recursive_search_href(parent, rec_list, floor + 1)
    return rec_list


def str_download_link(rss_list: list, soup_up) -> str:
    for i in rss_list:
        if not i:
            return '-'
        temp_str = i.replace("\xa0", " ")
        for old, new in REPLACEMENTS.items():
            temp_str = temp_str.lower().replace(old, new)
        if not search("31", temp_str) and not search("30", temp_str) and not search("29", temp_str) and not \
                search("28", temp_str) and not search(PUBLICATION_MONTH, temp_str):
            for old, new in MONTH_DICT.items():
                temp_str = temp_str.replace(old, new)
        if search(REPORT_DATE, temp_str.replace(" ", "")) or search(PUBLICATION_MONTH, temp_str):
            try:
                i = re.sub("\(.*?\)+", "", i)
                #i = re.sub("\(.*)$", "", i) #krivetko
                i = i.replace('(','').replace(')','') #krivetko
                a_tag = soup_up.find('a', string=i)
                if a_tag:
                    href_str = a_tag['href']
                else:
                    href_str = '-'
                break
            except TypeError:
                try:
                    u = soup_up.find(text=re.compile(i, re.I))
                    rec_list = []
                    href = recursive_search_href(u.parent, rec_list)
                    if len(href) > 0:
                        href_str = href[0]
                    else:
                        href_str = '-'
                    break
                except AttributeError:
                    for div in soup_up.find_all('div', {"class": "name"}):
                        if search(PUBLICATION_MONTH, div.text):
                            u = soup_up.find('div', text=div.text).parent.parent
                            href = recursive_search_href(u.parent, rec_list)
                            if len(href) > 0:
                                href_str = href[0]
                            else:
                                href_str = '-'
                            break
                    for span in soup_up.find_all('span', text=i):
                        if search(REPORT_DATE, str(span)):
                            href_str = span.parent['href']
                            break
            except AttributeError:
                href_str = '-'
                break
    try:
        href_str
    except UnboundLocalError:
        href_str = '-'
    return href_str
