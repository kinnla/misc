#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

import json
import os
import sys
from datetime import datetime
import re

# Daten einlesen
def read_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        try:
            # Versuche, das gesamte JSON zu laden
            data = json.loads(content)
            # Falls es ein einzelnes Objekt ist, wandle es in eine Liste um
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            # Datei enthält mehrere JSON-Objekte (Fragment)
            for line in content.splitlines():
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Fehler beim Parsen der Zeile: {line[:50]}... ({str(e)})")
                        # Teile der Zeile extrahieren und nutzen
                        partial_data = attempt_partial_parse(line)
                        if partial_data:
                            data.append(partial_data)
    return data

# Versuche, Teile eines fehlerhaften JSON-Objekts zu extrahieren
def attempt_partial_parse(line):
    try:
        match = re.search(r'\{.*\}', line)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        return None

# Objektstruktur generieren
def parse_dialogs(data):
    dialogs = []
    for entry in data:
        try:
            # Überprüfe, ob notwendige Felder existieren
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

# Text bereinigen
def clean_text(text):
    text = re.sub(r'\n', ' ', text)  # Zeilenumbrüche ersetzen
    return text.strip()

# Datum parsen
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return datetime(1970, 1, 1)  # Fallback-Datum

# LaTeX-Datei generieren
def generate_latex(dialogs, output_path):
    latex_content = "\\documentclass[a4paper,12pt]{article}\n"
    latex_content += "\\usepackage[utf8]{inputenc}\n"
    latex_content += "\\usepackage[ngerman]{babel}\n"
    latex_content += "\\begin{document}\n"
    latex_content += "\\section*{Dialog}\n"

    for dialog in dialogs:
        latex_content += f"\\textbf{{{dialog['speaker']}}} ({dialog['date'].strftime('%d.%m.%Y %H:%M')}):\\\\\n"
        latex_content += f"{dialog['text']}\\\\[1em]\n"

    latex_content += "\\end{document}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)

# LaTeX kompilieren
def compile_latex(latex_path):
    os.system(f"pdflatex -interaction=nonstopmode -output-directory={os.path.dirname(latex_path)} {latex_path}")

# Hauptprogramm
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

    # Daten verarbeiten
    data = read_data(input_file)
    dialogs = parse_dialogs(data)

    # LaTeX-Datei generieren
    generate_latex(dialogs, output_latex)
    print(f"LaTeX-Datei erstellt: {output_latex}")

    # LaTeX kompilieren
    compile_latex(output_latex)
    print(f"PDF erstellt: {output_pdf}")
