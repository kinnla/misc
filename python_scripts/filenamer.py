# coding: utf-8

# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "PyMuPDF>=1.24.0",
#     "ollama>=0.4.0",
#     "PyYAML>=6.0",
# ]
# ///

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
import shutil
import subprocess
import sys
import time
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

{examples}

If the doc is in English, use English terms. Wenn das Dokument auf Deutsch ist, dann verwende Deutsche Begriffe.

As a reply to this prompt, please be short and concise, and only reply with the file name. Thanks in advance!
""",
    'example_filenames': [
        "2025-04-15_Microsoft-QuarterlyReport.pdf",
        "2025-03-22_Amazon-OrderConfirmation.pdf",
        "2025-05-01_EDP_SA-Dividends.pdf",
        "Microsoft-ProductBrochure.pdf",
        "Amazon-UserManual.pdf",
        "EDP_SA-GeneralInformation.pdf"
    ]
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

def _is_ollama_responsive(client):
    try:
        client.ps()
        return True
    except Exception as e:
        log(f"Ollama is not responsive yet: {e}")
        return False

def ensure_ollama_ready(config):
    """
    Ensure the Ollama server is running and the configured model is available.
    Returns an Ollama client or raises RuntimeError with a user-facing message.
    """
    client = ollama.Client()

    if _is_ollama_responsive(client):
        log("Ollama is already running")
    else:
        ollama_binary = shutil.which("ollama")
        if not ollama_binary:
            raise RuntimeError(
                "Ollama CLI not found in PATH. Please install Ollama from https://ollama.com/download"
            )

        log(f"Starting Ollama server with: {ollama_binary} serve")
        try:
            subprocess.Popen(
                [ollama_binary, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start Ollama automatically: {e}") from e

        startup_timeout_seconds = 15
        poll_interval_seconds = 0.5
        deadline = time.time() + startup_timeout_seconds

        while time.time() < deadline:
            if _is_ollama_responsive(client):
                log("Ollama started successfully")
                break
            time.sleep(poll_interval_seconds)
        else:
            raise RuntimeError(
                "Failed to start Ollama automatically. Please check that Ollama can run on this machine."
            )

    try:
        client.show(config['model'])
    except Exception as e:
        raise RuntimeError(
            f"Ollama is running, but the model '{config['model']}' is not available: {e}"
        ) from e

    return client

def get_new_filename(client, prompt, content, config):
    # Truncate content if it exceeds max_characters
    max_chars = config['max_characters']
    encoded_content = content.encode('utf-8')
    if len(encoded_content) > max_chars:
        log(f"File content exceeds context length: {len(encoded_content)}. Truncating to {max_chars} characters.")
        content = encoded_content[:max_chars].decode('utf-8', errors='ignore')

    # Format examples from config
    example_filenames = config.get('example_filenames', [])
    if example_filenames:
        examples_with_dates = [ex for ex in example_filenames if '_' in ex and ex[0].isdigit()]
        examples_without_dates = [ex for ex in example_filenames if not ('_' in ex and ex[0].isdigit())]

        examples_text = ""
        if examples_with_dates:
            examples_text += "Examples with dates:\n"
            examples_text += "\n".join(f"- {ex}" for ex in examples_with_dates)
            examples_text += "\n\n"
        if examples_without_dates:
            examples_text += "Examples without dates:\n"
            examples_text += "\n".join(f"- {ex}" for ex in examples_without_dates)
    else:
        examples_text = ""

    formatted_prompt = prompt.format(pdf=content, examples=examples_text)
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

    raise RuntimeError(f"Unexpected response format: {response}")

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

def prepare_rename_operation(original_path, new_name, config):
    """
    Prepare a rename operation without actually renaming the file.
    Returns a dict with original_path, new_name (cleaned and validated), and directory.
    Returns None if the filename is invalid.
    """
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
        return None

    directory = os.path.dirname(original_path)
    current_filename = os.path.basename(original_path)

    return {
        'original_path': original_path,
        'current_filename': current_filename,
        'new_name': new_name,
        'directory': directory
    }

def execute_rename(rename_op, config):
    """
    Execute a single rename operation with duplicate checking.
    Returns True if successful, False otherwise.
    """
    original_path = rename_op['original_path']
    new_name = rename_op['final_name']
    directory = rename_op['directory']
    new_path = os.path.join(directory, new_name)

    # Check if the file already has the correct name
    if os.path.basename(original_path) == new_name:
        print(f"already correct: {new_name}")
        log(f"File already has correct name: {new_name}")
        return True

    # Try to rename, handling potential duplicates from other files in directory
    try:
        # Check if target exists (could be another file that wasn't in our batch)
        if os.path.exists(new_path):
            # Generate a unique name
            unique_name = generate_unique_filename(directory, new_name, config)
            new_path = os.path.join(directory, unique_name)
            log(f"Target exists, using unique name: {unique_name}")

        os.rename(original_path, new_path)
        print(f"{os.path.basename(original_path)} -> {os.path.basename(new_path)}")
        return True
    except FileExistsError:
        # Race condition - file was created between our check and rename
        unique_name = generate_unique_filename(directory, new_name, config)
        new_path = os.path.join(directory, unique_name)
        try:
            os.rename(original_path, new_path)
            print(f"{os.path.basename(original_path)} -> {os.path.basename(new_path)}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def process_files(file_paths, config):
    """
    Process all files in two phases:
    1. Generate all new filenames
    2. Check for duplicates and rename files
    """
    prompt = config['prompt']
    rename_operations = []

    # Phase 1: Generate all new filenames
    total_files = len([f for f in file_paths if f.lower().endswith(".pdf")])
    print(f"Processing {total_files} PDF file(s)...")
    log("Phase 1: Generating new filenames for all files...")

    try:
        client = ensure_ollama_ready(config)
    except RuntimeError as e:
        print(f"Cannot analyze files: {e}")
        return

    processed_count = 0
    for file_path in file_paths:
        if file_path.lower().endswith(".pdf"):
            processed_count += 1
            print(f"Analyzing file {processed_count}/{total_files}: {os.path.basename(file_path)}")
            content = read_pdf(file_path)
            if content:
                try:
                    new_name = get_new_filename(client, prompt, content, config)
                except Exception as e:
                    print(f"An error occurred while getting the new filename from the LLM: {e}")
                    return
                rename_op = prepare_rename_operation(file_path, new_name, config)
                if rename_op:
                    rename_operations.append(rename_op)

    if not rename_operations:
        log("No rename operations to perform")
        return

    # Phase 2: Check for duplicates in the planned new names and resolve them
    log("Phase 2: Checking for duplicate filenames in batch...")
    name_counts = {}
    for op in rename_operations:
        # Group by directory to handle duplicates per directory
        dir_key = op['directory']
        if dir_key not in name_counts:
            name_counts[dir_key] = {}

        new_name = op['new_name']
        if new_name not in name_counts[dir_key]:
            name_counts[dir_key][new_name] = []
        name_counts[dir_key][new_name].append(op)

    # Assign final names, adding indices where needed
    for dir_key, names in name_counts.items():
        for new_name, ops in names.items():
            if len(ops) == 1:
                # No duplicates, check if current filename matches
                op = ops[0]
                if op['current_filename'] == new_name:
                    # File already has correct name
                    op['final_name'] = new_name
                else:
                    # Check if a different file in the directory already has this name
                    target_path = os.path.join(dir_key, new_name)
                    if os.path.exists(target_path):
                        # A file exists with this name (not in our batch)
                        base, ext = os.path.splitext(new_name)
                        op['final_name'] = f"{base}_1{ext}"
                        log(f"File exists in directory, adding index: {new_name} -> {op['final_name']}")
                    else:
                        op['final_name'] = new_name
            else:
                # Multiple files want the same name - assign indices
                log(f"Found {len(ops)} files that want the name '{new_name}'")
                for idx, op in enumerate(ops):
                    if idx == 0 and op['current_filename'] == new_name:
                        # First one already has the correct name
                        op['final_name'] = new_name
                    elif idx == 0:
                        # First one gets the base name if not already taken
                        target_path = os.path.join(dir_key, new_name)
                        if os.path.exists(target_path) and os.path.basename(op['original_path']) != new_name:
                            base, ext = os.path.splitext(new_name)
                            op['final_name'] = f"{base}_1{ext}"
                        else:
                            op['final_name'] = new_name
                    else:
                        # Subsequent ones get indexed names
                        base, ext = os.path.splitext(new_name)
                        op['final_name'] = f"{base}_{idx}{ext}"
                        log(f"Duplicate resolved: {new_name} -> {op['final_name']}")

    # Phase 3: Execute all renames
    log("Phase 3: Executing rename operations...")
    total_renames = len(rename_operations)
    print(f"\nRenaming files...")
    for idx, op in enumerate(rename_operations, 1):
        print(f"Renaming {idx}/{total_renames}: ", end="")
        execute_rename(op, config)

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
