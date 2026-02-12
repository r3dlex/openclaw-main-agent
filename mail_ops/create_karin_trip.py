from calendar_ops import get_service

ACCOUNT = "andre"

EVENTS = [
    {
        "summary": "Reise Karin und Karl-Georg (Hinflug)",
        "location": "Flughafen Stuttgart",
        "description": "Hinflug 11:50. Am Flughafen sein um 09:50.",
        "start": {"dateTime": "2026-02-09T09:50:00", "timeZone": "Europe/Berlin"},
        "end": {"dateTime": "2026-02-09T12:00:00", "timeZone": "Europe/Berlin"}
    },
    {
        "summary": "Abholen: Reise Karin und Karl-Georg (Rückflug)",
        "location": "Flughafen Stuttgart",
        "description": "Geplante Landung: 23:30. Abholen!",
        "start": {"dateTime": "2026-03-30T23:15:00", "timeZone": "Europe/Berlin"},
        "end": {"dateTime": "2026-03-31T00:15:00", "timeZone": "Europe/Berlin"}
    }
]

service = get_service(ACCOUNT)
if service:
    for evt in EVENTS:
        try:
            event = service.events().insert(calendarId='primary', body=evt).execute()
            print(f"Created: {evt['summary']} - {event.get('htmlLink')}")
        except Exception as e:
            print(f"Error creating {evt['summary']}: {e}")
