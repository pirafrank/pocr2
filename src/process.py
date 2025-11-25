"""
OCR Screenshot Processor
Processes images from a folder using multithreaded OCR and stores results in SQLite database.
"""

from db.database import OCRDatabase
from utils.ocr_processor import OCRProcessor
from utils.config import (
    DB_FILE,
    get_screenshots_dir,
    get_tesseract_path,
    get_max_workers,
    ensure_dirs,
)


# Configuration
TESSERACT_PATH = get_tesseract_path()
MAX_WORKERS = get_max_workers()
SCREENSHOTS_DIR = get_screenshots_dir()


def progress_callback(filename: str, success: bool, message: str):
    """Callback function to display progress during processing."""
    if success:
        print(f"✓ {filename}: {message}")
    elif "Already in database" in message:
        print(f"⊘ {filename}: {message}")
    else:
        print(f"✗ {filename}: {message}")


def main():
    """Main processing function."""
    # Ensure all required directories exist
    ensure_dirs()

    print(f"Starting OCR processing from: {SCREENSHOTS_DIR}")
    print(f"Using {MAX_WORKERS} threads\n")

    # Initialize database handler
    db = OCRDatabase(DB_FILE)

    # Initialize OCR processor
    processor = OCRProcessor(tesseract_path=TESSERACT_PATH, max_workers=MAX_WORKERS)

    # Process all images in the folder
    stats = processor.process_folder(
        folder_path=SCREENSHOTS_DIR, db_handler=db, progress_callback=progress_callback
    )

    # Display summary
    print("\n" + "=" * 50)
    print("Processing Complete!")
    print("=" * 50)
    print(f"Total files found: {stats['total']}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Skipped (already in DB): {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print("=" * 50)

    # Cleanup
    db.close()

if __name__ == "__main__":
    main()
