import datetime
import os.path
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from calendar_ops import get_service

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token_andre.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token_andre.json"):
    creds = Credentials.from_authorized_user_file("token_andre.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      print("Token expired or missing for Andre. Run auth_google.py first.")
      return

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Check if a date is provided as argument (YYYY-MM-DD)
    if len(sys.argv) > 1:
        target_date_str = sys.argv[1]
        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        time_min = target_date.isoformat()
        time_max = (target_date + datetime.timedelta(days=1)).isoformat()
        print(f"Checking events for {target_date_str}...")
    else:
        time_min = now
        time_max = None
        print("Checking upcoming 10 events...")

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=10 if not time_max else 50,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(f"{start} - {event['summary']}")

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
