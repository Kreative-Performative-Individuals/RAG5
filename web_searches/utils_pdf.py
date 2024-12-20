from PyPDF2 import PdfWriter, PdfReader

# Sizes of the menus of mensa Martiri (Pisa)
X_START = 50
X_END = 720
Y_START = 100 
Y_END = 420
CELL_HEIGHT = (Y_END - Y_START) / 2
CELL_WIDTH = (X_END - X_START) / 6

def crop_pdf(input_pdf:str, x1:int, y1:int, x2:int, y2:int, output_pdf:str = None):
    """
    Crop the PDF file.

    Args:
        input_pdf (str): The path to the PDF file to crop.
        x1 (int): The x coordinate of the lower left corner.
        y1 (int): The y coordinate of the lower left corner.
        x2 (int): The x coordinate of the upper right corner.
        y2 (int): The y coordinate of the upper right corner.
    """
    with open(input_pdf, "rb") as in_f:
        input1 = PdfReader(in_f)
        output = PdfWriter()

        page = input1.pages[0]
        page.trimbox.lower_left = (x1, y1)
        page.trimbox.upper_right = (x2, y2)
        page.cropbox.lower_left = (x1, y1)
        page.cropbox.upper_right = (x2, y2)
        output.add_page(page)

        if output_pdf is None:
            output_pdf = input_pdf

        with open(output_pdf, "wb") as out_f:
            output.write(out_f)

def crop_pdftable_to_daymeal(input_pdf:str, day:int, dinner:bool=True):
    '''
    Crop the PDF file from a table to a specific day meal. (lunch or dinner)
    
    Args:
        input_pdf (str): The path to the PDF file to crop.
        day (int): The day of the week (from 0 to 5) (m,t,w,t,f,s).
        lunch (bool): True if lunch, False if dinner.

    Returns:
        The cropped PDF file's path.
    '''
    x1 = X_START + CELL_WIDTH * day + day
    x2 = x1 + CELL_WIDTH
    y1 = Y_START if dinner else Y_START + CELL_HEIGHT
    y2 = Y_START + CELL_HEIGHT if dinner else Y_END
    if dinner:
        y2 += 12
    else:
        y1 += 12
    path_to_save = f'./web_searches/cropped_menu_{day}_{dinner}.pdf'
    crop_pdf(input_pdf, x1, y1, x2, y2, path_to_save)
    return path_to_save

def int_from_day(day:str) -> int:
    '''
    Get the integer value from the day string.
    
    Args:
        day (str): The day string. (m,t,w,t,f,s) or (mon,tue,wed,thu,fri,sat) or (monday,tuesday,wednesday,thursday,friday,saturday)

    Returns:
        The integer value of the day.
    '''
    if len(day) == 1:
        return {'m': 0, 't': 1, 'w': 2, 't': 3, 'f': 4, 's': 5}[day]
    elif len(day) == 3:
        return {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5}[day]
    else:
        return {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5}[day]