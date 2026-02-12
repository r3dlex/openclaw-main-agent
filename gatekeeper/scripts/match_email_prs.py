from ado_client import get_data
import imaplib
import email
from email.header import decode_header
import os
import re
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"

def get_active_prs():
    data = get_data("git/pullrequests", {"searchCriteria.status": "active", "api-version": "7.0"})
    return {pr["pullRequestId"]: pr for pr in data.get("value", [])}

def check_emails_for_prs(active_prs):
    mail = imaplib.IMAP4("localhost", 1143)
    mail.login(USER, PASS)
    mail.select("Inbox")
    
    # Search recent emails about PRs
    status, messages = mail.search(None, "SUBJECT", "PR")
    email_ids = messages[0].split()
    
    found = []
    
    # Scan last 50 PR-related emails
    for eid in reversed(email_ids[-50:]):
        try:
            res, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = str(msg["Subject"])
            
            # Extract PR ID from subject (simple digits)
            # Usually "PR 12345" or "Pull Request 12345"
            ids = re.findall(r"PR\s?(\d+)|Pull Request\s?(\d+)", subject, re.IGNORECASE)
            
            for match in ids:
                pid = int(match[0] or match[1])
                if pid in active_prs:
                    pr = active_prs[pid]
                    found.append({
                        "id": pid,
                        "email_subject": subject,
                        "pr_title": pr["title"],
                        "author": pr["createdBy"]["displayName"],
                        "url": pr["url"]
                    })
        except:
            pass
            
    return found

if __name__ == "__main__":
    active = get_active_prs()
    matches = check_emails_for_prs(active)
    
    if matches:
        print("OPEN PRs with EMAILS:")
        seen = set()
        for m in matches:
            if m['id'] not in seen:
                print(f"- PR {m['id']}: {m['pr_title']} (Author: {m['author']})")
                print(f"  Email: {m['email_subject']}")
                seen.add(m['id'])
    else:
        print("No active PRs found that match recent emails.")
