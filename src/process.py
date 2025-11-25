"""
OCR Screenshot Processor
Processes images from a folder using multithreaded OCR and stores results in SQLite database.
"""

from db.database import OCRDatabase
from utils.ocr_processor import OCRProcessor


# Configuration
DB_FILE = "ocr_screenshots.db"
TESSERACT_PATH = (
    r"C:\Users\francesco\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"
)
SCREENSHOTS_DIR = (
    r"C:\\Users\francesco\\OneDrive - Leonardo S.p.a. - Div Cyber Security\\Screenshots"
)
MAX_WORKERS = 4  # Number of threads for parallel processing


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
