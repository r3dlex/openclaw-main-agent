import yaml
import os
import sys
import threading
from omniclean import process_account

# Load Config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: config.yaml not found.")
    sys.exit(1)

def run_account(acc):
    print(f"🚀 STARTING THREAD: {acc['name']}")
    try:
        process_account(acc)
    except Exception as e:
        print(f"❌ ERROR in {acc['name']}: {e}")
    print(f"🏁 FINISHED THREAD: {acc['name']}")

def main():
    print("⚡ Starting PARALLEL Tidy Cycle...")
    threads = []
    
    for acc in CONFIG['accounts']:
        if acc.get('active', False):
            t = threading.Thread(target=run_account, args=(acc,))
            threads.append(t)
            t.start()
            
    for t in threads:
        t.join()
        
    print("✅ ALL ACCOUNTS PROCESSED.")

if __name__ == "__main__":
    main()
