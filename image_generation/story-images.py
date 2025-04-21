#!/usr/bin/env python3
# coding: utf-8

import requests
import base64
import argparse
import re
import os

# Bildparameter
height = 480  # Höhe des Bildes
width = 270   # Breite des Bildes
num_inference_steps = 25  # Qualität und Geschwindigkeit
cfg_scale = 5.5      # Einfluss des Prompts
denoising_strength = 0.75
seed = 45
sampler_index = "Euler a"
negative_prompt = "blurry, distorted, deformed, asymmetrical face, extra limbs, extra eyes, bad anatomy, low quality, low resolution, missing facial features, wrong proportions, unnatural expression, poorly drawn face, poorly drawn hands, out of focus, grainy"
style = "artistic, professional studio setup, warm and vibrant colors, fashion editorial, high-res, friendly, most beautiful face, dark hair"
warmup_frames = 5

# URLs der lokalen Stable Diffusion-Instanz
url_txt2img = "http://127.0.0.1:7860/sdapi/v1/txt2img"
url_img2img = "http://127.0.0.1:7860/sdapi/v1/img2img"

# checkpoint
sd_model_checkpoint = "flux1-dev.safetensors [4610115bb0]"

# Funktion zur Speicherung des Base64-kodierten Bildes
def save_base64_image(image_data, output_file):
    if not image_data.startswith("data:image/png;base64,"):
        #print("Präfix fehlt, füge 'data:image/png;base64,' hinzu.")
        image_data = "data:image/png;base64," + image_data

    try:
        image_base64 = image_data.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
        with open(output_file, "wb") as image_file:
            image_file.write(image_bytes)
        print(f"Bild erfolgreich gespeichert: {output_file}")
    except Exception as e:
        print(f"Fehler beim Speichern des Bildes: {e}")

# Funktion zur Bildgenerierung über Text-zu-Bild
def generate_image_via_txt2img(prompt):
    payload = {
        "prompt": prompt,
        "steps": num_inference_steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "seed": seed,
        "sd_model_checkpoint": sd_model_checkpoint
    }
    response = requests.post(url_txt2img, json=payload)
    try:
        response_data = response.json()
    except ValueError:
        print("Fehler beim Parsen der Antwort:", response.text)
        return None

    if response.status_code == 200 and "images" in response_data:
        # Das erste Bild wird zurückgegeben
        return response_data["images"][0]
    else:
        print("Fehler bei der Text-zu-Bild-Anfrage:", response.text)
        return None

# Funktion zur Bildgenerierung über Bild-zu-Bild
def generate_image_via_img2img(prompt, init_image):
    payload = {
        "prompt": prompt,
        "init_images": [init_image],
        "steps": num_inference_steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "seed": seed,
        "denoising_strength": denoising_strength,
        "sampler_index": sampler_index,
        "sd_model_checkpoint": sd_model_checkpoint
    }
    response = requests.post(url_img2img, json=payload)
    try:
        response_data = response.json()
    except ValueError:
        print("Fehler beim Parsen der Antwort:", response.text)
        return None

    if response.status_code == 200 and "images" in response_data:
        return response_data["images"][0]
    else:
        print("Fehler bei der Bild-zu-Bild-Anfrage:", response.text)
        return None 

def main():
    parser = argparse.ArgumentParser(description='Generiere Bilder aus Text mit Kontextfenster.')
    parser.add_argument('text_file', help='Pfad zur Textdatei')
    parser.add_argument('--context_window', type=int, default=25, help='Größe des Kontextfensters (Standard: 30)')

    args = parser.parse_args()

    text_file = args.text_file
    context_window = args.context_window

    # Textdatei einlesen
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Text in Wörter aufteilen (split mit Leerzeichen und \n, dann Whitespace entfernen)
    words = re.split(r'\s+', text.strip())

    prev_output_file = None

    for i in range(len(words) - context_window + 1):
        prompt_words = words[i:i+context_window]
        prompt = ' '.join(prompt_words)
        prompt += "\n\n Style: "
        prompt += style

        print(f"Iteration {i + 1}: {prompt}")

        output_file = f"generated_image_{i+1:04}.png"

        if i == 0:
            # Erste Iteration: Text-zu-Bild generieren
            image_data = generate_image_via_txt2img(prompt=prompt)
            if image_data is None:
                print("Text-zu-Bild-Generierung fehlgeschlagen. Abbruch.")
                break

            # Das erste Bild speichern
            save_base64_image(image_data, output_file)

            # Innerer Loop für Bild-zu-Bild
            init_image = "data:image/png;base64," + image_data
            for j in range(warmup_frames):
                refined_image_data = generate_image_via_img2img(prompt=prompt, init_image=init_image)
                if refined_image_data is None:
                    print("Bild-zu-Bild-Generierung im inneren Loop fehlgeschlagen.")
                    break
                init_image = "data:image/png;base64," + refined_image_data
                save_base64_image(refined_image_data, output_file)

            prev_output_file = output_file
        else:
            # Folgende Iterationen: Normale Bild-zu-Bild Generierung
            with open(prev_output_file, "rb") as image_file:
                init_image_bytes = image_file.read()
            init_image_base64 = base64.b64encode(init_image_bytes).decode('utf-8')
            init_image = "data:image/png;base64," + init_image_base64

            image_data = generate_image_via_img2img(prompt=prompt, init_image=init_image)
            if image_data is not None:
                save_base64_image(image_data, output_file)
                prev_output_file = output_file
            else:
                print("Bildgenerierung fehlgeschlagen. Breche die Schleife ab.")
                break

if __name__ == "__main__":
    main()