"""
OCR Screenshot Processor
Processes images from a folder using multithreaded OCR and stores results in SQLite database.
"""

from .db.database import OCRDatabase
from .utils.ocr_processor import OCRProcessor, ProcessingStatus
from .utils.config import (
    DB_FILE,
    get_screenshots_dir,
    get_tesseract_path,
    get_max_workers,
    get_ocr_engine,
    get_ollama_host,
    get_ollama_model,
    get_ollama_prompt,
    ensure_dirs,
    set_config_file,
)

def progress_callback(filename: str, status: ProcessingStatus):
    """Callback function to display progress during processing."""
    if status == ProcessingStatus.SUCCESS:
        print(f"✓ {filename}: Successfully processed")
    elif status == ProcessingStatus.ALREADY_IN_DB:
        print(f"⊘ {filename}: Already in database")
    else:
        print(f"✗ {filename}: Failed")


def process(prog_callback=None, config_path=None):
    """Process screenshots folder and store OCR results in database.

    Args:
        prog_callback: Optional custom callback function(filename, status).
                                 If None, uses the default progress_callback.
        config_path: Optional path to custom config.toml.
    """
    if config_path:
        set_config_file(config_path)

    # Ensure all required directories exist
    ensure_dirs()

    tesseract_path = get_tesseract_path()
    max_workers = get_max_workers()
    screenshots_dir = get_screenshots_dir()
    ocr_engine = get_ocr_engine()
    ollama_host = get_ollama_host()
    ollama_model = get_ollama_model()
    ollama_prompt = get_ollama_prompt()

    # Initialize database handler
    db = OCRDatabase(DB_FILE)

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

    screenshots_dir = get_screenshots_dir()
    max_workers = get_max_workers()
    ocr_engine = get_ocr_engine()
    ollama_host = get_ollama_host()
    ollama_model = get_ollama_model()

    print(f"Starting OCR processing from: {screenshots_dir}")
    print(f"OCR engine: {ocr_engine}")
    if ocr_engine == "glm-ocr":
        print(f"Ollama host: {ollama_host}")
        print(f"Ollama model: {ollama_model}")
    print(f"Using {max_workers} threads\n")

    # Process screenshots folder
    stats = process(config_path=config_path)

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
