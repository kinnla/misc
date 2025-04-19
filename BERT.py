#!/usr/bin/env python3
# coding: utf-8

"""
Interactive duet writing with GPT-2

This script creates an interactive writing experience where the user and AI
take turns writing one word at a time to co-create text.
"""

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.ERROR)

def get_next_word(model, tokenizer, context):
    """Get the next word from the model based on the given context"""
    # Properly tokenize the input with attention mask
    encoded_input = tokenizer(context, return_tensors='pt', padding=True)
    input_ids = encoded_input['input_ids']
    attention_mask = encoded_input['attention_mask']
    
    # Generate the next token
    with torch.no_grad():
        output = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=input_ids.shape[1] + 2,  # Allow for up to 2 more tokens
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.7,
            top_k=40,
            top_p=0.9
        )
    
    # Get the full generated text
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    
    # Extract only the new part (what was added after the context)
    new_part = generated_text[len(context):].strip()
    
    # Get just the first word of the new part
    if new_part:
        words = new_part.split()
        if words:
            return words[0]
    
    # Fallback if no meaningful word was generated
    return "..."

def main():
    """Main interactive duet writing function"""
    print("Beginne in der nächsten Zeile einen Satz. Die KI wird mit dir im Duett schreiben.\n")
    
    try:
        # Load model and tokenizer directly (once, at the start)
        print("Lade GPT-2 Modell...")
        model_name = "distilgpt2"  # Smaller model for memory efficiency
        
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        # Set the padding token to be the EOS token
        tokenizer.pad_token = tokenizer.eos_token
        
        model = GPT2LMHeadModel.from_pretrained(model_name)
        print(f"Modell {model_name} geladen. Du kannst jetzt beginnen.\n")
        
        # Main interaction loop
        sentence = None
        
        while True:
            # Get user input
            input_text = input("")
            
            # Handle empty input
            if not input_text.strip():
                print("Bitte gib etwas ein.")
                continue
            
            # Initialize or append to sentence
            if not sentence:
                sentence = input_text
            elif input_text[-1].isalnum():
                sentence += " " + input_text
            else:
                sentence += input_text
            
            # Use a sliding window context to keep memory usage low
            context = ' '.join(sentence.split()[-10:]) if len(sentence.split()) > 10 else sentence
            
            # Get the next word from the model
            next_word = get_next_word(model, tokenizer, context)
            
            # Add the word to the sentence
            sentence += " " + next_word
            
            # Display the updated sentence
            print(sentence)
    
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
    except ImportError as e:
        print(f"Fehler beim Laden der benötigten Bibliotheken: {e}")
        print("Bitte installiere die fehlenden Pakete mit 'pip install transformers torch'")
        sys.exit(1)
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()