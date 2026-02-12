import imaplib
import yaml
import os
import sys
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

try:
    with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: config.yaml not found.")
    sys.exit(1)

def get_pwd(acc):
    env_key = acc.get('password_env')
    if env_key:
        val = os.getenv(env_key)
        if val: return val
    return acc.get('password')

def connect(acc):
    pwd = get_pwd(acc)
    if not pwd: return None
    try:
        if acc['provider'] == 'davmail':
            mail = imaplib.IMAP4("localhost", 1143)
        else:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(acc['user'], pwd)
        return mail
    except Exception as e:
        print(f"[{acc['name']}] Error: {e}")
        return None

# Mappings for Top-Level Folders
RENAMES = {
    # German
    "Unterlagen": "Reference",
    "Einkaufen": "Shopping",
    "Finanzen": "Finance",
    # Portuguese
    "Redes Sociais": "Social",
    "Compras": "Shopping",
    "Anúncios": "Newsletters",
    "An&APo-ncios": "Newsletters", # Encoded
    "UFSC": "Education",
}

def clean(mail, acc_name):
    status, data = mail.list()
    if status != 'OK': return 0

    folders = []
    for f in data:
        try:
            s = f.decode('utf-8', errors='ignore')
            if '"' in s:
                parts = s.split('"')
                if len(parts) >= 4:
                    folders.append(parts[-2])
        except: pass

    actions = 0
    print(f"\n🔵 {acc_name}: Found {len(folders)} folders.")

    for old in folders:
        # Check Rename
        for non_en, en in RENAMES.items():
            if old.lower() == non_en.lower():
                print(f"  Renaming '{old}' -> '{en}'")
                try:
                    mail.rename(old, en)
                    actions += 1
                    # Break inner loop
                    old = None
                    break
                except Exception as e:
                    print(f"    Failed: {e}")
        if old is None:
            continue

        # Check Consolidation (Simple Logic)
        # If folder ends in 's' and singular exists?
        # Skip for now to avoid complexity.
        # Example: "Social" and "Redes Sociais" -> "Redes Sociais" renamed to "Social".
        # If both exist, we might have dupes.
        # Let's just check for known dupes.

    return actions

def main():
    total = 0
    for acc in CONFIG['accounts']:
        if not acc.get('active'): continue
        m = connect(acc)
        if m:
            total += clean(m, acc['name'])
            m.logout()
    print(f"\n✅ Done. Actions: {total}")

if __name__ == "__main__":
    main()
