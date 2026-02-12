import datetime
from calendar_ops import get_service, create_timed_event

def check_and_create():
    try:
        # Service for 'andre' (token_andre.json)
        # Note: get_service uses Credentials.from_authorized_user_file with SCOPES = ['https://www.googleapis.com/auth/calendar']
        # This matches what create_event uses, so it should succeed where list_events.py failed (due to scope mismatch).
        service = get_service('andre') 
        if not service:
            print("Service failed")
            return

        # Time range: 2026-02-14
        # We need RFC3339 format. Z is UTC.
        # But let's use the same logic as list_events to be safe, or just hardcode ISO.
        time_min = "2026-02-14T00:00:00Z"
        time_max = "2026-02-14T23:59:59Z"

        print("Checking events for 2026-02-14...")
        events_result = service.events().list(
            calendarId='primary', timeMin=time_min, timeMax=time_max,
            singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        found = False
        for event in events:
            summary = event.get('summary', '')
            print(f"Found: {summary}")
            if "Möhringer Hexle" in summary or "TheFork" in summary:
                found = True
                print("Event already exists.")
                break

        if not found:
            print("Creating event...")
            # calendar_ops.create_timed_event takes start_dt, end_dt.
            # It sets timeZone='Europe/Berlin'. 
            # So we pass "2026-02-14T17:30:00" (local time).
            create_timed_event(
                'andre',
                'Dinner at Möhringer Hexle',
                '2026-02-14T17:30:00', 
                '2026-02-14T19:30:00',
                location='Vaihinger Straße 7, 70567 Stuttgart',
                description='Reservierung für 2 Personen via TheFork.'
            )
        else:
            print("Skipping creation.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_and_create()
