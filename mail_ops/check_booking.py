import sys
from datetime import datetime, timedelta
import argparse
from calendar_ops import get_service

def check_event(date_str, keyword, account="andre"):
    """
    date_str: YYYY-MM-DD
    keyword: partial title match
    """
    service = get_service(account)
    if not service:
        print("Error: Could not authenticate.")
        return False

    # Define range for that day (UTC)
    # Start of day
    start_dt = datetime.strptime(date_str, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=1)
    
    time_min = start_dt.isoformat() + "Z"
    time_max = end_dt.isoformat() + "Z"

    try:
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min, 
            timeMax=time_max,
            singleEvents=True, 
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        found = False
        for event in events:
            summary = event.get('summary', '')
            if keyword.lower() in summary.lower():
                print(f"FOUND: {summary} at {event['start'].get('dateTime', event['start'].get('date'))}")
                found = True
                break
        
        if not found:
            print("NOT_FOUND")
            return False
        return True

    except Exception as e:
        print(f"Error checking calendar: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument("keyword", help="Keyword to search in event title")
    args = parser.parse_args()
    
    check_event(args.date, args.keyword)
