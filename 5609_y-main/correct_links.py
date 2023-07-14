import re
from re import search
from urllib.parse import quote


def correct_site_link(site_link_list):
    for num, i in enumerate(site_link_list.copy()):
        site_link_list[num] = re.split(',', site_link_list[num])[0].replace(
            "https://", "").replace("http://", "").replace("/", "").replace("www.", "")
    return site_link_list


def full_download_link(download_link, url_index, site_links):
    quote_dict = {
        '%3F': '?',
        '%3D': '=',
        '%26': '&'
    }
    while download_link.startswith(".") or download_link.startswith("/"):
        download_link = download_link[1:]
    if download_link.startswith("http"):
        return download_link
    elif not download_link == '-':
        if search(' ', download_link):
            download_link = 'https://' + site_links[url_index] + "/" + quote(download_link)
        else:
            download_link = 'https://' + site_links[url_index] + "/" + download_link
    for old, new in quote_dict.items():
        download_link = download_link.replace(old, new)
    return download_link
