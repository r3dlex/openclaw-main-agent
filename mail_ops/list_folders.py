import imaplib
import yaml
import os
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
    CONFIG = yaml.safe_load(f)

def get_pwd(acc):
    env_key = acc.get('password_env')
    if env_key:
        val = os.getenv(env_key)
        if val: return val
    return acc.get('password')

def check(acc):
    try:
        pwd = get_pwd(acc)
        if not pwd:
            print(f"[{acc['name']}] No password.")
            return
        print(f"[{acc['name']}] Connecting...")
        if acc['provider'] == 'davmail':
            mail = imaplib.IMAP4("localhost", 1143)
        else:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(acc['user'], pwd)
        print(f"[{acc['name']}] Logged in.")
        status, data = mail.list()
        print(f"[{acc['name']}] List status: {status}")
        if status == 'OK':
            print(f"[{acc['name']}] Folders found: {len(data)}")
            for f in data:
                try:
                    # IMAP list response format: (FLAGS PARENTHESIS...) "NAME" "PATH"
                    # Example: (\\HasNoChildren) "." "INBOX"
                    s = f.decode('utf-8', errors='ignore')
                    # Extract the part in quotes
                    if '"' in s:
                        parts = s.split('"')
                        if len(parts) >= 4:
                            name = parts[-2]
                            print(f"  - {name}")
                except Exception as pe:
                    print(f"  Parse error: {pe}")
        else:
            print(f"[{acc['name']}] No folders returned.")
        mail.logout()
    except Exception as e:
        print(f"[{acc['name']}] Error: {e}")

for acc in CONFIG['accounts']:
    if acc.get('active'):
        check(acc)
