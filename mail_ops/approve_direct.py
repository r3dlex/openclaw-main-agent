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

TASKS = [
    {
        "to": "Rutuja.Pawar@rib-software.com",
        "subject": "RE: PR 40162 - Tooltip UX Fix",
        "body": "Hi Rutuja,\n\nApproved. Please proceed.\n\nBest,\nAndre"
    },
    {
        "to": "Vishal.Chatterjee@rib-software.com",
        "subject": "RE: PR 40160 - BPD_CONTACT_FK Bugfix",
        "body": "Hi Vishal,\n\nApproved. Please proceed.\n\nBest,\nAndre"
    },
    {
        "to": "Suela.Tahiri@rib-software.com",
        "subject": "RE: PR 40134 - DEV 62721 WIP Update",
        "body": "Hi Suela,\n\nApproved. Please proceed.\n\nBest,\nAndre"
    }
]

def send_direct():
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.login(USER, PASS)
            for task in TASKS:
                msg = EmailMessage()
                msg["From"] = USER
                msg["To"] = task["to"]
                msg["Cc"] = CC
                msg["Subject"] = task["subject"]
                msg.set_content(task["body"])
                
                recipients = [task["to"], CC]
                server.send_message(msg, to_addrs=recipients)
                print(f"Sent approval to {task['to']}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_direct()
