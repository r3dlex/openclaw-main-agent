import imaplib
import email
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Load Env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

# Config
IMAP_HOST = "localhost"
IMAP_PORT = 1143
USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"

# Draft Content
TO = "Florian.Haag@rib-software.com"
SUBJECT = "Re: Meeting Minutes: Sync on AI Efforts"
BODY = """Hi Florian,

Thanks for the minutes. I'd like to clarify the responsibilities moving forward:

1. **Framework** remains a TA responsibility.
2. **PLM** topics are still handled by Jignasa.
3. **Project Lead:** Tim is stepping in as the project lead and will be the primary contact person for the PMs.

We can follow up to solve any eventual questions if needed.

Best regards,

Andre"""

def create_draft():
    try:
        mail = imaplib.IMAP4(IMAP_HOST, IMAP_PORT)
        mail.login(USER, PASS)
        
        # Create Message
        msg = EmailMessage()
        msg["From"] = USER
        msg["To"] = TO
        msg["Subject"] = SUBJECT
        msg.set_content(BODY)
        
        # Append to Drafts
        # Note: Folder might be "Drafts" or "Entwürfe" depending on locale, 
        # but standardized to "Drafts" in previous steps? Let's try Drafts.
        
        print("Appending to Drafts...")
        # APPEND command: folder, flags, date, message
        mail.append("Drafts", "\\Draft", imaplib.Time2Internaldate(time.time()), str(msg).encode("utf-8"))
        
        print("Draft saved successfully.")
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")

import time
if __name__ == "__main__":
    create_draft()
