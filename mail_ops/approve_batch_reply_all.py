import imaplib
import smtplib
import email
from email.message import EmailMessage
from email.utils import parseaddr
import os
import re
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"
SMTP_HOST = "localhost"
SMTP_PORT = 1025
ASHWINI = "ashwini.bhujabalaiah@rib-software.com"

# Target PRs to find in Inbox
TARGETS = ["40162", "40160", "40134"]

def get_all_recipients(msg):
    """Extracts To, Cc, and From to create a Reply-All list."""
    recipients = set()
    
    # Add From
    sender = msg.get("From")
    if sender: recipients.add(parseaddr(sender)[1].lower())
    
    # Add To
    if msg.get("To"):
        for addr in msg.get("To").split(','):
            recipients.add(parseaddr(addr)[1].lower())
            
    # Add Cc
    if msg.get("Cc"):
        for addr in msg.get("Cc").split(','):
            recipients.add(parseaddr(addr)[1].lower())
            
    # Ensure Ashwini
    recipients.add(ASHWINI.lower())
    
    # Remove Self
    if USER.lower() in recipients:
        recipients.remove(USER.lower())
        
    return list(recipients)

def find_and_approve():
    try:
        mail = imaplib.IMAP4("localhost", 1143)
        mail.login(USER, PASS)
        mail.select("Inbox")
        
        # Search recent PR emails
        status, messages = mail.search(None, "SUBJECT", "PR")
        email_ids = messages[0].split()
        
        approved_prs = set()
        
        # Scan last 50 emails to find the threads for our targets
        for eid in reversed(email_ids[-50:]):
            res, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = str(msg["Subject"])
            
            # Check if this email is about one of our targets
            matched_pr = None
            for pr_id in TARGETS:
                if pr_id in subject and pr_id not in approved_prs:
                    matched_pr = pr_id
                    break
            
            if matched_pr:
                print(f"Found thread for PR {matched_pr}: {subject[:50]}...")
                
                # Build Recipient List
                recipients = get_all_recipients(msg)
                
                # Draft Reply
                reply = EmailMessage()
                reply["From"] = USER
                reply["To"] = ", ".join(recipients) # SMTP handles list, but header needs string
                reply["Subject"] = f"RE: {subject.replace('Re: ', '').replace('RE: ', '')}"
                # In-Reply-To / References for threading?
                # DavMail/SMTP usually handles basics, but proper threading requires Message-ID.
                # For now, Subject-based threading is the fallback.
                
                body = "Approved."
                reply.set_content(body)
                
                # Send
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.login(USER, PASS)
                    server.send_message(reply)
                    print(f"✅ Sent Reply-All for PR {matched_pr} to {len(recipients)} people.")
                
                approved_prs.add(matched_pr)
                
                # Move to Projects
                # mail.copy(eid, "Projects") # Optional, user said tidy does this.
        
        if len(approved_prs) < len(TARGETS):
            print(f"⚠️ Could not find emails for all PRs. Approved: {approved_prs}. Missing: {set(TARGETS) - approved_prs}")
            # Fallback: Send direct email if thread not found?
            
        mail.logout()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_and_approve()
