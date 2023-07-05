#!/usr/bin/python3

import os
import requests

import pymongo
from pdf2image import convert_from_path
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from Screenshot import Screenshot as Screenshot_Clipping

import config 

WRITTEN_Q_PAGE = "https://www.chambredesrepresentants.ma/ar/%D8%A7%D9%84%D8%A3%D8%B3%D9%80%D8%A6%D9%84%D8%A9-%D8%A7%D9%84%D9%83%D8%AA%D8%A7%D8%A8%D9%8A%D8%A9"
ORAL_Q_PAGE = "https://www.chambredesrepresentants.ma/ar/%D9%85%D8%B1%D8%A7%D9%82%D8%A8%D8%A9-%D8%A7%D9%84%D8%B9%D9%85%D9%84-%D8%A7%D9%84%D8%AD%D9%83%D9%88%D9%85%D9%8A/%D8%A7%D9%84%D8%A3%D8%B3%D9%80%D8%A6%D9%84%D8%A9-%D8%A7%D9%84%D8%B4%D9%81%D9%88%D9%8A%D8%A9"

twitter_map = {
'نجوى ككوس': '@VoixLibre6'
}

def connect_to_db():
    mongo = pymongo.MongoClient(config.mongo_db_url)
    db = mongo["barlamane"]
    return db

def download_first_page_as_jpeg(dl_link, dest):
    tmp = 'tmp_download.pdf'
    pdf = Path(tmp)

    res = requests.get(dl_link)
    pdf.write_bytes(res.content)

    pages = convert_from_path(pdf, last_page=1)
    pages[0].save(dest, "JPEG")

    os.remove(tmp)
    return dest

# Take a screenshot of the content of a [written|oral] question
def clip_question_verbatim_screenshot(url, dir='.'):
    options = Options()
    options.headless = True

    # use full path to geckodriver in order to avoid crontab PATH intricaties
    # sudo apt-get install chromium-chromedriver
    d = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=options)
    ob = Screenshot_Clipping.Screenshot()
    
    print("Clipping question text screenshot from: %s" % url)
    d.get(url)
    
    # delete page header (hinders remaining elements)
    d.execute_script('document.getElementsByClassName("container")[1].remove()')

    try:
        e = d.find_element_by_xpath('/html/body/section[5]/div/div/div[1]/div[1]/div[3]/div[2]/p')
    except Exception as exc:
        print("Exception: ", exc)
        e = d.find_element_by_xpath('/html/body/section[5]/div/div/div[1]/div[1]/div[3]/div/p')
        return ""

    img_path = ob.get_element(d, e, dir, hide_elements=['class=mid-header', 'class=top-header'])
    print("Img path : %s" % img_path)

    d.quit()

    return img_path
