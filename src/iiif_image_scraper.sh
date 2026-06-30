#!/bin/bash
# IIIF Image Scraper using curl and jq
# This is a lightweight alternative that doesn't require Python

set -e

MANIFEST_URL="${1}"
OUTPUT_DIR="${2:-downloaded_images}"
QUALITY="${3:-best}"

if [ -z "$MANIFEST_URL" ]; then
    echo "Usage: $0 <manifest_url> [output_directory] [quality]"
    echo ""
    echo "Quality options: best, png, jpg, color, gray"
    echo "  best   - PNG if available, else color JPG (default)"
    echo "  png    - Lossless PNG (highest quality)"
    echo "  jpg    - Compressed JPG (good quality, smaller files)"
    echo "  color  - Full color JPG"
    echo "  gray   - Grayscale (smaller files)"
    echo ""
    echo "Example:"
    echo "  $0 'https://bl.digirati.io/iiif/ark:/81055/vdc_100058663072.0x000001' downloaded_images best"
    exit 1
fi

# Check for required tools
command -v curl >/dev/null 2>&1 || { echo "curl is required but not installed."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq is required but not installed. Install with: apt-get install jq (Linux) or brew install jq (macOS)"; exit 1; }

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Fetching IIIF manifest..."
echo "URL: $MANIFEST_URL"

# Fetch the manifest
MANIFEST=$(curl -s "$MANIFEST_URL" 2>/dev/null)

if [ -z "$MANIFEST" ]; then
    echo "Error: Failed to fetch manifest"
    exit 1
fi

# Extract images - handle both IIIF v2 and v3
echo "Extracting image URLs..."

# Try IIIF v2 format first (sequences)
IMAGE_URLS=$(echo "$MANIFEST" | jq -r '.sequences[0].canvases[]?.images[]?.resource?.["@id"],.sequences[0].canvases[]?.images[]?.resource?.url' 2>/dev/null | grep -v null | grep -v '^$' || true)

# If no results, try IIIF v3 format (items)
if [ -z "$IMAGE_URLS" ]; then
    IMAGE_URLS=$(echo "$MANIFEST" | jq -r '.items[]?.items[]?.items[]?.body?.id' 2>/dev/null | grep -v null | grep -v '^$' || true)
fi

# Convert array to individual lines if needed
IMAGE_COUNT=$(echo "$IMAGE_URLS" | grep -c . || echo 0)

if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "Error: No images found in manifest"
    exit 1
fi

echo "Found $IMAGE_COUNT images"
echo "Quality: $QUALITY"
echo "Downloading to: $(pwd)/$OUTPUT_DIR"
echo ""

# Determine image format and quality based on QUALITY variable
case "$QUALITY" in
    png)
        QUALITY_PARAM="color.png"
        ;;
    jpg)
        QUALITY_PARAM="color.jpg"
        ;;
    color)
        QUALITY_PARAM="color.jpg"
        ;;
    gray)
        QUALITY_PARAM="gray.jpg"
        ;;
    best|*)
        # For best, try PNG first, fall back to color JPG
        QUALITY_PARAM="color.png"
        ;;
esac

# Download each image
COUNT=1
SUCCESSFUL=0
FAILED=0

while IFS= read -r IMAGE_URL; do
    if [ -z "$IMAGE_URL" ]; then
        continue
    fi
    
    # Convert IIIF Image API URL to full image URL if needed
    if [[ "$IMAGE_URL" == *"/info.json" ]]; then
        BASE_URL="${IMAGE_URL%/info.json}"
        FULL_URL="$BASE_URL/full/max/0/$QUALITY_PARAM"
    else
        FULL_URL="$IMAGE_URL"
    fi
    
    # Determine file extension
    if [[ "$QUALITY_PARAM" == *.png ]]; then
        FILENAME=$(printf "image_%04d.png" "$COUNT")
    else
        FILENAME=$(printf "image_%04d.jpg" "$COUNT")
    fi
    FILEPATH="$OUTPUT_DIR/$FILENAME"
    
    printf "[%d/%d] Downloading: %s... " "$COUNT" "$IMAGE_COUNT" "${FULL_URL:0:60}"
    
    if curl -s -L "$FULL_URL" -o "$FILEPATH" 2>/dev/null; then
        SIZE=$(du -h "$FILEPATH" | cut -f1)
        echo "✓ ($SIZE)"
        ((SUCCESSFUL++))
    else
        echo "✗ Failed"
        rm -f "$FILEPATH"
        ((FAILED++))
    fi
    
    ((COUNT++))
done <<< "$IMAGE_URLS"

echo ""
echo "============================================================"
echo "Download complete: $SUCCESSFUL successful, $FAILED failed"
echo "Images saved to: $(pwd)/$OUTPUT_DIR"
