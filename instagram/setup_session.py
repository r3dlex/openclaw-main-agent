from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired
import getpass
import os

SESSION_FILE = "session.json"

def main():
    cl = Client()
    
    if os.path.exists(SESSION_FILE):
        print(f"Loading existing session from {SESSION_FILE}...")
        try:
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()
            print("Session is valid!")
            return
        except Exception as e:
            print(f"Session invalid: {e}")
    
    username = input("Instagram Username: ")
    password = getpass.getpass("Instagram Password: ")
    
    try:
        print("Attempting login...")
        cl.login(username, password)
    except TwoFactorRequired:
        print("2FA Required!")
        code = input("Enter 2FA Code (SMS/App): ")
        cl.login(username, password, verification_code=code)
    except ChallengeRequired:
        print("Challenge Required!")
        print("1. Check your phone app for 'This Was Me' notification.")
        print("2. If no notification, we might need SMS verification.")
        
        # Try to resolve challenge via SMS if API supports it interactive
        # Usually re-login after 'This Was Me' works.
        api_path = cl.last_json.get("challenge", {}).get("api_path")
        if api_path:
             print(f"Challenge API Path: {api_path}")
             choice = input("Did you approve on phone? (y/n) or type 'sms' to request code: ")
             if choice.lower() == 'y':
                 cl.login(username, password)
             elif choice.lower() == 'sms':
                 try:
                     cl.challenge_resolve(cl.last_json) # Simplified logic
                     code = input("Enter SMS Code: ")
                     cl.challenge_resolve(cl.last_json, code)
                 except Exception as e:
                     print(f"SMS flow failed: {e}")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    print("Login successful!")
    print(f"Saving session to {SESSION_FILE}...")
    cl.dump_settings(SESSION_FILE)
    print("Done! You can now run bot.py.")

if __name__ == "__main__":
    main()
