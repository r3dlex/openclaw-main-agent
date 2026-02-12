import caldav
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Config
DAVMAIL_URL = "http://localhost:1080/users/andre.burgstahler@rib-software.com/calendar/"
USERNAME = "andre.burgstahler@rib-software.com"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
PASSWORD = os.getenv("PASS_RIB_WORK", "REDACTED_PASSWORD")

def fetch_week():
    print(f"Connecting to CalDAV...")
    try:
        client = caldav.DAVClient(url=DAVMAIL_URL, username=USERNAME, password=PASSWORD)
        principal = client.principal()
        calendars = principal.calendars()
        calendar = calendars[0]
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Range: Local Naive for comparison if needed, or UTC
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    
    print(f"Fetching events for {start.date()} - {end.date()}...")
    
    # Try Standard Search First
    try:
        events = calendar.date_search(start, end)
        print(f"Standard Search found {len(events)} events.")
        print_events(events)
        return
    except Exception as e:
        print(f"Standard search failed. Trying Raw Search...")

    # Fallback: List all objects and filter
    try:
        print("Listing all objects...")
        events = calendar.events() # Fetches URLs/metadata
        print(f"Found {len(events)} total objects. Filtering...")
        
        valid_events = []
        count = 0
        
        for event in events:
            try:
                # Load component data
                vevent = event.instance.components[0]
                dtstart = vevent.dtstart.value
                
                # Normalize dtstart to Naive datetime for comparison
                check_dt = None
                
                if isinstance(dtstart, datetime):
                    # Convert to naive local time (remove tzinfo if present)
                    # This assumes 'start' and 'end' are local naive
                    if dtstart.tzinfo:
                         # Convert to local time approximately? 
                         # Simpler: just strip tzinfo for rough check
                         check_dt = dtstart.replace(tzinfo=None)
                    else:
                        check_dt = dtstart
                else:
                    # It's a date object (All day)
                    check_dt = datetime.combine(dtstart, datetime.min.time())
                
                # Compare
                if check_dt and start <= check_dt <= end:
                    valid_events.append(event)
                
                count += 1
            except Exception as inner_e:
                continue
                
        print(f"Filtered to {len(valid_events)} relevant events.")
        print_events(valid_events)
        
    except Exception as e:
        print(f"Fallback failed: {e}")

def print_events(events):
    event_list = []
    for event in events:
        try:
            vevent = event.instance.components[0]
            summary = str(vevent.summary.value)
            dtstart = vevent.dtstart.value
            
            if isinstance(dtstart, datetime):
                dt_str = dtstart.strftime("%a %d %H:%M")
                sort_key = dtstart.replace(tzinfo=None)
            else:
                dt_str = str(dtstart)
                sort_key = datetime.combine(dtstart, datetime.min.time())

            event_list.append((sort_key, dt_str, summary))
        except:
            pass

    event_list.sort(key=lambda x: x[0])
    for _, dt_str, title in event_list:
        print(f"[{dt_str}] {title}")

if __name__ == "__main__":
    fetch_week()
