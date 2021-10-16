import os
from pdf2image import convert_from_path
from pathlib import Path
import re, requests

import twitter, config
import time

BASE_URL = "http://www.sgg.gov.ma"

url = BASE_URL + "/arabe/DesktopModules/MVC/TableListBO/BO/AjaxMethod?_=1634409796320"
"""
the list of the documents is fetched dynamically when loading the page, as a result
plain-old BeautifulSoup is useless.
I managed to find out when and the required headers (which I don't fully understand) to be
able to retrieve it.
"""
latest = requests.get(url, headers = {"ModuleId": "3111", "TabId": "847"}).json()[0]

jarida_file = open(config.jarida_index_file, "r+")
prev_index = jarida_file.read()
new_index = latest['BoNum']
print("Prev index: ", prev_index)

# convert epoch from: /Date(1633993200000)/, to a printable date used for tweeting
def parse_and_format_date(d):
    result = re.search('/Date\((.*)\)/', d).group(1)
    # /!\ we need to perform a division by 1000 when casting the integer
    # because it seems there are 3 extra '0' in the data field,
    # which breaks epoch conversion
    d = time.localtime(int(result) / 1000)
    return "%02d/%02d/%02d" % (d.tm_mday, d.tm_mon, d.tm_year)

if new_index != prev_index:
    tmp_name = "jarida_new.txt"
    new_jarida_file = open(tmp_name, "w+")
    new_jarida_file.write(new_index)

    date = parse_and_format_date(latest['BoDate'])
    print("date: ", date)

    # download and save
    dl_link = BASE_URL + latest['BoUrl']
    jarida_pdf = Path('jarida_assets/jarida_%s.pdf' % new_index)
    res = requests.get(dl_link)
    jarida_pdf.write_bytes(res.content)

    # print a screenshot of the first page
    front_page_jpg = "jarida_assets/jarida_%s_front_page.jpg" % new_index

    pages = convert_from_path(jarida_pdf, last_page=1)
    pages[0].save(front_page_jpg, "JPEG")

    twitter.tweet("#الجريدة_الرسمية :  عدد جديد [%s] تم نشره بتاريخ %s %s" % 
            (new_index, date, dl_link), False, front_page_jpg)

    os.rename(tmp_name, config.jarida_index_file)
else:
    print("Nothing new")
