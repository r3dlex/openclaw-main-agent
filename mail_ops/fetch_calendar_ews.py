from exchangelib import Credentials, Configuration, Account, DELEGATE, EWSDateTime
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
# from exchangelib.util import set_stream_logging
import datetime
import os
import sys
import logging
from dotenv import load_dotenv

# Enable Debug Logging
# set_stream_logging(level=logging.DEBUG)

# Disable SSL verification for localhost DavMail (http)
BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

USER = "andre.burgstahler@rib-software.com"
PASSWORD = os.getenv("PASS_RIB_WORK", "REDACTED_PASSWORD")
EWS_URL = "http://localhost:1080/ews/exchange.asmx" # DavMail EWS endpoint

def fetch_today():
    print(f"Connecting to EWS at {EWS_URL}...")
    
    try:
        creds = Credentials(USER, PASSWORD)
        # DavMail doesn't need autodiscover
        config = Configuration(service_endpoint=EWS_URL, credentials=creds, auth_type='basic')
        account = Account(primary_smtp_address=USER, config=config, autodiscover=False, access_type=DELEGATE)
        
        now = datetime.datetime.now()
        # Use account timezone directly
        tz = account.default_timezone
        start = EWSDateTime(now.year, now.month, now.day, tzinfo=tz)
        end = start + datetime.timedelta(days=1)
        
        print(f"Fetching items for {start.date()}...")
        
        # Retry logic for ServerBusy
        for attempt in range(3):
            try:
                items = account.calendar.view(start=start, end=end)
                count = items.count()
                print(f"Found {count} items.\n")
                break
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                if attempt == 2: raise
        
        for item in items:
            start_str = item.start.strftime("%H:%M")
            end_str = item.end.strftime("%H:%M")
            subject = item.subject
            location = item.location or "Teams/Online"
            
            # Attendees
            attendees = []
            if item.required_attendees:
                attendees.extend([a.mailbox.name for a in item.required_attendees])
            if item.optional_attendees:
                attendees.extend([a.mailbox.name for a in item.optional_attendees])
                
            attendees_str = ", ".join(attendees) if attendees else "No other attendees"
            
            print(f"🕒 {start_str} - {end_str}: {subject}")
            print(f"   📍 {location}")
            print(f"   👥 {attendees_str}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_today()
