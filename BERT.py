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
import os
import argparse
import datetime

# Configure logging - disable console output
logging.basicConfig(level=logging.ERROR, handlers=[])

OLLAMA_API = "http://localhost:11434/api/generate"

def setup_logger(log_enabled=False):
    """Setup logger for API interactions"""
    if not log_enabled:
        return None
        
    # Create logger
    logger = logging.getLogger("ollama_api")
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create file handler with timestamp in filename
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
    log_filename = os.path.join(logs_dir, f"{timestamp}_ollama_duett.log")
    file_handler = logging.FileHandler(log_filename)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # No terminal output for logging
    return logger

def get_next_word(model_name, context, temperature=0.7, api_logger=None):
    """Get the next word from Ollama based on the given context"""
    try:
        # Prepare the request for Ollama
        data = {
            "model": model_name,
            "prompt": context,
            "system": "Du bist ein Schriftsteller, der einen Text zusammen mit einem anderen Autor schreibt, abwechselnd Wort für Wort. Gib immer nur ein einzelnes passendes Wort zurück, das den Satz sinnvoll weiterführt. Du darfst auch Satzzeichen wie Punkt, Komma, Ausrufezeichen oder Fragezeichen verwenden, um den Satz zu strukturieren. Achte auf eine sinnvolle Zeichensetzung.",
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 10  # Limit token generation
            }
        }
        
        # Log API request if enabled
        if api_logger:
            api_logger.info(f"REQUEST: {json.dumps(data, ensure_ascii=False)}")
        
        # Make the API request
        response = requests.post(OLLAMA_API, json=data)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        generated_text = result.get('response', '').strip()
        
        # Log API response if enabled
        if api_logger:
            api_logger.info(f"RESPONSE: {json.dumps(result, ensure_ascii=False)}")
        
        # Extract just the first word
        if generated_text:
            words = generated_text.split()
            if words:
                return words[0]
        
        # Fallback if no meaningful word was generated
        return "..."
        
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        print(f"\nFehler bei der Verbindung zu Ollama: {e}")
        print("Ist Ollama installiert und läuft der Server? Starte Ollama mit 'ollama serve'")
        return "..."
    except Exception as e:
        print(f"\nFehler bei der Textgenerierung: {e}")
        return "..."

def read_single_char():
    """Read a single character from stdin without waiting for Enter key"""
    import sys
    import tty
    import termios
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        
        # Handle Ctrl+C (ASCII 3)
        if ch == '\x03':
            # Restore terminal settings before raising KeyboardInterrupt
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            raise KeyboardInterrupt()
            
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_user_input_realtime(debug_mode=False):
    """Get user input character by character, ending on Enter or certain punctuation"""
    chars = []
    last_char = None
    delete_preceding_space = False
    
    # Collect input character by character
    print_debug("Starting character input", debug_mode)
    
    while True:
        try:
            char = read_single_char()
            
            # Print debug info about the character
            if debug_mode:
                char_repr = repr(char)
                try:
                    char_ord = ord(char)
                    print_debug(f"Got char: {char_repr}, ord: {char_ord}", debug_mode)
                except:
                    print_debug(f"Got char: {char_repr} (no ord value)", debug_mode)
            
            # Handle special keys
            
            # Backspace (ASCII 8 or DEL 127)
            if char in ['\b', '\x7f']:
                if chars:  # Only delete if there are characters
                    chars.pop()
                    # Backspace+space+backspace to erase character from screen
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
                continue
            
            # Enter always ends input and triggers submission
            if char in ['\r', '\n']:
                print_debug("Enter pressed, ending input", debug_mode)
                break
            
            # Filter out other control characters
            if ord(char) < 32 and char not in ['\t']:
                print_debug(f"Skipping control character: {ord(char)}", debug_mode)
                continue
            
            # Special handling for punctuation - remove preceding space if needed
            if char in ['.', ',', '!', '?', ':', ';'] and ord(char) < 128:
                # If the first character is punctuation and we're at the beginning of a line
                # that probably follows the LLM output (which ended with a space)
                if not chars and not delete_preceding_space:
                    # Remove the preceding space on the screen
                    sys.stdout.write('\b')
                    sys.stdout.flush()
                    delete_preceding_space = True
                    print_debug("Removed preceding space for punctuation", debug_mode)
            
            # Add regular characters to our input buffer and display
            chars.append(char)
            sys.stdout.write(char)
            sys.stdout.flush()
            last_char = char
            
            # Auto-submit on punctuation (but ignore umlauts and special characters)
            if char in ['.', ',', '!', '?', ':', ';'] and ord(char) < 128:
                print_debug(f"Punctuation detected: {char}, ending input", debug_mode)
                break
            
            # Auto-submit on space (simplified - just one space is enough)
            if char == ' ':
                # If this is the first character and it's a space,
                # we're probably just triggering the LLM without adding content
                if len(chars) == 1 and chars[0] == ' ':
                    # Remove the space we just added both from array and screen
                    chars.pop()  # Remove the space
                    sys.stdout.write('\b')  # Move back one character
                    sys.stdout.flush()
                
                print_debug("Space detected, ending input", debug_mode)
                break
                
        except Exception as e:
            print_debug(f"Error during character input: {e}", debug_mode)
            # Only stop if we have some input already
            if chars:
                break
    
    # Join all characters into the final text
    text = ''.join(chars)
    print_debug(f"Final input: '{text}', delete_preceding_space: {delete_preceding_space}", debug_mode)
    
    return text, last_char, delete_preceding_space

def print_debug(message, debug_enabled=False):
    """Print debug message if debug mode is enabled"""
    if debug_enabled:
        print(f"\n[DEBUG] {message}")
        sys.stdout.write("\nStarte das Duett (schreibe): ")
        sys.stdout.flush()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Interaktives Duett-Schreiben mit Ollama")
    parser.add_argument("--log", action="store_true", help="API-Kommunikation loggen")
    parser.add_argument("--temp", type=float, default=0.7, 
                        help="Temperatur für die Textgenerierung (0.1-2.0, Standard: 0.7)")
    parser.add_argument("--model", type=str, help="Spezifisches Ollama-Modell verwenden")
    parser.add_argument("--debug", action="store_true", help="Debug-Modus für Tastatureingabe aktivieren")
    
    return parser.parse_args()

def main():
    """Main interactive duet writing function"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging if enabled
    api_logger = setup_logger(args.log)
    
    # Set debug mode
    debug_mode = args.debug
    
    # Validate temperature
    temperature = args.temp
    if temperature < 0.1 or temperature > 2.0:
        print("Warnung: Temperatur sollte zwischen 0.1 und 2.0 liegen. Verwende 0.7.")
        temperature = 0.7
    
    print("Interaktives Duett mit Ollama")
    print("-----------------------------")
    print("Schreibe und beende mit Enter oder einem Satzzeichen. Die KI schreibt das nächste Wort.")
    print("Verwende Backspace, um Tippfehler zu korrigieren.")
    print(f"Temperatur: {temperature}")
    if debug_mode:
        print("DEBUG-MODUS AKTIV")
    print("Drücke Strg+C zum Beenden.\n")
    
    # Try to connect to Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        
        # Select appropriate model
        model_name = args.model
        
        if not model_name:
            # Automatische Modellauswahl
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
        
        # Check if specified model exists
        if model_name and model_name not in [m["name"] for m in models]:
            print(f"Warnung: Modell '{model_name}' nicht gefunden. Verfügbare Modelle:")
            for model in models:
                print(f"- {model['name']}")
            print("\nVerwende automatische Modellauswahl.")
            model_name = None
            
            # Erneute automatische Auswahl
            for preferred in ["llama3", "llama3:8b", "mistral", "gemma:7b"]:
                for model in models:
                    if preferred in model["name"].lower():
                        model_name = model["name"]
                        break
                if model_name:
                    break
            
            if not model_name and models:
                model_name = models[0]["name"]
        
        if not model_name:
            print("Kein Ollama-Modell gefunden. Bitte installiere ein Modell mit 'ollama pull llama3'")
            sys.exit(1)
            
        print(f"Modell: {model_name}\n")
        
    except requests.exceptions.RequestException:
        print("Konnte keine Verbindung zu Ollama herstellen.")
        print("Bitte stelle sicher, dass Ollama installiert ist und läuft:")
        print("1. Installiere Ollama von https://ollama.com/")
        print("2. Starte den Ollama-Server mit 'ollama serve'")
        print("3. Lade ein Modell mit 'ollama pull llama3'")
        sys.exit(1)
    
    try:
        # Main interaction loop
        sentence = ""
        sys.stdout.write("Starte das Duett (schreibe): ")
        sys.stdout.flush()
        
        while True:
            # Get user input character by character
            input_text, last_char, delete_preceding_space = get_user_input_realtime(debug_mode)
            
            # Update the sentence with the new input
            if not sentence:
                # First input
                sentence = input_text
            elif input_text in ['.', ',', '!', '?', ':', ';']:
                # Handle punctuation characters
                if delete_preceding_space and sentence.endswith(" "):
                    # Remove the space that was just added by the LLM output
                    sentence = sentence[:-1] + input_text
                else:
                    # Just append the punctuation without space
                    sentence += input_text
                    
                # Add space after ALL punctuation marks
                sentence += " "
            elif sentence.endswith(" "):
                # If sentence already ends with space, just append
                sentence += input_text
            else:
                # Otherwise add a space before new input
                sentence += " " + input_text
            
            # Use the last 50 words as context to keep memory usage low
            context = ' '.join(sentence.split()[-50:]) if len(sentence.split()) > 50 else sentence
            
            # Check if the last character is a punctuation mark (and we need to add a space)
            # This ensures proper spacing when user ends with punctuation
            if sentence and sentence[-1] in ['.', ',', '!', '?', ':', ';'] and not sentence.endswith(" "):
                # Add space if we end with punctuation and no space
                sys.stdout.write(" ")
                sys.stdout.flush()
                sentence += " "
                print_debug(f"Added space after punctuation: {sentence}", debug_mode)
            
            # Show thinking indicator - add space only if needed
            if sentence and not sentence.endswith(" "):
                sys.stdout.write(" ... ")
            else:
                sys.stdout.write("... ")
            sys.stdout.flush()
            
            # Get the next word from the model
            next_word = get_next_word(model_name, context, temperature, api_logger)
            
            # Clear the thinking indicator with backspaces (accounting for possible space)
            if sentence and not sentence.endswith(" "):
                sys.stdout.write("\b\b\b\b\b\b")  # 6 chars: " ... "
            else:
                sys.stdout.write("\b\b\b\b")  # 4 chars: "... "
            sys.stdout.flush()
            
            # Handle punctuation in the output
            if next_word in ['.', ',', '!', '?', ':', ';'] or next_word.startswith(('.', ',', '!', '?')):
                # Punctuation - no space before
                sys.stdout.write(next_word)
                sys.stdout.flush()
                sentence += next_word
                
                # Add space after ANY punctuation (not just sentence-ending ones)
                # This makes it easier for the user to continue typing
                # Double-check that we always add the space after punctuation
                sys.stdout.write(" ")
                sys.stdout.flush()
                if not sentence.endswith(" "):  # Ensure we don't add double spaces
                    sentence += " "
            else:
                # Regular word - add space before if needed
                if not sentence.endswith(" "):
                    sys.stdout.write(" ")
                    sentence += " "
                
                sys.stdout.write(next_word)
                sys.stdout.flush()
                sentence += next_word
                
                # Always add space after a regular word (if it ends with letter or number)
                if next_word and next_word[-1].isalnum():
                    sys.stdout.write(" ")
                    sys.stdout.flush()
                    sentence += " "
            
            # Continue the loop for next word
    
    except KeyboardInterrupt:
        print("\n\nDuett beendet. Finaler Text:")
        print(sentence)
    except UnicodeError as e:
        print(f"\n\nEin Unicode-Fehler ist aufgetreten: {e}")
        print("Details:", repr(e))
        sys.exit(1)
    except Exception as e:
        print(f"\n\nEin Fehler ist aufgetreten: {e}")
        print("Details:", repr(e))
        sys.exit(1)

if __name__ == "__main__":
    main()