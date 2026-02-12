import datetime
from calendar_ops import create_event

# Target Account (matches token_andre.json)
ACCOUNT = "andre"
ATTENDEES = ["anke.vera@hotmail.de"]

EVENTS = [
    {"summary": "Kita Geschlossen - Brückentag", "start": "2026-05-15", "end": "2026-05-16"}, # End date is exclusive in GCal API for all-day
    {"summary": "Kita Geschlossen - Brückentag", "start": "2026-06-05", "end": "2026-06-06"},
    {"summary": "Kita Geschlossen - Pädagogischer Tag", "start": "2026-07-16", "end": "2026-07-17"},
    {"summary": "Kita Geschlossen - Teamtag", "start": "2026-07-17", "end": "2026-07-18"},
    {"summary": "Kita Geschlossen - Planungs- und Putztag", "start": "2026-07-31", "end": "2026-08-01"},
    {"summary": "Sommerschließung Kita", "start": "2026-08-17", "end": "2026-08-29"}, # Ends 28th, so exclusive is 29th
    {"summary": "Kita Geschlossen - Pädagogischer Tag", "start": "2026-10-26", "end": "2026-10-27"},
    {"summary": "Winterschließung Kita", "start": "2026-12-23", "end": "2027-01-07"} # Ends Jan 6, exclusive Jan 7
]

print(f"Creating {len(EVENTS)} events for {ACCOUNT}...")

for evt in EVENTS:
    print(f"Adding: {evt['summary']} ({evt['start']})...")
    create_event(ACCOUNT, evt['summary'], evt['start'], evt['end'], attendees=ATTENDEES)

print("Done!")
