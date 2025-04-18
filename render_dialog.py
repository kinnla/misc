#!/usr/bin/env python3
# coding: utf-8

import json
import os
import sys
import argparse
from datetime import datetime
import re

def read_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            for line in content.splitlines():
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Fehler beim Parsen der Zeile: {line[:50]}... ({str(e)})")
                        partial_data = attempt_partial_parse(line)
                        if partial_data:
                            data.append(partial_data)
    return data

def attempt_partial_parse(line):
    try:
        match = re.search(r'\{.*\}', line)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        return None

def parse_dialogs(data):
    dialogs = []
    for entry in data:
        try:
            text = entry.get("text", "[Kein Text]")
            sender = entry.get("sender", "[Unbekannter Sprecher]")
            created_at = entry.get("created_at", "1970-01-01T00:00:00Z")

            dialogs.append({
                "text": text,
                "speaker": sender,
                "date": parse_date(created_at),
            })
        except Exception as e:
            print(f"Fehler beim Verarbeiten des Eintrags: {entry}. Fehler: {e}")
    return sorted(dialogs, key=lambda x: x["date"])

def clean_text_latex(text):
    lines = text.split('\n')
    in_list = False
    cleaned_lines = []
    list_number = 0
    
    for line in lines:
        stripped_line = line.strip()
        # Check if line starts a new numbered section
        if stripped_line.startswith(('1. ', '2. ', '3. ')):
            # Add the number and text before the list
            list_number += 1
            header_text = stripped_line[3:]  # Skip the "n. " part
            cleaned_lines.append(f'{list_number}. {header_text}')
        # Check if it's a bullet point
        elif stripped_line.startswith('- '):
            if not in_list:
                cleaned_lines.append('\\begin{itemize}\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}')
                in_list = True
            cleaned_lines.append('\\item ' + stripped_line[2:])
        else:
            if in_list:
                cleaned_lines.append('\\end{itemize}')
                in_list = False
            if stripped_line:  # Only add backslashes for non-empty lines
                cleaned_lines.append(stripped_line + '\\\\')
    
    if in_list:
        cleaned_lines.append('\\end{itemize}')
    
    return '\n'.join(cleaned_lines).strip()

def clean_text_markdown(text):
    lines = text.split('\n')
    cleaned_lines = []
    in_list = False
    
    for line in lines:
        stripped_line = line.strip()
        # Aufzählungspunkte oder nummerierte Liste
        if stripped_line.startswith(('- ', '1. ', '2. ', '3. ')):
            if not in_list:
                in_list = True
            cleaned_lines.append(stripped_line)
        # Normaler Text
        elif stripped_line:
            if in_list:
                cleaned_lines.append('')  # Leerzeile nach Liste
                in_list = False
            cleaned_lines.append(stripped_line)
    
    return '\n'.join(cleaned_lines).strip()

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return datetime(1970, 1, 1)

def generate_latex(dialogs, output_path):
    latex_content = "\\documentclass[a4paper,12pt]{article}\n"
    latex_content += "\\usepackage[utf8]{inputenc}\n"
    latex_content += "\\usepackage[ngerman]{babel}\n"
    latex_content += "\\usepackage[margin=2.5cm]{geometry}\n"
    latex_content += "\\begin{document}\n"
    latex_content += "\\section*{Dialog}\n\n"

    for dialog in dialogs:
        speaker = dialog['speaker'].replace('_', '\\_').replace('&', '\\&')
        date_str = dialog['date'].strftime('%d.%m.%Y %H:%M')
        latex_content += f"\\noindent\\textbf{{{speaker}}} ({date_str}):\\\\\n"
        text = clean_text_latex(dialog['text'])
        latex_content += f"{text}\\\\\n"

    latex_content += "\\end{document}"
    
    # Replace quotes
    latex_content = re.sub(r'"([^"]*)"', r"``\1''", latex_content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    return output_path

def compile_latex(latex_path):
    os.system(f"pdflatex -interaction=nonstopmode -output-directory={os.path.dirname(latex_path)} {latex_path}")
    return os.path.splitext(latex_path)[0] + '.pdf'

def generate_markdown(dialogs, output_path):
    markdown_content = "# Dialog\n\n"

    for dialog in dialogs:
        speaker = dialog['speaker']
        date_str = dialog['date'].strftime('%d.%m.%Y %H:%M')
        markdown_content += f"## {speaker} ({date_str}):\n"
        text = clean_text_markdown(dialog['text'])
        markdown_content += f"{text}\n\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Konvertiere JSON-Dialog in Markdown oder LaTeX')
    parser.add_argument('input_file', help='Pfad zur JSON-Eingabedatei')
    parser.add_argument('--format', '-f', choices=['markdown', 'latex'], default='markdown',
                      help='Ausgabeformat: markdown oder latex (Standard: markdown)')
    parser.add_argument('--compile', '-c', action='store_true',
                      help='Bei LaTeX-Format: PDF kompilieren')
    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print(f"Fehler: Datei '{args.input_file}' existiert nicht.")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(args.input_file))[0]
    output_dir = os.path.dirname(args.input_file)

    data = read_data(args.input_file)
    dialogs = parse_dialogs(data)

    if args.format == 'markdown':
        output_file = os.path.join(output_dir, f"{base_name}.md")
        output_path = generate_markdown(dialogs, output_file)
        print(f"Markdown-Datei erstellt: {output_path}")
    else:  # latex
        output_file = os.path.join(output_dir, f"{base_name}.tex")
        output_path = generate_latex(dialogs, output_file)
        print(f"LaTeX-Datei erstellt: {output_path}")
        
        if args.compile:
            pdf_path = compile_latex(output_path)
            print(f"PDF erstellt: {pdf_path}")

if __name__ == "__main__":
    main()