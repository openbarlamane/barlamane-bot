import os
from pathlib import Path
import re
import time
from pdf2image import convert_from_path
import requests
import logging

import twitter
import config

BASE_URL = "http://www.sgg.gov.ma" # http, not https!

def parse_and_format_date(d):
    """
    convert epoch from: /Date(1633993200000)/, to a printable date used for tweeeting
    """
    result = re.search('/Date\((.*)\)/', d).group(1)
    # /!\ we need to perform a division by 1000 when casting the integer
    # because it seems there are 3 extra '0' in the data field,
    # which breaks epoch conversion
    d = time.localtime(int(result) / 1000)
    return "%02d/%02d/%02d" % (d.tm_mday, d.tm_mon, d.tm_year)

def main():
    """
    retrieve latest jarida item and tweet and update if necessary
    """

    url = BASE_URL + "/arabe/DesktopModules/MVC/TableListBO/BO/AjaxMethod?_=1634409796320"
    
    # the list of the documents is fetched dynamically when loading the page, as a result
    # plain-old BeautifulSoup is useless.
    # I managed to find out when and the required headers (which I don't fully understand) to be
    # able to retrieve it.
    latest = requests.get(url, headers={"ModuleId": "3111", "TabId": "847"}).json()[0]

    jarida_file = open(config.jarida_index_file, "r+")
    prev_index = jarida_file.read()
    new_index = latest['BoNum']
    logging.info("Prev index: %s" % prev_index)

    if new_index != prev_index:
        tmp_name = "jarida_new.txt"
        new_jarida_file = open(tmp_name, "w+")
        new_jarida_file.write(new_index)

        date = parse_and_format_date(latest['BoDate'])
        logging.debug("date: ", date)

        # download and save
        dl_link = BASE_URL + latest['BoUrl']
        jarida_pdf = Path('jarida_assets/jarida_%s.pdf' % new_index)
        res = requests.get(dl_link)
        jarida_pdf.write_bytes(res.content)

        # print a screenshot of the first page
        front_page_jpg = "jarida_assets/jarida_%s_front_page.jpg" % new_index

        pages = convert_from_path(jarida_pdf, last_page=1)
        pages[0].save(front_page_jpg, "JPEG")

        tweet_content = "#الجريدة_الرسمية :  عدد جديد [%s] تم نشره بتاريخ %s %s" % (new_index, date, dl_link)
        twitter.tweet(tweet_content, False, front_page_jpg)

        os.rename(tmp_name, config.jarida_index_file)
    else:
        logging.debug("Nothing new")

if __name__ == "__main__":
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.basicConfig(filename=jarida_log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)7s %(message)s')
    main()
