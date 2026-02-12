import pytesseract
from PIL import Image
import subprocess
import sys
import os
import time

CLICLICK = "/opt/homebrew/bin/cliclick"
SCREENSHOT_PATH = "screen_temp.png"

def capture_screen():
    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)
    subprocess.run(["/usr/sbin/screencapture", "-x", SCREENSHOT_PATH])
    return Image.open(SCREENSHOT_PATH)

def find_text_on_screen(target_text):
    img = capture_screen()
    # Get verbose data including boxes
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    found = False
    for i, text in enumerate(data['text']):
        if target_text.lower() in text.lower():
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            
            center_x = x + w // 2
            center_y = y + h // 2
            
            print(f"Found '{target_text}' at ({center_x}, {center_y})")
            return center_x, center_y
            
    print(f"Text '{target_text}' not found on screen.")
    return None

def click_at(x, y):
    subprocess.run([CLICLICK, f"c:{x},{y}"])

def main():
    if len(sys.argv) < 2:
        print("Usage: iphone_driver_v2.py <text_to_click>")
        return

    target = sys.argv[1]
    coords = find_text_on_screen(target)
    
    if coords:
        click_at(coords[0], coords[1])
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
