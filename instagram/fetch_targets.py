from instagrapi import Client
import json
import os
import sys

SESSION_FILE = "session.json"
TARGETS = ["stuttgart_blog", "stuttgartmitkind"]

def main():
    cl = Client()
    # Try load session for better access, but handle failure
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
        except:
            pass
            
    results = []
    
    for username in TARGETS:
        try:
            # We try to get user_id then medias
            # If API block (467) happens here, we might need to fallback or exit
            uid = cl.user_id_from_username(username)
            medias = cl.user_medias(uid, amount=3)
            
            for m in medias:
                # Basic check if already liked? 
                # API might know if logged in. If not logged in, we check in browser.
                # We return ALL top 3, let the browser check the heart icon status.
                
                results.append({
                    "username": username,
                    "url": f"https://www.instagram.com/p/{m.code}/",
                    "caption": m.caption_text[:200], # For context to generate comment
                    "pk": m.pk
                })
        except Exception as e:
            # If API fails, we return error so Agent knows to fallback to full-web navigation
            print(json.dumps({"error": str(e)}))
            return

    print(json.dumps(results))

if __name__ == "__main__":
    main()
