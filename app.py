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
import sqlite3
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
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
DB_PATH = 'fragrantica_news.db'

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

if TELEGRAM_BOT_TOKEN:
    masked_token = TELEGRAM_BOT_TOKEN[:10] + '...' + TELEGRAM_BOT_TOKEN[-4:] if len(TELEGRAM_BOT_TOKEN) > 14 else '[SET]'
    print(f"[INIT] Telegram Bot Token loaded: {masked_token}")
else:
    print(f"[INIT] WARNING: TELEGRAM_BOT_TOKEN not found in .env (required for publishing)")

if TELEGRAM_CHANNEL_ID:
    print(f"[INIT] Telegram Channel ID loaded: {TELEGRAM_CHANNEL_ID}")
else:
    print(f"[INIT] WARNING: TELEGRAM_CHANNEL_ID not found in .env (required for publishing)")

UPLOAD_FOLDER = 'main_images'
VIDEO_FOLDER = 'generated_videos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4'}

# Ensure folders exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(VIDEO_FOLDER).mkdir(exist_ok=True)

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

# ============================================================================
# DATABASE HELPERS (Randewoo Products)
# ============================================================================

def get_db_connection():
    """Creates connection to database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_products():
    """Get all Randewoo products from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, brand, name, product_url, fragrantica_url, parsed_at, 
                   description, image_path, styled_image_path, video_path
            FROM randewoo_products
            ORDER BY id DESC
            LIMIT 1000
        ''')
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'id': row['id'],
                'brand': row['brand'],
                'name': row['name'],
                'product_url': row['product_url'],
                'fragrantica_url': row['fragrantica_url'] if row['fragrantica_url'] else '',
                'description': row['description'] if row['description'] else '',
                'image_path': row['image_path'] if row['image_path'] else '',
                'styled_image_path': row['styled_image_path'] if row['styled_image_path'] else '',
                'video_path': row['video_path'] if row['video_path'] else '',
                'parsed_at': row['parsed_at']
            })
        
        conn.close()
        return products
        
    except Exception as e:
        print(f"[DB ERROR] Failed to get products: {e}")
        return []

def get_product_by_id(product_id):
    """Get single product by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, brand, name, product_url, fragrantica_url
            FROM randewoo_products
            WHERE id = ?
        ''', (product_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'brand': row['brand'],
                'name': row['name'],
                'product_url': row['product_url'],
                'fragrantica_url': row['fragrantica_url'] if row['fragrantica_url'] else ''
            }
        return None
        
    except Exception as e:
        print(f"[DB ERROR] Failed to get product {product_id}: {e}")
        return None

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
            
            print(f"[DOWNLOAD] Image downloaded successfully: {len(response.content)} bytes")
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
                
                print(f"[NANO-BANANA] Background removed successfully!")
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
                
                print(f"[NANO-BANANA] Image stylized successfully!")
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
        image_path = data.get('image_path', '').strip()  # Main image from database
        product_id = data.get('product_id')  # Product ID from database (optional)
        
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
        # Priority: 1) Main image from DB, 2) URL from form, 3) Auto-search
        if image_path:
            # Use main image from database
            print(f"[1/4] Using main image from database: {image_path}")
            source_path = os.path.join(UPLOAD_FOLDER, image_path)
            
            if not os.path.exists(source_path):
                print(f"[ERROR] Main image not found: {source_path}")
                return jsonify({'error': f'Main image not found: {image_path}'}), 400
            
            # Copy to working filename
            original_filename = f"{safe_name}_original_{timestamp}.jpg"
            original_path = os.path.join(UPLOAD_FOLDER, original_filename)
            import shutil
            shutil.copy(source_path, original_path)
            print(f"[SUCCESS] Copied main image to: {original_filename}")
            
        elif image_url:
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
            nobg_path = os.path.join(UPLOAD_FOLDER, nobg_filename)
            
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
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)
        
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
        
        # Update database with styled image path (if product_id provided)
        if product_id:
            try:
                conn = get_db_connection()
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
                'styled_url': f'/images/{final_filename}',
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

@app.route('/api/history')
def get_history():
    """Get generation history"""
    history = load_history()
    return jsonify(history)

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve generated images"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/search-image', methods=['POST'])
def search_image():
    """Search for perfume bottle image - tries Randewoo first, then Google"""
    print("[API] /api/search-image endpoint called")
    
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
        product_url = data.get('product_url', '').strip()
        
        print(f"[API] Brand: '{brand}', Perfume: '{perfume_name}'")
        print(f"[API] Product URL: '{product_url}'")
        
        if not brand or not perfume_name:
            print("[API] ERROR: Missing brand or perfume name")
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'message': 'Brand and perfume name are required'
            }), 400
        
        # STEP 1: Try to extract image from Randewoo if URL provided
        if product_url and 'randewoo.ru' in product_url:
            print("[API] Trying to extract image from Randewoo first...")
            randewoo_result = extract_randewoo_image(product_url)
            
            if randewoo_result:
                print(f"[API] Found image on Randewoo: {randewoo_result['url']}")
                return jsonify({
                    'success': True,
                    'image_url': randewoo_result['url'],
                    'title': randewoo_result.get('title', 'Randewoo Product Image'),
                    'source': 'randewoo',
                    'message': 'Image found on Randewoo'
                })
            else:
                print("[API] No image found on Randewoo, falling back to Google search...")
        else:
            print("[API] No Randewoo URL provided, using Google search...")
        
        # STEP 2: Fallback to Google Custom Search API
        # Force reload module to get latest changes (fix for Flask caching)
        import importlib
        import image_search
        importlib.reload(image_search)
        from image_search import search_perfume_image as search_fn
        print("[API] image_search module reloaded!")
        
        print(f"[API] Calling Google search: search_fn({brand}, {perfume_name})...")
        
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
                
                print(f"[CLAUDE] Concept generated!")
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
        
        # Retry logic for temporary errors (502, 503)
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"[SEEDANCE] Retry attempt {attempt + 1}/{max_retries} after {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
                response = requests.post(
                    'https://api.replicate.com/v1/models/bytedance/seedance-1-pro/predictions',
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # Success
                if response.status_code == 201:
                    prediction = response.json()
                    prediction_id = prediction['id']
                    print(f"[SEEDANCE] Prediction created: {prediction_id}")
                    print(f"[SEEDANCE] Generating 5-second video at 480p 24fps... This may take 2-3 minutes.")
                    break
                
                # Temporary errors - retry
                elif response.status_code in [502, 503, 504]:
                    print(f"[SEEDANCE WARN] Temporary error {response.status_code} (Gateway issue)")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        print(f"[SEEDANCE ERROR] Max retries reached")
                        print(f"[SEEDANCE ERROR] Replicate API may be temporarily unavailable")
                        return None
                
                # Permanent errors - don't retry
                else:
                    print(f"[SEEDANCE ERROR] Failed to create prediction: {response.status_code}")
                    print(f"[SEEDANCE ERROR] Response: {response.text[:500]}")
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"[SEEDANCE ERROR] Request timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return None
            except requests.exceptions.RequestException as e:
                print(f"[SEEDANCE ERROR] Network error: {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return None
        else:
            # All retries failed
            print(f"[SEEDANCE ERROR] All retry attempts failed")
            return None
        
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
                
                print(f"[SEEDANCE] Video generated successfully!")
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
        product_id = data.get('product_id')  # Product ID from database (optional)
        
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
        nobg_path = os.path.join(UPLOAD_FOLDER, nobg_filename)
        
        # If nobg file doesn't exist, try to find it by pattern
        if not os.path.exists(nobg_path):
            print(f"[VIDEO API] nobg file not found: {nobg_filename}")
            # Try to find any nobg file for this perfume
            import glob
            nobg_pattern = os.path.join(UPLOAD_FOLDER, f"*nobg*.png")
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
        
        print(f"[VIDEO API] Video generated: {video_filename}")
        
        # Update database with video path (if product_id provided)
        if product_id:
            try:
                conn = get_db_connection()
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

@app.route('/api/generate-tg-caption', methods=['POST'])
def generate_tg_caption():
    """Generate Telegram caption using Claude via Replicate"""
    try:
        data = request.json
        brand = data.get('brand', '').strip()
        perfume_name = data.get('perfume_name', '').strip()
        description = data.get('description', '').strip()
        custom_prompt = data.get('prompt', '').strip()
        
        print(f"[TG CAPTION] Generating caption for: {brand} {perfume_name}")
        
        # Validation
        if not all([brand, perfume_name, description]):
            return jsonify({'error': 'Brand, perfume name and description are required'}), 400
        
        # Check if Replicate is configured
        if not REPLICATE_API_TOKEN:
            return jsonify({
                'error': 'Replicate API not configured',
                'message': 'Please add REPLICATE_API_TOKEN to .env file'
            }), 500
        
        # Build Claude prompt
        if custom_prompt:
            # User provided custom prompt
            claude_prompt = custom_prompt
        else:
            # Default prompt
            claude_prompt = f"""Создай продающий пост для Telegram канала о парфюме {brand} {perfume_name}.

Описание аромата: {description}

Требования:
- Текст должен быть живым и эмоциональным
- Вызывать желание купить
- Подчеркивать уникальность аромата
- Использовать емодзи (но не переборщить)
- Длина: 3-5 предложений
- Стиль: casual, но профессионально

Формат ответа: только текст поста, без заголовков и пояснений."""
        
        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Call Claude via Replicate
        payload = {
            'input': {
                'prompt': claude_prompt,
                'max_tokens': 1024
            }
        }
        
        print(f"[TG CAPTION] Calling Claude 4.5 Sonnet via Replicate...")
        response = requests.post(
            'https://api.replicate.com/v1/models/anthropic/claude-4.5-sonnet/predictions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 201:
            print(f"[TG CAPTION ERROR] Failed to create prediction: {response.status_code}")
            print(f"[TG CAPTION ERROR] Response: {response.text}")
            return jsonify({'error': f'Failed to call Claude: {response.status_code}'}), 500
        
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
                if isinstance(output, list):
                    caption = ''.join(output).strip()
                else:
                    caption = str(output).strip()
                
                print(f"[TG CAPTION] Caption generated: {caption[:100]}...")
                
                return jsonify({
                    'success': True,
                    'caption': caption,
                    'prompt_used': claude_prompt
                })
            
            elif status == 'failed':
                print(f"[TG CAPTION ERROR] Prediction failed: {prediction.get('error')}")
                return jsonify({'error': f"Claude failed: {prediction.get('error')}"}), 500
        
        print(f"[TG CAPTION ERROR] Timeout waiting for Claude")
        return jsonify({'error': 'Timeout waiting for Claude response'}), 500
        
    except Exception as e:
        print(f"Error in generate_tg_caption: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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

# ============================================================================
# RANDEWOO PRODUCTS API
# ============================================================================

@app.route('/api/products')
def api_get_products():
    """Get all Randewoo products"""
    try:
        products = get_all_products()
        return jsonify({
            'success': True,
            'products': products,
            'total': len(products)
        })
    except Exception as e:
        print(f"[API ERROR] Failed to get products: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>')
def api_get_product(product_id):
    """Get single product by ID"""
    try:
        product = get_product_by_id(product_id)
        if product:
            return jsonify({'success': True, 'product': product})
        else:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        print(f"[API ERROR] Failed to get product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-main-image', methods=['POST'])
def api_save_main_image():
    """Download image from URL and save as main image for product"""
    try:
        import re
        
        data = request.json
        image_url = data.get('image_url', '').strip()
        product_id = data.get('product_id')
        brand = data.get('brand', '').strip()
        name = data.get('name', '').strip()
        
        if not image_url:
            return jsonify({'success': False, 'error': 'Image URL is required'}), 400
        
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID is required'}), 400
        
        print(f"[SAVE MAIN] Downloading image for product #{product_id}")
        print(f"[SAVE MAIN] URL: {image_url}")
        
        # Sanitize filename
        def sanitize_filename(text):
            text = re.sub(r'[<>:"/\\|?*]', '_', text)
            text = text.replace(' ', '_')
            text = text.replace("'", "")
            return text[:100]
        
        # Create filename
        brand_clean = sanitize_filename(brand) if brand else 'Unknown'
        name_clean = sanitize_filename(name) if name else 'Product'
        filename = f"{brand_clean}_{name_clean}_{product_id}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Save to file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"[SAVE MAIN] Saved to: {filename}")
        
        # Update database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE randewoo_products
            SET image_path = ?
            WHERE id = ?
        ''', (filename, product_id))
        
        conn.commit()
        conn.close()
        
        print(f"[SAVE MAIN] Updated database for product #{product_id}")
        
        return jsonify({
            'success': True,
            'image_path': filename,
            'message': 'Image saved successfully'
        })
        
    except requests.exceptions.RequestException as e:
        print(f"[SAVE MAIN ERROR] Failed to download image: {e}")
        return jsonify({'success': False, 'error': f'Failed to download image: {str(e)}'}), 500
    except Exception as e:
        print(f"[SAVE MAIN ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/parse-description', methods=['POST'])
def api_parse_description():
    """Parse perfume description from Randewoo product page"""
    try:
        from bs4 import BeautifulSoup
        
        data = request.json
        product_url = data.get('product_url', '').strip()
        
        if not product_url:
            return jsonify({'success': False, 'error': 'Product URL is required'}), 400
        
        print(f"[PARSER] Fetching description from: {product_url}")
        
        # Fetch page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(product_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find collapsable div with description
        collapsable_div = soup.find('div', class_='collapsable')
        
        if not collapsable_div:
            print(f"[PARSER] No collapsable div found")
            return jsonify({'success': False, 'error': 'Description block not found on page'}), 404
        
        # Extract text from all paragraphs
        paragraphs = collapsable_div.find_all('p')
        description_parts = []
        
        for p in paragraphs:
            # Remove links but keep their text
            for a in p.find_all('a'):
                a.replace_with(a.get_text())
            
            # Get clean text
            text = p.get_text().strip()
            if text:
                description_parts.append(text)
        
        description = '\n\n'.join(description_parts)
        
        if not description:
            print(f"[PARSER] No description text found in collapsable div")
            return jsonify({'success': False, 'error': 'Description text is empty'}), 404
        
        print(f"[PARSER] Successfully parsed description ({len(description)} chars)")
        
        return jsonify({
            'success': True,
            'description': description
        })
        
    except requests.exceptions.RequestException as e:
        print(f"[PARSER ERROR] Failed to fetch page: {e}")
        return jsonify({'success': False, 'error': f'Failed to fetch page: {str(e)}'}), 500
    except Exception as e:
        print(f"[PARSER ERROR] Failed to parse description: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def extract_randewoo_image(product_url):
    """
    Extract high-quality product image from Randewoo product page
    
    Args:
        product_url: Randewoo product URL
    
    Returns:
        dict with image URL or None if not found
    """
    try:
        from bs4 import BeautifulSoup
        
        print(f"[RANDEWOO IMG] Fetching image from: {product_url}")
        
        # Fetch page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(product_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find main product image
        # Looking for: <img class="js-main-product-image s-productItem__imgMain" data-zoom-image="...">
        main_img = soup.find('img', class_='js-main-product-image')
        
        if not main_img:
            print(f"[RANDEWOO IMG] No main product image found")
            return None
        
        # Try to get high quality image
        # Priority: data-zoom-image > srcset (2x) > src
        image_url = None
        
        # 1. Try data-zoom-image (highest quality)
        if main_img.get('data-zoom-image'):
            image_url = main_img.get('data-zoom-image')
            print(f"[RANDEWOO IMG] Found data-zoom-image: {image_url}")
        
        # 2. Try srcset (look for 2x version)
        elif main_img.get('srcset'):
            srcset = main_img.get('srcset')
            # Parse srcset: "url1 1x, url2 2x"
            parts = [s.strip() for s in srcset.split(',')]
            for part in parts:
                if '2x' in part:
                    image_url = part.split()[0]
                    print(f"[RANDEWOO IMG] Found srcset 2x: {image_url}")
                    break
            
            # If no 2x found, use first URL
            if not image_url and parts:
                image_url = parts[0].split()[0]
                print(f"[RANDEWOO IMG] Found srcset 1x: {image_url}")
        
        # 3. Fallback to src
        elif main_img.get('src'):
            image_url = main_img.get('src')
            print(f"[RANDEWOO IMG] Found src: {image_url}")
        
        if not image_url:
            print(f"[RANDEWOO IMG] No image URL extracted")
            return None
        
        # Make URL absolute if relative
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            image_url = 'https://randewoo.ru' + image_url
        
        print(f"[RANDEWOO IMG] Successfully extracted image: {image_url}")
        
        return {
            'url': image_url,
            'source': 'randewoo',
            'title': main_img.get('title', 'Randewoo Product Image')
        }
        
    except requests.exceptions.RequestException as e:
        print(f"[RANDEWOO IMG ERROR] Failed to fetch page: {e}")
        return None
    except Exception as e:
        print(f"[RANDEWOO IMG ERROR] Failed to extract image: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# GLOBAL SETTINGS API
# ============================================================================

@app.route('/api/settings/prompts', methods=['GET'])
def api_get_prompts():
    """Get global prompt settings from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, value FROM global_settings
            WHERE key IN ('prompt_stylize', 'prompt_caption')
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        prompts = {}
        for row in rows:
            prompts[row['key']] = row['value']
        
        return jsonify({
            'success': True,
            'prompts': {
                'stylize': prompts.get('prompt_stylize', ''),
                'caption': prompts.get('prompt_caption', '')
            }
        })
        
    except Exception as e:
        print(f"[API ERROR] Failed to get prompts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/prompts', methods=['POST'])
def api_update_prompts():
    """Update global prompt settings in database"""
    try:
        data = request.json
        prompt_stylize = data.get('prompt_stylize', '').strip()
        prompt_caption = data.get('prompt_caption', '').strip()
        
        if not prompt_stylize or not prompt_caption:
            return jsonify({'success': False, 'error': 'Both prompts are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update or insert stylize prompt
        cursor.execute('''
            INSERT OR REPLACE INTO global_settings (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', ('prompt_stylize', prompt_stylize, datetime.now()))
        
        # Update or insert caption prompt
        cursor.execute('''
            INSERT OR REPLACE INTO global_settings (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', ('prompt_caption', prompt_caption, datetime.now()))
        
        conn.commit()
        conn.close()
        
        print(f"[SETTINGS] Prompts updated:")
        print(f"  - prompt_stylize: {len(prompt_stylize)} chars")
        print(f"  - prompt_caption: {len(prompt_caption)} chars")
        
        return jsonify({
            'success': True,
            'message': 'Prompts updated successfully'
        })
        
    except Exception as e:
        print(f"[API ERROR] Failed to update prompts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# TELEGRAM PUBLISH API
# ============================================================================

@app.route('/api/publish-to-telegram', methods=['POST'])
def api_publish_to_telegram():
    """Publish perfume to Telegram channel with image or video"""
    try:
        data = request.json
        
        brand = data.get('brand', '').strip()
        perfume_name = data.get('perfume_name', '').strip()
        caption = data.get('caption', '').strip()  # Generated caption from Claude
        media_file = data.get('media_file', '').strip()  # filename
        media_type = data.get('media_type', 'image').strip()  # 'image' or 'video'
        product_url = data.get('product_url', '').strip()
        
        print(f"[TELEGRAM] Publishing to channel: {brand} - {perfume_name}")
        print(f"[TELEGRAM] Media type: {media_type}")
        
        # Validation
        if not all([brand, perfume_name, caption]):
            return jsonify({'error': 'Brand, perfume name and caption are required'}), 400
        
        if not media_file:
            return jsonify({'error': 'Media file is required. Please generate visual first.'}), 400
        
        # Check Telegram configuration
        if not TELEGRAM_BOT_TOKEN:
            return jsonify({'error': 'Telegram Bot Token not configured in .env'}), 500
        
        if not TELEGRAM_CHANNEL_ID:
            return jsonify({'error': 'Telegram Channel ID not configured in .env'}), 500
        
        # Add product URL to caption if provided
        telegram_caption = caption
        if product_url:
            telegram_caption += f"\n\n{product_url}"
        
        # Limit caption to 1024 characters (Telegram limit)
        if len(telegram_caption) > 1024:
            telegram_caption = telegram_caption[:1021] + "..."
        
        # Prepare media file path
        if media_type == 'video':
            media_path = os.path.join(VIDEO_FOLDER, media_file)
            if not os.path.exists(media_path):
                return jsonify({'error': f'Video file not found: {media_file}'}), 404
            
            print(f"[TELEGRAM] Sending video: {media_file}")
            
            # Send video
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            
            with open(media_path, 'rb') as vid_file:
                files = {'video': vid_file}
                payload = {
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "caption": telegram_caption
                }
                
                response = requests.post(url, data=payload, files=files, timeout=60)
        else:
            # Send image
            media_path = os.path.join(UPLOAD_FOLDER, media_file)
            if not os.path.exists(media_path):
                return jsonify({'error': f'Image file not found: {media_file}'}), 404
            
            print(f"[TELEGRAM] Sending image: {media_file}")
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            
            with open(media_path, 'rb') as img_file:
                files = {'photo': img_file}
                payload = {
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "caption": telegram_caption
                }
                
                response = requests.post(url, data=payload, files=files, timeout=60)
        
        result = response.json()
        
        if result.get('ok'):
            print(f"[TELEGRAM] Published successfully!")
            return jsonify({
                'success': True,
                'message': 'Published to Telegram successfully',
                'telegram_response': result
            })
        else:
            error_desc = result.get('description', 'Unknown error')
            print(f"[TELEGRAM ERROR] {error_desc}")
            return jsonify({
                'success': False,
                'error': f'Telegram API error: {error_desc}'
            }), 500
        
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
