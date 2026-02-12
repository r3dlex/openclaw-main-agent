import datetime
from calendar_ops import get_service

ACCOUNT = "andre"
SUMMARY = "Dinner: Möhringer Hexle (TheFork)"
LOCATION = "Möhringer Hexle" # I could look up address, but name is fine
START_TIME = "2026-02-14T17:30:00"
END_TIME = "2026-02-14T19:30:00"
ATTENDEES = ["dedefbs@gmail.com"]

service = get_service(ACCOUNT)
if service:
    event = {
        'summary': SUMMARY,
        'location': LOCATION,
        'start': {
            'dateTime': START_TIME,
            'timeZone': 'Europe/Berlin',
        },
        'end': {
            'dateTime': END_TIME,
            'timeZone': 'Europe/Berlin',
        },
        'attendees': [{'email': email} for email in ATTENDEES],
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating event: {e}")
else:
    print("Failed to get calendar service.")
