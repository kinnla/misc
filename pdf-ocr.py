#!/usr/bin/env python3

from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os
from PyPDF2 import PdfWriter, PdfReader
import argparse

def add_ocr_to_pdf(input_pdf, output_pdf):
    """Fügt OCR-Layer zu PDF hinzu / Adds OCR layer to PDF"""
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add OCR layer to PDF')
    parser.add_argument('input', help='Input PDF file')
    parser.add_argument('output', help='Output PDF file')
    args = parser.parse_args()
    
    add_ocr_to_pdf(args.input, args.output)