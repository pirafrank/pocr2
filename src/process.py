import sqlite3
import os
from PIL import Image
import pytesseract

# pip install pytesseract pillow
# Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\francesco\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'

#text = pytesseract.image_to_string(Image.open("C:\\Users\\francesco\\OneDrive - Leonardo S.p.a. - Div Cyber Security\\Screenshots\\Screenshot_1088.png"))
#print(text)


DB_FILE = 'ocr_screenshots.db'

# SQLite DB setup
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS ocr_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE,
    ocr_text TEXT
)
''')
conn.commit()


def file_exists_in_db(filename):
    cursor.execute('SELECT 1 FROM ocr_data WHERE filename = ?', (filename,))
    return cursor.fetchone() is not None

def save_to_db(filename, text):
    if not file_exists_in_db(filename):
        cursor.execute('INSERT INTO ocr_data (filename, ocr_text) VALUES (?, ?)', (filename, text))
        conn.commit()
        return True
    return False

def process_images(image_folder):
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            full_path = os.path.join(image_folder, filename)
            print(f"Processing {filename}...")

            ocr_text = pytesseract.image_to_string(Image.open((full_path)))
            if save_to_db(filename, ocr_text):
                print(f"OCR saved for {filename}")
            else:
                print(f"{filename} already exists in the database. Skipping.")

if __name__ == "__main__":
    SCREENSHOTS_DIR = "C:\\Users\\francesco\\OneDrive - Leonardo S.p.a. - Div Cyber Security\\Screenshots"
    process_images(SCREENSHOTS_DIR)
    conn.close()
