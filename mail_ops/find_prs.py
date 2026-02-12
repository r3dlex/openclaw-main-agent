import imaplib
import email
from email.header import decode_header
import os
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
    
    # Search All "PR" emails recent
    status, messages = mail.search(None, "SUBJECT", "PR")
    email_ids = messages[0].split()
    
    print(f"Found {len(email_ids)} PR emails total.")
    print("Recent 5:")
    for eid in email_ids[-5:]:
        res, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
        msg = email.message_from_bytes(msg_data[0][1])
        subj = decode_str(msg["Subject"])
        sender = decode_str(msg["From"])
        print(f"[{eid.decode()}] {subj} | From: {sender}")

except Exception as e:
    print(e)
