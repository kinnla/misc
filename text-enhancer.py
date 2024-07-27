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
import math

client = OpenAI()

"""
We generate the structured version in several steps.
1. generate chunks of raw text with a MAX_CHUNK_SIZE of characters.
2. For any chunk create a summary sentence.
3. For any raw text chunk, ask the model to do the proofread and provide the summaries 
produced in the step before. 
"""

MAX_CHUNK_SIZE = 8000

SUMMARY_MODEL = "gpt-4o-mini" # simple task, so use a simple model
SUMMARY_PROMPT = """Das ist ein Abschnitt aus einem längeren Text. 
Fasse den Abschnitt in einem Satz zusammen. Gib direkt wieder, 
was der Abschnitt enthält, behalte die Ich-Perspektive."""

PROOFREAD_MODEL = "gpt-4o" # complex task, so use an enhanced model
PROOFREAD_PROMPT = """Du bist ein ausgezeichneter Lektor, der einen Text korrektur liest.
Hier eine Zusammenfassung des Texts, den wir bearbeiten:
--------
{}
--------

Du bearbeitest nun das Segment {}. Korrigiere Grammatik und Rechtschreibung, und forme das
Segment so um, dass es klar und verständlich ist. Achte darauf, dass kein Inhalt verloren
geht und der Gedankengang erhalten bleibt. Erstelle eine passende Hauptüberschrift (##)
für das Segment. Zwischenüberschriften werden nicht gebraucht. 
Ziehe kein Zwischenfazit; ein Fazit ist nur im letzten Segment notwendig. 
Achte darauf, dass sich das Segment in den Kontext des gesamten Textes einfügt."""


def find_slice_end(text, start_index, slice_length):
    end_index = start_index + slice_length
    if end_index >= len(text):
        return len(text)

    # Find the next period after the slice length
    period_index = text.find('.', end_index)
    if period_index == -1:
        return len(text)  # If no period found, return the end of the text
    return period_index + 1

def get_summary(text):
    completion = client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0
    )
    # print ("summary")
    # print (completion.choices[0].message.content.strip())
    return completion.choices[0].message.content.strip()

def proofread_text(chunk, chunk_number, all_summaries):
    prompt = PROOFREAD_PROMPT.format(all_summaries, chunk_number)
    completion = client.chat.completions.create(
        model=PROOFREAD_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": chunk}
        ],
        temperature=0
    )
    # print ("prompt")
    # print (prompt)
    # print ("proofread")
    # print (completion.choices[0].message.content.strip())
    return completion.choices[0].message.content.strip()

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
    
    # Create summaries for each chunk
    summaries = []
    for i, slice in enumerate(slices, start=1):
        summary = get_summary(slice)
        summaries.append(f"Chunk {i}: {summary}")
    
    all_summaries = "\n".join(summaries)
    structured_text = ""
    
    # Proofread each chunk with the context of all summaries
    for i, slice in enumerate(slices, start=1):
        enhanced_chunk = proofread_text(slice, i, all_summaries)
        structured_text += enhanced_chunk + "\n\n"
    
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


