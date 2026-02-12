from calendar_ops import get_service
from datetime import datetime, timedelta

def check_event_exists(account_name, summary, start_time_str):
    service = get_service(account_name)
    if not service:
        print(f"Failed to get service for {account_name}")
        return False

    # Convert start_time_str to datetime object
    try:
        start_dt = datetime.fromisoformat(start_time_str)
    except ValueError:
        print(f"Invalid date format: {start_time_str}")
        return False
        
    # Search window: 2 hours before and after
    time_min = (start_dt - timedelta(hours=2)).isoformat() + 'Z'
    time_max = (start_dt + timedelta(hours=2)).isoformat() + 'Z'

    print(f"Checking for events between {time_min} and {time_max}...")
    
    events_result = service.events().list(calendarId='primary', timeMin=time_min, timeMax=time_max,
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    for event in events:
        event_summary = event.get('summary', '')
        # Check if summaries match closely (simple substring check for now)
        if summary.lower() in event_summary.lower() or event_summary.lower() in summary.lower():
            print(f"Found existing event: {event_summary} at {event['start'].get('dateTime', event['start'].get('date'))}")
            return True
            
    print("No matching event found.")
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        account_name = sys.argv[1]
        summary = sys.argv[2]
        start_time = sys.argv[3]
        exists = check_event_exists(account_name, summary, start_time)
        print(f"EXISTS: {exists}")
    else:
        print("Usage: python3 calendar_checker.py <account_name> <summary> <start_time_iso>")
