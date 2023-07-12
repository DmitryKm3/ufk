import datetime
from dateutil.relativedelta import relativedelta


def last_day_of_month(day):
    next_month = day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def report_and_publication_date():
    today = datetime.datetime.now()
    prev_date = datetime.datetime.now() - relativedelta(months=1)
    report_date = last_day_of_month(prev_date).strftime("%d.%m.%Y")
    return report_date, today.strftime("%d.%m.%Y")[2:], str(today.year)


def all_datetypes_for_searching():
    report_date_text, report_date_text_wo_day, publication_month_text = REPORT_DATE, REPORT_DATE[2:], PUBLICATION_MONTH

    for old, new in REVERSE_REPLACEMENTS.items():
        publication_month_text = publication_month_text.replace(new, old)
    for old, new in REVERSE_REPLACEMENTS.items():
        report_date_text = report_date_text.replace(new, old)
    for old, new in REVERSE_REPLACEMENTS.items():
        publication_month_text = publication_month_text.replace(new, old)
    for old, new in REVERSE_REPLACEMENTS_IM.items():
        report_date_text_wo_day = report_date_text_wo_day.replace(new, old)

    return report_date_text, report_date_text_wo_day, publication_month_text


LXML_PATH = 'lxml/'
REPORT_DATE, PUBLICATION_MONTH, PUBLICATION_YEAR = report_and_publication_date()

REVERSE_REPLACEMENTS = {
    ' января ': '.01.',
    ' февраля ': '.02.',
    ' марта ': '.03.',
    ' апреля ': '.04.',
    ' мая ': '.05.',
    ' июня ': '.06.',
    ' июля ': '.07.',
    ' августа ': '.08.',
    ' сентября ': '.09.',
    ' октября ': '.10.',
    ' ноября ': '.11.',
    ' декабря ': '.12.'}
REPLACEMENTS = {
    '\xa0': '',
    '\t': '',
    '&nbsp': '',
    ' январь ': '.01.',
    ' января ': '.01.',
    ' февраль ': '.02.',
    ' февраля ': '.02.',
    ' марта ': '.03.',
    ' март ': '.03.',
    ' апреля ': '.04.',
    ' апрель ': '.04.',
    ' май ': '.05.',
    ' мая ': '.05.',
    ' июнь ': '.06.',
    ' июня ': '.06.',
    ' июль ': '.07.',
    ' июля ': '.07.',
    ' августа ': '.08.',
    ' август ': '.08.',
    ' сентябрь ': '.09.',
    ' сентября ': '.09.',
    ' октябрь ': '.10.',
    ' октября ': '.10.',
    ' ноябрь ': '.11.',
    ' ноября ': '.11.',
    ' декабрь ': '.12.',
    ' декабря ': '.12.',
    '.21': '.2021',
    '.22': '.2022',
    '-': '.',
    '01.(': '01.{}'.format(REPORT_DATE[-4:]),
    '02.(': '02.{}'.format(REPORT_DATE[-4:]),
    '03.(': '03.{}'.format(REPORT_DATE[-4:]),
    '04.(': '04.{}'.format(REPORT_DATE[-4:]),
    '05.(': '05.{}'.format(REPORT_DATE[-4:]),
    '06.(': '06.{}'.format(REPORT_DATE[-4:]),
    '07.(': '07.{}'.format(REPORT_DATE[-4:]),
    '08.(': '08.{}'.format(REPORT_DATE[-4:]),
    '09.(': '09.{}'.format(REPORT_DATE[-4:]),
    '10.(': '10.{}'.format(REPORT_DATE[-4:]),
    '11.(': '11.{}'.format(REPORT_DATE[-4:]),
    '12.(': '12.{}'.format(REPORT_DATE[-4:]),
}
MONTH_DICT = {
    '.01.': '31.01.',
    '.02.': '28.02.',
    '.03.': '31.03.',
    '.04.': '30.04.',
    '.05.': '31.05.',
    '.06.': '30.06.',
    '.07.': '31.07.',
    '.08.': '31.08.',
    '.09.': '30.09.',
    '.10.': '31.10.',
    '.11.': '30.11.',
    '.12.': '31.12.'
}
REVERSE_REPLACEMENTS_IM = {
    ' январь ': '.01.',
    ' февраль ': '.02.',
    ' март ': '.03.',
    ' апрель ': '.04.',
    ' май ': '.05.',
    ' июнь ': '.06.',
    ' июль ': '.07.',
    ' август ': '.08.',
    ' сентябрь ': '.09.',
    ' октябрь ': '.10.',
    ' ноябрь ': '.11.',
    ' декабрь ': '.12.',
}

REPORT_DATE_TEXT, REPORT_DATE_TEXT_WO_DAY, PUBLICATION_MONTH_TEXT = all_datetypes_for_searching()
patterns = ['собственных средств', 'размер сс', 'расчет сс', 'размера сс', 'собственные средства',
            'собственный средства']
