import imaplib
import email
from email.header import decode_header, Header
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"

def clean_header(header_value):
    if not header_value: return ""
    try:
        decoded_list = decode_header(header_value)
    except:
        return str(header_value)
    parts = []
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            parts.append(content.decode(encoding or "utf-8", errors="replace"))
        else:
            parts.append(str(content))
    return "".join(parts)

def audit():
    mail = imaplib.IMAP4("localhost", 1143)
    mail.login(USER, PASS)
    mail.select("Inbox")
    
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    total = len(email_ids)
    print(f"Total in Inbox: {total}")

    print("\n--- OLDEST 10 MESSAGES ---")
    for eid in email_ids[:10]:
        res, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
        msg = email.message_from_bytes(msg_data[0][1])
        subj = clean_header(msg.get("Subject"))
        sender = clean_header(msg.get("From"))
        date = msg.get("Date")
        print(f"[{eid.decode()}] {date} | {sender[:30]}... | {subj[:50]}...")

    print("\n--- RANDOM SAMPLE (Middle) ---")
    mid = total // 2
    for eid in email_ids[mid:mid+5]:
        res, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
        msg = email.message_from_bytes(msg_data[0][1])
        subj = clean_header(msg.get("Subject"))
        print(f"[{eid.decode()}] {subj[:50]}...")

    mail.logout()

if __name__ == "__main__":
    audit()
