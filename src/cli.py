"""
OCR Query
CLI for searching OCR database.
"""

from db.database import OCRDatabase
from query import exact_search, fuzzy_search


# Configuration
DB_FILE = "ocr_screenshots.db"


def main():
    """Main query function."""
    print("OCR Query Tool")
    print("=" * 60)

    term_to_search = input("Enter text to search: ")
    search_mode = input("Search mode (1=exact, 2=fuzzy): ").strip()

    # Initialize database handler
    db = OCRDatabase(DB_FILE)

    try:
        if search_mode == "2":
            threshold_input = input(
                "Enter fuzzy threshold (0.0-1.0, default 0.5): "
            ).strip()
            threshold = float(threshold_input) if threshold_input else 0.5
            matches = fuzzy_search(db, term_to_search, threshold=threshold)
            print(f"\nPerforming fuzzy search (threshold: {threshold})...")
        else:
            matches = exact_search(db, term_to_search)
            print("\nPerforming exact search...")

        if matches:
            print(f"\nFound {len(matches)} matches:")
            print("=" * 60)
            for filename, _text in matches:
                # print_result(filename, _text)
                print(f"  {filename}")
        else:
            print("\nNo matches found.")

    finally:
        # Cleanup
        db.close()


if __name__ == "__main__":
    main()
