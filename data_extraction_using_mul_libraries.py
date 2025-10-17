import fitz
import pdfplumber
import camelot

class PDFExtractor:
    def __init__(self, path):
        self.path = path
        self.doc = fitz.open(path)
        self.pdf = pdfplumber.open(path)

    def get_text(self, page_no):
        return self.doc[page_no].get_text()

    def get_images(self, page_no):
        images = []  
        for xref, *_ in self.doc[page_no].get_images(full=True):  
            img_data = self.doc.extract_image(xref)  
            file_name = f"page{page_no}_img{xref}.{img_data['ext']}"  
            with open(file_name, "wb") as f:  
                f.write(img_data['image'])  
            images.append(file_name)  
        return images  



    def get_tables_plumber(self, page_no):
        return self.pdf.pages[page_no].extract_tables()

    def get_tables_camelot(self, page_no):
        return camelot.read_pdf(self.path, pages=str(page_no+1))


user = input("Enter the PDF path: ")
extractor = PDFExtractor(user)


def pdf_extracter_by_user(PDFExtracter, page=None, keyword=None, all_pages=False):
    results = {}

    if all_pages:  # new branch to extract entire PDF
        for page_no in range(len(PDFExtracter.doc)):
            results[page_no] = {
                "text": PDFExtracter.get_text(page_no),
                "images": PDFExtracter.get_images(page_no),
                "tables_plumber": PDFExtracter.get_tables_plumber(page_no),
                "tables_camelot": PDFExtracter.get_tables_camelot(page_no)
            }



    if page is not None:
        page_no = page
        results[page_no] = {
            "text": PDFExtracter.get_text(page_no),
            "images": PDFExtracter.get_images(page_no),
            "tables_plumber": PDFExtracter.get_tables_plumber(page_no),
            "tables_camelot": PDFExtracter.get_tables_camelot(page_no)
        }

    elif keyword is not None:
        for page_no in range(len(PDFExtracter.doc)):
            page_text = PDFExtracter.get_text(page_no)
            paragraphs = page_text.split("\n\n")
            related_paras = [para for para in paragraphs if keyword.lower() in para.lower()]

            if related_paras:
                results[page_no] = {
                    "text": "\n\n".join(related_paras),
                    "images": PDFExtracter.get_images(page_no),
                    "tables_plumber": PDFExtracter.get_tables_plumber(page_no),
                    "tables_camelot": PDFExtracter.get_tables_camelot(page_no)
                }

    return results
if __name__ == "__main__":

    choice = input("Do you want to extract by page or keyword? (page/keyword/all): ").strip().lower()

    if choice == "page":
        page_no = int(input("Enter page number (starting from 0): "))
        results = pdf_extracter_by_user(extractor, page=page_no)
    elif choice == "keyword":
        keyword = input("Enter keyword/topic to search: ").strip()
        results = pdf_extracter_by_user(extractor, keyword=keyword)
    elif choice == "all":
        results = pdf_extracter_by_user(extractor, all_pages=True)
    else:
        print("Invalid choice!")
        results = {}

    
    for page, content in results.items():
        print(f"\n--- Page {page} ---")
        print("Text:", content['text'])
        print("Images:", content['images'])
        print("Tables (Plumber):", content['tables_plumber'])
        print("Tables (Camelot):", content['tables_camelot'])
