import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import sys
import os

def ocr_file(path):
    if not os.path.exists(path):
        print(f"Error: File not found {path}")
        return

    print(f"Processing {path}...")
    try:
        # Convert PDF to images
        if path.lower().endswith('.pdf'):
            images = convert_from_path(path)
        else:
            # Assume image
            images = [Image.open(path)]

        full_text = ""
        for i, img in enumerate(images):
            print(f"OCR Page {i+1}...")
            text = pytesseract.image_to_string(img, lang='deu+eng') # German+English
            full_text += f"\n--- Page {i+1} ---\n{text}\n"
        
        print("\n=== EXTRACTED TEXT ===\n")
        print(full_text)
        
    except Exception as e:
        print(f"OCR Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ocr_pdf.py <path>")
    else:
        ocr_file(sys.argv[1])
