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
    
    # IDs to check: 111, 112, 113
    for eid in [b"111", b"112", b"113"]:
        res, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
            
        # Regex for PR link or ID
        # Looking for "pullrequest/XXXXX" or "PR XXXXX"
        ids = re.findall(r"pullrequest/(\d+)", body)
        if not ids:
            ids = re.findall(r"PR\s?(\d+)", body)
            
        print(f"Email {eid.decode()}: IDs Found: {list(set(ids))}")

    mail.logout()
except Exception as e:
    print(e)
