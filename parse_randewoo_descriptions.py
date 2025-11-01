"""
Parse descriptions and images from Randewoo product pages using Selenium
Usage: python parse_randewoo_descriptions.py [--limit N] [--start-id ID]
"""
import sqlite3
import time
import argparse
import os
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

DB_PATH = 'fragrantica_news.db'
IMAGES_FOLDER = 'main_images'

# Ensure images folder exists
os.makedirs(IMAGES_FOLDER, exist_ok=True)

def setup_driver():
    """Setup Chrome driver with options"""
    options = Options()
    options.add_argument('--headless')  # Run in background
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    return driver

def sanitize_filename(text):
    """Sanitize filename by removing invalid characters"""
    # Remove invalid characters for Windows filenames
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    # Limit length
    return text[:100]

def download_image(image_url, product_id, brand, name):
    """Download image from URL and save to generated_images folder"""
    try:
        # Sanitize brand and name for filename
        brand_clean = sanitize_filename(brand)
        name_clean = sanitize_filename(name)
        
        # Create filename: Brand_Name_ID.jpg
        filename = f"{brand_clean}_{name_clean}_{product_id}.jpg"
        filepath = os.path.join(IMAGES_FOLDER, filename)
        
        # Download image
        print(f"  Downloading image: {image_url}")
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        
        # Save to file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"  [OK] Saved to: {filename}")
        return filename  # Return relative path
        
    except Exception as e:
        print(f"  [ERROR] Failed to download image: {e}")
        return None

def parse_description_and_image(driver, product_url):
    """Parse description and image URL from product page"""
    try:
        print(f"  Fetching: {product_url}")
        driver.get(product_url)
        
        # Wait for content to load (wait for collapsable div)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'collapsable')))
        
        # Give a bit more time for JS to render
        time.sleep(1)
        
        # Get page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find description
        collapsable = soup.find('div', class_='collapsable')
        description = None
        
        if collapsable:
            # Extract paragraphs
            paragraphs = collapsable.find_all('p')
            description_parts = []
            
            for p in paragraphs:
                # Remove links but keep their text
                for a in p.find_all('a'):
                    a.replace_with(a.get_text())
                
                # Remove <br> tags
                for br in p.find_all('br'):
                    br.replace_with(' ')
                
                # Get clean text
                text = p.get_text().strip()
                # Remove extra whitespace
                text = ' '.join(text.split())
                
                if text:
                    description_parts.append(text)
            
            description = '\n\n'.join(description_parts)
            
            if description:
                print(f"  [OK] Parsed description: {len(description)} chars")
            else:
                print("  [WARN] Empty description")
        else:
            print("  [WARN] No collapsable div found")
        
        # Find main product image
        image_url = None
        main_img = soup.find('img', class_='js-main-product-image')
        
        if main_img:
            # Priority: data-zoom-image > srcset 2x > src
            if main_img.get('data-zoom-image'):
                image_url = main_img.get('data-zoom-image')
                print(f"  [OK] Found image (data-zoom-image)")
            elif main_img.get('srcset'):
                srcset = main_img.get('srcset')
                parts = [s.strip() for s in srcset.split(',')]
                for part in parts:
                    if '2x' in part:
                        image_url = part.split()[0]
                        print(f"  [OK] Found image (srcset 2x)")
                        break
                if not image_url and parts:
                    image_url = parts[0].split()[0]
                    print(f"  [OK] Found image (srcset 1x)")
            elif main_img.get('src'):
                image_url = main_img.get('src')
                print(f"  [OK] Found image (src)")
            
            # Make URL absolute if relative
            if image_url:
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = 'https://randewoo.ru' + image_url
        else:
            print("  [WARN] No product image found")
        
        return description, image_url
            
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return None, None

def update_product(product_id, description, image_path):
    """Update description and image_path in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE randewoo_products
        SET description = ?, image_path = ?
        WHERE id = ?
    ''', (description, image_path, product_id))
    
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Parse Randewoo descriptions')
    parser.add_argument('--limit', type=int, default=50, help='Number of products to parse')
    parser.add_argument('--start-id', type=int, default=None, help='Start from specific product ID')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    args = parser.parse_args()
    
    print("="*70)
    print("Randewoo Description Parser")
    print("="*70)
    
    # Get products without descriptions
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if args.start_id:
        cursor.execute('''
            SELECT id, brand, name, product_url
            FROM randewoo_products
            WHERE (description IS NULL OR description = '') AND id >= ?
            ORDER BY id ASC
            LIMIT ?
        ''', (args.start_id, args.limit))
    else:
        cursor.execute('''
            SELECT id, brand, name, product_url
            FROM randewoo_products
            WHERE description IS NULL OR description = ''
            ORDER BY id ASC
            LIMIT ?
        ''', (args.limit,))
    
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        print("\n[INFO] No products without descriptions found!")
        return
    
    print(f"\n[INFO] Found {len(products)} products without descriptions")
    print(f"[INFO] Will parse up to {args.limit} products")
    
    if not input("\nContinue? [y/N]: ").lower().startswith('y'):
        print("Cancelled")
        return
    
    # Setup Selenium
    print("\n[INFO] Starting Chrome browser...")
    driver = setup_driver()
    
    try:
        success_count = 0
        fail_count = 0
        
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] {product['brand']} - {product['name']}")
            
            # Parse description and image URL
            description, image_url = parse_description_and_image(driver, product['product_url'])
            
            # Download image if found
            image_path = None
            if image_url:
                image_path = download_image(image_url, product['id'], product['brand'], product['name'])
            
            # Update database if we got description or image
            if description or image_path:
                update_product(product['id'], description, image_path)
                success_count += 1
                print(f"  [SAVED] Updated product #{product['id']}")
            else:
                fail_count += 1
                print(f"  [SKIP] Nothing to save")
            
            # Small delay to be respectful
            time.sleep(0.5)
        
        print("\n" + "="*70)
        print("COMPLETE!")
        print("="*70)
        print(f"Success: {success_count}")
        print(f"Failed: {fail_count}")
        print(f"Total: {len(products)}")
        
    finally:
        print("\n[INFO] Closing browser...")
        driver.quit()

if __name__ == '__main__':
    main()

