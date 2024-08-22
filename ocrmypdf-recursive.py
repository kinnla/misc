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

def has_embedded_text(pdf_path):
    """Prüft, ob eine PDF-Datei eingebetteten Text enthält."""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            if page.extract_text().strip():
                return True
        return False
    except Exception as e:
        print(f"Fehler beim Lesen der PDF-Datei {pdf_path}: {e}")
        return False

def process_pdf_with_ocrmypdf(pdf_path):
    """Führt OCR mit ocrmypdf durch und überschreibt die Originaldatei."""
    temp_output_path = pdf_path.replace(".pdf", "_temp.pdf")
    try:
        ocrmypdf.ocr(pdf_path, temp_output_path)
        os.replace(temp_output_path, pdf_path)
        print(f"OCR erfolgreich für: {pdf_path}")
    except Exception as e:
        print(f"OCR fehlgeschlagen für {pdf_path}: {e}")
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

def process_directory(directory):
    """Geht rekursiv durch ein Verzeichnis und bearbeitet alle PDFs ohne eingebetteten Text."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                if not has_embedded_text(pdf_path):
                    print(f"Kein Text gefunden in: {pdf_path}. OCR wird durchgeführt.")
                    process_pdf_with_ocrmypdf(pdf_path)
                else:
                    print(f"Text bereits vorhanden in: {pdf_path}. Überspringe Datei.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Verwendung: python script.py /Pfad/zum/Verzeichnis")
        sys.exit(1)

    directory_to_scan = sys.argv[1]

    if not os.path.isdir(directory_to_scan):
        print(f"Das angegebene Verzeichnis existiert nicht: {directory_to_scan}")
        sys.exit(1)

    process_directory(directory_to_scan)