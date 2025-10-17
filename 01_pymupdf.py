import fitz
from PIL import Image
import pytesseract 

pdf_path = input("Enter PDF path: ")

pdf = fitz.open(pdf_path)

for page_no in range(len(pdf)):
    page = pdf[page_no]
    print("\nPage", page_no)
    
    
    try:
        text = page.get_text()
        if not text.strip():  # if text is empty, apply OCR
            im = page.to_image(resolution=300).original
            text = pytesseract.image_to_string(im)
        print("Text:", text)
    except:
        print("Text: Cannot extract")
    
    
    
    try:
        print("Images:", page.get_images(full=True))
    except:
        print("Images: Cannot extract")
    
    
    try:
        print("Tables:", page.get_text("blocks"))
    except:
        print("Tables: Cannot extract")

pdf.close()
