#!/usr/bin/env python3
# coding: utf-8
# A simplified version of image evolution that uses stable diffusion img2img directly

import base64
import argparse
import os
import datetime
import logging
from PIL import Image
import requests

# URLs for local Stable Diffusion instance
url_img2img = "http://127.0.0.1:7860/sdapi/v1/img2img"

# Checkpoint
sd_model_checkpoint = "flux1-dev.safetensors [4610115bb0]"

# Function to save base64 encoded image
def save_base64_image(image_data, output_file):
    if not image_data.startswith("data:image/png;base64,"):
        image_data = "data:image/png;base64," + image_data

    try:
        image_base64 = image_data.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
        with open(output_file, "wb") as image_file:
            image_file.write(image_bytes)
        logging.info(f"Image successfully saved: {output_file}")
        return True
    except Exception as e:
        logging.error(f"Error saving image: {e}")
        return False

# Function to load an image and convert to base64
def load_image_as_base64(image_path):
    try:
        # Open the image to get its dimensions
        with Image.open(image_path) as img:
            width, height = img.size
            logging.info(f"Image dimensions: {width}x{height}")
        
        # Read binary data
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        return {"data": "data:image/png;base64," + image_base64, "width": width, "height": height}
    except Exception as e:
        logging.error(f"Error loading image: {e}")
        return None

# Function for image generation via img2img
def generate_image_via_img2img(prompt, image_data, negative_prompt, current_seed, 
                         num_inference_steps, cfg_scale, denoising_strength):
    # Extract image dimensions and base64 data
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
        "sampler_index": "Euler a",
        "sd_model_checkpoint": sd_model_checkpoint,
        "negative_prompt": negative_prompt
    }
    logging.info(f"Sending img2img request with seed {current_seed} and size {width}x{height}")
    response = requests.post(url_img2img, json=payload)
    try:
        response_data = response.json()
    except ValueError:
        logging.error(f"Error parsing response: {response.text}")
        return None

    if response.status_code == 200 and "images" in response_data:
        logging.info("Img2img request successful")
        return response_data["images"][0]
    else:
        logging.error(f"Error in img2img request: {response.text}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Image Echo: Generate sequence of images using img2img with the same prompt')
    parser.add_argument('image_path', help='Path to the initial image')
    parser.add_argument('--concept', help='Abstract concept to use as the prompt (optional)')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations (default: 10)')
    parser.add_argument('--output_dir', default='echo_output', help='Output directory for images')
    parser.add_argument('--seed', type=int, default=-1, help='Seed for image generation (default: 42)')
    parser.add_argument('--negative_prompt', default='text, letters, words, writing, font, character, alphabet, signature, watermark', help='Negative prompt for stable diffusion')
    parser.add_argument('--num_inference_steps', type=int, default=30, 
                        help='Number of inference steps (default: 30)')
    parser.add_argument('--denoising_strength', type=float, default=0.5, 
                        help='Denoising strength (default: 0.5)')
    parser.add_argument('--tweak_denoise', type=float, default=0.2,
                        help='Value to modify denoising strength by iteration (default: 0.2)')
    parser.add_argument('--cfg_scale', type=float, default=5, 
                        help='CFG scale (default: 5)')
    
    args = parser.parse_args()
    
    # Create timestamp for output directory
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    timestamped_output_dir = f"{timestamp}-{args.output_dir}"
    
    # Create output directory if it doesn't exist
    os.makedirs(timestamped_output_dir, exist_ok=True)
    
    # Set up logging
    log_file = os.path.join(timestamped_output_dir, "echo.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    concept_msg = f"concept: {args.concept}" if args.concept else "no concept provided"
    logging.info(f"Image echo started with {concept_msg}")
    
    # Copy the original image to the output directory
    import shutil
    output_first_image = os.path.join(timestamped_output_dir, "echo_001.png")
    shutil.copy2(args.image_path, output_first_image)
    logging.info(f"Original image copied to {output_first_image}")
    
    # Parameters for the series
    current_seed = args.seed
    concept = args.concept if args.concept else ""
    image_path = output_first_image
    max_iterations = args.iterations
    negative_prompt = args.negative_prompt
    
    # Check if the initial image exists
    if not os.path.exists(args.image_path):
        logging.error(f"Initial image {args.image_path} not found.")
        return
    
    # List for image paths
    image_paths = [output_first_image]
    
    # Log basic information
    logging.info(f"Initial image: {args.image_path}")
    logging.info(f"Seed: {current_seed}")
    logging.info(f"Max iterations: {max_iterations}")
    logging.info(f"Negative prompt: {negative_prompt}")
    logging.info(f"Num inference steps: {args.num_inference_steps}")
    logging.info(f"Denoising strength: {args.denoising_strength}")
    logging.info(f"Tweak denoise: {args.tweak_denoise}")
    logging.info(f"CFG scale: {args.cfg_scale}")
    
    # Iteration loop
    for i in range(max_iterations):
        logging.info(f"Iteration {i+1}/{max_iterations} started")
        current_image_path = image_paths[-1]
        
        # Prompt for image generation
        prompt = concept
        
        # Load the current image as base64 with dimensions
        image_data = load_image_as_base64(current_image_path)
        if not image_data:
            logging.error("Error loading the image. Aborting.")
            break
        
        # Calculate adjusted denoising strength based on iteration
        adjusted_denoising_strength = args.denoising_strength - (args.tweak_denoise / (i+1))
        logging.info(f"Adjusted denoising strength for iteration {i+1}: {adjusted_denoising_strength}")
        
        # Generate new image using the current image as a base
        new_image_data = generate_image_via_img2img(
            prompt, image_data, negative_prompt, current_seed,
            args.num_inference_steps, args.cfg_scale, adjusted_denoising_strength
        )
        if not new_image_data:
            logging.error("Error generating image. Aborting.")
            break
        
        # Save the new image
        new_image_path = os.path.join(timestamped_output_dir, f"echo_{i+2:03d}.png")
        if save_base64_image(new_image_data, new_image_path):
            image_paths.append(new_image_path)
            logging.info(f"Image {i+2} saved to {new_image_path}")
        else:
            logging.error("Error saving the image. Aborting.")
            break
    
    # Summary of the echo process
    logging.info("\nImage echo process completed")
    logging.info(f"Number of iterations: {len(image_paths) - 1}")
    logging.info(f"Initial image: {image_paths[0]}")
    logging.info(f"Final image: {image_paths[-1]}")
    logging.info(f"All results have been saved in directory {timestamped_output_dir}.")

if __name__ == "__main__":
    main()