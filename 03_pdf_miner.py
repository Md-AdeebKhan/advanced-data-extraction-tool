from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from PIL import Image
import pytesseract

pdf_path = input("Enter PDF path: ")

for page_no, page_layout in enumerate(extract_pages(pdf_path)):
    print("\nPage", page_no)

    try:
        text = ""
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text += element.get_text()
        if not text.strip():
            img = Image.open(pdf_path)
            text = pytesseract.image_to_string(img)
        print("Text:", text)
    except Exception as e:
        print("Text extraction error:", e)

    try:
        print("Images: Cannot extract with PDFMiner")
    except Exception as e:
        print("Image extraction error:", e)

    try:
        print("Tables: Cannot extract with PDFMiner")
    except Exception as e:
        print("Table extraction error:", e)
