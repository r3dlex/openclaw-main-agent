import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import datetime

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_service(account_name):
    token_file = f"token_{account_name}.json"
    if not os.path.exists(token_file):
        print(f"Error: Token for {account_name} not found. Run auth_google.py first.")
        return None
        
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    return build('calendar', 'v3', credentials=creds)

def create_event(account_name, summary, start_date, end_date, attendees=[]):
    """
    Creates an all-day event.
    start_date/end_date: 'YYYY-MM-DD' string.
    """
    service = get_service(account_name)
    if not service: return

    event = {
        'summary': summary,
        'start': {'date': start_date},
        'end': {'date': end_date},
        'attendees': [{'email': email} for email in attendees],
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating event: {e}")

def create_timed_event(account_name, summary, start_dt, end_dt, location=None, description=None, attendees=[]):
    """
    Creates a timed event.
    start_dt/end_dt: ISO 8601 strings (e.g. '2023-10-25T19:00:00+02:00')
    """
    service = get_service(account_name)
    if not service: return

    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_dt,
            'timeZone': 'Europe/Berlin',
        },
        'end': {
            'dateTime': end_dt,
            'timeZone': 'Europe/Berlin',
        },
        'attendees': [{'email': email} for email in attendees],
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Timed Event created: {event.get('htmlLink')}")
        return event.get('htmlLink')
    except Exception as e:
        print(f"Error creating timed event: {e}")
        return None

if __name__ == '__main__':
    # Test stub
    pass
