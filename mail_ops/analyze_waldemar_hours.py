import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import datetime
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"

TARGET_SENDER = "Waldemar" # Broad search first
KEYWORDS = ["hours", "stunden", "timesheet", "report", "zeit"]
SINCE_DATE = "01-Nov-2025"

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
    mail = imaplib.IMAP4("localhost", 1143)
    mail.login(USER, PASS)
    # Search for Trivium / Rixner
    print("Searching for Trivium / Thomas Rixner in multiple folders...")
    
    for folder in ["Inbox", "Vendors", "Projects", "Archive"]:
        mail.select(folder)
        # Search Trivium
        status, ids_trivium = mail.search(None, f'(SINCE "{SINCE_DATE}" OR SUBJECT "Trivium" FROM "Trivium")')
        status, ids_rixner = mail.search(None, f'(SINCE "{SINCE_DATE}" FROM "Rixner")')
        
        all_ids = set(ids_trivium[0].split() + ids_rixner[0].split())
        print(f"[{folder}] Found {len(all_ids)} potential emails.")
        
        for eid in all_ids:
            try:
                res, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
                msg = email.message_from_bytes(msg_data[0][1])
                subj = decode_str(msg["Subject"])
                date = msg.get("Date")
                print(f"[{date}] {subj}")
            except: pass

except Exception as e:
    print(f"Error: {e}")
