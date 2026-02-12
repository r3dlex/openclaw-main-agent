import sys
import os
import imaplib
import smtplib
import email
from email.header import decode_header
from email.message import EmailMessage
import re
import requests
import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# Add Gatekeeper scripts to path
GATEKEEPER_SCRIPTS = "REDACTED_PATH/.openclaw/workspace/gatekeeper/scripts"
if GATEKEEPER_SCRIPTS not in sys.path:
    sys.path.append(GATEKEEPER_SCRIPTS)

try:
    from ado_client import get_data, get_headers, BASE_URL
except ImportError:
    print("Error: Could not import ado_client. Make sure Gatekeeper scripts are available.")
    sys.exit(1)

# Configuration
USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"
IMAP_HOST = "localhost"
IMAP_PORT = 1143
SMTP_HOST = "localhost"
SMTP_PORT = 1025
CC_EMAIL = "ashwini.bhujabalaiah@rib-software.com"
SENDER_NAME = "Georg Heißenberger"
FREEZE_GROUP = "RIB 4.0 Freeze Reviewers"

def get_pr_score(pr_id, pr_data=None):
    if not pr_data:
        pr_data = get_data(f"git/pullrequests/{pr_id}", {"api-version": "7.0"})
    
    if not pr_data or "pullRequestId" not in pr_data:
        return 0, "PR Not Found", None
    
    score = 10
    reason = []
    
    # Check Freeze Group
    reviewers = pr_data.get("reviewers", [])
    freeze_pending = False
    my_id = None
    
    for r in reviewers:
        if FREEZE_GROUP in r["displayName"] and r["vote"] == 0:
            freeze_pending = True
        if "Andre Burgstahler" in r["displayName"]:
            my_id = r["id"]

    if not freeze_pending:
        reason.append("Freeze Group not pending")
        # Don't zero score immediately, maybe we still want to vote if invited individually?
        # But instructions say "If Score > 8".
        # If freeze group is not pending, maybe we don't need to approve?
        # But if *I* am pending (Andre), I should probably vote.
        if my_id and any(r["id"] == my_id and r["vote"] == 0 for r in reviewers):
             pass # I need to vote
        else:
             score = 0 # No vote needed
             return 0, "No Vote Needed", my_id

    # Description check
    if not pr_data.get("description"):
        score -= 2
        reason.append("No Description")
    
    # Active comments check
    repo_id = pr_data['repository']['id']
    threads = get_data(f"git/repositories/{repo_id}/pullRequests/{pr_id}/threads", {"api-version": "7.0"})
    active_comments = sum(1 for t in threads.get("value", []) if t.get("status") in ["active", "pending"])
    
    if active_comments > 0:
        score -= 5
        reason.append(f"{active_comments} Active Threads")
        
    return score, ", ".join(reason) if reason else "OK", my_id

def vote_pr(repo_id, pr_id, reviewer_id):
    if not reviewer_id:
        print(f"  -> Cannot vote: reviewer ID for Andre not found in PR {pr_id}")
        return False
        
    url = f"{BASE_URL}/git/repositories/{repo_id}/pullRequests/{pr_id}/reviewers/{reviewer_id}?api-version=7.0"
    body = {"vote": 10} # 10 = Approved
    
    try:
        resp = requests.put(url, headers=get_headers(), json=body)
        resp.raise_for_status()
        print(f"  -> Voted Approved on PR {pr_id}")
        return True
    except Exception as e:
        print(f"  -> Failed to vote on PR {pr_id}: {e}")
        return False

def send_reply(to_addr, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = USER
        msg["To"] = to_addr
        msg["Cc"] = CC_EMAIL
        msg["Subject"] = subject
        msg.set_content(body)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.login(USER, PASS)
            recipients = [to_addr, CC_EMAIL]
            server.send_message(msg, to_addrs=recipients)
        print(f"  -> Emailed reply to {to_addr}")
        return True
    except Exception as e:
        print(f"  -> Failed to email {to_addr}: {e}")
        return False

def scan_ado_fallback():
    print("Fallback: Scanning ADO for active PRs...")
    # Fetch top 20 active PRs
    prs = get_data("git/pullrequests", {"searchCriteria.status": "active", "$top": 20, "api-version": "7.0"})
    found_prs = []
    
    if not prs or "value" not in prs:
        print("ADO Error or No PRs found.")
        return []
        
    for pr in prs.get("value", []):
        # Check if I am a reviewer and haven't voted, or Freeze Group hasn't voted
        # We can reuse get_pr_score logic partly
        score, reason, my_id = get_pr_score(pr["pullRequestId"], pr)
        if score > 0: # Relevant
             found_prs.append(str(pr["pullRequestId"]))
             
    # Limit to 4 as requested?
    return found_prs[:4]

def main():
    print("Connecting to Inbox...")
    try:
        mail = imaplib.IMAP4(IMAP_HOST, IMAP_PORT)
        mail.login(USER, PASS)
        mail.select("Inbox")
    except Exception as e:
        print(f"IMAP Connection Error: {e}")
        return

    # Search for emails from Georg
    print("Searching for FROM 'Georg'...")
    found_emails = []
    try:
        status, messages = mail.search(None, '(FROM "Georg")')
        email_ids = messages[0].split()
        
        now_utc = datetime.now(timezone.utc)
        print(f"Found {len(email_ids)} emails from 'Georg'. Checking last 10...")
        
        for i, eid in enumerate(reversed(email_ids[-10:])):
            try:
                res, msg_data = mail.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                date_header = msg["Date"]
                if not date_header: continue
                email_date = parsedate_to_datetime(date_header)
                if email_date.tzinfo is None:
                    email_date = email_date.replace(tzinfo=timezone.utc)
                else:
                    email_date = email_date.astimezone(timezone.utc)
                
                age = now_utc - email_date
                
                # Check Sender String
                from_header = msg["From"]
                decoded_header = decode_header(from_header)
                sender_str = ""
                for part, encoding in decoded_header:
                    if isinstance(part, bytes):
                        try:
                            sender_str += part.decode(encoding or "utf-8", errors="ignore")
                        except:
                            sender_str += part.decode("utf-8", errors="ignore")
                    else:
                        sender_str += part
                
                if age < timedelta(hours=1) and "Georg" in sender_str:
                    print(f"Found candidate email: {msg['Subject']} (Age: {age})")
                    found_emails.append((eid, msg))
            except:
                pass
                
    except Exception as e:
        print(f"IMAP Search Error: {e}")

    processed_prs = []
    unique_prs = []
    sender_addr = "Georg.Heissenberger@rib-software.com" # Default if fallback
    subject_reply = "RE: PR Approval"

    if found_emails:
        for eid, msg in found_emails:
            subject = msg["Subject"]
            subject_reply = f"RE: {subject}"
            sender = msg["From"]
            if "<" in sender:
                sender_addr = re.search(r"<(.+?)>", sender).group(1)
            
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
                
            matches = re.findall(r"(?:PR|Pull Request|!|#|pullrequest/|PR:)\s?(\d{4,})", subject + "\n" + body, re.IGNORECASE)
            unique_prs.extend(list(set(matches)))
    else:
        print("No emails found from Georg < 1h ago. Falling back to ADO check...")
        unique_prs = scan_ado_fallback()
        if unique_prs:
            print(f"Found pending PRs in ADO: {unique_prs}")
        else:
            print("No pending PRs found in ADO.")

    unique_prs = list(set(unique_prs))
    print(f"Processing PRs: {unique_prs}")
    
    approved_prs = []
    
    for pr_id in unique_prs:
        print(f"Evaluating PR {pr_id}...")
        score, reason, reviewer_id = get_pr_score(pr_id)
        
        pr_info = {
            "PR": pr_id,
            "Score": score,
            "Status": "Skipped",
            "Reason": reason
        }
        
        if score > 8:
            pr_data = get_data(f"git/pullrequests/{pr_id}", {"api-version": "7.0"})
            if pr_data and "repository" in pr_data:
                repo_id = pr_data["repository"]["id"]
                if vote_pr(repo_id, pr_id, reviewer_id):
                    pr_info["Status"] = "Approved (Voted)"
                else:
                    pr_info["Status"] = "Approved (Vote Failed)"
                approved_prs.append(pr_id)
            else:
                pr_info["Status"] = "Approved (Repo ID Not Found)"
                approved_prs.append(pr_id)
        else:
            pr_info["Status"] = "Rejected"
        
        processed_prs.append(pr_info)
        
    if approved_prs:
        if found_emails:
             reply_body = f"Hi,\n\nThe following PRs have been approved and voted on: {', '.join(approved_prs)}.\n\nBest,\nAndre"
             send_reply(sender_addr, subject_reply, reply_body)
        else:
             print(f"Would reply to {sender_addr} with: Approved {approved_prs}, but no email found to reply to.")
            
    print("\nFINAL REPORT TABLE")
    print("| PR | Score | Status | Reason |")
    print("|---|---|---|---|")
    for item in processed_prs:
        print(f"| {item['PR']} | {item['Score']} | {item['Status']} | {item['Reason']} |")

    mail.logout()

if __name__ == "__main__":
    main()
