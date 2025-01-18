#!/usr/bin/env python3
# coding: utf-8

import json
import os
import sys
from datetime import datetime
import re

def read_data(file_path):
    # Gleiche Implementierung wie im Original
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
    # Gleiche Implementierung wie im Original
    try:
        match = re.search(r'\{.*\}', line)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        return None

def parse_dialogs(data):
    # Gleiche Implementierung wie im Original
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
    # Neue Implementierung für Markdown
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
    # Gleiche Implementierung wie im Original
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return datetime(1970, 1, 1)

def generate_markdown(dialogs, output_path):
    markdown_content = "# Dialog\n\n"

    for dialog in dialogs:
        speaker = dialog['speaker']
        date_str = dialog['date'].strftime('%d.%m.%Y %H:%M')
        markdown_content += f"## {speaker} ({date_str}):\n"
        markdown_content += f"{dialog['text']}\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

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
    output_markdown = os.path.join(output_dir, f"{base_name}.md")

    data = read_data(input_file)
    dialogs = parse_dialogs(data)

    generate_markdown(dialogs, output_markdown)
    print(f"Markdown-Datei erstellt: {output_markdown}")