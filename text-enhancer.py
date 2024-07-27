#!~/venvs/default/bin/python3
# coding: utf-8

"""
This script takes a potentially unstructured text file as input, analyzes it, and generates
a structured version in markdown.

Usage:
./text-enhancer.py raw-text.txt
"""

import openai
import argparse
import os

# Set the OpenAI API key from your environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

MODEL = "gpt-4o-mini"  # Specify the model you want to use
PROMPT = """Du bist eine Stenographin und Sekretärin und hervorragend darin, Texte \
mitzuschreiben und zu formulieren. Anbei ein Transkript einer Sprachnotiz, die ich \
gerade eingesprochen habe. Korrigiere Grammatik und Rechtschreibung, und forme den \
Text so um, dass er Sinn ergibt. Achte darauf, dass kein Inhalt verloren geht und \
der Gedankengang erhalten bleibt. Es geht nicht um eine Zusammenfassung. Strukturiere \
den Text in geeignete Abschnitte und finde Zwischenüberschriften. Nutze Markdown \
als Ausgabeformat. Gib den Text dann aus, so dass ich ihn zu Protokoll geben kann."""


def enhance_text(file_path):
    # Read the input text file
    with open(file_path, 'r') as file:
        raw_text = file.read()
    
    # Generate structured text using OpenAI API
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": raw_text}
        ],
        temperature=0
    )
    
    structured_text = response['choices'][0]['message']['content']
    return structured_text

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Enhance and structure a plain text.")
    parser.add_argument("file_path", help="Path to the text file")
    args = parser.parse_args()
    
    # Get the structured text
    structured_text = enhance_text(args.file_path)
    
    # Save the structured text to a markdown file
    output_file = args.file_path.replace(".txt", "_structured.md")
    with open(output_file, 'w') as file:
        file.write(structured_text)
    
    print(f"Structured text saved to {output_file}")