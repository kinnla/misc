# coding: utf-8

"""
This script reads the contents of a PDF and then renames it with an adequate name.
We use llama3.1 via Ollama.

Usage:
filenamer file.pdf
filenamer directory
filenamer --config config.yaml file.pdf
"""

import fitz  # PyMuPDF
import argparse
import ollama
import os
import re
import sys
import yaml
from pathlib import Path

# Global verbose flag
VERBOSE = False

# Default configuration
DEFAULT_CONFIG = {
    'model': 'llama3.1',
    'temperature': 0,
    'max_characters': 128000,
    'duplicate_index_limit': 99,
    'prompt': """The following is the contents of a PDF document. Please read it and find:
- the company name
- the subject (or "Betreff")
- the date (if mentioned in the document)

>>>
{pdf}
<<<

Now we will construct a new name for the document, according to the following format:

IF A DATE IS FOUND:
'YYYY-MM-DD_COMPANY-SUBJECT.pdf'

IF NO DATE IS FOUND:
'COMPANY-SUBJECT.pdf'

IMPORTANT FILENAME REQUIREMENTS:
1. Use hyphens (-) between words in company names and subjects
2. Use underscores (_) between the date and company, and if needed for clarity
3. Do NOT include any spaces in the filename
4. Avoid special characters except for hyphens and underscores
5. Use dots (.) only for abbreviations, not before the .pdf extension
6. Keep company names concise, abbreviate if very long
7. If no date is found, omit the date prefix entirely

Examples with dates:
- 2025-04-15_Microsoft-QuarterlyReport.pdf
- 2025-03-22_Amazon-OrderConfirmation.pdf
- 2025-05-01_EDP_SA-Dividends.pdf

Examples without dates:
- Microsoft-ProductBrochure.pdf
- Amazon-UserManual.pdf
- EDP_SA-GeneralInformation.pdf

If the doc is in English, use English terms. Wenn das Dokument auf Deutsch ist, dann verwende Deutsche Begriffe.

As a reply to this prompt, please be short and concise, and only reply with the file name. Thanks in advance!
"""
}

def log(message):
    """Print message only if verbose mode is enabled."""
    if VERBOSE:
        print(message)

def load_config(config_path=None):
    """Load configuration from YAML file or use defaults."""
    config = DEFAULT_CONFIG.copy()

    if config_path is None:
        # Try to find config file in script directory
        script_dir = Path(__file__).parent
        config_path = script_dir / 'filenamer_config.yaml'
    else:
        config_path = Path(config_path)

    if config_path.exists():
        log(f"Loading configuration from: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
                    log("Configuration loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            print("Using default configuration")
    else:
        log(f"Config file not found at {config_path}, using defaults")

    return config

def read_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        content = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            content += page.get_text()
        log(f"Content extracted from {file_path}: {content[:500]}...")
        return content
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None

def get_new_filename(prompt, content, config):
    try:
        client = ollama.Client()

        # Truncate content if it exceeds max_characters
        max_chars = config['max_characters']
        encoded_content = content.encode('utf-8')
        if len(encoded_content) > max_chars:
            log(f"File content exceeds context length: {len(encoded_content)}. Truncating to {max_chars} characters.")
            content = encoded_content[:max_chars].decode('utf-8', errors='ignore')

        formatted_prompt = prompt.format(pdf=content)
        response = client.generate(
            prompt=formatted_prompt,
            model=config['model'],
            options={'temperature': config['temperature']}
        )

        # Extract the new filename from the 'response' key
        if response and 'response' in response:
            new_filename = response['response'].strip()
            log(f"LLM suggested filename: {new_filename}")
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
    
    return clean_name

def generate_unique_filename(directory, filename, config):
    base, ext = os.path.splitext(filename)
    unique_filename = filename
    index = 1
    limit = config.get('duplicate_index_limit', 99)
    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}_{index}{ext}"
        index += 1
        if index > limit:
            log(f"Warning: Reached duplicate filename limit of {limit}")
            break
    return unique_filename

def rename_file(original_path, new_name, config):
    if not new_name.endswith(".pdf"):
        new_name += ".pdf"

    # First clean the filename to handle any invalid characters
    cleaned_name = clean_filename(new_name)

    # Still validate, but log if we had to clean it
    if cleaned_name != new_name:
        log(f"Cleaned up filename: {new_name} -> {cleaned_name}")
        new_name = cleaned_name

    if not validate_filename(new_name):
        print(f"Invalid filename generated even after cleaning: {new_name}")
        return

    directory = os.path.dirname(original_path)
    unique_name = generate_unique_filename(directory, new_name, config)
    new_path = os.path.join(directory, unique_name)
    try:
        os.rename(original_path, new_path)
        print(f"File renamed to: {new_path}")
    except Exception as e:
        print(f"An error occurred while renaming the file: {e}")

def process_files(file_paths, config):
    prompt = config['prompt']
    for file_path in file_paths:
        if file_path.lower().endswith(".pdf"):
            content = read_pdf(file_path)
            if content:
                new_name = get_new_filename(prompt, content, config)
                if new_name:
                    rename_file(file_path, new_name, config)

def get_all_pdfs(directory):
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            log(f"Checking file: {file}")
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
                log(f"Found PDF: {file}")
    return pdf_files


def main():
    global VERBOSE

    parser = argparse.ArgumentParser(
        description="Rename PDF files based on their content using Ollama LLM.",
        epilog="Example: filenamer --verbose file.pdf directory/"
    )
    parser.add_argument("paths", nargs='+', help="The paths to the PDF files or folders containing PDF files to be renamed")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output for debugging")
    parser.add_argument("-c", "--config", help="Path to custom configuration file (YAML format)")
    args = parser.parse_args()

    # Set global verbose flag
    VERBOSE = args.verbose

    # Load configuration
    config = load_config(args.config)

    log(f"Using model: {config['model']}")
    log(f"Temperature: {config['temperature']}")
    log(f"Max characters: {config['max_characters']}")
    log(f"Duplicate index limit: {config['duplicate_index_limit']}")

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
        log(f"Processing {len(all_files)} PDF file(s)")
        process_files(all_files, config)

if __name__ == "__main__":
    if not sys.stdin.isatty():
        input_files = [line.strip() for line in sys.stdin if line.strip().lower().endswith('.pdf')]
        if input_files:
            sys.argv.extend(input_files)
    main()