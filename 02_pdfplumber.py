import pdfplumber
from PIL import Image
import pytesseract

pdf_path = input("Enter PDF path: ")

pdf = pdfplumber.open(pdf_path)
pages = pdf.pages
for page_no, page in enumerate(pages):
    print("\nPage", page_no)
    
    # Text extraction
    try:
        text = page.get_text()
        if not text.strip():  # if text is empty, apply OCR
            im = page.to_image(resolution=300).original
            text = pytesseract.image_to_string(im)
        print("Text:", text)
    except:
        print("Text: Cannot extract")
    
    # Images
    try:
        print("Images:", page.images)
    except:
        print("Images: Cannot extract")
    
    # Tables
    try:
        print("Tables:", page.extract_tables())
    except:
        print("Tables: Cannot extract")

pdf.close()
