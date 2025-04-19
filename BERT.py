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

# Safer character input handling
try:
    # Try to use a more robust implementation if available
    from readchar import readchar as getch
except ImportError:
    try:
        from getch import getch
    except ImportError:
        # Fallback implementation for character input
        import tty
        import termios
        
        def getch():
            """Get a single character from stdin, Unix version"""
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

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
            "system": "Du bist ein Schriftsteller, der einen Text zusammen mit einem anderen Autor schreibt, abwechselnd Wort für Wort. Gib immer nur ein einzelnes passendes Wort zurück, das den Satz sinnvoll weiterführt.",
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

def get_user_input_realtime():
    """Get user input character by character, ending at non-alphanumeric chars"""
    chars = []
    auto_submit = False
    last_char = None
    composing_char = False  # Flag for macOS dead key composition (like Option+u)
    
    while True:
        try:
            # Get a single character
            char = getch()
            
            # Skip empty input
            if not char:
                continue
                
            # Handle byte input and convert to string safely
            if isinstance(char, bytes):
                try:
                    char = char.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    # Skip invalid characters
                    continue
            
            # Handle dead keys (option+u on macOS)
            # When Option+u is pressed, some systems report special characters
            if char in ['\x00', '\x1b', '\xc2\xa8', '¨']:
                composing_char = True
                continue
            
            # If we just saw a dead key, this char might be the base vowel
            # macOS will automatically compose the umlaut, so no special handling needed
            if composing_char:
                composing_char = False
                # continue normal processing
            
            # ASCII values for Backspace (8) or DEL (127)
            if char in ['\b', '\x7f']:
                if chars:  # Only delete if there are characters
                    chars.pop()  # Remove the last character from the list
                    # Output Backspace+Space+Backspace to erase the character
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
                continue
            
            # Enter key ends input
            if char in ['\r', '\n']:
                auto_submit = True
                break
            
            # Try to handle the character more safely
            try:
                # Filter out control characters
                if ord(char) < 32 and char not in ['\r', '\n', '\t', '\b']:
                    continue
                    
                # Add character to input and display it
                chars.append(char)
                sys.stdout.write(char)
                sys.stdout.flush()
                last_char = char
                
                # If the last character is not alphanumeric, auto-submit
                if not char.isalnum():
                    auto_submit = True
                    break
            except ValueError:
                # Skip characters that cause problems
                continue
                
        except (UnicodeDecodeError, ValueError) as e:
            # Skip problematic characters
            continue
        except Exception as e:
            # For any other errors during character processing
            # Only break if we have some input, otherwise continue
            if chars:
                break
            continue
    
    text = ''.join(chars)
    return text, auto_submit, last_char

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Interaktives Duett-Schreiben mit Ollama")
    parser.add_argument("--log", action="store_true", help="API-Kommunikation loggen")
    parser.add_argument("--temp", type=float, default=0.7, 
                        help="Temperatur für die Textgenerierung (0.1-2.0, Standard: 0.7)")
    parser.add_argument("--model", type=str, help="Spezifisches Ollama-Modell verwenden")
    
    return parser.parse_args()

def main():
    """Main interactive duet writing function"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging if enabled
    api_logger = setup_logger(args.log)
    
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
            
        print(f"Modell: {model_name}")
        
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
        sys.stdout.write("\nStarte das Duett (schreibe): ")
        sys.stdout.flush()
        
        while True:
            # Get user input character by character
            input_text, auto_submit, last_char = get_user_input_realtime()
            
            # Handle empty input
            if not input_text.strip():
                sys.stdout.write("Bitte gib etwas ein: ")
                sys.stdout.flush()
                continue
            
            # Initialize or append to sentence
            if not sentence:
                sentence = input_text
            elif last_char and last_char.isalnum() and auto_submit:
                # Wenn automatischer Submit durch Enter und letztes Zeichen ist alphanumerisch
                sentence += " " + input_text
            else:
                # Wenn durch Sonderzeichen automatischer Submit oder letztes Zeichen ist nicht alphanumerisch
                sentence += " " + input_text
            
            # Kleiner Puffer, wenn nicht automatisch abgesendet wurde
            if not auto_submit:
                sys.stdout.write(" ")
                sys.stdout.flush()
            
            # Use the last 50 words as context to keep memory usage low
            context = ' '.join(sentence.split()[-50:]) if len(sentence.split()) > 50 else sentence
            
            # Show thinking indicator
            sys.stdout.write("... ")
            sys.stdout.flush()
            
            # Get the next word from the model
            next_word = get_next_word(model_name, context, temperature, api_logger)
            
            # Clear the thinking indicator with backspaces
            sys.stdout.write("\b\b\b\b")
            sys.stdout.flush()
            
            # Prüfe, ob das Wort einen Punkt enthält und korrigiere die Ausgabe
            if "." in next_word:
                # Wenn das Wort mit einem Punkt endet, gib es ohne Leerzeichen aus
                sys.stdout.write(f"{next_word}")
                sys.stdout.flush()
            else:
                # Normales Wort mit Leerzeichen
                sys.stdout.write(f"{next_word} ")
                sys.stdout.flush()
            
            # Add the word to the sentence
            sentence += " " + next_word
    
    except KeyboardInterrupt:
        print("\n\nDuett beendet. Finaler Text:")
        print(sentence)
    except UnicodeError as e:
        print(f"\n\nEin Unicode-Fehler ist aufgetreten: {e}")
        print("Das Skript wird neu gestartet...")
        main()  # Restart the script
    except Exception as e:
        print(f"\n\nEin Fehler ist aufgetreten: {e}")
        print("Details:", repr(e))
        sys.exit(1)

if __name__ == "__main__":
    main()