# POCR 2

An ptical Character Recognition (OCR) minimal CLI tool to recognized, save, and query data from images with lots of text, e.g. screenshots you make to remember things.

So boost privacy and avoid sending your images to third-party services, this tool runs locally on your machine. It's fast, multi-platform, and multi-threaded.

## Features

- Image text extraction from multiple image formats (PNG, JPG, BMP, etc.)
- Dead-simple Python interface
- Local processing for enhanced privacy
- Multi-threaded for performance
- Powered by tesseract OCR engine

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Usage is managed via `just` commands to make it simple, like so:

```
just setup
just process
just query
```

## Requirements

- Python 3.12+ (it may work on earlier versions, yet not tested)
- Additional dependencies in `requirements.txt`

## License

See LICENSE file for details.

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## Disclaimer

This project is provided "as is" without any warranties. Use at your own risk.
