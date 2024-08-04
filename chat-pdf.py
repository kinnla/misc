#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

"""
Chatting with a PDF

Usage:
./chat-pdf.py myDoc.pdf
"""

import fitz  # PyMuPDF
from langchain.prompts import PromptTemplate
import argparse
import os
import ollama

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with fitz.open(pdf_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text

# Command-line argument parsing for PDF path
parser = argparse.ArgumentParser(description="Chat with a PDF using LangChain and Llama 3.1.")
parser.add_argument("pdf_path", type=str, help="The path to the PDF file.")
args = parser.parse_args()

# Extract text from the PDF
pdf_name = os.path.basename(args.pdf_path)
pdf_text = extract_text_from_pdf(args.pdf_path)

# Truncate content if it exceeds context_window
context_window = 4096  # Example context window size; adjust as needed
encoded_content = pdf_text.encode('utf-8')
if len(encoded_content) > context_window:
    print(len(encoded_content))
    pdf_text = encoded_content[:context_window].decode('utf-8', errors='ignore')

# Greet the user and ask for a question
print(f"Hey welcome! You are chatting with {pdf_name}, facilitated by Llama 3.1. What would you like to know?")
user_query = input("Your question: ")

# Define the LangChain prompt template
template = PromptTemplate(
    input_variables=["pdf_content", "user_query"],
    template="""
    You are a helpful assistant. Here is some information from a document:

    {pdf_content}

    Based on this information, answer the following question:
    {user_query}
    
    Answer:
    """
)

# Create the prompt
prompt = template.format(pdf_content=pdf_text, user_query=user_query)

# Initialize the Ollama client
client = ollama.Client()

# Generate the response using Llama 3.1
formatted_prompt = prompt
response = client.generate(prompt=formatted_prompt, model="llama3.1", options={'temperature': 0})

# Output the response
print(response['response'])