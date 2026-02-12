import argparse
import datetime
import json
import os
import sys
import dateutil.parser as dparser
from calendar_ops import get_service, create_timed_event

def check_event_exists(service, start_dt, end_dt, summary):
    """
    Check if an event exists in the given range with a similar summary.
    start_dt, end_dt are datetime objects.
    """
    try:
        # Check from start of day to end of day
        day_start = start_dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        day_end = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        
        events_result = service.events().list(calendarId='primary', timeMin=day_start + 'Z', timeMax=day_end + 'Z', singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        for event in events:
            existing_summary = event.get('summary', '')
            if summary.lower() in existing_summary.lower() or existing_summary.lower() in summary.lower():
                print(f"Event already exists: {existing_summary} ({event.get('htmlLink')})")
                return True
        return False
    except Exception as e:
        print(f"Error checking calendar: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Create calendar event")
    parser.add_argument("--account", default="andre", help="Account name (e.g. andre)")
    parser.add_argument("--summary", required=True, help="Event summary")
    parser.add_argument("--start", required=True, help="Start time (ISO 8601)")
    parser.add_argument("--end", required=True, help="End time (ISO 8601)")
    parser.add_argument("--location", help="Event location")
    parser.add_argument("--description", help="Event description")
    
    args = parser.parse_args()
    
    try:
        start_dt = dparser.parse(args.start)
        end_dt = dparser.parse(args.end)
    except Exception as e:
        print(f"Error parsing date: {e}")
        sys.exit(1)
    
    service = get_service(args.account)
    if not service:
        print("Failed to get calendar service.")
        sys.exit(1)
        
    if check_event_exists(service, start_dt, end_dt, args.summary):
        print("Skipping creation.")
    else:
        print(f"Creating event: {args.summary} at {args.start}")
        create_timed_event(args.account, args.summary, args.start, args.end, args.location, args.description)

if __name__ == "__main__":
    main()
