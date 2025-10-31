# Data Extraction Using Multiple Python Libraries

This repository contains multiple implementations of PDF data extraction using different Python libraries.  
Each script demonstrates how to read, parse, and extract text or images from PDF files with distinct approaches.

---

# Project Structure

Data Extraction/
│
├── 01_pymupdf.py # Extract text and images using PyMuPDF (fitz)
├── 02_pdfplumber.py # Extract structured text and tables using pdfplumber
├── 03_pdf_miner.py # Text extraction using PDFMiner
├── 04_pypdf.py # Basic PDF text extraction using PyPDF
├── pypdf2.py # Extraction and manipulation using PyPDF2
├── data_extraction_using_mul_libraries.py # Combined approach using multiple libraries
├── data_extraction.ipynb # Jupyter notebook version for experimentation
├── extracted_images/ # Folder for images extracted from PDFs
└── venv/ # Virtual environment folder

# Overview

PDF data extraction is a common need in document automation, data mining, and NLP tasks.  
This project explores different libraries and their capabilities for handling PDFs in Python.

# Libraries Used:
- **PyMuPDF (fitz)** – Fast and efficient for text + image extraction  
- **pdfplumber** – Great for structured data and tables  
- **PDFMiner** – Powerful for text layout analysis  
- **PyPDF / PyPDF2** – Lightweight and simple text extraction  

---

# Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Md-AdeebKhan/advanced-data-extraction-tool.git
   cd advanced-data-extraction-tool