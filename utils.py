import os
import requests

from pdf2image import convert_from_path
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from Screenshot import Screenshot_Clipping

def download_first_page_as_jpeg(dl_link, dest):
    tmp = 'tmp_download.pdf'
    pdf = Path(tmp)

    res = requests.get(dl_link)
    pdf.write_bytes(res.content)

    pages = convert_from_path(pdf, last_page=1)
    pages[0].save(dest, "JPEG")

    os.remove(tmp)
    return dest

# Take a screenshot of the content of 
# a [written|oral] question
def clip_question_verbatim_screenshot(url, dir='.'):
    options = Options()
    options.headless = True
    d = webdriver.Firefox(options=options)
    ob = Screenshot_Clipping.Screenshot()
    
    print("Clipping question text screenshot from: %s" % url)
    d.get(url)

    e = d.find_element_by_xpath('/html/body/section[5]/div/div/div[1]/div[1]/div[3]/div[2]/p')

    img_path = ob.get_element(d, e, dir)
    print("Img path : %s" % img_path)

    d.quit()

    return img_path
