
import urllib
import urllib.request

MARTIRI_STR = '<p><strong>Martiri</strong>&nbsp;&nbsp;<br />'
HOMEPAGE_URL = 'https://www.dsu.toscana.it'
TOSCANA_MENU_URL = 'https://www.dsu.toscana.it/i-menu'

def get_page_string(url: str) -> str:
    '''
    Get the page content as a string
    Args:
        url: the url of the page
    Returns:
        the page content as a string
    '''
    page = urllib.request.urlopen(url)
    string_page = page.read().decode('utf-8')
    page.close()
    return string_page

def get_menu_url(page_str:str) -> str:
    '''
    Get the url of the pdf containing the menu
    Args:
        page_str: the page content as a string
    Returns:
        the url of the pdf containing the menu
    '''
    url = page_str.split(MARTIRI_STR)[1].split('href="')[1].split('"')[0]
    return HOMEPAGE_URL + url

def get_menu_pdf(page_url: str) -> bytes:
    '''
    Get the menu pdf from the page
    Args:
        page_url: the url of the page containing the pdf
    Returns:
        the pdf file downloaded or None if the pdf is not found
    '''
    pdf = urllib.request.urlopen(page_url)
    pdf_file = pdf.read()
    pdf.close()
    return pdf_file    

def save_pdf(pdf_file: bytes, path: str):
    '''
    Save the pdf file
    Args:
        pdf_file: the pdf file to save
        path: the path where the pdf file will be saved
    '''
    with open(path, 'wb') as f:
        f.write(pdf_file)
