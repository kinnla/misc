#!/usr/bin/env python3
# coding: utf-8

import ollama
import requests
import base64

# Bildparameter
height = 480  # Höhe des Bildes
width = 270   # Breite des Bildes
num_inference_steps = 20  # Qualität und Geschwindigkeit
guidance_scale = 6.5      # Einfluss des Prompts
seed = 42

# URLs der lokalen Stable Diffusion-Instanz
url_txt2img = "http://127.0.0.1:7860/sdapi/v1/txt2img"
url_img2img = "http://127.0.0.1:7860/sdapi/v1/img2img"

# Ollama-Client initialisieren
client = ollama.Client()

# Funktion zur Interaktion mit dem Ollama-Modell
def interact_with_model(prompt, model_name="llama3.1"):
    try:
        response = client.generate(prompt=prompt, model=model_name, options={'temperature': 0.8})
        if response and 'response' in response:
            return response['response'].strip()
        else:
            print(f"Unerwartetes Antwortformat: {response}")
            return None
    except Exception as e:
        print(f"Fehler bei der Interaktion mit dem Modell: {e}")
        return None

# Funktion zur Speicherung des Base64-kodierten Bildes
def save_base64_image(image_data, output_file):
    if not image_data.startswith("data:image/png;base64,"):
        print("Präfix fehlt, füge 'data:image/png;base64,' hinzu.")
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
        "cfg_scale": guidance_scale,
        "width": width,
        "height": height,
        "seed": seed
    }
    response = requests.post(url_txt2img, json=payload)
    response_data = response.json()
    if response.status_code == 200 and "images" in response_data:
        # Das erste Bild wird zurückgegeben
        return response_data["images"][0]
    else:
        print("Fehler bei der Text-zu-Bild-Anfrage:", response.text)
        return None

# Funktion zur Bildgenerierung über Bild-zu-Bild
def generate_image_via_img2img(prompt, init_image, strength=0.6):
    payload = {
        "prompt": prompt,
        "steps": num_inference_steps,
        "cfg_scale": guidance_scale,
        "width": width,
        "height": height,
        "seed": seed,
        "init_images": [init_image],
        "strength": strength
    }
    response = requests.post(url_img2img, json=payload)
    response_data = response.json()
    if response.status_code == 200 and "images" in response_data:
        return response_data["images"][0]
    else:
        print("Fehler bei der Bild-zu-Bild-Anfrage:", response.text)
        return None

def main():
    # Initialer Satz
    sentence = "A blon haired, calm, 35 yr old canadian in a wooden hut, with a piano."
    static_prompt = (
        "We play a game. I will describe a person in a room, and you have to play with the words it contains. "
        "Change their order and add a detail, or remove one. Generate a modified version of that description, and just reply with "
        "the description (no further comments from you are needded). Here is the person im the room:"
    )

    # Variable zum Speichern des vorherigen Bildes
    prev_image = None

    # Schleife für 10 Iterationen
    for i in range(1000):
        print(f"Iteration {i + 1}: {sentence}")

        # Speichere 'sentence' als Textdatei
        txt_output_file = f"sentence_{i}.txt"
        with open(txt_output_file, 'w', encoding='utf-8') as file:
            file.write(sentence)

        # Bild generieren
        #print("Generiere ein Bild...")

        if prev_image is None:
            # Erste Iteration: Text-zu-Bild
            image_data = generate_image_via_txt2img(prompt=f"{sentence}, high res, photo")
        else:
            # Folgende Iterationen: Bild-zu-Bild
            image_data = generate_image_via_img2img(prompt=sentence, init_image=prev_image, strength=0.9)

        # Überprüfen, ob das Bild erfolgreich generiert wurde
        if image_data is not None:
            # Bild speichern
            output_file = f"generated_image{i:03}.png"
            save_base64_image(image_data, output_file)

            # Setze das aktuelle Bild als prev_image für die nächste Iteration
            prev_image = image_data
        else:
            print("Bildgenerierung fehlgeschlagen. Breche die Schleife ab.")
            break
        # Antwort generieren
        sentence = interact_with_model(prompt=static_prompt + "\n\n" + sentence)

        if not sentence:
            print("Keine gültige Antwort erhalten. Beende die Schleife.")
            break

if __name__ == "__main__":
    main()