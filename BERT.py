#!/usr/bin/env python3
# coding: utf-8

"""
Interactive duet writing with GPT-2

This script creates an interactive writing experience where the user and AI
take turns writing one word at a time to co-create text.
"""

import os
import sys
import time
import logging

# Set environment variables before importing transformers
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Configure logging to suppress warnings
logging.basicConfig(level=logging.ERROR)

def main():
    """Main interactive duet writing function"""
    print("Beginne in der nächsten Zeile einen Satz. Die KI wird mit dir im Duett schreiben.\n")
    
    try:
        # Import here to better handle potential import errors
        print("Lade GPT-2 Modell...")
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Disable transformers warnings
        transformers.logging.set_verbosity_error()
        
        # Initialize with minimal settings
        tokenizer = AutoTokenizer.from_pretrained("distilgpt2")  # Smaller model
        model = AutoModelForCausalLM.from_pretrained("distilgpt2")
        
        print("Modell geladen. Du kannst jetzt beginnen.\n")
        
        sentence = None
        
        while True:
            try:
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
                
                try:
                    # Use a very short context to reduce memory issues
                    context = ' '.join(sentence.split()[-5:]) if len(sentence.split()) > 5 else sentence
                    
                    # Add a small delay to avoid memory issues
                    time.sleep(0.2)
                    
                    # Use direct tokenizer -> model -> decode approach instead of pipeline
                    inputs = tokenizer(context, return_tensors="pt", truncation=True, max_length=20)
                    
                    # Generate with minimal settings
                    with torch.no_grad():
                        output = model.generate(
                            inputs["input_ids"],
                            max_length=len(inputs["input_ids"][0]) + 2,  # Just enough for one more token
                            do_sample=True,
                            temperature=0.7,
                            top_k=50,
                            top_p=0.95,
                            num_return_sequences=1,
                            pad_token_id=tokenizer.eos_token_id
                        )
                    
                    # Decode the output
                    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
                    
                    # Get only the new part
                    new_text = generated_text[len(context):].strip()
                    
                    if new_text:
                        # Get just the first word
                        next_word = new_text.split()[0] if new_text.split() else "..."
                        sentence += " " + next_word
                    else:
                        # Fallback if no new text was generated
                        sentence += " ..."
                    
                    # Print the updated sentence
                    print(sentence)
                    
                except Exception as e:
                    print(f"Fehler bei der Textgenerierung: {str(e)}")
                    print("Das Skript wird beendet.")
                    break
            
            except KeyboardInterrupt:
                print("\nProgramm beendet.")
                break
            except Exception as e:
                print(f"Ein Fehler ist aufgetreten: {str(e)}")
                break
    
    except ImportError as e:
        print(f"Fehler: Eine benötigte Bibliothek konnte nicht geladen werden: {e}")
        print("Bitte installiere die erforderlichen Pakete mit: pip install transformers torch")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
    except Exception as e:
        print(f"Fataler Fehler: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
