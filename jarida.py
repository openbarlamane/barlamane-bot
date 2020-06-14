import os
from pdf2image import convert_from_path
from pathlib import Path
from bs4 import BeautifulSoup
import requests

import twitter, config
from datetime import datetime

print(datetime.now().strftime("%d/%m/%Y %H:%M"))

r = requests.get("http://www.sgg.gov.ma/arabe/Legislations/DernierBulletinOfficiel.aspx")
soup = BeautifulSoup(r.text, 'html.parser')

new_index = soup.find_all(class_='Normal UDT_Table_AlternateItem')[1].text.split('\n')[1]

jarida_file = open(config.jarida_index_file, "r+")
prev_index = jarida_file.read()
print("Prev index: ", prev_index)

if new_index != prev_index:
    tmp_name = "jarida_new.txt"
    new_jarida_file = open(tmp_name, "w+")
    new_jarida_file.write(new_index)

    date = soup.find_all(class_='Normal UDT_Table_Item')[0].text.split('\n')[1].replace('.', '_')
    print("Date: %s" % date)
    dl_link = soup.find_all(class_='Normal UDT_Table_AlternateItem')[0].find_all('a', href=True)[0]['href']
    jarida_pdf = Path('jarida_assets/jarida_%s.pdf' % date)
    res = requests.get(dl_link)
    jarida_pdf.write_bytes(res.content)

    front_page_jpg = "jarida_assets/jarida_%s_front_page.jpg" % date

    pages = convert_from_path(jarida_pdf, last_page=1)
    pages[0].save(front_page_jpg, "JPEG")

    twitter.tweet("#الجريدة_الرسمية :  عدد جديد [%s] تم نشره بتاريخ %s %s" % 
            (new_index, date.replace('_', '/'), dl_link), False, front_page_jpg)

    os.rename(tmp_name, config.jarida_index_file)
else:
    print("Nothing new")
