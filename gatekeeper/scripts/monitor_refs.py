from ado_client import get_data
import json, os

CACHE_FILE = "REDACTED_PATH/.openclaw/workspace/gatekeeper/data/refs_cache.json"

def monitor():
    # Get Tags & Release Branches
    tags = get_data("git/refs", {"filter": "tags", "api-version": "7.0"})
    branches = get_data("git/refs", {"filter": "heads/release", "api-version": "7.0"})
    
    current_refs = {r["name"]: r["objectId"] for r in (tags.get("value", []) + branches.get("value", []))}
    
    new_refs = []
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            try:
                old_refs = json.load(f)
                new_refs = [name for name in current_refs if name not in old_refs]
            except:
                pass # Corrupt cache
    
    with open(CACHE_FILE, "w") as f:
        json.dump(current_refs, f)
        
    print(f"New Releases: {new_refs}" if new_refs else "No new releases.")

if __name__ == "__main__":
    monitor()
