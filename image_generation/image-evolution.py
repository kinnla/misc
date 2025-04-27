#!/usr/bin/env python3
# coding: utf-8
# Updated to include logging and timestamped output directories (2025-04-27)

import base64
import argparse
import os
import json
from difflib import SequenceMatcher
from PIL import Image
import io
import anthropic
import datetime
import logging

# Parameter für Bildgenerierung
num_inference_steps = 25  # Qualität und Geschwindigkeit
cfg_scale = 5.5  # Einfluss des Prompts
denoising_strength = 0.7
seed = 42
sampler_index = "Euler a"
negative_prompt = "blurry, distorted, deformed, asymmetrical face, extra limbs, extra eyes, bad anatomy, low quality, low resolution, missing facial features, wrong proportions, unnatural expression, poorly drawn face, poorly drawn hands, out of focus, grainy"

# Parameter für Bildbeschreibung
image_description_prompt = "Provide a description of this image that could be used to recreate it. Focus on capturing all important visual elements, including subjects, style, composition, colors, lighting, and atmosphere. Be specific, thorough, and objective in your description. The description should be concise and not exceed {} words. Output like this: Futuristic Tokyo at night, neon lights reflecting in wet streets, cyberpunk aesthetic, detailed urban landscape, dramatic lighting, wide perspective."

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
        # Open the image to get its dimensions
        with Image.open(image_path) as img:
            width, height = img.size
            logging.info(f"Bildabmessungen: {width}x{height}")
        
        # Read binary data
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        return {"data": "data:image/png;base64," + image_base64, "width": width, "height": height}
    except Exception as e:
        logging.error(f"Fehler beim Laden des Bildes: {e}")
        return None

# Funktion zur Bildgenerierung über Bild-zu-Bild
def generate_image_via_img2img(prompt, image_data, current_seed):
    import requests
    
    # Extrahiere die Bildabmessungen und Base64-Daten
    init_image = image_data["data"]
    width = image_data["width"]
    height = image_data["height"]
    
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
    logging.info(f"Sende Bild-zu-Bild-Anfrage mit Seed {current_seed} und Größe {width}x{height}")
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
def describe_image_with_claude(image_path, api_key, current_seed, max_length=30):
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
                            "text": image_description_prompt.format(max_length)
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

# Funktion zum Prüfen, ob die Beschreibungsähnlichkeit über dem Schwellenwert liegt
def is_description_similar(descriptions, threshold):
    if len(descriptions) < 2:
        return False
    
    # Letzte beiden Beschreibungen vergleichen
    last_desc = descriptions[-1]
    second_last_desc = descriptions[-2]
    
    # Ähnlichkeit mit SequenceMatcher berechnen
    similarity_ratio = SequenceMatcher(None, last_desc, second_last_desc).ratio()
    
    logging.info(f"Ähnlichkeitsverhältnis: {similarity_ratio:.4f}")
    
    # Wenn die Ähnlichkeit größer als der Schwellenwert ist, sind die Beschreibungen zu ähnlich
    return similarity_ratio >= threshold

def main():
    parser = argparse.ArgumentParser(description='Bildevolution: Von Beschreibung zu Bild und zurück')
    parser.add_argument('image_path', help='Pfad zum Ausgangsbild')
    parser.add_argument('concept', help='Abstrakter Begriff, der der Bildbeschreibung hinzugefügt wird')
    parser.add_argument('--iterations', type=int, default=10, help='Anzahl der Iterationen (Standard: 10)')
    parser.add_argument('--similarity_threshold', type=float, default=0.95, help='Schwellenwert für das Ähnlichkeitsverhältnis, bei dem die Evolution stoppt (0-1, Standard: 0.95)')
    parser.add_argument('--output_dir', default='evolution_output', help='Ausgabeverzeichnis für die Bilder und Beschreibungen')
    parser.add_argument('--api_key', default=os.environ.get('ANTHROPIC_API_KEY'), help='Claude API-Schlüssel (wenn nicht als Umgebungsvariable ANTHROPIC_API_KEY gesetzt)')
    parser.add_argument('--seed', type=int, default=seed, help=f'Seed für die Bildgenerierung (Standard: {seed})')
    parser.add_argument('--max_description_length', type=int, default=50, help='Maximale Anzahl der Wörter in der Bildbeschreibung (Standard: 50)')
    
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
    
    # Kopiere das Originalbild in das Ausgabeverzeichnis
    import shutil
    output_first_image = os.path.join(timestamped_output_dir, "evolution_001.png")
    shutil.copy2(args.image_path, output_first_image)
    logging.info(f"Originalbild kopiert nach {output_first_image}")
    
    # Parameter für die Serie
    current_seed = args.seed
    abstract_concept = args.concept
    image_path = args.image_path
    max_iterations = args.iterations
    similarity_threshold = args.similarity_threshold
    
    # Validiere den Schwellenwert
    if similarity_threshold < 0 or similarity_threshold > 1:
        logging.warning(f"Ungültiger Schwellenwert {similarity_threshold}. Setze auf Standardwert 0.95.")
        similarity_threshold = 0.95
    
    # Überprüfen, ob das Ausgangsbild existiert
    if not os.path.exists(image_path):
        logging.error(f"Ausgangsbild {image_path} nicht gefunden.")
        return
    
    # Listen für Beschreibungen und Bildpfade
    descriptions = []
    image_paths = [output_first_image]
    
    # Grundlegende Informationen loggen
    logging.info(f"Ausgangsbild: {image_path}")
    logging.info(f"Seed: {current_seed}")
    logging.info(f"Max Iterationen: {max_iterations}")
    logging.info(f"Ähnlichkeitsschwellenwert: {similarity_threshold}")
    logging.info(f"Max Beschreibungslänge: {args.max_description_length} Wörter")
    
    # Iterationsschleife
    for i in range(max_iterations):
        logging.info(f"Iteration {i+1}/{max_iterations} gestartet")
        current_image_path = image_paths[-1]
        
        # 1. Bild beschreiben
        logging.info(f"Beschreibe Bild: {current_image_path}")
        description = describe_image_with_claude(current_image_path, args.api_key, current_seed, args.max_description_length)
        
        if not description:
            logging.error("Fehler bei der Bildbeschreibung. Breche ab.")
            break
        
        # Beschreibung speichern
        description_file = os.path.join(timestamped_output_dir, f"description_{i+1:03d}.txt")
        save_description(description, description_file)
        descriptions.append(description)
        logging.info(f"Beschreibung {i+1} gespeichert in {description_file}")
        
        # Prüfen, ob Beschreibungen zu ähnlich sind basierend auf Ähnlichkeitsverhältnis
        if is_description_similar(descriptions, similarity_threshold):
            logging.info(f"Beschreibungen sind zu ähnlich (Ähnlichkeitsverhältnis über Schwellenwert: {similarity_threshold}). Ende der Evolution erreicht.")
            break
            
        # Prompt für die Bildgenerierung
        prompt = f"{description}, {abstract_concept}."
        
        # 2. Neues Bild aus Beschreibung generieren
        logging.info(f"Generiere neues Bild aus Beschreibung mit Konzept: {abstract_concept}")
        
        # Lade das aktuelle Bild als Base64 mit Dimensionen
        # Dieses Bild wurde für die Beschreibung verwendet
        image_data = load_image_as_base64(current_image_path)
        if not image_data:
            logging.error("Fehler beim Laden des Bildes. Breche ab.")
            break
        
        # Generiere neues Bild mit dem aktuellen Bild als Basis
        # Das aktuelle Bild ist das, das für die Beschreibung verwendet wurde
        new_image_data = generate_image_via_img2img(prompt, image_data, current_seed)
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