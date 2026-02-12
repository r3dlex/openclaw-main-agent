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

# PR 40005
TO_FLORIAN = "Florian.Haag@rib-software.com"
SUBJ_FLORIAN = "RE: PR 40005 - Assigned rights to RIB Unify service user"
BODY_FLORIAN = """Hi Florian,

Approved (Gatekeeper Score: 10/10). Please proceed with the merge.

Best,
Andre"""

# PR 39992
TO_JUILY = "Juily.Deshkar@rib-software.com"
SUBJ_JUILY = "RE: PR 39992 - DEV 62087 Total Hours Issue"
BODY_JUILY = """Hi Juily,

Approved (Gatekeeper Score: 10/10). Please proceed with the merge.

Best,
Andre"""

# PR 39978 / 39976
TO_HAUK = "Hauk.Zhi@rib-software.com"
SUBJ_HAUK = "RE: PR 39978 / 39976 - SonarQ SSL/TLS Fixes"
BODY_HAUK = """Hi Hauk,

Approved both PRs (Gatekeeper Score: 10/10). Please proceed with the merge.

Best,
Andre"""

def send(to, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = USER
        msg["To"] = to
        msg["Cc"] = CC
        msg["Subject"] = subject
        msg.set_content(body)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.login(USER, PASS)
            recipients = [to, CC]
            server.send_message(msg, to_addrs=recipients)
        print(f"Sent to {to}")
    except Exception as e:
        print(f"Failed to send to {to}: {e}")

if __name__ == "__main__":
    send(TO_FLORIAN, SUBJ_FLORIAN, BODY_FLORIAN)
    send(TO_JUILY, SUBJ_JUILY, BODY_JUILY)
    send(TO_HAUK, SUBJ_HAUK, BODY_HAUK)
