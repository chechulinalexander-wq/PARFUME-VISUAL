"""
AI-powered Image Search for Perfume Bottles
Uses Google Custom Search API for finding images + AI for selection
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def search_perfume_image(brand, perfume_name):
    """
    Search for perfume bottle image using Google Custom Search API
    
    Args:
        brand: Brand name (e.g., "Chanel")
        perfume_name: Perfume name (e.g., "No. 5")
    
    Returns:
        dict with best image URL and metadata
    """
    
    print(f"[FUNCTION CALLED] search_perfume_image('{brand}', '{perfume_name}')")
    print(f"[MODULE VERSION] Updated 2025-10-29 15:33")
    
    # Check if Google API is configured
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return {
            'success': False,
            'error': 'Google Custom Search API not configured',
            'message': 'Please set GOOGLE_API_KEY and GOOGLE_CSE_ID in .env file. See GOOGLE_SEARCH_SETUP.md for instructions.'
        }
    
    # Check for placeholder values
    if str(GOOGLE_API_KEY) == 'your_google_api_key_here' or str(GOOGLE_CSE_ID) == 'your_google_cse_id_here':
        return {
            'success': False,
            'error': 'Google API keys are placeholders',
            'message': 'Replace placeholder values in .env with real Google API keys. Get them from: https://console.cloud.google.com/'
        }
    
    # Build search query - exactly as requested!
    query = f'{brand} {perfume_name} perfume bottle front view white background'
    
    print(f"[Search] Google Custom Search: {query}")
    
    try:
        # Google Custom Search API request
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'searchType': 'image',
            'num': 10,  # Get top 10 results
            'imgSize': 'large',
            'imgType': 'photo',
            'safe': 'active'
        }
        
        print(f"[Search] Calling Google API...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'items' not in data or len(data['items']) == 0:
            return {
                'success': False,
                'error': 'No images found',
                'message': f'No images found for {brand} {perfume_name}. Try different spelling or check if perfume exists.'
            }
        
        print(f"[Search] Found {len(data['items'])} images")
        
        # Extract images from results
        images = []
        for item in data['items']:
            images.append({
                'url': item['link'],
                'title': item.get('title', ''),
                'thumbnail': item['image'].get('thumbnailLink', ''),
                'context': item.get('snippet', ''),
                'width': item['image'].get('width', 0),
                'height': item['image'].get('height', 0),
                'source': item.get('displayLink', '')
            })
        
        # Select best image using AI algorithm
        print(f"[Selection] Analyzing {len(images)} images...")
        best_image = select_best_image(images, brand, perfume_name)
        
        if not best_image:
            return {
                'success': False,
                'error': 'No suitable image found',
                'message': 'Found images but none meet quality criteria'
            }
        
        print(f"[SUCCESS] Selected: {best_image['url']}")
        
        return {
            'success': True,
            'image_url': best_image['url'],
            'thumbnail': best_image.get('thumbnail', ''),
            'title': best_image.get('title', f'{brand} {perfume_name}'),
            'source': 'Google Custom Search',
            'total_found': len(images),
            'score': best_image.get('score', 0)
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        print(f"[ERROR] Google API error: {error_msg}")
        
        # Check for specific errors
        if '400' in error_msg or 'Bad Request' in error_msg:
            return {
                'success': False,
                'error': 'Invalid API credentials',
                'message': 'Google API key or CSE ID is invalid. Please check your .env file.'
            }
        elif '403' in error_msg or 'Forbidden' in error_msg:
            return {
                'success': False,
                'error': 'API quota exceeded or forbidden',
                'message': 'Google Custom Search quota exceeded (100/day free limit) or API not enabled.'
            }
        
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to search images via Google Custom Search API'
        }
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'message': 'Unexpected error during image search'
        }

def select_best_image(images, brand, perfume_name):
    """
    AI-powered selection of best image from search results
    
    Критерии выбора (как вы просили):
    1. Вид спереди (не под углом)
    2. Желательно белый фон
    3. Название аромата на флаконе хорошо читается
    
    Args:
        images: List of image results from Google
        brand: Brand name
        perfume_name: Perfume name
    
    Returns:
        Best image dict with score
    """
    
    if not images:
        return None
    
    scored_images = []
    
    for img in images:
        score = 0
        title_lower = img.get('title', '').lower()
        context_lower = img.get('context', '').lower()
        source_lower = img.get('source', '').lower()
        
        # 1. BRAND & PERFUME NAME MATCHING (высший приоритет)
        if brand.lower() in title_lower:
            score += 30
        if perfume_name.lower() in title_lower:
            score += 30
        
        # Check in context/description too
        if brand.lower() in context_lower:
            score += 10
        if perfume_name.lower() in context_lower:
            score += 10
        
        # 2. KEYWORDS FOR GOOD PRODUCT PHOTOS
        # Хорошие ключевые слова
        good_keywords = {
            'bottle': 15,
            'perfume': 10,
            'fragrance': 10,
            'parfum': 10,
            'eau de': 8,
            'official': 15,
            'product': 12,
            'front': 20,  # вид спереди!
            'white background': 25,  # белый фон!
            'studio': 15
        }
        
        for keyword, points in good_keywords.items():
            if keyword in title_lower or keyword in context_lower:
                score += points
        
        # Плохие ключевые слова
        bad_keywords = ['review', 'unboxing', 'comparison', 'fake', 'vs', 
                       'vintage', 'empty', 'box', 'set', 'collection',
                       'miniature', 'sample', 'tester']
        
        for keyword in bad_keywords:
            if keyword in title_lower:
                score -= 15
        
        # 3. IMAGE SIZE (большие изображения = лучше качество)
        width = img.get('width', 0)
        height = img.get('height', 0)
        
        if width > 800 and height > 800:
            score += 25  # высокое разрешение
        elif width > 500 and height > 500:
            score += 15
        elif width > 300 and height > 300:
            score += 5
        
        # 4. ASPECT RATIO (портрет или квадрат = продуктовые фото)
        if width > 0 and height > 0:
            aspect_ratio = width / height
            
            # Идеальные соотношения для продуктовых фото
            if 0.8 <= aspect_ratio <= 1.2:  # Почти квадрат
                score += 20
            elif 0.6 <= aspect_ratio <= 0.8:  # Портрет (типично для флаконов)
                score += 25
            elif 1.2 <= aspect_ratio <= 1.5:  # Небольшой ландшафт
                score += 10
        
        # 5. SOURCE QUALITY (официальные источники лучше)
        trusted_sources = ['fragrantica', 'sephora', 'nordstrom', 'bloomingdales',
                          'macy', 'ulta', 'douglas', 'boots', 'notino']
        
        for source in trusted_sources:
            if source in source_lower:
                score += 20
                break
        
        # Check if official brand site
        if brand.lower().replace(' ', '') in source_lower:
            score += 30  # официальный сайт бренда!
        
        # Save scored image
        img['score'] = score
        scored_images.append(img)
    
    # Sort by score descending
    scored_images.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Log top 3 for debugging
    print(f"[Selection] Top 3 candidates:")
    for i, img in enumerate(scored_images[:3], 1):
        print(f"  {i}. Score: {img['score']} | {img['title'][:60]}")
    
    best = scored_images[0]
    print(f"[Selection] SELECTED: Score={best['score']} | {best['url']}")
    
    return best

def search_with_openai_vision(images, brand, perfume_name):
    """
    Use OpenAI Vision API to analyze images and select the best one
    This is an advanced feature that can be enabled if needed
    
    Args:
        images: List of image URLs
        brand: Brand name
        perfume_name: Perfume name
    
    Returns:
        Best image URL selected by AI
    """
    
    if not OPENAI_API_KEY:
        return None
    
    # This would use GPT-4 Vision to analyze images
    # Implementation placeholder for future enhancement
    
    prompt = f"""Analyze these perfume bottle images and select the BEST one for {brand} {perfume_name}.

Criteria:
1. Front view of the bottle (not angled or side view)
2. White or neutral background preferred
3. Brand name clearly visible on bottle
4. High quality, well-lit product photo
5. Full bottle visible (not cropped)
6. No hands, no packaging, just the bottle

Return the index (0-based) of the best image."""
    
    # TODO: Implement OpenAI Vision API call
    # For now, return None to fall back to heuristic selection
    
    return None

# Test function
if __name__ == "__main__":
    print("=" * 70)
    print("OpenAI Image Search Test")
    print("=" * 70)
    
    # Test search
    result = search_perfume_image("Chanel", "No. 5")
    
    if result['success']:
        print(f"\n[SUCCESS] Found image!")
        print(f"URL: {result['image_url']}")
        print(f"Source: {result.get('source', 'Unknown')}")
        print(f"Verified: {result.get('verified', False)}")
    else:
        print(f"\n[ERROR] {result['message']}")
        print("\nTo enable image search:")
        print("1. Get OpenAI API key: https://platform.openai.com/api-keys")
        print("2. Add to .env file: OPENAI_API_KEY=your_key_here")
        print("3. Run this script again")

