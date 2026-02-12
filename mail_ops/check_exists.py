import datetime
from calendar_ops import get_service

def check():
    # Attempt to get service for "andre" (based on token_andre.json existence implies this name)
    service = get_service("andre") 
    if not service:
        print("No service")
        return

    # 2026-02-14
    start = "2026-02-14T00:00:00+01:00"
    end = "2026-02-15T00:00:00+01:00"
    
    events_result = service.events().list(
        calendarId='primary', timeMin=start, timeMax=end,
        singleEvents=True, orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    for event in events:
        if "Möhringer Hexle" in event.get('summary', ''):
            print("FOUND_EVENT")
            return
    print("NO_EVENT")

if __name__ == "__main__":
    check()