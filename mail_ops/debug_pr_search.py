import imaplib
import email
from email.header import decode_header
import re
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
    
    # Check Inbox AND Projects
    for folder in ["Inbox", "Projects"]:
        print(f"\nScanning {folder}...")
        mail.select(folder)
        # Search "PR"
        status, messages = mail.search(None, "SUBJECT", "PR")
        if not messages[0]:
            print("  No PR emails found.")
            continue
            
        email_ids = messages[0].split()
        print(f"  Found {len(email_ids)} PR emails. Checking last 5:")
        
        for eid in email_ids[-5:]:
            res, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_str(msg["Subject"])
            
            # Test Regex
            match = re.search(r"(PR|Pull Request)\s?(\d{4,})", subject, re.IGNORECASE)
            id_found = match.group(2) if match else "NO_MATCH"
            
            print(f"  [{eid.decode()}] {subject[:50]}... -> ID: {id_found}")

    mail.logout()
except Exception as e:
    print(f"Error: {e}")
