import sys
# Add Gatekeeper scripts to path immediately
sys.path.append("REDACTED_PATH/.openclaw/workspace/gatekeeper/scripts")

import imaplib
import email
from email.header import decode_header
import smtplib
from email.message import EmailMessage
import os
import re
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from ado_client import get_data # From Gatekeeper

# Setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"
CC_EMAIL = "ashwini.bhujabalaiah@rib-software.com"

# Gatekeeper Logic
FREEZE_GROUP = "RIB 4.0 Freeze Reviewers"

def is_working_hours():
    now = datetime.now()
    # Mon=0, Sun=6. Working: 0-4 (Mon-Fri)
    if now.weekday() > 4: return False
    # Hours: 08:00 to 18:00
    if 8 <= now.hour < 18: return True
    return False

def evaluate_pr(pr_id):
    # Fetch PR from ADO
    pr = get_data(f"git/pullrequests/{pr_id}", {"api-version": "7.0"})
    if not pr or "pullRequestId" not in pr: return 0, "Not Found"
    
    score = 10
    
    # Check Reviewers (Is Freeze Pending?)
    reviewers = pr.get("reviewers", [])
    freeze_pending = False
    for r in reviewers:
        if FREEZE_GROUP in r["displayName"] and r["vote"] == 0:
            freeze_pending = True
            
    if not freeze_pending:
        return 0, "Freeze Group not pending"

    # Score Logic
    if not pr.get("description"): score -= 2
    
    threads = get_data(f"git/repositories/{pr['repository']['id']}/pullRequests/{pr_id}/threads", {"api-version": "7.0"})
    active_comments = sum(1 for t in threads.get("value", []) if t.get("status") in ["active", "pending"])
    if active_comments > 0: score -= 5

    return score, pr

def send_approval(to, subject_reply, pr_id):
    body = "Approved."
    try:
        msg = EmailMessage()
        msg["From"] = USER
        msg["To"] = to
        msg["Cc"] = CC_EMAIL
        msg["Subject"] = subject_reply
        msg.set_content(body)
        
        with smtplib.SMTP("localhost", 1025) as server:
            server.login(USER, PASS)
            recipients = [to, CC_EMAIL]
            server.send_message(msg, to_addrs=recipients)
        print(f"✅ Emailed approval for PR {pr_id} to {to}")
    except Exception as e:
        print(f"❌ Failed to email {to}: {e}")

def main():
    if "--ignore-hours" not in sys.argv and not is_working_hours():
        print("Outside working hours. Skipping PR approvals.")
        return

    print("Connecting to Inbox...")
    mail = imaplib.IMAP4("localhost", 1143)
    mail.login(USER, PASS)
    mail.select("Inbox")
    
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    
    print(f"Scanning {len(email_ids[-50:])} emails (Header+Body)...")
    
    processed_prs = set()
    
    for eid in reversed(email_ids[-50:]):
        try:
            res, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = str(msg["Subject"])
            sender = str(msg["From"])
            
            # Filter optimization
            if "PR" not in subject and "Pull Request" not in subject and "Approval" not in subject:
                continue

            # Get Body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try: body = part.get_payload(decode=True).decode(errors="ignore")
                        except: pass
                        break
            else:
                try: body = msg.get_payload(decode=True).decode(errors="ignore")
                except: pass

            # Extract ID (Subject OR Body)
            # Regex: PR 1234, !1234, pullrequest/1234, PR#1234, PR: 1234
            match = re.search(r"(?:PR|Pull Request|!|#|pullrequest/|PR:)\s?(\d{4,})", subject + " " + body, re.IGNORECASE)
            
            if match:
                pr_id = match.group(1)
                if pr_id in processed_prs: continue
                
                print(f"Found PR {pr_id} in email '{subject[:30]}...'")
                print(f"  SENDER: {sender}")
                print(f"  BODY: {body[:200]}...")
                score, pr_data = evaluate_pr(pr_id)
                
                if score > 8:
                    print(f"  -> Score {score}. Approving...")
                    sender_addr = re.search(r"<(.+?)>", sender).group(1) if "<" in sender else sender
                    
                    send_approval(sender_addr, f"RE: {subject}", pr_id)
                    
                    target_folder = "Projects" 
                    # Try to deduce release folder
                    v_match = re.search(r"(release|version|v)\s?(\d{2}\.\d)", subject + str(pr_data), re.IGNORECASE)
                    if v_match:
                        year = "20" + v_match.group(2).split('.')[0]
                        target_folder = f"Releases/{year}.{v_match.group(2).split('.')[1]}"
                        try: mail.create(target_folder)
                        except: pass
                    
                    mail.copy(eid, target_folder)
                    mail.store(eid, "+FLAGS", "\\Deleted")
                    print(f"  -> Moved email to {target_folder}")
                    
                else:
                    reason = pr_data if isinstance(pr_data, str) else "Low Score"
                    print(f"  -> Skipped (Score {score}: {reason})")
                
                processed_prs.add(pr_id)
        except Exception as e:
            print(f"Error processing {eid}: {e}")

    mail.expunge()
    mail.logout()

if __name__ == "__main__":
    main()
