#!/usr/bin/env python3
# coding: utf-8

"""
Combined PDF OCR Script

This script adds OCR text layer to PDF files that don't have embedded text.
It can process individual files or recursively scan directories.

Features:
- Uses Tesseract for OCR via pytesseract
- Can check if PDFs already have text without modifying them
- Option to repair damaged PDFs using Ghostscript
- Supports single file or recursive directory processing

Usage:
    Single file:
    ./pdf_ocr_combined.py --input input.pdf --output output.pdf

    Directory (recursive):
    ./pdf_ocr_combined.py --dir /path/to/directory [--check-only] [--repair]
"""

import os
import sys
import argparse
import subprocess
from PyPDF2 import PdfWriter, PdfReader
from PyPDF2.errors import PdfReadError
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

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
    except IndexError as e:
        print(f"List index out of range error processing the file {pdf_path}: {e}")
        return False
    except Exception as e:
        print(f"General error processing the file {pdf_path}: {e}")
        return False

def repair_pdf(pdf_path):
    """Attempts to repair the PDF using Ghostscript."""
    repaired_pdf_path = pdf_path.replace(".pdf", "_repaired.pdf")
    try:
        subprocess.run(['gs', '-o', repaired_pdf_path, '-sDEVICE=pdfwrite', '-dPDFSETTINGS=/prepress', pdf_path], check=True)
        os.replace(repaired_pdf_path, pdf_path)
        print(f"PDF repaired successfully: {pdf_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"PDF repair failed for {pdf_path}: {e}")
        if os.path.exists(repaired_pdf_path):
            os.remove(repaired_pdf_path)
        return False

def add_ocr_to_pdf(input_pdf, output_pdf):
    """Adds OCR layer to PDF using Tesseract and PDF2Image."""
    try:
        # Convert PDF to images with specific DPI
        images = convert_from_path(input_pdf, dpi=300)
        pdf_writer = PdfWriter()
        pdf_reader = PdfReader(input_pdf)
        
        for i, image in enumerate(images):
            # Get original page dimensions
            original_page = pdf_reader.pages[i]
            width = float(original_page.mediabox.width)
            height = float(original_page.mediabox.height)
            
            # Resize image to match original dimensions
            image = image.resize((int(width), int(height)), Image.Resampling.LANCZOS)
            
            # Perform OCR with specific DPI setting
            text = pytesseract.image_to_pdf_or_hocr(
                image,
                extension='pdf',
                config='--dpi 300'
            )
            
            temp_pdf = f'temp_ocr_{i}.pdf'
            with open(temp_pdf, 'wb') as f:
                f.write(text)
            
            ocr_reader = PdfReader(temp_pdf)
            page = pdf_reader.pages[i]
            
            # Scale OCR layer to match original page
            ocr_page = ocr_reader.pages[0]
            ocr_page.scale_to(width, height)
            
            page.merge_page(ocr_page)
            pdf_writer.add_page(page)
            os.remove(temp_pdf)
        
        with open(output_pdf, 'wb') as f:
            pdf_writer.write(f)
        
        print(f"OCR successful for: {output_pdf}")
        return True
    except Exception as e:
        print(f"Error processing the file {input_pdf}: {e}")
        return False

def process_pdf(pdf_path, output_path=None, check_only=False, repair=False):
    """Processes a single PDF file - checks, repairs, or adds OCR."""
    if check_only:
        if has_embedded_text(pdf_path):
            print(f"The file contains text: {pdf_path}")
        else:
            print(f"The file does not contain text: {pdf_path}")
        return True
    
    # If output not specified, use input path as output (overwrite original)
    if output_path is None:
        output_path = pdf_path
        temp_output_path = pdf_path.replace(".pdf", "_temp.pdf")
    else:
        temp_output_path = output_path
    
    # Only process files without text
    if not has_embedded_text(pdf_path):
        try:
            success = add_ocr_to_pdf(pdf_path, temp_output_path)
            
            # If successful and we're overwriting the original file
            if success and output_path == pdf_path:
                os.replace(temp_output_path, pdf_path)
            
            return success
        except Exception as e:
            print(f"Error processing the file {pdf_path}: {e}")
            if repair:
                print(f"Attempting to repair the file: {pdf_path}")
                if repair_pdf(pdf_path):
                    # Retry after repair
                    return process_pdf(pdf_path, output_path, check_only=False, repair=False)
            return False
    else:
        print(f"Text already present in: {pdf_path}. Skipping file.")
        return True

def process_directory(directory, check_only=False, repair=False):
    """Recursively processes or checks all PDFs in a directory."""
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                
                if check_only:
                    process_pdf(pdf_path, check_only=True)
                    continue
                
                if has_embedded_text(pdf_path):
                    print(f"Text already present in: {pdf_path}. Skipping file.")
                    skipped_count += 1
                    continue
                
                result = process_pdf(pdf_path, repair=repair)
                if result:
                    success_count += 1
                else:
                    failure_count += 1
    
    if not check_only:
        print(f"\nSummary:")
        print(f"  Successfully processed: {success_count}")
        print(f"  Failed: {failure_count}")
        print(f"  Skipped (text already present): {skipped_count}")

def main():
    parser = argparse.ArgumentParser(description='Add OCR layer to PDF files')
    
    # Create mutually exclusive group for input mode
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='Single input PDF file')
    input_group.add_argument('--dir', help='Process all PDFs in directory recursively')
    
    # Other arguments
    parser.add_argument('--output', help='Output PDF file (only for single file mode)')
    parser.add_argument('--check-only', action='store_true', help='Only check if PDFs have text without modifying')
    parser.add_argument('--repair', action='store_true', help='Try to repair damaged PDFs')
    
    args = parser.parse_args()
    
    # Process a single file
    if args.input:
        if args.output and args.check_only:
            parser.error("--output cannot be used with --check-only")
            
        process_pdf(args.input, args.output, check_only=args.check_only, repair=args.repair)
    
    # Process a directory recursively
    elif args.dir:
        if args.output:
            parser.error("--output cannot be used with --dir (directory mode)")
            
        if not os.path.isdir(args.dir):
            print(f"The specified directory does not exist: {args.dir}")
            sys.exit(1)
            
        process_directory(args.dir, check_only=args.check_only, repair=args.repair)

if __name__ == "__main__":
    main()