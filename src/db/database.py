import sqlite3
import threading
from typing import Tuple, List


class OCRDatabase:
    """
    Thread-safe SQLite database handler for OCR data.
    Uses thread-local storage to ensure each thread has its own connection.
    """

    def __init__(self, db_file: str):
        """
        Initialize the database handler.

        Args:
            db_file: Path to the SQLite database file
        """
        self.db_file = db_file
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialize_schema()

    def _get_connection(self) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        """
        Get or create a thread-local database connection.

        Returns:
            Tuple of (connection, cursor)
        """
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self._local.cursor = self._local.conn.cursor()
        return self._local.conn, self._local.cursor

    def _initialize_schema(self):
        """Create the database schema if it doesn't exist."""
        conn, cursor = self._get_connection()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ocr_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE,
                ocr_text TEXT
            )
        """
        )
        conn.commit()

    def file_exists(self, filename: str) -> bool:
        """
        Check if a file already exists in the database.

        Args:
            filename: The filename to check

        Returns:
            True if the file exists, False otherwise
        """
        _, cursor = self._get_connection()
        cursor.execute("SELECT 1 FROM ocr_data WHERE filename = ?", (filename,))
        return cursor.fetchone() is not None

    def save_ocr_data(self, filename: str, text: str) -> bool:
        """
        Save OCR text to the database.

        Args:
            filename: The name of the file
            text: The OCR extracted text

        Returns:
            True if saved successfully, False if already exists
        """
        if self.file_exists(filename):
            return False

        conn, cursor = self._get_connection()
        with self._lock:
            try:
                cursor.execute(
                    "INSERT INTO ocr_data (filename, ocr_text) VALUES (?, ?)",
                    (filename, text),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Another thread inserted it first
                return False

    def search_exact(self, search_term: str) -> List[Tuple[str, str]]:
        """
        Perform an exact search for text in OCR data.

        Args:
            search_term: Text to search for

        Returns:
            List of (filename, ocr_text) tuples
        """
        _, cursor = self._get_connection()
        cursor.execute(
            "SELECT filename, ocr_text FROM ocr_data WHERE ocr_text LIKE ?",
            (f"%{search_term}%",),
        )
        return cursor.fetchall()

    def get_all_records(self) -> List[Tuple[int, str, str]]:
        """
        Get all records from the database.

        Returns:
            List of (id, filename, ocr_text) tuples
        """
        _, cursor = self._get_connection()
        cursor.execute("SELECT id, filename, ocr_text FROM ocr_data")
        return cursor.fetchall()

    def close(self):
        """Close the thread-local database connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
            self._local.cursor = None

    def close_all(self):
        """
        Close all connections. Use this when completely shutting down.
        Note: This only closes the current thread's connection.
        For full cleanup, call close() from each thread.
        """
        self.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()
