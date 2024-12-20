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
    #crop_pdf(PATH_FOR_PDF, X_START, Y_START, X_END, Y_END, PATH_FOR_PDF)
    
    for day in range(6):
        menu_at = crop_pdftable_to_daymeal(PATH_FOR_PDF, day, dinner=False)
        menu_at = crop_pdftable_to_daymeal(PATH_FOR_PDF, day, dinner=True)

    for i in range(6):
        print(f'Menu for {day_from_int(i)}:')
        print(get_text_from_pdf(f'./web_searches/cropped_menu_{i}_False.pdf'))