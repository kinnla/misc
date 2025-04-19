#!/usr/bin/env python3
# coding: utf-8

"""
Interactive duet writing with Ollama

This script creates an interactive writing experience where the user and AI
take turns writing one word at a time to co-create text. It uses a locally running
Ollama model to generate text.
"""

import sys
import logging
import requests
import json
import re

# Configure logging
logging.basicConfig(level=logging.ERROR)

OLLAMA_API = "http://localhost:11434/api/generate"

def get_next_word(model_name, context):
    """Get the next word from Ollama based on the given context"""
    try:
        # Prepare the request for Ollama
        data = {
            "model": model_name,
            "prompt": context,
            "system": "Du bist ein Schriftsteller, der einen Text zusammen mit einem anderen Autor schreibt, abwechselnd Wort für Wort. Gib immer nur ein einzelnes passendes Wort zurück, das den Satz sinnvoll weiterführt.",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 10  # Limit token generation
            }
        }
        
        # Make the API request
        response = requests.post(OLLAMA_API, json=data)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        generated_text = result.get('response', '').strip()
        
        # Extract just the first word
        if generated_text:
            words = generated_text.split()
            if words:
                return words[0]
        
        # Fallback if no meaningful word was generated
        return "..."
        
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        print(f"Fehler bei der Verbindung zu Ollama: {e}")
        print("Ist Ollama installiert und läuft der Server? Starte Ollama mit 'ollama serve'")
        return "..."
    except Exception as e:
        print(f"Fehler bei der Textgenerierung: {e}")
        return "..."

def main():
    """Main interactive duet writing function"""
    print("Beginne in der nächsten Zeile einen Satz. Die KI wird mit dir im Duett schreiben.\n")
    
    # Try to connect to Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        
        # Select appropriate model
        model_name = None
        preferred_models = ["llama3", "llama3:8b", "mistral", "gemma:7b"]
        
        for preferred in preferred_models:
            for model in models:
                if preferred in model["name"].lower():
                    model_name = model["name"]
                    break
            if model_name:
                break
        
        if not model_name and models:
            # Use the first available model if preferred ones aren't found
            model_name = models[0]["name"]
        
        if not model_name:
            print("Kein Ollama-Modell gefunden. Bitte installiere ein Modell mit 'ollama pull llama3'")
            sys.exit(1)
            
        print(f"Verwende Ollama-Modell: {model_name}")
        print("Du kannst jetzt beginnen.\n")
        
    except requests.exceptions.RequestException:
        print("Konnte keine Verbindung zu Ollama herstellen.")
        print("Bitte stelle sicher, dass Ollama installiert ist und läuft:")
        print("1. Installiere Ollama von https://ollama.com/")
        print("2. Starte den Ollama-Server mit 'ollama serve'")
        print("3. Lade ein Modell mit 'ollama pull llama3'")
        sys.exit(1)
    
    try:
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
            
            # Use the last 50 words as context to keep memory usage low
            context = ' '.join(sentence.split()[-50:]) if len(sentence.split()) > 50 else sentence
            
            # Get the next word from the model
            next_word = get_next_word(model_name, context)
            
            # Add the word to the sentence
            sentence += " " + next_word
            
            # Display the updated sentence
            print(sentence)
    
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()