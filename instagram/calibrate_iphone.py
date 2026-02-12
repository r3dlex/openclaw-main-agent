import time
import subprocess
import json
import sys

# Requirements: cliclick
CLICLICK = "/opt/homebrew/bin/cliclick"

COORDS_FILE = "iphone_coords.json"
TARGETS = [
    "Instagram Icon (Home Screen)",
    "Home Tab (Bottom Left)",
    "Search Tab (Bottom)",
    "Reels Tab (Bottom)",
    "Profile Tab (Bottom Right)",
    "DM Icon (Top Right)",
    "First Story (Top Left Circle)",
    "First Post Like Button (Heart)",
    "First Post Comment Button",
    "Search Bar (Top)"
]

def get_mouse_pos():
    # Use cliclick to get position: "p:123,456"
    out = subprocess.check_output([CLICLICK, "p"]).decode().strip()
    return out

def main():
    print("📱 iPhone Mirroring Calibration")
    print("--------------------------------")
    print("I will ask you to hover your mouse over specific elements on the iPhone Mirroring window.")
    print("You will have 5 seconds per element. Do not click, just hover.")
    
    coords = {}
    
    try:
        for target in TARGETS:
            print(f"\n👉 Point to: {target}")
            for i in range(5, 0, -1):
                sys.stdout.write(f"\rRecording in {i}...")
                sys.stdout.flush()
                time.sleep(1)
            
            pos = get_mouse_pos()
            print(f"\n✅ Captured: {pos}")
            coords[target] = pos
            
    except KeyboardInterrupt:
        print("\nCalibration cancelled.")
        return

    print("\nSaving coordinates...")
    with open(COORDS_FILE, "w") as f:
        json.dump(coords, f, indent=2)
    print(f"Saved to {COORDS_FILE}")

if __name__ == "__main__":
    main()
