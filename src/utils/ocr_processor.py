import os
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import pytesseract


class OCRProcessor:
    """
    Multithreaded OCR processor for image files.
    """

    def __init__(self, tesseract_path: str, max_workers: int = 4):
        """
        Initialize the OCR processor.

        Args:
            tesseract_path: Path to the tesseract executable
            max_workers: Maximum number of threads for parallel processing
        """
        self.tesseract_path = tesseract_path
        self.max_workers = max_workers
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.supported_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif")

    def extract_text(self, image_path: str) -> str:
        """
        Extract text from a single image using OCR.

        Args:
            image_path: Full path to the image file

        Returns:
            Extracted text from the image
        """
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except (IOError, OSError) as e:
            print(f"Error processing {image_path}: {e}")
            return ""

    def get_image_files(self, folder_path: str) -> List[str]:
        """
        Get list of all supported image files in a folder.

        Args:
            folder_path: Path to the folder containing images

        Returns:
            List of full paths to image files
        """
        image_files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(self.supported_extensions):
                full_path = os.path.join(folder_path, filename)
                image_files.append(full_path)
        return image_files

    def process_image(
        self, image_path: str, db_handler, skip_existing: bool = True
    ) -> Tuple[str, bool, str]:
        """
        Process a single image: extract text and save to database.

        Args:
            image_path: Full path to the image
            db_handler: Database handler instance
            skip_existing: Whether to skip files already in the database

        Returns:
            Tuple of (filename, success, message)
        """
        filename = os.path.basename(image_path)

        # Check if already processed
        if skip_existing and db_handler.file_exists(filename):
            return filename, False, "Already in database"

        # Extract text
        ocr_text = self.extract_text(image_path)

        if not ocr_text.strip():
            return filename, False, "No text extracted"

        # Save to database
        if db_handler.save_ocr_data(filename, ocr_text):
            return filename, True, "Successfully processed"
        else:
            return filename, False, "Failed to save (duplicate)"

    def process_folder(
        self, folder_path: str, db_handler, progress_callback=None
    ) -> dict:
        """
        Process all images in a folder using multithreading.

        Args:
            folder_path: Path to folder containing images
            db_handler: Database handler instance
            progress_callback: Optional callback function(filename, success, message)

        Returns:
            Dictionary with processing statistics
        """
        image_files = self.get_image_files(folder_path)
        total_files = len(image_files)

        if total_files == 0:
            return {"total": 0, "processed": 0, "skipped": 0, "failed": 0}

        stats = {"total": total_files, "processed": 0, "skipped": 0, "failed": 0}

        # Process images in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_image, img_path, db_handler): img_path
                for img_path in image_files
            }

            # Process results as they complete
            for future in as_completed(future_to_file):
                filename, success, message = future.result()

                if success:
                    stats["processed"] += 1
                elif "Already in database" in message:
                    stats["skipped"] += 1
                else:
                    stats["failed"] += 1

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(filename, success, message)

        return stats
