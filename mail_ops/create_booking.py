import argparse
import sys
from calendar_ops import create_timed_event

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument("start_time", help="HH:MM:SS")
    parser.add_argument("end_time", help="HH:MM:SS")
    parser.add_argument("title", help="Event Title")
    parser.add_argument("location", nargs='?', help="Event Location")
    parser.add_argument("desc", nargs='?', help="Description")
    args = parser.parse_args()

    # Create ISO Strings
    start_dt = f"{args.date}T{args.start_time}+01:00" # Assuming Berlin +1
    end_dt = f"{args.date}T{args.end_time}+01:00"

    print(f"Creating event '{args.title}' on {start_dt} at '{args.location}'")
    
    # We pass 'andre' as the account
    create_timed_event(
        account_name="andre",
        summary=args.title,
        start_dt=start_dt,
        end_dt=end_dt,
        location=args.location,
        description=args.desc
    )

if __name__ == "__main__":
    main()
