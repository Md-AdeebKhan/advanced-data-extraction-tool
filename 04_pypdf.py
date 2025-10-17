from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

pdf_path = input("Enter PDF path: ")

try:
    reader = PdfReader(pdf_path)
    for page_no, page in enumerate(reader.pages):
        print(f"\nPage {page_no + 1}")

        # Text extraction
        try:
            text = page.extract_text()
            if not text or not text.strip():
                img = Image.open(pdf_path)
                text = pytesseract.image_to_string(img)
            print("Text:", text)
        except Exception as e:
            print("Text extraction error:", e)

        # PyPDF2 does not support image or table extraction
        print("Images: Cannot extract with PyPDF2")
        print("Tables: Cannot extract with PyPDF2")

except Exception as e:
    print("Error opening PDF:", e)
