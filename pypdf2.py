from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

pdf_path = input("Enter PDF path: ")

reader = PdfReader(pdf_path)

for page_no, page in enumerate(reader.pages):
    print("\nPage", page_no)

    try:
        text = page.extract_text()
        if not text or not text.strip():
            img = Image.open(pdf_path)
            text = pytesseract.image_to_string(img)
        print("Text:", text)
    except Exception as e:
        print("Text extraction error:", e)

    try:
        images = page.images
        print("Images:", images)
    except Exception as e:
        print("Image extraction error:", e)

    try:
        tables = page.get("tables")
        print("Tables:", tables)
    except Exception as e:
        print("Table extraction error:", e)
