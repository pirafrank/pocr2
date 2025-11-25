import sqlite3
import Levenshtein

def fuzzy_search(db_path, search_term, threshold=0.6):
    """
    Perform a fuzzy search for `search_term` in the 'ocr_text' field.
    Args:
        db_path (str): Path to SQLite DB file.
        search_term (str): Text to search for.
        threshold (float): Approximate match threshold (0-1), closer to 1 is stricter.

    Returns:
        List of filenames matching the search term approximately.
    """
    conn = sqlite3.connect(db_path)
    conn.create_function("SIMILARITY", 2, similarity_score)
    cursor = conn.cursor()

    query = """
    SELECT filename, ocr_text FROM ocr_data
    WHERE SIMILARITY(ocr_text, ?) > ?
    ORDER BY SIMILARITY(ocr_text, ?) DESC
    """

    cursor.execute(query, (search_term, threshold, search_term))
    results = cursor.fetchall()

    conn.close()
    return results

def similarity_score(text1, text2):
    """
    Calculate approximate similarity score between two strings (0-1).
    This uses a simple ratio based on Levenshtein distance.
    """
    if not text1 or not text2:
        return 0.0
    ratio = Levenshtein.ratio(text1.lower(), text2.lower())
    return ratio

if __name__ == "__main__":
    db_file = 'ocr_screenshots.db'
    term_to_search = input("Enter text to search: ")
    matches = fuzzy_search(db_file, term_to_search, threshold=0.5)

    if matches:
        print(f"Found {len(matches)} matches:")
        for filename, text in matches:
            print(f"- {filename}")
    else:
        print("No matches found.")
