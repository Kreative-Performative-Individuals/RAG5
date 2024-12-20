import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web_searches.utils_web import *
from web_searches.utils_pdf import *

if __name__ == '__main__':
    page_str = get_page_string(TOSCANA_MENU_URL)
    menu_url = get_menu_url(page_str)
    menu_pdf = get_menu_pdf(menu_url)
    #save_pdf(menu_pdf, './web_searches/menu.pdf')