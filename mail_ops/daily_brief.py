import imaplib
import email
from email.header import decode_header
import yaml
import os
import sys
from dotenv import load_dotenv

# Setup Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

# Load Config
try:
    with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: config.yaml not found.")
    sys.exit(1)

def get_password(acc):
    env_key = acc.get('password_env')
    if env_key:
        return os.getenv(env_key)
    return acc.get('password')

def clean_subject(subject_bytes):
    if not subject_bytes: return "(No Subject)"
    decoded_list = decode_header(subject_bytes)
    subject_parts = []
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            subject_parts.append(content.decode(encoding or "utf-8", errors="ignore"))
        else:
            subject_parts.append(str(content))
    return "".join(subject_parts)

def daily_brief():
    print(f"☀️ *Daily OmniMail Briefing*")
    
    # Iterate all active accounts
    for acc in CONFIG['accounts']:
        if not acc.get('active', False): continue
        
        try:
            # Connection Logic
            password = get_password(acc)
            if not password:
                print(f"[{acc['name']}] Skipped (No Password)")
                continue

            if acc['provider'] == 'davmail':
                host = acc.get('host', CONFIG['defaults']['davmail_host'])
                port = acc.get('port', CONFIG['defaults']['davmail_port'])
                mail = imaplib.IMAP4(host, port)
            elif acc['provider'] == 'gmail':
                host = acc.get('host', CONFIG['defaults']['gmail_host'])
                port = acc.get('port', CONFIG['defaults']['gmail_port'])
                mail = imaplib.IMAP4_SSL(host, port)
            else:
                continue

            mail.login(acc['user'], password)
            mail.select("Inbox")
            
            status, messages = mail.search(None, "UNSEEN")
            email_ids = messages[0].split()
            total_unread = len(email_ids)
            
            print(f"\n📧 **{acc['name']}**: {total_unread} unread")
            
            if total_unread > 0:
                # Get last 3 unread
                for e_id in email_ids[-3:]:
                    res, msg_data = mail.fetch(e_id, "(RFC822.HEADER)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = clean_subject(msg["Subject"])
                            sender = msg.get("From")
                            print(f"  - {sender[:40]}...: _{subject[:60]}..._")

            mail.logout()
        except Exception as e:
            print(f"[{acc['name']}] Error: {e}")

if __name__ == "__main__":
    daily_brief()
