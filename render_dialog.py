#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

import json
import os
import sys
from datetime import datetime
import re

def read_data(file_path):
    # [unchanged]
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
    # [unchanged]
    try:
        match = re.search(r'\{.*\}', line)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        return None

def parse_dialogs(data):
    # [unchanged]
    dialogs = []
    for entry in data:
        try:
            text = entry.get("text", "[Kein Text]")
            sender = entry.get("sender", "[Unbekannter Sprecher]")
            created_at = entry.get("created_at", "1970-01-01T00:00:00Z")

            dialogs.append({
                "text": clean_text(text),
                "speaker": sender,
                "date": parse_date(created_at),
            })
        except Exception as e:
            print(f"Fehler beim Verarbeiten des Eintrags: {entry}. Fehler: {e}")
    return sorted(dialogs, key=lambda x: x["date"])

def clean_text(text):
    # Replace quotation marks
    text = re.sub(r'"([^"]*)"', r'``\1\'\'', text)
    
    # Erkennen von Listen mit Spiegelstrichen
    lines = text.split('\n')
    in_list = False
    cleaned_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('- '):
            if not in_list:
                cleaned_lines.append('\\vspace{0.5\\baselineskip}\\begin{itemize}\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}')
                in_list = True
            cleaned_lines.append('\\item ' + stripped_line[2:])
        else:
            if in_list:
                cleaned_lines.append('\\end{itemize}\\vspace{0.5\\baselineskip}')
                in_list = False
            cleaned_lines.append(stripped_line)
    
    if in_list:
        cleaned_lines.append('\\end{itemize}\\vspace{0.5\\baselineskip}')
    
    return '\n'.join(cleaned_lines).strip()

def parse_date(date_str):
    # [unchanged]
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
    latex_content += "\\section*{Dialog}\n"

    for dialog in dialogs:
        # Escape special LaTeX characters in speaker name
        speaker = dialog['speaker'].replace('_', '\\_').replace('&', '\\&')
        latex_content += f"\\textbf{{{speaker}}} ({dialog['date'].strftime('%d.%m.%Y %H:%M')}):\\\\\n"
        latex_content += f"{dialog['text']}\\\\\n\\bigskip\n"

    latex_content += "\\end{document}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)

# [Rest des Skripts bleibt unverändert]
def compile_latex(latex_path):
    os.system(f"pdflatex -interaction=nonstopmode -output-directory={os.path.dirname(latex_path)} {latex_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_json>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.dirname(input_file)
    output_latex = os.path.join(output_dir, f"{base_name}.tex")
    output_pdf = os.path.join(output_dir, f"{base_name}.pdf")

    data = read_data(input_file)
    dialogs = parse_dialogs(data)

    generate_latex(dialogs, output_latex)
    print(f"LaTeX-Datei erstellt: {output_latex}")

    compile_latex(output_latex)
    print(f"PDF erstellt: {output_pdf}")