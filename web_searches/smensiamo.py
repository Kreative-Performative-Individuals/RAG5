import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web_searches.utils_web import *
from web_searches.utils_pdf import *

PATH_FOR_PDF = './web_searches/menu.pdf'

if __name__ == '__main__':
    page_str = get_page_string(TOSCANA_MENU_URL)
    menu_url = get_menu_url(page_str)
    menu_pdf = get_menu_pdf(menu_url)
    save_pdf(menu_pdf, PATH_FOR_PDF)
    crop_pdf(PATH_FOR_PDF, 50, 100, 720, 440)