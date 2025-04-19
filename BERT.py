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

def main():
    """Main interactive duet writing function"""
    print("Beginne in der nächsten Zeile einen Satz. Die KI wird mit dir im Duett schreiben.\n")
    
    try:
        # Load model and tokenizer directly (once, at the start)
        print("Lade GPT-2 Modell...")
        model_name = "distilgpt2"  # Smaller model for memory efficiency
        
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        model = GPT2LMHeadModel.from_pretrained(model_name)
        
        print(f"Modell {model_name} geladen. Du kannst jetzt beginnen.\n")
        
        # No parallelism, just a simple loop
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
            
            # Get context (use just the last few words to keep memory usage low)
            context = ' '.join(sentence.split()[-10:]) if len(sentence.split()) > 10 else sentence
            
            # Simple generation
            input_ids = tokenizer.encode(context, return_tensors='pt')
            
            # Generate without gradient computation for efficiency
            with torch.no_grad():
                output = model.generate(
                    input_ids,
                    max_length=input_ids.shape[1] + 1,  # Just one more token
                    num_return_sequences=1,
                    pad_token_id=tokenizer.eos_token_id,
                    do_sample=True,
                    temperature=0.7,
                    top_k=40,
                    top_p=0.9
                )
            
            # Decode and get just the new token
            generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
            new_part = generated_text[len(context):].strip()
            
            # Extract just the first word
            if new_part:
                next_word = new_part.split()[0] if new_part.split() else "..."
            else:
                next_word = "..."
            
            # Update the sentence
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