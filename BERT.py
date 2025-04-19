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

def get_user_input_realtime():
    """Get user input character by character, ending at non-alphanumeric chars"""
    chars = []
    auto_submit = False
    last_char = None
    composing_char = False  # Flag for macOS dead key composition (like Option+u)
    deadkey_buffer = ""  # Buffer to handle deadkeys on macOS
    
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
            if char in ['\x00', '\x1b', '\xc2\xa8', '¨', '˙', '´', '`', '^']:
                composing_char = True
                deadkey_buffer = char  # Store the deadkey
                # Don't add it to the input or display it
                continue
            
            # If we just saw a dead key, this char might be the base vowel
            if composing_char:
                composing_char = False
                
                # On macOS, pressing Option+u and then 'o' directly produces 'ö'
                # Let's try to detect common umlaut combinations
                if deadkey_buffer in ['¨', '\xc2\xa8'] and char.lower() in 'aeiou':
                    # Map to the corresponding umlaut
                    umlaut_map = {
                        'a': 'ä', 'A': 'Ä',
                        'e': 'ë', 'E': 'Ë',
                        'i': 'ï', 'I': 'Ï',
                        'o': 'ö', 'O': 'Ö',
                        'u': 'ü', 'U': 'Ü'
                    }
                    # Replace with the actual umlaut
                    char = umlaut_map.get(char, char)
                
                deadkey_buffer = ""  # Clear the buffer
                # Continue with normal processing for the resulting character
            
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
                # Always end input on Enter
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
                
                # Check if the character should trigger auto-submit
                # Punctuation marks that should trigger auto-submit
                auto_submit_chars = ['.', ',', '!', '?', ':', ';', '-', ')', ']', '}', '/']
                
                # If it's a punctuation mark, auto-submit
                if char in auto_submit_chars:
                    auto_submit = True
                    break
                    
                # Special handling for space: only auto-submit if the last character in the text was also a space
                if char == ' ':
                    # Check if the input already has a space (double space)
                    if len(chars) > 1 and chars[-2] == ' ':
                        auto_submit = True
                        break
                
                # Don't auto-submit for umlauts or other special characters
                # We'll only auto-submit for specific punctuation marks and double spaces
                
            except ValueError:
                # Skip characters that cause problems
                continue
                
        except (UnicodeDecodeError, ValueError) as e:
            # Skip problematic characters
            continue
        except Exception as e:
            # For any other errors during character processing
            if chars:  # Only break if we have some input
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
            
            # Auch leere Eingabe (z.B. nur Enter) akzeptieren und fortfahren
            # (dadurch kann der Nutzer einfach Enter drücken, um das LLM zum Generieren zu bringen)
            
            # Behandlung der Eingabe je nach Kontext
            input_is_punctuation = input_text in [".", ",", "!", "?", ":", ";"] or (
                len(input_text) > 0 and input_text[0] in [".", ",", "!", "?", ":", ";"]
            )
            
            # Fall 1: Erste Eingabe überhaupt
            if not sentence:
                sentence = input_text
            
            # Fall 2: Eingabe ist ein Satzzeichen
            elif input_is_punctuation:
                # Satzzeichen direkt ohne Leerzeichen anhängen
                sentence += input_text
                
                # Bei Satzendzeichen ein Leerzeichen nachträglich hinzufügen
                if any(input_text.endswith(c) for c in [".", "!", "?"]):
                    sentence += " "
            
            # Fall 3: Normale Eingabe mit Leerzeichen vorher
            elif sentence.endswith(" "):
                # Wenn der Satz bereits mit Leerzeichen endet, ohne weiteres anhängen
                sentence += input_text
            
            # Fall 4: Normale Eingabe ohne Leerzeichen vorher
            else:
                # Leerzeichen hinzufügen und dann die Eingabe
                sentence += " " + input_text
            
            # Kein zusätzlicher Puffer mehr - wir lassen die Leerzeichen-Handhabung dem Input überlassen
            
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
            
            # Behandlung von Satzzeichen im Modelloutput
            is_punctuation = next_word in [".", ",", "!", "?", ":", ";"] or next_word.startswith((".", ",", "!", "?"))
            
            # Prüfe, ob wir die drei Punkte "..." erhalten haben (Fallback)
            if next_word == "...":
                # Versuche es noch einmal mit einem anderen Prompt
                retry_word = get_next_word(
                    model_name, 
                    context + " [Bitte gib nur ein einzelnes Wort zurück]", 
                    temperature, 
                    api_logger
                )
                if retry_word and retry_word != "...":
                    next_word = retry_word
            
            # Handhabung des Outputs basierend auf Worttyp
            if is_punctuation:
                # Wenn es ein Satzzeichen ist, füge es ohne Leerzeichen hinzu
                sys.stdout.write(f"{next_word}")
                sys.stdout.flush()
                
                # Füge ein Leerzeichen nach dem Satzzeichen hinzu, wenn es ein Satzendzeichen ist
                if next_word in [".", "!", "?"]:
                    sys.stdout.write(" ")
                    sys.stdout.flush()
                    # Add the word to the sentence with space after
                    sentence += next_word + " "
                else:
                    # For commas and other punctuation, just add without trailing space
                    sentence += next_word
            else:
                # Check if the sentence already ends with a space
                needs_space = not sentence.endswith(" ")
                
                # Normales Wort ausgeben
                sys.stdout.write(next_word)
                
                # Leerzeichen nur hinzufügen, wenn nötig (vermeidet doppelte Leerzeichen)
                if needs_space:
                    sys.stdout.write(" ")
                    # Add the word to the sentence with space
                    sentence += " " + next_word
                else:
                    # Just add the word without extra space
                    sentence += next_word
                
                sys.stdout.flush()
    
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