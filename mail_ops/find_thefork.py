import imaplib
import email
from email.header import decode_header
import yaml
import os
import re
from datetime import datetime
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
    CONFIG = yaml.safe_load(f)

# Find Dede's account
DEDE_ACC = next(a for a in CONFIG['accounts'] if a['id'] == 'dedefbs')
PASS = os.getenv(DEDE_ACC['password_env'])

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def decode_str(s):
    if not s: return ""
    decoded_list = decode_header(s)
    parts = []
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            parts.append(content.decode(encoding or "utf-8", errors="ignore"))
        else:
            parts.append(str(content))
    return "".join(parts)

try:
    print(f"Connecting to {DEDE_ACC['user']}...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(DEDE_ACC['user'], PASS)
    mail.select("Inbox")

    # Search for TheFork
    status, messages = mail.search(None, '(FROM "TheFork" SUBJECT "booking")')
    if not messages[0]:
         # Try broader search
         status, messages = mail.search(None, '(FROM "TheFork")')
    
    email_ids = messages[0].split()
    
    if email_ids:
        latest_id = email_ids[-1]
        res, msg_data = mail.fetch(latest_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        subject = decode_str(msg["Subject"])
        print(f"Found: {subject}")
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
            
        print("--- BODY SNIPPET ---")
        print(body[:1000]) # Print first 1000 chars to help Agent parse
    else:
        print("No TheFork emails found.")

    mail.logout()
except Exception as e:
    print(f"Error: {e}")
