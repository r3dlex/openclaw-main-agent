import json
import os
import sys
import time
import subprocess
import random

# Config
COORDS_FILE = "iphone_coords.json"
CLICLICK = "/opt/homebrew/bin/cliclick"
SCREENSHOT_PATH = "REDACTED_PATH/.openclaw/workspace/instagram/screen_snapshot.png"

def load_coords():
    if not os.path.exists(COORDS_FILE):
        # Fallback if no calibration: Assume some defaults or fail?
        # Let's just fail for safety.
        print(f"Error: {COORDS_FILE} not found. Run calibrate_iphone.py first.")
        sys.exit(1)
    with open(COORDS_FILE, "r") as f:
        return json.load(f)

def snapshot():
    # Capture screen (silent)
    subprocess.run(["screencapture", "-x", SCREENSHOT_PATH])
    print(f"📸 Screen captured to {SCREENSHOT_PATH}")
    # Ideally we would crop to the window, but we don't know window bounds without AppleScript.
    # We rely on user keeping window visible.

def click(coords_str):
    xy = coords_str.replace("p:", "").strip()
    subprocess.run([CLICLICK, f"c:{xy}"])

def scroll_down(start_xy, end_xy):
    s = start_xy.replace("p:", "").strip()
    e = end_xy.replace("p:", "").strip()
    cmd = f"dd:{s} w:50 dm:{e} w:50 du:{e}"
    subprocess.run([CLICLICK, cmd])

def main():
    if len(sys.argv) < 2:
        print("Usage: iphone_driver.py <action>")
        return

    action = sys.argv[1]
    coords = load_coords()
    
    # Pre-action snapshot
    snapshot()

    if action == "like_feed":
        print("Liking feed posts...")
        # 1. Click Home
        click(coords.get("Home Tab (Bottom Left)"))
        time.sleep(2)
        
        # Loop
        for i in range(3):
            # Click Like
            click(coords.get("First Post Like Button (Heart)"))
            print(f"Liked post {i+1}")
            time.sleep(1)
            
            # Scroll logic
            start = coords.get("Home Tab (Bottom Left)")
            hx, hy = map(int, start.replace("p:", "").split(","))
            dx, dy = map(int, coords.get("DM Icon (Top Right)").replace("p:", "").split(","))
            
            # Swipe Up
            sx, sy = hx + 50, hy - 100
            ex, ey = hx + 50, dy + 100
            
            scroll_down(f"{sx},{sy}", f"{ex},{ey}")
            print("Scrolled.")
            time.sleep(random.uniform(2, 4))
            
            # Snapshot after scroll to verify?
            snapshot()

    elif action == "check_dms":
        print("Checking DMs...")
        click(coords.get("DM Icon (Top Right)"))
        time.sleep(2)
        snapshot() # Capture inbox state

    elif action == "open":
        click(coords.get("Instagram Icon (Home Screen)"))

if __name__ == "__main__":
    main()
