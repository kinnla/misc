#! /Users/zoppke/venvs/default/bin/python3
# coding: utf-8

"""
This script takes a potentially unstructured text file as input, analyzes it, and generates
a structured version in markdown.

Usage:
./text-enhancer.py raw-text.txt
"""

from openai import OpenAI
import argparse
import os

client = OpenAI()

MODEL = "gpt-4o"  # Specify the model you want to use
PROMPT = """Du bist eine Stenographin und Sekretärin und hervorragend darin, Texte \
mitzuschreiben und zu formulieren. Anbei ein Transkript einer Sprachnotiz, die ich \
gerade eingesprochen habe. Korrigiere Grammatik und Rechtschreibung, und forme den \
Text so um, dass er Sinn ergibt. Achte darauf, dass kein Inhalt verloren geht und \
der Gedankengang erhalten bleibt. Es geht nicht um eine Zusammenfassung. Strukturiere \
den Text in geeignete Abschnitte und finde Zwischenüberschriften. Nutze Markdown \
als Ausgabeformat. Gib den Text dann aus, so dass ich ihn zu Protokoll geben kann."""

MAX_CHUNK_SIZE = 10000


def find_slice_end(text, start_index, slice_length):
    end_index = start_index + slice_length
    if end_index >= len(text):
        return len(text)

    # Find the next period after the slice length
    period_index = text.find('.', end_index)
    if period_index == -1:
        return len(text)  # If no period found, return the end of the text
    return period_index + 1

def enhance_text(file_path):
	
	# Read the input text file
	with open(file_path, 'r') as file:
		raw_text = file.read()
	
    text_length = len(raw_text)
    if text_length <= MAX_CHUNK_SIZE:
        slices = [raw_text]
    else:
        num_slices = math.ceil(text_length / MAX_CHUNK_SIZE)
        slice_length = text_length // num_slices
        slices = []
        
        start_index = 0
        for _ in range(num_slices):
            end_index = find_slice_end(raw_text, start_index, slice_length)
            slices.append(raw_text[start_index:end_index])
            start_index = end_index
    
    structured_text = ""
    for slice in slices:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": slice}
            ],
            temperature=0
        )
        structured_text += completion.choices[0].message.content + "\n"
    
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