import os
import re
import sys
import fitz           # PyMuPDF
import pdfplumber
import camelot
import pandas as pd
from pathlib import Path

# --------------------------- UTILITIES ---------------------------

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

def clean_sheet_name(name: str) -> str:
    # Excel sheet name constraints: <=31 chars, no []:*?/\
    name = re.sub(r'[\[\]\:\*\?\/\\]', '_', name)[:31]
    if not name:
        name = "Sheet"
    return name

def page_list_from_input(choice: str, total_pages: int):
    """
    choice examples:
      - 'all'
      - '5' (0-indexed or 1-indexed? We'll use 0-indexed for consistency here)
      - '0-5'
      - '0,3,7'
    This function returns a sorted unique list of valid 0-indexed page numbers.
    """
    choice = choice.strip().lower()
    if choice == "all":
        return list(range(total_pages))

    pages = set()
    if "-" in choice and "," not in choice:
        # range "a-b"
        a, b = choice.split("-")
        a, b = int(a), int(b)
        rng = range(min(a, b), max(a, b) + 1)
        pages.update([p for p in rng if 0 <= p < total_pages])
    else:
        # comma separated "a,b,c"
        for tok in choice.split(","):
            tok = tok.strip()
            if not tok:
                continue
            if "-" in tok:
                a, b = tok.split("-")
                a, b = int(a), int(b)
                rng = range(min(a, b), max(a, b) + 1)
                pages.update([p for p in rng if 0 <= p < total_pages])
            else:
                p = int(tok)
                if 0 <= p < total_pages:
                    pages.add(p)

    return sorted(pages)

# ------------------------ EXTRACTION CORE ------------------------

def extract_text_for_page(doc: fitz.Document, page_no: int) -> str:
    return doc[page_no].get_text("text") or ""

def extract_images_for_page(doc: fitz.Document, page_no: int, out_dir: Path) -> int:
    """
    Saves images as PNGs to out_dir/page-{n}/image-{idx}.png
    Returns count of images saved.
    """
    page = doc[page_no]
    img_list = page.get_images(full=True)
    if not img_list:
        return 0

    page_img_dir = ensure_dir(out_dir / f"page-{page_no}")
    count = 0
    for idx, img in enumerate(img_list, start=1):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        # Handle CMYK/Alpha conversions
        if pix.n >= 4 and pix.alpha:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        elif pix.n > 4:  # e.g., CMYK without alpha
            pix = fitz.Pixmap(fitz.csRGB, pix)
        out_path = page_img_dir / f"image-{idx}.png"
        pix.save(out_path.as_posix())
        pix = None
        count += 1
    return count

def extract_tables_for_page(pdf_path: str, page_no_one_indexed: int):
    """
    Returns list of DataFrames for a single page using both flavors.
    Deduplicates by content shape/values where possible.
    """
    dfs = []
    seen_signatures = set()
    for flavor in ("lattice", "stream"):
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_no_one_indexed), flavor=flavor)
            for t in tables:
                df = t.df
                # Create a simple signature to avoid dup tables
                sig = (df.shape, tuple(df.head(3).fillna("").astype(str).agg("|".join, axis=1)))
                if sig not in seen_signatures and df.shape[1] >= 2:  # keep only >= 2 columns
                    seen_signatures.add(sig)
                    dfs.append(df)
        except Exception:
            # swallow Camelot errors; continue with other flavor
            pass
    return dfs

# ------------------------ SAVE HELPERS ---------------------------

def save_text(page_no: int, text: str, text_pages_dir: Path, combined_texts: list):
    # Per-page TXT
    out_file = text_pages_dir / f"text-page-{page_no}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(text)
    # Combined accumulator
    combined_texts.append(f"\n--- Page {page_no} ---\n{text}")

def save_tables(page_no: int, tables: list[pd.DataFrame], tables_dir: Path,
                excel_writer_holder: dict, excel_ok_holder: dict, sheet_count_holder: dict):
    """
    Always saves per-table CSVs. If Excel writer available, also writes each table to its own sheet.
    excel_writer_holder: {"writer": ExcelWriter or None}
    excel_ok_holder: {"ok": bool}
    sheet_count_holder: {"count": int} to ensure unique sheet names
    """
    if not tables:
        return 0

    page_dir = ensure_dir(tables_dir / f"page-{page_no}")
    saved = 0
    for idx, df in enumerate(tables, start=1):
        # Save CSV
        csv_path = page_dir / f"table-{idx}.csv"
        df.to_csv(csv_path, index=False, header=False, encoding="utf-8-sig")
        saved += 1

        # Save to Excel sheet if possible
        if excel_ok_holder["ok"] and excel_writer_holder["writer"] is not None:
            try:
                # Keep sheet name short and valid
                base_name = clean_sheet_name(f"p{page_no}_t{idx}")
                # Ensure uniqueness if many sheets
                sheet_count_holder["count"] += 1
                sheet_name = base_name
                if sheet_count_holder["count"] > 0:
                    # Append a suffix if we somehow collide (Excel will still enforce)
                    sheet_name = clean_sheet_name(f"{base_name}_{sheet_count_holder['count']}")
                df_to_write = df.copy()
                df_to_write.columns = [f"col_{i+1}" for i in range(df_to_write.shape[1])]
                df_to_write.to_excel(excel_writer_holder["writer"], sheet_name=sheet_name, index=False)
            except Exception:
                # If Excel writing fails midway, turn off Excel mode to avoid repeated errors
                excel_ok_holder["ok"] = False
                excel_writer_holder["writer"] = None

    return saved

def write_combined_text(combined_texts: list, out_dir: Path):
    combined_path = out_dir / "text_combined.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("\n".join(combined_texts))

# ---------------------------- MAIN -------------------------------

def main():
    pdf_path = input("Enter the PDF path: ").strip().strip('"').strip("'")
    if not pdf_path:
        print("No PDF path provided.")
        sys.exit(1)
    if not os.path.isfile(pdf_path):
        print("PDF not found:", pdf_path)
        sys.exit(1)

    # Output root folder
    out_root = ensure_dir(Path("extracted_output"))
    # Per-run subfolder named after the PDF file
    pdf_stem = Path(pdf_path).stem
    run_dir = ensure_dir(out_root / pdf_stem)

    text_dir = ensure_dir(run_dir / "text")
    text_pages_dir = ensure_dir(text_dir / "pages")
    tables_dir = ensure_dir(run_dir / "tables")
    images_dir = ensure_dir(run_dir / "images")
    index_rows = []  # summary

    # Open documents
    doc = fitz.open(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
    print(f"Total pages detected: {total_pages}")

    # Page selection
    print("\nSelect pages to extract:")
    print(" - Type 'all' for all pages")
    print(" - Single page (0-indexed), e.g. '10'")
    print(" - Range, e.g. '0-5'")
    print(" - List, e.g. '0,3,7' or mix like '0-2,5,9-11'")
    page_choice = input("Pages: ").strip()
    pages = page_list_from_input(page_choice, total_pages)
    if not pages:
        print("No valid pages selected.")
        sys.exit(0)

    # What to extract
    print("\nWhat to extract? Choose any (comma separated): text, tables, images, all")
    what = input("Extract: ").strip().lower()
    if what == "all":
        extract_text_flag = extract_tables_flag = extract_images_flag = True
    else:
        parts = {w.strip() for w in what.split(",")}
        extract_text_flag = "text" in parts
        extract_tables_flag = "tables" in parts
        extract_images_flag = "images" in parts
        if not any([extract_text_flag, extract_tables_flag, extract_images_flag]):
            print("Nothing selected to extract.")
            sys.exit(0)

    # Prepare Excel writer (optional)
    excel_writer_holder = {"writer": None}
    excel_ok_holder = {"ok": False}
    sheet_count_holder = {"count": 0}
    if extract_tables_flag:
        try:
            excel_writer = pd.ExcelWriter(run_dir / "tables.xlsx", engine="openpyxl")
            excel_writer_holder["writer"] = excel_writer
            excel_ok_holder["ok"] = True
        except Exception:
            # No openpyxl or failure → fall back to CSV-only
            excel_writer_holder["writer"] = None
            excel_ok_holder["ok"] = False

    combined_texts = []

    # Extraction loop
    for p in pages:
        print(f"\n--- Extracting page {p} ---")
        row = {"page": p, "text_chars": 0, "tables_found": 0, "images_found": 0}

        # TEXT
        if extract_text_flag:
            txt = extract_text_for_page(doc, p)
            save_text(p, txt, text_pages_dir, combined_texts)
            row["text_chars"] = len(txt)

        # TABLES
        if extract_tables_flag:
            dfs = extract_tables_for_page(pdf_path, p + 1)  # Camelot is 1-indexed
            saved_tables = save_tables(p, dfs, tables_dir, excel_writer_holder, excel_ok_holder, sheet_count_holder)
            row["tables_found"] = saved_tables

        # IMAGES
        if extract_images_flag:
            img_count = extract_images_for_page(doc, p, images_dir)
            row["images_found"] = img_count

        index_rows.append(row)

    # Finish text combined
    if extract_text_flag and combined_texts:
        write_combined_text(combined_texts, text_dir)

    # Finish Excel
    if extract_tables_flag and excel_writer_holder["writer"] is not None and excel_ok_holder["ok"]:
        try:
            excel_writer_holder["writer"].close()
        except Exception:
            pass

    # Write index CSV
    index_df = pd.DataFrame(index_rows)
    index_df.to_csv(run_dir / "index_summary.csv", index=False, encoding="utf-8-sig")

    print("\n=== DONE ===")
    print(f"Output folder: {run_dir.resolve()}")
    print("Artifacts generated (depending on your choices):")
    print(f" - Text: {text_dir}")
    print(f" - Tables (CSV per table + optional tables.xlsx): {tables_dir} and {run_dir / 'tables.xlsx'}")
    print(f" - Images: {images_dir}")
    print(f" - Summary: {run_dir / 'index_summary.csv'}")

if __name__ == "__main__":
    main()
