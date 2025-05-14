#!/usr/bin/env python3
import os
import re
import argparse
import sys

def count_words(text):
    # Entfernt Markdown-Codeblöcke
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Entfernt HTML-Tags
    text = re.sub(r'<.*?>', '', text)
    # Zählt Wörter
    words = re.findall(r'\w+', text)
    return len(words)

def main():
    # Argument-Parser einrichten
    parser = argparse.ArgumentParser(description='Zählt Wörter in Textdateien.')
    parser.add_argument('directory', nargs='?', default='.', 
                        help='Verzeichnis, das durchsucht werden soll (Standard: aktuelles Verzeichnis)')
    args = parser.parse_args()
    
    directory = args.directory
    
    if not os.path.isdir(directory):
        print(f"Fehler: {directory} ist kein gültiges Verzeichnis")
        sys.exit(1)
    
    total_words = 0
    file_counts = {}
    
    text_extensions = ['.md', '.txt', '.text']
    
    # Rekursiv durch alle Unterordner gehen
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in text_extensions:
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                        word_count = count_words(content)
                        file_counts[filepath] = word_count
                        total_words += word_count
                except Exception as e:
                    print(f"Fehler bei {filepath}: {e}")
    
    print("\nWortanzahl pro Datei:")
    for filepath, count in sorted(file_counts.items()):
        print(f"{filepath}: {count} Wörter")
    
    print(f"\nGesamtanzahl Wörter: {total_words}")
    print(f"Anzahl Dateien: {len(file_counts)}")

if __name__ == "__main__":
    main()