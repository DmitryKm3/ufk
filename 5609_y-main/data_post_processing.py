from re import search
from settings import REPORT_DATE, PUBLICATION_MONTH, REVERSE_REPLACEMENTS, PUBLICATION_YEAR
import datetime

post_correct_date_dict = {
    " янв ": ".01.",
    " фев ": ".02.",
    " мар ": ".03.",
    " апр ": ".04.",
    " май ": ".05.",
    " июн ": ".06.",
    " июл ": ".07.",
    " авг ": ".08.",
    " сен ": ".09.",
    " окт ": ".10.",
    " ноя ": ".11.",
    " дек ": ".12.",
    "." + REPORT_DATE[-2:]: REPORT_DATE[-5:],
    "." + PUBLICATION_MONTH[-2:]: PUBLICATION_MONTH[-5:]
}


def yes_no_result(href_list, yes_no_date):
    for gen_num, i in enumerate(href_list):
        if i == "-" or i is None:
            yes_no_date.append("Нет")
        else:
            yes_no_date.append("Да")
    return yes_no_date


def correct_publication_dates(publication_date_list):
    for index, date in enumerate(publication_date_list.copy()):
        if date is None:
            date = '-'
        for old, new in REVERSE_REPLACEMENTS.items():
            print(f'{date=} {old=} {new=}')
            date = date.replace("\xa0", " ").replace(old, new)
        for old, new in post_correct_date_dict.items():
            print(f'{date=} {old=} {new=}')
            date = date.replace("\xa0", " ").replace(old, new)
        date = date.replace('(','').replace(')','').strip()
        if search(PUBLICATION_MONTH, date):
            print(f'1:{date} |')
            publication_date_list[index] = datetime.datetime.strptime(date, "%d.%m.%Y").strftime("%d.%m.%Y")
        elif search(PUBLICATION_YEAR + PUBLICATION_MONTH[:3], date):
            print(f'2:{date} |')
            publication_date_list[index] = datetime.datetime.strptime(date, "%Y.%m.%d").strftime("%d.%m.%Y")
    return publication_date_list
