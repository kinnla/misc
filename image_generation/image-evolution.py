#!/usr/bin/env python3
# coding: utf-8
# Updated to include logging and timestamped output directories (2025-04-27)

import base64
import argparse
import os
import json
import hashlib
from PIL import Image
import io
import anthropic
import datetime
import logging

# Bildparameter
width = 620  # Breite des Bildes (150 dpi)
height = 874  # Höhe des Bildes (150 dpi)
num_inference_steps = 25  # Qualität und Geschwindigkeit
cfg_scale = 5.5  # Einfluss des Prompts
denoising_strength = 0.75
seed = 42
sampler_index = "Euler a"
negative_prompt = "blurry, distorted, deformed, asymmetrical face, extra limbs, extra eyes, bad anatomy, low quality, low resolution, missing facial features, wrong proportions, unnatural expression, poorly drawn face, poorly drawn hands, out of focus, grainy"

# URLs der lokalen Stable Diffusion-Instanz
url_txt2img = "http://127.0.0.1:7860/sdapi/v1/txt2img"
url_img2img = "http://127.0.0.1:7860/sdapi/v1/img2img"

# Checkpoint
sd_model_checkpoint = "flux1-dev.safetensors [4610115bb0]"

# Claude API model
claude_model = "claude-3-7-sonnet-20250219"

# Funktion zur Speicherung des Base64-kodierten Bildes
def save_base64_image(image_data, output_file):
    if not image_data.startswith("data:image/png;base64,"):
        image_data = "data:image/png;base64," + image_data

    try:
        image_base64 = image_data.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
        with open(output_file, "wb") as image_file:
            image_file.write(image_bytes)
        logging.info(f"Bild erfolgreich gespeichert: {output_file}")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Speichern des Bildes: {e}")
        return False

# Funktion zum Laden eines Bildes und Konvertierung in Base64
def load_image_as_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        return "data:image/png;base64," + image_base64
    except Exception as e:
        logging.error(f"Fehler beim Laden des Bildes: {e}")
        return None

# Funktion zur Bildgenerierung über Bild-zu-Bild
def generate_image_via_img2img(prompt, init_image, current_seed):
    import requests
    
    payload = {
        "prompt": prompt,
        "init_images": [init_image],
        "steps": num_inference_steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "seed": current_seed,
        "denoising_strength": denoising_strength,
        "sampler_index": sampler_index,
        "sd_model_checkpoint": sd_model_checkpoint,
        "negative_prompt": negative_prompt
    }
    logging.info(f"Sende Bild-zu-Bild-Anfrage mit Seed {current_seed}")
    response = requests.post(url_img2img, json=payload)
    try:
        response_data = response.json()
    except ValueError:
        logging.error(f"Fehler beim Parsen der Antwort: {response.text}")
        return None

    if response.status_code == 200 and "images" in response_data:
        logging.info("Bild-zu-Bild-Anfrage erfolgreich")
        return response_data["images"][0]
    else:
        logging.error(f"Fehler bei der Bild-zu-Bild-Anfrage: {response.text}")
        return None

# Funktion zur Bildbeschreibung mit Claude
def describe_image_with_claude(image_path, api_key, current_seed):
    try:
        # Bild als Base64 laden
        with open(image_path, "rb") as img_file:
            img_bytes = img_file.read()
        
        # Bild als Base64 kodieren
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Bestimme Mime-Type (einfach als PNG annehmen für dieses Beispiel)
        image_media_type = "image/png"
        
        # Anthropic Client erstellen
        client = anthropic.Anthropic(api_key=api_key)
        
        logging.info(f"Sende Anfrage an Claude API mit Modell {claude_model}")
        # Anfrage an Claude senden
        message = client.messages.create(
            model=claude_model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_media_type,
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": "Provide a detailed description of this image that could be used to recreate it. Focus on capturing all important visual elements, including subjects, style, composition, colors, lighting, and atmosphere. Be specific, thorough, and objective in your description. Keep the description to 2-3 paragraphs maximum."
                        }
                    ]
                }
            ],
            temperature=0
        )
        
        # Beschreibung aus Claude's Antwort extrahieren
        description = message.content[0].text
        logging.info("Beschreibung von Claude erhalten")
        return description
    
    except Exception as e:
        logging.error(f"Fehler bei der Bildbeschreibung mit Claude: {e}")
        return None

# Funktion zum Speichern der Beschreibungen
def save_description(description, output_file):
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(description)
        logging.info(f"Beschreibung gespeichert: {output_file}")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Beschreibung: {e}")
        return False

# Funktion zum Prüfen auf Wiederholung
def is_description_repeated(descriptions):
    if len(descriptions) < 2:
        return False
    
    # Berechne Ähnlichkeit zwischen den letzten beiden Beschreibungen
    # Verwende einen einfachen Ansatz: Hash-basierter Vergleich
    last_hash = hashlib.md5(descriptions[-1].encode()).hexdigest()
    second_last_hash = hashlib.md5(descriptions[-2].encode()).hexdigest()
    
    # Alternativ könnte man hier auch komplexere Textähnlichkeitsalgorithmen verwenden
    return last_hash == second_last_hash

def main():
    parser = argparse.ArgumentParser(description='Bildevolution: Von Beschreibung zu Bild und zurück')
    parser.add_argument('image_path', help='Pfad zum Ausgangsbild')
    parser.add_argument('concept', help='Abstrakter Begriff, der der Bildbeschreibung hinzugefügt wird')
    parser.add_argument('--max_iterations', type=int, default=10, help='Maximale Anzahl von Iterationen (Standard: 10)')
    parser.add_argument('--output_dir', default='evolution_output', help='Ausgabeverzeichnis für die Bilder und Beschreibungen')
    parser.add_argument('--api_key', default=os.environ.get('ANTHROPIC_API_KEY'), help='Claude API-Schlüssel (wenn nicht als Umgebungsvariable ANTHROPIC_API_KEY gesetzt)')
    parser.add_argument('--seed', type=int, default=seed, help=f'Seed für die Bildgenerierung (Standard: {seed})')
    
    args = parser.parse_args()
    
    # Überprüfen, ob der API-Schlüssel vorhanden ist
    if not args.api_key:
        print("Fehler: Claude API-Schlüssel fehlt. Bitte über --api_key oder Umgebungsvariable ANTHROPIC_API_KEY angeben.")
        return
    
    # Zeitstempel für das Ausgabeverzeichnis erstellen
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    timestamped_output_dir = f"{timestamp}-{args.output_dir}"
    
    # Ausgabeverzeichnis erstellen, falls es nicht existiert
    os.makedirs(timestamped_output_dir, exist_ok=True)
    
    # Logging einrichten
    log_file = os.path.join(timestamped_output_dir, "evolution.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info(f"Bildevolution gestartet mit Konzept: {args.concept}")
    
    # Parameter für die Serie
    current_seed = args.seed
    abstract_concept = args.concept
    image_path = args.image_path
    max_iterations = args.max_iterations
    
    # Überprüfen, ob das Ausgangsbild existiert
    if not os.path.exists(image_path):
        logging.error(f"Ausgangsbild {image_path} nicht gefunden.")
        return
    
    # Listen für Beschreibungen und Bildpfade
    descriptions = []
    image_paths = [image_path]
    
    # Grundlegende Informationen loggen
    logging.info(f"Ausgangsbild: {image_path}")
    logging.info(f"Seed: {current_seed}")
    logging.info(f"Max Iterationen: {max_iterations}")
    
    # Iterationsschleife
    for i in range(max_iterations):
        logging.info(f"Iteration {i+1}/{max_iterations} gestartet")
        current_image_path = image_paths[-1]
        
        # 1. Bild beschreiben
        logging.info(f"Beschreibe Bild: {current_image_path}")
        description = describe_image_with_claude(current_image_path, args.api_key, current_seed)
        
        if not description:
            logging.error("Fehler bei der Bildbeschreibung. Breche ab.")
            break
        
        # Beschreibung speichern
        description_file = os.path.join(timestamped_output_dir, f"description_{i+1:03d}.txt")
        save_description(description, description_file)
        descriptions.append(description)
        logging.info(f"Beschreibung {i+1} gespeichert in {description_file}")
        
        # Prüfen, ob eine Beschreibung sich wiederholt
        if is_description_repeated(descriptions):
            logging.info("Eine Beschreibung hat sich wiederholt. Ende der Evolution erreicht.")
            break
        
        # 2. Neues Bild aus Beschreibung generieren
        # Füge den abstrakten Begriff zur Beschreibung hinzu
        prompt = f"{description}\n\nThe image conveys a sense of {abstract_concept}."
        logging.info(f"Generiere neues Bild aus Beschreibung mit Konzept: {abstract_concept}")
        
        # Lade aktuelles Bild als Base64
        init_image = load_image_as_base64(current_image_path)
        if not init_image:
            logging.error("Fehler beim Laden des Bildes. Breche ab.")
            break
        
        # Generiere neues Bild
        new_image_data = generate_image_via_img2img(prompt, init_image, current_seed)
        if not new_image_data:
            logging.error("Fehler bei der Bildgenerierung. Breche ab.")
            break
        
        # Speichere das neue Bild
        new_image_path = os.path.join(timestamped_output_dir, f"evolution_{i+2:03d}.png")
        if save_base64_image(new_image_data, new_image_path):
            image_paths.append(new_image_path)
            logging.info(f"Bild {i+2} gespeichert in {new_image_path}")
        else:
            logging.error("Fehler beim Speichern des Bildes. Breche ab.")
            break
    
    # Zusammenfassung der Evolution
    logging.info("\nBildevolution abgeschlossen")
    logging.info(f"Anzahl der Iterationen: {len(descriptions)}")
    logging.info(f"Ausgangsbild: {image_paths[0]}")
    logging.info(f"Endbild: {image_paths[-1]}")
    logging.info(f"Alle Ergebnisse wurden im Verzeichnis {timestamped_output_dir} gespeichert.")

if __name__ == "__main__":
    main()