#!/usr/bin/env python3
# coding: utf-8

import requests
import base64
import os
import datetime
import html

# Fixed seed
seed = 13357

# Image parameters
height = 1024
width = 1024
num_inference_steps = 30
cfg_scale = 7.0
sampler_index = "Euler a"

# URLs for local Stable Diffusion instance
url_txt2img = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# Checkpoint (remove if not available)
# sd_model_checkpoint = "flux1-dev.safetensors [4610115bb0]"

# List of positive prompts
positive_prompts = [
    "cat, dog, play, ball, piano, motion blur",
    "cozy room, elephant, clock, in the syle of Dali",
    "lovers, paradise beach, palm trees, clear sky, blue hour. In the style of Massimo Vitali",
    "A happy hippie playing guitar at a colorful picnic in a sunny meadow, surrounded by flowers, friends, and peaceful vibes. Boho outfits, flower crowns, love and rock energy in the air",
    "opera, stage, Papageno, Mozart, close-up, soft tone",
    "church, rome, pigeon, glass, holy, bible, god",
    "portrait, Dutch woman, confident, artist, look into the camera",
    "amazonas, forest, animals, trees, a bit of sun"
]

# List of negative prompts
negative_prompts = [
    "ugly face, blue, horror, mutation, geometry",
    "distorted, bad quality, draft, duplicated features",
    "extra digits, extra arms, extra hands, extra heads",
    "violence, fascism, war, hate, devil, brown",
    "nsfw, uncensored, explicit, nipples, kitsch, pink",
    "climate, heat wave, drought, flood, drown, hunger, fire",
    "watermark, text, incorrect ratio, indistinct"
]

def save_base64_image(image_data, output_file):
    """Save base64 encoded image to file"""
    if not image_data.startswith("data:image/png;base64,"):
        image_data = "data:image/png;base64," + image_data

    try:
        image_base64 = image_data.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
        with open(output_file, "wb") as image_file:
            image_file.write(image_bytes)
        print(f"Image saved: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

def generate_image_via_txt2img(positive_prompt, negative_prompt, current_seed):
    """Generate image using txt2img API with positive and negative prompts"""
    payload = {
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "steps": num_inference_steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "seed": current_seed,
        "sampler_index": sampler_index
    }
    
    print(f"Generating image with seed {current_seed}")
    response = requests.post(url_txt2img, json=payload)
    
    try:
        response_data = response.json()
    except ValueError:
        print(f"Error parsing response: {response.text}")
        return None

    if response.status_code == 200 and "images" in response_data:
        return response_data["images"][0]
    else:
        print(f"Error in txt2img request (Status {response.status_code}): {response.text}")
        if response.status_code == 404:
            print("API endpoint not found. Is Stable Diffusion WebUI running on http://127.0.0.1:7860?")
        return None

def generate_html_gallery(output_dir, positive_prompts, negative_prompts):
    """Generate HTML file displaying images in a matrix with prompts and interactive features"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dual AI Image Matrix Gallery</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .matrix-container {{
            display: grid;
            grid-template-columns: 250px repeat(var(--pos-count), 1fr);
            gap: 2px;
            max-width: 95vw;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .axis-label {{
            background-color: #333;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }}
        .corner-cell {{
            background-color: #666;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }}
        .image-cell {{
            position: relative;
            aspect-ratio: 1;
            border: 1px solid #ddd;
        }}
        .image-cell img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .image-cell:hover img {{
            transform: scale(1.05);
        }}
        .image-info {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 2px 4px;
            font-size: 10px;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        .image-cell:hover .image-info {{
            opacity: 1;
        }}
        .prompt-text {{
            font-size: 8px;
            text-align: center;
            padding: 3px;
            line-height: 1.1;
            overflow: hidden;
            word-wrap: break-word;
            hyphens: auto;
            max-height: 60px;
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }}
        .modal-content {{
            position: relative;
            margin: auto;
            padding: 20px;
            max-width: 90%;
            max-height: 90%;
            top: 50%;
            transform: translateY(-50%);
            text-align: center;
        }}
        .modal-images {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .modal-image-container {{
            max-width: 45%;
        }}
        .modal-image-container img {{
            max-width: 100%;
            max-height: 60vh;
            object-fit: contain;
        }}
        .modal-image-title {{
            color: white;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        .modal-info {{
            color: white;
            margin-top: 20px;
            font-size: 16px;
        }}
        .close {{
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        .close:hover {{
            color: white;
        }}
        .legend {{
            text-align: center;
            margin-bottom: 20px;
            padding: 10px;
            background-color: #e8f4f8;
            border-radius: 5px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dual AI Image Matrix Gallery</h1>
        <p>{len(positive_prompts)}×{len(negative_prompts)} matrix showing combinations of positive (horizontal) and negative (vertical) prompts</p>
        <div class="legend">
            <strong>Instructions:</strong> Hover over images to see reversed versions (positive ↔ negative). Click to view both versions side by side.
        </div>
    </div>
    
    <div class="matrix-container" style="--pos-count: {len(positive_prompts)};">
        <!-- Corner cell -->
        <div class="corner-cell">Pos→<br>↓Neg</div>
        
        <!-- Top row headers (positive prompts) -->"""

    # Add positive prompt headers
    for i, prompt in enumerate(positive_prompts, 1):
        escaped_prompt = html.escape(prompt)
        html_content += f"""
        <div class="axis-label">
            <div class="prompt-text" title="{escaped_prompt}">
                P{i}: {escaped_prompt}
            </div>
        </div>"""

    # Add rows
    for y in range(1, len(negative_prompts) + 1):
        # Negative prompt header
        neg_prompt = negative_prompts[y-1]
        escaped_neg_prompt = html.escape(neg_prompt)
        html_content += f"""
        <div class="axis-label">
            <div class="prompt-text" title="{escaped_neg_prompt}">
                N{y}: {escaped_neg_prompt}
            </div>
        </div>"""
        
        # Image cells for this row
        for x in range(1, len(positive_prompts) + 1):
            image_count = (x-1) * len(negative_prompts) + y
            filename_normal = f"x{x:02d}_y{y:02d}_{image_count:03d}.png"
            filename_reversed = f"x{x:02d}_y{y:02d}_{image_count:03d}_rev.png"
            pos_prompt = positive_prompts[x-1]
            neg_prompt = negative_prompts[y-1]
            
            html_content += f"""
        <div class="image-cell" 
             onmouseover="switchImage(this, '{filename_reversed}')" 
             onmouseout="switchImage(this, '{filename_normal}')">
            <img src="{filename_normal}" alt="x{x:02d}_y{y:02d}" 
                 onclick="openModal('{filename_normal}', '{filename_reversed}', '{html.escape(pos_prompt)}', '{html.escape(neg_prompt)}', {x}, {y})">
            <div class="image-info">x{x:02d}_y{y:02d}</div>
        </div>"""

    html_content += """
    </div>

    <!-- Modal -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div class="modal-images">
                <div class="modal-image-container">
                    <div class="modal-image-title">Normal (Positive as Positive)</div>
                    <img id="modalImageNormal" src="" alt="">
                </div>
                <div class="modal-image-container">
                    <div class="modal-image-title">Reversed (Positive as Negative)</div>
                    <img id="modalImageReversed" src="" alt="">
                </div>
            </div>
            <div class="modal-info">
                <div id="modalInfo"></div>
            </div>
        </div>
    </div>

    <script>
        function switchImage(element, newSrc) {
            const img = element.querySelector('img');
            img.src = newSrc;
        }

        function openModal(filenameNormal, filenameReversed, posPrompt, negPrompt, x, y) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImageNormal').src = filenameNormal;
            document.getElementById('modalImageReversed').src = filenameReversed;
            document.getElementById('modalInfo').innerHTML = 
                '<strong>Position:</strong> x' + x.toString().padStart(2, '0') + '_y' + y.toString().padStart(2, '0') + '<br>' +
                '<strong>Positive Prompt:</strong> ' + posPrompt + '<br>' +
                '<strong>Negative Prompt:</strong> ' + negPrompt;
        }

        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }

        // Close modal when clicking outside the image
        window.onclick = function(event) {
            const modal = document.getElementById('imageModal');
            if (event.target == modal) {
                closeModal();
            }
        }

        // Close modal with Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>"""

    # Write HTML file
    html_file = os.path.join(output_dir, "index.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML gallery created: {html_file}")
    return html_file

def main():
    # Check if API is reachable first
    try:
        test_response = requests.get("http://127.0.0.1:7860/sdapi/v1/progress", timeout=5)
        if test_response.status_code == 404:
            print("ERROR: Stable Diffusion WebUI API not found at http://127.0.0.1:7860")
            print("Please start the Stable Diffusion WebUI with --api flag")
            return
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Stable Diffusion WebUI at http://127.0.0.1:7860")
        print("Please start the Stable Diffusion WebUI with --api flag")
        return
    except requests.exceptions.Timeout:
        print("ERROR: Timeout connecting to Stable Diffusion WebUI")
        return
    
    # Create timestamped output directory
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    output_dir = f"{timestamp}-dual_matrix_output"
    os.makedirs(output_dir, exist_ok=True)
    
    total_images = len(positive_prompts) * len(negative_prompts) * 2  # Double for reversed versions
    print(f"Starting dual matrix generation with fixed seed {seed}")
    print(f"Output directory: {output_dir}")
    print(f"Generating {len(positive_prompts)}x{len(negative_prompts)} matrix: {total_images} images total (normal + reversed)")
    print(f"Image size: {width}x{height}, Steps: {num_inference_steps}, CFG: {cfg_scale}, Sampler: {sampler_index}")
    
    image_count = 0
    
    # Generate images for each x,y combination
    for x in range(1, len(positive_prompts) + 1):  # x: positive prompt
        for y in range(1, len(negative_prompts) + 1):  # y: negative prompt
            image_count += 1
            positive_prompt = positive_prompts[x-1]  # Convert to 0-based index
            negative_prompt = negative_prompts[y-1]  # Convert to 0-based index
            
            print(f"\nImage {image_count}/{total_images//2} (Normal) - x{x:02d}_y{y:02d}")
            print(f"Positive: {positive_prompt}")
            print(f"Negative: {negative_prompt}")
            
            # Generate normal image (positive as positive, negative as negative)
            image_data = generate_image_via_txt2img(positive_prompt, negative_prompt, seed)
            if image_data:
                output_file = os.path.join(output_dir, f"x{x:02d}_y{y:02d}_{image_count:03d}.png")
                save_base64_image(image_data, output_file)
            else:
                print(f"Failed to generate normal image x{x:02d}_y{y:02d}")
            
            print(f"\nImage {image_count}/{total_images//2} (Reversed) - x{x:02d}_y{y:02d}")
            print(f"Positive (as negative): {positive_prompt}")
            print(f"Negative (as positive): {negative_prompt}")
            
            # Generate reversed image (positive as negative, negative as positive)
            image_data_reversed = generate_image_via_txt2img(negative_prompt, positive_prompt, seed)
            if image_data_reversed:
                output_file_reversed = os.path.join(output_dir, f"x{x:02d}_y{y:02d}_{image_count:03d}_rev.png")
                save_base64_image(image_data_reversed, output_file_reversed)
            else:
                print(f"Failed to generate reversed image x{x:02d}_y{y:02d}")
    
    print(f"\nDual matrix generation completed. {image_count * 2} images saved in {output_dir}")
    
    # Generate HTML gallery
    print("\nGenerating HTML gallery...")
    generate_html_gallery(output_dir, positive_prompts, negative_prompts)
    print(f"Open {output_dir}/index.html in your browser to view the gallery")

if __name__ == "__main__":
    import sys
    
    # Check if user wants to generate HTML only
    if len(sys.argv) > 1 and sys.argv[1] == "--html-only":
        if len(sys.argv) < 3:
            print("Usage: python dual-batch-generate.py --html-only <output_directory>")
            print("Example: python dual-batch-generate.py --html-only 2025-06-01-2231-dual_matrix_output")
            sys.exit(1)
        
        output_dir = sys.argv[2]
        if not os.path.exists(output_dir):
            print(f"Error: Directory '{output_dir}' does not exist")
            sys.exit(1)
        
        print(f"Generating HTML gallery for existing images in {output_dir}")
        generate_html_gallery(output_dir, positive_prompts, negative_prompts)
        print(f"Open {output_dir}/index.html in your browser to view the gallery")
    else:
        main()