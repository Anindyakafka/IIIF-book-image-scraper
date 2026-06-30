# IIIF Image Scraper

A Python tool to download all images from IIIF (International Image Interoperability Framework) manifests, including British Library collections.

## What is IIIF?

IIIF is a standard for sharing and accessing digital images. Collections that use IIIF (like the British Library) expose their images through a structured manifest format that allows programmatic access.

## Installation

### Requirements
- Python 3.6+
- `requests` library

### Setup

```bash
pip install requests
```

## Usage

### Basic Usage (Best Quality)

```bash
python iiif_image_scraper.py "https://bl.digirati.io/iiif/ark:/81055/vdc_100058663072.0x000001"
```

This downloads **TIFF** format if available (highest quality, lossless uncompressed), otherwise PNG, otherwise JPG.

### Quality Options

You can specify different quality levels:

```bash
# Best quality - TIFF if available, else PNG, else JPG (default)
python iiif_image_scraper.py "<manifest_url>" best

# TIFF lossless uncompressed format (absolute highest quality, largest files ~50MB+)
python iiif_image_scraper.py "<manifest_url>" tif

# PNG lossless format (high quality, large files)
python iiif_image_scraper.py "<manifest_url>" png

# Compressed JPG format (smaller files, good quality)
python iiif_image_scraper.py "<manifest_url>" jpg

# Full color JPG (server default)
python iiif_image_scraper.py "<manifest_url>" color

# Grayscale (for b&w documents, smaller files)
python iiif_image_scraper.py "<manifest_url>" gray
```

### Quality Comparison

| Option | Format | Quality | File Size | Best For |
|--------|--------|---------|-----------|----------|
| **best** | TIFF/PNG/JPG | Highest | Very Large | Maximum fidelity (auto-selects best available) |
| **tif** | TIFF | Lossless Uncompressed | ~50MB+ per image | Archival, absolute maximum quality |
| **png** | PNG | Lossless | Large | Photography, detailed art |
| **jpg** | JPG | High | Medium | General use |
| **color** | JPG | High | Medium | Color documents |
| **gray** | JPG | Good | Small | B&W manuscripts |

### How to find IIIF manifest URLs

1. **From the British Library:**
   - Go to any digitized item on the British Library website
   - Look for a "IIIF Manifest" link or URL pattern
   - It will look like: `https://bl.digirati.io/iiif/ark:/81055/[id]`

2. **From the viewer:**
   - Right-click in the Universal Viewer (UV)
   - Look for manifest/metadata information
   - Or check the browser's network tab

3. **Common British Library pattern:**
   - `https://bl.digirati.io/iiif/ark:/81055/[unique-id]`
   - `https://api.bl.uk/metadata/iiif/ark:/81055/[unique-id]/manifest.json`

## Features

- ✅ **Multiple quality levels**: TIFF lossless uncompressed, PNG lossless, JPG, grayscale
- ✅ **Automatic quality detection**: TIFF if available, else PNG, else JPG
- ✅ Downloads all images from a IIIF manifest
- ✅ Automatically detects IIIF Image API URLs and converts them
- ✅ Supports both IIIF v2 and v3 manifest formats
- ✅ Creates organized output directory
- ✅ Shows progress for each download
- ✅ Handles errors gracefully
- ✅ Full resolution downloads (not downscaled)

## Output

Images are saved to `downloaded_images/` directory with names like:
- `image_0001.tif` (default best quality — lossless uncompressed TIFF)
- `image_0002.tif`
- etc.

Extension depends on quality chosen: `.tif` (best/tif), `.png` (png), `.jpg` (jpg/color/gray).

## Advanced Usage

### Custom output directory

Modify the script or call it programmatically:

```python
from iiif_image_scraper import fetch_manifest, extract_image_urls, download_images

manifest_url = "https://bl.digirati.io/iiif/ark:/81055/vdc_100058663072.0x000001"
manifest = fetch_manifest(manifest_url)
image_urls = extract_image_urls(manifest)
download_images(image_urls, output_dir="my_custom_folder")
```

## Troubleshooting

### "No images found in manifest"
- The manifest format may not be recognized
- Check if it's a valid IIIF manifest by opening it in a browser
- Try opening the URL directly to see the JSON structure

### "Connection timeout"
- The server might be rate limiting
- Add delays between downloads
- Check your internet connection

### "Permission denied" on image URLs
- Some institutions may have access restrictions
- The script will skip those images and continue

## Tips

1. **Check before downloading:**
   - Open the manifest URL in your browser to preview
   - See how many images will be downloaded

2. **Large collections:**
   - For very large collections (100+ images), the download may take time
   - Consider checking storage space first

3. **Image quality:**
   - The script downloads at maximum available resolution
   - TIFF (default) produces very large files (~50MB+ per image)
   - PNG lossless produces large files (~10-20MB per image)
   - Use `jpg` or `gray` quality if storage is limited

## Legal and Ethical Use

- Check the repository's terms of use and licensing
- British Library content is often available under open licenses (e.g., Creative Commons)
- Respect copyright and attribution requirements
- Use downloaded content according to the specified license

## Example

For the URL you provided:
```bash
python iiif_image_scraper.py "https://bl.digirati.io/iiif/ark:/81055/vdc_100058663072.0x000001"
```

This will download all images from that manuscript/document to your `downloaded_images/` folder.
