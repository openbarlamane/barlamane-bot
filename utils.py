import os
import requests

from pdf2image import convert_from_path
from pathlib import Path

def download_first_page_as_jpeg(dl_link, dest):
    tmp = 'tmp_download.pdf'
    pdf = Path(tmp)

    res = requests.get(dl_link)
    pdf.write_bytes(res.content)

    pages = convert_from_path(pdf, last_page=1)
    pages[0].save(dest, "JPEG")

    os.remove(tmp)
    return dest
