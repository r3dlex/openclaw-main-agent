from calendar_ops import create_event

ACCOUNT = "andre"
SUMMARY = "Termin Dominic U9 - Dr. Michael Herter"
LOCATION = "Schreiberstraße 35, 70199 Stuttgart"
ATTENDEES = ["anke.vera@hotmail.de"]

# Date: 24.03.2026
START = "2026-03-24T08:30:00"
END = "2026-03-24T09:30:00" # Assume 1h

print(f"Creating event: {SUMMARY} on {START}...")
# Note: create_event in calendar_ops.py currently supports all-day via 'date' keys.
# I need to check if calendar_ops.py supports dateTime.
# I will import get_service and do it manually to be safe, or check calendar_ops.py content.

from calendar_ops import get_service

service = get_service(ACCOUNT)
if service:
    event = {
        'summary': SUMMARY,
        'location': LOCATION,
        'start': {
            'dateTime': START,
            'timeZone': 'Europe/Berlin',
        },
        'end': {
            'dateTime': END,
            'timeZone': 'Europe/Berlin',
        },
        'attendees': [{'email': email} for email in ATTENDEES],
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating event: {e}")
