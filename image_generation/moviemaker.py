#!/usr/bin/env python3
# coding: utf-8

import argparse
import requests
import base64
import time
import os
from PIL import Image

# --- Stable Diffusion-Einstellungen ---
URL_TXT2IMG = "http://127.0.0.1:7860/sdapi/v1/txt2img"
URL_IMG2IMG = "http://127.0.0.1:7860/sdapi/v1/img2img"
SD_MODEL_CHECKPOINT = "flux1-dev.safetensors [4610115bb0]"

# --- Standard-Bildparameter ---
HEIGHT = 1024
WIDTH = 512
NUM_INFERENCE_STEPS = 25
SAMPLER_INDEX = "Euler a"
STYLE = "artistic, professional studio setup, warm and vibrant colors, fashion editorial, high-res, friendly, most beautiful face, dark hair"
WARMUP_FRAMES = 5

# --- Parameter für Prompt-Einfluss ---
CFG_SCALE_DEFAULT = 5.5
DENOISING_DEFAULT = 0.59

def save_base64_image(image_data: str, output_file: str):
    """Base64-codiertes PNG dekodieren und speichern."""
    if not image_data.startswith("data:image/png;base64,"):
        image_data = "data:image/png;base64," + image_data
    try:
        image_base64 = image_data.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
        with open(output_file, "wb") as image_file:
            image_file.write(image_bytes)
        print(f"[INFO] Bild erfolgreich gespeichert: {output_file}")
    except Exception as e:
        print(f"[ERROR] Fehler beim Speichern des Bildes: {e}")

def generate_image_via_txt2img(prompt: str, cfg_scale: float) -> str:
    """Sendet ein txt2img-Request an die lokale SD-API und gibt das base64-Bild zurück."""
    payload = {
        "prompt": prompt,
        "steps": NUM_INFERENCE_STEPS,
        "cfg_scale": cfg_scale,
        "width": WIDTH,
        "height": HEIGHT,
        "seed": -1,
        "sd_model_checkpoint": SD_MODEL_CHECKPOINT
    }
    try:
        response = requests.post(URL_TXT2IMG, json=payload)
        response.raise_for_status()
        response_data = response.json()
        if "images" in response_data:
            return response_data["images"][0]
        else:
            print("[ERROR] Keine 'images' in der Antwort enthalten.")
            return None
    except Exception as e:
        print(f"[ERROR] txt2img fehlgeschlagen: {e}")
        return None

def generate_image_via_img2img(prompt: str, init_image: str, cfg_scale: float, denoising_strength: float) -> str:
    """Sendet ein img2img-Request an die lokale SD-API und gibt das base64-Bild zurück."""
    payload = {
        "prompt": prompt,
        "init_images": [init_image],
        "steps": NUM_INFERENCE_STEPS,
        "cfg_scale": cfg_scale,
        "width": WIDTH,
        "height": HEIGHT,
        "seed": -1,
        "denoising_strength": denoising_strength,
        "sampler_index": SAMPLER_INDEX,
        "sd_model_checkpoint": SD_MODEL_CHECKPOINT
    }
    try:
        response = requests.post(URL_IMG2IMG, json=payload)
        response.raise_for_status()
        response_data = response.json()
        if "images" in response_data:
            return response_data["images"][0]
        else:
            print("[ERROR] Keine 'images' in der Antwort enthalten.")
            return None
    except Exception as e:
        print(f"[ERROR] img2img fehlgeschlagen: {e}")
        return None

def read_prompt_file(filename: str) -> str:
    """Liest den Inhalt einer Textdatei ein und gibt ihn als String zurück."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"[ERROR] Konnte Prompt-Datei nicht lesen: {e}")
        return ""

def encode_image_to_base64(image_path: str) -> str:
    """Konvertiert eine PNG-Datei in einen base64-String."""
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        return "data:image/png;base64," + image_base64
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden des Startbildes: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Stable Diffusion Endlosschleife ohne GUI.")
    parser.add_argument("--prompt-file", default="prompt.txt",
                        help="Pfad zur Prompt-Textdatei (Standard: prompt.txt)")
    parser.add_argument("--start-image", default=None,
                        help="Optionaler Pfad zu einem PNG-Startbild (img2img).")
    parser.add_argument("--cfg-scale", type=float, default=CFG_SCALE_DEFAULT,
                        help=f"CFG Scale (Standard: {CFG_SCALE_DEFAULT})")
    parser.add_argument("--denoising-strength", type=float, default=DENOISING_DEFAULT,
                        help=f"Denoising Strength (Standard: {DENOISING_DEFAULT})")

    args = parser.parse_args()

    prompt_file = args.prompt_file
    start_image_path = args.start_image
    cfg_scale = args.cfg_scale
    denoising_strength = args.denoising_strength

    # Aktueller Prompt + Startbild (base64)
    last_prompt = None
    current_init_image = None
    image_counter = 1

    # Falls gewünscht, Startbild einlesen
    if start_image_path and os.path.isfile(start_image_path):
        current_init_image = encode_image_to_base64(start_image_path)
        print(f"[INFO] Starte mit angegebenem Startbild: {start_image_path}")
    else:
        print("[INFO] Kein Startbild angegeben. Zuerst wird txt2img ausgeführt.")

    print(f"[INFO] Lese Prompt aus Datei: {prompt_file}")
    print("[INFO] Drücke STRG+C zum Abbrechen.\n")

    while True:
        # Prompt aus Datei lesen
        new_prompt = read_prompt_file(prompt_file)
        # Kombiniere Prompt mit Style
        prompt_with_style = new_prompt + "\n\nStyle: " + STYLE

        # Prüfe, ob sich der Prompt geändert hat oder ob wir noch gar keinen init_image haben
        if new_prompt != last_prompt or current_init_image is None:
            print("[INFO] Neuer Prompt erkannt oder kein init_image vorhanden. -> txt2img")
            image_data = generate_image_via_txt2img(prompt_with_style, cfg_scale)
            if image_data is None:
                print("[ERROR] txt2img schlug fehl. Warte 3 Sekunden und versuche erneut.")
                time.sleep(3)
                continue
            current_init_image = "data:image/png;base64," + image_data

            # Speichere das Bild
            output_file = f"generated_image_{image_counter:04}.png"
            save_base64_image(image_data, output_file)

            # Optionaler Warmup
            for j in range(WARMUP_FRAMES):
                print(f"[INFO] Warmup {j+1}/{WARMUP_FRAMES} (img2img)")
                refined_data = generate_image_via_img2img(prompt_with_style, current_init_image,
                                                          cfg_scale, denoising_strength)
                if refined_data is None:
                    print("[ERROR] Warmup schlug fehl, breche Warmup ab.")
                    break
                current_init_image = "data:image/png;base64," + refined_data
                save_base64_image(refined_data, output_file)

            last_prompt = new_prompt
        else:
            print("[INFO] Prompt unverändert. -> img2img")
            image_data = generate_image_via_img2img(prompt_with_style, current_init_image,
                                                    cfg_scale, denoising_strength)
            if image_data is None:
                print("[ERROR] img2img schlug fehl. Warte 3 Sekunden und versuche erneut.")
                time.sleep(3)
                continue
            current_init_image = "data:image/png;base64," + image_data

            # Speichere das Bild
            output_file = f"generated_image_{image_counter:04}.png"
            save_base64_image(image_data, output_file)

        image_counter += 1

        # Kurze Wartezeit, bevor die Schleife erneut anläuft
        time.sleep(3)

if __name__ == "__main__":
    main()