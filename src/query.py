"""
OCR Query Tool
Search OCR database using fuzzy text matching.
"""

import Levenshtein

from db.database import OCRDatabase


def exact_search(db: OCRDatabase, search_term: str):
    """
    Perform an exact search for `search_term` in the 'ocr_text' field.

    Args:
        db: OCRDatabase instance
        search_term: Text to search for
    Returns:
        List of (filename, ocr_text) tuples matching the search term exactly
    """
    results = db.search_exact(search_term)
    results.sort(key=lambda x: x[0])
    return results


def fuzzy_search(db: OCRDatabase, search_term: str, threshold: float = 0.6):
    """
    Perform a fuzzy search for `search_term` in the 'ocr_text' field.

    Args:
        db: OCRDatabase instance
        search_term: Text to search for
        threshold: Approximate match threshold (0-1), closer to 1 is stricter

    Returns:
        List of (filename, ocr_text) tuples matching the search term approximately
    """
    # Get all records and perform fuzzy matching in Python
    all_records = db.get_all_records()

    results = []
    for _, filename, ocr_text in all_records:
        score = similarity_score(ocr_text, search_term)
        if score > threshold:
            results.append((score, filename, ocr_text))

    # Sort by similarity score (descending)
    results.sort(reverse=True, key=lambda x: x[0])

    # Return without score
    return [(filename, text) for _, filename, text in results]


def similarity_score(text1: str, text2: str) -> float:
    """
    Calculate approximate similarity score between two strings (0-1).
    This uses a simple ratio based on Levenshtein distance.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity ratio between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    ratio = Levenshtein.ratio(text1.lower(), text2.lower())
    return ratio


def print_result(filename: str, text: str):
    """
    Print search results in a readable format.

    Args:
        filename: Name of the file
        text: OCR text content
    """
    print(f"\n{'='*60}")
    print(f"{filename}\n")
    # Show snippet of matching text
    text_snippet = text[:200] + "..." if len(text) > 200 else text
    print(f"Text: {text_snippet}")
