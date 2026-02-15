import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import yaml
import os
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from calendar_ops import get_service, create_event

# Load Config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
    CONFIG = yaml.safe_load(f)

# Providers Regex
PROVIDERS = {
    "TheFork": r"(TheFork|LaFourchette)",
    "Lufthansa": r"(Lufthansa|Eurowings|Swiss)",
    "DB": r"(Deutsche Bahn|DB Fernverkehr)",
    "Booking": r"(Booking\.com|Airbnb|Hotel)",
}

CONFIRMATION_KEYWORDS = ["confirmed", "bestätigung", "ticket", "buchung", "reservation", "reservierung"]

def get_password(acc):
    env_key = acc.get('password_env')
    return os.getenv(env_key) if env_key else acc.get('password')

def decode_str(s):
    if not s: return ""
    decoded_list = decode_header(s)
    parts = []
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            parts.append(content.decode(encoding or "utf-8", errors="ignore"))
        else:
            parts.append(str(content))
    return "".join(parts)

def check_calendar(service, start_time, title_keyword):
    # Check if event exists around start_time (+- 1 hour)
    # This is a basic check.
    try:
        # ISO format for GCal
        # Using simple check: list events for that day?
        # Let's assume if we find something with similar title in future, skip.
        # Ideally we need the exact date.
        pass 
    except:
        pass
    return False

def scan_bookings():
    print("🕵️‍♂️ Scanning for new bookings (Last 24h)...")
    
    # We scan ALL personal accounts
    for acc in CONFIG['accounts']:
        print(f"Scanning {acc['name']}...", flush=True)
        if acc.get('role') not in ['personal', 'work'] or not acc.get('active', False):
            continue

        password = get_password(acc)
        if not password: continue

        try:
            if acc['provider'] == 'gmail':
                mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            else:
                mail = imaplib.IMAP4("localhost", 1143)
            
            mail.login(acc['user'], password)
            
            folders_to_scan = ["Inbox", "Travel"]
            for folder in folders_to_scan:
                try:
                    mail.select(folder)
                except:
                    continue

                # Search recent emails (Last 2 days to be safe)
                since_date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
                status, messages = mail.search(None, f'(SINCE "{since_date}")')
                
                if not messages[0]: continue

                for e_id in messages[0].split():
                    res, msg_data = mail.fetch(e_id, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = decode_str(msg["Subject"])
                    sender = decode_str(msg.get("From"))
                    
                    # 1. Is it a booking confirmation?
                    is_conf = any(k in subject.lower() for k in CONFIRMATION_KEYWORDS)
                    is_provider = any(re.search(p, sender, re.IGNORECASE) for p in PROVIDERS.values())
                    
                    if is_conf and is_provider:
                        print(f"[{acc['name']}] Found Potential Booking: {subject}")
                        
                        # Extract body for LLM parsing
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if "attachment" not in content_disposition:
                                    try:
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            part_text = payload.decode(errors="ignore")
                                            if content_type == "text/plain":
                                                body += part_text + "\n"
                                            elif content_type == "text/html":
                                                # Simple HTML strip for log readability
                                                body += re.sub('<[^<]+?>', '', part_text) + "\n"
                                    except:
                                        pass
                        else:
                            try:
                                payload = msg.get_payload(decode=True)
                                if payload:
                                    body = payload.decode(errors="ignore")
                            except:
                                pass
                        
                        print(f"--- EMAIL BODY START ---\n{body[:2000]}\n--- EMAIL BODY END ---")

                        # TheFork Parser (Simple Example)
                        if "TheFork" in sender:
                            # Extract date/time from body... (Requires HTML parsing)
                            pass
                        
        except Exception as e:
            # print(f"Error scanning {acc['name']}: {e}")
            pass

if __name__ == "__main__":
    scan_bookings()
