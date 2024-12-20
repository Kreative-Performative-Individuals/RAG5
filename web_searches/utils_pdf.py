from PyPDF2 import PdfWriter, PdfReader

def crop_pdf(input_pdf:str, x1:int, y1:int, x2:int, y2:int):
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

        with open(input_pdf, "wb") as out_f:
            output.write(out_f)