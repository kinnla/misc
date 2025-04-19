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
    import os
    import select
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        
        # Use select with a timeout to avoid blocking indefinitely
        r, _, _ = select.select([sys.stdin], [], [], 0.1)
        if not r:
            # No input ready, return None
            return None
            
        # Input is ready, read it
        ch = sys.stdin.read(1)
        
        # Handle Ctrl+C (ASCII 3)
        if ch == '\x03':
            # Restore terminal settings before raising KeyboardInterrupt
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            raise KeyboardInterrupt()
            
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class TextState:
    """Class to maintain text state and handle display synchronization"""
    
    def __init__(self, debug_mode=False):
        self.text = ""
        self.debug_mode = debug_mode
    
    def debug(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug_mode:
            print(f"\n[DEBUG] {message}")
            # Restore prompt
            sys.stdout.write(f"\n> {self.text}")
            sys.stdout.flush()
    
    def append_text(self, text):
        """Append text and update display"""
        self.text += text
        sys.stdout.write(text)
        sys.stdout.flush()
    
    def append_with_space_check(self, text):
        """Append text with proper spacing, but don't write to screen"""
        # Check if we need a space before adding text in our internal state
        if self.text and not self.text.endswith(" ") and text and not text.startswith(tuple('.,!?:;')):
            # Add to internal state only
            self.text += " "
            # Don't write to screen as the user has already seen their input
        
        # Add to internal state only, don't write to screen again
        self.text += text
    
    def append_punctuation(self, punct):
        """Append punctuation mark correctly, but don't write to screen"""
        # For punctuation, we need to make sure:
        # 1. No space before the punctuation
        # 2. Add space after the punctuation
        # 3. The visual representation matches the internal state
        
        # Handle space before punctuation
        if self.text.endswith(" "):
            # Remove trailing space from internal state
            self.text = self.text[:-1]
            
            # Remove space from screen as well - go back one character
            sys.stdout.write("\b")
            sys.stdout.flush()
        
        # Add punctuation to internal state only
        self.text += punct
        
        # Add space after punctuation in internal state
        self.text += " "
        
        # Add space to display as well since the user hasn't seen it yet
        sys.stdout.write(" ")
        sys.stdout.flush()
    
    def append_ai_word(self, word):
        """Append AI generated word with proper formatting"""
        # Check if the word is a punctuation mark
        if word in ['.', ',', '!', '?', ':', ';'] or word.startswith(tuple('.,!?')):
            # For punctuation, remove trailing space if exists
            if self.text.endswith(" "):
                self.text = self.text[:-1]
                sys.stdout.write("\b")
                sys.stdout.flush()
                
            self.append_text(word)
            # Always add space after punctuation
            self.append_text(" ")
        else:
            # For regular words
            if not self.text.endswith(" "):
                self.append_text(" ")
                
            self.append_text(word)
            
            # Always add space after word to prepare for next input
            if not word.endswith(" "):
                self.append_text(" ")
    
    def get_user_input(self, block_input=False):
        """Get user input character by character, with real-time feedback
        
        Args:
            block_input: If True, don't accept any input (used when LLM is responding)
        """
        user_input = ""
        composing_umlaut = False  # Flag to track umlaut composition
        
        self.debug("Starting character input")
        
        while True:
            try:
                # Check if we should block input (when LLM is responding)
                if block_input:
                    # Just sleep a tiny bit and continue the loop
                    import time
                    time.sleep(0.01)
                    continue
                
                # Non-blocking read
                char = read_single_char()
                
                # No input available yet, continue loop
                if char is None:
                    continue
                    
                # Debug output
                if self.debug_mode:
                    try:
                        self.debug(f"Got char: {repr(char)}, ord: {ord(char)}")
                    except:
                        self.debug(f"Got unprintable char")
                
                # Special handling for backspace with umlaut composition
                if char in ['\b', '\x7f']:
                    # If we're in the middle of composing an umlaut, cancel the composition
                    if composing_umlaut:
                        composing_umlaut = False
                        continue
                        
                    if user_input:
                        # Special case for German umlauts
                        # Check if we're deleting an umlaut
                        last_char = user_input[-1]
                        if last_char in 'äöüÄÖÜ':
                            # Remove last character from input
                            user_input = user_input[:-1]
                            # And from display (backspace, space, backspace)
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                        else:
                            # Regular backspace behavior
                            user_input = user_input[:-1]
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    continue
                
                # Enter key ends input
                if char in ['\r', '\n']:
                    self.debug("Enter pressed, submitting")
                    break
                
                # Filter control characters
                if ord(char) < 32 and char not in ['\t']:
                    continue
                
                # Handle special character sequences
                # Check for possible dead keys used for umlaut composition
                if char in ['\xc2\xa8', '¨', '\xa8']:
                    composing_umlaut = True
                    self.debug("Umlaut composition detected")
                    continue
                
                # If we were composing an umlaut and got a regular vowel, convert it
                if composing_umlaut and char.lower() in 'aeiou':
                    umlaut_map = {
                        'a': 'ä', 'A': 'Ä',
                        'e': 'ë', 'E': 'Ë',
                        'i': 'ï', 'I': 'Ï',
                        'o': 'ö', 'O': 'Ö',
                        'u': 'ü', 'U': 'Ü'
                    }
                    # Replace with corresponding umlaut
                    char = umlaut_map.get(char, char)
                    composing_umlaut = False
                    self.debug(f"Composed umlaut: {char}")
                
                # Handle special cases
                
                # Single space when input is empty - just submit without adding space
                if char == ' ' and not user_input:
                    self.debug("Space with empty input, submitting without adding space")
                    break
                
                # Add character to input and display it
                user_input += char
                # We only write to stdout here, not to the text state
                # The actual text state update happens in process_user_input
                sys.stdout.write(char)
                sys.stdout.flush()
                
                # Auto-submit on punctuation
                if char in ['.', ',', '!', '?', ':', ';'] and ord(char) < 128:
                    self.debug(f"Punctuation detected: {char}, submitting")
                    break
                
                # Auto-submit on space
                if char == ' ':
                    self.debug("Space detected, submitting")
                    break
                    
            except Exception as e:
                self.debug(f"Error in input: {str(e)}")
                # Continue with input if we have something
                if user_input:
                    break
        
        self.debug(f"Final input: '{user_input}'")
        return user_input
    
    def process_user_input(self, input_text):
        """Process and add user input to state"""
        if not input_text:
            # Empty input, just continue
            return
            
        # Special case for punctuation
        if input_text in ['.', ',', '!', '?', ':', ';']:
            self.append_punctuation(input_text)
        else:
            # Normal text input
            self.append_with_space_check(input_text)
    
    def display_thinking(self):
        """Show thinking indicator"""
        sys.stdout.write("... ")
        sys.stdout.flush()
    
    def clear_thinking(self):
        """Clear thinking indicator"""
        sys.stdout.write("\b\b\b\b")
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

def is_input_ready():
    """Check if there's any input ready from stdin without blocking"""
    import select
    
    # Use select to check if there's input waiting on stdin
    # This is non-blocking - it just checks if there's input available
    r, _, _ = select.select([sys.stdin], [], [], 0)
    return len(r) > 0

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
        # Initialize text state
        state = TextState(debug_mode)
        
        # Start prompt
        sys.stdout.write("> ")
        sys.stdout.flush()
        
        # Indicator for LLM busy state
        llm_busy = False
        
        # Main interaction loop
        while True:
            # Get user input - block it if LLM is busy responding
            user_input = state.get_user_input(block_input=llm_busy)
            
            # Process user input
            state.process_user_input(user_input)
            
            # Use the text state as context
            context = state.text
            
            # Set LLM busy status to block input during processing
            llm_busy = True
            
            # Show thinking indicator 
            state.display_thinking()
            
            # Get the next word from the model
            next_word = get_next_word(model_name, context, temperature, api_logger)
            
            # Clear the thinking indicator
            state.clear_thinking()
            
            # Add AI word to text
            state.append_ai_word(next_word)
            
            # LLM is no longer busy - unblock input
            llm_busy = False
    
    except KeyboardInterrupt:
        print("\n\nDuett beendet. Finaler Text:")
        print(state.text)
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