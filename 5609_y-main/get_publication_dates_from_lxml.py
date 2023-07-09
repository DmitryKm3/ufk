import re
from re import search
import traceback
from settings import REPORT_DATE, REPORT_DATE_TEXT, REPORT_DATE_TEXT_WO_DAY, PUBLICATION_MONTH, PUBLICATION_MONTH_TEXT


def recursive_search_pub_date(point, rec_list, floor=0):
    pub_date = re.sub(" +", " ", str(point.text).replace("\n", " ").replace("-", ".").replace("/", ".").replace(",", ""))
    if search(PUBLICATION_MONTH, pub_date) or\
        search(PUBLICATION_MONTH[:4] + PUBLICATION_MONTH[-2:], pub_date) or\
        search(PUBLICATION_MONTH[-4:] + PUBLICATION_MONTH[:4], pub_date) or\
        search(PUBLICATION_MONTH_TEXT, pub_date) or\
        search(PUBLICATION_MONTH[0:5] + PUBLICATION_MONTH[-1], pub_date) or\
        search(PUBLICATION_MONTH_TEXT.replace(" ", "\xa0"), pub_date) or\
        search(PUBLICATION_MONTH_TEXT[1:4] + ' ' + PUBLICATION_MONTH_TEXT[6:], pub_date) or\
        search(PUBLICATION_MONTH_TEXT[1:6] + PUBLICATION_MONTH_TEXT[-2:], pub_date):
        try:
            if search(PUBLICATION_MONTH, pub_date):
                month_pos = pub_date.index(PUBLICATION_MONTH)
                publication_str = pub_date[month_pos - 2:month_pos + 8]
            elif search(PUBLICATION_MONTH_TEXT, pub_date) or \
                    search(PUBLICATION_MONTH_TEXT.replace(" ", "\xa0"), pub_date):
                try:
                    month_pos = pub_date.index(PUBLICATION_MONTH_TEXT)
                except ValueError:
                    month_pos = pub_date.index(PUBLICATION_MONTH_TEXT.replace(" ", "\xa0"))
                publication_str = pub_date[month_pos - 2:month_pos + 10]
            elif search(PUBLICATION_MONTH_TEXT[1:6] + PUBLICATION_MONTH_TEXT[-2:], pub_date):
                month_pos = pub_date.index(PUBLICATION_MONTH_TEXT[1:6] + PUBLICATION_MONTH_TEXT[-2:])
                publication_str = pub_date[month_pos - 3: month_pos + 7]
            elif search(PUBLICATION_MONTH[-4:] + PUBLICATION_MONTH[0:4], pub_date):
                month_pos = pub_date.index(PUBLICATION_MONTH[-4:] +
                                           PUBLICATION_MONTH[:4])
                publication_str = pub_date[month_pos:month_pos + 10]
            elif search(PUBLICATION_MONTH[:4] + PUBLICATION_MONTH[-2:], pub_date):
                month_pos = pub_date.index(PUBLICATION_MONTH[:4] + PUBLICATION_MONTH[-2:])
                publication_str = pub_date[month_pos - 2:month_pos + 5] +\
                    PUBLICATION_MONTH[-3:]
            elif search(PUBLICATION_MONTH_TEXT[1:4] + ' ' + PUBLICATION_MONTH_TEXT[6:], pub_date):
                month_pos = pub_date.index(PUBLICATION_MONTH_TEXT[1:4] + ' ' + PUBLICATION_MONTH_TEXT[6:])
                publication_str = pub_date[month_pos - 3:month_pos + 5] + \
                    PUBLICATION_MONTH[-3:]
        except:
            traceback.print_exc()
            publication_str = ''
        rec_list.append(publication_str)
        return rec_list
    if floor >= 23:  # 23 parents is too much, but for publication date with href it's ok
        return
    parent = point.parent
    recursive_search_pub_date(parent, rec_list, floor + 1)
    return rec_list


def date_of_pub_parents(flat, soup):
    for i in flat:
        if not i:
            return '-'
        k = re.sub(" +", " ", i.replace("\xa0", " "))
        if (search(REPORT_DATE, k) \
            or search(REPORT_DATE[0:7] + REPORT_DATE[-1], k) \
            or search(REPORT_DATE_TEXT, k) or search(REPORT_DATE_TEXT_WO_DAY, k.lower())
            or search(PUBLICATION_MONTH, k.lower())) or search((REPORT_DATE[0:-3] + REPORT_DATE[-1]).replace(".", ""), k)\
            and not search("уточнен", i.lower()):
            i = re.sub("\(.*?\)+", "", i)
            i = re.sub("\(.*$", "", i)
            rec_list = []
            i = i.replace('(','').replace(')','') #krivetko
            u = soup.find(text=re.compile(i[:97], re.I))
            if "\xa0" in str(u):
                print('what to do')
            try:
                p = recursive_search_pub_date(u.parent, rec_list)[0]
            except (IndexError, AttributeError):
                traceback.print_exc()
                p = '-'
            break
    try:
        if p is None:
            p = '-'
    except UnboundLocalError:
        p = '-'
    return p
