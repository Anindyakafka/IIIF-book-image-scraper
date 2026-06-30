#!/usr/bin/env python3
"""
IIIF Image Scraper for British Library and other IIIF repositories
Extracts and downloads all images from a IIIF manifest
"""

import requests
import json
import os
from pathlib import Path
from urllib.parse import urlparse
import sys

def fetch_manifest(manifest_url):
    """Fetch the IIIF manifest JSON"""
    print(f"Fetching manifest from: {manifest_url}")
    try:
        response = requests.get(manifest_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching manifest: {e}")
        return None

def extract_image_urls(manifest):
    """Extract image URLs from IIIF manifest"""
    images = []
    
    # Handle IIIF v2 and v3 formats
    if 'sequences' in manifest:  # v2
        for sequence in manifest['sequences']:
            for canvas in sequence.get('canvases', []):
                for image in canvas.get('images', []):
                    image_resource = image.get('resource', {})
                    image_url = image_resource.get('@id') or image_resource.get('url')
                    if image_url:
                        images.append(image_url)
                        
    elif 'items' in manifest:  # v3
        for item in manifest['items']:
            if item.get('type') == 'Canvas':
                for painting_anno in item.get('items', []):
                    for anno_body in painting_anno.get('items', []):
                        body_obj = anno_body.get('body', {})
                        # Extract full-resolution service URL from body.service[]
                        # body.id is a low-res thumbnail; service[] points to full-res
                        services = body_obj.get('service', [])
                        if services:
                            # Prefer ImageService2 (@id), fall back to ImageService3 (id)
                            svc = services[0]
                            image_url = svc.get('@id') or svc.get('id')
                            if image_url:
                                images.append(image_url)
    
    return images

def get_image_info(info_url):
    """Fetch IIIF image info.json to determine available qualities and formats"""
    try:
        response = requests.get(info_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def get_full_image_url(image_url, quality="best"):
    """
    Convert IIIF image service URL to full image download URL.
    
    Quality options:
    - 'best': TIFF if available (lossless uncompressed), then PNG, then JPG
    - 'tif': TIFF format (highest quality, lossless uncompressed)
    - 'png': PNG lossless format
    - 'jpg': JPG format (smaller file size)
    - 'color': Full color (default quality)
    - 'gray': Grayscale
    """
    # Normalize: if URL points to a service base, append info.json
    if '/info.json' in image_url:
        base = image_url.replace('/info.json', '')
        info_url = image_url
    else:
        base = image_url.rstrip('/')
        info_url = base + '/info.json'
    
    # Fetch info.json to determine available formats
    info_data = get_image_info(info_url)
    available_formats = _get_available_formats(info_data)
    
    # Determine best format and quality
    if quality == "best":
        # Priority: TIFF (lossless uncompressed) > PNG (lossless) > JPG
        if 'tif' in available_formats:
            return f"{base}/full/max/0/default.tif"
        elif 'png' in available_formats:
            return f"{base}/full/max/0/default.png"
        else:
            return f"{base}/full/max/0/default.jpg"
    elif quality == "tif":
        return f"{base}/full/max/0/default.tif"
    elif quality == "png":
        return f"{base}/full/max/0/default.png"
    elif quality == "jpg":
        return f"{base}/full/max/0/default.jpg"
    elif quality == "gray":
        return f"{base}/full/max/0/gray.jpg"
    else:  # "color" or other
        return f"{base}/full/max/0/default.jpg"


def _get_available_formats(info_data):
    """Extract available image formats from info.json (supports both v2 and v3)"""
    formats = set()
    if not info_data:
        return formats
    # v3: extraFormats is a top-level array; also check 'format' for the default
    if 'extraFormats' in info_data:
        formats.update(info_data['extraFormats'])
    if 'format' in info_data:
        formats.add(info_data['format'])
    # v2: profile can be a list where [1] is a dict with 'formats' key
    profile = info_data.get('profile', [])
    if isinstance(profile, list):
        for p in profile:
            if isinstance(p, dict) and 'formats' in p:
                formats.update(p['formats'])
    return formats

def download_images(image_urls, output_dir="downloaded_images", quality="best",
                    skip_existing=True, max_retries=3):
    """
    Download all images to output directory.
    
    Args:
        image_urls: List of IIIF image service URLs
        output_dir: Directory to save images
        quality: Image quality ('best', 'tif', 'png', 'jpg', etc.)
        skip_existing: If True, skip images already downloaded (for resuming)
        max_retries: Number of retry attempts per failed image
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"\nFound {len(image_urls)} images")
    print(f"Quality: {quality}")
    print(f"Downloading to: {os.path.abspath(output_dir)}")
    print(f"Skip existing: {skip_existing}, Max retries: {max_retries}\n")
    
    successful = 0
    failed = 0
    skipped = 0
    
    for idx, image_url in enumerate(image_urls, 1):
        # Determine extension from quality (we know it'll be TIFF for "best" on BL)
        if quality == "tif":
            ext = ".tif"
        elif quality == "png":
            ext = ".png"
        elif quality in ("jpg", "color", "gray"):
            ext = ".jpg"
        else:
            ext = ".tif"  # default for "best"
        
        filename = f"image_{idx:04d}{ext}"
        filepath = os.path.join(output_dir, filename)
        
        # Skip if file already exists and has content
        if skip_existing and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"[{idx}/{len(image_urls)}] Already exists: {filename} ({size_mb:.1f} MB) — skipping")
            skipped += 1
            successful += 1
            continue
        
        # Download with retry logic
        downloaded = False
        for attempt in range(1, max_retries + 1):
            try:
                full_url = get_full_image_url(image_url, quality=quality)
                suffix = f" (attempt {attempt}/{max_retries})" if attempt > 1 else ""
                print(f"[{idx}/{len(image_urls)}] Downloading: {full_url[:80]}...{suffix}")
                
                # Update ext in case format changed (e.g., best resolved to png)
                if full_url.endswith(".tif"):
                    ext = ".tif"
                    filename = f"image_{idx:04d}{ext}"
                    filepath = os.path.join(output_dir, filename)
                elif full_url.endswith(".png"):
                    ext = ".png"
                    filename = f"image_{idx:04d}{ext}"
                    filepath = os.path.join(output_dir, filename)
                else:
                    ext = ".jpg"
                    filename = f"image_{idx:04d}{ext}"
                    filepath = os.path.join(output_dir, filename)
                
                response = requests.get(full_url, timeout=300, stream=True)
                response.raise_for_status()
                
                # Write file in chunks (handles large TIFFs without loading all into RAM)
                total_bytes = 0
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_bytes += len(chunk)
                
                print(f"  ✓ Saved as {filename} ({total_bytes / (1024*1024):.1f} MB)")
                successful += 1
                downloaded = True
                break  # success, exit retry loop
                
            except Exception as e:
                print(f"  ✗ Attempt {attempt}/{max_retries} failed: {e}")
                # Clean up partial file
                if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
                    os.remove(filepath)
                if attempt < max_retries:
                    print(f"    Retrying...")
        
        if not downloaded:
            print(f"  ✗✗ FAILED after {max_retries} attempts: image_{idx:04d}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Download complete: {successful} successful ({skipped} already existed), {failed} failed")
    print(f"Images saved to: {os.path.abspath(output_dir)}")
    return successful, failed

def main():
    # IIIF manifest URL from British Library
    manifest_url = "https://bl.digirati.io/iiif/ark:/81055/vdc_100058663072.0x000001"
    quality = "best"  # Default: TIFF if available (highest quality), else PNG, else JPG
    
    # Optional: allow command line arguments
    if len(sys.argv) > 1:
        manifest_url = sys.argv[1]
    if len(sys.argv) > 2:
        quality = sys.argv[2].lower()
    
    # Validate quality argument
    valid_qualities = ["best", "tif", "png", "jpg", "color", "gray"]
    if quality not in valid_qualities:
        print(f"Invalid quality: {quality}")
        print(f"Valid options: {', '.join(valid_qualities)}")
        quality = "best"
    
    # Fetch manifest
    manifest = fetch_manifest(manifest_url)
    if not manifest:
        print("Failed to fetch manifest")
        return
    
    # Extract image URLs
    image_urls = extract_image_urls(manifest)
    if not image_urls:
        print("No images found in manifest")
        return
    
    # Download images
    download_images(image_urls, quality=quality)

if __name__ == "__main__":
    main()
