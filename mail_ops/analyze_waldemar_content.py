import imaplib
import email
from email.header import decode_header
import os
import re
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"

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
    mail.select("Inbox")
    
    # Search by Sender to be safe
    status, messages = mail.search(None, 'FROM', "Trivium") # Or part of subject
    # If fails, try just ALL and filter
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    
    # Check last 500
    for eid in reversed(email_ids[-500:]):
        res, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
        msg = email.message_from_bytes(msg_data[0][1])
        subj = decode_str(msg["Subject"])
        
        if "Trivium" in subj and "booking" in subj:
            print(f"FOUND: {subj}")
            # Fetch body now
            res, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                         print(part.get_payload(decode=True).decode(errors="ignore"))
            else:
                print(msg.get_payload(decode=True).decode(errors="ignore"))
            break

    mail.logout()
except Exception as e:
    print(e)
