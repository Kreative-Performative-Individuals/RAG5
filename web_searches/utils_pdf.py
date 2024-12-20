import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Sizes of the menus of mensa Martiri (Pisa)
X_START = 50
X_END = 720
Y_START = 175
Y_END = 500
CELL_HEIGHT = (Y_END - Y_START) / 2
CELL_WIDTH = (X_END - X_START) / 6

def crop_pdf(input_pdf: str, x1: int, y1: int, x2: int, y2: int, output_pdf: str = None, dpi: int = 300):
    """
    Extract a cropped region of a PDF as a new high-quality PDF.

    Args:
        input_pdf (str): Path to the input PDF.
        x1 (int): The x-coordinate of the lower-left corner of the crop area.
        y1 (int): The y-coordinate of the lower-left corner of the crop area.
        x2 (int): The x-coordinate of the upper-right corner of the crop area.
        y2 (int): The y-coordinate of the upper-right corner of the crop area.
        output_pdf (str): Path to save the cropped PDF. If None, appends '_cropped' to input filename.
        dpi (int): The resolution for rendering the cropped region. Default is 300 DPI.
    """
    doc = fitz.open(input_pdf)
    page = doc[0]
    crop_rect = fitz.Rect(x1, y1, x2, y2)

    zoom = dpi / 72  # Convert DPI to zoom factor (72 is the default resolution of PyMuPDF)
    mat = fitz.Matrix(zoom, zoom)  # Scale matrix for higher resolution

    new_doc = fitz.open()
    new_page = new_doc.new_page(width=crop_rect.width, height=crop_rect.height)

    pix = page.get_pixmap(matrix=mat, clip=crop_rect)
    new_page.insert_image(new_page.rect, pixmap=pix)

    # Save the cropped PDF
    if output_pdf is None:
        output_pdf = input_pdf.replace(".pdf", "_cropped.pdf")
    new_doc.save(output_pdf)
    new_doc.close()
    doc.close()


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
        y2 -= 12
    else:
        y1 -= 12
    path_to_save = f'./web_searches/cropped_menu_{day}_{dinner}.pdf'
    crop_pdf(input_pdf, x1, y1, x2, y2, path_to_save, dpi=300)
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

def day_from_int(day:int) -> str:
    '''
    Get the day string from the integer value.
    
    Args:
        day (int): The integer value of the day.

    Returns:
        The day string. (mon,tue,wed,thu,fri,sat)
    '''
    return ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'][day]

def get_text_from_pdf(image_path: str, lang: str = 'it') -> str:
    """
    Perform OCR on an image to extract text.

    Args:
        image_path (str): Path to the input image.
        lang (str): Language for OCR. Default is English ('eng').

    Returns:
        str: The extracted text from the image.
    """
    # Perform OCR using Tesseract
    text = pytesseract.image_to_string(Image.open(image_path), lang=lang)
    return text
