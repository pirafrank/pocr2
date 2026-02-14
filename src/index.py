"""
OCR Screenshot Processor
Processes images from a folder using multithreaded OCR and stores results in SQLite database.
"""

import sys
from typing import Optional

from .db.database import OCRDatabase
from .utils.ocr_processor import OCRProcessor, ProcessingStatus
from .utils.config import *

def progress_callback(filename: str, status: ProcessingStatus):
    """Callback function to display progress during processing."""
    if status == ProcessingStatus.SUCCESS:
        print(f"✓ {filename}: Successfully processed")
    elif status == ProcessingStatus.ALREADY_IN_DB:
        print(f"⊘ {filename}: Already in database")
    else:
        print(f"✗ {filename}: Failed")


def process(prog_callback=None, config_path=None, config: Optional[dict] = None):
    """Process screenshots folder and store OCR results in database.

    Args:
        prog_callback: Optional custom callback function(filename, status).
                                 If None, uses the default progress_callback.
        config_path: Optional path to custom config.toml.
        config: Optional preloaded config dictionary.
    """
    if config_path:
        set_config_file(config_path)

    # Ensure all required directories exist
    ensure_dirs()

    config_data = config if config is not None else load_config()
    tesseract_path = str(config_data.get("tesseract_path", "")).strip() or (
        "tesseract.exe" if sys.platform == "win32" else "tesseract"
    )
    max_workers = int(config_data.get("max_workers", 4))
    screenshots_dir = config_data.get("screenshots_dir")
    if not screenshots_dir:
        raise RuntimeError("Missing 'screenshots_dir' in configuration.")
    ocr_engine = str(config_data.get("ocr_engine", "tesseract")).strip().lower()
    if ocr_engine not in ("tesseract", "ollama"):
        ocr_engine = "tesseract"
    ollama_host = str(config_data.get("ollama_host", "http://localhost:11434")).strip()
    ollama_model = str(config_data.get("ollama_model", "glm-ocr")).strip()
    ollama_prompt = str(
        config_data.get(
            "ollama_prompt", "Extract the text from this image and format it as Markdown."
        )
    ).strip()

    # Initialize database handler
    db = OCRDatabase(get_db_file())

    # Initialize OCR processor
    processor = OCRProcessor(
        tesseract_path=tesseract_path,
        max_workers=max_workers,
        ocr_engine=ocr_engine,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        ollama_prompt=ollama_prompt,
    )

    # Use custom callback if provided, otherwise use default
    callback = prog_callback if prog_callback else progress_callback

    # Process all images in the folder
    stats = processor.process_folder(
        folder_path=screenshots_dir, db_handler=db, progress_callback=callback
    )

    # Cleanup
    db.close()

    return stats


def main(config_path=None):
    """Main processing function."""
    if config_path:
        set_config_file(config_path)

    config = load_config()
    print_config()
    screenshots_dir = get_screenshots_dir()
    max_workers = get_max_workers()
    ocr_engine = get_ocr_engine()
    ollama_host = get_ollama_host()
    ollama_model = get_ollama_model()

    print(f"Starting OCR processing from: {screenshots_dir}")
    print(f"OCR engine: {ocr_engine}")
    if ocr_engine == "ollama":
        print(f"Ollama host: {ollama_host}")
        print(f"Ollama model: {ollama_model}")
    print(f"Using {max_workers} threads\n")

    # Process screenshots folder
    stats = process(config=config)

    # Display summary
    print("\n" + "=" * 50)
    print("Processing Complete!")
    print("=" * 50)
    print(f"Total files found: {stats['total']}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Skipped (already in DB): {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
