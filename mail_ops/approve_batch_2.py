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
        "to": "Justyna.Podhajska@rib-software.com",
        "subject": "RE: PR 40055 / 40039 - DEV-61632 Create product fix",
        "body": "Hi Justyna,\n\nApproved PR 40055 and 40039 (Gatekeeper Score: 9/10). Please proceed with the merge.\n\nBest,\nAndre"
    },
    {
        "to": "Suela.Tahiri@rib-software.com",
        "subject": "RE: PR 40052 - DEV 62721 WIP Update fix",
        "body": "Hi Suela,\n\nApproved PR 40052 (Gatekeeper Score: 9/10). Please proceed with the merge.\n\nBest,\nAndre"
    },
    {
        "to": "Florian.Haag@rib-software.com",
        "subject": "RE: PR 40005 - RIB Unify Rights",
        "body": "Hi Florian,\n\nApproved PR 40005 (Gatekeeper Score: 9/10). Please proceed with the merge.\n\nBest,\nAndre"
    }
]

def send_all():
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
    send_all()
