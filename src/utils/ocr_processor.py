import os
from typing import List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from PIL import Image
import cv2
import pytesseract


class ProcessingStatus(Enum):
    """Status of image processing operation."""

    SUCCESS = "success"
    ALREADY_IN_DB = "already_in_db"
    FAILED = "failed"


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

    def extract_text(self, image_source: Union[str, Image.Image]) -> str:
        """
        Extract text from a single image using OCR.

        Args:
            image_source: Either a full path to the image file or a PIL Image object

        Returns:
            Extracted text from the image
        """
        try:
            if isinstance(image_source, str):
                image = Image.open(image_source)
            else:
                image = image_source

            text = pytesseract.image_to_string(image)
            return text
        except (IOError, OSError) as e:
            source_name = image_source if isinstance(image_source, str) else "PIL Image"
            print(f"Error processing {source_name}: {e}")
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

    def resize_for_ocr(
        self, image_path: str, scale_factor: float = 3.0
    ) -> Union[Image.Image, None]:
        """
        Resize image for optimal OCR performance.

        Args:
            image_path: Path to the image file
            scale_factor: Scaling factor for enlargement (default: 3.0)

        Returns:
            Resized PIL Image object, or None if processing fails
        """
        try:
            img = cv2.imread(image_path)

            if img is None:
                print(f"Error: Could not read image from {image_path}")
                return None

            enlarged = cv2.resize(
                img,
                None,
                fx=scale_factor,
                fy=scale_factor,
                interpolation=cv2.INTER_CUBIC,
            )

            # Convert BGR to RGB and return as PIL Image
            img_rgb = cv2.cvtColor(enlarged, cv2.COLOR_BGR2RGB)
            return Image.fromarray(img_rgb)
        except Exception as e:
            print(f"Error resizing image {image_path}: {e}")
            return None

    def process_image(
        self,
        image_path: str,
        db_handler,
        skip_existing: bool = True,
        scale_factor: float = 3.0,
    ) -> Tuple[str, ProcessingStatus]:
        """
        Process a single image: extract text and save to database.

        Args:
            image_path: Full path to the image
            db_handler: Database handler instance
            skip_existing: Whether to skip files already in the database
            scale_factor: Scaling factor for image enlargement (default: 3.0)

        Returns:
            Tuple of (filename, status)
        """
        filename = os.path.basename(image_path)

        # Check if already processed
        if skip_existing and db_handler.file_exists(filename):
            return filename, ProcessingStatus.ALREADY_IN_DB

        # Resize image for better OCR performance
        enlarged_image = self.resize_for_ocr(image_path, scale_factor)

        if enlarged_image is None:
            return filename, ProcessingStatus.FAILED

        # Extract text from the enlarged image
        ocr_text = self.extract_text(enlarged_image)

        if not ocr_text.strip():
            return filename, ProcessingStatus.FAILED

        # Save to database
        if db_handler.save_ocr_data(filename, ocr_text):
            return filename, ProcessingStatus.SUCCESS
        else:
            return filename, ProcessingStatus.FAILED

    def process_folder(
        self, folder_path: str, db_handler, progress_callback=None
    ) -> dict:
        """
        Process all images in a folder using multithreading.

        Args:
            folder_path: Path to folder containing images
            db_handler: Database handler instance
            progress_callback: Optional callback function(filename, status)

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
                filename, status = future.result()

                if status == ProcessingStatus.SUCCESS:
                    stats["processed"] += 1
                elif status == ProcessingStatus.ALREADY_IN_DB:
                    stats["skipped"] += 1
                else:
                    stats["failed"] += 1

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(filename, status)

        return stats
