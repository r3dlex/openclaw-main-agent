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

TO = "Florian.Haag@rib-software.com"
SUBJ = "RE: PR 40059 - Prepared 25.3.1.P1 patch"
BODY = """Hi Florian,

Approved (Gatekeeper Score: 10/10). Please proceed with the merge.

Best,
Andre"""

try:
    msg = EmailMessage()
    msg["From"] = USER
    msg["To"] = TO
    msg["Cc"] = CC
    msg["Subject"] = SUBJ
    msg.set_content(BODY)
    
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.login(USER, PASS)
        recipients = [TO, CC]
        server.send_message(msg, to_addrs=recipients)
    print(f"Sent approval to {TO}")
except Exception as e:
    print(f"Failed: {e}")
