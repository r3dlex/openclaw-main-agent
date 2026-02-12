from instagrapi import Client
import json
import os
import time
from datetime import datetime, timedelta, timezone

SESSION_FILE = "session.json"
CACHE_FILE = "processed_reposts.json"
TARGET_ACCOUNTS = ["stuttgart_blog", "stuttgartmitkind"]

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(cache), f)

def main():
    cl = Client()
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
        except:
            print(json.dumps({"error": "Invalid session"}))
            return
    else:
        print(json.dumps({"error": "No session"}))
        return

    output = {"dms": [], "posts_to_like": [], "repost_candidates": []}
    reposted_cache = load_cache()
    
    # Time window (Last 4 hours to cover 3h cron interval + buffer)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=4)

    # 1. DMs (Existing logic)
    threads = cl.direct_threads(amount=10, selected_filter="unread")
    for t in threads:
        last_msg = t.messages[0] if t.messages else None
        if last_msg and last_msg.user_id != cl.user_id:
            output["dms"].append({
                "thread_id": t.pk,
                "username": t.users[0].username,
                "last_text": last_msg.text,
                "context": [m.text for m in t.messages[:3]]
            })

    # 2. Check Targets
    for target in TARGET_ACCOUNTS:
        try:
            uid = cl.user_id_from_username(target)
            medias = cl.user_medias(uid, amount=5) # Check last 5 just in case
            
            for m in medias:
                # Like Logic (Simple)
                if not m.has_liked:
                    output["posts_to_like"].append(m.pk)

                # Repost Logic (Strict Time + Cache)
                # m.taken_at is usually timezone aware
                if m.taken_at > cutoff and m.pk not in reposted_cache:
                    output["repost_candidates"].append({
                        "pk": m.pk,
                        "code": m.code,
                        "user": target,
                        "caption": m.caption_text[:100],
                        "url": f"https://instagram.com/p/{m.code}"
                    })
                    # We optimistically mark as seen/candidate to avoid double reporting
                    # In a real system, we'd mark AFTER action, but here we let the Agent decide.
                    # Actually, let's NOT mark it here. The Agent (Cron) should trigger a "mark_reposted" action or we rely on the agent's memory?
                    # Better: The Agent will run 'act_instagram.py repost ...' which should update the cache.
                    # I'll add a 'mark_reposted' mode to act.py or just update cache here if I assume the Agent acts?
                    # Let's assume the Agent acts. I'll NOT save to cache here to allow retries if Agent fails, 
                    # BUT this risks double posting if the Agent runs twice.
                    # Safety: I will expect `act_instagram.py` to handle the cache update.
        except:
            pass

    print(json.dumps(output, default=str))

if __name__ == "__main__":
    main()
