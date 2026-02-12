from instagrapi import Client
import sys
import os
import time
import random
import json

SESSION_FILE = "session.json"
CACHE_FILE = "processed_reposts.json"

def update_cache(media_pk):
    cache = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = set(json.load(f))
    cache.add(media_pk)
    with open(CACHE_FILE, "w") as f:
        json.dump(list(cache), f)

def load_session():
    cl = Client()
    if os.path.exists(SESSION_FILE):
        cl.load_settings(SESSION_FILE)
        return cl
    return None

def main():
    if len(sys.argv) < 3:
        print("Usage: act.py <mode> <id> [text]")
        return

    mode = sys.argv[1]
    target_id = sys.argv[2]
    text = sys.argv[3] if len(sys.argv) > 3 else ""

    cl = load_session()
    if not cl: return

    try:
        if mode == "like":
            cl.media_like(target_id)
            print(f"Liked media {target_id}")

        elif mode == "reply":
            # Direct Message Reply
            # target_id is thread_id (or user_id? direct_answer needs thread_id)
            cl.direct_answer(int(target_id), text)
            print(f"Replied to thread {target_id}")

        elif mode == "repost":
            # Repost to Story Logic (Placeholder for full image download)
            # Mark as processed so we don't spam it, even if we just "Logged" it for now
            # or if we successfully shared it (future).
            update_cache(target_id)
            print(f"Processed repost for {target_id} (Cache updated).")
            # TODO: Implement actual story_upload here

        # Human delay
        time.sleep(random.uniform(2, 5))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
