# IIIF Book Image Scraper

A tool to download high-quality images from IIIF (International Image Interoperability Framework) manifests, commonly used by digital libraries and archives.

## Features

- Download images from IIIF v2 and v3 manifests
- Support for multiple image quality levels
- Both Python and Bash implementations available
- Configurable output directory

## Installation

### Python Version

```bash
pip install requests
```

### Bash Version

Requires `curl` and `jq`:
```bash
# On Ubuntu/Debian
sudo apt-get install curl jq

# On macOS with Homebrew
brew install curl jq
```

## Usage

### Python Script

```bash
python src/iiif_image_scraper.py <manifest_url> [quality]
```

Example:
```bash
python src/iiif_image_scraper.py https://example.org/manifest.json high
```

### Bash Script

```bash
bash src/iiif_image_scraper.sh <manifest_url> [quality]
```

Example:
```bash
bash src/iiif_image_scraper.sh https://example.org/manifest.json high
```

## Quality Options

- `native`: Original image size (largest)
- `high`: High quality
- `medium`: Medium quality (default)
- `low`: Low quality

## Structure

```
.
├── src/                 # Source code
│   ├── iiif_image_scraper.py
│   └── iiif_image_scraper.sh
├── docs/                # Documentation
│   └── IIIF_SCRAPER_README.md
├── downloaded_images/   # Output directory (created automatically)
└── README.md            # This file
```

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.