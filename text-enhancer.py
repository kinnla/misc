#!~/venvs/default/bin/python3
# coding: utf-8

"""
This script takes a potentially unstructured text file as input, analyzes it and generates
a structured version in markdown.

Usage:
./text-enhancer.py raw-text.txt
"""




import openai


# gets OPENAI_API_KEY from your environment variables
openai = openai.OpenAI()



response = client.chat.completions.create(
    model=MODEL,
    messages=[
    {"role": "system", "content":"""You are generating a transcript summary. Create a summary of the provided transcription. Respond in Markdown."""},
    {"role": "user", "content": [
        {"type": "text", "text": f"The audio transcription is: {transcription.text}"}
        ],
    }
    ],
    temperature=0,
)



if __name__ == "__main__":

    # Set up argument parsing
    parser = argparse.ArgumentParser(description=
        "Enhance and structure a plain text.")
    parser.add_argument("file_path", help="Path to the voice file")
