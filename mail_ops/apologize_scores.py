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
        "to": "Florian.Haag@rib-software.com",
        "subject": "RE: PR 40059 - Prepared 25.3.1.P1 patch", # Assuming this thread
        "body": "Hi Florian,\n\nSorry wegen dem 'Score', ich habe Augment Code mit etwas Automatisierung getestet 😅\n\nBest,\nAndre"
    },
    {
        "to": "Juily.Deshkar@rib-software.com",
        "subject": "RE: PR 39992 - DEV 62087 Total Hours Issue",
        "body": "Hi Juily,\n\nSorry about the score, I was just using Augment code with some automation 😅\n\nBest,\nAndre"
    },
    {
        "to": "Hauk.Zhi@rib-software.com",
        "subject": "RE: PR 39978 / 39976 - SonarQ SSL/TLS Fixes",
        "body": "Hi Hauk,\n\nSorry about the score, I was just using Augment code with some automation 😅\n\nBest,\nAndre"
    },
     {
        "to": "Justyna.Podhajska@rib-software.com", 
        "subject": "RE: PR 40055 / 40039 - DEV-61632 Create product fix",
        "body": "Hi Justyna,\n\nSorry about the score, I was just using Augment code with some automation 😅\n\nBest,\nAndre"
    },
    {
        "to": "Suela.Tahiri@rib-software.com",
        "subject": "RE: PR 40052 - DEV 62721 WIP Update fix",
        "body": "Hi Suela,\n\nSorry about the score, I was just using Augment code with some automation 😅\n\nBest,\nAndre"
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
                print(f"Sent apology to {task['to']}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_all()
