#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

"""
This script reads the contents of a PDF and then renames it with an adequate name. 
We use Llama 3.1 as LLM via Ollama.

Usage:
./filenamer.py file.pdf
./filenamer.py directory
"""

import fitz  # PyMuPDF
import argparse
import ollama
import os
import re
import sys

# prompt to be passed to the LLM
prompt = """The following is the contents of a PDF document. Please read it and find
- the company name
- the subject (or "Betreff")
Also check if there is a date mentioned in the document.
>>>
{pdf}
<<<
Now we will construct a new name for the document, according to the following format:
'YYYY-MM-DD_COMPANY-SUBJECT.pdf'

IMPORTANT FILENAME REQUIREMENTS:
1. Use hyphens (-) between words in company names and subjects
2. Use underscores (_) between the date and company, and if needed for clarity
3. Do NOT include any spaces in the filename
4. Avoid special characters except for hyphens and underscores
5. Use dots (.) only for abbreviations, not before the .pdf extension
6. Keep company names concise, abbreviate if very long

Examples:
- 2025-04-15_Microsoft-QuarterlyReport.pdf
- 2025-03-22_Amazon-OrderConfirmation.pdf
- 2025-05-01_EDP_SA-Dividends.pdf (note: no dots before .pdf)

If the doc is in English, use English terms. Wenn das Dokument auf Deutsch ist, dann verwende Deutsche Begriffe.

As a reply to this prompt, please be short and concise, and only reply with the file name. Thanks in advance!
"""

# Maximum context window of the LLM
context_window = 128000

def read_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        content = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            content += page.get_text()
        print(f"Content extracted from {file_path}: {content[:500]}...")  # Debugging-Ausgabe (erste 500 Zeichen)
        return content
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None

def get_new_filename(prompt, content):
    try:
        client = ollama.Client()

        # Truncate content if it exceeds context_window
        encoded_content = content.encode('utf-8')
        if len(encoded_content) > context_window:
            print (f"File content exceeds context length: {len(encoded_content)}. Truncate it to {128000} characters.")
            content = encoded_content[:context_window].decode('utf-8', errors='ignore')
        
        formatted_prompt = prompt.format(pdf=content)  # Formatting the hardcoded prompt
        response = client.generate(prompt=formatted_prompt, model="llama3.1", options={'temperature': 0})

        # Extract the new filename from the 'response' key
        if response and 'response' in response:
            new_filename = response['response'].strip()
            return new_filename
        else:
            print(f"Unexpected response format: {response}")
            return None

    except Exception as e:
        print(f"An error occurred while getting the new filename from the LLM: {e}")
        return None

def validate_filename(filename):
    # Check if the filename only includes alphanumerical characters, hyphens, underscores
    # dots are allowed within the name but the file must end with .pdf
    if re.match(r'^[\w\.-]+\.pdf$', filename):
        return True
    return False

def clean_filename(filename):
    """
    Cleans up invalid filenames, particularly handling dots before the .pdf extension.
    Returns the cleaned filename.
    """
    # If filename doesn't end with .pdf, add it
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    
    # Handle case where there might be dots before the extension
    # Ensure we keep the dots in dates and other valid uses, but avoid dots right before .pdf
    # This handles cases like "Company.Name-Subject.pdf" -> "Company.Name-Subject.pdf"
    # But fixes "Company-Subject..pdf" -> "Company-Subject.pdf"
    clean_name = re.sub(r'\.+\.pdf$', '.pdf', filename)
    
    # Replace spaces with underscores
    clean_name = clean_name.replace(' ', '_')
    
    return clean_name$', filename):
        return True
    return False
    
def clean_filename(filename):
    """
    Cleans up invalid filenames, particularly handling dots before the .pdf extension.
    Returns the cleaned filename.
    """
    # If filename doesn't end with .pdf, add it
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    
    # Handle case where there might be dots before the extension
    # Ensure we keep the dots in dates and other valid uses, but avoid dots right before .pdf
    # This handles cases like "Company.Name-Subject.pdf" -> "Company.Name-Subject.pdf"
    # But fixes "Company-Subject..pdf" -> "Company-Subject.pdf"
    clean_name = re.sub(r'\.+\.pdf$', '.pdf', filename)
    
    # Replace spaces with underscores
    clean_name = clean_name.replace(' ', '_')
    
    return clean_name

def generate_unique_filename(directory, filename):
    base, ext = os.path.splitext(filename)
    unique_filename = filename
    index = 1
    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}_{index}{ext}"
        index += 1
        if index > 9:
            break  # Use a single-digit index
    return unique_filename

def rename_file(original_path, new_name):
    if not new_name.endswith(".pdf"):
        new_name += ".pdf"

    # First clean the filename to handle any invalid characters
    cleaned_name = clean_filename(new_name)
    
    # Still validate, but log if we had to clean it
    if cleaned_name != new_name:
        print(f"Cleaned up filename: {new_name} -> {cleaned_name}")
        new_name = cleaned_name
    
    if not validate_filename(new_name):
        print(f"Invalid filename generated even after cleaning: {new_name}")
        return
    
    directory = os.path.dirname(original_path)
    unique_name = generate_unique_filename(directory, new_name)
    new_path = os.path.join(directory, unique_name)
    try:
        os.rename(original_path, new_path)
        print(f"File renamed to: {new_path}")
    except Exception as e:
        print(f"An error occurred while renaming the file: {e}")

def process_files(file_paths):
    for file_path in file_paths:
        if file_path.lower().endswith(".pdf"):
            content = read_pdf(file_path)
            if content:
                new_name = get_new_filename(prompt, content)
                if new_name:
                    rename_file(file_path, new_name)

def get_all_pdfs(directory):
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            print(f"Checking file: {file}")  # Debugging-Ausgabe
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
                print(f"Found PDF: {file}")  # Debugging-Ausgabe
    return pdf_files


def main():
    parser = argparse.ArgumentParser(description="Rename PDF files based on their content using Llama 3.1 model.")
    parser.add_argument("paths", nargs='+', help="The paths to the PDF files or folders containing PDF files to be renamed")
    args = parser.parse_args()

    all_files = []
    for path in args.paths:
        if not os.path.exists(path):
            print(f"Error: The path '{path}' does not exist.")
            continue

        if os.path.isfile(path) and path.lower().endswith(".pdf"):
            all_files.append(path)
        elif os.path.isdir(path):
            pdf_files = get_all_pdfs(path)
            if not pdf_files:
                print(f"Error: The directory '{path}' is empty or contains no PDF files.")
            else:
                all_files.extend(pdf_files)

    if not all_files:
        print("Error: No valid PDF files found to process.")
    else:
        process_files(all_files)

if __name__ == "__main__":
    if not sys.stdin.isatty():
        input_files = [line.strip() for line in sys.stdin if line.strip().lower().endswith('.pdf')]
        if input_files:
            sys.argv.extend(input_files)
    main()