"""
Perfume Visual Generator - Flask Backend
Генерирует стилизованные изображения парфюмов на основе описания
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import requests
import base64
import time
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Force reload of image_search module to ensure latest changes
if 'image_search' in sys.modules:
    del sys.modules['image_search']

from image_search import search_perfume_image

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

app = Flask(__name__)
CORS(app)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

if OPENAI_API_KEY:
    masked_key = OPENAI_API_KEY[:10] + '...' + OPENAI_API_KEY[-4:] if len(OPENAI_API_KEY) > 14 else '[SET]'
    print(f"[INIT] OpenAI API Key loaded: {masked_key}")
else:
    print(f"[INIT] WARNING: OPENAI_API_KEY not found in .env!")

if REPLICATE_API_TOKEN:
    masked_token = REPLICATE_API_TOKEN[:10] + '...' + REPLICATE_API_TOKEN[-4:] if len(REPLICATE_API_TOKEN) > 14 else '[SET]'
    print(f"[INIT] Replicate API Token loaded: {masked_token}")
else:
    print(f"[INIT] WARNING: REPLICATE_API_TOKEN not found in .env!")

# Folder configuration - use environment variables or defaults
MAIN_IMAGES_FOLDER = os.getenv('UPLOAD_FOLDER', 'main_images')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'main_images')  # For backwards compatibility
GENERATED_IMAGES_FOLDER = 'generated_images'
VIDEO_FOLDER = os.getenv('VIDEO_FOLDER', 'generated_videos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4'}

# Ensure folders exist
Path(MAIN_IMAGES_FOLDER).mkdir(exist_ok=True)
Path(GENERATED_IMAGES_FOLDER).mkdir(exist_ok=True)
Path(VIDEO_FOLDER).mkdir(exist_ok=True)

print(f"[INIT] Main images folder: {MAIN_IMAGES_FOLDER}")
print(f"[INIT] Generated images folder: {GENERATED_IMAGES_FOLDER}")
print(f"[INIT] Video folder: {VIDEO_FOLDER}")

# Store generation history
HISTORY_FILE = 'generation_history.json'

def load_history():
    """Load generation history from file"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(entry):
    """Save generation to history"""
    history = load_history()
    history.append(entry)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def search_perfume_image(brand, perfume_name):
    """
    Search for perfume bottle image using web search
    Returns URL of the best matching image
    """
    # Use web search or image database
    # For now, we'll use a placeholder approach
    search_query = f"{brand} {perfume_name} perfume bottle front view"
    
    # In production, integrate with Google Custom Search API or similar
    # For MVP, we'll return a mock URL or allow user to provide URL
    return None

def download_image(url, filename):
    """Download image from URL with retry logic"""
    max_retries = 3
    timeout = 30  # Increased timeout to 30 seconds
    
    for attempt in range(max_retries):
        try:
            print(f"[DOWNLOAD] Attempt {attempt + 1}/{max_retries}: Downloading from {url[:60]}...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"[DOWNLOAD] ✓ Image downloaded successfully: {len(response.content)} bytes")
            return filepath
            
        except requests.exceptions.Timeout:
            print(f"[DOWNLOAD] Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"[DOWNLOAD] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"[DOWNLOAD ERROR] Failed after {max_retries} attempts due to timeout")
                return None
                
        except Exception as e:
            print(f"[DOWNLOAD ERROR] Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return None
    
    return None

def remove_background_replicate(image_path):
    """Remove background using Google Nano Banana (Gemini 2.5 Flash) on Replicate via HTTP API"""
    if not REPLICATE_API_TOKEN:
        print("[WARNING] Replicate API token not found, skipping background removal")
        return image_path
    
    try:
        print(f"[NANO-BANANA] Starting background removal for: {image_path}")
        
        abs_path = os.path.abspath(image_path)
        output_path = image_path.replace('.jpg', '_nobg.png').replace('.jpeg', '_nobg.png')
        abs_output = os.path.abspath(output_path)
        
        print(f"[NANO-BANANA] Input: {abs_path}")
        print(f"[NANO-BANANA] Output: {abs_output}")
        
        # Read and encode image as base64
        with open(abs_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Create prediction via Replicate HTTP API
        print(f"[NANO-BANANA] Calling Google Gemini 2.5 Flash (Nano Banana) via HTTP API...")
        
        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Using Google Nano Banana via models API (automatically uses latest version)
        payload = {
            'input': {
                'prompt': 'In the image, there is a perfume bottle. Remove the background and keep only the bottle! Do not change any existing labels or text on the bottle, and do not add any new elements or writings.',
                'image_input': [f'data:image/jpeg;base64,{image_data}'],
                'aspect_ratio': '3:4',
                'output_format': 'png'
            }
        }
        
        # Start prediction with retry for rate limit
        max_retries = 3
        for retry in range(max_retries):
            response = requests.post(
                'https://api.replicate.com/v1/models/google/nano-banana/predictions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                break
            elif response.status_code == 429:
                # Rate limit - wait and retry
                retry_after = response.json().get('retry_after', 10)
                print(f"[NANO-BANANA] Rate limit hit, waiting {retry_after}s before retry {retry+1}/{max_retries}...")
                time.sleep(retry_after)
                continue
            else:
                print(f"[NANO-BANANA ERROR] Failed to create prediction: {response.status_code}")
                print(f"[NANO-BANANA ERROR] Response: {response.text}")
                return image_path
        
        if response.status_code != 201:
            print(f"[NANO-BANANA ERROR] Failed after {max_retries} retries")
            return image_path
        
        prediction = response.json()
        prediction_id = prediction['id']
        print(f"[NANO-BANANA] Prediction created: {prediction_id}")
        print(f"[NANO-BANANA] Using Gemini 2.5 Flash for intelligent background removal...")
        
        # Poll for result
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(2)
            
            response = requests.get(
                f'https://api.replicate.com/v1/predictions/{prediction_id}',
                headers=headers,
                timeout=30
            )
            
            prediction = response.json()
            status = prediction['status']
            
            print(f"[NANO-BANANA] Status: {status} (attempt {attempt+1}/{max_attempts})")
            
            if status == 'succeeded':
                output_url = prediction['output']
                print(f"[NANO-BANANA] Downloading result from: {output_url[:60]}...")
                
                result_response = requests.get(output_url, timeout=60)
                with open(abs_output, 'wb') as out:
                    out.write(result_response.content)
                
                print(f"[NANO-BANANA] ✓ Background removed successfully!")
                return output_path
            
            elif status == 'failed':
                print(f"[NANO-BANANA ERROR] Prediction failed: {prediction.get('error')}")
                return image_path
        
        print(f"[NANO-BANANA ERROR] Timeout waiting for result")
        return image_path
            
    except Exception as e:
        print(f"[NANO-BANANA ERROR] {e}")
        import traceback
        traceback.print_exc()
        return image_path

def remove_background_openai(image_path, custom_prompt=None):
    """Remove background using OpenAI GPT Image API via direct HTTP call"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    try:
        from PIL import Image
        import io
        
        print(f"[OpenAI] Starting background removal for: {image_path}")
        
        # Get absolute path
        abs_path = os.path.abspath(image_path)
        output_path = image_path.replace('.jpg', '_nobg.png').replace('.jpeg', '_nobg.png')
        abs_output = os.path.abspath(output_path)
        
        print(f"[OpenAI] Input: {abs_path}")
        print(f"[OpenAI] Output: {abs_output}")
        
        # Convert to PNG with RGBA (OpenAI requires RGBA format!)
        img = Image.open(abs_path)
        
        # Convert to RGBA (add alpha channel)
        if img.mode != 'RGBA':
            print(f"[OpenAI] Converting from {img.mode} to RGBA")
            img = img.convert('RGBA')
        
        # Resize if too large (max 4MB)
        if img.width > 1024 or img.height > 1024:
            print(f"[OpenAI] Resizing from {img.width}x{img.height} to fit 1024x1024")
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        # Convert to PNG in memory
        png_buffer = io.BytesIO()
        img.save(png_buffer, format='PNG')
        png_buffer.seek(0)
        png_data = png_buffer.read()
        
        print(f"[OpenAI] Converted to PNG RGBA: {len(png_data)} bytes ({len(png_data)/1024/1024:.2f} MB)")
        
        # Use custom prompt or default
        if custom_prompt:
            prompt = custom_prompt
            print(f"[OpenAI] Using CUSTOM prompt: {prompt[:80]}...")
        else:
            prompt = """Remove the background completely, leaving only the perfume bottle. 
        Make the background pure white or transparent. 
        Keep the perfume bottle sharp, detailed, and centered. 
        Preserve all text and labels on the bottle clearly."""
            print(f"[OpenAI] Using DEFAULT prompt")
        
        # Create multipart form data
        png_buffer.seek(0)
        files = {
            'image': ('image.png', png_buffer, 'image/png'),
            'model': (None, 'dall-e-2'),
            'prompt': (None, prompt),
            'n': (None, '1'),
            'size': (None, '1024x1024')
        }
        
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }
        
        # Call OpenAI API
        url = "https://api.openai.com/v1/images/edits"
        print(f"[OpenAI] Calling API...")
        
        response = requests.post(url, headers=headers, files=files, timeout=120)
        
        print(f"[OpenAI] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0].get('url')
                if image_url:
                    print(f"[OpenAI] Downloading result from: {image_url[:50]}...")
                    img_response = requests.get(image_url, timeout=30)
                    
                    with open(abs_output, 'wb') as f:
                        f.write(img_response.content)
                    
                    print(f"[OpenAI] ✓ Background removed successfully!")
                    return output_path
        
        print(f"[OpenAI] API error: {response.text[:300]}")
        return image_path
        
    except Exception as e:
        print(f"[OpenAI ERROR] Background removal failed: {e}")
        import traceback
        traceback.print_exc()
        return image_path

def stylize_with_stable_diffusion(image_path, description, custom_prompt=None):
    """Stylize image with new background using Google Nano Banana (Gemini 2.5 Flash) via HTTP API"""
    if not REPLICATE_API_TOKEN:
        raise ValueError("Replicate API token not configured")
    
    try:
        from PIL import Image
        import io
        
        print(f"[NANO-BANANA] Starting image stylization...")
        print(f"[NANO-BANANA] Input: {image_path}")
        
        # Create prompt
        if custom_prompt:
            prompt = custom_prompt.replace('{DESCRIPTION}', description[:400])
            print(f"[NANO-BANANA] Using CUSTOM prompt")
        else:
            prompt = f"""Transform this perfume bottle image by adding a stunning, vibrant, artistic background while keeping the bottle EXACTLY as it is - same shape, same color, same text, same position.

Create a beautiful atmospheric background that captures the mood and essence of this fragrance: {description[:200]}

The background should feature: vivid elegant colors with glowing bokeh lights in pink, purple, gold, and blue tones, soft dreamy blur, sophisticated luxury ambiance, professional studio lighting with colored gels, cinematic composition. Make it look like high-end commercial perfume advertising photography with magazine quality.

IMPORTANT: Do NOT change the perfume bottle itself - keep it identical to the input. Only transform the background behind it!"""
            print(f"[NANO-BANANA] Using DEFAULT prompt")
        
        print(f"[NANO-BANANA] Prompt: {prompt[:120]}...")
        
        # Read and encode image as base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Create prediction via Replicate HTTP API
        print(f"[NANO-BANANA] Calling Google Gemini 2.5 Flash for stylization...")
        
        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Using Google Nano Banana via models API (automatically uses latest version)
        payload = {
            'input': {
                'prompt': prompt,
                'image_input': [f'data:image/png;base64,{image_data}'],
                'aspect_ratio': '3:4',
                'output_format': 'png'
            }
        }
        
        # Start prediction with retry for rate limit
        max_retries = 3
        for retry in range(max_retries):
            response = requests.post(
                'https://api.replicate.com/v1/models/google/nano-banana/predictions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                break
            elif response.status_code == 429:
                # Rate limit - wait and retry
                retry_after = response.json().get('retry_after', 10)
                print(f"[NANO-BANANA] Rate limit hit, waiting {retry_after}s before retry {retry+1}/{max_retries}...")
                time.sleep(retry_after)
                continue
            else:
                print(f"[NANO-BANANA ERROR] Failed to create prediction: {response.status_code}")
                print(f"[NANO-BANANA ERROR] Response: {response.text}")
                return None
        
        if response.status_code != 201:
            print(f"[NANO-BANANA ERROR] Failed after {max_retries} retries")
            return None
        
        prediction = response.json()
        prediction_id = prediction['id']
        print(f"[NANO-BANANA] Prediction created: {prediction_id}")
        print(f"[NANO-BANANA] Using Gemini 2.5 Flash for intelligent image editing...")
        
        # Poll for result
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(3)
            
            response = requests.get(
                f'https://api.replicate.com/v1/predictions/{prediction_id}',
                headers=headers,
                timeout=30
            )
            
            prediction = response.json()
            status = prediction['status']
            
            print(f"[NANO-BANANA] Status: {status} (attempt {attempt+1}/{max_attempts})")
            
            if status == 'succeeded':
                output_url = prediction['output']
                print(f"[NANO-BANANA] Downloading result from: {str(output_url)[:60]}...")
                
                result_response = requests.get(output_url, timeout=60)
                generated_img = Image.open(io.BytesIO(result_response.content))
                
                print(f"[NANO-BANANA] ✓ Image stylized successfully!")
                return generated_img
            
            elif status == 'failed':
                print(f"[NANO-BANANA ERROR] Prediction failed: {prediction.get('error')}")
                return None
        
        print(f"[NANO-BANANA ERROR] Timeout waiting for result")
        return None
        
    except Exception as e:
        print(f"[NANO-BANANA ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

def create_styled_background_dalle3(description, custom_prompt=None):
    """Create styled background using DALL-E 3"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    try:
        print(f"[DALL-E 3] Creating styled background...")
        
        # Generate background prompt
        if custom_prompt:
            bg_prompt = custom_prompt.replace('{DESCRIPTION}', description[:400])
            print(f"[DALL-E 3] Using CUSTOM prompt")
        else:
            bg_prompt = f"""Create a beautiful, elegant abstract background for a perfume advertisement.
The mood and atmosphere should match this perfume: {description[:400]}

Style: Professional commercial photography background, sophisticated, atmospheric.
No text, no bottles, no products - only the background scenery.
High-end luxury advertising aesthetic. Blurred bokeh lights, soft focus, cinematic lighting.
1024x1024 square format."""
            print(f"[DALL-E 3] Using DEFAULT prompt")
        
        print(f"[DALL-E 3] Prompt preview: {bg_prompt[:120]}...")
        
        # Call DALL-E 3 API
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": bg_prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard"
        }
        
        print(f"[DALL-E 3] Calling API...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        print(f"[DALL-E 3] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and len(result['data']) > 0:
                bg_url = result['data'][0].get('url')
                print(f"[DALL-E 3] ✓ Background created!")
                
                # Download background
                bg_response = requests.get(bg_url, timeout=30)
                return bg_response.content
        
        print(f"[DALL-E 3] API error: {response.text[:200]}")
        return None
        
    except Exception as e:
        print(f"[DALL-E 3 ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

def composite_bottle_with_background(bottle_path, background_data):
    """Composite bottle image with generated background"""
    try:
        from PIL import Image
        import io
        
        print(f"[COMPOSITE] Compositing bottle with background...")
        
        # Load bottle (with transparent/white background)
        bottle = Image.open(bottle_path)
        if bottle.mode != 'RGBA':
            bottle = bottle.convert('RGBA')
        
        # Load background
        bg = Image.open(io.BytesIO(background_data))
        if bg.size != (1024, 1024):
            bg = bg.resize((1024, 1024), Image.Resampling.LANCZOS)
        if bg.mode != 'RGBA':
            bg = bg.convert('RGBA')
        
        # Resize bottle if needed
        if bottle.width > 1024 or bottle.height > 1024:
            bottle.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Calculate position to center bottle
        x = (bg.width - bottle.width) // 2
        y = (bg.height - bottle.height) // 2
        
        # Create composite
        result = bg.copy()
        result.paste(bottle, (x, y), bottle)
        
        print(f"[COMPOSITE] ✓ Composition complete!")
        return result
        
    except Exception as e:
        print(f"[COMPOSITE ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

def stylize_image_openai(image_path, description, custom_prompt=None):
    """Add styled background based on perfume description using OpenAI"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    try:
        from PIL import Image
        import io
        
        print(f"[OpenAI] Starting stylization for: {image_path}")
        
        # Get absolute path
        abs_path = os.path.abspath(image_path)
        # Replace _nobg with _styled (handle timestamp in filename)
        output_path = image_path.replace('_nobg', '_styled').replace('.jpg', '_styled.png').replace('.jpeg', '_styled.png')
        abs_output = os.path.abspath(output_path)
        
        print(f"[OpenAI] Input: {abs_path}")
        print(f"[OpenAI] Output: {abs_output}")
        
        # Convert to PNG with RGBA (OpenAI requires RGBA format!)
        img = Image.open(abs_path)
        
        # Convert to RGBA (add alpha channel)
        if img.mode != 'RGBA':
            print(f"[OpenAI] Converting from {img.mode} to RGBA")
            img = img.convert('RGBA')
        
        # Resize if too large (max 4MB)
        if img.width > 1024 or img.height > 1024:
            print(f"[OpenAI] Resizing from {img.width}x{img.height} to fit 1024x1024")
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        # Convert to PNG in memory
        png_buffer = io.BytesIO()
        img.save(png_buffer, format='PNG')
        png_buffer.seek(0)
        png_data = png_buffer.read()
        
        print(f"[OpenAI] Converted to PNG RGBA: {len(png_data)} bytes ({len(png_data)/1024/1024:.2f} MB)")
        
        # Use custom prompt or default with template
        if custom_prompt:
            # Replace {DESCRIPTION} placeholder with actual description
            style_prompt = custom_prompt.replace('{DESCRIPTION}', description[:350])
            print(f"[OpenAI] Using CUSTOM prompt template!")
            print(f"[OpenAI] Custom prompt length: {len(custom_prompt)} chars")
            print(f"[OpenAI] Final prompt length: {len(style_prompt)} chars")
        else:
            style_prompt = f"""Add a beautiful, elegant background that captures the essence and mood of this perfume:

{description[:350]}

Create sophisticated commercial photography with atmospheric colors and style matching the fragrance notes. 
Keep the perfume bottle centered, sharp, and as the main focus. Professional advertising quality."""
            print(f"[OpenAI] Using DEFAULT prompt (no custom provided)")
        
        print(f"[OpenAI] Final prompt preview: {style_prompt[:150]}...")
        print(f"[OpenAI] Sending to DALL-E 2...")
        
        # Create multipart form data
        png_buffer.seek(0)
        files = {
            'image': ('image.png', png_buffer, 'image/png'),
            'model': (None, 'dall-e-2'),
            'prompt': (None, style_prompt),
            'n': (None, '1'),
            'size': (None, '1024x1024')
        }
        
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }
        
        url = "https://api.openai.com/v1/images/edits"
        print(f"[OpenAI] Calling stylization API...")
        
        response = requests.post(url, headers=headers, files=files, timeout=120)
        
        print(f"[OpenAI] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0].get('url')
                if image_url:
                    print(f"[OpenAI] Downloading styled result...")
                    img_response = requests.get(image_url, timeout=30)
                    
                    with open(abs_output, 'wb') as f:
                        f.write(img_response.content)
                    
                    print(f"[OpenAI] ✓ Image stylized successfully!")
                    return output_path
        
        print(f"[OpenAI] API response: {response.text[:300]}")
        return image_path
        
    except Exception as e:
        print(f"[OpenAI ERROR] Stylization failed: {e}")
        import traceback
        traceback.print_exc()
        return image_path

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate styled perfume image"""
    try:
        data = request.json
        brand = data.get('brand', '').strip()
        perfume_name = data.get('perfume_name', '').strip()
        description = data.get('description', '').strip()
        image_url = data.get('image_url', '').strip()
        
        # Get custom prompts or use defaults
        prompt_background = data.get('prompt_background', '').strip()
        prompt_stylize = data.get('prompt_stylize', '').strip()
        
        print(f"[PROMPTS] Background prompt received: {len(prompt_background)} chars")
        print(f"[PROMPTS] Stylize prompt received: {len(prompt_stylize)} chars")
        if prompt_background:
            print(f"[PROMPTS] Background: {prompt_background[:100]}...")
        if prompt_stylize:
            print(f"[PROMPTS] Stylize: {prompt_stylize[:100]}...")
        
        # Validation
        if not all([brand, perfume_name, description]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Generate unique filename (sanitize for filesystem)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Remove special characters that can cause issues
        import re
        safe_brand = re.sub(r'[^\w\s-]', '', brand).strip().replace(' ', '_')
        safe_perfume = re.sub(r'[^\w\s-]', '', perfume_name).strip().replace(' ', '_')
        safe_name = f"{safe_brand}_{safe_perfume}"[:50]
        print(f"[FILENAME] Sanitized: '{brand} {perfume_name}' -> '{safe_name}'")
        
        # Step 1: Get image
        if image_url:
            print(f"[1/4] Downloading image from URL...")
            original_filename = f"{safe_name}_original_{timestamp}.jpg"
            original_path = download_image(image_url, original_filename)
            if not original_path:
                return jsonify({'error': 'Failed to download image from URL'}), 400
        else:
            # Try to find image automatically
            print(f"[1/4] Searching for perfume image...")
            found_url = search_perfume_image(brand, perfume_name)
            if found_url:
                original_filename = f"{safe_name}_original_{timestamp}.jpg"
                original_path = download_image(found_url, original_filename)
            else:
                return jsonify({'error': 'Please provide image URL (auto-search not yet implemented)'}), 400
        
        # Check if OpenAI is available
        if not OPENAI_API_KEY:
            print("[ERROR] OpenAI API key not configured!")
            generation_entry = {
                'timestamp': timestamp,
                'brand': brand,
                'perfume_name': perfume_name,
                'description': description,
                'original_image': original_filename if image_url else None,
                'final_image': f"{safe_name}_styled_{timestamp}.png",
                'status': 'pending'
            }
            save_history(generation_entry)
            
            return jsonify({
                'success': True,
                'message': 'OpenAI API not configured',
                'data': {
                    'brand': brand,
                    'perfume_name': perfume_name,
                    'timestamp': timestamp,
                    'image_url': image_url,
                    'requires_manual_processing': True,
                    'original_filename': original_filename if image_url else None
                }
            })
        
        # Step 2: Remove background using Nano Banana (Gemini 2.5 Flash)
        print(f"[2/4] Removing background with Nano Banana...")
        try:
            nobg_result = remove_background_replicate(original_path)
            nobg_filename = f"{safe_name}_nobg_{timestamp}.png"
            nobg_path = os.path.join(GENERATED_IMAGES_FOLDER, nobg_filename)
            
            if nobg_result != original_path:
                # Background was removed, save it
                import shutil
                if nobg_result != nobg_path:
                    shutil.copy(nobg_result, nobg_path)
                else:
                    nobg_path = nobg_result
                print(f"[SUCCESS] Background removed: {nobg_filename}")
            else:
                # Function returned same path, use original
                nobg_path = original_path
                print(f"[WARNING] Background removal skipped, using original")
        except Exception as e:
            print(f"[ERROR] Failed to remove background: {e}")
            nobg_path = original_path
        
        # Step 3: Stylize with Nano Banana (Gemini 2.5 Flash)
        print(f"[3/4] Stylizing with Nano Banana...")
        final_filename = f"{safe_name}_styled_{timestamp}.png"
        final_path = os.path.join(GENERATED_IMAGES_FOLDER, final_filename)
        
        try:
            # Stylize with Nano Banana (Gemini 2.5 Flash)
            styled_image = stylize_with_stable_diffusion(nobg_path, description, prompt_stylize or None)
            
            if styled_image:
                # Save result
                styled_image.save(final_path, 'PNG')
                print(f"[SUCCESS] Image stylized with Nano Banana: {final_filename}")
            else:
                # Stylization failed, copy original
                import shutil
                shutil.copy(original_path, final_path)
                print(f"[WARNING] Nano Banana failed, using original")
                
        except Exception as e:
            print(f"[ERROR] Failed to stylize: {e}")
            import traceback
            traceback.print_exc()
            import shutil
            shutil.copy(original_path, final_path)
        
        # Step 4: Save to history
        print(f"[4/4] Saving to history...")
        generation_entry = {
            'timestamp': timestamp,
            'brand': brand,
            'perfume_name': perfume_name,
            'description': description,
            'original_image': original_filename if image_url else None,
            'final_image': final_filename,
            'status': 'completed'
        }

        save_history(generation_entry)

        # Update database with styled image path if product_id is provided
        product_id = data.get('product_id')
        if product_id:
            try:
                import sqlite3
                db_path = os.getenv('DB_PATH', 'fragrantica_news.db')

                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute('''
                        UPDATE randewoo_products
                        SET styled_image_path = ?
                        WHERE id = ?
                    ''', (final_filename, product_id))

                    conn.commit()
                    conn.close()

                    print(f"[DB] Updated styled_image_path for product {product_id}: {final_filename}")
            except Exception as e:
                print(f"[DB ERROR] Failed to update styled_image_path: {e}")

        return jsonify({
            'success': True,
            'message': 'Image generated successfully',
            'data': {
                'brand': brand,
                'perfume_name': perfume_name,
                'timestamp': timestamp,
                'image_url': f'/images/{final_filename}',
                'requires_manual_processing': False,
                'original_filename': original_filename if image_url else None,
                'final_filename': final_filename
            }
        })
        
    except Exception as e:
        print(f"Error in generate: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-with-mcp', methods=['POST'])
def process_with_mcp():
    """
    Endpoint to receive results from MCP tool processing
    This is called after manual MCP tool invocation
    """
    try:
        data = request.json
        final_image_path = data.get('final_image_path')
        timestamp = data.get('timestamp')
        
        # Update history
        history = load_history()
        for entry in history:
            if entry['timestamp'] == timestamp:
                entry['status'] = 'completed'
                entry['final_image_path'] = final_image_path
                break
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    """Get generation history"""
    history = load_history()
    return jsonify(history)

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from main_images or generated_images folder"""
    # Try main_images first (where main product images are stored)
    main_path = os.path.join(MAIN_IMAGES_FOLDER, filename)
    if os.path.exists(main_path):
        return send_from_directory(MAIN_IMAGES_FOLDER, filename)

    # Try generated_images (where styled images are stored)
    gen_path = os.path.join(GENERATED_IMAGES_FOLDER, filename)
    if os.path.exists(gen_path):
        return send_from_directory(GENERATED_IMAGES_FOLDER, filename)

    # Fallback to UPLOAD_FOLDER for backwards compatibility
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/search-image', methods=['POST'])
def search_image():
    """Search for perfume bottle image using OpenAI"""
    print("[API] /api/search-image endpoint called")
    
    # Force reload module to get latest changes (fix for Flask caching)
    import importlib
    import image_search
    importlib.reload(image_search)
    from image_search import search_perfume_image as search_fn
    print("[API] image_search module reloaded!")
    
    try:
        # Get request data
        print("[API] Getting request data...")
        data = request.json
        print(f"[API] Request data: {data}")
        
        if not data:
            print("[API] ERROR: No data provided")
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'message': 'Request body is empty'
            }), 400
        
        brand = data.get('brand', '').strip()
        perfume_name = data.get('perfume_name', '').strip()
        print(f"[API] Brand: '{brand}', Perfume: '{perfume_name}'")
        
        if not brand or not perfume_name:
            print("[API] ERROR: Missing brand or perfume name")
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'message': 'Brand and perfume name are required'
            }), 400
        
        print(f"[API] Calling search_fn({brand}, {perfume_name})...")
        
        # Search using Google Custom Search API
        try:
            result = search_fn(brand, perfume_name)
            print(f"[API] search_perfume_image returned: {result}")
            
            # Check if result is None
            if result is None:
                print("[API] ERROR: search_perfume_image returned None!")
                return jsonify({
                    'success': False,
                    'error': 'No result from search function',
                    'message': 'Internal error: search function returned None. Check server logs.'
                }), 500
            
            # Check if result is a dict
            if not isinstance(result, dict):
                print(f"[API] ERROR: search_perfume_image returned non-dict: {type(result)}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid result type',
                    'message': f'Internal error: search returned {type(result)} instead of dict'
                }), 500
                
        except Exception as search_error:
            print(f"[API] ERROR in search_perfume_image: {search_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(search_error),
                'message': f'Error during image search: {str(search_error)}'
            }), 500
        
        # Ensure result has success field
        if 'success' not in result:
            print("[API] WARNING: Result missing 'success' field, adding it")
            result['success'] = False
        
        print(f"[API] Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"[API] FATAL ERROR in search_image endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error during image search'
        }), 500

def generate_video_concept_with_claude(brand, perfume_name, description):
    """
    Generate video concept using Claude 4.5 Sonnet via Replicate
    
    Returns:
        dict with concept and prompt for Seedance-1-pro
    """
    if not REPLICATE_API_TOKEN:
        raise ValueError("Replicate API token not configured")
    
    try:
        print(f"[CLAUDE] Generating video concept for {brand} {perfume_name}...")
        
        # Create prompt for Claude
        claude_prompt = f"""Придумай интересный однокадровый визуал длинной 5 секунд для парфюма {brand} {perfume_name} соответствующий описанию: {description}

И составь по нему МАКСИМАЛЬНО КРАТКИЙ технический промт для AI seedance-1-pro на английском языке.

Промт должен быть в стиле:
- Описание движения камеры (tracking shot, dolly, static, etc)
- Конкретные объекты в кадре
- Технические детали (shallow focus, depth of field, lighting)
- Стиль (cinematic, commercial, photorealistic)
- БЕЗ лирики, только технические описания

Пример стиля промта:
"Low angle tracking shot: perfume bottle on marble surface, rose petals, golden light rays. Camera slowly orbits around bottle. Shallow focus, luxury commercial style, depth of field, moody lighting."

Формат ответа:
КОНЦЕПЦИЯ: [краткое описание на русском]
ПРОМТ: [краткий технический промт на английском, максимум 2-3 предложения]"""
        
        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Call Claude via Replicate
        payload = {
            'input': {
                'prompt': claude_prompt,
                'max_tokens': 1024  # Claude 4.5 requires minimum 1024 tokens
            }
        }
        
        print(f"[CLAUDE] Calling Claude 4.5 Sonnet via Replicate...")
        response = requests.post(
            'https://api.replicate.com/v1/models/anthropic/claude-4.5-sonnet/predictions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 201:
            print(f"[CLAUDE ERROR] Failed to create prediction: {response.status_code}")
            print(f"[CLAUDE ERROR] Response: {response.text}")
            return None
        
        prediction = response.json()
        prediction_id = prediction['id']
        print(f"[CLAUDE] Prediction created: {prediction_id}")
        
        # Poll for result
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(2)
            
            response = requests.get(
                f'https://api.replicate.com/v1/predictions/{prediction_id}',
                headers=headers,
                timeout=30
            )
            
            prediction = response.json()
            status = prediction['status']
            
            print(f"[CLAUDE] Status: {status} (attempt {attempt+1}/{max_attempts})")
            
            if status == 'succeeded':
                output = prediction['output']
                # Output is a list of strings, join them
                result_text = ''.join(output) if isinstance(output, list) else str(output)
                
                print(f"[CLAUDE] ✓ Concept generated!")
                print(f"[CLAUDE] Result preview: {result_text[:200]}...")
                
                # Parse the result
                concept = ""
                prompt = ""
                
                if "КОНЦЕПЦИЯ:" in result_text and "ПРОМТ:" in result_text:
                    parts = result_text.split("ПРОМТ:")
                    concept = parts[0].replace("КОНЦЕПЦИЯ:", "").strip()
                    prompt = parts[1].strip()
                else:
                    # Fallback - use the whole response as prompt
                    prompt = result_text.strip()
                    concept = "Визуал для парфюма"
                
                return {
                    'concept': concept,
                    'prompt': prompt,
                    'raw_output': result_text
                }
            
            elif status == 'failed':
                print(f"[CLAUDE ERROR] Prediction failed: {prediction.get('error')}")
                return None
        
        print(f"[CLAUDE ERROR] Timeout waiting for result")
        return None
        
    except Exception as e:
        print(f"[CLAUDE ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_video_seedance(image_path, video_prompt):
    """
    Generate video using Seedance-1-pro via Replicate
    
    Args:
        image_path: Path to image with removed background (nobg)
        video_prompt: Prompt generated by Claude
    
    Returns:
        Video data (bytes) or None
    """
    if not REPLICATE_API_TOKEN:
        raise ValueError("Replicate API token not configured")
    
    try:
        print(f"[SEEDANCE] Starting video generation...")
        print(f"[SEEDANCE] Input: {image_path}")
        print(f"[SEEDANCE] Prompt: {video_prompt[:100]}...")
        
        # Read and encode image as base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Call Seedance-1-pro
        payload = {
            'input': {
                'image': f'data:image/png;base64,{image_data}',
                'prompt': video_prompt,
                'duration': 5,  # 5 seconds
                'resolution': '480p',
                'fps': 24,
                'aspect_ratio': '9:16',  # Vertical video for perfume bottle
                'camera_fixed': False  # Allow camera movement as described in prompt
            }
        }
        
        print(f"[SEEDANCE] Calling Seedance-1-pro API...")
        response = requests.post(
            'https://api.replicate.com/v1/models/bytedance/seedance-1-pro/predictions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 201:
            print(f"[SEEDANCE ERROR] Failed to create prediction: {response.status_code}")
            print(f"[SEEDANCE ERROR] Response: {response.text}")
            return None
        
        prediction = response.json()
        prediction_id = prediction['id']
        print(f"[SEEDANCE] Prediction created: {prediction_id}")
        print(f"[SEEDANCE] Generating 5-second video at 480p 24fps... This may take 2-3 minutes.")
        
        # Poll for result
        max_attempts = 90  # ~4.5 minutes max
        for attempt in range(max_attempts):
            time.sleep(3)
            
            response = requests.get(
                f'https://api.replicate.com/v1/predictions/{prediction_id}',
                headers=headers,
                timeout=30
            )
            
            prediction = response.json()
            status = prediction['status']
            
            print(f"[SEEDANCE] Status: {status} (attempt {attempt+1}/{max_attempts})")
            
            if status == 'succeeded':
                output_url = prediction['output']
                print(f"[SEEDANCE] Downloading video from: {str(output_url)[:60]}...")
                
                result_response = requests.get(output_url, timeout=180)
                
                print(f"[SEEDANCE] ✓ Video generated successfully!")
                return result_response.content
            
            elif status == 'failed':
                print(f"[SEEDANCE ERROR] Prediction failed: {prediction.get('error')}")
                return None
        
        print(f"[SEEDANCE ERROR] Timeout waiting for result")
        return None
        
    except Exception as e:
        print(f"[SEEDANCE ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Generate video from static perfume image using Claude + Seedance-1-pro"""
    try:
        data = request.json
        image_filename = data.get('image_filename', '').strip()
        brand = data.get('brand', '').strip()
        perfume_name = data.get('perfume_name', '').strip()
        description = data.get('description', '').strip()
        
        print(f"[VIDEO API] Starting video generation with Claude + Seedance-1-pro")
        print(f"[VIDEO API] Brand: {brand}, Perfume: {perfume_name}")
        
        # Validation
        if not all([brand, perfume_name, description]):
            return jsonify({'error': 'Brand, perfume name and description are required'}), 400
        
        if not image_filename:
            return jsonify({'error': 'Image filename is required'}), 400
        
        # Check if Replicate is configured
        if not REPLICATE_API_TOKEN:
            print("[ERROR] Replicate API token not configured!")
            return jsonify({
                'error': 'Replicate API not configured',
                'message': 'Please add REPLICATE_API_TOKEN to .env file'
            }), 500
        
        # Find nobg image (not styled!)
        # Replace _styled with _nobg in filename
        nobg_filename = image_filename.replace('_styled', '_nobg')
        nobg_path = os.path.join(GENERATED_IMAGES_FOLDER, nobg_filename)

        # If nobg file doesn't exist, try to find it by pattern
        if not os.path.exists(nobg_path):
            print(f"[VIDEO API] nobg file not found: {nobg_filename}")
            # Try to find any nobg file for this perfume
            import glob
            nobg_pattern = os.path.join(GENERATED_IMAGES_FOLDER, f"*nobg*.png")
            nobg_files = sorted(glob.glob(nobg_pattern), key=os.path.getmtime, reverse=True)
            if nobg_files:
                nobg_path = nobg_files[0]
                nobg_filename = os.path.basename(nobg_path)
                print(f"[VIDEO API] Found alternative nobg file: {nobg_filename}")
            else:
                return jsonify({'error': 'No background-removed image found. Please generate image first.'}), 404
        
        if not os.path.exists(nobg_path):
            return jsonify({'error': f'Background-removed image not found: {nobg_filename}'}), 404
        
        print(f"[VIDEO API] Using nobg image: {nobg_filename}")
        
        # Step 1: Generate video concept with Claude
        print(f"[VIDEO API] Step 1/2: Generating concept with Claude...")
        claude_result = generate_video_concept_with_claude(brand, perfume_name, description)
        
        if not claude_result:
            return jsonify({'error': 'Failed to generate video concept with Claude'}), 500
        
        concept = claude_result['concept']
        video_prompt = claude_result['prompt']
        
        print(f"[VIDEO API] Concept: {concept[:100]}...")
        print(f"[VIDEO API] Prompt: {video_prompt[:100]}...")
        
        # Step 2: Generate video with Seedance-1-pro
        print(f"[VIDEO API] Step 2/2: Generating video with Seedance-1-pro...")
        video_data = generate_video_seedance(nobg_path, video_prompt)
        
        if not video_data:
            return jsonify({'error': 'Failed to generate video with Seedance-1-pro'}), 500
        
        # Generate timestamp and filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        import re
        safe_brand = re.sub(r'[^\w\s-]', '', brand).strip().replace(' ', '_')
        safe_perfume = re.sub(r'[^\w\s-]', '', perfume_name).strip().replace(' ', '_')
        safe_name = f"{safe_brand}_{safe_perfume}"[:50]
        video_filename = f"{safe_name}_seedance_{timestamp}.mp4"
        video_path = os.path.join(VIDEO_FOLDER, video_filename)
        
        # Save video
        with open(video_path, 'wb') as f:
            f.write(video_data)

        print(f"[VIDEO API] ✓ Video generated: {video_filename}")

        # Update database with video path if product_id is provided
        product_id = data.get('product_id')
        if product_id:
            try:
                import sqlite3
                db_path = os.getenv('DB_PATH', 'fragrantica_news.db')

                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute('''
                        UPDATE randewoo_products
                        SET video_path = ?
                        WHERE id = ?
                    ''', (video_filename, product_id))

                    conn.commit()
                    conn.close()

                    print(f"[DB] Updated video_path for product {product_id}: {video_filename}")
            except Exception as e:
                print(f"[DB ERROR] Failed to update video_path: {e}")

        return jsonify({
            'success': True,
            'message': 'Video generated successfully',
            'data': {
                'video_url': f'/videos/{video_filename}',
                'video_filename': video_filename,
                'brand': brand,
                'perfume_name': perfume_name,
                'concept': concept,
                'prompt': video_prompt,
                'nobg_image': nobg_filename
            }
        })
        
    except Exception as e:
        print(f"Error in generate_video: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve generated videos"""
    return send_from_directory(VIDEO_FOLDER, filename)

@app.route('/api/test')
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'ok',
        'openai_configured': bool(OPENAI_API_KEY),
        'replicate_configured': bool(REPLICATE_API_TOKEN),
        'upload_folder': UPLOAD_FOLDER,
        'video_folder': VIDEO_FOLDER
    })

@app.route('/api/products')
def get_products():
    """Get all Randewoo products from database"""
    try:
        import sqlite3

        db_path = os.getenv('DB_PATH', 'fragrantica_news.db')

        if not os.path.exists(db_path):
            return jsonify({
                'success': False,
                'error': f'Database not found: {db_path}',
                'products': []
            })

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, brand, name, product_url, fragrantica_url,
                   description, image_path, styled_image_path, video_path,
                   parsed_at
            FROM randewoo_products
            ORDER BY parsed_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        # Convert to list of dictionaries
        products = [dict(row) for row in rows]

        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })

    except Exception as e:
        print(f"[API ERROR] /api/products: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'products': []
        }), 500

@app.route('/api/settings/prompts', methods=['GET', 'POST'])
def manage_prompts():
    """Get or update global prompts from database"""
    try:
        import sqlite3

        db_path = os.getenv('DB_PATH', 'fragrantica_news.db')

        if not os.path.exists(db_path):
            return jsonify({
                'success': False,
                'error': f'Database not found: {db_path}'
            }), 404

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if request.method == 'GET':
            # Get prompts
            cursor.execute('''
                SELECT key, value FROM global_settings
                WHERE key IN ('prompt_stylize', 'prompt_caption')
            ''')

            rows = cursor.fetchall()
            conn.close()

            prompts = {}
            for row in rows:
                key = row[0].replace('prompt_', '')  # Remove 'prompt_' prefix
                prompts[key] = row[1]

            return jsonify({
                'success': True,
                'prompts': prompts
            })

        else:  # POST - update prompts
            data = request.json
            prompt_stylize = data.get('prompt_stylize', '').strip()
            prompt_caption = data.get('prompt_caption', '').strip()

            if not prompt_stylize or not prompt_caption:
                return jsonify({
                    'success': False,
                    'error': 'Both prompts are required'
                }), 400

            # Update prompts
            from datetime import datetime

            cursor.execute('''
                INSERT OR REPLACE INTO global_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', ('prompt_stylize', prompt_stylize, datetime.now()))

            cursor.execute('''
                INSERT OR REPLACE INTO global_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', ('prompt_caption', prompt_caption, datetime.now()))

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Prompts updated successfully'
            })

    except Exception as e:
        print(f"[API ERROR] /api/settings/prompts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/save-main-image', methods=['POST'])
def save_main_image():
    """Download and save main image for a product"""
    try:
        import sqlite3
        from datetime import datetime

        data = request.json
        image_url = data.get('image_url', '').strip()
        product_id = data.get('product_id')
        brand = data.get('brand', '').strip()
        name = data.get('name', '').strip()

        if not image_url or not product_id:
            return jsonify({
                'success': False,
                'error': 'Image URL and product ID are required'
            }), 400

        # Generate filename
        import re
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_brand = re.sub(r'[^\w\s-]', '', brand).strip().replace(' ', '_')
        safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
        safe_filename = f"{safe_brand}_{safe_name}"[:50]
        filename = f"{safe_filename}_main_{timestamp}.jpg"

        # Download image
        main_images_folder = os.getenv('UPLOAD_FOLDER', 'main_images')
        os.makedirs(main_images_folder, exist_ok=True)

        filepath = download_image(image_url, filename)

        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Failed to download image'
            }), 500

        # Get just the filename (not full path)
        image_filename = os.path.basename(filepath)

        # Update database
        db_path = os.getenv('DB_PATH', 'fragrantica_news.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE randewoo_products
            SET image_path = ?
            WHERE id = ?
        ''', (image_filename, product_id))

        conn.commit()
        conn.close()

        print(f"[SAVE MAIN] Image saved: {image_filename} for product ID {product_id}")

        return jsonify({
            'success': True,
            'image_path': image_filename,
            'message': 'Main image saved successfully'
        })

    except Exception as e:
        print(f"[API ERROR] /api/save-main-image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-tg-caption', methods=['POST'])
def generate_tg_caption():
    """Generate Telegram caption using Claude via Replicate"""
    try:
        if not REPLICATE_API_TOKEN:
            return jsonify({
                'success': False,
                'error': 'Replicate API not configured'
            }), 500

        data = request.json
        brand = data.get('brand', '').strip()
        perfume_name = data.get('perfume_name', '').strip()
        description = data.get('description', '').strip()
        custom_prompt = data.get('prompt', '').strip()

        if not all([brand, perfume_name, description]):
            return jsonify({
                'success': False,
                'error': 'Brand, perfume name, and description are required'
            }), 400

        # Use custom prompt or default
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = f"""Создай продающий пост для Telegram канала о парфюме {brand} {perfume_name}.

Описание аромата: {description}

Требования:
- Текст должен быть живым и эмоциональным
- Вызывать желание купить
- Подчеркивать уникальность аромата
- Использовать емодзи (но не переборщить)
- Длина: 3-5 предложений
- Стиль: casual, но профессионально

Формат ответа: только текст поста, без заголовков и пояснений."""

        print(f"[TG CAPTION] Generating with Claude for {brand} {perfume_name}...")

        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}',
            'Content-Type': 'application/json'
        }

        payload = {
            'input': {
                'prompt': prompt,
                'max_tokens': 1024
            }
        }

        # Create prediction
        response = requests.post(
            'https://api.replicate.com/v1/models/anthropic/claude-4.5-sonnet/predictions',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 201:
            print(f"[TG CAPTION ERROR] Failed to create prediction: {response.status_code}")
            print(f"[TG CAPTION ERROR] Response: {response.text}")
            return jsonify({
                'success': False,
                'error': f'Failed to call Claude API: {response.status_code}'
            }), 500

        prediction = response.json()
        prediction_id = prediction['id']
        print(f"[TG CAPTION] Prediction created: {prediction_id}")

        # Poll for result
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(2)

            response = requests.get(
                f'https://api.replicate.com/v1/predictions/{prediction_id}',
                headers=headers,
                timeout=30
            )

            prediction = response.json()
            status = prediction['status']

            if status == 'succeeded':
                output = prediction['output']
                caption = ''.join(output) if isinstance(output, list) else str(output)

                print(f"[TG CAPTION] ✓ Generated: {caption[:100]}...")

                return jsonify({
                    'success': True,
                    'caption': caption.strip()
                })

            elif status == 'failed':
                error_msg = prediction.get('error', 'Unknown error')
                print(f"[TG CAPTION ERROR] Prediction failed: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'Caption generation failed: {error_msg}'
                }), 500

        print(f"[TG CAPTION ERROR] Timeout waiting for result")
        return jsonify({
            'success': False,
            'error': 'Timeout waiting for caption generation'
        }), 500

    except Exception as e:
        print(f"[API ERROR] /api/generate-tg-caption: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/publish-to-telegram', methods=['POST'])
def publish_to_telegram():
    """Publish image/video to Telegram channel"""
    try:
        import sqlite3

        TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
            return jsonify({
                'success': False,
                'error': 'Telegram bot token or channel ID not configured in .env'
            }), 500

        data = request.json
        brand = data.get('brand', '').strip()
        perfume_name = data.get('perfume_name', '').strip()
        caption = data.get('caption', '').strip()
        media_file = data.get('media_file', '').strip()
        media_type = data.get('media_type', 'image')  # 'image' or 'video'
        product_url = data.get('product_url', '').strip()

        if not all([brand, perfume_name, caption, media_file]):
            return jsonify({
                'success': False,
                'error': 'Brand, perfume name, caption, and media file are required'
            }), 400

        # Add product link button if available
        reply_markup = None
        if product_url:
            reply_markup = {
                'inline_keyboard': [[
                    {'text': '🛒 Купить на Randewoo', 'url': product_url}
                ]]
            }

        # Determine file path
        if media_type == 'video':
            file_path = os.path.join(VIDEO_FOLDER, media_file)
        else:
            file_path = os.path.join(UPLOAD_FOLDER, media_file)

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': f'Media file not found: {media_file}'
            }), 404

        print(f"[TELEGRAM] Publishing {media_type} to channel {TELEGRAM_CHANNEL_ID}...")
        print(f"[TELEGRAM] File: {file_path}")

        # Send to Telegram
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

        if media_type == 'video':
            endpoint = f'{url}/sendVideo'
            files = {'video': open(file_path, 'rb')}
        else:
            endpoint = f'{url}/sendPhoto'
            files = {'photo': open(file_path, 'rb')}

        payload = {
            'chat_id': TELEGRAM_CHANNEL_ID,
            'caption': caption,
            'parse_mode': 'HTML'
        }

        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)

        response = requests.post(endpoint, data=payload, files=files, timeout=60)

        if response.status_code == 200:
            result = response.json()
            print(f"[TELEGRAM] ✓ Published successfully!")

            return jsonify({
                'success': True,
                'message': 'Published to Telegram successfully',
                'telegram_response': result
            })
        else:
            error_msg = response.text
            print(f"[TELEGRAM ERROR] Failed to publish: {response.status_code}")
            print(f"[TELEGRAM ERROR] Response: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'Telegram API error: {error_msg}'
            }), 500

    except Exception as e:
        print(f"[API ERROR] /api/publish-to-telegram: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    PORT = 8080
    print("=" * 70)
    print("Perfume Visual Generator - Starting Server")
    print("=" * 70)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"OpenAI configured: {bool(OPENAI_API_KEY)}")
    print(f"\nServer running on http://localhost:{PORT}")
    print(f"Open in browser: http://localhost:{PORT}")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=PORT)

