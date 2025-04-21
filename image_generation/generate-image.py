#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

from diffusers import StableDiffusionPipeline
import torch
import random
import numpy as np

# Seed setzen
seed = 42
generator = torch.manual_seed(seed)
random.seed(seed)
np.random.seed(seed)

# Modell laden
model_id = "stabilityai/stable-diffusion-2"  # Anderes Modell? Passe dies an
#model_id = "flux1-dev.safetensors"
pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipeline = pipeline.to("mps")  # Verwende "cpu", falls keine GPU verfügbar ist

# Prompt definieren
prompt = "A serene forest with sunlight filtering through the trees, photorealistic"

# Bildparameter
height = 400  # Höhe des Bildes
width = 400   # Breite des Bildes
num_inference_steps = 20  # Qualität und Geschwindigkeit
guidance_scale = 7.5      # Einfluss des Prompts

# Bild generieren
print("Generiere ein Bild...")
image = pipeline(
    prompt, 
    num_inference_steps=num_inference_steps, 
    guidance_scale=guidance_scale, 
    height=height, 
    width=width,
    generator=generator
).images[0]

# Bild speichern
output_file = "generated_image.png"
image.save(output_file)
print(f"Bild gespeichert als {output_file}")