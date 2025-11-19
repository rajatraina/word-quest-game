#!/usr/bin/env python3
"""
Script to download cat breed images from various sources.
This script will download 3-5 images for each cat breed and save them locally.

Usage:
    python3 download_cat_images.py

Requirements:
    - requests library
    - Optional: GOOGLE_API_KEY and GOOGLE_CX for Google Image Search
    - Optional: UNSPLASH_ACCESS_KEY for Unsplash
    - Optional: PEXELS_API_KEY for Pexels
"""

import os
import json
import requests
import time
from pathlib import Path
from urllib.parse import urlparse
import hashlib

# Load cat breeds from JSON file (same as main.py)
def load_cat_breeds():
    """Load cat breeds from JSON file."""
    try:
        with open('cat_breeds_api.json', 'r') as f:
            breeds = json.load(f)
            # Ensure breed_number is set correctly
            for i, breed in enumerate(breeds):
                breed['breed_number'] = i + 1
            return breeds
    except FileNotFoundError:
        print("Warning: cat_breeds_api.json not found. Run fetch_cat_breeds.py first.")
        return []

# Load cat breeds from JSON file (same as main.py)
def load_cat_breeds():
    """Load cat breeds from JSON file."""
    try:
        with open('cat_breeds_api.json', 'r') as f:
            breeds = json.load(f)
            # Ensure breed_number is set correctly
            for i, breed in enumerate(breeds):
                breed['breed_number'] = i + 1
            return breeds
    except FileNotFoundError:
        print("Warning: cat_breeds_api.json not found. Run fetch_cat_breeds.py first.")
        return []

CAT_BREEDS = load_cat_breeds()

ASSETS_DIR = Path('assets/cat_images')
IMAGES_PER_BREED = 5
DOWNLOAD_DELAY = 1  # Seconds between downloads to be respectful

def sanitize_filename(name):
    """Convert breed name to safe filename."""
    return name.lower().replace(' ', '_').replace("'", '')

def download_image(url, filepath):
    """Download an image from URL and save to filepath."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return False
        
        # Save the image
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify file was created and has content
        if filepath.exists() and filepath.stat().st_size > 0:
            return True
        return False
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False

def fetch_google_images(breed_name, num_images=5):
    """Fetch images from Google Custom Search API."""
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    cx = os.environ.get('GOOGLE_CX', '')
    
    if not api_key or not cx:
        return []
    
    images = []
    search_queries = [
        f"cute {breed_name} cat",
        f"fluffy {breed_name} cat",
        f"{breed_name} cat portrait",
        f"{breed_name} cat",
        f"beautiful {breed_name} cat"
    ]
    
    try:
        for query in search_queries[:num_images]:
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'key': api_key,
                'cx': cx,
                'q': query,
                'searchType': 'image',
                'num': 1,
                'safe': 'active',
                'imgSize': 'medium',
                'imgType': 'photo'
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('items') and len(data['items']) > 0:
                    image_url = data['items'][0]['link']
                    images.append(image_url)
                    if len(images) >= num_images:
                        break
            elif response.status_code == 429:
                print(f"  Rate limit reached for Google API")
                break
            time.sleep(DOWNLOAD_DELAY)
    except Exception as e:
        print(f"  Error with Google API: {e}")
    
    return images

def fetch_unsplash_images(breed_name, num_images=5):
    """Fetch images from Unsplash API."""
    api_key = os.environ.get('UNSPLASH_ACCESS_KEY', '')
    if not api_key:
        return []
    
    images = []
    search_queries = [
        f"cute {breed_name} cat",
        f"fluffy {breed_name} cat",
        f"{breed_name} cat"
    ]
    
    try:
        for query in search_queries:
            url = 'https://api.unsplash.com/search/photos'
            headers = {'Authorization': f'Client-ID {api_key}'}
            params = {
                'query': query,
                'per_page': min(2, num_images - len(images)),
                'orientation': 'squarish'
            }
            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    for result in data['results']:
                        if 'urls' in result and 'small' in result['urls']:
                            images.append(result['urls']['small'])
                            if len(images) >= num_images:
                                break
            time.sleep(DOWNLOAD_DELAY)
    except Exception as e:
        print(f"  Error with Unsplash API: {e}")
    
    return images

def fetch_cat_api_images(breed_name, num_images=5, api_id=None):
    """Fetch images from The Cat API."""
    images = []
    
    try:
        if api_id:
            # Use the API ID directly
            url = 'https://api.thecatapi.com/v1/images/search'
            params = {'limit': num_images, 'breed_ids': api_id}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if 'url' in item:
                        images.append(item['url'])
        else:
            # Fallback to breed name search or general cat images
            breed_id_map = {
                'persian': 'pers',
                'siamese': 'siam',
                'maine coon': 'mcoo',
                'bengal': 'beng',
                'ragdoll': 'ragd',
                'british shorthair': 'bsho',
                'abyssinian': 'abys',
                'scottish fold': 'sfol',
                'sphynx': 'sphy',
                'norwegian forest cat': 'norw',
                'russian blue': 'rblu',
                'turkish angora': 'tang',
                'oriental': 'orie',
                'american shorthair': 'asho',
                'exotic shorthair': 'esho',
                'devon rex': 'drex',
                'cornish rex': 'crex',
                'himalayan': 'hima',
                'burmese': 'bure',
                'tonkinese': 'tonk'
            }
            breed_lower = breed_name.lower()
            breed_id = breed_id_map.get(breed_lower, None)
            
            if breed_id:
                url = 'https://api.thecatapi.com/v1/images/search'
                params = {'limit': num_images, 'breed_ids': breed_id}
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        if 'url' in item:
                            images.append(item['url'])
            else:
                # Fallback to general cat images
                url = 'https://api.thecatapi.com/v1/images/search'
                params = {'limit': num_images}
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        if 'url' in item:
                            images.append(item['url'])
        time.sleep(DOWNLOAD_DELAY)
    except Exception as e:
        print(f"  Error with The Cat API: {e}")
    
    return images

def download_breed_images(breed):
    """Download images for a specific breed."""
    breed_name = breed.get('name', 'Unknown')
    breed_dir = ASSETS_DIR / sanitize_filename(breed_name)
    breed_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nDownloading images for {breed_name}...")
    
    # Check how many images we already have
    existing_images = list(breed_dir.glob('*.jpg')) + list(breed_dir.glob('*.png'))
    if len(existing_images) >= IMAGES_PER_BREED:
        print(f"  Already have {len(existing_images)} images, skipping...")
        return
    
    # Try to fetch images from various sources
    all_image_urls = []
    
    # Try Google first (best quality)
    if os.environ.get('GOOGLE_API_KEY') and os.environ.get('GOOGLE_CX'):
        print("  Trying Google Custom Search API...")
        urls = fetch_google_images(breed_name, IMAGES_PER_BREED)
        all_image_urls.extend(urls)
    
    # Try Unsplash
    if len(all_image_urls) < IMAGES_PER_BREED and os.environ.get('UNSPLASH_ACCESS_KEY'):
        print("  Trying Unsplash API...")
        urls = fetch_unsplash_images(breed_name, IMAGES_PER_BREED - len(all_image_urls))
        all_image_urls.extend(urls)
    
    # Try The Cat API (free, no auth)
    if len(all_image_urls) < IMAGES_PER_BREED:
        print("  Trying The Cat API...")
        # Use API ID if available, otherwise use breed name
        api_id = breed.get('api_id', None)
        urls = fetch_cat_api_images(breed_name, IMAGES_PER_BREED - len(all_image_urls), api_id)
        all_image_urls.extend(urls)
    
    # Download the images
    downloaded = 0
    for i, image_url in enumerate(all_image_urls[:IMAGES_PER_BREED]):
        # Determine file extension
        parsed = urlparse(image_url)
        ext = os.path.splitext(parsed.path)[1] or '.jpg'
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            ext = '.jpg'
        
        filepath = breed_dir / f"{i+1}{ext}"
        
        if filepath.exists():
            print(f"  Image {i+1} already exists, skipping...")
            downloaded += 1
            continue
        
        print(f"  Downloading image {i+1}/{IMAGES_PER_BREED}...")
        if download_image(image_url, filepath):
            downloaded += 1
            print(f"    ✓ Saved to {filepath}")
        else:
            print(f"    ✗ Failed to download")
        
        time.sleep(DOWNLOAD_DELAY)
    
    print(f"  Downloaded {downloaded}/{IMAGES_PER_BREED} images for {breed_name}")

def main():
    """Main function to download images for all breeds."""
    print("Cat Breed Image Downloader")
    print("=" * 50)
    
    # Create assets directory
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for API keys
    has_google = bool(os.environ.get('GOOGLE_API_KEY') and os.environ.get('GOOGLE_CX'))
    has_unsplash = bool(os.environ.get('UNSPLASH_ACCESS_KEY'))
    
    if has_google:
        print("✓ Google Custom Search API configured")
    if has_unsplash:
        print("✓ Unsplash API configured")
    if not has_google and not has_unsplash:
        print("⚠ No API keys found, will use The Cat API (free, no auth)")
        print("  For better results, set GOOGLE_API_KEY/GOOGLE_CX or UNSPLASH_ACCESS_KEY")
    
    print(f"\nWill download {IMAGES_PER_BREED} images per breed")
    print(f"Total breeds: {len(CAT_BREEDS)}")
    
    # Download images for each breed
    for breed in CAT_BREEDS:
        download_breed_images(breed)
    
    print("\n" + "=" * 50)
    print("Download complete!")
    print(f"Images saved to: {ASSETS_DIR.absolute()}")

if __name__ == '__main__':
    main()

