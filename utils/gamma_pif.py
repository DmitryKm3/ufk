import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring_project.settings")
django.setup()

from monitoring.models import PIF, UK

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from datetime import datetime, timezone
import pytz
localtime = pytz.timezone("Asia/Krasnoyarsk")

from fake_useragent import UserAgent
fua = UserAgent(verify_ssl=False)

headers = {'User-Agent': fua.random}

from bs4 import BeautifulSoup

import sys

def main(rtype, npp):
    
    if rtype == "pif_monitoring":
        pif = PIF.objects.get(pif_npp=npp)
        uk = pif.pif_uk
        site = pif.checksite
    else:
        uk = UK.objects.get(uk_npp=npp)
        site = uk.checkpage
    
    sibarray = []

    timedelta = datetime.now() - uk.uk_lastaccess 
    if timedelta.seconds < 3600:
        retries = 10
        for retry in range(retries):
            try:
                response = requests.get(site, headers=headers, verify=False)
            except requests.exceptions.RequestException as re:
                pass
            else:
                break
        if response.status_code == 200:
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup.find_all(["h1","h2","h3", "h4", "h5", "h6"]):
                if tag.text.strip() != "":
                    elemarray = []
                    sibling = tag.find_next_sibling()
                    while sibling is not None:
                        if sibling.name == "p" and sibling.text.strip() != "":
                            name = sibling.text
                            sibling = sibling.find_next_sibling()
                            if sibling is not None:
                                if sibling.name == "p":
                                    dates = re.findall(r'\d{2}.\d{2}.\d{4}', sibling.text)
                                    if len(dates) > 0:
                                        elemarray.append([name, dates[0]])
                                    sibling = sibling.find_next_sibling()
                                else:
                                    sibling = sibling.find_next_sibling()
                        else:
                            sibling = sibling.find_next_sibling()
                        if sibling is not None and sibling.name in ["h1","h2","h3", "h4", "h5", "h6", "div"]:
                            sibling = None
                    if len(elemarray) > 0:
                        sibarray.append([tag.text, elemarray])
    return sibarray
