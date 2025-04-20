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

def setup_logger(log_enabled=False, debug_mode=False):
    """Setup a unified logger for API interactions and debug messages
    
    Args:
        log_enabled: Whether to log API interactions
        debug_mode: Whether to log detailed debug information
        
    Returns:
        The logger object, or None if both logging modes are disabled
    """
    if not log_enabled and not debug_mode:
        return None
        
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create timestamp for filename
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
    
    # Create a single unified logger
    logger = logging.getLogger("duett_logger")
    
    # Set the lowest level needed
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    # Create a single log file with timestamp
    log_filename = os.path.join(logs_dir, f"{timestamp}_duett.log")
    file_handler = logging.FileHandler(log_filename)
    
    # Create formatter with source prefix
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    print(f"Logs will be saved to {log_filename}")
    
    return logger

def get_next_word(model_name, context, temperature=0.7, logger=None):
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
        if logger:
            logger.info(f"API REQUEST: {json.dumps(data, ensure_ascii=False)}")
        
        # Make the API request
        response = requests.post(OLLAMA_API, json=data)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        generated_text = result.get('response', '').strip()
        
        # Log API response if enabled
        if logger:
            logger.info(f"API RESPONSE: {json.dumps(result, ensure_ascii=False)}")
        
        # Extract just the first word
        if generated_text:
            words = generated_text.split()
            if words:
                return words[0]
        
        # Fallback if no meaningful word was generated
        return "[...]"
        
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        print(f"\nFehler bei der Verbindung zu Ollama: {e}")
        print("Ist Ollama installiert und läuft der Server? Starte Ollama mit 'ollama serve'")
        return "[...]"
    except Exception as e:
        print(f"\nFehler bei der Textgenerierung: {e}")
        return "[...]"

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
    
    def __init__(self, logger=None):
        self.text = ""
        self.logger = logger
    
    def debug(self, message):
        """Log debug message if logger is enabled"""
        if self.logger:
            self.logger.debug(message)
    
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
        """Append punctuation mark correctly, but don't write to screen again"""
        # For punctuation, we need to make sure it's added correctly to the internal state
        # The visual display has already been handled during input
        
        # Check for existing space before punctuation
        if self.text.endswith(" "):
            # Remove trailing space from internal state only
            self.text = self.text[:-1]
            # Don't modify the screen - already handled during input
        
        # Add punctuation to internal state
        self.text += punct
        
        # Add space after punctuation in internal state
        self.text += " "
        
        # Add space to display as well
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
                try:
                    self.debug(f"Got char: {repr(char)}, ord: {ord(char) if char else 'None'}")
                except:
                    self.debug(f"Got unprintable char")
                
                # Special handling for backspace with umlaut composition
                if char in ['\b', '\x7f']:
                    self.debug("Backspace detected")
                    # If we're in the middle of composing an umlaut, cancel the composition
                    if composing_umlaut:
                        composing_umlaut = False
                        self.debug("Cancelled umlaut composition")
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
                            self.debug(f"Deleted umlaut: '{last_char}'")
                        else:
                            # Regular backspace behavior
                            user_input = user_input[:-1]
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                            self.debug(f"Deleted character: '{last_char}'")
                    continue
                
                # Enter key ends input
                if char in ['\r', '\n']:
                    self.debug("Enter pressed, submitting")
                    break
                
                # Filter control characters
                if ord(char) < 32 and char not in ['\t']:
                    self.debug(f"Skipping control character: {ord(char)}")
                    continue
                
                # Handle special character sequences
                # Check for possible dead keys used for umlaut composition
                if char in ['\xc2\xa8', '¨', '\xa8']:
                    composing_umlaut = True
                    self.debug(f"Umlaut composition detected with char: {repr(char)}")
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
                        # Store original char for debugging
                    orig_char = char
                    # Replace with corresponding umlaut
                    char = umlaut_map.get(char, char)
                    composing_umlaut = False
                    self.debug(f"Composed umlaut: {orig_char} → {char}")
                
                # Handle special cases
                
                # Single space when input is empty - just submit without adding space
                if char == ' ' and not user_input:
                    self.debug("Space with empty input, submitting without adding space")
                    break
                
                # Handle punctuation specially - check if we need to remove leading space
                is_punctuation = char in ['.', ',', '!', '?', ':', ';'] and ord(char) < 128
                
                # Add character to input
                user_input += char
                self.debug(f"Current input buffer: '{user_input}'")
                
                # For all characters, just display them normally during input
                # We'll handle special formatting during processing
                sys.stdout.write(char)
                sys.stdout.flush()
                
                # Auto-submit on punctuation  
                if is_punctuation:
                    self.debug(f"Punctuation detected: {char}, submitting")
                    break
                
                # Auto-submit on space
                if char == ' ':
                    self.debug("Space detected, submitting")
                    break
                    
            except Exception as e:
                self.debug(f"Error in input: {str(e)}")
                self.debug(f"Exception details: {repr(e)}")
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
            
        # Check if input ends with punctuation
        ends_with_punct = input_text and input_text[-1] in ['.', ',', '!', '?', ':', ';']
        
        if len(input_text) == 1 and ends_with_punct:
            # Single punctuation character
            self.append_punctuation(input_text)
        elif ends_with_punct:
            # Word ending with punctuation - special handling
            # Split into word and punctuation
            word = input_text[:-1]
            punct = input_text[-1]
            
            # Add the word first
            self.append_with_space_check(word)
            
            # Then handle the punctuation correctly
            # For punctuation after a word, we need to:
            # 1. Remove any space that might have been added after the word
            if self.text.endswith(" "):
                self.text = self.text[:-1]
                # Go back one space on the screen to remove the visual space
                sys.stdout.write("\b")
                sys.stdout.flush()
                
            # 2. Add the punctuation
            self.text += punct
            
            # 3. Add a space after the punctuation
            self.text += " "
            # Add space to the screen
            sys.stdout.write(" ")
            sys.stdout.flush()
        else:
            # Normal text input without punctuation
            self.append_with_space_check(input_text)
    
    def display_thinking(self):
        """Show thinking indicator"""
        # Use a more visible thinking indicator that's easier to clear
        sys.stdout.write("[...]")
        sys.stdout.flush()
    
    def clear_thinking(self):
        """Clear thinking indicator"""
        # Go back 5 characters and clear them with spaces
        sys.stdout.write("\b\b\b\b\b")
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
    
    # Setup unified logger
    logger = setup_logger(args.log, args.debug)
    
    # Log start of session
    if logger:
        logger.debug("Starting new duet writing session")
        logger.debug(f"Command line args: {args}")
    
    # Validate temperature
    temperature = args.temp
    if temperature < 0.1 or temperature > 2.0:
        print("Warnung: Temperatur sollte zwischen 0.1 und 2.0 liegen. Verwende 0.7.")
        temperature = 0.7
        if logger:
            logger.debug(f"Invalid temperature {args.temp}, using 0.7 instead")
    
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
            
        print(f"Modell: {model_name}\n")
        
    except requests.exceptions.RequestException:
        print("Konnte keine Verbindung zu Ollama herstellen.")
        print("Bitte stelle sicher, dass Ollama installiert ist und läuft:")
        print("1. Installiere Ollama von https://ollama.com/")
        print("2. Starte den Ollama-Server mit 'ollama serve'")
        print("3. Lade ein Modell mit 'ollama pull llama3'")
        sys.exit(1)
    
    try:
        # Initialize text state with unified logger
        state = TextState(logger)
        
        # Start prompt
        sys.stdout.write("> ")
        sys.stdout.flush()
        
        # Indicator for LLM busy state
        llm_busy = False
        
        if logger:
            logger.debug("Ready for user input")
        
        # Main interaction loop
        while True:
            # Get user input - block it if LLM is busy responding
            user_input = state.get_user_input(block_input=llm_busy)
            
            if logger:
                logger.debug(f"Got user input: '{user_input}'")
            
            # Process user input
            state.process_user_input(user_input)
            
            # Use the text state as context
            context = state.text
            
            if logger:
                logger.debug(f"Current text state: '{context}'")
            
            # Set LLM busy status to block input during processing
            llm_busy = True
            
            if logger:
                logger.debug("LLM is now busy, blocking user input")
            
            # Show thinking indicator 
            state.display_thinking()
            
            if logger:
                logger.debug(f"Requesting next word from model '{model_name}' with temperature {temperature}")
            
            # Get the next word from the model
            next_word = get_next_word(model_name, context, temperature, logger)
            
            if logger:
                logger.debug(f"Model returned: '{next_word}'")
            
            # Clear the thinking indicator
            state.clear_thinking()
            
            # Sometimes the model returns "[...]" as a fallback
            if next_word == "[...]":
                if logger:
                    logger.debug("Got fallback response, trying again with clearer prompt")
                
                # Try once more with a clearer prompt
                next_attempt = get_next_word(
                    model_name,
                    context + " [Bitte gib ein einzelnes sinnvolles Wort zurück]",
                    temperature,
                    logger
                )
                
                if logger:
                    logger.debug(f"Second attempt returned: '{next_attempt}'")
                
                # Use the new result if it's not also "[...]"
                if next_attempt != "[...]":
                    next_word = next_attempt
                    if logger:
                        logger.debug(f"Using second attempt: '{next_word}'")
            
            # Add AI word to text
            state.append_ai_word(next_word)
            
            if logger:
                logger.debug(f"Updated text state: '{state.text}'")
            
            # LLM is no longer busy - unblock input
            llm_busy = False
            
            if logger:
                logger.debug("LLM is no longer busy, accepting user input")
    
    except KeyboardInterrupt:
        print("\n\nDuett beendet. Finaler Text:")
        print(state.text)
        if logger:
            logger.info("User terminated session with Ctrl+C")
            logger.info(f"Final text: {state.text}")
    except UnicodeError as e:
        print(f"\n\nEin Unicode-Fehler ist aufgetreten: {e}")
        print("Details:", repr(e))
        if logger:
            logger.error(f"Unicode error: {e}")
            logger.error(f"Error details: {repr(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nEin Fehler ist aufgetreten: {e}")
        print("Details:", repr(e))
        if logger:
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Error details: {repr(e)}")
            logger.error(f"Stack trace:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()