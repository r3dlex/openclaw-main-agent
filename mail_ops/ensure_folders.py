import imaplib
import yaml
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: config.yaml not found.")
    sys.exit(1)

def get_password(acc):
    env_key = acc.get('password_env')
    if env_key and os.getenv(env_key):
        return os.getenv(env_key)
    return acc.get('password')

def connect(acc):
    password = get_password(acc)
    if not password: return None
    try:
        if acc['provider'] == 'davmail':
            mail = imaplib.IMAP4("localhost", 1143)
        else:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(acc['user'], password)
        return mail
    except Exception as e:
        print(f"[{acc['name']}] Login Failed: {e}")
        return None

# Standard English Folders
FOLDERS = [
    "Archive",
    "Finance",
    "Shopping",
    "Newsletters",
    "Social",
    "Gaming",
    "Travel",
    "Health",
    "Food/Delivery",
    "Events",
    "Logs",
    "Releases", # For work
    "Projects", # For work
    "HR", # For work
    "Sales", # For work
    "Vendors", # For work
]

def ensure_folders(acc):
    print(f"\n🔵 Setting up: {acc['name']}")
    mail = connect(acc)
    if not mail: return

    created = 0
    for folder in FOLDERS:
        # Only create 'Releases', 'Projects', etc if it's RIB (or all? Let's do all but warn)
        # Actually, let's just create standard ones for everyone, and extra ones for RIB.
        if acc['role'] == 'work':
            pass # We add specific work ones below
        else:
            if folder in ["Releases", "Projects", "HR", "Sales", "Vendors"]:
                continue

        try:
            typ, data = mail.create(folder)
            if typ == 'OK':
                print(f"  ✅ Created '{folder}'")
                created += 1
            # elif "exists" in str(data).lower():
            #     pass # Already exists
        except Exception as e:
            pass # Ignore errors (folder likely exists)

    # Work specific
    if acc['role'] == 'work':
        for folder in ["Releases", "Projects", "HR", "Sales", "Vendors"]:
            try:
                mail.create(folder)
            except: pass

    mail.logout()
    print(f"  Done. Created {created} folders.")

def main():
    for acc in CONFIG['accounts']:
        if acc.get('active', False):
            ensure_folders(acc)

if __name__ == "__main__":
    main()
