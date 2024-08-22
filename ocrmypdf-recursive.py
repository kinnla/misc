#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

"""
This script queries a directory tree and recursively processes PDFs
that do not contain embedded text. The text of this PDF will be extracted
via ocrmypdf. The file will be replaced by a copy with that text embedded.

Usage:
./ocrmypdf-recursive.py directory
"""

import os
import sys
import ocrmypdf
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

def has_embedded_text(pdf_path):
    """Checks if a PDF file contains embedded text."""
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            try:
                reader.decrypt('')
            except:
                print(f"The file is encrypted and cannot be read: {pdf_path}")
                return True  # Skip this file
        for page in reader.pages:
            if page.extract_text().strip():
                return True
        return False
    except PdfReadError as e:
        print(f"Error reading the PDF file {pdf_path}: {e}")
        return False
    except Exception as e:
        print(f"General error processing the file {pdf_path}: {e}")
        return False

def process_pdf_with_ocrmypdf(pdf_path, check_only=False):
    """Performs OCR with ocrmypdf and overwrites the original file or just checks."""
    if check_only:
        if has_embedded_text(pdf_path):
            print(f"The file contains text: {pdf_path}")
        else:
            print(f"The file does not contain text: {pdf_path}")
    else:
        if not has_embedded_text(pdf_path):
            temp_output_path = pdf_path.replace(".pdf", "_temp.pdf")
            try:
                ocrmypdf.ocr(pdf_path, temp_output_path)
                os.replace(temp_output_path, pdf_path)
                print(f"OCR successful for: {pdf_path}")
            except Exception as e:
                print(f"OCR failed for {pdf_path}: {e}")
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
        else:
            print(f"Text already present in: {pdf_path}. Skipping file.")

def process_directory(directory, check_only=False):
    """Recursively processes or checks all PDFs in a directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                process_pdf_with_ocrmypdf(pdf_path, check_only=check_only)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script.py /path/to/directory [--check-only]")
        sys.exit(1)

    directory_to_scan = sys.argv[1]
    check_only = "--check-only" in sys.argv

    if not os.path.isdir(directory_to_scan):
        print(f"The specified directory does not exist: {directory_to_scan}")
        sys.exit(1)

    process_directory(directory_to_scan, check_only=check_only)