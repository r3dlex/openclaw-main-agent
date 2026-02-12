import imaplib
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"
SMTP_HOST = "localhost"
SMTP_PORT = 1025

CC = "ashwini.bhujabalaiah@rib-software.com"

# Email 1: Simon
TO_SIMON = "Simon.Welss@rib-software.com"
SUBJ_SIMON = "RE: FW: PR Approval" # Based on previous fetch
BODY_SIMON = """Hi Simon,

Approved. Please proceed with the merge for PR 39657.

Best,
Andre"""

# Email 2: Arthur
TO_ARTHUR = "Arthur.Henkel@rib-software.com"
SUBJ_ARTHUR = "RE: Approved PRs into release 26.1.0" # Based on previous fetch
BODY_ARTHUR = """Hi Arthur,

Approved. Please proceed with the merge for PR 39805 and PR 39856.

Best,
Andre"""

def send_approval(to, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = USER
        msg["To"] = to
        msg["Cc"] = CC
        msg["Subject"] = subject
        msg.set_content(body)
        
        # Connect to DavMail SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            # DavMail might not require starttls on 1025 locally, usually plain auth
            server.login(USER, PASS)
            recipients = [to, CC]
            server.send_message(msg, to_addrs=recipients)
            
        print(f"Sent approval to {to}")
    except Exception as e:
        print(f"Failed to send to {to}: {e}")

if __name__ == "__main__":
    send_approval(TO_SIMON, SUBJ_SIMON, BODY_SIMON)
    send_approval(TO_ARTHUR, SUBJ_ARTHUR, BODY_ARTHUR)
